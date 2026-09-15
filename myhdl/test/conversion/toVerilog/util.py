import os
import re
path = os.path
import subprocess
from glob import glob

from myhdl import Cosimulation, CosimulationError

_REPO_ROOT = path.normpath(path.join(path.dirname(__file__), '../../../../'))
_SHIM_DIR = path.join(_REPO_ROOT, 'cosimulation/verilator')
_VPI_FILE = path.join(_REPO_ROOT, 'cosimulation/icarus/myhdl.vpi')


def _parse_tb_cosim_ports(tb_path):
    """Return (from_names, to_names) from generated $from_myhdl/$to_myhdl calls."""
    text = open(tb_path).read()

    def _names(call):
        m = re.search(r'\$%s\s*\(\s*(.*?)\s*\)\s*;' % call, text, re.DOTALL)
        if not m:
            return []
        return [n.strip() for n in m.group(1).replace('\n', ' ').split(',') if n.strip()]

    return _names('from_myhdl'), _names('to_myhdl')


def _write_verilator_manifest(manifest_path, tb_top, from_names, to_names):
    lines = []
    for sig in from_names:
        lines.append(f"from {tb_top}.{sig} {sig}\n")
    for sig in to_names:
        lines.append(f"to {tb_top}.{sig} {sig}\n")
    with open(manifest_path, 'w') as f:
        f.writelines(lines)


def _verilator_workdir(name, vfile):
    return path.join(path.dirname(vfile), '.vlt_{}'.format(name))


# Icarus
def setupCosimulationIcarus(**kwargs):
    name = kwargs['name']
    objfile = "%s.o" % name
    if path.exists(objfile):
        os.remove(objfile)
    analyze_cmd = ['iverilog', '-o', objfile, '%s.v' % name, 'tb_%s.v' % name]
    subprocess.call(analyze_cmd)
    vpifile = _VPI_FILE
    if not path.isfile(vpifile):
        vpifiles = glob("**/myhdl.vpi", recursive=True)
        if len(vpifiles) == 1:
            vpifile = vpifiles[0]
    simulate_cmd = ['vvp', '-m', vpifile, objfile]
    return Cosimulation(simulate_cmd, **kwargs)


def setupCosimulationVerilator(**kwargs):
    """Verilator cosim using MYHDL_MANIFEST (see cosimulation/verilator/)."""
    name = kwargs['name']
    vfile = path.abspath('%s.v' % name)
    tbfile = path.abspath('tb_%s.v' % name)
    if not path.isfile(tbfile):
        raise CosimulationError("testbench %s not found; convert to Verilog first" % tbfile)

    tb_top = 'tb_%s' % name
    from_names, to_names = _parse_tb_cosim_ports(tbfile)
    workdir = path.abspath(_verilator_workdir(name, vfile))
    os.makedirs(workdir, exist_ok=True)
    manifest_path = path.join(workdir, 'manifest')
    _write_verilator_manifest(manifest_path, tb_top, from_names, to_names)

    sources = '%s %s' % (vfile, tbfile)
    build_cmd = [
        'make', '-C', _SHIM_DIR,
        'WORKDIR=%s' % workdir,
        'DUT=%s' % tb_top,
        'SOURCES=%s' % sources,
    ]
    subprocess.run(build_cmd, check=True)

    exe = path.join(workdir, 'Vtop')
    env = os.environ.copy()
    env['MYHDL_MANIFEST'] = manifest_path
    return Cosimulation([exe], _env=env, **kwargs)


# cver
def setupCosimulationCver(**kwargs):
    name = kwargs['name']
    cmd = "cver -q +loadvpi=../../../../cosimulation/cver/myhdl_vpi:vpi_compat_bootstrap " + \
          "%s.v tb_%s.v " % (name, name)
    return Cosimulation(cmd, **kwargs)


def verilogCompileIcarus(name):
    objfile = "%s.o" % name
    if path.exists(objfile):
        os.remove(objfile)
    analyze_cmd = "iverilog -o %s %s.v tb_%s.v" % (objfile, name, name)
    os.system(analyze_cmd)


def verilogCompileCver(name):
    cmd = "cver -c %s.v" % name
    os.system(cmd)


def _default_cosim_backend():
    return os.environ.get('MYHDL_COSIM', 'icarus').lower()


if _default_cosim_backend() == 'verilator':
    setupCosimulation = setupCosimulationVerilator
else:
    setupCosimulation = setupCosimulationIcarus
# setupCosimulation = setupCosimulationCver

verilogCompile = verilogCompileIcarus
# verilogCompile = verilogCompileCver
