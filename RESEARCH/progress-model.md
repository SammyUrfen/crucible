# Progress / Mastery / Scheduling Subsystem

> Research track. Faithful rendering of the agent's structured findings.

**Dimension:** Progress / Mastery / Scheduling subsystem for a single-user teach-and-test workbook

## Summary

Recommendation: model per-skill mastery as an Elo-with-decay latent — a continuous ability logit θ per skill updated against a difficulty logit b per item via a logistic (Elo/Glicko-lite) rule, with a 2-parameter half-life memory state (H, last_reviewed) folded on top to drive spacing. Pick Elo (not BKT, not full FSRS) because it (a) cold-starts and self-calibrates from a handful of attempts, which BKT's 4 per-skill slip/guess/learn params and FSRS's ~17 DSR params cannot at n=1 on a small deck; (b) produces one probabilistically-meaningful number (P(correct on a b-difficulty item)) that matches his numbers-over-adjectives taste; (c) natively consumes rubric partial-credit as a continuous score y∈[0,1] rather than BKT's binary observations; and (d) simultaneously rates *item* difficulty, letting the scheduler target the ~85% desirable-difficulty band that fights the rote recall he dislikes. Mastery is a deterministic pure fold over an append-only attempt log (event-sourced, replayable — recompute θ from scratch if you retune K), which matches his from-scratch/verification ethos. The scheduler blends due-review pressure, weakness, and a capped "one new + spaced reviews" cadence, with hard interleaving across domains. Deliberately accepted simplifications (single-exponential forgetting instead of FSRS's power law; θ/b co-drift on tiny decks mitigated by freezing b) are named, not hidden.

## Key findings

### Mastery model = Elo-with-decay (θ per skill, b per item); BKT and FSRS explicitly rejected

θ_skill and b_item live on a logit scale. Expected score E = σ(θ−b), σ(x)=1/(1+e^−x). REJECTED — BKT/knowledge-tracing-lite: its P(L0)/P(T)/P(slip)/P(guess) are fit by EM over a *student population*; with n=1 and few items they are unidentifiable, and its observation model is binary so it cannot ingest rubric %. Its latent 'mastered' is also a step function — no smooth number, no forgetting. REJECTED — FSRS memory-state: purpose-built for pure-recall flashcards, its Difficulty/Stability/Retrievability weights are fit over thousands of reviews and it optimizes retention of atomic facts (exactly the rote he dislikes); it schedules but never rates ability-vs-difficulty. Elo keeps ONE latent that both scores mastery and calibrates difficulty, cold-starts in a few attempts, and reads as a probability.

*Source:* Elo (1978) / Glicko (Glickman 1999); Corbett & Anderson 1995 (BKT); FSRS/SuperMemo DSR

### Attempt→mastery update rule (correct/incorrect, rubric %, hints, time-on-task all wired in)

On each graded attempt: (1) E=σ(θ−b). (2) y=rubric_pct∈[0,1] (binary correct=1/0 is the special case — this is why Elo beats binary BKT). (3) hint discount: y_eff=clip(y·(1−HINT_PENALTY·hints_used),0,1), HINT_PENALTY=0.15 — a hinted-correct is weaker evidence. (4) annealing gain K=K0/(1+n_attempts_skill/RD_TAU) (Glicko rating-deviation idea: big early moves, small once well-estimated), K0=0.6, RD_TAU=8. (5) θ←θ+K·(y_eff−E). (6) b←b−(K·0.25)·(y_eff−E) but FROZEN after M=8 item-attempts (see gotcha). (7) TIME-ON-TASK is kept OUT of θ to honor Correctness>Performance — it only modulates half-life growth via latency_factor=clip(expected_time/max(time,1),0.5,1.5) and feeds p50/p90/p99 analytics.

*Source:* Design; Glicko RD annealing; his stated value order Correctness>Reliability>UX>Maintainability>Performance

### Spacing = 2-param half-life folded on Elo (FSRS-*lite*, not FSRS)

