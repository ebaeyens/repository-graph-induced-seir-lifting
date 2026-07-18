# Ejemplo completo de tres ciudades aplicando el Algoritmo 1

Esta carpeta contiene un ejemplo autocontenido y exhaustivo de la construcción graph-induced y linearly closed aplicada a un modelo SEIR en red con tres ciudades.

El documento no forma parte del artículo. Su finalidad es:

- explicar paso a paso el Algoritmo 1;
- mostrar cómo aparecen todos los términos no lineales;
- distinguir las semillas generadas por la transmisión cuadrática de los términos añadidos por cierre lineal;
- verificar los conteos de los diccionarios de grados 2, 3 y 4;
- proporcionar una referencia interna para futuras revisiones del manuscrito y del código.

## Resultado principal

Para los siete canales efectivos

```text
(1,1), (1,2), (2,1), (2,2), (2,3), (3,2), (3,3)
```

se obtiene:

```text
Semillas cuadráticas:                     7
Diccionario cuadrático cerrado:          14
Apariciones cúbicas antes de fusionar:   51
Semillas cúbicas distintas:              42
Términos añadidos por cierre lineal:      25
Diccionario cúbico cerrado:              67
Dimensión de z2:                          26
Dimensión de z3:                          93
Semillas cuárticas:                      159
Diccionario cuártico cerrado:            223
```

## Estructura

```text
three_city_algorithm1_complete/
├── README.md
├── BUILD.md
├── VALIDATION.md
├── DERIVATION_MAP.md
├── main.tex
├── macros.tex
├── sections/
├── appendices/
├── scripts/
│   └── generate_example_artifacts.py
├── data/
│   ├── three_city_dictionary_counts.csv
│   ├── three_city_m3_dictionary.csv
│   └── shared_cubic_coordinates.csv
├── generated/
│   └── fragmentos TeX generados automáticamente
└── three_city_algorithm1_complete.pdf
```

## Regenerar los datos y tablas

No se requieren paquetes externos de Python.

```bash
python scripts/generate_example_artifacts.py
```

El script comprueba todos los conteos esperados y las propiedades de cierre. También regenera los CSV y los fragmentos TeX incluidos en el documento.

## Compilar el documento

```bash
latexmk -pdf main.tex
```

Para limpiar los auxiliares:

```bash
latexmk -C
```

## Convenciones matemáticas

- El par `(i,j)` representa influencia epidemiológica desde la ciudad fuente `j` hacia la ciudad receptora `i`.
- Los pares diagonales representan transmisión agregada dentro de una misma ciudad, no autoinfección individual.
- La parte cuadrática del campo genera el grado siguiente.
- La parte lineal cierra el diccionario dentro del mismo grado.
- Los monomios se canonicalizan como productos conmutativos.
- Los factores repetidos se conservan.
- Los duplicados entre distintas ecuaciones comparten una coordenada, pero mantienen coeficientes en filas diferentes del operador.
- Tras el cierre lineal, el residuo de orden 3 contiene únicamente términos de grado 4.

## Archivos canónicos

- `main.tex`: punto de entrada del documento.
- `scripts/generate_example_artifacts.py`: implementación reproducible del Algoritmo 1 para este ejemplo.
- `data/three_city_m3_dictionary.csv`: diccionario cúbico completo de 67 monomios.
- `data/three_city_dictionary_counts.csv`: conteos de control.
