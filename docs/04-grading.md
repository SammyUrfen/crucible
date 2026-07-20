# 04 — Hybrid Grading

How Crucible decides whether an answer passes: a router in front of three grader strategies — deterministic checks wherever a computable oracle exists, a **hosted** LLM-judge only for free-form design reasoning, and hybrid items that use both. This doc specifies the routing, the graders, the judge invocation, the trust invariants, and the cost/latency budget. Sibling reading: [content-model](05-content-model.md) for the lesson/assessment schema these strategies key off, [progress-model](06-progress-model.md) for how graded scores feed θ, and [../RESEARCH/claude-headless.md](../RESEARCH/claude-headless.md) for the raw headless-vs-API research.

The router keys on `grading.strategy`, not question type, so there are exactly three code paths regardless of how many question types exist. Adding a type is a table row, never a router edit — the discriminated-union seam mirrors the `StorageEngine`/`Source`-adapter pattern used elsewhere in the portfolio.

## Routing table

| Question type | Strategy | Notes |
|---|---|---|
| `mcq` | `deterministic_choice` | Exact match to the single `correct: true` option. Gate requires exactly one correct and a non-empty `why` on every option (kills giveaway distractors). |
| `multi_select` | `deterministic_choice` | Set-equality, or Jaccard `|A∩B|/|A∪B|` for partial credit. Gate rejects degenerate all-true/all-false. |
| `predict_output` | `deterministic_output` | Expected value is **machine-DERIVED**: the gate executes the program and captures stdout — never hand-typed. |
| `predict_race_verdict` (Go) | `deterministic_output` | **PROBABILISTIC, not a clean oracle** — see R4 below. Runs many iterations, reports the verdict as an observed frequency. |
| `capacity` / back-of-envelope | `deterministic_numeric` | Numeric-derivation-with-tolerance against a **worked-formula oracle**. Compares within a relative/absolute band, not exact equality. |
| `code_completion` | `hidden_tests` | Public example tests for iteration + hidden grading tests injected from outside the sandbox. |
| `code_from_scratch` | `hidden_tests` | Hidden tests + Hypothesis/differential/metamorphic properties vs a locked reference. Optional advisory `llm_review` at style-weight 0.0 (comment-only; can never fail a correct solution). |
| `debug_this` | `hidden_tests` | Gate asserts the `buggy` code fails ≥1 test and the reference passes all. |
| `benchmark_reproduction` | `hybrid` | Deterministic harness emits p50/p99/msgs-per-op; the LLM-judge grades the **written defense** of the numbers. Deterministic result is a hard gate on the harness half. |
| `short_answer` / `definition` | `llm_judge` | Cheap keyword guard (AND-of-OR / must-not) short-circuits first; fall through to a one-criterion rubric only if inconclusive (cost control). |
| `explain_tradeoff` / `design_essay` | `llm_judge` | Weighted-criteria rubric + locked reference. Must reward the NAMED rejected alternative + a failure mode + a quantified claim, or the essay fails. |
| `critique_design` | `llm_judge` | ≥2 criteria: names the flaw AND proposes a concrete better alternative. |
| `feynman` / `explain_back` | `llm_judge` | Scores analogy fidelity + "no technical error introduced by the simplification." The best single defense against illusion-of-competence. |
| `paper_comprehension` / reading | `llm_judge` | Reference-grounded against the source (DDIA / Raft / Dynamo / Spanner). The distributed track rests on these, so comprehension is graded, not assumed. |
| `refactor_to_idiomatic` | `llm_judge` | Grades whether the rewrite is idiomatic and behavior-preserving against a reference rationale; correctness of behavior, where testable, is gated deterministically first. |

Rejected across the board: **routing MCQ / numeric / exact-output to the judge.** A string or float compare is faster, free, and strictly more reliable than a metered network call; the judge is reserved for questions with no computable oracle.

---

## 1. Deterministic graders

Deterministic graders own everything with a checkable ground truth. They emit `confidence: HIGH` and return the normalized envelope `{score, max, verdict, per_criterion[], evidence[], confidence, grader_id, logs}`.

