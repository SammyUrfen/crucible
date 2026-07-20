# 09 — Roadmap: phased build order

This doc fixes the order in which Crucible gets built. The governing decision (see
[`../PLAN.md`](../PLAN.md), R2) is that the **content pilot comes first** and the engine is
*earned* by proven daily use — not the reverse. The #1 failure mode for a systems builder is
finishing the fun part (the platform) and never sustaining the boring part (studying), so the
sequence below is deliberately hostile to that trap: no sandbox, no anti-gaming subsystem, and no
mastery fold until a hand-authored pilot has proven you actually open the thing every day.

Every phase pairs a concrete deliverable set with a **testable exit criterion**. Status is
`planned` throughout — nothing here is built yet.

## Must-decide before building

Seven things must be resolved on paper before Phase 0, because a wrong call on any of them
invalidates downstream cost, trust, or latency claims. Each is stated with the resolution already
taken in [`../PLAN.md`](../PLAN.md) (R1–R10); this list is the condensed version.

1. **The design-judge is hosted, not offline (R1).** `claude -p` and the Anthropic Messages API are
   network calls to Anthropic's hosted models, metered in USD. Do **not** ship anything that calls
   it "offline/local-first." The consequences are load-bearing: a per-lesson and per-session USD
   ceiling with `total_cost_usd` tracking, and a **network-down fail-open** path
   (self-grade-against-the-shown-reference, confidence `LOW`, never a hard session failure). A
   genuinely-local model (Ollama/llama.cpp) stays an *optional, materially weaker* alternative — it
   does not become the default. Everything else (content, deterministic grading, mastery store) is
   genuinely local.
2. **Content pilot before infrastructure (R2).** Prove daily use and real learning value on
   10–15 hand-authored lessons graded with plain `go test` before writing a single line of sandbox,
   anti-gaming, or Elo code. Building the cathedral for an unvalidated behavior is the top
   abandonment risk.
3. **Descope the v1 sandbox (R3).** v1 runs your own code on your own machine under plain
   `go test`/`pytest` + wall-clock timeout + `ulimit` — near-zero RCE threat. Defer the hardened
   container (rootless + seccomp + gVisor + cgroups) to Phase 7, when AI-authored content first
   creates a genuine untrusted surface.
4. **Fix race/nondeterminism soundness (R4).** `go test -race` has false negatives (it only reports
   interleavings it observes) and Go randomizes map iteration order. A single "expected: DATA RACE"
   oracle and a "reject if stdout differs across two runs" check are both **unsound**. Either harden
   (N≫2 iterations, reliably-tripping race constructions, static flagging of
   map-range/goroutine/time/float nondeterminism) or demote `predict_race_verdict` to
   *probabilistic, reported as such*. Do not overclaim determinism.
5. **Set latency + cost budgets (R5).** Container spin-up, multi-second Go compile/`-race`, and 3–5×
   hosted-judge round-trips can dominate a 25-minute session. Fix a per-item latency budget and a
   per-session cost ceiling up front, and engineer to them: warm/persistent runner, cached build
   artifacts, judge sampling **capped at 3 with early-stop on agreement**, samples parallelized, code
   graded **asynchronously** so the session keeps moving. Grading-latency p50/p90/p99 is a
   first-class health metric.
6. **Orchestrate over external labs (R6).** Layer over MIT 6.824's autograder, Jepsen
   Maelstrom / Fly.io Gossip Glomers, and CodeCrafters for code and distributed *conformance*.
   Crucible's unique additions are the design-defense judge on your own repos, spacing/interleaving,
   mastery/θ tracking, and the rejected-alternative rubric. Only hand-roll a grader where no external
   one exists.
7. **Right-size anti-gaming (R7).** The self-gaming premise is weak — the grade's only value is
   accurate self-knowledge, which you want, and you control every tunable anyway. Keep only the two
   near-free structural guards (**reference-grounding** and **deterministic-wins**). Defer the
   gold-set-reproduction-before-trust harness and retry-trace machinery until there is evidence of
   gaming. The real failure mode is disengagement + lenient-judge false confidence, which the two
   cheap guards already cover.

## Phase table

