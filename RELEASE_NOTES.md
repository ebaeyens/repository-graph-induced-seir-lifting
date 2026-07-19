# Release 1.0.2

This release synchronizes the repository with the final manuscript. It does
not change the numerical model, experiment configuration, random seeds, or
reported scientific results.

## Changes

- replaced procedural uses of *linear closure* with *linear saturation*;
- reserved *linearly closed* for the resulting dictionary property and
  retained *first edge-closure lifting* as the established name;
- removed the term *mechanistic* in favor of precise model- and
  transmission-supported terminology;
- separated the standalone three-city worked example into its own repository because it is not part of the numerical illustrations in Section 5;
- updated figure references so the cubic dictionary corresponds to Figure 5
  and the two residual plots correspond to Figures 3 and 4;
- converted the quick checks into discoverable `pytest` tests;
- removed generated Python cache files;
- updated repository metadata to version 1.0.2.

## Reproducibility

All structural values and stored numerical outputs remain unchanged, apart
from terminology in column names and generated explanatory files.

## DOI

The manuscript cites release v1.0.1 at DOI
`10.5281/zenodo.21427751`. A new version-specific DOI will be assigned by
Zenodo when v1.0.2 is published and should then be inserted into the citation
metadata.