Per skill track H (half_life_days, init 2) and last_reviewed_at. Retrievability proxy R=0.5^(Δt/H). Due when R≤ρ, ρ=target retention 0.85 (desirable-difficulty band): due_at = last_reviewed + H·(ln ρ/ln 0.5) days. On pass (y_eff≥0.6): H←min(H_MAX, H·HL_GROWTH·latency_factor), HL_GROWTH=1.6 (fast-correct grows spacing more). On lapse: H←max(H_MIN, H·HL_LAPSE), HL_LAPSE=0.4, H_MIN=1. This is a deliberate single-exponential approximation of forgetting — simpler than FSRS's power law and honestly weaker; I keep the mastery model of record = θ and treat H purely as a scheduler input.

*Source:* Ebbinghaus / spacing effect; Bjork desirable difficulty (~85% success)

### Scheduler: one priority score per candidate, then hard interleaving

Candidate pool = due reviews (due_at≤now) ∪ weak-skill items (θ<goal) ∪ new items whose prereq skills clear a gate (prereq θ≥0 logit ≈ 50%). score = w_due·overdue + w_weak·weakness + w_new·newness + w_desirable·desirable, where overdue=max(0,(now−due_at)/H), weakness=max(0,goal−θ), desirable=−|E_at_core−ρ| (prefer items whose expected success ≈85% — not rote-easy, not impossible), newness=1 for a budgeted new item. Weights w_due=1.0,w_weak=0.6,w_new=0.4,w_desirable=0.5 (config table). CONSTRAINTS: ≤ new_per_session new items (default 1); ≤ interleave_max_run=2 consecutive items from the same domain, else round-robin domains — interleaving improves discrimination and matches his cross-domain (cloud/DevOps/distributed) goal.

*Source:* Rohrer & Taylor 2007 (interleaving); design

### Session design: mixed teach+test, time-boxed, one-new + spaced-reviews cadence

Target = 25-min block OR ~8–12 graded items (config). Structure: 1 TEACH-then-test new concept, remainder filled by spaced reviews interleaved across ≥2 domains, cadence ~1 new : 6 review when a backlog exists; if no due backlog, allow up to 2 new. Item kinds: new items are teach→test (exposition of the primitive, then a graded check — fits 'explain the primitive'); reviews are test-first, reveal-on-miss (adversarial, no free re-exposure). Session ends on time-box OR item-budget OR all-due-cleared, and is logged for analytics. Streaks are informational only and NEVER gate scheduling — gating on streaks would incentivize the cramming/rote he dislikes.

*Source:* Design; his learn-by-building + adversarial-verification style

### Analytics tuned to numbers-over-adjectives

(1) Mastery heatmap: domain×skill grid colored by σ(θ) at core difficulty, numeric labels shown. (2) MODEL CALIBRATION: reliability plot of predicted E vs observed y in buckets + Brier score — the model scores itself, which he'll value. (3) Retention check: observed review success rate per interval bucket vs ρ=0.85 (is spacing calibrated?). (4) Latency: p50/p90/p99 time-on-task per domain and per difficulty tier, with trend. (5) Weakest-topic surfacing three ways: bottom-k by θ, skills blocked-below-prereqs, and most-overdue. (6) Throughput: items/session, new-introduced/week, reviews-cleared vs due. (7) Coverage: %% of deck with θ≥goal per domain + a rough time-to-mastery estimate. (8) Streaks: current + longest consecutive-day, informational.

*Source:* Design; Brier score; his p50/p99 reporting habit

### Persisted state = SQLite; append-only attempt log is source of truth, θ is a fold

DDL:

CREATE TABLE domain(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, prior_logit REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT (datetime('now')));

CREATE TABLE skill(id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL REFERENCES domain(id), name TEXT NOT NULL, theta REAL NOT NULL, rd REAL NOT NULL, n_attempts INTEGER NOT NULL DEFAULT 0, half_life_days REAL NOT NULL DEFAULT 2, last_reviewed_at TEXT, due_at TEXT, goal_logit REAL NOT NULL DEFAULT 1.5, updated_at TEXT NOT NULL DEFAULT (datetime('now')), UNIQUE(domain_id,name));

CREATE TABLE skill_prereq(skill_id INTEGER NOT NULL REFERENCES skill(id), prereq_id INTEGER NOT NULL REFERENCES skill(id), PRIMARY KEY(skill_id,prereq_id));

