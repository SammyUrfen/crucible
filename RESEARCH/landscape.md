# Prior-Art Survey — interactive learn + test education

> Research track. Faithful rendering of the agent's structured findings.

**Dimension:** Prior-art survey of interactive "learn + test" technical education — mechanism, effectiveness, grading approach, and one steal/reject per platform — for an advanced-engineer, self-graded, from-scratch workbook (Python deep + Go beginner + design + distributed internals)

## Summary

Across 13 platforms the grading mechanism is the real design axis, and it forms a rigor ladder: self-graded recall (Anki/FSRS) → visible unit tests (Tour of Go, boot.dev) → hidden test batteries with partial credit (LeetCode, nbgrader/Otter) → black-box protocol conformance against a real client (CodeCrafters) → adversarial fault-injection property checking (Gossip Glomers / Maelstrom / Jepsen). For THIS learner the two rungs worth building the workbook around are CodeCrafters-style stage-gated build-your-own-primitive and Gossip-Glomers-style adversarial property checkers, because both make correctness objective while rewarding from-scratch construction and quantitative reporting — his exact ethos. Text-first-no-video (educative, Real Python, Go by Example) and dependency-map curricula (roadmap.sh) are worth borrowing as delivery/skeleton, but their grading is weak-to-absent and their system-design depth is interview-shallow (a thing he has explicitly outgrown). Gamification (boot.dev) and human mentoring (exercism) are the two mechanisms to largely reject: the first is rote-recall-adjacent motivation scaffolding a self-driven advanced learner does not need, the second does not scale to a solo workbook (though it converts cleanly into a self-run adversarial "now make it idiomatic" second pass). Spaced repetition survives only as a narrow adjunct for the genuinely-rote (Go idioms/APIs he keeps re-looking-up), never as the core. The workbook's differentiators: per-language altitude asymmetry (Go = scaffolded on-ramp then ramp; Python = deep/adversarial from the start), grading that reports numbers (p50/p99, msgs/op, throughput delta) not just pass/fail, a "design defense" rubric forcing the WHY + named rejected alternative, and correctness-weighted rubrics matching his stated Correctness > Reliability > UX > Maintainability > Performance order.

## Key findings

### Exercism = automated test-runner + free human mentoring, split into concept tracks

Mechanism: download an exercise, solve locally, submit; the exercise's canonical test suite gives pass/fail, then a volunteer mentor reviews idiom/style in a second pass. Effective because it separates correctness (tests) from idiom-quality (human) — two feedback layers. Grading: run the canonical suite (some edge cases hidden) plus qualitative mentor review. STEAL: the two-layer 'green tests, THEN make it idiomatic' loop — for a solo learner the mentor becomes a self-run adversarial idiom/design review pass against a checklist. REJECT: human mentoring does not scale solo, and the test suites skew gentle/toy — too soft a correctness gate for him.

*Source:* exercism.org

### CodeCrafters = stage-gated build-your-own-X with black-box protocol conformance on git push

Mechanism: build your own Redis/Git/SQLite/HTTP/DNS/grep/Kafka/interpreter in ordered stages; you write code in a per-user repo and git push to run a remote harness that black-box tests your real binary (e.g. your Redis must speak RESP to a real client). Pass stage N to unlock N+1; hints tailored to your language. Effective: real-protocol ground truth + incremental momentum + language-agnostic. Grading: TDD-style per-stage tests triggered by push; conformance against the actual protocol, not a mock. STEAL (highest value): stage-gated from-scratch primitive verified by black-box conformance against a real client — near-perfect fit for his from-scratch ethos. REJECT: it prescribes the exact next micro-step (low ambiguity) — an advanced learner should sometimes design the stage boundaries himself; and it is paywalled/closed.

*Source:* codecrafters.io, docs.codecrafters.io/challenges/how-challenges-work

### Gossip Glomers / Maelstrom / Jepsen = adversarial fault-injection property checker as the grader

Mechanism: Fly.io's challenge series on Maelstrom (built on Jepsen). You implement one node speaking JSON over stdin/stdout; Maelstrom routes messages, INJECTS partitions/delays/message-loss, and verifies the required invariant (unique-ids, broadcast convergence, g-counter, kafka-style log, linearizable KV with transactions), while reporting latency and messages-per-operation. Effective: the grader actively tries to break your invariant under a nemesis — teaches real availability/consistency/CALM/CRDT reasoning, not trivia. Grading: property-based consistency checker under fault injection + quantitative cost report. STEAL (highest value for him): a checker that injects faults, asserts an invariant, AND reports the quantitative cost (msgs/op, p50/p99) — matches his adversarial-verification + numbers-over-adjectives ethos exactly, and pushes his system-design past interview level into distributed internals. REJECT: essentially nothing; only caveat is Maelstrom's node protocol is fixed, so bespoke systems need his own harness in the same spirit.

