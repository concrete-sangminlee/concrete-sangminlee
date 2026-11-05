PYTHON ?= python3

.PHONY: build test check check-dois

build:
	$(PYTHON) scripts/build_readme_page.py

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

check: build test

# Needs network access to doi.org; not part of `check`.
check-dois:
	$(PYTHON) scripts/check_dois.py
