// MyHDL cosimulation VPI shim for Verilator (manifest-based signal discovery).
// Port of cosimulation/icarus/myhdl.c; omits $from_myhdl/$to_myhdl (unsupported).

#include <vpi_user.h>

#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <unistd.h>

#define MAXLINE 4096
#define MAXWIDTH 10
#define MAXARGS 1024
#define MAXNAME 256

typedef unsigned long long myhdl_time64_t;

struct PortEntry {
    vpiHandle handle;
    char myhdl_name[MAXNAME];
};

static int rpipe;
static int wpipe;

static PortEntry from_ports[MAXARGS];
static PortEntry to_ports[MAXARGS];
static int num_from;
static int num_to;

static char changeFlag[MAXARGS];
static int change_ids[MAXARGS];
static char bufcp[MAXLINE];

static myhdl_time64_t myhdl_time;
static myhdl_time64_t verilog_time;
static myhdl_time64_t pli_time;
static int delta;
static int time_synced;

extern "C" int myhdl_time_synced() {
    return time_synced;
}

static PLI_INT32 readonly_callback(p_cb_data cb_data);
static PLI_INT32 delay_callback(p_cb_data cb_data);
static PLI_INT32 delta_callback(p_cb_data cb_data);
static PLI_INT32 change_callback(p_cb_data cb_data);

static myhdl_time64_t timestruct_to_time(const t_vpi_time* ts) {
    myhdl_time64_t ti = ts->high;
    ti <<= 32;
    ti += ts->low & 0xffffffff;
    return ti;
}

static int init_pipes() {
    static int init_pipes_flag = 0;
    if (init_pipes_flag) return 0;

    char* w = getenv("MYHDL_TO_PIPE");
    char* r = getenv("MYHDL_FROM_PIPE");
    if (!w) {
        vpi_printf("ERROR: no write pipe to myhdl\n");
        vpi_control(vpiFinish, 1);
        return 0;
    }
    if (!r) {
        vpi_printf("ERROR: no read pipe from myhdl\n");
        vpi_control(vpiFinish, 1);
        return 0;
    }
    wpipe = atoi(w);
    rpipe = atoi(r);
    init_pipes_flag = 1;
    return 0;
}

static int read_manifest(const char* path) {
    FILE* fp = fopen(path, "r");
    if (!fp) {
        vpi_printf("ERROR: cannot open MYHDL manifest %s\n", path);
        return 1;
    }
    char line[MAXLINE];
    num_from = num_to = 0;
    while (fgets(line, sizeof(line), fp)) {
        char dir[16];
        char hier[MAXNAME];
        char myhdl[MAXNAME];
        if (sscanf(line, "%15s %255s %255s", dir, hier, myhdl) != 3) continue;

        vpiHandle h = vpi_handle_by_name(hier, NULL);
        if (!h) {
            vpi_printf("ERROR: vpi_handle_by_name(%s) failed\n", hier);
            fclose(fp);
            return 1;
        }
        if (strcmp(dir, "from") == 0) {
            if (num_from >= MAXARGS) {
                vpi_printf("ERROR: too many FROM ports\n");
                fclose(fp);
                return 1;
            }
            from_ports[num_from].handle = h;
            strncpy(from_ports[num_from].myhdl_name, myhdl, MAXNAME - 1);
            num_from++;
        } else if (strcmp(dir, "to") == 0) {
            if (num_to >= MAXARGS) {
                vpi_printf("ERROR: too many TO ports\n");
                fclose(fp);
                return 1;
            }
            to_ports[num_to].handle = h;
            strncpy(to_ports[num_to].myhdl_name, myhdl, MAXNAME - 1);
            num_to++;
        }
    }
    fclose(fp);
    return 0;
}

static int pipe_read_ok(char* buf, int n) {
    if (n <= 0) return 0;
    buf[n] = '\0';
    return 1;
}

static void pipe_write(const char* buf, size_t n) {
    if (write(wpipe, buf, n) != (ssize_t)n) {
        vpi_control(vpiFinish, 1);
    }
}

