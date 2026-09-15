// Custom Verilator main: VPI cosim event loop (cocotb-style scheduling).

#include "verilated.h"
#include "verilated_vpi.h"
#include "Vtop.h"

#include <algorithm>
#include <memory>

extern "C" void myhdl_startup();
extern "C" int myhdl_time_synced();

static vluint64_t main_time = 0;

double sc_time_stamp() {
    return static_cast<double>(main_time);
}

static bool settle_value_callbacks() {
    bool cbs_called = VerilatedVpi::callValueCbs();
    bool again = cbs_called;
    while (again) {
        again = VerilatedVpi::callValueCbs();
    }
    return cbs_called;
}

int main(int argc, char** argv) {
    const std::unique_ptr<VerilatedContext> contextp{new VerilatedContext};
    contextp->commandArgs(argc, argv);
    const std::unique_ptr<Vtop> top{new Vtop{contextp.get(), ""}};

    Verilated::fatalOnVpiError(false);
    myhdl_startup();
    VerilatedVpi::callCbs(cbStartOfSimulation);
    settle_value_callbacks();

    while (!Verilated::gotFinish()) {
        if (!myhdl_time_synced()) {
            VerilatedVpi::callTimedCbs();
            VerilatedVpi::callCbs(cbReadOnlySynch);
            settle_value_callbacks();
            continue;
        }
        do {
            do {
                top->eval_step();
                VerilatedVpi::clearEvalNeeded();
                VerilatedVpi::doInertialPuts();
                settle_value_callbacks();
            } while (VerilatedVpi::evalNeeded());

            VerilatedVpi::callCbs(cbReadWriteSynch);
            VerilatedVpi::doInertialPuts();
            settle_value_callbacks();
        } while (VerilatedVpi::evalNeeded());

        top->eval_end_step();
        VerilatedVpi::callCbs(cbReadOnlySynch);

        const vluint64_t NO_EVENT = static_cast<vluint64_t>(~0ULL);
        vluint64_t next = VerilatedVpi::cbNextDeadline();
        if (top->eventsPending()) {
            next = std::min(next, top->nextTimeSlot());
        }
        if (next == NO_EVENT) {
            break;
        }

        main_time = next;
        contextp->time(next);

        VerilatedVpi::callCbs(cbNextSimTime);
        settle_value_callbacks();
        VerilatedVpi::callTimedCbs();
        settle_value_callbacks();
    }

    top->final();
    VerilatedVpi::callCbs(cbEndOfSimulation);
    return 0;
}
