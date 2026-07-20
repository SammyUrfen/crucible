# PLAN.md — Crucible architecture contract

> **Read this first.** This is the frozen decision record for Crucible. It is the contract a future
> build session (human or Claude) must honor. Prose explanation lives in `docs/`; this file is the
> *what was decided and why it may not silently change*. Status: **planning complete, build not
> started.**

Crucible is a **local, single-user "teach then test" workbook** for one advanced engineer. It teaches
a primitive, forces effortful retrieval/reconstruction, and grades the answer with a **hybrid** engine
— deterministic checks where a machine can decide, a reference-grounded **LLM-judge** only for design
reasoning — assessing at Bloom **Analyze/Evaluate/Create** ("name the rejected alternative + the
failure mode + a number, or the answer fails"). Domains: **Go**, **Python/FastAPI internals**, **deep
system design / cloud / DevOps**, and **defend-and-extend case-studies from his own repos**.

---

## 1. Locked stack decisions

| Axis | Decision | Rationale |
|---|---|---|
| Engine language | **Python** (FastAPI) | Deepest language; content-orchestration + LLM-grading fit. Ship the tool fast — the *content* is the real project. |
| Interface | **Local web app** (FastAPI + light web UI); CLI runner for the earliest slices | Room for an editor pane, per-criterion feedback, mastery heatmaps. |
| Grading | **Hybrid per question-type** | Deterministic where a computable oracle exists; LLM-judge only for design essays / explain-backs. |
| First vertical slice | **Go concurrency-discrimination module**, end-to-end | His genuine gap, tied to `conclave`; exercises all three grading strategies at once. |
| Persistence | **SQLite**, append-only attempt log + materialized mastery fold | Event-sourced, replayable, deterministic. |
| Deliverables | **Local files only** | Per his standing rule — nothing published to claude.ai. |

## 2. Binding resolutions (R1–R10)

A first-draft synthesis was adversarially critiqued; the critique found real defects. These
resolutions are the corrected plan and **override** any contradicting text in `RESEARCH/`. Full
reasoning: `RESEARCH/_synthesis.md` (first draft) and `RESEARCH/_critique.md` (the review).

- **R1 — The LLM-judge is HOSTED, not offline.** `claude -p` (Claude Code headless) and the Anthropic
  Messages API are both **network calls to Anthropic's hosted models, metered in USD**. The plan must
  never call the judge "offline/local/self-hosted." Consequences: a per-lesson + per-session **USD
  cost ceiling** with `total_cost_usd` tracking; a **network-down fail-open** path (self-grade against
  the shown reference at LOW confidence, never hard-fail); a genuinely-local model (Ollama) is an
  *optional, materially weaker* alternative that would require re-baselining trust. Everything else in
  Crucible (content, deterministic grading, mastery store) is genuinely local/offline — only the
  design-judge is not.
- **R2 — Content-first pilot BEFORE the infra.** The #1 risk is building the fun platform instead of
  studying. Phase 0 is a pilot: **10–15 hand-authored Go lessons** (tied to conclave), graded with
  plain `go test`, **used daily for 2+ weeks** to prove learning value — *before* the sandbox /
  anti-gaming / mastery machinery. The engine is earned by demonstrated daily use.
- **R3 — v1 sandbox descoped to plain local execution.** v1 runs learner code with plain local
  `go test` / `pytest` + wall-clock timeout + `ulimit`. It is **his own code on his own machine —
  near-zero RCE threat.** The hardened container (rootless + seccomp + gVisor + cgroups) is deferred
  to when **AI-authored or shared** content exists. When hardened, first solve the Go **no-network
  module-cache** problem (pre-baked `GOMODCACHE`, `-mod=vendor`, `GOPROXY=off`) and **panic/compile
  source-leak scrubbing**.
- **R4 — Race/nondeterminism oracles are probabilistic, not clean.** `go test -race` has **false
  negatives**; Go **randomizes map iteration**. So `predict_race_verdict` runs **many iterations** and
  is reported as probabilistic, and the "reject if stdout differs across two runs" nondeterminism
  check is unsound (use N≫2 runs + static flagging of map-range/goroutine/time/float patterns). Do not
  overclaim determinism here.
- **R5 — Explicit latency + cost budgets.** Grading latency (container/compile + 3–5× hosted-judge
  round-trips) can dominate a 25-min session; daily-driver friction is the top abandonment predictor.
  Warm/persistent runner + cached builds, **cap judge sampling at 3 with early-stop on agreement**,
  parallelize samples, grade code **asynchronously**, track grading-latency p50/p90/p99 as a
  first-class metric, and alarm on a per-session USD ceiling.
- **R6 — Orchestrate over external labs; don't re-implement them.** Reuse **MIT 6.824**,
  **Maelstrom / Gossip Glomers**, **CodeCrafters** for code + distributed *conformance*. Crucible's
  unique value is the **design-defense judge on his own repos + spacing/interleaving + mastery/θ
  tracking + the rejected-alternative rubric**. Hand-roll a grader only where no external one exists.
- **R7 — Right-size anti-gaming.** The grade's only value is accurate self-knowledge, which he *wants*;
  he controls every tunable anyway. Keep only the two near-free structural guards —
  **reference-grounding** and **deterministic-wins** (judge may only lower/flag, never raise a test
  verdict). **Defer** the gold-set-reproduction harness and retry-trace machinery until there's
  evidence he'd game it. The real failure mode is disengagement + lenient-judge false confidence, which
  the two cheap guards already cover.
- **R8 — Add four question types** the first taxonomy missed: **paper/reading-comprehension**
  (llm_judge), **capacity / back-of-envelope numeric-with-tolerance** (deterministic, worked-formula
  oracle), **refactor-to-idiomatic** (llm_judge), **benchmark-reproduction** (hybrid).
- **R9 — Mastery precision.** The behavioral mastery **gate is a discrete unlock latch**; a continuous
  **θ** drives *review scheduling*; a decayed θ schedules review but **does NOT re-lock** a passed
  module. Add a **prereq-propagation prior**. **Half-life** governs review *timing*; **θ-decay** governs
  the *ability estimate* — no double-penalty for one forgetting event. Composite items update **each
  objective's skill θ from its own per-criterion sub-score**; a hard-gate failure is attributed to the
  correctness skill only. **`recompute_from_log()` replays SCHEDULER arithmetic from stored grades — it
  does NOT re-grade.** Retuning a rubric or swapping the judge model invalidates stored grades and needs
  a (non-free, non-deterministic) re-grade pass.
- **R10 — Content aging is a maintenance model.** Pinned toolchains age; a bump can turn dozens of green
  lessons red at once. Ship **changed-only / incremental gate execution**, **per-track toolchain pins**,
  and a periodic "**gate against latest toolchain**" job.

## 3. Non-negotiable invariants

1. **Gradeability by construction.** The executable green-gate runs every reference answer/solution and
   rejects any lesson with an orphan objective, a non-reproducing reference, a fake debug-bug, or a
   rubric its own gold answer can't clear. A broken lesson **cannot** be committed. (This is his numeric
   anti-fabrication guard generalized to teaching content.)
