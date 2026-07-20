# SYNTHESIS — consolidated build plan (first draft, before critique)

> First-draft consolidation. **Superseded on several points by the critique and by PLAN.md's R1–R10 resolutions** — read those for the corrected plan.

## Vision

**Problem**

A senior-level systems engineer (deep Python/FastAPI/asyncio, C++ DB internals, real concurrency-correctness) with ONE true gap — Go, at true-beginner level — wants to go past interview-level system design into cloud/DevOps/distributed internals. He learns by building and adversarial verification, dislikes rote recall, and demands the WHY plus the NAMED rejected alternative. No existing tool fits: exercism/A-Tour-of-Go grade too softly (toy suites), Anki/LeetCode gate on rote content he dislikes, educative/roadmap.sh stop at interview depth with passive or no grading, boot.dev wraps it in gamification he doesn't need. What is missing is a teach-then-TEST workbook that assesses at Bloom Analyze/Evaluate/Create, auto-grades via a hybrid of deterministic checks plus a LOCAL Claude-headless LLM-judge, reports NUMBERS not adjectives, and — because he is both author and sole beneficiary of a high grade — cannot be self-gamed.

**Goals**

- Teach a primitive, then force effortful closed-book RETRIEVAL/RECONSTRUCTION; gate the next module on a BEHAVIOR bar (builds the primitive from scratch + names the rejected alternative + states >=1 failure mode with a number), not a percentage
- Hybrid auto-grading with a router: deterministic wherever a computable oracle exists (MCQ, exact/derived output, hidden unit + property/differential tests in a sandbox); a local Claude-headless LLM-judge ONLY for free-form design essays, always reference-grounded
- Per-language altitude asymmetry: Go starts as a scaffolded Tour/boot.dev-level on-ramp then ramps to from-scratch primitives under `go test -race`; Python is deep and adversarial from day one (hidden-test batteries, mypy --strict gate)
- Encode his value order Correctness > Reliability > UX > Maintainability > Performance directly in rubric arithmetic — a fast solution that fails a fault-injection invariant scores below a slower correct one
- Prove gradeability BY CONSTRUCTION: a content green-gate executes every reference answer/solution and rejects any lesson with an ungradeable objective, a non-reproducing reference, or a rubric its own gold answer can't clear
- Report numbers as first-class: mastery heatmap sigma(theta), model-calibration Brier score, first-try pass rate, msgs/op and p50/p90/p99 latency
- Anti-gaming as a first-class subsystem, not an afterthought: deterministic-wins invariant, reference-grounded judge, answer-in-a-data-channel, logged attempts, a hand-graded gold-set the judge must reproduce before it is trusted

**Non-goals**

- NOT a flashcard app — FSRS is a thin adjunct capped to genuinely-rote Go idioms/stdlib signatures he keeps re-looking-up; design judgment NEVER enters the scheduler (it trains verbatim recall and crowds out transfer)
- NOT a multi-user LMS: no accounts, no auth, single-learner; no gamification (XP/streaks/boss-battles) and streaks NEVER gate scheduling (that rewards cramming)
- NOT interview-level system-design rehearsal — design modules are gated on a distributed-internals/cloud/DevOps depth bar, rejecting educative/roadmap.sh contamination
- NOT a from-scratch Kubernetes or Terraform — build the primitive only where the primitive IS the learning target (container runtime via namespaces+cgroups yes; a whole orchestrator no); USE real Kafka/Postgres/K8s and study their internals
- NOT hosted/cloud — local-first, offline-capable, CLI-first; per his standing instruction NOTHING is published to claude.ai, all deliverables are local files
- NOT human-mentored and NOT reliant on a hosted frontier judge — the judge is the local `claude --bare -p` headless model, treated as fail-open and never the sole gate

**Success criteria**

- Vertical slice done: the Go concurrency-discrimination module runs teach -> test -> grade -> schedule end-to-end, `make gate` green, exercising ALL THREE grading strategies (deterministic MCQ, hidden-tests `go test -race`, LLM-judge explain-it-back) in one module
- Structural guarantee holds: a lesson with an orphan objective, a reference solution that fails its own hidden tests, a `debug_this` whose buggy code doesn't actually fail, or a rubric its gold answer can't clear — CANNOT be committed
- Judge trust established before use: the local judge reproduces the ordering of his 15-20 hand-graded gold answers within tolerance, and is proven to only ever LOWER or flag a deterministic verdict, never raise it
- On any hidden-test failure the minimal failing input/counterexample is surfaced (steal LeetCode rigor, reject its opacity)
- Numbers surfaced and honest: per-module Limitations panel names what the exercise does NOT prove (e.g. an aiosqlite-green test says nothing about asyncpg concurrency; a single-node lab is not 'production-grade')
- Mastery is a deterministic pure fold: recompute_from_log() reproduces live theta bit-for-bit after retuning any constant

## Prototype features

### [P0] VERTICAL SLICE: Go concurrency-discrimination module, end-to-end

Build ONE module fully — 'select among sync.Mutex / channel / atomic / errgroup for an unlabeled contention scenario, then build a leak-free goroutine lifecycle under context cancellation and prove it with `go test -race`'. It contains interleaved decision-first MCQs, a predict-the-`-race`-verdict item, a build-the-primitive hidden-tests item, and an explain-it-back 'why NOT a channel here + the failure mode' judge item.

