# Rule: Transliteration & homoglyph fidelity

Cross-script variants must come from documented, competing standards — NOT invented rules.
The *divergence between standards* is the phenomenon under test.

- Every mapping is grounded in a named standard and documented in `docs/transliteration.md`
  (script transliteration) or `docs/homoglyphs.md` (Unicode TR39 confusables).
- Standards in scope:
  - **AZ Latin ⇄ Cyrillic:** BGN/PCGN 1993, ALA-LC, ISO 9 (schwa `Ə ⇄ Ә`).
  - **RU Cyrillic → Latin:** ICAO Doc 9303, GOST 7.79-2000 / ISO 9, BGN/PCGN 1947,
    ALA-LC 1997, plus ad-hoc "translit" (no consistent standard — the common real case).
  - **Adversarial homoglyphs:** Unicode TR39 confusables (Latin → Cyrillic look-alikes).
- Each standard is a separately-toggleable mapping. Every generated variant is tagged with
  the standard(s) that produced it (`translit_standard`) for provenance.
- Reversibility (round-trip) is expected ONLY for ISO 9 / GOST. Others are intentionally
  many-to-one — that lossy ambiguity is exactly why matching is hard; do not "fix" it.
- Where standards diverge, emit MULTIPLE variants (e.g. `х → {kh, h}`, `ə → {e, a}`),
  each tagged. Do not collapse to a single "preferred" rendering.
- Homoglyph substitution is a *deliberate-obfuscation* threat model, kept OUT of the core
  positive set (separate `data/adversarial/`). Do not mix it into incidental cross-script
  divergence — that would distort the cross-script findings.