| Phase | Goal | Key deliverables | Exit criteria | Status |
|---|---|---|---|---|
| **0 — Content pilot** | Prove the thing is worth building at all. | 10–15 hand-authored Go lessons tied to `conclave`; graded with plain `go test` + a wall-clock timeout; a throwaway Markdown/CLI harness; **no engine**. | Used daily for **2+ weeks**; self-reported real learning value on `conclave` work; a per-lesson authoring-cost estimate (hours/lesson) and an ordered backlog of the next ~35 lessons exist. | planned |
| **1 — Spine + green-gate** | Make a broken or ungradeable lesson impossible to commit. | Lesson YAML schema + YAML→JSON compiler; two-layer gate (ajv shape + `validate.mjs` procedural); structural guards (gradeable-or-reject, coverage-closure, reference-reproduces, `debug_this`-buggy-must-fail, rubric-passes-own-reference, leak-guard); the pilot lessons ported to schema as fixtures. | `make gate` passes on the real lessons **and rejects four deliberately-broken variants** (orphan objective, non-reproducing reference, fake `debug_this` bug, rubric its own gold answer fails); exit non-zero on any error, warnings non-blocking. | planned |
| **2 — Deterministic grading + runner + mastery** | Run a real teach→test session on non-code items with honest numbers out. | Router + normalized grade envelope `{score,max,verdict,per_criterion,evidence,confidence,grader_id,logs}`; deterministic grader (choice + derived-output); CLI session runner (teach-then-test new; test-first reveal-on-miss review); SQLite append-only attempt log + Elo-with-decay θ/b fold; `recompute_from_log()`. | An MCQ + predict-output session grades instantly; θ matches hand-computed values; `recompute_from_log()` reproduces live θ **bit-for-bit** after retuning K. | planned |
| **3 — Hidden-tests grader** | Grade build-the-primitive items by executing code. | Plain local `go test -race` runner (timeout + `ulimit`, **not** a hardened container); hidden tests + reference injected from outside; counterexample-on-fail surfacing; Hypothesis-style differential/metamorphic property harness vs a locked reference; hardened `predict_race_verdict` (N≫2 iterations, reliably-tripping constructions). | The worker-pool item grades end-to-end: reference executed green by the gate; learner code run under `-race` with `goleak`; an infinite loop / fork bomb times out cleanly; a hidden-test input never appears in a traceback; `predict_race_verdict` is reported with its probabilistic confidence, not as a clean oracle. | planned |
| **4 — Hosted LLM-judge + trust guards** | Grade design judgment, trustworthy by construction. | `claude -p` subprocess judge (JSON schema, disallowed-tools, reference-grounded, ≤3 samples median+spread, abstain on wide spread); **network-down fail-open** to self-grade; **deterministic-wins** enforced in the composite combiner; **reference-grounding** (never run reference-free); answer-in-data-channel sanitization; per-session USD ceiling with `total_cost_usd` tracking. | The explain-it-back item grades with a per-criterion breakdown; the judge is **proven unable to raise** a deterministic verdict; a killed network connection degrades to self-grade with confidence `LOW` rather than failing the session; a session's judge spend stays under the ceiling. | planned |
| **5 — Scheduler + spacing** | Turn single-module sessions into a paced, interleaved, mastery-gated curriculum. | Candidate-pool ranker (due ∪ weak ∪ prereq-cleared-new); FSRS-lite half-life spacing (`due_at`); hard domain interleaving (≤2 consecutive same-domain) + new-per-session cap; prereq DAG gating; test-out challenge path. | A multi-module session mixes due/weak/new correctly, never runs >2 consecutive same-domain items, introduces ≤1 new item with a backlog present, and lets you test out of a known-strong skill via one Evaluate-level challenge. | planned |
| **6 — Local web UI + analytics** | Move off the CLI to the target interface and surface honest numbers. | FastAPI backend + lightweight local web session UI; local-file analytics dashboard (mastery heatmap σ(θ), calibration reliability + Brier, retention-vs-ρ, latency p50/p90/p99, weakest-topic three ways, per-module Limitations panel). | The web UI runs a full session; the dashboard renders (Playwright QA green, dark/light, no console errors), written **locally** — nothing published; grading-latency p50/p90/p99 is displayed as a first-class metric. | planned |
| **7 — AI-authoring + hardened sandbox** | Scale content authoring — and only now, when untrusted content exists, harden execution. | Bounded self-repair authoring pipeline (skeleton → preflight → materialization → rubric self-check → adversarial audit → merge), N=3 then quarantine; hardened container (rootless + seccomp + no-net + cgroups); Go **no-network module cache** (pre-baked `GOMODCACHE`, `GOFLAGS=-mod=vendor`, `GOPROXY=off`); panic/compile-error **source-leak scrubbing**. | A pipeline-authored lesson passes `make gate` green with any non-reproducing draft **quarantined, not shipped**; a hidden-test *compile error* is proven not to leak its source into a traceback; an AI-authored reference runs offline with no module fetch. | planned |
| **8 — Domain expansion** | Prove the engine is domain-agnostic and deliver the deeper cloud/DevOps/distributed track. | Python-deep track (deep-from-day-1 hidden-test batteries + `mypy --strict` gate); distributed-internals track orchestrated over **Maelstrom / Gossip Glomers** (msgs/op + p50/p99); defend-and-extend case-studies from your own repos (WALterDB 2PL, GOOGLY ring, TraceLens reward shaping); a thin FSRS deck capped to genuinely-rote Go idioms. | At least two further tracks run behind the **same engine with zero router changes**; the Maelstrom-orchestrated checker injects a partition and either finds an invariant violation or produces the evidence it holds; case-study memos grade against the reference-grounded judge. | planned |

