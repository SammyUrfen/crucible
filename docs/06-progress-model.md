# 06 — Progress model: mastery, scheduling, persistence

This doc specifies the subsystem that turns a stream of graded attempts into a per-skill ability
estimate, a spaced-review schedule, and an append-only SQLite record. It picks one mastery model,
names the two it rejects and why, and pins down the precision points where "mastery gate," "ability
θ," and "review timing" would otherwise smear into each other. It is the numeric backbone under
[`01-pedagogy.md`](01-pedagogy.md) (the teach→test loop) and the state layer inside
[`03-architecture.md`](03-architecture.md).

## The mastery model: per-skill Elo-with-decay

Each skill carries a latent ability logit **θ**; each item carries a difficulty logit **b**. Expected
score is `E = σ(θ − b)` with `σ(x) = 1/(1+e^−x)`. On a graded attempt the update is a logistic fold:

```
E        = σ(θ − b)
y        = rubric_pct ∈ [0,1]          # binary correct = the y∈{0,1} special case
y_eff    = clip(y · (1 − HINT_PENALTY · hints_used), 0, 1)   # HINT_PENALTY = 0.15
K        = K0 / (1 + n_attempts_skill / RD_TAU)              # K0 = 0.6, RD_TAU = 8
θ       ← θ + K · (y_eff − E)
b       ← b − (K · K_ITEM_RATIO) · (y_eff − E)               # K_ITEM_RATIO = 0.25; FROZEN after 8 attempts
```

Four properties earn this choice, and each is why the alternatives lose:

- **It ingests rubric partial-credit natively.** `y` is a continuous score in `[0,1]`, so a rubric
  that awards 0.7 for "named the rejected alternative but not the failure-mode number" moves θ by
  0.7 of the way, not all-or-nothing. Crucible's rubrics are partial-credit by design; a binary
  observation model would discard that signal at the door.
- **It cold-starts in a handful of attempts.** The annealed gain `K = K0/(1 + n/RD_TAU)` (Glicko's
  rating-deviation idea) makes early moves large and late moves small, so θ is usefully placed after
  ~5 attempts rather than needing a training corpus. Skill θ is seeded from family priors (Go ≈ −1.5,
  C++/JS ≈ 0, Python ≈ +1.0, Java ≈ +1.2 logits) and `b` from author difficulty tiers
  (`intro = −1, core = 0, hard = +1, brutal = +2`) so his heterogeneous fluency is roughly right at
  attempt #1.
- **It emits one probabilistically-meaningful number.** `σ(θ)` reads as "P(pass a core-difficulty
  item)", which is the numbers-over-adjectives currency the analytics layer wants, and which the
  scheduler can target directly.
- **It rates the item, not just the learner.** Because `b` is estimated alongside θ, the scheduler
  can select items whose expected success sits in the ~85% desirable-difficulty band — the concrete
  anti-rote lever, not a slogan.

### Rejected: BKT (Bayesian Knowledge Tracing)

BKT's four per-skill parameters — P(L₀), P(transit), P(slip), P(guess) — are fit by EM over a
**student population**. At n = 1 with a small deck they are unidentifiable: there is no population
to disentangle "slipped" from "hasn't learned." Its observation model is **binary**, so it cannot
consume a rubric percentage. And its latent "mastered" is a **step function** — a hidden 0→1 flip
with no smooth number and no native forgetting. Every one of those is a direct mismatch here.

### Rejected: full FSRS as the mastery model

FSRS's Difficulty-Stability-Retrievability weights (17+ of them) are fit over **thousands of
reviews**, and its objective is retention of **atomic facts** — precisely the rote recall the
learner dislikes. It schedules but never rates ability against difficulty. We keep FSRS's *idea*
(an exponential memory trace for spacing) as a deliberately weaker 2-parameter half-life — see
below — but the **model of record for mastery is θ**, not a DSR state.

## θ, the gate, and half-life — three mechanisms, no double-counting

This is the precision the design most needs to state out loud (per PLAN.md R9):

- **The behavioral mastery gate is a discrete unlock latch.** Passing a module's gate (build it +
  name the rejected alternative + the failure mode + a number) flips a one-way boolean. It is *not*
  θ ≥ goal; it is a latch.
- **θ drives review scheduling, never re-locking.** A decayed θ raises a module's review pressure
  and can pull it back into the candidate pool, but **a passed latch never re-locks**. Forgetting
  costs you a review, not your unlock.
- **Half-life governs review *timing*; θ-decay governs the *ability estimate*.** They read the same
  calendar but do different jobs and must not both be charged for one forgetting event. Concretely:
  a lapse decays **H** (re-schedules the item sooner) *or* is realized as a low `y_eff` that moves
  **θ** (lowers the ability estimate) — the same missed review is one event with two projections,
  not two penalties. θ is not decayed by wall-clock on a schedule; it moves only on graded evidence.
