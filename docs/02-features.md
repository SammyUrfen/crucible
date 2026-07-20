# 02 — Prototype Feature Spec

This doc enumerates what the Crucible prototype builds, in priority order, and — for each feature — *why* it exists and the named alternative it beats. It is the core scoping deliverable. The priorities below deliberately diverge from the first-draft feature list: an adversarial critique reordered them so the prototype proves *learning value* before it builds *grading machinery*. Where this doc states a priority, that ordering is binding; see [`09-roadmap.md`](09-roadmap.md) for the phased build sequence and [`../PLAN.md`](../PLAN.md) for the R1–R10 resolutions the reordering rests on.

Everything is anchored on one vertical slice: the **Go concurrency-discrimination module** — "select among `sync.Mutex` / channel / `atomic` / `errgroup` for an unlabeled contention scenario, then build a leak-free goroutine lifecycle under `context` cancellation and prove it with `go test -race`." It is his genuine gap (Go true-beginner), it ties to an active project (`conclave`), and it exercises every grading strategy at once. That slice is the spine every feature below is measured against.

## Priority table

| Feature | Priority | One-line rationale |
|---|---|---|
| Content-first Go pilot (10–15 lessons) | **P0** | Prove he studies daily for 2+ weeks before building any engine — the #1 risk is building the platform instead of learning. |
| Content-as-data lesson files (YAML→JSON) | **P0** | Diffable, git-versioned, executable-spine-carrying source of truth; the substrate everything else reads. |
| Executable green-gate (`make gate`) | **P0** | Makes a broken or ungradeable lesson *impossible to commit* — correctness by construction, zero LLM in the loop. |
| Deterministic grader (choice + derived-output) | **P0** | The objective correctness gate; expected outputs machine-derived, never hand-typed. |
| Plain-local code grader (`go test`/`pytest` + timeout + `ulimit`) | **P0** | His own code on his own box ≈ zero RCE threat; a hardened container is premature for v1. |
| CLI session runner (teach-then-test; test-first review) | **P0** | Retrieval practice as the delivery loop; CLI is the fastest path to a usable slice. |
| Append-only attempt log + Elo-with-decay mastery fold | **P0** | One self-calibrating number from n=1, replayable from the log. |
| Hosted LLM-judge (reference-grounded) | **P1** | The only defensible way to grade design judgment; adds cost + network, so it comes after the free graders work. |
| Two structural anti-gaming guards | **P1** | Reference-grounding + deterministic-wins prevent false confidence at near-zero cost. |
| Scheduler: due/weak/new + interleaving + spacing | **P1** | Interleaving trains *selecting* the primitive; the 85% band fights rote. |
| Web-UI session runner (CLI→web) | **P1** | The stated target interface; CLI is the on-ramp, not the destination. |
| Analytics dashboard (local HTML) | **P1** | Numbers over adjectives, including the judge scoring itself via Brier. |
| Hardened sandbox (rootless + seccomp + cgroups) | **P2** | Only earns its cost once AI-authored or shared content exists. |
| AI-authoring pipeline (bounded self-repair) | **P2** | Scales content once the gate can guarantee no broken lesson ships. |
| Gold-set calibration harness | **P2** | Deferred until there is evidence he'd game the judge. |
| Domain expansion (Python-deep, distributed, case-studies) | **P2** | Proves the engine is domain-agnostic — after it works on one. |
| Four new question types (paper / capacity / refactor / benchmark) | **P1–P2** | Backlog; strategy-mapped below. |
| Thin FSRS deck for rote Go idioms | **P2** | The small rote residue, kept off the design track. |

---

## P0 — prove learning value

### Content-first Go pilot (10–15 lessons)
Hand-author 10–15 real Go lessons in the concurrency-discrimination vertical, tied to `conclave`, and **use them daily for 2+ weeks**, grading code with plain `go test`. This is the true P0 and it precedes the grading cathedral.

**Why.** The single largest failure mode is that building the engine scratches his systems-builder itch, so he "finishes" the fun part and never sustains the boring part — the tool becomes the procrastination. The only way to de-risk that is to force the *content* and *daily use* to exist first, on the cheapest possible grader, and confirm the behavior before spending weeks on infrastructure. If he won't do 15 lessons with `go test`, no sandbox will save it.

