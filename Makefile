PYTHON ?= python3

.PHONY: build preview-image test check check-dois

build:
	$(PYTHON) scripts/build_readme_page.py

# Rasterizes docs/og-preview.svg to PNG with a local Chrome or Chromium, if one is found.
preview-image: build
	$(PYTHON) scripts/render_og_png.py

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

check: build test

# Needs network access to doi.org; not part of `check`.
check-dois:
	$(PYTHON) scripts/check_dois.py
