# 01 — Pedagogy: the teach→test loop

This doc converts the learning-science evidence into Crucible's one load-bearing mechanism: **teach a primitive, then force effortful reconstruction, then grade at Bloom Analyze/Evaluate/Create.** Everything downstream — the question taxonomy ([05-content-model.md](05-content-model.md)), the scheduler and θ store ([06-progress-model.md](06-progress-model.md)), the hybrid grader ([04-grading.md](04-grading.md)) — implements the decisions made here. The audience is one advanced engineer whose real gap is Go; calibrate to that.

## The core loop

The single most-replicated result in the literature is the **testing effect**: retrieval practice beats restudy for durable retention (Roediger & Karpicke 2006 — ~50% vs ~35% recall at one week; the restudy group *out-scored* the tested group at 5 minutes and lost badly by day 7). That 5-minute inversion is the illusion-of-competence trap, and it is the whole reason a re-reading workbook feels productive and teaches nothing.

So the delivery loop is asymmetric by item state:

- **New item → generate-before-reveal.** Make him attempt the design, predict the output, or build the primitive from a blank editor *before* the exposition unlocks. The generation attempt is the desirable difficulty (Bjork & Bjork 2011); the exposition is the feedback on it, not the lesson.
- **Review item → test-first, reveal-on-miss.** Pose the retrieval cold. Only surface the reference on a wrong or hand-waved answer.

For code, the retrieval artifact is **running code that passes `go test`**, not a recognition MCQ. *Rejected alternative: recognition/MCQ recall as the default probe* — rejected because recognition is answerable by pattern-matching and does not discriminate the reconstruction ability we actually want. MCQ survives only where it encodes a genuine *discrimination* (see interleaving) or a Track-B atom.

## Two tracks, and why the deck is thin

Design judgment and rote atoms have opposite optimal treatments, so they get separate tracks:

- **Track A — design/systems judgment.** build → critique → explain-back, at Analyze/Evaluate/Create, gated by mastery. **Not** in a spaced deck.
- **Track B — the memorizable residue only.** Go syntax, stdlib signatures, named gotchas. This is the *only* rote surface, and it is deliberately small.

The firewall between them is not fussiness. A spaced deck is a known **rote-recall attractor**: verbatim reproduction is orthogonal to transfer and can crowd it out (Barnett & Ceci 2002). If design content leaks into the scheduler, it trains the wrong layer. Operating rule: **if a search engine can answer the item, it is a Track-B atom or it is cut** — it never enters the design track.

## Spacing (FSRS as a thin adjunct — calibrated, not oversold)

