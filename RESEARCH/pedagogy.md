# Learning-Science Foundations

> Research track. Faithful rendering of the agent's structured findings.

**Dimension:** Learning-science foundations for a personalized "teach then test" technical workbook (single advanced learner)

## Summary

For a single advanced systems engineer whose real gap is Go (true beginner) sitting next to deep Python/systems knowledge, the workbook should NOT be a flashcard deck of definitions. The strongest, most-replicated findings (testing effect, spacing, interleaving, desirable difficulties, deliberate practice, self-explanation) all point the same way: teach a primitive, then force effortful RETRIEVAL and RECONSTRUCTION under variation, gate progression on demonstrated mastery, and assess at Bloom's Analyze/Evaluate/Create levels using critique/extend/design prompts plus explain-it-back — never "what is X?". A spaced-repetition scheduler (FSRS with default parameters, target retention ~0.85-0.90) belongs ONLY on the small residue of genuinely memorizable atoms (Go syntax/stdlib idioms, API signatures), not on design judgment. Concrete, numeric guidance below. Key calibration: on a sub-1,000-card single-user deck FSRS's headline "20-30% fewer reviews" advantage over SM-2 is essentially noise (~20 s/day) until ~1,000 reviews accumulate; choose FSRS anyway because its default params already dominate SM-2 cold and it's the right long-term substrate, but don't oversell the win.

## Key findings

### Testing effect / active recall beats re-reading

Retrieval practice produces markedly better long-term retention than restudy (Roediger & Karpicke 2006: ~50% vs ~35% recall at 1 week; the restudy group looked better at 5 min and worse later — the classic illusion-of-competence trap he already distrusts). WORKBOOK IMPLICATION: every module ends in a closed-book RETRIEVAL task (reconstruct the design / write the function from a blank editor / re-derive the invariant), never a 'read the summary again'. For code, the retrieval artifact is running code that passes `go test`, not a recognition question.

*Source:* Roediger & Karpicke (2006), Test-Enhanced Learning

### Spaced repetition: SM-2 vs FSRS, and what actually fits a small single-user deck

