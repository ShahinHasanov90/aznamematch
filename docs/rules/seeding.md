# Rule: Seeding & reproducibility

Same seed → byte-identical dataset. This is sacred.

- There is exactly one master `seed` (in `configs/generation.yaml`).
- Derive per-stage seeds deterministically:
  ```python
  import numpy as np
  root = np.random.SeedSequence(cfg.seed)
  s_canonical, s_suffix, s_translit, s_noise, s_homoglyph, s_pairs = root.spawn(6)
  rng = np.random.default_rng(s_canonical)
  ```
  Each stage gets its own child `SeedSequence`, so a change in one stage's draw count does
  not shift another stage's stream.
- For per-record reproducibility independent of iteration order, derive a record-local RNG
  from the stage seed + a stable key (e.g. `canonical_id`):
  `np.random.default_rng(np.random.SeedSequence(entropy=[stage_entropy, record_int]))`.
- **Never** use `random` without seeding, `np.random` global state, `Math`/time-based
  entropy, `set`/`dict` iteration order as a source of order, or Python `hash()` of strings
  (salted per process). Sort collections before sampling.
- Anything non-deterministic (LLM generation, model downloads) stays OUT of the core
  generation pipeline (v2 backlog).
- Determinism is a tested invariant: generating twice with the same seed must produce
  equal outputs (see `tests/test_determinism.py`).