Track B rides on **FSRS with shipped default parameters**, target retention **0.85–0.90**. The primitive worth explaining: FSRS models each atom by **Difficulty, Stability, Retrievability** over a power-law forgetting curve and schedules the next review to land at your chosen retention, whereas **SM-2** (the rejected alternative — Anki's legacy ease-factor scheme) uses a cruder exponential model and drifts into "ease hell." We pick FSRS because its defaults already dominate SM-2 *cold*, so there is zero downside to adopting it un-optimized.

The honesty clause: FSRS's headline **"20–30% fewer reviews for equal retention" is a heavy-mature-deck average and will not materialize here.** On a single-user, sub-1,000-card deck the real saving is ~**20 s/day — noise.** FSRS needs roughly **1,000 reviews** (400 on Anki ≥24.04) before per-user optimization can fit *his* curve; below that it runs the shipped priors regardless. So: **do not optimize per-user until ~1,000 reviews exist**, and do not present the 30% figure as a benefit. FSRS is the correct long-term substrate; at this scale it is a wall-clock tie with SM-2, and we say so.

Target-retention choice is a Reliability/UX trade, not a Correctness one: **0.95 roughly doubles daily review load and 0.97 roughly quadruples it** for negligible durability gain on a learning deck. 0.85–0.90 is the band.

Cadence for atoms: first retrieval **same session (~10 min post-teach)**, second **within 24h**, then hand to FSRS to expand (~3d → 7d → 16d → 35d). For Track-A design modules that are *not* in the deck, set explicit **closed-book "re-derive from scratch" checkpoints at ~7d and ~30d** after the module's mastery date. (Uniform spacing is nearly as good as a tuned expanding schedule — Cepeda et al. 2006 — so this does not need over-engineering.)

## Mastery gating as a behavior bar

A module is gated on a **behavior, not a percentage** (Bloom 1968 mastery learning; Keller PSI). The bar, which also *is* the assessment format Crucible teaches:

> **He builds the primitive from scratch and it passes the automated gate (`go test -race` / `vet` / `staticcheck` / gofmt-diff), AND names the rejected alternative in writing, AND states ≥1 concrete failure mode with a number.**

Miss any leg and the module is not done; module N+1 stays hard-gated behind it. *Rejected alternative: an ~85% score threshold* — rejected because a numeric threshold is gameable by partial credit and does not force the rejected-alternative-plus-failure-mode reasoning that is the actual competency.

Gating a strong engineer through material he already owns is busywork and the fastest route to disengagement, so every skill carries a **test-out path**: one Evaluate-level challenge that, if passed, latches the unlock without the teach step. This matters most for his deep Python/systems areas.

The gate is a **discrete unlock latch**. The *continuous* ability estimate (**θ**) and forgetting *timing* (half-life) live in [06-progress-model.md](06-progress-model.md); note here only the boundary this pedagogy draws: **a decayed θ schedules a review but must never re-lock an already-passed module.** Forgetting triggers retrieval, not regression.

## Bloom: ban "what is X"

Systems competence lives in **Analyze < Evaluate < Create**; a deck of Remember/Understand cards trains the wrong layer (Anderson & Krathwohl 2001). Every objective and every item is written with a top-tier verb and **tagged with its Bloom level so the mix is auditable** by the content pipeline:

- **Analyze** — "trace *why* this SFU full-mesh saturates at ~6 Mbit/s by 5 peers."
- **Evaluate** — "critique `sync.Mutex` vs a channel here; when does each break?"
- **Create** — "design a leak-free goroutine lifecycle for a migrating SFU under `context` cancellation, and prove it with `go test -race`."

"What is a goroutine?"-shaped items are banned from Track A by construction.

## Interleaving — the discrimination case

Blocking one problem type inflates in-session performance and *hurts* final-test transfer; **interleaving** the types lowers practice accuracy but improves both retention and — the payoff — the ability to **select** the right approach (Rohrer & Taylor 2007; Kornell & Bjork 2008). The flagship application is the **Go concurrency discrimination set**: shuffle `sync.Mutex` / channel / `atomic` / `errgroup` problems so he must first **diagnose which primitive fits an unlabeled contention scenario**, mirroring his own explicit mutex-vs-channel-vs-atomic trade-off habit. The same principle is varied across surfaces — 2PL in a DB, a lock in a Go server, a lifecycle in the SFU — to force abstraction of the invariant rather than memorization of one instance.

## Desirable difficulties, and the honest dip (a named abandonment risk)

Interleaving and generate-before-reveal **lower visible in-session accuracy by design.** This is the load-bearing honesty point: **that dip is the signal that the method is working, not evidence it is failing.** Without framing, a first-try pass rate that drops when interleaving turns on reads as "the workbook is broken," and the rational response is to switch it off — which optimizes away the exact mechanism producing the learning. Crucible must therefore **surface the dip explicitly and label it** (the instrumentation panel notes when a lower first-try rate is expected). Treat "he disables the difficulty because the numbers look worse" as a first-class abandonment risk, not an edge case.

## Deliberate practice — the 15–30% failure band

Expertise grows at the **edge of ability** with immediate specific feedback, not from time-on-task (Ericsson et al. 1993). Two consequences: each module isolates **one named weakness** (e.g. `%w` wrapping + `errors.Is/As`; `defer`/`panic`/`recover` nuance) with a **fast automated signal as the coach** (`go vet`, `staticcheck`, `-race`, gofmt-diff); and difficulty is tuned to the band where he **fails ~15–30% of attempts.** Below that band the reps are wasted; well above it the feedback loop stalls. Per-skill first-try pass/fail is logged over time so progression is evidence-based, not asserted.

## Feynman / explain-back — the strongest defense against illusion-of-competence

Self-explanation builds deeper, transferable models and exposes gaps that recognition *and even passing code* can hide (Chi et al. 1994). So **explain-it-back is a first-class assessment**: he writes the mechanism as if teaching a competent peer, and an **adversarial rubric fails the write-up unless it contains all three of — the named rejected alternative, a concrete failure mode, and a quantified claim (percentile / throughput / delta).** You cannot fake this by pattern-matching, which is why it is the primary guard against a rote answer passing as understanding. Per the grading design the LLM-judge here is **fail-open and reference-grounded** — it may lower or flag but never raise a deterministic verdict, and a network-down path degrades to self-grade-against-reference at LOW confidence rather than hard-failing ([04-grading.md](04-grading.md)).

## How pedagogy drives the rest of the system

- **Question taxonomy ([05-content-model.md](05-content-model.md)).** Every item type exists to serve a Bloom level and a track: generate-before-reveal builds, interleaved discrimination probes, explain-back essays, and the thin Track-B recall atoms. The Bloom tag and the "search-engine-answerable ⇒ cut or Track-B" rule are content-pipeline invariants, not editorial suggestions.
- **Scheduler and mastery ([06-progress-model.md](06-progress-model.md)).** The behavior-bar latch, the test-out unlock, the FSRS default-param deck for Track B, and the manual 7d/30d re-derive checkpoints for Track A are the scheduler's inputs. The pedagogy fixes *what* schedules; that doc fixes the θ/half-life arithmetic and guarantees decay never re-locks a pass.

## Limitations / open questions

- **The FSRS win is a wash at this scale.** We adopt it as the right substrate and explicitly *do not* claim the 20–30% figure; below ~1,000 reviews it is SM-2 with a better default curve.
- **Build vs consume the scheduler.** Consistent with his from-scratch ethos, implementing the DSR update rules himself makes FSRS a *learning target* rather than a dependency. Open — decide before [06](06-progress-model.md) freezes.
- **Track-B size is unmeasured.** If the genuinely-rote residue turns out tiny, a full FSRS deck is over-engineered and a Leitner/manual schedule would do. Revisit after the R2 content pilot yields real atom counts.
- **Explain-back grader boundary.** Deterministic-checklist vs LLM-judge vs his own self-audit checklist is unresolved; the rubric's three hard requirements hold regardless of who runs them.
- **What this does not prove.** Passing Crucible's gates demonstrates reconstruction under variation on *these* items; it is not evidence of production competence at scale, and the workbook should say so per module rather than imply mastery it has not tested.
