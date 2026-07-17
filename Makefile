PYTHON ?= python

.PHONY: install reproduce experiments structural dynamic tables figures validate clean-output

install:
	$(PYTHON) -m pip install -r requirements.txt

reproduce:
	$(PYTHON) scripts/reproduce.py

experiments: structural dynamic

structural:
	$(PYTHON) scripts/run_experiments.py --stage structural

dynamic:
	$(PYTHON) scripts/run_experiments.py --stage dynamic

tables:
	$(PYTHON) scripts/make_tables.py

figures:
	$(PYTHON) scripts/make_figures.py

validate:
	$(PYTHON) scripts/validate_outputs.py

clean-output:
	rm -rf output/data output/tables output/figures
	mkdir -p output/data output/tables output/figures