**Rejected alternative — *engine-first, content-last* (the first-draft sequence).** Building the sandbox, anti-gaming, and mastery fold across Phases 0–4 *before* real content means he hand-authors a handful of lessons, hits the end after 3–5 sessions, and the engine is still "impressive" with nothing left to teach. Also rejected: a **Python-deep pilot** — lower learning ROI (Python is already one of his deepest languages) and it under-stresses the on-ramp asymmetry that Go exposes.

### Content-as-data lesson files (YAML → JSON)
One YAML file per lesson under `content/<track>/<id>.yaml`, co-locating teach blocks, worked examples, ≥1 assessment, a per-assessment rubric, the reference answer/solution, and hidden tests. The gate compiles each to `build/<id>.json` for the runtime. `schema_version` + per-lesson `content_rev`; git is the version store. Field names follow the canonical schema at [`../content/examples/go04-concurrency-discrimination.yaml`](../content/examples/go04-concurrency-discrimination.yaml).

**Why.** YAML block scalars beat raw JSON for embedded code (his own `AUTHORING.md` flags JSON escaping as a pain point), while the compiled JSON keeps a fast, formal schema gate. Compiling *inside* the gate stops anyone hand-editing the JSON and drifting it from source.

**Rejected alternative — a *database of content*** (opaque, un-diffable, un-reviewable — you lose code review and git history) and **Markdown-with-front-matter** (cannot express the executable grading spine: hidden tests, derived outputs, weighted rubrics).

### Executable green-gate (`make gate`)
Two layers: a declarative JSON Schema for field shape, plus a procedural validator for what a schema cannot express — coverage-closure (every objective taught *and* assessed), gradeable-or-reject, reference-reproduces (it *executes* every reference solution and predict-output program), `debug_this`-buggy-must-fail, rubric-passes-own-reference, and leak-guard. Non-zero exit on any error; warnings non-blocking.

**Why.** This is his numeric set-containment anti-fabrication guard generalized to teaching content: a lesson with an orphan objective, a reference that fails its own hidden tests, a fake debug bug, or a rubric its own gold answer can't clear *cannot be committed*. Correctness is proven by construction with zero model in the loop.

**Rejected alternative — *schema-only validation*** (cannot execute a reference or diff a coverage graph) and **trusting the authoring LLM's self-report** (the exact reward-hacking surface to avoid).

### Deterministic grader (choice + derived-output)
Grades MCQ / multi-select by exact or Jaccard match, and `predict_output` by executing the program and comparing stdout to the *derived* expected value. No model call.

**Why.** Where a computable oracle exists, a string/float compare is faster, cheaper, and strictly more reliable than a model. Expected outputs are machine-derived at gate time, never hand-typed — this is the anti-fabrication core.

One caveat, per R4: the Go `predict_race_verdict` item lives here but is **probabilistic, not a clean oracle**. `go test -race` has false negatives (it only reports interleavings it observes) and Go randomizes map iteration order, so the verdict is derived over **N ≫ 2 iterations** using reliably-tripping race constructions, and reported as probabilistic — not as "the cleanest deterministic signal." A 2-run stdout-diff nondeterminism check is unsound and is replaced by many-iteration runs plus static flagging of map-range / goroutine / time / float patterns.

**Rejected alternative — *routing MCQ/numeric to the LLM judge*** (slower, costlier, and less reliable than a comparison a machine can decide exactly).

### Plain-local code grader (`go test` / `pytest` + timeout + `ulimit`)
v1 runs learner code and locked references with **plain local `go test -race` / `pytest`, a wall-clock timeout, and resource `ulimit`s**. Public example tests ship for iteration; grading tests stay hidden, injected at grade time; the minimal failing input is surfaced on failure. Property / differential tests vs a locked reference close the "hardcode the visible cases" hole.

**Why (R3).** The code being run is *his own answers on his own machine* — the RCE threat is near-zero for v1. A wall-clock timeout plus `ulimit` contains the realistic failure modes (infinite loop, runaway memory) without a container. This removes the single hardest blocker from the path to first learning value. The genuine untrusted surface (AI-authored references) does not exist until much later; the hardened sandbox is demoted to P2 and budgeted as its own project then.

