"""Cosimulation backend implementations."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from cosimulation_reference import get_model
from designs import REPO_ROOT, Design, verilog_sources, write_manifest

CapabilitySet = frozenset[str]

VERILATOR_MIN = (5, 48)
SHIM_DIR = REPO_ROOT / "cosimulation" / "verilator"

_CAPABILITIES: dict[str, CapabilitySet] = {}
_VPI_PATH: Path | None | bool = False


def _find_on_path(name: str) -> str | None:
    return shutil.which(name)


def _find_myhdl_vpi() -> Path | None:
    global _VPI_PATH
    if _VPI_PATH is not False:
        return _VPI_PATH
    primary = REPO_ROOT / "cosimulation" / "icarus" / "myhdl.vpi"
    if primary.is_file():
        _VPI_PATH = primary
        return primary
    for path in REPO_ROOT.rglob("myhdl.vpi"):
        if path.is_file():
            _VPI_PATH = path
            return path
    _VPI_PATH = None
    return None


def _verilator_version() -> tuple[int, int, int] | None:
    exe = _find_on_path("verilator")
    if not exe:
        return None
    out = subprocess.run(
        [exe, "--version"], check=True, capture_output=True, text=True
    )
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", out.stdout)
    if not m:
        return None
    patch = int(m.group(3) or 0)
    return int(m.group(1)), int(m.group(2)), patch


def _verilator_ok() -> bool:
    ver = _verilator_version()
    if ver is None:
        return False
    return ver[:2] >= VERILATOR_MIN


class CosimBackend(ABC):
    name: str

    @abstractmethod
    def available(self) -> bool:
        ...

    @abstractmethod
    def build(self, design: Design, workdir: Path, params: dict) -> None:
        ...

    @abstractmethod
    def command(self, design: Design, workdir: Path) -> list[str]:
        ...

    @abstractmethod
    def create_dut(
        self,
        design: Design,
        workdir: Path,
        params: dict,
        signals: dict,
    ):
        ...

    def env(self, design: Design, workdir: Path) -> dict:
        return {}

    def capabilities(self, workdir: Path) -> CapabilitySet:
        cached = _CAPABILITIES.get(self.name)
        if cached is not None:
            return cached
        caps = self._probe_capabilities(workdir.resolve())
        _CAPABILITIES[self.name] = caps
        return caps

    def _probe_capabilities(self, workdir: Path) -> CapabilitySet:
        from probe import probe_xz

        return probe_xz(self, workdir / f"probe_{self.name}")


class PythonBackend(CosimBackend):
    name = "python"

    def available(self) -> bool:
        return True

    def build(self, design: Design, workdir: Path, params: dict) -> None:
        pass

    def command(self, design: Design, workdir: Path) -> list[str]:
        return []

    def create_dut(
        self,
        design: Design,
        workdir: Path,
        params: dict,
        signals: dict,
    ):
        factory = get_model(design.name)
        kw = dict(signals)
        kw.update(params)
        return factory(**kw)


class IcarusBackend(CosimBackend):
    name = "iverilog"

    def __init__(self) -> None:
        self._vpi = _find_myhdl_vpi()

    def available(self) -> bool:
        return (
            _find_on_path("iverilog") is not None
            and _find_on_path("vvp") is not None
            and self._vpi is not None
        )

    def build(self, design: Design, workdir: Path, params: dict) -> None:
        workdir.mkdir(parents=True, exist_ok=True)
        obj = workdir / f"{design.top}.o"
        cmd = ["iverilog", "-o", str(obj)]
        for key, value in sorted(params.items()):
            cmd.append(f"-D{key}={value}")
        cmd.extend(str(p) for p in verilog_sources(design))
        subprocess.run(cmd, check=True)

    def command(self, design: Design, workdir: Path) -> list[str]:
        assert self._vpi is not None
        obj = workdir / f"{design.top}.o"
        return ["vvp", "-m", str(self._vpi), str(obj)]

    def create_dut(
        self,
        design: Design,
        workdir: Path,
        params: dict,
        signals: dict,
    ):
        return _cosim_with_env(
            self.command(design, workdir), self.env(design, workdir), signals
        )


class VerilatorBackend(CosimBackend):
    name = "verilator"
    fourstate = False

    def available(self) -> bool:
        return _find_on_path("verilator") is not None and _verilator_ok()

    def build(self, design: Design, workdir: Path, params: dict) -> None:
        workdir = workdir.resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        write_manifest(design, workdir / "manifest")

        defs = [f"{k}={v}" for k, v in sorted(params.items())]
        sources = " ".join(str(p) for p in verilog_sources(design))
        four = "1" if self.fourstate else "0"
        cmd = [
            "make",
            "-C",
            str(SHIM_DIR),
            f"WORKDIR={workdir}",
            f"DUT={design.top}",
            f"SOURCES={sources}",
            f"DEFS={' '.join(defs)}",
            f"FOURSTATE={four}",
        ]
        subprocess.run(cmd, check=True)

    def command(self, design: Design, workdir: Path) -> list[str]:
        return [str(workdir.resolve() / "Vtop")]

    def env(self, design: Design, workdir: Path) -> dict:
        return {"MYHDL_MANIFEST": str(workdir.resolve() / "manifest")}

    def create_dut(
        self,
        design: Design,
        workdir: Path,
        params: dict,
        signals: dict,
    ):
        return _cosim_with_env(
            self.command(design, workdir), self.env(design, workdir), signals
        )


def _cosim_with_env(cmd: list[str], extra_env: dict, signals: dict):
    from myhdl import Cosimulation

    env = os.environ.copy()
    env.update(extra_env)
    return Cosimulation(cmd, _env=env, **signals)


class Verilator4Backend(VerilatorBackend):
    name = "verilator4"
    fourstate = True


def all_backends() -> list[CosimBackend]:
    return [
        PythonBackend(),
        IcarusBackend(),
        VerilatorBackend(),
        Verilator4Backend(),
    ]


def get_backend(name: str) -> CosimBackend:
    for backend in all_backends():
        if backend.name == name:
            return backend
    raise KeyError(f"Unknown cosim backend: {name!r}")