CREATE TABLE item(id INTEGER PRIMARY KEY, skill_id INTEGER NOT NULL REFERENCES skill(id), kind TEXT NOT NULL CHECK(kind IN('teach','test')), prompt TEXT NOT NULL, answer TEXT, rubric_json TEXT, difficulty_logit REAL NOT NULL, b_frozen INTEGER NOT NULL DEFAULT 0, n_attempts INTEGER NOT NULL DEFAULT 0, expected_time_sec INTEGER, tags_json TEXT, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT (datetime('now')));

CREATE TABLE session(id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, ended_at TEXT, time_budget_sec INTEGER, n_new INTEGER NOT NULL DEFAULT 0, n_review INTEGER NOT NULL DEFAULT 0, domains_json TEXT);

CREATE TABLE attempt(id INTEGER PRIMARY KEY, ts TEXT NOT NULL DEFAULT (datetime('now')), session_id INTEGER REFERENCES session(id), item_id INTEGER NOT NULL REFERENCES item(id), skill_id INTEGER NOT NULL REFERENCES skill(id), is_review INTEGER NOT NULL DEFAULT 0, rubric_pct REAL NOT NULL, hints_used INTEGER NOT NULL DEFAULT 0, time_sec INTEGER, expected_score REAL NOT NULL, y_effective REAL NOT NULL, theta_before REAL, theta_after REAL, b_before REAL, b_after REAL, hl_before REAL, hl_after REAL);
CREATE INDEX ix_attempt_skill_ts ON attempt(skill_id, ts);
CREATE INDEX ix_attempt_item ON attempt(item_id);

CREATE TABLE config(key TEXT PRIMARY KEY, value REAL NOT NULL);
-- seed: K0=0.6, rd_tau=8, rho=0.85, hl_growth=1.6, hl_lapse=0.4, hl_min=1, hint_penalty=0.15, new_per_session=1, interleave_max_run=2, b_freeze_m=8, k_item_ratio=0.25, w_due=1.0, w_weak=0.6, w_new=0.4, w_desirable=0.5