2. **Deterministic-wins.** The LLM-judge may only lower or flag a grade, never raise a deterministic
   (tests/exact-match) verdict. Correctness is decided by tests; the judge grades only what tests can't
   see.
3. **Numbers over adjectives.** Grades are per-criterion breakdowns with evidence; progress is σ(θ), a
   Brier calibration score, first-try pass rate, and p50/p90/p99 latency — never a "you're doing great"
   bar. Every module carries a **Limitations** note naming what it does *not* prove.
4. **Value order in the arithmetic.** Correctness > Reliability > UX > Maintainability > Performance —
   a fast solution failing a fault-injection invariant scores below a slower correct one.
5. **Graceful degradation.** An unreliable model (judge) or tool never hard-fails the session; it
   degrades with a surfaced reason (fail-open, quarantine).
6. **Local only.** Nothing is published to claude.ai; the dashboard is a local file.

## 4. Architecture-contract clause (do not silently rename)

Once build starts, treat these identifiers as a stable vocabulary — do **not** silently rename modules,
columns, or functions across sessions: the grading `strategy` values (`deterministic_choice`,
`deterministic_output`, `hidden_tests`, `llm_judge`), the normalized grade **envelope**
(`{score, max, verdict, per_criterion, evidence, confidence, grader_id, logs}`), `recompute_from_log()`,
the lesson `schema_version` / `content_rev` fields, and the `θ` / half-life / `due_at` mastery triple.
If a rename is genuinely needed, change it here first with the reason, then propagate.

## 5. Document map

`README.md` (index) · `docs/00-vision.md` · `docs/01-pedagogy.md` · `docs/02-features.md` (feature
spec) · `docs/03-architecture.md` · `docs/04-grading.md` · `docs/05-content-model.md` ·
`docs/06-progress-model.md` · `docs/07-landscape.md` · `docs/09-roadmap.md` ·
`docs/curriculum/{go,python,system-design,project-design}.md` · `RESEARCH/*.md` (raw research,
incl. `_synthesis.md` + `_critique.md`) · `content/examples/go04-concurrency-discrimination.yaml`
(canonical lesson schema).