*Source:* fly.io/dist-sys, fly.io/blog/gossip-glomers, github.com/jepsen-io/maelstrom

### boot.dev = gamified guided backend path (Go/Python/SQL/HTTP) with per-lesson unit tests and CLI projects

Mechanism: linear career path with in-browser lessons + CLI-submitted real projects (web crawler, Pokedex CLI in Go), wrapped in XP/streaks/levels/boss-battles. Effective: strong motivation scaffolding + a genuinely well-regarded Go beginner path with real buildable projects. Grading: unit tests per lesson; CLI projects checked by a runner. STEAL: the structured 'build a real Go CLI end-to-end' beginner projects specifically for his Go gap — the on-ramp shape is good. REJECT: the gamification layer (XP/streaks/boss battles) is motivation scaffolding + rote-recall-adjacent that a self-driven advanced learner does not need and he dislikes; keep the project shape, drop the game.

*Source:* boot.dev

### educative.io = text-first, no-video, runnable-inline courses; system-design content is interview-shallow

Mechanism: read-fast text with in-browser runnable code widgets and quizzes, no video; famous for 'Grokking the System Design Interview'. Effective: fast skim/read pace with runnable snippets in place — good for a fast reader who dislikes video. Grading: quizzes + runnable widgets; weak-to-absent autograding, and the system-design courses are essentially read-only. STEAL: the text-first / no-video / runnable-inline delivery format. REJECT: its system-design depth is interview-level (he is explicitly past that and wants distributed internals + cloud/DevOps), and its 'grading' is passive — do not model rigor on it.

*Source:* educative.io

### Anki + FSRS = self-graded spaced repetition; FSRS models memory as difficulty/stability/retrievability

Mechanism: flashcards scheduled by FSRS (Anki default since v23.10, Nov 2023), which models each card by Difficulty, Stability (days until recall drops to the retention target) and continuously-decaying Retrievability on a power-law curve, fine-tuned on your own review log. Effective: benchmarks on 500M+ reviews show ~20-30% fewer reviews than SM-2 for equal retention — proven long-term retention at minimal time. Grading: pure self-graded recall (Again/Hard/Good/Easy). STEAL: run a SMALL FSRS deck over only the genuinely-rote — Go idioms/APIs and error-wrapping patterns he keeps re-looking-up. REJECT: he dislikes rote recall and learns by building/verification; do NOT make the workbook a flashcard app — spaced repetition is a narrow adjunct, not the core.

*Source:* faqs.ankiweb.net/what-spaced-repetition-algorithm, github.com/open-spaced-repetition

### A Tour of Go + Go by Example = canonical, minimal, runnable-in-place concept-per-page references with near-zero grading

Mechanism: Tour is the official in-browser sandbox with editable/runnable snippets and a few real exercises (image, equivalent binary trees, concurrent web crawler); Go by Example is annotated runnable one-concept programs. Effective: minimal, canonical, runnable-in-place, one idea per page — the ideal Go on-ramp. Grading: Tour auto-checks a couple of exercises, mostly self-check; Go by Example none. STEAL: the 'annotated runnable example per concept' format for a Go-idioms reference, and the Tour concurrency exercises (crawler, binary trees) as from-scratch katas seeding his Go modules. REJECT: no real grading and too basic to BE the workbook — it is the on-ramp, not the assessment.

*Source:* go.dev/tour, gobyexample.com

### Real Python = high-quality long-form depth with recall-only quizzes

Mechanism: deep, correct, code-along tutorials + learning paths + some interactive quizzes. Effective: excellent explanation depth and correctness on real Python topics (asyncio, typing, packaging). Grading: quizzes are recall; no real autograding — consumption is passive. STEAL: the depth/quality of explanation and 'code along a real thing' articles as reference reading for the Python-deep modules. REJECT: quiz-based recall grading and passive consumption — not an assessment model for him.

*Source:* realpython.com

### LeetCode-style hidden-test graders = objective, instant, scalable verdicts with time/space limits — but opaque and rote content

Mechanism: submit a function; run against hidden tests + a few visible samples under time/memory limits; instant AC/WA/TLE verdict. Effective: objective, instant, scalable, and catches edge cases you did not think of. Grading: hidden test battery + explicit perf limits. STEAL: the hidden-edge-case battery + explicit time/space budget as the objective correctness gate (he already reports p50/p99, so a perf limit fits). REJECT: (a) the CONTENT — algorithm-puzzle rote pattern-recall he explicitly dislikes; (b) the OPACITY — hidden tests with no visible failing input hurt learning-by-understanding, so steal the mechanism but SHOW the minimal failing input.

