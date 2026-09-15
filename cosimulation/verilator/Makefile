# Build MyHDL Verilator cosim executable for one DUT.
#
# Usage:
#   make DUT=dut_inc SOURCES="../../test/verilog/inc.v ../../test/verilog/dut_inc.v" \
#        DEFS="n=253" WORKDIR=/tmp/vlt_inc

VERILATOR ?= verilator
WORKDIR ?= obj_dir
DUT ?= dut_inc
SOURCES ?=
DEFS ?=
FOURSTATE ?= 0

VERILATOR_DIR := $(shell dirname $(shell which $(VERILATOR)))/../share/verilator
SHIM_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# Do not pass global --public-flat-rw: with --timing it marks std::process
# internals public and fails to compile on Verilator 5.048 (issue #7592).
# VPI access is via /*verilator public_flat_rw*/ on DUT/tb signals.
VLT_FLAGS = --cc --exe --vpi --timing --timescale 1ns/1ps \
	--prefix Vtop -o Vtop -Mdir $(WORKDIR) --top-module $(DUT) \
	-Wno-fatal -Wno-DEFPARAM --language 1364-2005 \
	-CFLAGS -Wno-error=write-strings

ifeq ($(FOURSTATE),1)
VLT_FLAGS += --fourstate -Wno-FUTURE
else
VLT_FLAGS += --no-fourstate
endif

DEF_ARGS := $(foreach d,$(DEFS),-D$(d))

.PHONY: all clean

all: $(WORKDIR)/Vtop

$(WORKDIR)/Vtop: $(SOURCES) $(SHIM_DIR)myhdl_verilator.cpp $(SHIM_DIR)myhdl_main.cpp
	$(VERILATOR) $(VLT_FLAGS) $(DEF_ARGS) \
		$(SOURCES) $(SHIM_DIR)myhdl_verilator.cpp $(SHIM_DIR)myhdl_main.cpp
	$(MAKE) -C $(WORKDIR) -f Vtop.mk

clean:
	rm -rf $(WORKDIR)
