# Mapa de la derivación

| Paso del Algoritmo 1 | Contenido | Archivo principal |
|---|---|---|
| 1 | Descomposición `f = f_L + f_Q` | `sections/02_network_model.tex` |
| 2 | Semillas cuadráticas `S_i I_j` | `sections/04_degree_two.tex` |
| 3 | Cierre lineal y aparición de `S_i E_j` | `sections/04_degree_two.tex` |
| 4 | Generación cúbica por `f_Q` | `sections/05_cubic_generation.tex` |
| 5 | Canonicalización y fusión de duplicados | `sections/06_canonicalization.tex` |
| 6 | Cierre lineal del grado 3 | `sections/07_linear_closure.tex` |
| 7 | Ensamblaje de `z_2` y `z_3` | `sections/08_lifted_system.tex` |
| 8 | Residuo cuártico y verificación de cierre | `sections/09_forward_check.tex` |
| Desarrollo completo | 14 derivadas con coeficientes | `appendices/A_full_quadratic_derivatives.tex` |
| Diccionario final | 67 monomios cúbicos | `appendices/B_complete_cubic_dictionary.tex` |
| Trazabilidad | Correspondencia con los archivos generados | `appendices/C_traceability.tex` |

## Secuencia conceptual

```text
canales de transmisión
        ↓
semillas SI de grado 2
        ↓ cierre lineal
bloque {SI, SE}
        ↓ generación cuadrática
42 semillas cúbicas
        ↓ cierre lineal
67 coordenadas cúbicas
        ↓ generación cuadrática
159 semillas cuárticas
```