*Source:* leetcode.com

### nbgrader / Otter-Grader = classroom autograding with a visible-test / hidden-test split and partial credit

Mechanism: instructor authors assert-based test cells (visible = formative, hidden = summative) with per-test point allocation; Otter grades notebooks or plain .py locally or hosted against a rubric. Effective: visible tests guide while hidden tests verify you generalized; the grader IS the spec; reproducible batch grading with partial credit. Grading: assert-based cells, visible/hidden split, points per test. STEAL: the visible-guide / hidden-verify split with partial credit — visible tests teach, hidden tests confirm generalization — implementable as plain pytest tiers he already lives in. REJECT: notebook-centricity (he is a CLI/pytest/mypy person, not notebooks) and classroom point-scoring overhead that is meaningless solo.

*Source:* nbgrader.readthedocs.io, otter-grader.readthedocs.io

### roadmap.sh = community dependency-graph curriculum maps with self-marked checkboxes and no real grading

Mechanism: visual prerequisite graphs (backend, DevOps, system design, Go, Python) with curated links per node and self-checked boxes; recently some AI-generated quizzes. Effective: exposes the DEPENDENCY STRUCTURE and breadth of a domain and doubles as a 'what do I not know' gap audit. Grading: none — self-marked checkboxes; link quality varies. STEAL: the dependency-graph as the workbook's SKELETON (explicit prereq edges between modules) plus a gap-audit checklist. REJECT: no grading, breadth-over-depth, variable link quality — a map is not a workbook, and checking boxes is not competence.

*Source:* roadmap.sh

## Recommendations

- Build the workbook's grading around the top two rungs of the observed rigor ladder: CodeCrafters-style stage-gated build-your-own-primitive (black-box conformance against a real client/protocol) and Gossip-Glomers-style adversarial property checkers (inject faults, assert an invariant). These are the only two prior-art mechanisms that are both objective AND reward from-scratch construction.
- Encode a per-language altitude asymmetry: Python modules start deep and adversarial (he is fluent — hidden-test batteries, fault injection, mypy-strict gates from day one); Go modules start as a Tour/boot.dev-level scaffolded on-ramp (annotated runnable examples, guided CLI builds) and only THEN ramp into from-scratch primitives. Grading the two languages identically would either bore him in Python or overwhelm him in Go.
- Make grading report NUMBERS, not just pass/fail: every build-your-own exercise should emit p50/p99 latency, messages-per-operation, throughput delta vs a baseline (his A/B instinct), plus a correctness verdict. This mirrors Maelstrom's quantitative cost report and his own benchmarking ethos.
- Add a 'design defense' rubric to each module: a short self-graded written artifact stating the WHY and the NAMED rejected alternative, scored against a checklist. This converts exercism's human-mentor 'now make it idiomatic' pass into a solo adversarial review and enforces his 'every trade-off written down' habit.
- Weight rubrics to his explicit value order — Correctness > Reliability > UX > Maintainability > Performance. A fast solution that fails a fault-injection invariant should score below a slower correct one; make the rubric arithmetic reflect that ordering rather than treating speed as the tiebreaker.
- When you borrow LeetCode's hidden-test mechanism, reject its opacity: on failure, surface the minimal failing input/counterexample. He learns by understanding the failure, not by guessing; hidden-but-revealed-on-fail beats hidden-and-silent.
- Use roadmap.sh-style dependency edges as the workbook skeleton and an FSRS micro-deck only for the genuinely-rote (Go idioms/APIs he re-looks-up) — keep spaced repetition a narrow adjunct, never the core, since he dislikes rote recall.
- Reject gamification wholesale (boot.dev XP/streaks/boss-battles) and human-mentoring dependency (exercism) as core mechanisms — the first is unnecessary motivation scaffolding for a self-driven learner, the second does not scale solo; keep only their project shapes and their idiom-review step respectively.

## Proposed modules

### Build-Your-Own Primitive (CodeCrafters pattern, self-hosted)

**Objectives**

- Reimplement a real primitive from scratch in ordered stages, gated by black-box conformance against a real client/protocol
- Author the stage boundaries himself for at least one primitive (the ambiguity CodeCrafters removes)
- Python-deep target (e.g. an async RESP/HTTP server or a mini LSM) and a Go on-ramp target (e.g. a concurrent line-oriented protocol server)

**Testable skills**