skill.theta/half_life/due_at are a MATERIALIZED fold over attempt; attempt.*_before/*_after snapshots make every update auditable and let you replay the whole log to recompute θ after retuning K.

*Source:* Design; event-sourcing / his replayable-determinism taste

## Recommendations

- Adopt Elo-with-decay as the single mastery model; store b seeded from author difficulty tiers {intro=-1, core=0, hard=+1, brutal=+2} and skill θ seeded from family priors (Go≈-1.5, C++/JS≈0, Python≈+1.0, Java≈+1.2 logits) so his heterogeneous fluency is right from attempt #1.
- Make the attempt table append-only and compute θ/H/due_at as a pure fold; expose a `recompute_from_log()` so retuning any constant is a deterministic replay, not a migration — this is directly testable and matches his verification ethos.
- Freeze item difficulty b after b_freeze_m=8 attempts (or update it at 0.25×K) to kill θ/b co-drift on a tiny deck; treat b as 'difficulty for him', never claim absolute difficulty.
- Keep time-on-task strictly out of θ (Correctness>Performance); use it only to modulate half-life growth and as p50/p90/p99 analytics, and winsorize it to blunt interruption noise.
- Set target retention ρ=0.85 and target item selection at E≈0.85 so sessions sit in the desirable-difficulty band — this is the concrete anti-rote lever he asked for.
- Cap new items at 1/session by default with a 1-new:6-review cadence and hard domain-interleaving (≤2 consecutive same-domain); keep streaks informational so nothing rewards cramming.
- Ship a model-calibration report (reliability plot + Brier score) as a first-class analytic — the model scoring itself is the honest, calibrated-claims move he values.

## Proposed modules

### Mastery Engine (Elo-with-decay fold)

**Objectives**

- Compute E=σ(θ−b), apply annealed-K update to θ and (unless frozen) b
- Fold rubric %, hint discount, and lapse/pass into θ and half-life H
- Expose pure recompute_from_log() over the append-only attempt table

**Testable skills**

- σ and logistic-update numerics vs hand-computed values
- K anneals monotonically as n_attempts grows (Glicko-lite)
- recompute_from_log() reproduces live θ bit-for-bit (determinism)
- rubric_pct=partial credit moves θ proportionally; hints discount y_eff
- half-life grows on pass, floors at H_MIN on lapse

### Scheduler / Selector

**Objectives**

- Assemble due∪weak∪new candidate pool with prereq gating
- Rank by w_due·overdue + w_weak·weakness + w_new·newness + w_desirable·desirable
- Enforce new-per-session cap and domain interleaving

**Testable skills**

- Overdue reviews outrank fresh weak items when backlog exists
- No more than interleave_max_run consecutive same-domain items
- New item withheld until prereq skills clear the gate
- Selection concentrates chosen items near E≈ρ (desirable difficulty)

### Session Builder

**Objectives**

- Build a teach+test mixed session within time/item budget
- Apply 1-new + spaced-review cadence; teach-then-test new, test-first review
- Open/close session rows and tag domains covered

**Testable skills**

- Session respects time_budget and item budget
- Exactly ≤ new_per_session new items introduced
- Ends on all-due-cleared even under budget

### Analytics / Reporting

**Objectives**

- Mastery heatmap σ(θ) per domain×skill with numeric labels
- Model calibration (reliability + Brier), retention-vs-ρ, latency p50/p90/p99
- Weakest-topic and most-overdue surfacing; streaks (informational)

**Testable skills**

- Brier score matches manual computation on a fixed attempt fixture
- p50/p90/p99 latency correct on known distribution
- Weakest-k and blocked-below-prereq lists are correct on a seeded DAG

### Persistence (SQLite, event-sourced)

**Objectives**

- DDL with append-only attempt log as source of truth
- Materialized θ/H/due_at on skill; per-attempt before/after snapshots
- Config table of all named constants for tuning

**Testable skills**

- Foreign-key + CHECK constraints reject malformed rows
- Fold over attempt reproduces skill row state
- Retuning a config constant + replay changes θ deterministically

## Risks & gotchas

- θ/b co-drift: with few items per skill, ability and difficulty are jointly under-identified and can drift together. Mitigation = seed b from author tiers, update it at 0.25×K, and freeze it after 8 attempts. This is the single biggest correctness risk at small-deck scale.
- Cold start: no population to fit priors; a bad seed can mis-schedule early sessions. Mitigation = family priors + high initial K that anneals; expect the first ~5 attempts/skill to be noisy and say so.
- Single-exponential forgetting is a deliberate simplification — real forgetting is closer to a power law (FSRS). It will mis-time very long intervals; the retention-vs-ρ analytic is there to expose that error rather than hide it.
- b is 'difficulty for this one user', not absolute — do not report or export it as objective item difficulty.
- Time-on-task is noisy (interruptions, context-switching). Keeping it out of θ and winsorizing it for analytics is intentional; don't let it leak into correctness scoring.
- Streak mechanics can nudge toward cramming/rote he dislikes — kept informational and never used to gate selection; revisit if it starts driving behavior.
- Multi-skill items need a credit-assignment rule (equal or weighted split of y across tagged skills) — unmodeled in the base schema; add a junction table if items commonly span skills.

## Open questions

- What is the intended skill↔item granularity, and will items ever tag multiple skills (needs credit-split)?
- Preferred target retention ρ and daily time budget — is 0.85 / 25 min right, or does he want a harder ~0.80 desirable-difficulty band?
- Should teach-kind items be graded at all, or count only as exposure that unlocks the paired test?
- How is rubric_pct produced — self-graded, LLM-graded, or deterministic checker — and does that grader's noise warrant a slip/guess floor on E?
- Deck taxonomy for the cross-domain goal (cloud / DevOps / distributed internals): what are the top-level domains and their prereq DAG edges?

## Citations

- Elo, A. (1978). The Rating of Chessplayers, Past and Present
- Glickman, M. (1999). Parameter estimation in large dynamic paired comparison experiments (Glicko / rating deviation)
- Corbett & Anderson (1995). Knowledge Tracing: Modeling the Acquisition of Procedural Knowledge (BKT)
- FSRS / SuperMemo DSR spaced-repetition memory model (Difficulty-Stability-Retrievability)
- Bjork & Bjork — Desirable Difficulties and the ~85% optimal success band
- Rohrer & Taylor (2007) — The shuffling of mathematics problems improves learning (interleaving effect)
- Brier, G. (1950). Verification of forecasts expressed in terms of probability (calibration scoring)

