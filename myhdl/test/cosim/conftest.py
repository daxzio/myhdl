"""Pytest fixtures for backend-agnostic cosimulation tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Cosim is a pytest directory, not myhdl.test.cosim: myhdl/test has no
# __init__.py (adding one breaks collection of myhdl/test/core).
_COSIM_DIR = Path(__file__).resolve().parent
if str(_COSIM_DIR) not in sys.path:
    sys.path.insert(0, str(_COSIM_DIR))

from backends import CosimBackend, all_backends, get_backend
from designs import DESIGNS, Design


def pytest_addoption(parser):
    parser.addoption(
        "--cosim",
        action="store",
        default=None,
        help="Cosim backend to use (python, iverilog, verilator, verilator4)",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires(capability): skip unless backend supports capability",
    )


@pytest.fixture(autouse=True)
def _reset_simulation_state():
    yield
    from myhdl._Simulation import Simulation

    Simulation._no_of_instances = 0


def pytest_generate_tests(metafunc):
    if "backend" not in metafunc.fixturenames:
        return
    opt = metafunc.config.getoption("--cosim")
    if opt:
        backend = get_backend(opt)
        if not backend.available():
            pytest.skip(f"cosim backend {opt!r} is not available")
        backends = [backend]
    else:
        backends = [b for b in all_backends() if b.available()]
        if not backends:
            pytest.skip("no cosim backends available")
    metafunc.parametrize("backend", backends, ids=lambda b: b.name)


@pytest.fixture
def build_cache(tmp_path_factory):
    cache = {}

    def _build(backend: CosimBackend, design: Design, params: dict) -> Path:
        key = (backend.name, design.name, tuple(sorted(params.items())))
        if key not in cache:
            workdir = tmp_path_factory.mktemp(
                f"{backend.name}_{design.name}_{len(cache)}"
            )
            backend.build(design, workdir, params)
            cache[key] = workdir
        return cache[key]

    return _build


def _infer_params(design: Design, params: dict, signals: dict) -> dict:
    params = dict(params)
    for pname in design.params:
        if pname in params:
            continue
        if pname == "width":
            for port in design.ports:
                if port.width == 0 and port.name in signals:
                    params["width"] = len(signals[port.name])
                    break
        if pname not in params:
            raise ValueError(f"missing design param {pname!r}")
    return params


@pytest.fixture
def cosim(backend, build_cache, request, tmp_path_factory):
    def _cosim(design_name: str, params=None, **signals):
        marker = request.node.get_closest_marker("requires")
        if marker is not None:
            (cap,) = marker.args
            probe_root = tmp_path_factory.getbasetemp()
            if cap not in backend.capabilities(probe_root):
                pytest.skip(f"{backend.name} lacks {cap!r}")

        design = DESIGNS[design_name]
        params = _infer_params(design, dict(params or {}), signals)
        workdir = build_cache(backend, design, params)
        return backend.create_dut(design, workdir, params, signals)

    return _cosim