**Rejected alternative — a *defense-in-depth container from day one*** (rootless + seccomp + gVisor + cgroups): a security cathedral against a threat that doesn't exist yet, on the critical path to any learning. Also rejected: **in-process / language-level sandboxing** (does not exist in a usable form, especially for Python) and **visible-only tests** (the learner overfits to the checker). See [`03-architecture.md`](03-architecture.md) for the swappable language-runner seam and [`04-grading.md`](04-grading.md) for the hidden-test isolation contract.

### CLI session runner (teach-then-test new; test-first review)
Renders exposition for a new concept then a graded check (generate-before-reveal); reviews are test-first, reveal-on-miss — adversarial, no free re-exposure. Time-boxed to ~25 min / 8–12 items.

**Why.** Retrieval practice under desirable difficulty is the delivery loop, and it matches his build-and-verify style. CLI is his daily driver and the fastest path to a working slice.

**Rejected alternative — *read-then-summarise*** (the illusion-of-competence trap he distrusts) and a **GUI-first shell** (slower to build; the web UI is the eventual target, not the on-ramp — see the Web-UI feature under P1).

### Append-only attempt log + Elo-with-decay mastery fold
Every graded attempt is appended immutably. Per-skill **θ** and per-item difficulty **b** update by an annealed-K logistic rule that ingests rubric partial-credit `y ∈ [0,1]`; θ / half-life / `due_at` are a materialized fold with a deterministic `recompute_from_log()`.

**Why.** One probabilistically-meaningful number that cold-starts at n=1 and self-calibrates, in SQLite, replayable. Per R9, keep two facts precise: the behavioral mastery *gate* is a discrete **unlock latch**, while continuous θ drives **review scheduling** — a decayed θ schedules review but does **not** re-lock an already-passed module; half-life governs review *timing* and θ-decay governs the *ability estimate*, and they do not double-penalize one forgetting event. Per R9 also: `recompute_from_log()` replays the **scheduler arithmetic** from stored grades — it does **not** re-grade, so retuning a rubric or swapping the judge model invalidates stored grades and needs a (non-free, non-deterministic) re-grade pass. Full treatment in [`06-progress-model.md`](06-progress-model.md).

