# Rule: No real persons

The dataset is 100% synthetic. It must not contain real individuals or PII.

- Names are generated combinatorially from invented component banks (given roots, family
  roots + suffixes, patronymics, org tokens). The banks are plausible AZ/RU forms, not
  copied from any real registry, sanctions list, or public-figure list.
- A denylist (`src/aznamematch/components/denylist.txt`) holds well-known real full names
  (politicians, celebrities, sanctioned individuals). The generator skips any canonical
  full name that matches the denylist (case/diacritic-folded). The denylist is a guard,
  not a guarantee of exhaustiveness — document this limitation in the README.
- Do NOT seed the banks from real datasets, and do NOT reproduce a specific real person's
  full name even if it would be "realistic". Plausible-but-fictional only.
- Suffix-matrix positives (e.g. `Əliyev ↔ Əlizadə`) are a *modeling assumption* about
  geopolitical name variation, not a claim about any real person. Documented in
  `docs/suffix_matrix.md`.
