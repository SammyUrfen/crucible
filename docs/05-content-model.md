# 05 — Content Model, Question Taxonomy & the Executable Green-Gate

This doc defines how a Crucible lesson is stored, what a lesson may assess, and the two-layer gate that makes a **broken or ungradeable lesson impossible to commit**. The canonical schema and a full worked example live at [`../content/examples/go04-concurrency-discrimination.yaml`](../content/examples/go04-concurrency-discrimination.yaml); every field named below is that file's field, not an invented parallel schema. Grading strategy internals and the hosted judge live in [`04-grading.md`](04-grading.md); the phased build order (content-pilot first) lives in [`09-roadmap.md`](09-roadmap.md).

## 1. Content-as-data: YAML source, JSON runtime

A lesson is one file per lesson under `content/<track>/<id>.yaml`, compiled to `build/<id>.json` at gate time. Git is the version store; there is no content database.

**Why YAML source → JSON runtime, and the named rejected alternatives.** A lesson co-locates embedded code — Go reference solutions, `predict_output` programs, inline SVG figures — as multi-line literals. YAML block scalars (`|`, `>`) carry backslashes, quotes, and newlines verbatim; his own `dsa-workbook/AUTHORING.md` flags JSON string-escaping of embedded code as the concrete pain point that made authoring miserable. So YAML wins for the *human-authored* artifact. But YAML has no fast, formal, tool-checkable shape contract, and a hand-edited YAML runtime would let two representations drift. So JSON wins for the *runtime* artifact: `ajv` validates it against a declarative JSON Schema in milliseconds, and the runtime loads it with no YAML parser in the hot path. **Rejected: a content database** (opaque, un-diffable, un-reviewable — you cannot `git blame` a row or PR-review a schema migration). **Rejected: Markdown-with-front-matter** (cannot express the executable grading spine — a hidden-test battery, a rubric, a reference solution the gate must run). The compile step is *inside* the gate, and `build/` is either gitignored or asserted to match a fresh compile, so no one can edit the JSON and silently diverge from source.

## 2. The lesson schema, field by field

Reference the go04 example as you read this.

- **`schema_version`** (int) — bumped only on a *breaking* field change. The gate refuses an unknown or newer version rather than guessing. This is the PLAN.md "architecture contract" habit applied to content: a breaking change requires an explicit migration + version bump, never a silent rename.
- **`id`** (kebab, globally unique) — MUST start with `<tag>-` (e.g. `go04-...` under tag `go04`). The gate enforces the prefix so ids stay locally sortable and collision-resistant.
- **`tag`** — the short module handle used as the id prefix and for cross-lesson references.
- **`track`** (e.g. `go`, `python`, `systems`) — routes the lesson to its track directory and, per R10, to its **toolchain pin**.
- **`toolchain`** (per-track/per-lesson pin) — the compiler/library versions the lesson's executable material was authored and gated against (e.g. `go: "1.22"`, `pydantic: "2.x"`, `pion: "<rev>"`). Pinned because a toolchain bump can turn dozens of green lessons red at once; see §6.
- **`content_rev`** (int) — bumped on *any* content edit (not just breaking ones). It is how [`06-progress-model.md`](06-progress-model.md) knows a graded attempt was against a now-superseded lesson; git remains the actual diff store.
- **`prerequisites`** (list of ids) — the prereq DAG edges. The gate asserts each referenced id exists (referential integrity), so a dangling prereq cannot ship.
- **`altitude`** (`on_ramp | ramp`) — encodes the per-language asymmetry. Go modules start `on_ramp` (scaffolded) then move to `ramp` (from-scratch primitives under `go test -race`); Python is `ramp`/deep from day one. The field is load-bearing: grading the two tracks identically would either bore him in Python or drown him in Go.
- **`priority`** (`attack | moderate | review | meta`) — authoring intent, consumed by the scheduler.
- **`summary`** — one-paragraph framing (a block scalar), stating what the *skill* is, not what the topic is.
- **`learning_objectives`** — each is `{ id, bloom, text }`. `bloom` targets Analyze/Evaluate/Create, never Remember. Objectives are the spine: **every objective id must be both taught and assessed** (§4, coverage-closure).
- **`teach`** — exposition blocks, each with a `heading`, a `body` block scalar, and a `covers: [objective-ids]` list. `covers` is what lets the gate prove no objective is taught-but-unassessed or assessed-but-untaught.
- **`worked_examples`** — `{ id, covers, prompt, solution }` — a shown-work bridge between teach and test; graded by nobody, but they carry `covers` too.
- **`assessments`** (**≥1 REQUIRED**) — the gradeable spine. Each has `id`, `type`, `covers`, optional `difficulty`, a `prompt`, and a `grading` block whose **`grading.strategy`** is the real discriminant (§3). Depending on strategy it also carries `options`, `reference_solution` + `tests` (hidden tests), `program` + `expected_output`, or a `rubric` + `reference_answer`. `union(assessments[].covers)` MUST equal the objective-id set.
- **`figures`** — a map of `id → { caption, svg }`. Same referential-integrity and no-hardcoded-colors rules as the DSA workbook: a `[[fig:...]]` token in a body with no matching figure fails the gate.
- **`limitations`** (block scalar / list) — names what the module does **not** prove (e.g. "an aiosqlite-green test says nothing about asyncpg concurrency; a single-node lab is not production-grade"). This is a first-class field, not a footnote — it feeds the per-module Limitations panel and keeps claims calibrated.