*Rationale:* This single domain is the strongest first slice because it (a) is his GENUINE gap (Go true-beginner) so the prototype delivers real learning value, not just infra validation; (b) exercises all three grading strategies at once, stressing the whole engine including the hardest path (untrusted-code sandbox); (c) ties directly to his active project conclave, so output is load-bearing; (d) the predict-then-run-`-race` loop is the cleanest deterministic+adversarial signal available. REJECTED alternatives: a Python-deep slice (lower learning ROI, under-stresses the on-ramp asymmetry and the Go runner) and a design-case-study slice mined from WALterDB 2PL (pure LLM-judge — under-exercises the deterministic and hidden-test paths, the very parts that most need de-risking).

### [P0] Content-as-data lesson files (YAML source -> JSON runtime)

One YAML file per lesson co-locating teach blocks, worked examples, >=1 assessment, per-assessment rubric, reference answer/solution, and hidden tests; compiled to JSON for the runtime. schema_version + content_rev; git is the version store.

*Rationale:* Mirrors his proven dsa-workbook content-as-data pattern. YAML source (block scalars) beats raw JSON because his own AUTHORING.md flags JSON escaping of embedded code as a pain point; JSON runtime keeps a fast formal schema gate. REJECTED: a database-of-content (opaque, un-diffable, un-reviewable) and Markdown-with-front-matter (can't express the executable grading spine).

### [P0] Executable green-gate (make gate)

Two-layer gate: declarative JSON Schema (ajv) for field shape + a procedural validator (a validate.mjs sibling) for what a schema cannot express — coverage-closure, gradeable-or-reject, reference-reproduces (executes every reference solution + predict-output program), debug_this buggy-must-fail, rubric-passes-own-reference, leak-guard. Exits non-zero on any error; warnings non-blocking.

*Rationale:* This is the anti-fabrication guard generalized from his numeric set-containment resume check: correctness proven by construction, zero LLM in the loop. It makes a broken or ungradeable lesson impossible to commit. REJECTED: schema-only validation (cannot execute a reference or diff a coverage graph) and trusting the authoring LLM's self-report (the exact reward-hacking surface to avoid).

### [P0] Deterministic grader (choice + derived-output)

Grades MCQ/multi-select by exact/Jaccard match and predict_output by executing the program and comparing stdout to the DERIVED expected value. No model call.

*Rationale:* The objective correctness gate; expected outputs are machine-derived never hand-typed. REJECTED: routing MCQ/numeric to the LLM judge (slower, costlier, strictly less reliable than a string/float compare).

### [P0] Hidden-tests grader in a sandboxed Go runner

Ships a few PUBLIC example tests for iteration; keeps grading tests HIDDEN, injected at grade time from OUTSIDE the sandbox; runs learner code under `go test -race` + optional Hypothesis-style differential/metamorphic properties vs a locked reference; surfaces the minimal failing input on fail.

*Rationale:* The backbone of code grading and the hardest P0 — it validates the untrusted-code path on the most valuable content. Property/differential tests close the 'hardcode the visible cases' hole. REJECTED: language-level/in-process sandboxing (does not exist, especially for Python; a naive subprocess is an RCE) and visible-only tests (learner overfits to the checker).

### [P0] Session runner (CLI): teach-then-test new, test-first reviews

Renders exposition for a new concept then a graded check (generate-before-reveal); reviews are test-first, reveal-on-miss (adversarial, no free re-exposure). Time-boxed ~25 min / 8-12 items.

*Rationale:* Retrieval practice + desirable difficulty as the delivery loop; matches his build-and-verify style. REJECTED: read-then-summarise (the illusion-of-competence trap he distrusts) and a GUI-first shell (CLI is his daily driver and the fastest path to a working slice).

### [P0] Append-only attempt log + Elo-with-decay mastery fold (SQLite)

Every graded attempt appended immutably; per-skill theta and per-item difficulty b updated by an annealed-K logistic rule that ingests rubric partial-credit y in [0,1]; theta/half-life/due_at are a materialized fold with a deterministic recompute_from_log().

*Rationale:* One probabilistically-meaningful number that cold-starts at n=1 and self-calibrates. REJECTED: BKT (its slip/guess/learn params are unidentifiable at n=1, observation model is binary so it can't ingest rubric %, latent mastery is a step function) and full FSRS as the mastery model (17+ DSR weights need thousands of reviews and it rates recall of atomic facts — the rote he dislikes — never ability-vs-difficulty).

### [P0] Local Claude-headless LLM-judge (reference-grounded)

Invokes `claude --bare -p --output-format json` with a per-criterion rubric + locked reference answer for explain-it-back / name-the-rejected-alternative / design essays; forced JSON, CoT through criteria before the score, 3-5x sample with median+spread, abstain on wide spread.

*Rationale:* The only defensible way to grade design judgment; matches his self-hosting/offline ethos. REJECTED: a hosted frontier judge (network dependency + cost, against local-first) and a reference-FREE judge (self-play drives pass rate 0.72->0.94 at 0.20 true accuracy — it scores persuasiveness, not correctness).

### [P1] Scheduler: due/weak/new priority + hard interleaving + spacing

Candidate pool = due reviews U weak skills (theta<goal) U prereq-cleared new items; ranked by w_due*overdue + w_weak*weakness + w_new*newness + w_desirable*(target E~=0.85); caps new items (default 1/session) and forbids >2 consecutive same-domain items; FSRS-lite 2-param half-life drives due_at.

*Rationale:* Interleaving trains SELECTING the primitive (his own mutex-vs-channel-vs-atomic habit) and the 85% band fights rote. REJECTED: fixed-calendar review (ignores mastery) and blocking one topic to completion (worse discrimination and transfer).

### [P1] Anti-gaming + calibration + trust layer

Enforces deterministic-wins (judge may only lower/flag); sanitizes learner answer text into a delimited DATA channel; requires the judge to reproduce a hand-graded gold set before trust; logs every answer+grade so retry-until-lenient leaves a trace.

*Rationale:* For a solo learner who is both author and beneficiary, a lenient judge is worse than none — it manufactures false confidence. REJECTED: relying on an ensemble as 'objectivity' (majority vote reduces random noise but reinforces shared systematic bias).

### [P1] Analytics dashboard (local HTML)

Mastery heatmap sigma(theta) with numeric labels; MODEL CALIBRATION reliability plot + Brier; retention-vs-rho check; latency p50/p90/p99; weakest-topic three ways (bottom-k theta, blocked-below-prereq, most-overdue); per-module Limitations panel.

*Rationale:* Numbers-over-adjectives, and the model scoring itself (Brier) is the calibrated-claims move he values. Written as a LOCAL file (his no-publish rule). REJECTED: adjective progress bars / 'you're doing great' (uncalibrated, he'd catch it).

### [P1] AI-authoring pipeline (bounded self-repair, quarantine)

LLM skeleton -> structural preflight (no LLM) -> executable materialization (run references in sandbox) -> rubric self-consistency -> adversarial audit (advisory red-team) -> merge; bounded to N=3 retries then QUARANTINE to a review queue, never hard-fail the batch.

*Rationale:* Scales content authoring while the green-gate guarantees no broken lesson ships; graceful degradation with a surfaced reason. REJECTED: trusting AI-authored lessons without the executable gate, and hard-failing a 200-lesson batch on one bad draft.

### [P2] Domain expansion: Python-deep, distributed internals, design case-studies

Second/third tracks behind the same engine: Python internals (deep from day one), distributed internals via a Maelstrom/Gossip-Glomers-style fault-injection checker, and defend-and-extend case-studies mined from his own repos (WALterDB 2PL, GOOGLY ring, TraceLens reward shaping).

*Rationale:* Proves the engine is domain-agnostic and delivers the cloud/DevOps/distributed depth he asked for. REJECTED: building all four tracks before the engine is proven on one (surveys breadth shallowly; the defend-and-extend format only pays off at depth).

### [P2] Thin FSRS deck for rote Go idioms

A capped spaced-repetition deck holding ONLY genuinely-memorizable atoms (Go stdlib signatures, error-wrapping idioms, named gotchas) with default FSRS params, target retention 0.85-0.90.

*Rationale:* The small rote residue belongs somewhere, but off the design track. REJECTED: per-user FSRS optimization (on a sub-1000-card solo deck the famed 20-30% saving is ~20s/day noise — not worth claiming) and putting any design judgment in the deck.

## Architecture components

### Content Store

Hold lessons as content-as-data: one YAML file per lesson under content/<track>/<id>.yaml (teach + worked examples + assessments + rubric + reference + hidden tests), compiled to build/<id>.json for the runtime. Own schema_version (gate refuses unknown/newer) and per-lesson content_rev; git is the version store.

*Notes:* Data flow: authored-or-AI-generated YAML -> gate compiles to JSON and validates -> session runner loads JSON. YAML source / JSON runtime is a deliberate trade: block scalars beat JSON escaping for embedded code; JSON keeps the fast formal schema gate. Compile-in-gate so nobody hand-edits the compiled JSON (drift guard).

### Curriculum / Scheduler

Turn mastery state + prereq DAG into an ordered session queue. Assemble candidate pool (due U weak U prereq-cleared-new), rank by w_due*overdue + w_weak*weakness + w_new*newness + w_desirable*(-|E-rho|), enforce new-per-session cap and <=2-consecutive-same-domain interleaving, gate new items behind prereq theta>=0 logit.

*Notes:* Reads Progress/Mastery Store (theta, due_at, half_life) and Content Store (prereq edges, item difficulty b). Emits the queue to the Session Runner. Spacing via FSRS-lite half-life; target E~=0.85 keeps items in the desirable-difficulty band. Streaks are informational and never enter the ranking.

### Grading Engine (router + strategies)

Front a Router that maps grading.strategy -> exactly one of three graders (deterministic / hidden_tests / llm_judge). Each grader returns ONE normalized envelope {score, max, verdict, per_criterion[], evidence[], confidence, grader_id, logs}. Composite items (code + design prose) combine sub-scores with deterministic as a HARD GATE.

*Notes:* Data flow: attempt -> router (keys on grading.strategy, not question type, so only 3 code paths) -> grader(s) -> envelope -> Mastery Store update. Discriminated-union design mirrors his Source-adapter/StorageEngine seam habit: adding a strategy never touches the router. Envelope is the exercism results.json contract internalized.

### Sandbox Executor

Run untrusted code (learner submissions AND locked reference solutions, in separate invocations) with defense-in-depth: hardened rootless container + seccomp + no network + read-only rootfs + cgroup CPU/mem/pid caps + wall-clock timeout. Return bounded results even on infinite loops / fork bombs / crashes.

*Notes:* Hidden tests and the reference implementation are injected at grade time from OUTSIDE the boundary and NEVER visible inside it; tracebacks are scrubbed so test/reference source can't leak. Go runner base image for the vertical slice; Python next; the language runner is a swappable seam. This is the single hardest piece — budget for it; gVisor is the upgrade if untrusted code scares you.

### Progress / Mastery Store

SQLite. Append-only attempt log is the source of truth (per-attempt before/after snapshots of theta/b/half-life). skill.theta, half_life_days, due_at are a MATERIALIZED fold via the Elo-with-decay update. Config table holds every tunable (K0, rd_tau, rho, hl_growth, hl_lapse, hint_penalty, weights, b_freeze_m).

*Notes:* recompute_from_log() replays the whole log deterministically so retuning any constant is a replay, not a migration — directly testable, matches his event-sourcing/verification taste. Time-on-task stays OUT of theta (Correctness > Performance); it only modulates half-life growth and feeds p50/p90/p99 analytics. Freeze item b after 8 attempts to fight theta/b co-drift on a tiny deck.

### Authoring Pipeline

Convert a source note/topic into a gate-passing lesson via a bounded self-repair loop: (1) LLM skeleton against the pinned schema contract; (2) structural preflight, no LLM (parse + shape + gradeable-or-reject + coverage-closure); (3) executable materialization (run every reference solution + predict-output program, bounce non-reproducing drafts with runner output as the repair prompt); (4) rubric self-consistency (judge each gold answer against its own rubric); (5) adversarial audit (red-team LLM flags giveaway distractors / non-discriminating items — advisory); (6) merge only green lessons, bump content_rev.

*Notes:* Bounded N=3 then QUARANTINE to a review queue — never hard-fail the batch (graceful degradation with a surfaced reason). Two HARD errors block commit: 'no gradeable assessment' and 'reference answer does not reproduce'; everything else is a warning. This is his multi-agent adversarial self-audit as a pipeline.

### Interface Layer

CLI-first session runner: render teach blocks, capture answers, drive the grading engine, and give feedback (reveal-on-miss, minimal failing input on hidden-test fail, per-criterion breakdown with evidence + confidence for judge items). Plus a local static-HTML analytics dashboard.

*Notes:* No server, offline, no accounts. Answers flow to the Grading Engine in a delimited data channel (never concatenated into judge instructions). Dashboard is a LOCAL file with a hand-rolled light/dark theme (his taste) — per his standing rule, NOTHING is published to claude.ai. Playwright render-QA is the optional second gate (missing-figure sentinels, console errors, theme toggle).

## Grading design

| Question type | Strategy | Notes |
|---|---|---|
| mcq | `deterministic_choice` | Exact match to the single correct option; no model call. Gate requires exactly one correct:true and a non-empty `why` on EVERY option (kills giveaway distractors). Rejected: LLM judge (slower, less reliable than a string compare). |
| multi_select | `deterministic_choice` | Set-equality or Jaccard partial credit. Gate rejects degenerate all-true/all-false. Reference_answer array must equal the correct set. |
| predict_output | `deterministic_output` | Gate EXECUTES the program and DERIVES expected_output (never hand-typed) — anti-fabrication core. match in {exact,trimmed,regex}. Gate rejects programs whose stdout differs across two runs (nondeterminism) or forces regex/normalized compare. |
| predict_race_verdict (Go) | `deterministic_output` | Learner predicts what `go test -race` prints for a snippet; gate runs it under -race and compares the verdict. The cleanest deterministic+adversarial Go signal; central to the vertical slice. |
| code_completion | `hidden_tests` | Public example tests for iteration + hidden grading tests injected from outside the sandbox; >=1 visible and >=1 hidden. Gate EXECUTES reference_solution vs ALL tests (green or lesson rejected). Leak-guard: no hidden input/expect appears in starter/prompt. |
| code_from_scratch | `hidden_tests` | Hidden tests + Hypothesis-style differential/metamorphic properties vs a locked reference decide pass/fail. Optional advisory llm_review at weight_of_style 0.0 (comment-only — a flaky model review can NEVER fail a correct solution: 'LLM must never hard-fail the pipeline'). |
| debug_this | `hidden_tests` | Gate runs BOTH: the `buggy` code must FAIL >=1 test (a fake/no-op bug is rejected) and reference_solution must PASS all. Emits real p50/p99/msgs-per-op where the primitive supports it. |
| short_answer / definition | `llm_judge` | keyword_or_rubric: cheap keyword_must (AND-of-OR) / keyword_must_not short-circuit first; fall through to a one-criterion rubric only if inconclusive (cost control). Gold answer must satisfy the keyword guard AND clear the rubric. |
| explain_tradeoff / design_essay | `llm_judge` | Weighted-criteria rubric + locked reference; anti_reward_hacking (min_words, penalize_if_contains 'as an AI'/'it depends'). Rubric must reward the NAMED rejected alternative + a failure mode + a quantified claim, or the essay fails. Rejected: reference-free grading (gameable to uselessness). |
| critique_design | `llm_judge` | >=2 criteria (names the flaw AND proposes a concrete better alternative). Reference answer must clear its own rubric at authoring time. |
| feynman / explain_back | `llm_judge` | Rubric scores analogy fidelity + 'no technical error introduced by the simplification'. The single best defense against illusion-of-competence — can't be pattern-matched. |

**LLM-judge design (first draft — see R1: this judge is HOSTED, not offline)**

Invocation: `claude --bare -p --output-format json --json-schema <rubric_schema> --disallowed-tools 'Bash,Edit,Glob,Write' --append-system-prompt-file rubric.txt`, spawned from a Python (or Go) subprocess. --bare skips hook/MCP/settings discovery for reproducible CI-style behavior; --disallowed-tools makes the judge Read-only so it can never execute or mutate. Model: claude-opus-4-8 or claude-sonnet-5 (temperature/top_p are not settable on these models — responses are intrinsically deterministic; older temperature-bearing models are rejected for the judge). Structured output via --json-schema forces {per_criterion:[{id,score,evidence}], total, verdict, abstain:bool} so there is no free-text-score parsing. G-Eval shape: the prompt makes the judge reason THROUGH each rubric criterion (with an evidence span) BEFORE emitting the number. The LOCKED reference answer is ALWAYS in context; the judge is NEVER run reference-free. The learner's answer is placed in a clearly delimited DATA block, never interpolated into the instruction channel, and the judge is instructed to ignore any 'grade me X' meta-text inside it (defeats the fake-evaluation-note injection). Sample 3-5x, take the MEDIAN with spread reported as confidence; wide spread => ABSTAIN and route to self-grade-against-reference rather than print a false precise number. Parse total_cost_usd per call for budget tracking; distinguish exit-code 1 (API error) from --max-turns via stderr. Because the LOCAL model is a weaker, more gameable judge than a hosted frontier one, the anti-gaming posture is HARDER not softer: lean on structural guards, pin the model + snapshot the rubric+reference, and re-calibrate on the gold set after any model or rubric change. Rejected alternatives: hosted Claude/GPT judge (stronger but adds cost + network dependency, violates local-first/offline); the Anthropic Messages API directly (lower-level, must hand-roll cost tracking + tool restriction + JSON enforcement that Claude Code gives for free); an ensemble marketed as objectivity (it reduces random noise but reinforces shared systematic bias — used only for spread/confidence).

**Trust safeguards**

- DETERMINISTIC-WINS INVARIANT (non-negotiable): the LLM judge may only LOWER a grade or flag a concern, never RAISE a deterministic (tests/exact-match) verdict. Correctness is decided by tests; the judge grades only what tests can't see.
- RUBRIC-PASSES-OWN-REFERENCE: at authoring time the gate runs the judge on each gold answer; if the gold answer can't clear its own rubric + keyword guard, the rubric is broken and the lesson is rejected.
- GOLD-SET CALIBRATION: the learner hand-grades ~15-20 representative past answers; the judge must reproduce that ordering/scores within tolerance BEFORE it is trusted on fresh answers, and re-runs whenever the model or rubric changes. Agreement with the gold set is the single headline trust metric.
- ANSWER-IN-DATA-CHANNEL + META-TEXT IGNORE: learner text is sanitized into a delimited block, never the instruction channel — blocks prompt injection through the answer.
- HIDDEN-TEST + REFERENCE ISOLATION: tests and reference impl injected from outside the sandbox, never importable/mounted inside; tracebacks scrubbed so source can't leak into a stack trace.
- COUNTEREXAMPLE-ON-FAIL: on any hidden-test failure surface the minimal failing input (steal LeetCode's rigor, reject its opacity — he learns by understanding the failure).
- APPEND-ONLY ATTEMPT LOG: every answer+grade logged so retry-until-lenient leaves a trace; periodic hand-audit of a random sample of judge PASSes (he is the calibration oracle).
- CONFIDENCE + ABSTENTION SURFACED: HIGH for deterministic, MEDIUM for reference-grounded judge with tight spread, LOW/ABSTAIN for wide-spread subjective items routed to self-grading — never fake precision.
- CORRECTNESS-WEIGHTED RUBRIC ARITHMETIC: scoring reflects Correctness > Reliability > UX > Maintainability > Performance, so a fast solution failing a fault-injection invariant scores below a slower correct one.

## Content schema proposal

```yaml
# content/go/go04-concurrency-discrimination.yaml   (YAML source-of-truth; gate compiles -> build/*.json)
# Illustrates the vertical-slice Go module and all three grading strategies.
schema_version: 1
id: go04-concurrency-discrimination        # kebab, MUST start with "<tag>-"; gate refuses unknown/newer schema_version
tag: go04
title: "Go: mutex vs channel vs atomic — discrimination & leak-free lifecycles"
track: go
week: "Track Go · Module 04"
priority: attack                           # attack | moderate | review | meta
content_rev: 1                             # bumped on ANY edit; git is the store
prerequisites: [go02-interfaces, go03-errors-as-values]   # gate asserts these ids exist
altitude: ramp                             # on_ramp | ramp — enforces per-language asymmetry (Go ramps, not deep-from-day-1)
summary: >
  Go gives you Mutex, channel, atomic, and errgroup for concurrency. The skill is not
  "what is a race" (he owns that) — it is SELECTING the idiomatic primitive and proving
  the choice under `go test -race`.

learning_objectives:                       # each MUST be taught AND assessed via `covers`
  - { id: go04-o1, bloom: evaluate, text: "Select Mutex/channel/atomic/errgroup for an unlabeled contention scenario and justify" }
  - { id: go04-o2, bloom: create,   text: "Build a leak-free goroutine lifecycle under context cancellation, proven -race clean" }
  - { id: go04-o3, bloom: analyze,  text: "Predict the exact -race verdict for a data-race snippet" }

teach:
  - heading: "Three primitives, one decision"
    covers: [go04-o1]
    body: |
      > [!KEY] Default: atomic for a counter, Mutex for a multi-word invariant, channel for ownership transfer.
      errgroup when you need fan-out + first-error + cancellation.
  - heading: "Who closes the channel; who cancels the context"
    covers: [go04-o2, go04-o3]
    body: |
      The creator closes the channel. `context.WithTimeout` + `defer cancel()` or you leak the timer.

worked_examples:
  - id: go04-w1
    covers: [go04-o1]
    prompt: "A hot counter incremented by 8 goroutines, read rarely. Pick the primitive."
    solution: |
      atomic.Int64 — single-word, lock-free; a Mutex here is idiomatic-wrong (over-serializes the common path).

assessments:                               # >=1 REQUIRED; union(assessments[].covers) == objective id set
  # ---- MCQ (deterministic_choice) ----
  - id: go04-a1
    type: mcq
    covers: [go04-o1]
    difficulty: easy
    prompt: "8 goroutines increment one int64 counter, read once/sec. The idiomatic primitive is..."
    grading:
      strategy: deterministic_choice
      options:
        - { text: "sync.Mutex",     correct: false, why: "over-serializes a single-word update; contention on the hot path" }
        - { text: "atomic.Int64",   correct: true,  why: "single-word, lock-free, exactly the LongAdder mental model" }
        - { text: "buffered channel", correct: false, why: "channel is for ownership transfer, not a shared counter" }
        - { text: "errgroup",        correct: false, why: "that's fan-out + first-error, not counting" }
    reference_answer: "atomic.Int64"

  # ---- predict the -race verdict (deterministic_output; gate RUNS it under -race) ----
  - id: go04-a2
    type: predict_race_verdict
    covers: [go04-o3]
    grading:
      strategy: deterministic_output
      runner: "go test -race"
      program: |
        // two goroutines write the same map key with no sync
        m := map[string]int{}
        go func(){ m["x"]++ }(); go func(){ m["x"]++ }()
      expected_output: "DATA RACE"          # gate asserts the -race report contains this; expected is DERIVED not typed
      match: regex

  # ---- build-the-primitive (hidden_tests in the Go sandbox) ----
  - id: go04-a3
    type: code_from_scratch
    covers: [go04-o2]
    difficulty: hard
    grading:
      strategy: hidden_tests
      language: go
      starter: |
        // Worker pool over jobs, graceful shutdown via ctx; must not leak goroutines.
        func Run(ctx context.Context, jobs <-chan int, n int) (processed int) { /* TODO */ }
      reference_solution: |                 # gate EXECUTES this vs ALL tests under -race; green or lesson REJECTED
        func Run(ctx context.Context, jobs <-chan int, n int) (processed int) {
            var wg sync.WaitGroup; var c atomic.Int64
            for i := 0; i < n; i++ { wg.Add(1); go func(){ defer wg.Done()
                for { select { case <-ctx.Done(): return
                    case j, ok := <-jobs: if !ok { return }; _ = j; c.Add(1) } } }() }
            wg.Wait(); return int(c.Load())
        }
      tests:
        - { name: drains_all,   visible: true,  golden: "closes jobs, all processed" }
        - { name: ctx_cancel,   visible: false, golden: "returns promptly on cancel" }
        - { name: no_leak,      visible: false, golden: "goleak: zero lingering goroutines" }
      race: true
      timeout_ms: 5000
      llm_review: { enabled: true, weight_of_style: 0.0 }   # advisory only; tests decide pass/fail

  # ---- explain-it-back (llm_judge; reference-grounded, rubric) ----
  - id: go04-a4
    type: explain_tradeoff
    covers: [go04-o1]
    difficulty: hard
    grading:
      strategy: llm_judge
      judge_mode: rubric
      rubric:
        pass_threshold: 0.6
        criteria:
          - { id: c1, weight: 0.4, text: "Names the rejected alternative (why NOT a channel here)" }
          - { id: c2, weight: 0.3, text: "States a concrete failure mode of the wrong choice" }
          - { id: c3, weight: 0.3, text: "Includes a quantified claim (contention/ns-per-op/allocs)" }
        anti_reward_hacking: { min_words: 40, penalize_if_contains: ["as an AI", "it depends"] }
    reference_answer: |                      # gate asserts this gold answer clears its OWN rubric before commit
      Use atomic for the counter; a channel is rejected because ownership isn't transferring — you'd pay a
      scheduler hop per increment (measurably higher ns/op under 8-way contention) and the failure mode of a
      Mutex is convoy-ing readers behind writers. atomic.Int64 is ~1 CAS, no allocation.

figures:
  go04-fig-select:
    caption: "Decision: single-word -> atomic; invariant -> Mutex; ownership -> channel; fan-out+error -> errgroup."
    svg: "<svg viewBox=\"0 0 640 200\" role=\"img\">...</svg>"   # same referential-integrity + no-hardcoded-colors rules as dsa-workbook
```

## Roadmap phases (first draft — reordered in docs/09-roadmap.md per R2)

### Phase 0 — Spine + executable green-gate

*Goal:* Make a broken or ungradeable lesson impossible to commit, before any grading UI exists.

- Lesson YAML schema + YAML->JSON compiler
- Two-layer gate: JSON Schema (ajv) shape + procedural validator (validate.mjs sibling)
- Structural guards: gradeable-or-reject, coverage-closure, reference-reproduces (executes references), debug_this-buggy-must-fail, rubric-passes-own-reference, leak-guard
- One hand-authored Go lesson (the vertical-slice module) as fixture
- config table of tunables seeded

*Exit criteria:* `make gate` passes on the hand-authored Go lesson AND rejects four deliberately-broken variants (orphan objective, non-reproducing reference solution, fake debug bug, rubric its gold answer fails). Exit non-zero on any error; warnings non-blocking.

### Phase 1 — Deterministic grading + session runner + mastery fold

*Goal:* Run a real teach->test session on non-code items with numbers coming out.

- Router + normalized grade envelope {score,max,verdict,per_criterion,evidence,confidence,grader_id,logs}
- Deterministic grader (choice + derived-output)
- CLI session runner (teach-then-test new; test-first reveal-on-miss review)
- SQLite append-only attempt log + Elo-with-decay theta/b fold
- recompute_from_log()

*Exit criteria:* A session of MCQ + predict-output grades instantly, theta updates against hand-computed values, and recompute_from_log() reproduces live theta bit-for-bit after retuning K.

### Phase 2 — Sandbox + hidden-tests grader (Go runner)

*Goal:* Grade build-the-primitive items by running untrusted code — the hardest path, on the most valuable content.

- Defense-in-depth sandbox (rootless container + seccomp + no-net + ro-rootfs + cgroups + wall-clock timeout)
- Hidden-tests + `go test -race` grader; tests/reference injected from OUTSIDE, tracebacks scrubbed
- Hypothesis-style differential/metamorphic property harness vs locked reference
- counterexample-on-fail surfacing
- predict_race_verdict end-to-end

*Exit criteria:* The vertical-slice worker-pool item grades end-to-end: reference solution executed green by the gate, learner code run under -race with goleak, an infinite loop / fork-bomb is contained and times out cleanly, and a hidden test's input never appears in the sandbox or a traceback.

### Phase 3 — Local LLM-judge + trust layer

*Goal:* Grade design judgment with the local Claude-headless judge, trustworthy by construction.

- `claude --bare -p` subprocess judge (JSON schema, disallowed-tools, reference-grounded, 3-5x median+spread, abstain)
- Deterministic-wins invariant enforced in the composite combiner
- Answer-in-data-channel sanitization + meta-text-ignore
- Gold-set calibration harness (15-20 hand-graded answers)
- attempt+grade logging

*Exit criteria:* The explain-it-back item grades with a per-criterion breakdown; the judge is PROVEN unable to raise a deterministic verdict; and the judge reproduces the hand-graded gold-set ordering within tolerance before being switched on for fresh answers.

### Phase 4 — Scheduler, spacing, interleaving

*Goal:* Turn single-module sessions into a paced, interleaved, mastery-gated curriculum.

- Candidate-pool ranker (due U weak U prereq-cleared-new)
- FSRS-lite half-life spacing (due_at)
- hard domain interleaving (<=2 consecutive same-domain) + new-per-session cap
- prereq DAG gating
- test-out challenge path for already-strong skills

*Exit criteria:* A multi-module session mixes due/weak/new correctly, never runs >2 consecutive same-domain items, introduces <=1 new item with a backlog present, and lets him test out of a known-strong skill via one Evaluate-level challenge.

### Phase 5 — Analytics + AI-authoring pipeline

*Goal:* Surface honest numbers and scale content authoring without weakening the gate.

- Local-HTML dashboard: mastery heatmap sigma(theta), calibration reliability + Brier, retention-vs-rho, latency p50/p90/p99, weakest-topic, per-module Limitations panel
- Bounded self-repair authoring pipeline (skeleton -> preflight -> materialization -> rubric self-check -> adversarial audit -> merge), N=3 then quarantine

*Exit criteria:* Dashboard renders (Playwright QA green, dark/light, no console errors, written LOCALLY — nothing published); and a new lesson authored via the pipeline passes `make gate` green with any non-reproducing draft quarantined, not shipped.

### Phase 6 — Domain expansion

*Goal:* Prove the engine is domain-agnostic and deliver the deeper cloud/DevOps/distributed track.

- Python-deep track (deep-from-day-1 hidden-test batteries + mypy --strict gate)
- Distributed-internals track via a Maelstrom/Gossip-Glomers-style fault-injection checker reporting msgs/op + p50/p99
- Design case-study track (defend-and-extend on his own WALterDB/GOOGLY/TraceLens)
- thin FSRS deck for rote Go idioms

*Exit criteria:* At least two further tracks run behind the SAME engine with zero router changes; the distributed checker injects a partition and either finds an invariant violation or produces the evidence it holds; design case-study memos are graded by the reference-grounded judge.

## Cross-cutting risks

- Self-gaming the judge is the #1 threat: he is both author and beneficiary of a high grade, and a reference-free judge scores persuasiveness not correctness (0.72->0.94 pass at 0.20 true accuracy). Mitigation is structural (reference grounding + deterministic-wins + gold-set calibration + logging), never judge cleverness — and it must be built in Phase 3, not bolted on.
- Sandbox is the hard part and a real security surface: running his own code plus a Go (then Python) runner means an infinite loop, fork bomb, or code reading other answer files can hose the grader or leak hidden tests/reference impl if isolation is weak. Never co-locate reference/hidden-tests with the execution boundary; treat even his own code as untrusted; budget the sandbox as its own project cost.
- Harness eats learning time: CodeCrafters and Fly.io spent real engineering on their graders. The workbook infra can crowd out the actual studying. Mitigation — lean on existing tools (Maelstrom for distributed, real protocol clients, plain pytest/go test) rather than hand-rolling a platform, and time-box P2 domains.
- The local model is a weaker, more gameable judge than a hosted frontier one — the offline/self-hosting win comes with a trust cost. The anti-gaming posture must be HARDER for a local judge, and its agreement with the gold set watched over time for drift.
- Go on-ramp vs from-scratch-ethos collision: forcing from-scratch primitives too early in a true-beginner language makes him fight syntax instead of learning the concept; the altitude-asymmetry (Go scaffolded then ramps, Python deep from day 1) must be enforced or Go modules stall.
- Interleaving and generate-before-reveal LOWER visible in-session accuracy by design; without framing, that reads as 'the workbook isn't working'. Label the dip as the desirable-difficulty signal so he doesn't optimize it away.
- Mastery-model pitfalls at n=1: theta/b co-drift on a tiny deck (mitigate by seeding b from author tiers, updating at 0.25*K, freezing after 8 attempts) and cold-start noise in the first ~5 attempts/skill (say so honestly).
- Nondeterministic predict_output / flaky -race: dict ordering, timestamps, floats, or scheduler nondeterminism break the derived-expected guarantee. Gate must reject programs whose stdout differs across two runs or force regex/normalized compare.
- FSRS scope creep: spaced repetition is seductive and could quietly become the center of gravity, which he'd resent. Cap the deck to genuinely-rote atoms and measure whether he actually uses it.
- Aspirational-framing edge (flagged in his own profile): resist labeling a single-node lab 'production-grade'; every module's Limitations panel must name what the build does NOT prove.

## Differentiators

- Gradeability PROVEN BY CONSTRUCTION: an executable green-gate runs every reference answer/solution and rejects any lesson with an ungradeable objective, a non-reproducing reference, a fake debug-bug, or a rubric its own gold answer can't clear — his numeric set-containment anti-fabrication guard generalized to teaching content. No other platform makes a broken lesson impossible to commit.
- Trust without ground truth: the deterministic-wins invariant (the LLM judge may only lower/flag, never raise a test verdict) + a reference-grounded LOCAL judge + a hand-graded gold-set the judge must reproduce before it's trusted. Trust comes from structural guarantees, not from believing any single grade.
- Per-language altitude asymmetry: Go starts as a scaffolded on-ramp then ramps to from-scratch primitives under `go test -race`; Python is deep and adversarial from day one. Grading the two identically would bore him in Python or drown him in Go — no prior-art tool does this.
- Numbers-over-adjectives grading, including the model scoring ITSELF via a calibration reliability plot + Brier score; grades reported as per-criterion breakdowns with evidence spans, p50/p90/p99 latency, msgs/op, first-try pass rate — matching his measured-not-asserted habit.
- Defend-and-extend as first-class assessment: 'name the rejected alternative + the failure mode + a quantified claim, or the answer fails' — testing at Bloom Analyze/Evaluate/Create, banning any item a search engine could answer, directly targeting the rote recall he dislikes.
- Event-sourced, replayable mastery: an append-only attempt log with a deterministic recompute_from_log(), so retuning any scheduler constant is a verifiable replay, not a migration — his from-scratch/verification ethos baked into the progress model.
- The two highest rungs of the grading rigor ladder combined: CodeCrafters-style stage-gated build-your-own-primitive (black-box conformance) AND Gossip-Glomers/Maelstrom-style adversarial fault-injection checkers — the only prior-art mechanisms that are both objective AND reward from-scratch construction.
- Local-first, offline, single-learner, no gamification, nothing published to claude.ai — a workbook that respects his level, his machine, and his standing no-artifact-publish rule, with graceful-degradation (quarantine, fail-open judge) so an unreliable model never hard-fails the pipeline.

