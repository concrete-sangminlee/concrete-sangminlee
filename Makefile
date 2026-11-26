PYTHON ?= python3

.PHONY: lint build preview-image test check check-dois

# Fails when README.md drifts from the shapes the site and structured data rely on.
lint:
	$(PYTHON) scripts/lint_readme.py

build:
	$(PYTHON) scripts/build_readme_page.py

# Rasterizes docs/og-preview.svg to PNG with a local Chrome or Chromium, if one is found.
preview-image: build
	$(PYTHON) scripts/render_og_png.py

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

check: lint build test

# Needs network access to doi.org; not part of `check`.
check-dois:
	$(PYTHON) scripts/check_dois.py
