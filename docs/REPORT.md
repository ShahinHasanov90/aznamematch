# AzNameMatch — Technical Report

**Cross-script name matching across Azerbaijani (Latin) ↔ Russian (Cyrillic) ↔ English/Latin,
for the fraud / AML / sanctions-screening domain.**

Every number in this report is produced by `aznamematch bench` from the committed run in
[`results/`](../results/SUMMARY.md). None are hand-written. Reproduce the whole thing with
`bash scripts/reproduce.sh`. Run: seed `20260618`, **1592 test pairs**, RegressionV1 fit on a
**1046-pair entity-disjoint split** (no canonical entity shared with the test set), semantic
tier on.

---

## 1. Executive summary — what this is, and the three findings

This is **not a new matching algorithm**. Every component — phonetic coding, fuzzy string
distance, sentence embeddings, logistic regression — already exists. It is a **benchmark**
(a synthetic dataset + a set of matchers + an evaluation harness) and an **empirical study**
of how those matchers behave on the AZ-RU-EN script triple. Two contributions:

1. the first reproducible benchmark for the AZ-RU-EN triple, and
2. three measured findings that run counter to the field's prior expectation.

The claim under test is the industry's working assumption: that **cross-script
transliteration variance** — the same person written `Əliyev` / `Алиев` / `Aliyev` — is the
hard part, and that multilingual semantic embeddings would handle it best. Eight matchers
over 1592 labelled test pairs say otherwise.

| | Finding |
|---|---|
| **1** | **Cross-script matching is the easy part.** On all three cross-script cells every matcher scores **0.855–0.946** F1. A few lines of phonetic folding handle it. |
| **2** | **The hard part is same-script confusable identities.** Every zero-shot matcher collapses to **0.436–0.466** F1 there and waves through **445** hard negatives. Only the trained baseline separates them: **34** false positives, **0.860** overall F1. |
| **3** | **Cheap explainable phonetics beat a multilingual embedding** on accuracy and by ~719× on latency — the embedding wins on no accuracy axis while costing 16.3 ms per pair on CPU. |

---

## 2. Motivation and the gap

Entity-resolution systems are stress-tested with synthetic data generators. The established
lineage is **FEBRL** (Christen 2008) → **GeCo/Gecko** (Tran et al. 2013) → **pseudopeople**
(IHME 2024). They share one per-token corruption taxonomy — character edits, OCR errors,
phonetic substitutions, keyboard-adjacency typos — and they all corrupt names **within a
single writing system**.

That is the gap. For post-Soviet names the dominant real-world divergence is not an
intra-script typo. It is the *same identity rendered across three writing systems* under
competing and frequently inconsistent transliteration standards, sometimes under deliberate
obfuscation. Large 2026 multilingual benchmarks (OpenSanctions Pairs; Symphonym) do include
cross-script names, but offer no Azerbaijani-specific evaluation and no controlled
cross-script noise model.

AzNameMatch extends the FEBRL/GeCo/pseudopeople corruption paradigm with a **standard-grounded
cross-script dimension** and an **adversarial homoglyph layer**, for the AZ-RU-EN triple.

> **Honesty note.** The dataset is 100% synthetic and seeded. Name components are invented
> (Azerbaijani-realistic morphology), and the distribution does **not** reflect real-world
> name frequency — per-script-cell proportions are engineered for *evaluability* (each cell
> large and label-balanced enough for stable metrics), not as an estimate of how often each
> script pair occurs in practice.

---

## 3. What was built — dataset and transliteration standards

The frozen v1.0 dataset starts from **500 seeded synthetic identities** (persons and
organizations), expands them into **~18,000 surface forms**, and assembles **2993 labelled
pairs** (1499 positive / 1494 negative, ~50% of negatives are hard negatives; exact duplicates
removed), plus a separately frozen adversarial set of **150 homoglyph attacks**.

Every surface form carries structured **provenance**: the writing system, the transliteration
standard that produced it, the corruption types applied, the post-Soviet suffix transformation
(if any), a homoglyph flag, and a name-origin group used for fairness slicing. Components
(given / patronymic / family / organization tokens) are stored separately — this is what makes
per-cause and per-group breakdowns possible at all.

Cross-script variants are generated from **documented, competing standards**, never invented
rules, because the phenomenon under test *is* the divergence between standards:

| Direction | Standards |
|---|---|
| AZ Latin ↔ Cyrillic | BGN/PCGN, ALA-LC, ISO 9 |
| RU Cyrillic → Latin | ICAO Doc 9303 (passports), GOST 7.79 / ISO 9, BGN/PCGN, ALA-LC |
| ad-hoc | models the standardless transliteration common outside passports: `Алиев` → `Aliyev` \| `Aliev` \| `Alyev` \| `Alijev` |

Every variant is tagged with the standard that produced it.

---

## 4. The AZ-RU phonetic normalization layer, and the eight matchers

The genuine engineering core is the **AZ-RU phonetic normalization layer** — the only
component in the system that is not off-the-shelf, and deliberately kept simple.

**Before** standard phonetic coding (Soundex / Metaphone / NYSIIS), an input string is reduced
to an abstract form that collapses letters that are phonetically equivalent but written
differently across the three languages:

```
ə/e/a    x/kh/h    q/g    c/j    ç/ch    ş/sh    ğ/gh
```

So `Əliyev` and `Aliyev` reduce to a common intermediate form *before* being phonetically
indexed. Vanilla Soundex fails on that pair because it treats the leading `Ə` and `A` as
different categories; the normalization step removes that failure. The rest of the dataset was
explicitly **not** tuned to flatter this layer.

Eight matchers are evaluated under identical conditions, each returning a similarity in [0,1]:

| Matcher | Family | Trained? |
|---|---|---|
| `lexical` (rapidfuzz token-set) | lexical | no |
| `lexical_jaro_winkler` | lexical | no |
| `phonetic` | phonetic **with** the AZ-RU normalization layer | no |
| `phonetic_vanilla` | phonetic **without** it | no |
| `semantic` | multilingual sentence-BERT (MiniLM) cosine | no |
| `regression_v1` | nomenklatura/OpenSanctions-style logistic regression over name-similarity features — the field's production reference point | **yes** |
| `hybrid_blend` | weighted blend | no |
| `hybrid_cascade` | cheap-filter → expensive-confirm | no |

---

## 5. Results — the headline table and the per-cell paradox

Best-F1 operating point per matcher over the 1592-pair test set. `thr-sens` = sensitivity of
F1 to threshold choice (lower = more stable); `fair-gap` = max F1 difference across
name-origin groups (lower = smaller spread).

| matcher | F1 | P | R | PR-AUC | ROC-AUC | thr-sens | fair-gap |
|---|---|---|---|---|---|---|---|
| **regression_v1** | **0.860** | 0.884 | 0.838 | **0.951** | **0.928** | **0.010** | 0.103 |
| phonetic (normalized) | 0.754 | 0.667 | 0.866 | 0.607 | 0.612 | 0.111 | 0.097 |
| hybrid_blend | 0.727 | 0.573 | 0.993 | 0.494 | 0.463 | 0.087 | 0.079 |
| hybrid_cascade | 0.727 | 0.573 | 0.993 | 0.488 | 0.436 | 0.079 | 0.079 |
| semantic (mBERT cosine) | 0.720 | 0.565 | 0.990 | 0.481 | 0.422 | 0.034 | 0.053 |
| lexical (token-set) | 0.719 | 0.569 | 0.976 | 0.437 | 0.323 | 0.046 | 0.094 |
| lexical (Jaro-Winkler) | 0.716 | 0.562 | 0.987 | 0.558 | 0.406 | 0.033 | 0.076 |
| phonetic (vanilla) | 0.716 | 0.557 | 1.000 | 0.492 | 0.362 | 0.040 | 0.054 |

**The paradox.** Six of the eight matchers post a ROC-AUC **at or below 0.5** — they rank
pairs *worse than chance* — and yet their F1 sits at a respectable 0.716–0.727. A metric that
says "worse than a coin flip" sitting next to a metric that says "72% good" is not a bug; it
is the whole story, and the per-cell breakdown resolves it:

| matcher | AZ-RU | AZ-EN | RU-EN | **same** | same P | same R |
|---|---|---|---|---|---|---|
| hybrid_blend | 0.886 | 0.876 | 0.886 | **0.437** | 0.280 | 1.000 |
| hybrid_cascade | 0.886 | 0.876 | 0.886 | **0.437** | 0.280 | 1.000 |
| lexical | 0.869 | 0.874 | 0.876 | **0.437** | 0.280 | 1.000 |
| lexical_jaro_winkler | 0.858 | 0.878 | 0.862 | **0.436** | 0.279 | 0.995 |
| phonetic | 0.904 | 0.946 | 0.899 | **0.466** | 0.312 | 0.914 |
| phonetic_vanilla | 0.855 | 0.876 | 0.856 | **0.437** | 0.280 | 1.000 |
| **regression_v1** | 0.882 | 0.874 | 0.900 | **0.757** | 0.798 | 0.720 |
| semantic | 0.858 | 0.897 | 0.861 | **0.436** | 0.279 | 0.989 |

On the three **cross-script** cells every matcher lands **0.855–0.946**. On the **same-script**
cell every matcher except the trained RegressionV1 collapses to **~0.44**.

Read `hybrid_blend` on the same-script cell: precision **0.280** against recall **1.000**. It
says "match" to *everything* — so it never misses a positive, and it is wrong about virtually
every hard negative. The aggregate below-0.5 ROC-AUC is produced **entirely** by this cell,
which is where the hard negatives live by construction:

- **name-order swaps** — `Əli Vəli oğlu` vs `Vəli Əli oğlu`
- **generation collisions** — a father `Muradov Kənan` vs his son `Muradov Elçin Kənan oğlu`

---

## 6. Error decomposition and the homoglyph capability check

False-negative counts per root cause, per matcher, at each matcher's best-F1 threshold — plus
the column that matters most, false positives on hard negatives:

| matcher | script_divergence | phonetic_orth | lexical | hard_neg | homoglyph | **FP(hard)** |
|---|---|---|---|---|---|---|
| hybrid_blend | 6 | 0 | 0 | 0 | 0 | **445** |
| hybrid_cascade | 6 | 0 | 0 | 0 | 0 | **445** |
| lexical | 21 | 0 | 0 | 0 | 0 | **445** |
| lexical_jaro_winkler | 11 | 0 | 1 | 0 | 0 | **445** |
| phonetic | 103 | 0 | 16 | 0 | 0 | **373** |
| phonetic_vanilla | 0 | 0 | 0 | 0 | 0 | **445** |
| **regression_v1** | 92 | 3 | 49 | 0 | 0 | **34** |
| semantic | 7 | 0 | 2 | 0 | 0 | **445** |

The categories the benchmark was designed to stress produce almost no false *negatives*;
residual errors concentrate in cross-script `script_divergence`, and even there they are
modest. The revealing column is the last one. **Six of eight matchers produce 445 false
positives on hard negatives — they accept essentially all of them.** The two exceptions are
the normalized phonetic matcher (373) and, decisively, the trained RegressionV1 (**34**), which
cuts hard-negative false positives by **an order of magnitude** because it has *seen labelled
hard negatives and learned to reject them*. **445 versus 34** is the quantitative core of
Finding 2.

Adversarial homoglyphs are a separate, near-binary capability check — recall on
Latin-vs-Cyrillic confusable positives at a fixed 0.5 threshold:

| matcher | recall |
|---|---|
| regression_v1 / phonetic (normalized) / lexical (Jaro-Winkler) | **1.000** |
| hybrid_blend | 0.993 |
| semantic | 0.940 |
| hybrid_cascade | 0.820 |
| lexical (token-set) | 0.693 |
| **phonetic (vanilla)** | **0.127** |

The slice substitutes visually identical Cyrillic codepoints for Latin letters (Unicode TR39
confusables) — a real sanctions-evasion technique. A matcher either folds confusables or it
does not, so recalls are bimodal: near 1.0 or near 0.0. Plain `unidecode` does **not** defeat
the attack; the TR39 confusable-skeleton fold does. Vanilla phonetic, lacking that fold,
recalls **13%**.

---

## 7. The phonetic layer is the active ingredient — robustness, fairness, cost, latency

The two phonetic matchers differ by exactly one step, so comparing them isolates the layer's
contribution:

| | ROC-AUC | F1 | homoglyph recall | µs/pair |
|---|---|---|---|---|
| phonetic **(normalized)** | **0.612** | **0.754** | **1.000** | 22.7 |
| phonetic (vanilla) | 0.362 | 0.716 | 0.127 | 2.7 |

One normalization step moves a **below-random ranker** to clearly the second-best matcher
overall — at **22.7 µs per pair**. This is the strongest evidence in the study that a small,
domain-specific, fully explainable transformation outperforms heavier generic machinery on
this task.