## Phase notes (why each boundary is where it is)

**Phase 0 leads because the risk it retires is the largest.** The rejected alternative — the
original synthesis order — put a spine + green-gate first and the pilot nowhere. That builds the
grading cathedral against a behavior (daily study) that has never been observed. If Phase 0 shows
you *don't* open the tool daily, no amount of Elo or sandbox rescues it, and you've spent the
runway on the part that was fun to build rather than the part that teaches. The pilot uses plain
`go test` and a throwaway harness precisely so almost none of it survives into the real engine — it
is a probe, not a foundation.

**Phases 1–3 are ordered correctness-first**, matching the Correctness > Reliability > UX >
Maintainability > Performance order. The green-gate (Phase 1) makes ungradeable content impossible
*before* any grading UI exists, so every later phase builds on content proven executable. Phase 2
grades the cheap deterministic path and stands up the mastery fold — the fold is trivial to verify
(`recompute_from_log()` is a pure replay), so it comes before the hard, expensive paths. Phase 3
takes the hardest deterministic path (executing code) but *not* the hardened sandbox: the rejected
alternative here is the R3 error of front-loading a rootless/seccomp/gVisor container against a
threat (untrusted code) that does not exist until Phase 7.

**Phase 4 is the first hosted, metered, non-deterministic component**, so it lands only after the
whole deterministic spine works — the judge grades *only what tests cannot see* and is structurally
forbidden (deterministic-wins) from overriding them. Its exit criterion tests the fail-open path,
not just the happy path, because a metered network call in the hot loop is a reliability liability
first and a feature second.

**Phase 5 before Phase 6** because the scheduler is logic you can test headless; the web UI is
presentation over already-correct state. Building the UI first (the rejected "GUI-first" ordering)
would mean debugging scheduling through a browser instead of a unit test.

**Phase 7 is where the sandbox finally hardens** — deferred, per R3, to the exact moment
AI-authored content creates a real untrusted surface. Two Go-specific operational hazards are
first-class deliverables here, not footnotes: the no-network module cache (`go test` will otherwise
try to fetch modules and fail with `GOPROXY` unreachable) and source-leak scrubbing (a compile
error in a hidden-test file dumps its `file:line` source unless explicitly scrubbed, and a test
proves it doesn't).

**Phase 8 is deliberately last and time-boxed.** Per R6, the distributed track is *orchestrated
over* Maelstrom rather than a hand-rolled fault-injection checker — the rejected alternative
(re-implementing what Jepsen already does better) is exactly the "harness crowds out the studying"
trap. The engine having to absorb three new tracks with **zero router changes** is the real test of
the discriminated-union grader seam.

## Limitations / open questions

- **The pilot might disprove the whole project.** That is the point. If Phase 0's 2-week daily-use
  bar fails, the honest outcome is to stop — not to proceed to Phase 1 anyway. This roadmap does not
  assume the pilot succeeds.
- **`recompute_from_log()` replays scheduler arithmetic, not grading (R9).** Bit-for-bit
  reproducibility holds for θ recomputed from *stored* grades after retuning K/half-life/weights. It
  does **not** re-grade: retuning a rubric or swapping the judge model invalidates stored judge
  grades and requires a fresh (non-free, non-deterministic, hosted) re-grade pass. "Bit-for-bit"
  must never be read as grade reproducibility.
- **Authoring throughput is the unquantified bottleneck.** Phases 1–6 hand-author against a gate
  that makes each lesson *harder* to write (every reference must execute green, every rubric must
  clear its own gold). The per-lesson cost estimate from Phase 0 is what tells us whether the
  backlog is weeks or months of authoring; the AI pipeline (Phase 7) is what makes it tractable, and
  it is deliberately late because it needs the gate to exist first.
- **Content aging is a maintenance model, not a one-time cost (R10).** Pinned toolchains (Go 1.22+,
  pydantic-v2, SQLAlchemy 2.0, pion) age; one toolchain bump can turn dozens of green lessons red at
  once. Not yet scheduled into a phase: changed-only/incremental gate execution, per-track toolchain
  pins, and a periodic "gate against latest toolchain" job. These belong somewhere between Phases 1
  and 8 and are currently an open placement question.
- **`predict_race_verdict` is probabilistic even after hardening (R4).** N≫2 iterations reduce the
  false-negative rate but do not eliminate it; the item is reported with its confidence, never as a
  clean deterministic signal. Do not let the Phase 3 exit criterion imply otherwise.

---

Related: the binding decisions and resolved tensions live in [`../PLAN.md`](../PLAN.md); the
P0/P1/P2 feature spec these phases deliver is in [`02-features.md`](02-features.md).