extern "C" void myhdl_startup() {
    init_pipes();

    const char* manifest = getenv("MYHDL_MANIFEST");
    if (!manifest) {
        vpi_printf("ERROR: MYHDL_MANIFEST not set\n");
        vpi_control(vpiFinish, 1);
        return;
    }
    if (read_manifest(manifest)) {
        vpi_control(vpiFinish, 1);
        return;
    }

    t_vpi_time verilog_time_s;
    verilog_time_s.type = vpiSimTime;
    vpi_get_time(NULL, &verilog_time_s);
    verilog_time = timestruct_to_time(&verilog_time_s);
    if (verilog_time != 0) {
        vpi_printf("ERROR: myhdl_startup should run at time 0\n");
        vpi_control(vpiFinish, 1);
        return;
    }

    pli_time = 0;
    delta = 0;

    char buf[MAXLINE];
    char s[MAXWIDTH];
    int n;

    // FROM handshake
    buf[0] = '\0';
    strcat(buf, "FROM 0 ");
    for (int i = 0; i < num_from; i++) {
        strcat(buf, from_ports[i].myhdl_name);
        strcat(buf, " ");
        sprintf(s, "%d ", vpi_get(vpiSize, from_ports[i].handle));
        strcat(buf, s);
    }
    pipe_write(buf, strlen(buf));
    n = read(rpipe, buf, MAXLINE - 1);
    if (!pipe_read_ok(buf, n)) {
        vpi_printf("Info: MyHDL simulator down (FROM)\n");
        vpi_control(vpiFinish, 1);
        return;
    }

    // TO handshake + register change callbacks
    buf[0] = '\0';
    strcat(buf, "TO 0 ");
    s_cb_data cb_data_s;
    t_vpi_time time_s;
    s_vpi_value value_s;
    time_s.type = vpiSuppressTime;
    value_s.format = vpiSuppressVal;
    cb_data_s.reason = cbValueChange;
    cb_data_s.cb_rtn = change_callback;
    cb_data_s.time = &time_s;
    cb_data_s.value = &value_s;

    for (int i = 0; i < num_to; i++) {
        strcat(buf, to_ports[i].myhdl_name);
        strcat(buf, " ");
        sprintf(s, "%d ", vpi_get(vpiSize, to_ports[i].handle));
        strcat(buf, s);
        changeFlag[i] = 1;
        change_ids[i] = i;
        cb_data_s.user_data = (PLI_BYTE8*)&change_ids[i];
        cb_data_s.obj = to_ports[i].handle;
        vpi_register_cb(&cb_data_s);
    }
    pipe_write(buf, strlen(buf));
    n = read(rpipe, buf, MAXLINE - 1);
    if (!pipe_read_ok(buf, n)) {
        vpi_printf("ABORT from TO handshake\n");
        vpi_control(vpiFinish, 1);
        return;
    }

    time_s.type = vpiSimTime;
    time_s.high = 0;
    time_s.low = 0;
    cb_data_s.reason = cbReadOnlySynch;
    cb_data_s.user_data = NULL;
    cb_data_s.cb_rtn = readonly_callback;
    cb_data_s.obj = NULL;
    cb_data_s.time = &time_s;
    cb_data_s.value = NULL;
    vpi_register_cb(&cb_data_s);

    delta = 0;
    time_s.low = 1;
    cb_data_s.reason = cbAfterDelay;
    cb_data_s.cb_rtn = delta_callback;
    vpi_register_cb(&cb_data_s);
}

