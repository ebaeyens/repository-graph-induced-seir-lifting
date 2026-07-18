#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python scripts/generate_example_artifacts.py
latexmk -pdf -interaction=nonstopmode main.tex
cp main.pdf three_city_algorithm1_complete.pdf

echo "Mathematical checks and LaTeX build completed successfully."
