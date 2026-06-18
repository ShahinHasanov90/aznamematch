# data/adversarial/

Adversarial obfuscation sets, versioned separately from the frozen core dataset so they
can grow without touching v1.0. The first set, `homoglyph_v1/` (Latin→Cyrillic Unicode
confusables, Phase 3b), is written by `aznamematch generate` and committed for inspection.

This is a *deliberate-obfuscation* threat model, intentionally kept out of the core
positive set (which models *incidental* cross-script divergence).
