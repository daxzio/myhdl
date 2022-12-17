PYTEST_OPTS ?= 
TAG ?=`grep __version__ myhdl/__init__.py | grep -oe '\([0-9.]*\)'`
MSG ?= "Release "${TAG}
VERSION_FILE := myhdl/__init__.py
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

dist:
	rm -rf MANIFEST 
	rm -rf CHANGELOG.txt
	#hg glog > CHANGELOG.txt
	python setup.py sdist

release:
	@echo "Preparing ${TAG} - Message - ${MSG}"
	@rm -rf ${VERSION_FILE}
	@git checkout -qf ${VERSION_FILE}
	@sed -i "s|__version__ = \"[0-9.]\+\"|__version__ = \"${TAG}\"|g" ${VERSION_FILE}
	git commit --allow-empty -m ${MSG} ${VERSION_FILE}
	git tag -a ${TAG} -m "${MSG}"
	git push && git push --tags

clean:
	rm -rf *.vhd *.v *.o *.log *.hex work/ cosimulation/icarus/myhdl.vpi

lint:
	pyflakes myhdl/

black:
	black myhdl/
core:
	@echo -e "\n${ANSI_CYAN}running test: $@ ${ANSI_RESET}"
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
	@echo -e "\n${ANSI_CYAN}running test: $@ ${ANSI_RESET}"
	pytest ./myhdl/test/conversion/general ./myhdl/test/conversion/toVerilog ./myhdl/test/bugs --sim iverilog ${PYTEST_OPTS}

ghdl_general:
	pytest ./myhdl/test/conversion/general --sim ghdl ${PYTEST_OPTS}

ghdl_tovhdl:
	pytest ./myhdl/test/conversion/toVHDL --sim ghdl ${PYTEST_OPTS}

ghdl_bugs:
	pytest ./myhdl/test/bugs --sim ghdl ${PYTEST_OPTS}

ghdl:
	@echo -e "\n${ANSI_CYAN}running test: $@ ${ANSI_RESET}"
	pytest ./myhdl/test/conversion/general ./myhdl/test/conversion/toVHDL ./myhdl/test/bugs --sim ghdl ${PYTEST_OPTS}

pytest: core iverilog ghdl