**Rejected alternative — *BKT*** (slip/guess/learn params are unidentifiable at n=1; binary observation model can't ingest a rubric %; latent mastery is a step function) and **full FSRS as the mastery model** (17+ DSR weights need thousands of reviews and it rates recall of atomic facts — the rote he dislikes).

---

## P1 — grade design judgment, pace the curriculum, move to the web

### Hosted LLM-judge (reference-grounded)
For explain-it-back / name-the-rejected-alternative / design essays, invoke a **hosted** Claude model (via `claude -p` headless or the Anthropic Messages API) with a per-criterion rubric and the *locked reference answer* always in context. Forced JSON output, reasoning through each criterion before the score, sampling capped at **3** with early-stop on agreement, median + spread, abstain on wide spread.

**Why.** Design judgment has no computable oracle; a reference-grounded model is the only defensible grader. Per R1 this judge is **not offline** — `claude -p` and the Messages API are network calls to Anthropic's hosted models, metered in USD. That has three binding consequences, all engineered for here: (a) a per-lesson and per-session **USD cost ceiling** with `total_cost_usd` tracking; (b) a **network-down fail-open** path — fall back to self-grade against the shown reference, mark confidence LOW, never hard-fail the session; (c) a genuinely-local model (Ollama / llama.cpp) is an *optional*, materially weaker alternative that would need trust re-baselining — offered, not defaulted to. Per R5, cost and latency are budgeted: cap samples at 3, parallelize them, grade asynchronously so the session keeps moving, and track grading-latency p50/p90/p99 as a first-class health metric. This is why the judge is P1, not P0 — the pilot proves value first on free graders.

**Rejected alternative — a *reference-free judge*** (self-play drives pass rate ~0.72→0.94 at ~0.20 true accuracy — it scores persuasiveness, not correctness). Also rejected framing: calling the judge "offline / self-hosted," which R1 forbids. Design detail in [`04-grading.md`](04-grading.md).

### Two structural anti-gaming guards
Exactly two, both near-free: **reference-grounding** (the judge always sees the locked reference and grades against it) and **deterministic-wins** (the judge may only *lower or flag* a grade, never *raise* a deterministic test/exact-match verdict). Learner answer text is also sanitized into a delimited data channel, never the instruction channel.

**Why (R7).** The self-gaming premise is weak: the grade's only value is accurate self-knowledge, which he *wants*, and he controls every tunable (`pass_threshold`, K, goal θ) anyway — so gold-sets and retry-logging can't stop the one "gaming" that matters (lowering the bar or not opening the app). The real failure mode is disengagement plus lenient-judge false confidence, and the two cheap guards already cover the latter.

**Rejected alternative — the *full gold-set-reproduction-before-trust harness + retry-trace machinery*** (over-built for the actual risk; deferred to P2 until there's evidence he'd game it). Also rejected: **an ensemble marketed as objectivity** (majority vote reduces random noise but reinforces shared systematic bias).

### Scheduler: due/weak/new priority + interleaving + spacing
Candidate pool = due reviews ∪ weak skills (θ < goal) ∪ prereq-cleared new items; ranked by `w_due·overdue + w_weak·weakness + w_new·newness + w_desirable·(target E ≈ 0.85)`; caps new items (default **1/session**) and forbids **>2 consecutive same-domain** items; an FSRS-lite 2-param half-life drives `due_at`.

**Why.** Interleaving trains *selecting* the primitive — his own mutex-vs-channel-vs-atomic habit — and the ~85% success band keeps items in the desirable-difficulty range that fights rote. Per R9, a prereq-propagation prior means clearing a parent raises children's prior.

**Rejected alternative — *fixed-calendar review*** (ignores mastery) and **blocking one topic to completion** (worse discrimination and transfer than interleaving).

### Web-UI session runner (CLI → web)
Port the session loop to the target **local web app** (FastAPI backend + lightweight local web UI) once the CLI slice is proven. Same grading engine and data channel; a hand-rolled light/dark theme, nothing published to claude.ai.

**Why.** The web UI is the stated target interface; the CLI is the fastest on-ramp, not the destination. Building it after the engine works avoids UI churn while the grading contract is still moving.

**Rejected alternative — *web-first from day one*** (couples UI iteration to an unstable grading contract, slowing the pilot).

### Analytics dashboard (local HTML)
A local HTML file: mastery heatmap of σ(θ) with numeric labels; a model-calibration reliability plot + **Brier score**; retention-vs-ρ check; grading-latency **p50/p90/p99**; weakest-topic three ways (bottom-k θ, blocked-below-prereq, most-overdue); a per-module **Limitations** panel.

**Why.** Numbers over adjectives — and the model scoring *itself* via Brier is the calibrated-claims move he values. Written as a local file per his no-publish rule.

**Rejected alternative — *adjective progress bars / "you're doing great"*** (uncalibrated; he'd catch it immediately).

---

## P2 — earn the machinery

### Hardened sandbox (rootless + seccomp + cgroups)
Defense-in-depth container (rootless + seccomp + no-network + read-only rootfs + cgroup CPU/mem/pid caps + wall-clock timeout), swapped in behind the same runner seam. Promoted here per R3 — it only earns its cost once **AI-authored or shared** content exists. When built, two problems must be solved *first*: (a) the Go **no-network module-cache** problem — a pre-baked `GOMODCACHE` with `GOFLAGS=-mod=vendor` and `GOPROXY=off`, since a naive no-net sandbox fails on any non-stdlib import; and (b) **panic / compile-error source-leak scrubbing** — Go prints `file:line` and can dump a hidden-test file's source on a compile error, so scrubbing needs a dedicated test that a hidden-test compile error does *not* leak. **Rejected alternative — front-loading this in v1** (a threat that doesn't exist yet on the critical path).

### AI-authoring pipeline (bounded self-repair, quarantine)
LLM skeleton → structural preflight (no LLM) → executable materialization (run references in the sandbox) → rubric self-consistency → advisory adversarial audit → merge; bounded to **N=3** retries then **quarantine** to a review queue, never hard-failing the batch. **Why:** scales authoring while the green-gate guarantees no broken lesson ships — graceful degradation with a surfaced reason. **Rejected alternative — *trusting AI-authored lessons without the executable gate***, and **hard-failing a 200-lesson batch on one bad draft**. See [`05-content-model.md`](05-content-model.md).

### Gold-set calibration harness
The deferred half of anti-gaming: hand-grade ~15–20 representative past answers and require the judge to reproduce that ordering within tolerance before trusting it, re-run on any model/rubric change. Deferred per R7 until there's evidence of gaming; a periodic hand-audit of a random sample of judge PASSes covers the interim.

### Domain expansion (Python-deep, distributed, case-studies)
Second/third tracks behind the same engine and router: Python internals (deep from day one, hidden-test batteries + `mypy --strict`), a distributed-internals track, and defend-and-extend case-studies mined from his own repos (WALterDB 2PL, GOOGLY ring, TraceLens reward shaping). Per R6, **orchestrate over external labs — MIT 6.824's autograder, Jepsen Maelstrom / Fly.io Gossip Glomers, CodeCrafters — for code and distributed conformance**, and hand-roll a grader only where none exists. Crucible's unique additions are the design-defense judge on his own repos, spacing/interleaving, mastery/θ, and the rejected-alternative rubric. **Rejected alternative — *re-implementing 6.824/Maelstrom/CodeCrafters graders*** (the harness crowds out the studying) and **building all four tracks before the engine is proven on one**.

### Thin FSRS deck for rote Go idioms
A capped spaced-repetition deck for *only* genuinely-memorizable atoms (stdlib signatures, error-wrapping idioms, named gotchas), target retention 0.85–0.90. Design judgment never enters the scheduler. **Rejected alternative — *per-user FSRS optimization*** (on a sub-1000-card solo deck the famous 20–30% saving is ~20 s/day of noise).

---

## Four new question types (R8 backlog)

The first taxonomy missed four types the curriculum needs. Each is added with an explicit strategy mapping; capacity-derivation is P1-eligible (deterministic, cheap), the three judge-graded types land with the distributed/design tracks at P2.

| Type | Strategy | What it grades | Priority |
|---|---|---|---|
| Paper / reading-comprehension | `llm_judge` (reference-grounded) | Absorbed a safety argument or invariant from DDIA / Raft / Dynamo / Spanner | P2 |
| Capacity / back-of-envelope | `deterministic` (worked-formula oracle, numeric-with-tolerance) | Bottleneck math, crossover point, load variance — a computable number within tolerance | P1 |
| Refactor-to-idiomatic | `llm_judge` | Turning a working-but-unidiomatic solution idiomatic — not captured by hidden tests | P2 |
| Benchmark-reproduction | Hybrid (deterministic harness emits p50/p99 + judge on the written defense) | Producing *and defending* a reproducible measurement | P2 |

**Why these four.** The distributed track rests on papers, so comprehension needs its own reference-grounded item; capacity math is repeatedly demanded and has a clean formula oracle, so it should never touch the judge; idiom isn't visible to hidden tests, so it needs a judge; and the A/B modules ask him to *commit a reproducible harness*, which only a hybrid measure-and-defend item grades. Full taxonomy and routing in [`04-grading.md`](04-grading.md) and [`05-content-model.md`](05-content-model.md).

---

## Limitations / open questions

- **The pilot could still fail its own premise.** If he does not sustain 2+ weeks of daily use on 10–15 `go test`-graded lessons, that is a *signal to stop*, not to build more engine. The prototype's first job is to surface that honestly.
- **Per-lesson authoring cost is unquantified.** The green-gate makes each lesson *harder* to author (every reference must execute green, every rubric must clear its own gold). No hours-per-lesson estimate or ordered ~50-lesson backlog exists yet; this, not the sandbox, is the real throughput bottleneck. Open question: which 50 lessons, in what order.
- **The Go race verdict is probabilistic.** Even at N ≫ 2 iterations, `go test -race` false negatives mean a green run on genuinely racy code is possible; the item is reported with confidence, never as a clean oracle.
- **`recompute_from_log()` reproduces scheduler arithmetic, not grades.** Judge-graded attempts are non-reproducibly re-gradable (hosted, non-deterministic, model may change). "Bit-for-bit" applies to θ from stored grades only.
- **A single-node lab is not "production-grade."** Every module ships a Limitations panel naming what the exercise does *not* prove (e.g. an aiosqlite-green test says nothing about asyncpg concurrency).
- **Content aging is a maintenance model, not a footnote (R10).** Pinned toolchains (Go 1.22+, pydantic-v2, SQLAlchemy 2.0, pion) age; a bump can turn dozens of green lessons red at once. The plan needs changed-only / incremental gate execution, per-track toolchain pins, and a periodic "gate against latest toolchain" job.

See [`09-roadmap.md`](09-roadmap.md) for how these features sequence into phases, and [`../PLAN.md`](../PLAN.md) for the binding R1–R10 resolutions.
