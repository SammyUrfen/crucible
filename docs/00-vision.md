# 00 — Vision

What Crucible is for, what it deliberately is not, and how we'll know it worked.

## Problem

A senior-level systems engineer — deep in Python/FastAPI/asyncio and C++ DB internals, with real
concurrency-correctness experience — has **one true gap (Go, at true-beginner level)** and wants to
push **past interview-level system design into cloud / DevOps / distributed internals**. He learns by
building and adversarial verification, dislikes rote recall, and demands the **WHY** plus the **named
rejected alternative**.

No existing tool fits. exercism and *A Tour of Go* grade too softly (toy suites); Anki and LeetCode
gate on rote content he dislikes; educative.io and roadmap.sh stop at interview depth with passive or
no grading; boot.dev wraps it in gamification he doesn't need. What's missing is a **teach-then-TEST**
workbook that:

- assesses at Bloom **Analyze / Evaluate / Create**, not recall;
- **auto-grades** via a hybrid of deterministic checks plus a reference-grounded LLM-judge;
- reports **numbers, not adjectives**; and
- is **trustworthy without external ground truth** — a broken or ungradeable lesson cannot even be
  committed.

## Goals

- **Teach then force retrieval.** Teach a primitive, then require effortful closed-book
  reconstruction (build it from a blank editor / re-derive the invariant). Gate the next module on a
  **behavior** — *builds the primitive from scratch + names the rejected alternative + states ≥1
  failure mode with a number* — not a percentage.
- **Hybrid auto-grading with a router.** Deterministic wherever a computable oracle exists (MCQ,
  derived output, hidden unit + property tests); a **hosted** Claude LLM-judge, always
  reference-grounded, *only* for free-form design reasoning. (The judge is a metered network call —
  see [`../PLAN.md`](../PLAN.md) R1 — not offline.)
- **Per-language altitude asymmetry.** Go starts as a scaffolded on-ramp then ramps to from-scratch
  primitives under `go test -race`; Python is deep and adversarial from day one. Grading the two
  identically would either bore him in Python or drown him in Go.
- **Value order in the arithmetic.** Correctness > Reliability > UX > Maintainability > Performance,
  encoded directly into rubric scoring — a fast solution that fails a fault-injection invariant scores
  below a slower correct one.
- **Gradeability by construction.** An executable green-gate runs every reference answer/solution and
  rejects any lesson with an ungradeable objective, a non-reproducing reference, a fake debug-bug, or a
  rubric its own gold answer can't clear.
- **Numbers as first-class output.** Mastery heatmap σ(θ), model-calibration Brier score, first-try
  pass rate, grading-latency p50/p90/p99, msgs/op where the primitive supports it.
- **Content before cathedral.** Prove daily use with a small hand-authored pilot before building the
  grading engine (see [`09-roadmap.md`](09-roadmap.md)).

## Non-goals

- **NOT a flashcard app.** FSRS spaced repetition is a thin adjunct capped to genuinely-rote Go
  idioms/stdlib signatures he keeps re-looking-up. **Design judgment never enters the scheduler** — it
  would train verbatim recall and crowd out transfer.
- **NOT a multi-user LMS.** No accounts, no auth, single learner. **No gamification** (XP / streaks /
  boss-battles); streaks never gate scheduling (that rewards cramming).
- **NOT interview-level rehearsal.** Design modules are gated on a distributed-internals / cloud /
  DevOps depth bar, rejecting educative/roadmap.sh-grade contamination.
- **NOT from-scratch Kubernetes or Terraform.** Build the primitive only where the primitive *is* the
  learning target (a container runtime from namespaces + cgroups: yes; a whole orchestrator: no). Use
  **real** Kafka / Postgres / K8s and study their internals; reuse **Maelstrom / 6.824 / CodeCrafters**
  as graded labs rather than re-implementing them.
- **NOT a hosted product, and nothing published.** Everything is local files; per his standing rule
  nothing goes to claude.ai. *Caveat (R1):* the LLM-judge itself is a hosted Anthropic API call — the
  workbook is local-first **except** for that one component, which needs network and costs metered USD.

## Success criteria

- **Content pilot earns daily use.** ~12 hand-authored Go lessons (graded with plain `go test`) are
  used daily for 2+ weeks and demonstrably teach — *before* any engine is built.
- **Vertical slice runs end-to-end.** The Go concurrency-discrimination module runs teach → test →
  grade → schedule, exercising all three grading strategies (deterministic MCQ, hidden-tests
  `go test -race`, LLM-judge explain-it-back) in one module.
- **Structural guarantee holds.** A lesson with an orphan objective, a reference solution that fails
  its own hidden tests, a `debug_this` whose buggy code doesn't actually fail, or a rubric its gold
  answer can't clear — **cannot be committed**.
- **Deterministic-wins is provable.** The judge can only ever *lower* or flag a deterministic verdict,
  never raise it.
- **Honest numbers.** Every module's Limitations panel names what the exercise does *not* prove (a
  green aiosqlite test says nothing about asyncpg concurrency; a single-node lab is not
  "production-grade").
- **Mastery is a deterministic replay.** `recompute_from_log()` reproduces live θ bit-for-bit after
  retuning any scheduler constant — noting (R9) that replay reproduces θ from *stored grades*; it does
  not re-grade.

## Limitations of this vision

Two things this document does **not** claim: that the workbook will be *fun* to build daily (the
abandonment risks in [`../RESEARCH/_critique.md`](../RESEARCH/_critique.md) are real and the roadmap is
ordered to fight them), and that the hosted judge is free or perfectly reliable (it is metered and
fail-open by design). Both are managed, not wished away.
