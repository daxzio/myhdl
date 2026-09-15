"""Cosimulation design descriptors shared by all backends."""

from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VERILOG_DIR = REPO_ROOT / "cosimulation" / "test" / "verilog"


@dataclass(frozen=True)
class Port:
    """One signal crossing the MyHDL/HDL boundary."""

    name: str
    direction: str  # "from" (MyHDL drives) | "to" (HDL drives)
    width: int  # 0 => width comes from params at runtime


@dataclass(frozen=True)
class Design:
    """One cosimulation DUT."""

    name: str
    top: str
    sources: tuple[str, ...]
    ports: tuple[Port, ...]
    params: tuple[str, ...] = ()


DESIGNS = {
    "inc": Design(
        name="inc",
        top="dut_inc",
        sources=("inc.v", "dut_inc.v"),
        params=("n",),
        ports=(
            Port("enable", "from", 1),
            Port("clock", "from", 1),
            Port("reset", "from", 1),
            Port("count", "to", 16),
        ),
    ),
    "dff": Design(
        name="dff",
        top="dut_dff",
        sources=("dff.v", "dut_dff.v"),
        ports=(
            Port("d", "from", 1),
            Port("clk", "from", 1),
            Port("reset", "from", 1),
            Port("q", "to", 1),
        ),
    ),
    "dff_clkout": Design(
        name="dff_clkout",
        top="dut_dff_clkout",
        sources=("dff_clkout.v", "dut_dff_clkout.v"),
        ports=(
            Port("d", "from", 1),
            Port("clk", "from", 1),
            Port("reset", "from", 1),
            Port("clkout", "to", 1),
            Port("q", "to", 1),
        ),
    ),
    "bin2gray": Design(
        name="bin2gray",
        top="dut_bin2gray",
        sources=("bin2gray.v", "dut_bin2gray.v"),
        params=("width",),
        ports=(
            Port("B", "from", 0),
            Port("G", "to", 0),
        ),
    ),
    "const_1": Design(
        name="const_1",
        top="dut_const_1",
        sources=("const_1.v", "dut_const_1.v"),
        ports=(
            Port("clk", "from", 1),
            Port("q", "to", 1),
        ),
    ),
    "passthrough": Design(
        name="passthrough",
        top="dut_passthrough",
        sources=("passthrough.v", "dut_passthrough.v"),
        params=("width",),
        ports=(
            Port("a", "from", 0),
            Port("b", "to", 0),
        ),
    ),
    "xz_probe": Design(
        name="xz_probe",
        top="dut_xz_probe",
        sources=("xz_probe.v", "dut_xz_probe.v"),
        ports=(
            Port("clk", "from", 1),
            Port("x_sig", "to", 1),
            Port("z_sig", "to", 1),
            Port("z_wide", "to", 16),
        ),
    ),
}


def verilog_sources(design: Design) -> list[Path]:
    return [VERILOG_DIR / src for src in design.sources]


def write_manifest(design: Design, path: Path) -> None:
    """Write MYHDL_MANIFEST for Verilator (name-based VPI lookup)."""
    lines = []
    for port in design.ports:
        hier = f"{design.top}.{port.name}"
        lines.append(f"{port.direction} {hier} {port.name}\n")
    path.write_text("".join(lines))
