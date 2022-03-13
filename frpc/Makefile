
.PHONY: help install-dev pep257 pep8 check lint wheel install all


PYTHONPATH :=		# prevent pip from looking into sources
PYTHON     := python
PYLINT     := pylint
PEP257     := pep257
PEP8       := flake8
PIP        := pip
NAME       := frpc
VERSION    := $(shell $(PYTHON) -c \
"from frpc import VERSION; \
print(VERSION)")


help:
	@echo "Usage: \`make <target>' where <target> is one of:"
	@echo "    help           to show this message"
	@echo "    install-dev    to install dependencies for development"
	@echo "    lint           to check code using pylint"
	@echo "    pep8           to check code against PEP8"
	@echo "    pep257         to check code against PEP257"
	@echo "    check          shorthand for make lint pep8 pep257"
	@echo "    wheel          build wheel and sdist packages for pip"
	@echo "    install        install the package locally"
	@echo "    all            to run all targets"


install-dev:
	$(PIP) install $(shell $(PYTHON) -c \
"from configparser  import ConfigParser; \
parser = ConfigParser(); \
parser.read('setup.cfg'); \
print(parser.get('options.extras_require', 'dev'))")


lint:
	$(PYLINT) $(NAME)


pep8:
	$(PEP8) $(NAME)


pep257:
	$(PEP257) $(NAME)


check: lint pep8 pep257


wheel: install-dev
	$(PYTHON) -m build


install: wheel
	cd dist
	$(PIP) uninstall --yes frpc
	$(PIP) install \
	    $(shell find . -name "$(NAME)-$(VERSION)-*.whl" | head -n 1)
	cd ..


all: install-dev check wheel