## 3. Question-type taxonomy → grading strategy

Ten authored question types collapse onto **exactly three grading engines**. The discriminated union is on `grading.strategy`, **not on `type`** — so the grader and the gate's per-type structural checks each have three branches with a thin per-type adapter on top, and adding a type never touches the router. The four types marked **(R8)** were missing from the first taxonomy and are added here.

| Question type | `grading.strategy` | How graded | Gate's per-type structural check |
|---|---|---|---|
| `mcq` | `deterministic_choice` | exact match to the single `correct: true` option; no model call | exactly one `correct:true`; every option carries a non-empty `why` (kills giveaway distractors); `reference_answer` == correct text |
| `multi_select` | `deterministic_choice` | set-equality (`partial_credit: all`) or `jaccard` overlap | ≥1 correct and ≥1 incorrect (rejects degenerate all-true/all-false); `reference_answer` == correct set |
| `predict_output` | `deterministic_output` | run `program` with `runner`; match learner stdout to **derived** `expected_output` | executes program; asserts stdout == `expected_output`; `match ∈ {exact, trimmed, regex}` |
| `predict_race_verdict` (Go) | `deterministic_output` | run under `go test -race`, compare the verdict — **probabilistic, see R4 below** | runs the snippet under `-race` over N≫2 iterations; nondeterminism statically flagged |
| `capacity_estimate` **(R8)** | `deterministic_output` | back-of-envelope numeric derivation, compared with tolerance to a worked-formula oracle | executes the formula; asserts learner value within tolerance band |
| `code_completion` | `hidden_tests` | fill a starter stub; run vs visible + hidden tests in the sandbox | executes `reference_solution` vs ALL tests (green or reject); ≥1 visible & ≥1 hidden; leak-guard |
| `code_from_scratch` | `hidden_tests` | hidden tests + property/differential tests decide; optional advisory `llm_review` at `weight_of_style: 0.0` | executes `reference_solution` (must pass all); `llm_review` never overrides tests |
| `debug_this` | `hidden_tests` | learner fixes provided `buggy` code until green | runs `buggy` (must FAIL ≥1 test — a fake bug is rejected) AND `reference_solution` (must pass all) |
| `benchmark_reproduction` **(R8)** | `hidden_tests` **+** `llm_judge` | deterministic harness emits p50/p99; judge grades the written defense | harness runs; reference defense clears its own rubric |
| `short_answer` / `definition` | `llm_judge` | cheap `keyword_must`/`keyword_must_not` first, fall through to a one-criterion rubric | `reference_answer` satisfies keyword guard AND clears rubric |
| `explain_tradeoff` / `design_essay` | `llm_judge` | weighted-criteria rubric + locked `reference_answer`; `anti_reward_hacking` (`min_words`, `penalize_if_contains`) | weights sum to 1.0; reference clears its own rubric; anti-hacking fields present |
| `refactor_to_idiomatic` **(R8)** | `llm_judge` | rubric grades idiom fidelity against a reference refactor | reference clears its own rubric |
| `paper_reading` **(R8)** | `llm_judge` | reference-grounded comprehension of DDIA/Raft/Dynamo/Spanner; the distributed track rests on these | reference clears its own rubric |
| `critique_design` | `llm_judge` | rubric rewards naming the flaw AND proposing a concrete better alternative | ≥2 criteria; reference clears its own rubric |
| `feynman` / `explain_back` | `llm_judge` | rubric scores analogy fidelity + "no error introduced by the simplification" | a "no-error-from-simplification" criterion present; weights sum to 1.0 |