static PLI_INT32 readonly_callback(p_cb_data cb_data) {
    (void)cb_data;
    s_cb_data cb_data_s;
    t_vpi_time verilog_time_s;
    s_vpi_value value_s;
    t_vpi_time time_s;
    char buf[MAXLINE];
    int n;
    myhdl_time64_t delay;

    static int start_flag = 1;
    if (start_flag) {
        start_flag = 0;
        pipe_write("START", 5);
        n = read(rpipe, buf, MAXLINE - 1);
        if (!pipe_read_ok(buf, n)) {
            vpi_printf("ABORT from RO cb at start-up\n");
            vpi_control(vpiFinish, 1);
        }
    }

    buf[0] = '\0';
    verilog_time_s.type = vpiSimTime;
    vpi_get_time(NULL, &verilog_time_s);
    verilog_time = timestruct_to_time(&verilog_time_s);

    sprintf(buf, "%llu ", (unsigned long long)pli_time);
    value_s.format = vpiHexStrVal;
    for (int i = 0; i < num_to; i++) {
        if (changeFlag[i]) {
            strcat(buf, to_ports[i].myhdl_name);
            strcat(buf, " ");
            vpi_get_value(to_ports[i].handle, &value_s);
            strcat(buf, value_s.value.str);
            strcat(buf, " ");
            changeFlag[i] = 0;
        }
    }
    pipe_write(buf, strlen(buf));
    n = read(rpipe, buf, MAXLINE - 1);
    if (!pipe_read_ok(buf, n)) {
        vpi_control(vpiFinish, 1);
        return 0;
    }
    strcpy(bufcp, buf);
    time_synced = 1;

    char* myhdl_time_string = strtok(buf, " ");
    myhdl_time = (myhdl_time64_t)strtoull(myhdl_time_string, NULL, 10);
    delay = (myhdl_time - pli_time) * 1000;
    if (delay > 0) {
        delay -= delta;
        delta = 0;
        pli_time = myhdl_time;
        time_s.type = vpiSimTime;
        time_s.high = 0;
        time_s.low = (PLI_UINT32)delay;
        cb_data_s.reason = cbAfterDelay;
        cb_data_s.user_data = NULL;
        cb_data_s.cb_rtn = delay_callback;
        cb_data_s.obj = NULL;
        cb_data_s.time = &time_s;
        cb_data_s.value = NULL;
        vpi_register_cb(&cb_data_s);
    } else {
        delta++;
    }
    return 0;
}

static PLI_INT32 delay_callback(p_cb_data cb_data) {
    (void)cb_data;
    s_cb_data cb_data_s;
    t_vpi_time time_s;

    time_s.type = vpiSimTime;
    time_s.high = 0;
    time_s.low = 0;
    cb_data_s.reason = cbReadOnlySynch;
    cb_data_s.user_data = NULL;
    cb_data_s.cb_rtn = readonly_callback;
    cb_data_s.obj = NULL;
    cb_data_s.time = &time_s;
    cb_data_s.value = NULL;
    vpi_register_cb(&cb_data_s);

    time_s.low = 1;
    cb_data_s.reason = cbAfterDelay;
    cb_data_s.cb_rtn = delta_callback;
    vpi_register_cb(&cb_data_s);
    return 0;
}

static PLI_INT32 delta_callback(p_cb_data cb_data) {
    (void)cb_data;
    if (delta == 0) return 0;

    s_cb_data cb_data_s;
    t_vpi_time time_s;
    s_vpi_value value_s;

    strtok(bufcp, " ");
    value_s.format = vpiHexStrVal;
    for (int i = 0; i < num_from; i++) {
        value_s.value.str = strtok(NULL, " ");
        if (!value_s.value.str) break;
        vpi_put_value(from_ports[i].handle, &value_s, NULL, vpiNoDelay);
    }

    time_s.type = vpiSimTime;
    time_s.high = 0;
    time_s.low = 0;
    cb_data_s.reason = cbReadOnlySynch;
    cb_data_s.user_data = NULL;
    cb_data_s.cb_rtn = readonly_callback;
    cb_data_s.obj = NULL;
    cb_data_s.time = &time_s;
    cb_data_s.value = NULL;
    vpi_register_cb(&cb_data_s);

    time_s.low = 1;
    cb_data_s.reason = cbAfterDelay;
    cb_data_s.cb_rtn = delta_callback;
    vpi_register_cb(&cb_data_s);
    return 0;
}

static PLI_INT32 change_callback(p_cb_data cb_data) {
    int* id = (int*)cb_data->user_data;
    changeFlag[*id] = 1;
    return 0;
}
