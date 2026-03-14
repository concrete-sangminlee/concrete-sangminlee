PYTHON ?= python3

.PHONY: build test check

build:
	$(PYTHON) scripts/build_readme_page.py

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

check: build test