**Cross-standard robustness (Unknown-Standard).** F1 retained when tuned on named standards
and evaluated on ad-hoc renderings (1.0 = no loss): phonetic **0.991** (most robust),
hybrid_cascade 0.982, lexical 0.972, hybrid_blend 0.968, Jaro-Winkler 0.963, vanilla 0.961,
semantic 0.958, **regression_v1 0.924** (least robust). The losses are real but modest across
the board — this metric does *not* strongly separate the matchers and should not be oversold.
Its one honest signal: the trained baseline gives up the most when the transliteration
standard is unseen, which is the expected cost of having been fit to named standards.

**Fairness, sliced by name-origin group.** F1 per group, and the max gap:

| matcher | russified | zade | soy | li | organization | max gap |
|---|---|---|---|---|---|---|
| **phonetic** | **0.916** | **0.901** | 0.879 | **0.925** | **0.975** | 0.097 |
| regression_v1 | 0.859 | 0.833 | **0.917** | 0.875 | 0.813 | 0.103 |
| hybrid_blend / cascade | 0.833 | 0.816 | 0.868 | 0.815 | 0.789 | 0.079 |
| lexical | 0.828 | 0.797 | 0.868 | 0.815 | 0.774 | 0.094 |
| lexical_jaro_winkler | 0.814 | 0.803 | 0.841 | 0.792 | 0.765 | 0.076 |
| phonetic_vanilla | 0.813 | 0.783 | 0.824 | 0.777 | 0.771 | **0.054** |
| semantic | 0.827 | 0.784 | 0.837 | 0.798 | 0.809 | **0.053** |

Read this column carefully, because the naive reading is wrong. The **smallest gaps belong to
`semantic` (0.053) and `phonetic_vanilla` (0.054)** — but they are uniform by being uniformly
weak, at 0.77–0.84 everywhere. The normalized phonetic matcher has a *larger* gap (0.097)
while scoring **0.879–0.975 — higher than every other matcher in every single group**. Its
spread is wide only because its ceiling (organization, 0.975) rises further than its floor.

> **Equal-outcome parity and per-group quality are different things, and on this benchmark
> they rank the matchers in opposite orders.** If the compliance question is "does any group
> get systematically worse service", the answer favours the phonetic layer: every group is
> better off under it. If the question is strictly "is the spread narrow", the weakest
> matchers win it by being bad everywhere.

Among comparably strong matchers, the group that is consistently hardest is **`national_li`**
(vowel-harmony `-li` family-suffix names) for the lexical family, and organization names are
the easiest for phonetic. A raw lexical matcher would systematically under-serve one
ethnic-morphology group — a real compliance concern.

**Cost** is parametric: `ECT = P(FP)·c_FP + P(FN)·c_FN`; the ratio is an input and no absolute
monetary value is claimed. At **1:1**, regression_v1 (**0.151**) is cheapest, then normalized
phonetic (0.315), hybrid_blend (0.383), hybrid_cascade (0.393), lexical (0.425), semantic
(0.430), Jaro-Winkler (0.436), vanilla (0.443). At asymmetric ratios (**10:1**, **100:1**) a
degenerate strategy takes over — most matchers drive the threshold to 0, i.e. *"accept
everything, never miss"* — and only **regression_v1** (0.355 / 0.374) and **semantic**
(0.439) retain a non-trivial operating point.

**Latency**, mean µs per pair, relative to the fastest:

| matcher | µs/pair | ×fastest |
|---|---|---|
| lexical (Jaro-Winkler) | 0.3 | 1× |
| lexical (token-set) | 1.3 | 4× |
| phonetic (vanilla) | 2.7 | 9× |
| hybrid_cascade | 14.5 | 48× |
| phonetic (normalized) | 22.7 | 76× |
| hybrid_blend | 24.6 | 82× |
| regression_v1 | 184.7 | 616× |
| **semantic (mBERT)** | **16,318.1** | **~54,000×** |

The embedding is ~54,000× slower than the fastest lexical matcher and **~719× slower than the
normalized phonetic layer** — while scoring below it on F1 (0.720 vs 0.754), on ROC-AUC (0.422
vs 0.612), and on every per-group F1.

---

## 8. The three findings, in full