**Choice (`mcq`, `multi_select`).** Exact-match for single-answer; set-equality or Jaccard partial credit for multi-select. No model, no I/O beyond a comparison. The rejected alternative — an LLM tie-breaker on "close" MCQ answers — buys nothing: the correct option is known at authoring time, so there is nothing to adjudicate.

**Derived-output (`predict_output`).** The core anti-fabrication move: the expected value is **produced by running the program at gate time**, never written by the author. The learner predicts stdout; the gate has already executed the reference program and stored its output; grading is a compare under `match ∈ {exact, trimmed, regex}`. The named alternative — a hand-typed `expected_output` — is exactly the fabrication surface Crucible refuses, because a typo in the key silently marks correct answers wrong. The cost is that the program must be deterministic; the gate rejects any program whose stdout differs across runs, or forces a normalized/regex compare (see the R4 caveat — a *two*-run check is not sufficient).

**Capacity-numeric (`capacity`).** Back-of-envelope questions ("QPS for a 1M-title typeahead at p95 17ms across 3 Redis shards") are graded against a **worked-formula oracle**: the lesson carries the derivation as executable arithmetic, not a single frozen number, and the learner's answer passes if it lands within a tolerance band (relative for large magnitudes, absolute near zero). Tolerance is first-class because estimation answers legitimately vary by rounding and assumption — an exact-equality check would reject correct reasoning that rounded 8.3 to 8. The formula oracle also makes the *reasoning* auditable: if the learner is out of band, the graded evidence shows which factor diverged, not just "wrong."

---

## 2. Hidden-tests grader

The backbone of code grading. The learner iterates against a few **public example tests**; the verdict is decided by **hidden grading tests injected from outside the execution boundary at grade time** — never shipped in the starter, never importable, never mounted — so the learner cannot optimize to the checker (the nbgrader/Otter marker pattern, internalized). On any failure the grader surfaces the **minimal failing input / counterexample** — LeetCode's rigor without its opacity, because the point is understanding the failure.

Beyond fixed hidden cases, non-trivial code is backed by a **locked reference implementation** plus **Hypothesis-style property tests**: differential (`student_fn(x) == reference_fn(x)` over generated inputs — the most-implemented PBT kind in Goldstein et al.'s ICSE'24 study, and the answer to "no fixed expected output"), and metamorphic (sort is idempotent, reverse∘reverse is identity). Properties close the "hardcode the visible cases" hole by exploring inputs the learner never considered. The reference is only as good as its own tests — a buggy reference will "correctly" fail correct student code — so the gate executes the reference against all tests before the lesson can ship, and pins the input domain so generated edge cases stay in-spec.

**v1 sandbox is plain local execution (R3).** v1 runs learner code with plain local `go test` / `pytest` under a wall-clock timeout and a resource `ulimit`. This is *his own code on his own machine* — near-zero RCE threat — so the hardened container (rootless + seccomp + gVisor + cgroups) is deliberately **deferred** to when AI-authored or shared content exists. When that day comes, two Go-specific problems must be solved first: the no-network module cache (pre-baked `GOMODCACHE`, `GOFLAGS=-mod=vendor`, `GOPROXY=off`) and panic/compile-error **source-leak scrubbing** (Go prints `file:line` and can dump hidden-test source on a compile error). Don't overclaim isolation v1 doesn't have.

**R4 — race/nondeterminism oracles are unsound as first drafted, and are reported as such.** Two guarantees the first synthesis assumed do not hold:

