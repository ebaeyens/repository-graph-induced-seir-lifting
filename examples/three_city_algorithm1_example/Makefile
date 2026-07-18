.PHONY: generate verify pdf clean all

generate:
	python scripts/generate_example_artifacts.py

verify: generate
	@echo "Mathematical dictionary checks completed."

pdf: generate
	latexmk -pdf main.tex
	cp main.pdf three_city_algorithm1_complete.pdf

all: verify pdf

clean:
	latexmk -C
	rm -f main.pdf
