# Rule: Zero fabricated numbers

Every metric in this repo must be produced by running the harness. No exceptions.

- Do NOT hardcode, guess, illustrate, or "for example" any F1 / precision / recall /
  AUC / accuracy / latency number — not in README, not in docstrings, not in comments,
  not in markdown tables, not in test fixtures pretending to be results.
- A hypothesis is allowed only as **words with no numbers**, explicitly labelled as an
  unmeasured expectation to be confirmed by a run. Example (allowed):
  "We expect lexical matchers to collapse under the homoglyph attack until confusable
  folding is applied." Example (forbidden): "lexical F1 drops to ~0.2 under homoglyphs."
- Numbers describing the *dataset itself* (counts, ratios, seed values, code-point values,
  config defaults) are fine — they are inputs/provenance, not measured outcomes.
- `results/` is written ONLY by the eval harness (Phase 7). Until then it stays empty.
- When citing external work (e.g. "OpenSanctions RegressionV1 ~91% F1 on their Pairs set"),
  attribute it to the source explicitly; it is a citation, not our measurement.