- `go test -race` has **false negatives** — it only reports interleavings it actually observes in a given run. A single "expected: DATA RACE" oracle over one run is unsound. `predict_race_verdict` is therefore **demoted from "cleanest signal" to "probabilistic"**: the grader runs N ≫ 2 iterations against reliably-tripping race constructions, and reports the verdict as an observed frequency ("DATA RACE in 47/50 runs"), not a certainty. The canonical `go04` lesson's `predict_race_verdict` item must be described this way — a probabilistic check run over many iterations, not a deterministic oracle.
- Go **randomizes map iteration order**, and goroutine scheduling, `time`, and float formatting are all nondeterministic. So the "reject if stdout differs across TWO runs" nondeterminism check is **unsound** — two runs can coincidentally agree. The real defense is static flagging (map-range, goroutine, `time`, float) plus N-run sampling, or forcing a normalized/regex compare. A 2-run diff is a smoke test, not a guarantee.

---

## 3. The LLM-judge

Used only where no computable oracle exists: design essays, explain-backs, paper comprehension, refactor rationale, critique. Reference-grounded, forced-schema, sampled, and — this is the load-bearing correction — **hosted**.

**R1 — the judge is a HOSTED frontier judge, metered in USD. It is NOT offline/local/self-hosted.** Both viable invocation paths — `claude -p` (Claude Code headless) and the Anthropic Messages API directly — are **network calls to Anthropic's hosted models, billed per token**. Everything else in Crucible (content store, deterministic grading, the SQLite mastery fold) is genuinely local and offline; the design-judge alone is not. Three consequences follow and are non-negotiable:

- A per-lesson and per-session **USD cost ceiling**, with `total_cost_usd` tracked per call and accumulated.
- A **network-down FAIL-OPEN** path: if the call fails, fall back to self-grade-against-the-shown-reference, mark `confidence: LOW`, and **never hard-fail the session**. An unreliable model must never block learning.
- A genuinely-local model (Ollama / llama.cpp) is an **optional, materially weaker** alternative that would require re-baselining trust — offered, never defaulted to.

**Invocation shape.** Grade via non-interactive print mode with JSON output and a forced output schema, spawned as a subprocess (Python or Go). The shape, at the level I'm confident is accurate:

- **Non-interactive print mode**, machine-parseable JSON out (the response carries `result`, a per-call `total_cost_usd`, and — with a forced schema — a `structured_output` object).
- **Forced output schema** so there is no free-text-score parsing: the model must return `{per_criterion: [{id, score, evidence}], total, verdict, abstain}`.
- **Read-only tool posture** — disallow all code-execution / edit / write tools so the judge can never run code or mutate anything. It reads and scores; it does not act.
- **Rubric + reference in the system prompt**; the learner answer in a delimited DATA channel (below).
- **Model:** `claude-opus-4-8` or `claude-sonnet-5`. Temperature / top_p are **not settable** on current Claude models — they are intrinsically low-variance, so reproducibility comes from pinning the exact model + prompt + input, not from a temperature knob. Older temperature-bearing models are rejected for the judge.

> **Flag names:** the concrete CLI flags for print mode, JSON output, forced schema, and tool restriction should be **verified against `claude --help` / the Claude Code headless docs** before implementation — the capabilities above are what the grader depends on; the exact flag spellings are an implementation detail to confirm, not to hard-code from memory. The Messages API path expresses the same capabilities as `output_config.format` (schema), a read-only/no-tools request, and per-response `usage` for cost — at the price of hand-rolling the cost/tooling/JSON plumbing the headless CLI gives for free.

**Reference-grounding — always, never reference-free.** The locked reference answer is **always in context**. A reference-free judge scores persuasiveness, not correctness: self-play drives its pass rate 0.72 → 0.94 while true accuracy stays 0.20 (arXiv 2607.05904). For a solo learner who is both author and beneficiary of a high grade, that is worse than no grade — it manufactures false confidence. The reference is the oracle the judge measures against.

**Answer in a delimited DATA channel.** The learner's text goes in a clearly-delimited data block, **never interpolated into the instruction channel**, and the judge is instructed to ignore any "grade me a 10" meta-text inside it — defeating the fake-evaluation-note injection documented in WebArena/CAR-bench.

