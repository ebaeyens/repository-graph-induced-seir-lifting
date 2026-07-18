# Compilación

## Requisitos

- Python 3.10 o posterior. El script usa solo la biblioteca estándar.
- Una distribución LaTeX con `pdflatex`, `latexmk`, `amsmath`, `booktabs`, `longtable`, `tikz`, `hyperref` y `cleveref`.

## Flujo recomendado

Desde la raíz de la carpeta:

```bash
python scripts/generate_example_artifacts.py
latexmk -C
latexmk -pdf main.tex
```

## Salida esperada

- `three_city_algorithm1_complete.pdf`
- CSV actualizados en `data/`
- fragmentos TeX actualizados en `generated/`

## Comprobación rápida

El script debe terminar con:

```text
All three-city Algorithm 1 checks passed.
```

La compilación LaTeX no debe producir referencias indefinidas, etiquetas duplicadas ni elementos recortados.