**R4 caveat, stated plainly.** `predict_race_verdict` is **not** a clean deterministic oracle. `go test -race` reports only interleavings it actually observes (false negatives), and Go randomizes map-iteration order. The example lesson's race item must be described as **probabilistic** — run over N≫2 iterations with reliably-tripping race constructions, with map-range/goroutine/time/float nondeterminism statically flagged — and its verdict reported *as* probabilistic, never as "the cleanest signal." The `predict_output` gate likewise rejects any program whose stdout differs across two runs, or forces `match: regex`/normalized compare; otherwise the anti-fabrication guarantee quietly breaks.

## 4. The two-layer green-gate

`make gate` is the definition of done. It exits non-zero on any **error** and prints **warnings** non-blocking — the exact errors-vs-warnings split of his `validate.mjs`. It is his numeric set-containment anti-fabrication guard **generalized from résumé bullets to teaching content**: correctness is proven *by construction*, with zero LLM in the pass/fail path.

**Layer 1 — declarative JSON Schema (`ajv`), for shape.** Field presence, types, enums, required keys. This is the fast formal artifact. But a JSON Schema **cannot execute a reference solution, cannot diff a coverage graph, cannot check that a bug actually fails.** Those are the interesting guards, and they cannot live here.

**Layer 2 — a procedural validator (a `validate.mjs` sibling), for what a schema cannot express.** Six invariants:

1. **Gradeable-or-reject** — a lesson with zero assessments cannot be committed.
2. **Coverage-closure** — `union(assessments[].covers)` must equal the declared objective-id set, **and** every objective must be taught by ≥1 `teach`/`worked` block via `covers`. An orphan objective or an orphan assessment fails.
3. **Reference-reproduces** — every `predict_output` `program` is executed and its stdout must equal `expected_output` (outputs are machine-**derived**, never hand-typed); every `hidden_tests` `reference_solution` is executed and must pass **all** tests.
4. **Debug-this-buggy-must-actually-fail** — `debug_this` additionally runs the `buggy` code and asserts it **fails ≥1 test**. A fake or no-op bug is rejected.
5. **Rubric-passes-own-reference** — every `llm_judge` assessment ships a non-empty `reference_answer`; the gate runs the judge on that gold answer and it must score ≥ `pass_threshold` and satisfy `keyword_must` / violate no `keyword_must_not`. A rubric its own gold answer cannot clear is broken.
6. **Leak-guard** — a string-containment check that no hidden test's input/expected appears in the visible `prompt` or `starter`.

**Rejected: schema-only validation** (cannot execute a reference or diff a coverage graph). **Rejected: trusting the authoring LLM's self-report** that a lesson is fine — that is precisely the reward-hacking surface the gate exists to remove. An optional Playwright render-QA pass (missing-figure sentinels, dark/light, console errors) is the second gate, mirroring `qa.mjs`.

> One honest cost, per R1: invariant (5) runs the **hosted** LLM-judge — a network call to Anthropic's models metered in USD, not an offline check. The gate therefore has a per-lesson cost ceiling and `total_cost_usd` tracking, and on a network-down authoring run it degrades to a shape-only pass with the rubric-self-check marked *pending*, rather than hard-failing. The other five invariants are genuinely local.