**Finding 1 — cross-script divergence is the easy part.** Contrary to the field's intuition,
on all three cross-script cells *every* matcher scores 0.855–0.946 F1, and a simple phonetic
normalization step handles it cleanly (0.899–0.946). The problem is real, but it is largely
solved by cheap means. The industry over-weights it.

**Finding 2 — the hard part is same-script confusable identities.** Hard negatives such as
name-order swaps and father/son patronymic collisions, where surface similarity is high but
the identities differ. Every zero-shot matcher collapses to ~0.44 F1 there and accepts
essentially all **445** hard negatives as matches. Only RegressionV1 — trained on labelled
hard negatives, on an entity-disjoint split so this is generalization and not memorization —
separates them: **34** false positives, 0.860 overall F1, 0.757 on the same-script cell.
The operational implication is concrete: **separating real-world lookalikes cannot be done
from string features alone. It requires labelled examples of the confusions you care about.**

**Finding 3 — cheap explainable phonetics beat a generic neural embedding.** The multilingual
sentence embedding wins on no accuracy axis. It catches cross-script positives well (only 7
cross-script false negatives) but does not discriminate hard negatives at all (precision
0.565, accepting all 445), lands at ROC-AUC 0.422, and costs ~54,000× the fastest lexical
matcher and ~719× the normalized phonetic layer. The AZ-RU phonetic normalization — a few
lines of rule-based letter folding — beats it on F1, on ROC-AUC, on per-group F1 in every
group, and on speed. The production lesson: **prefer a small domain-specific transform over a
large generic model for short-name matching, and reserve the learned component for the part
that genuinely needs it — hard-negative discrimination, where a plain logistic regression
already does the job.**

---

## 9. Limitations, and what this does *not* contribute

- **Synthetic distribution ≠ real frequency.** Components are invented; per-cell and
  script-pair proportions are engineered for evaluability, not prevalence. Absolute F1 values
  are an **upper-bound proxy on this controlled distribution**, not a production guarantee.
- **Rule-based transliteration** captures each standard's salient divergences, not every
  edition byte-for-byte.
- **Suffix-transition positives** (`Əliyev` ↔ `Əlizadə`) are a stated modeling assumption about
  geopolitical name variation, not a universal truth. Treating them as the same identity is a
  design choice.
- **The homoglyph slice is a capability check** with bimodal recalls that read pass/fail, not
  a fine-grained ranking.
- **The trained baseline is not zero-shot.** RegressionV1's advantage partly reflects that it
  was fit on a labelled split while the others were not. The split is entity-disjoint, so the
  advantage is not memorization — but the fair reading is *"training on hard negatives is what
  separates them"*, not *"this algorithm is universally superior"*.
- **ECT is parametric**; no absolute monetary cost is claimed.
- **The accidental-real-name denylist guard is not exhaustive** — it reduces, does not
  eliminate, collisions. The data is otherwise 100% synthetic with no PII.

This is a **resource and empirical contribution, not a methodological one.** It introduces the
first reproducible benchmark for AZ-RU-EN cross-script name matching, plus three measured
findings that revise the prior expectation about where the difficulty lies. **It does not
propose a new matching algorithm.**

---

## 10. Reproducibility — one command regenerates everything

The full reference run is reproduced from zero with a single command, and every result in this
report is regenerated by it. A regression test locks the dataset to be byte-identical across
processes, hash seeds, and re-serialized configs.

```bash
uv sync --extra matchers --extra plots   # dependencies
uv run aznamematch generate              # frozen v1.0 dataset, seed 20260618
uv run aznamematch block                 # blocking: RR / PQ / PC
uv run aznamematch bench                 # all matchers -> results/
bash scripts/reproduce.sh                # all of the above, end to end
```

**License:** MIT, code and data. **Data:** 100% synthetic — no real persons, no PII.

**Standards cited, never invented:** BGN/PCGN, ALA-LC, ISO 9, ICAO Doc 9303, GOST 7.79 for
transliteration; Unicode TR39 for homoglyphs. **Corruption paradigm:** FEBRL (2008), GeCo
(2013), pseudopeople (2024). **Production baseline:** OpenSanctions nomenklatura RegressionV1.

It is precisely this discipline — every number regenerable from the seed, none hardcoded —
that lets this report claim honest numbers rather than opinions.

---

*Repository: [github.com/ShahinHasanov90/aznamematch](https://github.com/ShahinHasanov90/aznamematch)
· Full result tables: [`results/SUMMARY.md`](../results/SUMMARY.md)*