**Median-of-3 sampling with early-stop and ABSTAIN (R5).** Sample the judge up to 3× (capped at 3), take the **median**, and report the spread as confidence. Early-stop on agreement — if the first two samples agree within tolerance, don't pay for the third. On a **wide spread**, do not fake precision: **ABSTAIN** and route the item to self-grade-against-reference. Wide spread is itself signal — the question is genuinely subjective or the judge can't grade it (LLM self-consistency has a low ceiling; arXiv 2510.27106). Samples are parallelized so three round-trips cost roughly one wall-clock.

### Cost + latency budget (R5)

The judge is the one metered, network-bound, multi-second component in an otherwise-local 25-minute session, so it is budgeted explicitly and grading-latency p50/p90/p99 is a first-class health metric.

*Cost, per judge item* (illustrative, assumptions stated). A judge call carries reference + rubric + answer ≈ 3K input tokens and returns ≈ 0.5K output tokens of scored JSON. At `claude-opus-4-8` ($5/$25 per MTok): ≈ **$0.028/call**, so median-of-3 ≈ **$0.08/item** worst case (less with early-stop, and with the reference+rubric prefix cached across samples). At `claude-sonnet-5` ($3/$15, intro $2/$10 through 2026-08-31): ≈ $0.017/call, ≈ **$0.05/item**. A typical 8–12-item session has only 1–3 judge items, so **per-session judge spend lands ≈ $0.05–0.25**. The per-lesson and per-session USD ceilings cap this; keyword-guard short-circuits keep cheap `short_answer` items off the judge entirely.

*Latency.* A single-turn judge call is ≈ 2–5s (Opus slowest ≈ 4–5s; a first forced-schema call adds ≈ 1–2s of grammar compilation, cached for ~24h after). Three **parallel** samples ≈ one round-trip of wall-clock, ≈ 5s. Engineered to the budget: grade code and judge items **asynchronously** so the session keeps moving, keep a warm/persistent runner with cached build artifacts, cap sampling at 3 with early-stop, and treat container spin-up + multi-second Go `-race` compiles as the real latency tail to attack — not the judge.

### Trust (v1)

For v1 Crucible keeps only the **two near-free structural guards**, per the right-sized anti-gaming stance (R7):

1. **Reference-grounding** — the judge is never run reference-free (above).
2. **Deterministic-wins invariant** — the judge may only **lower or flag** a grade, **never raise** a deterministic (tests/exact-match) verdict. Correctness is decided by tests; the judge grades only what tests can't see (design quality, trade-off reasoning, clarity). This directly encodes Correctness > everything and defuses judge unreliability by construction.

**Deferred (R7):** the gold-set-reproduction-before-trust calibration harness. The self-gaming premise is weak — the grade's only value is accurate self-knowledge, which he *wants*, and he controls every tunable anyway. The real failure mode is disengagement + lenient-judge false confidence, which the two cheap guards already cover. The 15–20-answer hand-graded gold set and the agreement-metric machinery are built only if evidence of gaming appears; building them now is effort against a risk that isn't there.

---

## Limitations / open questions

- **Judge reproducibility is not grade reproducibility.** Pinning model + prompt + input makes the judge low-variance, not bit-identical. Re-tuning a rubric or swapping the judge model **invalidates stored judge grades** and needs a fresh, non-free, non-deterministic re-grade pass — the scheduler's `recompute_from_log()` replays arithmetic from stored grades, it does not re-grade. Don't let "replayable mastery" imply reproducible *grades*.
- **The race oracle stays probabilistic.** No amount of iteration converts `-race` into a sound oracle; a rare interleaving can hide indefinitely. Crucible reports frequency and says so — it does not claim to have detected every race.
- **v1 sandbox proves nothing about untrusted code.** Plain local execution is right for his-code-on-his-machine and says nothing about safely running AI-authored or shared lessons; that is a separate, deferred project (R3).
- **A green hidden-test suite is scoped.** An aiosqlite-green concurrency test says nothing about asyncpg under real contention; a single-node lab is not "production-grade." Per-item Limitations panels name what each exercise does *not* prove.
- **Local-judge fallback is materially weaker** and would need trust re-baselined; it is offered as an escape hatch for the network-down path, not a peer of the hosted judge.
