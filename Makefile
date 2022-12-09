PYTEST_OPTS ?= -W error::DeprecationWarning -W error::pytest.PytestWarning
ANSI_RED=`tput setaf 1`
ANSI_GREEN=`tput setaf 2`
ANSI_CYAN=`tput setaf 6`
ANSI_RESET=`tput sgr0`

install:
	python setup.py install

localinstall:
	python setup.py install --home=${HOME}

docs:
	tox -e docs html

livedocs:
	tox -e docs livehtml

release:
	rm -rf MANIFEST 
	rm -rf CHANGELOG.txt
	hg glog > CHANGELOG.txt
	python setup.py sdist 

clean:
	rm -rf *.vhd *.v *.o *.log *.hex work/

core:
	echo -e "\n${ANSI_CYAN}running test: $@ ${ANSI_RESET}"
	pytest ./myhdl/test/core ${PYTEST_OPTS}

iverilog_myhdl.vpi:
	${MAKE} -C cosimulation/icarus myhdl.vpi

iverilog_cosim: iverilog_myhdl.vpi
	${MAKE} -C cosimulation/icarus test

iverilog_general:
	pytest ./myhdl/test/conversion/general --sim iverilog ${PYTEST_OPTS}

iverilog_toverilog: iverilog_myhdl.vpi
	pytest ./myhdl/test/conversion/toVerilog --sim iverilog ${PYTEST_OPTS}

iverilog_bugs:
	pytest ./myhdl/test/bugs --sim iverilog ${PYTEST_OPTS}

iverilog: iverilog_cosim
	echo -e "\n${ANSI_CYAN}running test: $@ ${ANSI_RESET}"
	pytest ./myhdl/test/conversion/general ./myhdl/test/conversion/toVerilog ./myhdl/test/bugs --sim iverilog ${PYTEST_OPTS}

ghdl_general:
	pytest ./myhdl/test/conversion/general --sim ghdl ${PYTEST_OPTS}

ghdl_tovhdl:
	pytest ./myhdl/test/conversion/toVHDL --sim ghdl ${PYTEST_OPTS}

ghdl_bugs:
	pytest ./myhdl/test/bugs --sim ghdl ${PYTEST_OPTS}

ghdl:
	echo -e "\n${ANSI_CYAN}running test: $@ ${ANSI_RESET}"
	pytest ./myhdl/test/conversion/general ./myhdl/test/conversion/toVHDL ./myhdl/test/bugs --sim ghdl ${PYTEST_OPTS}

test: core iverilog ghdl