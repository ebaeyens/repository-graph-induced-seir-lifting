# The full target cleans generated outputs and reproduces all published and
# additional results. Timing columns naturally depend on the machine.
PYTHON ?= python

.PHONY: install reproduce reproduce-all reproduce-additional check check-reported check-metadata check-index pytest validate clean-output help
install:
	$(PYTHON) -m pip install -r requirements-lock.txt

reproduce:
	$(PYTHON) scripts/reproduce.py

reproduce-all:
	$(PYTHON) scripts/reproduce_all.py

reproduce-additional:
	$(PYTHON) scripts/reproduce_additional.py

pytest:
	$(PYTHON) -m pytest -q

validate:
	$(PYTHON) scripts/validate_outputs.py
	$(PYTHON) experiments/scripts/validate_experimental_data.py --repo . --results experiments/data

check-reported:
	$(PYTHON) scripts/validate_reported_tables.py

check-index:
	$(PYTHON) scripts/check_reproducibility_index.py

check-metadata:
	$(PYTHON) scripts/check_release_metadata.py

check: pytest validate check-reported check-metadata check-index
	$(PYTHON) -m compileall -q scripts tests experiments

clean-output:
	rm -rf output/data output/tables output/figures \
	  experiments/data experiments/figures experiments/tables experiments/results

help:
	@echo 'make reproduce-all   Full clean reproduction, original and revised experiments'
	@echo 'make check           Run tests, validators, reported-table audit and syntax checks'
	@echo 'make check-reported  Audit manuscript table values against CSVs'
	@echo 'make check-metadata  Check the GitHub URL, versions and Zenodo DOI status'
	@echo 'make check-index     Check table/figure mappings, paths and accepted seeds'
	@echo 'make reproduce       Original published experiments and peak-grid refinement'