SM-2 (SuperMemo, 1987; Anki's legacy default): ease-factor per card, interval = prev x EF, EF nudged by a 0-5 grade. Simple, works cold, but the forgetting model is crude and it suffers 'ease hell'. FSRS (open-spaced-repetition, current lineage v4.5->v6): DSR model — Difficulty, Stability, Retrievability — with ~19-21 trainable weights, power-law forgetting curve, schedules to hit a chosen target retention. FSRS needs ~1,000 reviews (400 on Anki >=24.04) before it can fit YOUR curve; below that it uses shipped default params and behaves ~like SM-2. MEASURED tradeoff: ~20-30% fewer reviews for equal retention at scale, but that average comes from heavy mature decks — on a sub-1,000-card solo deck the real saving is ~20 s/day (noise). WORKBOOK IMPLICATION: use FSRS with DEFAULT parameters (they already dominate SM-2 even un-optimized, so zero downside), set target retention 0.85-0.90 (0.95 roughly doubles daily reviews, 0.97 quadruples — not worth it for a learning deck), and do NOT attempt per-user optimization until ~1,000 reviews exist. Don't market the '30%' number to him; it won't materialize at this deck size.

*Source:* open-spaced-repetition FSRS docs/benchmark (500M+ reviews); Anki SM-2 spec

### Mastery / competency-based progression gates advancement, not a fixed calendar

Bloom's mastery learning + Keller's PSI: learners advance only after demonstrating a high bar (~80-90%) on the current unit; this compresses the variance in outcomes. WORKBOOK IMPLICATION: define each module's mastery bar as a BEHAVIOR, not a score — e.g. 'builds the primitive from scratch AND names the rejected alternative AND states one failure mode' — and hard-gate module N+1 behind it. Matches his 'never say done without verification' and correctness-first ranking. Let him TEST OUT of anything he already owns (much of Python/systems) via a single Evaluate-level challenge, so mastery-gating doesn't waste his known-strong areas.

*Source:* Bloom (1968) Learning for Mastery; Keller PSI

### Bloom's taxonomy, applied to DESIGN skills, not recall

Revised taxonomy (Anderson & Krathwohl 2001): Remember < Understand < Apply < Analyze < Evaluate < Create. Systems-design competence lives in the top three; a deck of Remember/Understand cards trains the wrong layer. WORKBOOK IMPLICATION: write every objective and assessment with a top-tier verb — ANALYZE ('trace why this SFU mesh saturates at 5 peers'), EVALUATE ('critique using sync.Mutex vs a channel here; when does each break'), CREATE ('design a leak-free goroutine lifecycle for a migrating SFU under context cancellation'). Ban 'What is a goroutine?'-shaped items. Tag each item with its Bloom level so the mix is auditable.

*Source:* Anderson & Krathwohl (2001), revised Bloom's taxonomy

### Interleaving beats blocking for discrimination and transfer

Mixing problem types within a session (vs massing one type) lowers during-practice performance but improves later test performance and — crucially — the ability to SELECT the right approach (Rohrer & Taylor 2007; math-category studies show large final-test gains). WORKBOOK IMPLICATION: interleave the decision-shaped problems, especially Go concurrency: shuffle mutex / channel / atomic / errgroup problems so he must first DIAGNOSE which primitive fits, mirroring his own 'explicit mutex-vs-channel-vs-atomic trade-off' habit. Interleave storage-engine, scheduling, and failure-mode problems rather than finishing one topic before the next.

*Source:* Rohrer & Taylor (2007); Kornell & Bjork (2008)

### Desirable difficulties: make acquisition harder to make retention/transfer stronger

Bjork: spacing, interleaving, testing, varying conditions, and GENERATION are 'desirable difficulties' — they slow visible progress but improve durable learning and transfer. WORKBOOK IMPLICATION: default to GENERATE-BEFORE-REVEAL — make him attempt/predict the design or the bug before the exposition unlocks; vary the surface (same locking principle posed in DB 2PL, then in a Go server, then in the SFU) so he abstracts the invariant. He already prefers this ('adversarial verification', build-from-scratch); lean in rather than smoothing the path.

*Source:* Bjork & Bjork (2011), Making Things Hard on Yourself

### Deliberate practice: edge-of-ability tasks with immediate, specific feedback

Ericsson: expertise grows from focused practice at the edge of current ability, with well-defined goals, immediate feedback, and repetition-with-refinement — not mere time-on-task. WORKBOOK IMPLICATION: each module targets ONE named weakness (e.g. 'error wrapping with %w + errors.Is/As', 'defer/panic/recover nuance') with an explicit success criterion and a FAST automated feedback signal — `go vet`, `staticcheck`, `go test -race`, gofmt-diff — as the coach. Keep tasks in the difficulty band where he fails ~15-30% of the time; too-easy is wasted reps.

*Source:* Ericsson, Krampe & Tesch-Romer (1993)

### Feynman / explain-it-back as an ASSESSMENT mode (self-explanation effect)

Chi et al.: learners who self-explain build deeper, more transferable models; explaining exposes gaps that recognition and even coding can hide. WORKBOOK IMPLICATION: add an 'explain-it-back' assessment where he writes the mechanism as if teaching a competent peer, then an ADVERSARIAL rubric (checklist or an LLM grader) checks for the three things he values — the named rejected alternative, the failure mode, and a number/percentile — and fails the explanation if any is hand-waved. This is the single best assessment for DEEP design understanding versus rote, because you can't fake it by pattern-matching.

*Source:* Chi et al. (1994), self-explanation; Feynman technique

### Retrieval-practice cadence: initial test soon, then expanding intervals

Spacing effect + expanding retrieval: a first successful retrieval shortly after learning, then reviews at growing gaps, maximizes durability (roughly test same-session -> ~1d -> ~3d -> ~7d -> ~16d -> ~35d; uniform spacing is nearly as good, so don't over-engineer). WORKBOOK IMPLICATION: schedule the FIRST retrieval within the same session (~10 min after teaching) and a second within 24h, then hand the atom to FSRS to expand automatically. For design-level items that aren't in the deck, schedule a manual 're-derive from scratch' checkpoint at ~7d and ~30d after the module's mastery date.

*Source:* Landauer & Bjork (1978) expanding retrieval; Cepeda et al. (2006) spacing meta-analysis

### Avoiding rote recall when the goal is deep design understanding

Rote recall optimizes verbatim reproduction, which is orthogonal to (and can crowd out) transfer. The fix is to raise the retrieval to higher-order form. WORKBOOK IMPLICATION: constrain card/prompt templates to Analyze/Evaluate/Create shapes — 'why NOT X here', 'when does this break / what's the failure mode', 'redesign under this new constraint', 'what invariant does this preserve and how would you violate it'. Reserve the deck for the small memorizable residue (Go syntax, stdlib signatures, gotchas) and route all judgment content to build+critique+explain tasks. Rule of thumb: if a card can be answered by a search engine, it doesn't belong in the design track.

*Source:* Barnett & Ceci (2002) transfer taxonomy; Bjork desirable difficulties

## Recommendations

- Two-track structure: TRACK A (design/systems judgment) uses build -> critique -> explain-it-back at Bloom Analyze/Evaluate/Create and is gated by mastery, NOT spaced flashcards. TRACK B (a thin FSRS deck) holds only the genuinely memorizable residue — Go syntax, stdlib idioms/signatures, named gotchas. Never put design judgment in the deck.
- Scheduler choice, stated with calibration: use FSRS with SHIPPED DEFAULT parameters and target retention 0.85-0.90. Rationale: FSRS defaults already beat SM-2 cold, so there's no downside; but on a single-user sub-1,000-card deck the famous '20-30% fewer reviews' is noise (~20 s/day) — do not claim it. Do not run per-user optimization until ~1,000 reviews (400 on Anki >=24.04) exist. If he'd rather build the scheduler from scratch (his ethos), implement the DSR update rules — the learning target IS the algorithm.
- Retrieval cadence: first retrieval same session (~10 min post-teach), second within 24h, then expanding (~3d, 7d, 16d, 35d) handled by FSRS for deck atoms. For non-deck design modules, set explicit 're-derive from scratch, closed-book' checkpoints at ~7d and ~30d after the mastery date.
- Every objective and every assessment item carries an explicit Bloom verb tag; enforce a mix that is majority Analyze/Evaluate/Create for the design track. Reject any item answerable by recall or by a web search — if a search engine answers it, it's a Track-B atom or it's cut.
- Mastery bar as behavior, not percentage: a module is 'done' only when he (1) builds the primitive from scratch and it passes the automated gate (go test -race / vet / staticcheck / gofmt), (2) names the rejected alternative in writing, and (3) states >=1 concrete failure mode with a number. Hard-gate the next module behind this. Provide a single Evaluate-level 'test-out' challenge so his already-strong Python/systems areas aren't re-taught.
- Interleave decision-shaped problems, especially Go concurrency (mutex vs channel vs atomic vs errgroup) and failure-mode analysis, so he practices SELECTING the tool, not just applying a pre-named one. Accept and even flag the lower during-practice accuracy as expected and desirable.
- Generate-before-reveal by default: each module makes him predict the design/output/bug (or attempt the from-scratch build) BEFORE the exposition unlocks. Vary the surface for the same principle across domains (2PL in a DB -> lock in a Go server -> lifecycle in the SFU) to force abstraction of the invariant.
- Adopt explain-it-back as a first-class assessment with an adversarial rubric that FAILS the explanation unless it contains the named rejected alternative, a failure mode, and a quantified claim (percentile/throughput/delta). This is the primary defense against illusion-of-competence and against rote answers passing as understanding.
- Deliberate-practice tuning: target the difficulty band where he fails ~15-30% of attempts; each module isolates ONE named weakness with a fast automated feedback loop as the coach. Track per-skill pass/fail over time (numbers over adjectives) so progression is evidence-based, matching his 'measured, not asserted' habit.
- Instrument the workbook itself: log per-item Bloom level, first-try pass rate, retrieval latency, and lapse counts, and surface an honest 'what this does NOT yet prove' panel per module — turning his own calibrated-claims discipline into the workbook's progress model.

## Proposed modules

### Go concurrency discrimination (interleaved, decision-first)

**Objectives**

- Given a contention scenario, SELECT among sync.Mutex / channel / atomic / errgroup and justify the choice (Analyze/Evaluate)
- Design a leak-free goroutine lifecycle under context cancellation and prove it with go test -race (Create)

**Testable skills**

- Diagnose which primitive fits an unlabeled contention problem
- Explain-it-back: why NOT a channel here, and the failure mode of the wrong choice
- Build a minimal reproducer that -race flags, then fix it

### Explain-it-back assessment harness (Feynman mode)

**Objectives**

- Reconstruct a mechanism as a peer-teaching write-up that passes an adversarial rubric (Evaluate)
- Surface and repair a gap the explanation exposes (Analyze)

**Testable skills**

- Write-up contains named rejected alternative + failure mode + a quantified claim, or it fails
- Re-derive the same mechanism closed-book at the 7d and 30d checkpoints

### Thin FSRS retention deck (Track B residue only)

**Objectives**

- Retain Go syntax/stdlib idioms and named gotchas at ~0.85-0.90 target retention (Remember/Understand — deliberately the ONLY rote surface)

**Testable skills**

- Produce the correct idiom/signature from a blank prompt within the review
- Deck excludes any item answerable by search or requiring design judgment

## Risks & gotchas

- FSRS's '20-30% fewer reviews' is a large-mature-deck average; on a single-user sub-1,000-card deck it's ~20 s/day and will not show until ~1,000 reviews accumulate — presenting it as a headline benefit would be an uncalibrated claim he'd catch.
- Spaced-repetition decks are a well-known rote-recall attractor; if design content leaks into the deck it will train verbatim reproduction and actively crowd out transfer. Keep the design track OUT of the scheduler entirely.
- Interleaving and generate-before-reveal LOWER visible in-session performance; without framing, that reads as the workbook 'not working'. Label the dip as the desirable-difficulty signal so he doesn't optimize it away.
- Explain-it-back graded by an LLM can be gamed or can hallucinate a pass; keep the rubric a hard checklist (named alternative / failure mode / number) and treat the LLM as a fail-open assistant, never the sole gate — matches his 'LLM must never hard-fail the pipeline' rule.
- Mastery-gating can waste his existing Python/systems strength; without a test-out path it becomes busywork and he'll disengage.
- Higher target retention feels safer but roughly doubles (0.95) or quadruples (0.97) daily review load for a learning deck — a reliability/UX cost with little correctness gain here.

## Open questions

- Does he want to BUILD the scheduler from scratch (implement the DSR update rules himself, consistent with his ethos) or just consume an existing FSRS implementation? That flips FSRS from a dependency into a learning target.
- What's the intended session cadence (daily vs a few times a week)? Expanding-retrieval intervals and the FSRS target-retention choice should be tuned to realistic sitting frequency.
- How much content is genuinely memorizable (Track B) vs judgment (Track A)? If Track B is tiny, a full FSRS deck may be overkill and a simple Leitner/manual schedule would do.
- Should the adversarial explain-it-back grader be a deterministic rubric, an LLM judge, or a self-audit checklist he runs on himself (his multi-agent self-audit pattern)?

## Citations

- [Roediger & Karpicke (2006), Test-Enhanced Learning](https://journals.sagepub.com/doi/10.1111/j.1467-9280.2006.01693.x)
- Bjork & Bjork (2011), Making Things Hard on Yourself, But in a Good Way (desirable difficulties)
- Rohrer & Taylor (2007), The shuffling of mathematics problems improves learning (interleaving)
- Anderson & Krathwohl (2001), A Taxonomy for Learning, Teaching, and Assessing (revised Bloom's)
- Ericsson, Krampe & Tesch-Romer (1993), The Role of Deliberate Practice
- Chi et al. (1994), Eliciting Self-Explanations Improves Understanding
- Cepeda et al. (2006), Distributed Practice: A Review and Quantitative Synthesis (spacing)
- [open-spaced-repetition FSRS — algorithm overview and benchmark](https://github.com/open-spaced-repetition/fsrs4anki)
- [FSRS vs SM-2 for small decks / optimization threshold](https://github.com/open-spaced-repetition/fsrs4anki/blob/main/docs/tutorial.md)
- Bloom (1968), Learning for Mastery / Keller (1968) PSI