- **Prereq-propagation prior.** Clearing a parent skill raises the *prior* θ of its children
  (edges in `skill_prereq`), so an advanced learner does not re-measure correlated skills from
  scratch. This is a one-time prior nudge on first exposure, not ongoing coupling — it informs the
  cold start, then graded evidence takes over.

### Composite items: per-objective credit assignment

A composite item (code + design prose) spans multiple objectives, possibly across different skills.
It does **not** collapse to one θ update. Each objective's skill θ is updated from **its own
per-criterion sub-score** (`per_criterion[]` in the grading envelope → the objective's skill). A
deterministic **hard-gate failure** (e.g. hidden tests red) is attributed to the **correctness skill
only** — it does not drag down the design-reasoning skill that the same attempt may have scored well.

## Persistence: append-only log, materialized skill state, config

State is SQLite. The **attempt log is the source of truth**; `skill.theta / half_life_days / due_at`
are a materialized fold over it. Every attempt row snapshots before/after, so any update is auditable
and the whole log is replayable.

```sql
CREATE TABLE domain(
  id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL,
  prior_logit REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT (datetime('now')));

CREATE TABLE skill(
  id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL REFERENCES domain(id),
  name TEXT NOT NULL, theta REAL NOT NULL, rd REAL NOT NULL,
  n_attempts INTEGER NOT NULL DEFAULT 0, half_life_days REAL NOT NULL DEFAULT 2,
  last_reviewed_at TEXT, due_at TEXT, goal_logit REAL NOT NULL DEFAULT 1.5,
  gate_passed INTEGER NOT NULL DEFAULT 0,           -- the discrete unlock latch
  updated_at TEXT NOT NULL DEFAULT (datetime('now')), UNIQUE(domain_id,name));

CREATE TABLE skill_prereq(
  skill_id INTEGER NOT NULL REFERENCES skill(id),
  prereq_id INTEGER NOT NULL REFERENCES skill(id), PRIMARY KEY(skill_id,prereq_id));

CREATE TABLE item(
  id INTEGER PRIMARY KEY, skill_id INTEGER NOT NULL REFERENCES skill(id),
  kind TEXT NOT NULL CHECK(kind IN('teach','test')), prompt TEXT NOT NULL,
  answer TEXT, rubric_json TEXT, difficulty_logit REAL NOT NULL,
  b_frozen INTEGER NOT NULL DEFAULT 0, n_attempts INTEGER NOT NULL DEFAULT 0,
  expected_time_sec INTEGER, tags_json TEXT, active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')));

CREATE TABLE session(
  id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, ended_at TEXT,
  time_budget_sec INTEGER, n_new INTEGER NOT NULL DEFAULT 0,
  n_review INTEGER NOT NULL DEFAULT 0, domains_json TEXT);

-- append-only; never UPDATEd
CREATE TABLE attempt(
  id INTEGER PRIMARY KEY, ts TEXT NOT NULL DEFAULT (datetime('now')),
  session_id INTEGER REFERENCES session(id), item_id INTEGER NOT NULL REFERENCES item(id),
  skill_id INTEGER NOT NULL REFERENCES skill(id), is_review INTEGER NOT NULL DEFAULT 0,
  rubric_pct REAL NOT NULL, hints_used INTEGER NOT NULL DEFAULT 0, time_sec INTEGER,
  expected_score REAL NOT NULL, y_effective REAL NOT NULL,
  theta_before REAL, theta_after REAL, b_before REAL, b_after REAL,
  hl_before REAL, hl_after REAL);
CREATE INDEX ix_attempt_skill_ts ON attempt(skill_id, ts);
CREATE INDEX ix_attempt_item ON attempt(item_id);

CREATE TABLE config(key TEXT PRIMARY KEY, value REAL NOT NULL);
-- seed: K0=0.6, rd_tau=8, rho=0.85, hl_growth=1.6, hl_lapse=0.4, hl_min=1, hl_max=180,
--       hint_penalty=0.15, new_per_session=1, interleave_max_run=2, b_freeze_m=8,
--       k_item_ratio=0.25, w_due=1.0, w_weak=0.6, w_new=0.4, w_desirable=0.5
```

Every tunable is a `config` row so retuning is data, not a code change. `b` is frozen after
`b_freeze_m = 8` attempts (`item.b_frozen = 1`) to kill θ/b co-drift on a small deck — this is the
single biggest correctness risk at this scale, so difficulty stops moving once it is roughly placed.

### What `recompute_from_log()` does — and does not — reproduce

`recompute_from_log()` replays the **scheduler arithmetic** from the **stored grades**. It re-folds
θ, H, and `due_at` from each attempt's stored `rubric_pct` / `hints_used` / `time_sec`, so retuning
a *scheduler* constant (K₀, half-life growth, ranking weights) is a **deterministic replay**, not a
migration — and that replay is bit-for-bit testable against live state.

It emphatically does **not re-grade**. The log stores the grade `y`, not the answer's re-derivation.
Any attempt graded by the hosted LLM-judge (see [`04-grading.md`](04-grading.md)) is not
reproducibly re-gradable — the model is hosted, metered, and may change. So **retuning a rubric or
swapping the judge model invalidates the stored `y` values** and requires a fresh re-grade pass that
is neither free nor deterministic. "Bit-for-bit" is a claim about scheduler math over frozen grades,
never about grade reproducibility.

## Spacing: a 2-parameter half-life folded on top

Per skill we track `half_life_days` (H, init 2) and `last_reviewed_at`. Retrievability proxy is
`R = 0.5^(Δt/H)`; an item is **due** when `R ≤ ρ`, i.e.
`due_at = last_reviewed + H · (ln ρ / ln 0.5)` with target retention `ρ = 0.85`. On a pass
(`y_eff ≥ 0.6`): `H ← min(H_MAX, H · HL_GROWTH · latency_factor)` with `HL_GROWTH = 1.6`. On a lapse:
`H ← max(H_MIN, H · HL_LAPSE)` with `HL_LAPSE = 0.4, H_MIN = 1`. This is deliberately a
**single-exponential** approximation of forgetting — simpler and honestly weaker than FSRS's power
law, which is why the retention-vs-ρ analytic (below) exists to expose its error rather than hide it.
`latency_factor = clip(expected_time / max(time,1), 0.5, 1.5)` lets a fast-correct grow spacing more
— the **only** place time-on-task enters state, keeping it out of θ to honor
Correctness > Performance.

## Scheduler: candidate pool → ranking → hard interleaving

**Candidate pool** = due reviews (`due_at ≤ now`) ∪ weak-skill items (`θ < goal`) ∪ new items whose
prereq skills clear a gate (`prereq θ ≥ 0` logit ≈ 50%). Each candidate gets one priority score:

```
score = w_due·overdue + w_weak·weakness + w_new·newness + w_desirable·desirable
  overdue   = max(0, (now − due_at)/H)
  weakness  = max(0, goal − θ)
  desirable = −|E_at_core − ρ|          # prefer items whose expected success ≈ 0.85
  newness   = 1 for a budgeted new item
# weights: w_due=1.0, w_weak=0.6, w_new=0.4, w_desirable=0.5
```

**Constraints:** ≤ `new_per_session` new items (default 1); ≤ `interleave_max_run = 2` consecutive
items from the same domain, else round-robin across domains. Hard interleaving improves
discrimination and serves the cross-domain (Go / Python / distributed / case-study) goal — it is a
selection constraint, not a scoring nudge, so it cannot be washed out by a high single-domain score.

## Session design (~25 min)

A session targets a 25-minute block **or** ~8–12 graded items, whichever binds first, and also ends
when all due items are cleared. Structure: one **teach-then-test** new concept (expose the primitive,
then a graded check), remainder filled by **test-first, reveal-on-miss** reviews (adversarial, no
free re-exposure) interleaved across ≥2 domains, at a ~1-new : 6-review cadence when a backlog
exists; with no backlog, up to 2 new are allowed. Streaks are **informational only and never gate
scheduling** — gating on a streak would reward the cramming the whole design fights.

## Analytics (numbers over adjectives)

- **Mastery heatmap** — domain × skill grid colored by `σ(θ)` at core difficulty, with the numeric
  value printed in each cell.
- **Model calibration** — a reliability plot of predicted `E` vs observed `y` in buckets, plus a
  **Brier score**. The model scores its own predictions; that self-honesty is the point.
- **First-try pass rate** — fraction of `is_review = 0` attempts with `y_eff ≥ pass` per domain/tier.
- **Retention check** — observed review success per interval bucket vs `ρ = 0.85`, to catch the
  single-exponential's mis-timing on long intervals.
- **Latency** — **p50/p90/p99** time-on-task per domain and difficulty tier, winsorized against
  interruption noise, with trend.
- **Weakest topic, three ways** — bottom-k by θ; skills **blocked below prereqs**; and **most
  overdue**. Three lenses because "weak" means three different actionable things.

## Limitations / open questions

- **b is "difficulty for this one user," never absolute** — do not export it as objective item
  difficulty; on a tiny deck with < 8 attempts it is still co-drifting with θ.
- **Cold start is noisy for ~5 attempts/skill** — family priors + high annealing K mitigate but do
  not remove this; early scheduling can misfire and should be read as provisional.
- **Single-exponential forgetting mis-times very long intervals** — the retention-vs-ρ analytic
  surfaces the error; it is not corrected.
- **Multi-skill credit split beyond the composite rule is unmodeled** — items that commonly span
  skills would want a weighted junction table; deferred until the deck shows it is needed.
- **Open:** intended skill↔item granularity; whether `ρ = 0.85 / 25 min` is right or a harder ~0.80
  band is wanted; whether `teach`-kind items are graded at all or count only as exposure that unlocks
  the paired test; and how `rubric_pct`'s grader noise (self / LLM / deterministic) should set a
  slip/guess floor on `E`.