- Protocol conformance verified by a real off-the-shelf client, not a mock
- Stage-gated progression where stage N unlocks only on green
- Emit throughput/latency numbers per stage against a baseline

### Adversarial Distributed Checker (Gossip Glomers / Maelstrom pattern)

**Objectives**

- Implement nodes that hold an invariant (broadcast convergence, monotone counter, linearizable KV, replicated log) under a self-written nemesis that injects partitions/delays/loss
- Go deeper than interview system design: reason explicitly about CALM, CRDTs, availability-vs-consistency, and quorum trade-offs
- Report messages-per-op and p50/p99 as first-class grading output, not an afterthought

**Testable skills**

- Property-based invariant check under fault injection
- Quantitative cost report (msgs/op, latency percentiles)
- Written trade-off defense naming the rejected consistency/replication alternative

### Two-Tier Test Harness (nbgrader/Otter + LeetCode pattern, de-opaqued)

**Objectives**

- Structure every exercise as visible-guide tests (formative) + hidden-verify tests (summative) with partial credit, all in plain pytest / go test
- On failure, always surface the minimal failing input — steal the hidden-test rigor, reject the opacity
- Wire the rubric arithmetic to Correctness > Reliability > UX > Maintainability > Performance

**Testable skills**

- Visible/hidden test split with partial credit
- Counterexample surfaced on failure
- Correctness-weighted scoring

## Risks & gotchas

- Self-grading has no external anchor: without a mentor or hidden instructor tests, he can unconsciously write the grader to match his solution. Mitigate by writing the adversarial checker/property test BEFORE the implementation (test-first), and by borrowing canonical external suites (Maelstrom workloads, real protocol clients) where they exist so the spec is not self-authored.
- Building the grading infrastructure can eat the learning time — CodeCrafters and Fly.io spent real engineering on their harnesses. Budget for the harness as its own cost, and lean on existing tools (Maelstrom for distributed, real clients for protocol conformance, plain pytest/go test for the rest) rather than hand-rolling a platform.
- His from-scratch ethos can collide with the on-ramp need in Go: forcing from-scratch primitives too early in a true-beginner language risks him fighting syntax instead of learning the concept. The altitude asymmetry must be enforced or Go modules stall.
- Spaced repetition scope creep: FSRS is seductive and could quietly become the workbook's center of gravity, which he'd resent. Cap the deck to genuinely-rote items and measure whether he actually uses it.
- Interview-shallow contamination: educative and roadmap.sh content is easy to import and will silently pull system-design modules back to interview depth. Explicitly gate design modules on a distributed-internals / cloud / DevOps depth bar.

## Open questions

- Does he want the workbook to auto-generate quantitative reports (a small results dashboard, per his hand-rolled-theme habit) or keep grading CLI-only?
- For distributed modules, use Maelstrom directly (fixed node protocol, batteries-included checker) or a bespoke in-process nemesis harness (more from-scratch, more effort)? Trade-off: canonical external spec vs full control.
- How much of the Go track should be pure on-ramp before the first from-scratch primitive — one module, or a whole scaffolded phase mirroring conclave's phase-0-2 approach?
- Should the 'design defense' artifacts be private self-notes or living docs he could later surface (matching his layered-docs habit)?

## Citations

- [Gossip Glomers — Fly.io Distributed Systems Challenges](https://fly.io/dist-sys/)
- [Gossip Glomers announcement — The Fly Blog](https://fly.io/blog/gossip-glomers/)
- [Maelstrom (Jepsen) — workbench for distributed-systems challenges](https://github.com/jepsen-io/maelstrom)
- [CodeCrafters — build your own Redis, Git, SQLite from scratch](https://codecrafters.io/)
- [CodeCrafters docs — How challenges work](https://docs.codecrafters.io/challenges/how-challenges-work)
- [Exercism — code practice with test runner + mentoring](https://exercism.org/)
- [boot.dev — gamified backend developer path](https://www.boot.dev/)
- [educative.io — text-first interactive courses](https://www.educative.io/)
- [Anki FAQ — what spaced repetition algorithm (FSRS default since 23.10)](https://faqs.ankiweb.net/what-spaced-repetition-algorithm)
- [Open Spaced Repetition — FSRS algorithm & benchmark](https://github.com/open-spaced-repetition)
- [A Tour of Go](https://go.dev/tour/)
- [Go by Example](https://gobyexample.com/)
- [Real Python](https://realpython.com/)
- [nbgrader — Jupyter classroom autograding](https://nbgrader.readthedocs.io/)
- [Otter-Grader — notebook/py autograding](https://otter-grader.readthedocs.io/)
- [roadmap.sh — developer roadmaps](https://roadmap.sh/)