## 5. AI-authoring pipeline (DEFERRED per R2)

The pipeline scales content authoring **without weakening the gate**, but it is explicitly **not built first**. Per R2, the roadmap leads with a **content pilot**: 10–15 hand-authored Go lessons graded by plain `go test`, used daily for 2+ weeks to prove learning value. The elaborate authoring engine is *earned* by that proven daily use — building the fun platform instead of studying is the #1 risk.

When built, it is a bounded self-repair loop:

1. **Skeleton** — an LLM converts one source note into a lesson draft against the pinned schema contract.
2. **Structural preflight (no LLM)** — parse + shape + gradeable-or-reject + coverage-closure; a draft missing an assessment or with an orphan objective bounces back with the specific failure as feedback.
3. **Executable materialization** — run every `predict_output` program and every `reference_solution` in the sandbox; non-reproducing gold answers bounce back with the runner output as the repair prompt.
4. **Rubric self-consistency** — run the judge on each `reference_answer`; a gold answer that can't clear its own rubric bounces.
5. **Adversarial audit** — a red-team LLM tries MCQ-by-elimination (flags giveaway distractors), finds teaching claims with no assessment, and flags non-discriminating items. Findings are **advisory warnings only**.
6. **Merge** — only lessons green on the deterministic gate are committed; `content_rev` bumped.

The loop is **bounded to N=3 retries, then QUARANTINE** to a review queue — never hard-fail the batch. A run of 200 auto-authored drafts never silently ships a broken one, and never drops a salvageable one either (graceful degradation with a surfaced reason). Only **two errors block commit**: "no gradeable assessment" and "reference answer does not reproduce." Everything else is a warning.

## 6. Content aging (R10) — a maintenance model, not a footnote

Pinned toolchains age: a Go, pydantic-v2, SQLAlchemy-2.0, or pion bump can turn dozens of green lessons red simultaneously. Three mechanisms keep the corpus honest:

- **Per-track toolchain pins** — the `toolchain` field records exactly what each lesson was gated against, so a red lesson's cause is unambiguous (its pin vs the installed toolchain), not a mystery.
- **Changed-only / incremental gate execution** — the routine `make gate` re-runs the executable layer only for lessons whose `content_rev` (or whose toolchain pin) changed since the last green run, keeping the daily gate fast; a full-corpus run is reserved for toolchain changes.
- **Periodic gate-against-latest-toolchain job** — a scheduled run gates the whole corpus against the *newest* toolchain (not the pins), surfacing lessons that will break on the next bump *before* they block a study session. Failures here are a maintenance queue, not a study-time surprise.

## Limitations / open questions

- **The gate proves gradeability, not pedagogical depth.** Coverage-closure can be satisfied by declaring a trivially-assessable objective; the adversarial-audit stage is the only counter, and it is advisory. A determined author can still ship shallow-but-green content.
- **Rubric quality is the soft underbelly.** `rubric-passes-own-reference` proves a gold answer clears the bar, not that the bar discriminates. Budget periodic human spot-audits of judge scores against a held-out hand-graded set — his A/B instinct applied to the grader itself.
- **`predict_output` / `-race` nondeterminism** (dict ordering, timestamps, floats, scheduler) can defeat the derived-expected guarantee; the two-run reject and the R4 iteration/static-flag hardening reduce but do not eliminate flakiness.
- **Open: language scope.** Python-first for the sandbox runner, or multi-language (Go/C++/Java) from day one? Multi-language multiplies the sandbox and harness surface; recommend Python/Go-first with the runner as a swappable seam.
- **Open: track granularity.** One flat namespace with a `track` tag, or per-track directories with their own module tables and source-note cross-checks? The latter buys per-track validation but costs structure.
- **Open: learner state boundary.** This schema is content-only; attempts, θ, and scheduling belong to a separate store keyed by `assessment_id` — see [`06-progress-model.md`](06-progress-model.md).
