# Design Case-Study Curriculum (from his own systems)

> Research track. Faithful rendering of the agent's structured findings.

**Dimension:** Design case-study curriculum — teaching transferable design concepts through the engineer's own systems, tested by defend-and-extend (not recall)

## Summary

This curriculum converts the learner's own portfolio into a sequence of DESIGN case-study modules. Each module names a transferable design concept, grounds it in a system HE actually built, and tests mastery through defend-and-extend questions: re-derive the decision from first principles, name the rejected alternative, quantify the tradeoff, and push the design into a regime where it breaks. This matches his stated learning mode (build + adversarial verification), his values order (Correctness > Reliability > UX > Maintainability > Performance), and his demand for the WHY and the named rejected alternative over hand-holding. The 16 proposed modules cover every requested area (seam-first design, storage-engine abstraction/LSM-vs-heap, buffer pool & B+tree, Volcano executor & cost optimizer, 2PL & deadlock detection, ARIES recovery, consistent hashing, lock-free aggregation, control/data-plane split & SFU election, graceful degradation, structural guards, hybrid deterministic+probabilistic pipelines, package-by-feature, structured-error envelopes, A/B measurement, reward shaping & LLM-judge). Difficulty is calibrated to a strong systems engineer who already knows interview-level system design and wants distributed-internals depth; Go modules assume true early-beginner Go and lean on his existing concurrency-correctness discipline as transferable. The testable_skills are the load-bearing output: each is a design question that cannot be answered by recall, only by re-deriving or extending the decision.

## Key findings

### His recurring engineering 'tells' ARE the transferable curriculum — each tell recurs across 3+ unrelated systems, which is exactly what makes it teachable as a pattern rather than a project detail.

Seam-first design appears as WALterDB's StorageEngine, JobAggregator's Source interface, OpenTrace's profiler registry, and NoteLens's OpenAI-compatible client swap. Structural guards appear as JobAggregator's numeric set-containment check and OpenTrace's sandboxed AST DSL. Graceful-degradation-with-surfaced-reason appears in CRAG fallback, per-source stale-deletion guard, and OpenTrace privilege-drop collectors. Teaching the pattern once and testing it across the recurrences is the highest-leverage structure.

*Source:* Portfolio CLAUDE.md 'How he works — engineering techniques & patterns'

### The best test format for this learner is 'defend the choice, then name where it breaks and what you'd switch to' — pure recall is explicitly disliked and pure system-design is already known.

He wants the WHY and the named rejected alternative; he runs adversarial self-audits; he writes design docs that reject alternatives in writing. So every testable_skill is phrased to (a) force re-derivation of a tradeoff he already made, then (b) push into a regime (scale, workload skew, failure) where the original decision inverts. This tests understanding-all-the-way-down, his stated ethos.

*Source:* Learner context + 'Behaviour & personality' (rejects designs in writing; adversarial QA)

### Several flagship claims rest on uncommitted or grader-coupled measurement — these are the richest A/B and eval-validity teaching moments, not weaknesses to avoid.

GOOGLY's ~17ms p95 / 1.85K req/s come from an uncommitted suite (0 automated tests); TraceLens's grader is both reward signal and eval ground-truth, and the 0.5B-beats-GPT-4o-mini claim risks overfitting to the grader's blind spots; WALterDB's 2.7x write throughput needs decomposition to be causal. Modules 15 and 16 turn these into design exercises on reproducible harness design and reward-hacking / judge-validity.

*Source:* Portfolio 'Growth edges' (benchmarks from uncommitted non-reproducible suites) + TraceLens description

### conclave is the one module set that must teach forward (design-ahead) not backward, because its hard core is documented-but-unbuilt and it is his first real Go.

The elected/migrating SFU is doc-comment stubs (phases 0-2 of 7). So its module tests distributed-systems design he is ABOUT to build (leader election vs capacity scheduling, make-before-break SRTP migration, split-brain avoidance, arbiter SPOF), plus Go-specific goroutine-lifecycle correctness under context cancellation — leveraging his existing 2PL/lock-free correctness discipline as 'new syntax for a discipline he already owns'.

*Source:* Portfolio 'Active projects' + 'Current Go proficiency'

### The structural-guard and hybrid-pipeline patterns are his most distinctive intellectual signature and deserve formalization, not just illustration.

His instinct to make a bad outcome impossible BY CONSTRUCTION (set-containment anti-fabrication, sandboxed AST eval) rather than by prompting/testing is a soundness-vs-probabilistic-confidence distinction most engineers never formalize. Module 11 pushes him to state the guard as an invariant and prove it can't be bypassed (then find the bypass), which is exactly the adversarial-verification loop he already runs manually.

*Source:* Portfolio 'Structural guards that make a bad outcome impossible by construction'

## Recommendations

- Sequence the curriculum in three arcs matched to his fluency: (1) Storage-internals arc in C++/WALterDB (seam-first, LSM-vs-heap, buffer pool/B+tree, Volcano, 2PL, ARIES) where he is strongest and can go deepest; (2) Distributed/backend arc (consistent hashing, lock-free aggregation, package-by-feature, error envelopes) in Java/Python; (3) Frontier arc (control/data-plane SFU in Go, hybrid pipelines, structural guards, graceful degradation, A/B design, reward shaping) which stretches him into distributed internals and Go. Put the conclave module last in each pass since it's design-ahead and his weakest language.
- Run every module as a written defense, not a quiz: he already writes design docs that reject alternatives in writing, so the deliverable per module is a short DESIGN_NOTES-style memo answering the testable_skills with a named rejected alternative and a quantified tradeoff. Grade it adversarially — the goal is to find the regime where his original decision inverts.
- For the measurement modules (A/B, reward shaping, GOOGLY reproducibility), make the extension concrete and buildable: have him actually commit the reproducible harness he designs. This turns the 'uncommitted benchmark' growth edge into a shipped artifact and matches his learn-by-building mode.
- Force the structural-guard and hybrid-pipeline modules to end in a formal invariant + a bypass attempt. The highest-value skill is stating 'the property that must hold by construction', proving it, then breaking it — this is his adversarial-verification instinct applied to his own most distinctive pattern.
- Keep every prompt calibrated to numbers-over-adjectives: each testable_skill should demand a derived number (crossover point, load variance, false-positive budget, bottleneck math, stopping rule) rather than a qualitative answer, so 'defend' can't collapse into hand-waving.

## Proposed modules

### Interface-seam-first: designing the swappable-storage-engine contract before either side

**Objectives**

- Understand why defining a narrow interface contract first constrains both implementations honestly and is the precondition for a fair A/B
- Learn to place cross-cutting concerns (durability, stats) above vs below a seam without leaking implementation

**Testable skills**

- State the exact operation contract of WALterDB's StorageEngine seam. Which single operation, if leaked, would make the heap↔LSM A/B unfair (e.g. exposing page-level iteration LSM can't honor cheaply)?
- Does the WAL live above or below the StorageEngine seam? Defend the placement, then argue the opposite and say what durability story each forces on the LSM side.
- Add a third engine (columnar/PAX) — which current seam methods break, and how do you evolve the interface without a versioned breaking change to existing callers?
- Name a cost-based-optimizer decision that legitimately needs to see THROUGH the seam (e.g. per-engine cost estimation), and expose it without coupling the planner to either engine.

### Storage-engine abstraction in practice: deriving the LSM-vs-heap crossover and proving it

**Objectives**

- Derive from workload the regime where LSM beats heap, and predict read/write amplification each pays
- Design an A/B that cannot lie to you — isolate the cause of a throughput delta

**Testable skills**

- Derive the read/write/point/range mix where WALterDB's LSM beats the heap engine; predict the write-amp and read-amp each pays and locate the crossover.
- Decompose the measured ~2.7x write throughput: how much is sequential append vs deferred index maintenance vs skipped in-place page writes? Design the microbenchmark that isolates each factor.
- Size-tiered vs leveled compaction: which did you choose, what's the space-vs-write-amp tradeoff, and at what read-latency SLO would you switch?
- Size the bloom-filter false-positive budget for a 1% point-lookup-miss target across N SSTables — and identify where blooms stop helping (range scans).
- List everything that must be held fixed (buffer-pool size, fsync policy, dataset skew, warmup) for the heap↔LSM comparison to be causal rather than coincidental.

### Buffer pool (LRU-K) and page-backed B+tree: replacement policy and latch discipline

**Objectives**

- Reason about replacement-policy behavior under scan vs OLTP access patterns
- Design latch-crabbing that stays disjoint from lock order to avoid deadlock across the concurrency layers

**Testable skills**

- Why LRU-K (K=2) over plain LRU or CLOCK? Construct the access pattern where correlated-reference protection saves you, and the one where it is pure overhead.
- Design the latch-crabbing protocol for concurrent B+tree insert+split. Where exactly could it deadlock against 2PL row locks, and how do you keep latch order provably disjoint from lock order?
- Trace a leaf split that triggers eviction of the parent page mid-split. Which invariant protects you (pin counts), and what corruption appears if pin accounting is off by one?
- Derive the node fanout from page size and key size, and show how fill-factor choice trades tree height (read cost) against split frequency (write cost).

### Volcano executor and cost-based optimizer: the iterator model and why cardinality estimation is the real hard part

**Objectives**

- Weigh the pull-based iterator model against vectorized/push-based execution
- Recognize cardinality estimation as the dominant source of plan error and design for plan robustness over point-optimality

**Testable skills**

- Volcano/iterator vs vectorized execution: what does WALterDB pay per tuple in virtual-call overhead, at what row count does vectorization win, and what must change in the operator interface to get it?
- Show a 3-join query where an independence-assumption error in cardinality estimation compounds multiplicatively. How do you bound the damage instead of chasing a perfect estimate?
- Design the minimal statistics set (histograms? count-distinct sketches?) that would materially improve join-order choice, and justify the storage and refresh cost against the query classes it helps.
- Name the query class where a rule-based heuristic is provably good enough that the cost model is wasted complexity.

### Concurrency control: strict 2PL with wait-for-graph detection vs the alternatives

**Objectives**

- Justify detection over prevention over avoidance for a chosen workload
- Design victim selection and detection cadence as explicit tradeoffs, then compare against MVCC

**Testable skills**

- Why strict 2PL + wait-for-graph detection over timeout-based avoidance or wound-wait/wait-die prevention? Name the workload where each rival wins and the signal that would make you switch.
- Design victim selection: youngest-transaction vs least-work-done vs most-locks-held. Which minimizes wasted work, and how does the choice interact with starvation guarantees?
- At what cycle-check frequency does wait-for-graph detection cost more than the deadlocks it catches? Derive the tradeoff and propose an adaptive trigger.
- Strict 2PL holds write locks to commit — quantify the throughput cost under a hot-key workload, then redesign toward MVCC: what do you gain, and which anomaly (write-skew) reappears that 2PL didn't have?

### ARIES-lite crash recovery: WAL invariants and idempotent replay

**Objectives**

- State the WAL invariants as preconditions and show the exact bug each relaxation introduces
- Reconcile ARIES-style recovery with the LSM engine's structural durability behind the same seam

**Testable skills**

- State the two WAL invariants (write-ahead logging, force-log-at-commit) as preconditions, then exhibit the durability bug that appears if you relax each.
- Walk Redo's repeat-history phase: why redo even loser transactions' actions before undoing them? Construct the corrupted state you'd reach if you skipped that.
- Design the pageLSN idempotency check so Redo is safe under repeated crashes-during-recovery. Where does an off-by-one in pageLSN comparison silently double-apply an update?
- Name what ARIES-lite drops from full ARIES (CLRs? nested top actions?) and the recovery scenario your simplification cannot handle — plus the cost to add it back.
- Does ARIES even apply to the LSM engine, or does LSM recovery fall out of WAL + SSTable structure for free? Reconcile the two durability stories that live behind one StorageEngine seam.

### Consistent hashing without a coordinator: the app-layer ring in GOOGLY

**Objectives**

- Justify an app-layer ring over Redis Cluster and name exactly what you gave up
- Extend the ring to weighted/heterogeneous nodes and bound load variance

**Testable skills**

- Why an app-layer consistent-hash ring over 3 Redis instead of Redis Cluster? Name what you surrendered (online resharding, MOVED/ASK redirection, gossip) and the condition that flips the call.
- Redesign the ring for weighted/heterogeneous nodes (a 2x-RAM Redis). How do vnode counts encode weight, and prove load variance stays bounded as capacity is added.
- With 150 vnodes over 3 nodes, derive the load-imbalance standard deviation and show how it shrinks with vnode count. What's the memory and lookup cost of pushing to 1500 vnodes?
- A node dies: trace which keys move and where, show only ~1/N of the keyspace remaps, then add replication — where do reads fall back and what consistency do you promise?
- SHA-256 for placement is expensive — when does hash cost surface in p99, and what's the cheapest hash that still gives you uniform placement?

### Lock-free batch-write aggregation: proving exactly-once across an atomic buffer swap

**Objectives**

- Prove the exactly-once flush property across the swap boundary
- Choose the counter primitive and flush cadence from the contention and latency regime

**Testable skills**

- Walk the ConcurrentHashMap + LongAdder + atomic buffer-swap flush and prove exactly-once: what guarantees a count is neither lost nor double-counted across the swap?
- Exhibit the race where a writer holds a reference to the old buffer mid-increment during the swap. Prove your design either prevents it or reclaims the straggler increment.
- LongAdder vs AtomicLong vs a hand-striped counter here: derive the contention regime where each wins, tied to core count and key skew.
- Redesign flush cadence — time-based vs size-based vs backpressure-driven. Which best bounds BOTH p99 write latency and the single JDBC UPSERT batch size, and what's the failure mode if the DB stalls mid-flush?

### Control/data-plane split and the elected, migrating SFU (conclave, design-ahead)

**Objectives**

- Locate where the plane split breaks at scale and prove the bottleneck with math
- Design SFU election and mid-call migration as real distributed-systems problems, including Go goroutine-lifecycle correctness

**Testable skills**

- The central Go server is control-plane election arbiter only; media is peer data-plane. Where does this break at 50 peers — arbiter, elected SFU uplink, or fan-out CPU? Show the bottleneck math.
- Is SFU election leader election (Raft-lite) or capacity-aware scheduling? Name the rejected simpler design (static / lowest-ID) and why it fails under heterogeneous uplinks.
- Enumerate the state that must transfer on SFU migration mid-call (SRTP keys, RTP sequence/timestamp continuity, subscription graph) and design a make-before-break cutover that doesn't drop a keyframe. Where's the unavoidable glitch?
- Prove the call survives arbiter death (data plane keeps flowing), define exactly what degrades, and design a re-election trigger that can't split-brain into two live SFUs.
- Go-specific: design the migrating-SFU goroutine lifecycle under context cancellation. Where does a leaked goroutine or send-on-closed-channel hide, and does go test -race actually catch it here?

### Graceful degradation with a surfaced reason: never hard-fail on an unreliable call

**Objectives**

- State the shared degradation contract across NoteLens, JobAggregator, and OpenTrace as one invariant
- Distinguish degrade-open from degrade-closed per operation and prove the fallback terminates

**Testable skills**

- State the degradation invariant shared by CRAG's keyword-overlap fallback, JobAggregator's per-source stale-deletion guard, and OpenTrace's privilege-drop collectors — and why the reason must be surfaced, not swallowed.
- In CRAG, the relevance grader can itself fail. Design the fallback-of-the-fallback so the loop terminates and never returns silently-empty context; prove termination and bound worst-case retrieval cost.
- JobAggregator's stale-deletion is fail-CLOSED (guarded on per-source success) but collection is fail-OPEN. Justify the asymmetry and name where flipping either becomes a correctness bug.
- Design the surfaced-reason envelope so degradation is measurable: what SLO tells you the safety-net has quietly become silent quality loss?

### Structural guards: making a bad outcome impossible by construction, not by prompting

**Objectives**

- Formalize a 'the model must never X' requirement as a post-hoc invariant and prove (or break) it
- Situate structural guards against LLM-judge and unit tests as distinct enforcement strata (sound vs probabilistic)

**Testable skills**

- Formalize JobAggregator's anti-fabrication guard: every number in an output bullet must be in the source's number set. Prove it can't be bypassed — then find the bypass (unit conversion, rounding, derived numbers) and patch the invariant.
- Contrast structural guard vs LLM-judge vs unit test for this property: which is sound, which is merely probabilistic, and why keep all three?
- OpenTrace's sandboxed AST rule DSL is a structural guard against arbitrary code execution. Enumerate the node allowlist and argue no allowed subset reaches I/O or unbounded compute — then name the node you'd most likely forget.
- Give the general recipe for turning any 'never X' requirement into a post-hoc structural check, and state precisely when no such check exists (X isn't decidable from the output alone).

### Hybrid deterministic + probabilistic pipelines: model does semantics, code owns the exact part

**Objectives**

- State the division-of-labor rule that keeps the deterministic half owning the safety-critical property
- Design the confidence handoff and an eval that attributes failure to the correct half

**Testable skills**

- State the division-of-labor rule across Set-of-Marks (model picks, code locates), CRAG (model retrieves, code grades overlap), and JobAggregator (LLM drafts, code checks numbers). What property must the deterministic half ALWAYS own?
- Design the confidence handoff: when the probabilistic stage is uncertain, does the deterministic stage reject, fall back, or re-ask? Bound the loop and its cost.
- When does a post-hoc deterministic check beat constraining the model's inputs up front (grounding / constrained decoding), and vice versa? Pick per system and justify.
- Design an eval that separates 'model got the semantics wrong' from 'deterministic geometry/check was wrong', so you know which half to fix.

### Package-by-feature as an architectural boundary

**Objectives**

- Defend feature-slicing in terms of change locality and blast radius, and place the concerns that cut across it
- Map feature packages to deploy/transaction boundaries and to Go's import-cycle constraints

**Testable skills**

- Defend package-by-feature (SideQuests auctions/franchises/disputes each owning dto/) over package-by-layer via change locality and blast radius, then name the cross-cutting concern (auth, transactions) that breaks the clean split and how you place it.
- In Go (conclave internal/signaling, internal/overlay), show a feature-to-feature dependency that would force an import cycle, and the seam (interface in a third package) that resolves it.
- When does package-by-feature become premature modularity? Give the team-size / churn threshold where package-by-layer is honestly better.
- Which SideQuests/conclave feature packages are microservice-extraction candidates and which must stay co-transactional — and how does the package boundary predict that?

### Structured error hierarchy to centralized handler to {code,message,details} envelope

**Objectives**

- Design the error taxonomy and its single translation point without leaking internals
- Reproduce the pattern idiomatically in Go and enforce a redaction boundary structurally

**Testable skills**

- Define the taxonomy split (client/server, transient/permanent) behind your envelope and show how the centralized handler maps each to an HTTP status plus retryability without leaking internals.
- Translate the pattern to idiomatic Go for conclave: error wrapping with %w + errors.Is/As at one middleware, sentinel vs typed errors, and the single place errors map to a signaling-protocol code.
- The `details` field can leak stack/SQL/PII. Design the redaction boundary — safe-for-client vs logs vs traces — and enforce it structurally rather than by convention.
- Show where a wrong retryable/non-retryable classification causes a correctness bug (double-apply) versus merely an availability bug, and how the envelope must encode the difference.

### A/B baseline-vs-treatment measurement designed in from the start

**Objectives**

- Identify the single control each A/B must hold fixed to be causal, and the likeliest confounder
- Make a performance claim reproducible and defensible, with an honest stopping rule

**Testable skills**

- Across LSM-vs-heap, GRPO'd-0.5B-vs-GPT-4o-mini, and single-vs-multi-agent grading — state the one thing each A/B must hold fixed to be causal and the confounder you're most likely to miss.
- GOOGLY's numbers came from an uncommitted suite. Redesign it reproducible-and-committed: the minimum harness (fixed dataset, warmup, percentile reporting) that makes a p95 claim defensible.
- Design the stopping rule: how many rollouts/requests before a delta is real not noise? Tie it to measured variance, not a round number.
- Name the decision in your portfolio where you CAN'T run a fair A/B (irreversible, or the treatment changes the workload) and what you substitute for one.

### Reward shaping and LLM-as-judge validity: TraceLens as a specification-gaming surface

**Objectives**

- Anticipate reward hacking under a shaped reward and design structural fixes
- Separate grader-as-reward from grader-as-eval and defend the headline claim against overfitting

**Testable skills**

- The shaped reward (signal-discovery bonuses, step + early-submit penalties) is a gaming surface. Name three ways a 0.5B policy could farm reward without actually diagnosing, and the structural fix for each.
- The grader is both the reward signal and the eval ground-truth. Separate them or defend the coupling — and prove the 0.5B-beats-GPT-4o-mini claim isn't overfit to the grader's blind spots.
- Under partial observability with step penalties, does the reward incentivize giving up early on hard incidents? Show the incentive and reshape it.
- GRPO vs PPO for this 0.5B setup: why GRPO, what does dropping the value network cost under sparse/shaped reward, and at what model scale would you switch back?
- Redesign the grader from graded buckets toward a rubric robust to reward hacking. What does an LLM-judge add over the deterministic grader, and what new bias (verbosity, self-preference) does it inject?

## Risks & gotchas

- Some modules test systems whose hard core is unbuilt (conclave's elected/migrating SFU) or whose numbers are unreproducible (GOOGLY) — frame these as design-ahead / harness-building exercises, not as 'defend what you measured', or the questions will feel unfair.
- Team-and-capstone attribution (WALterDB, SideQuests, TraceLens) means some design decisions may have been made by collaborators; phrase questions as 'defend this design' (a valid learning exercise regardless of authorship) rather than 'defend YOUR decision', to avoid false-premise questions.
- The Go modules risk conflating design difficulty with language difficulty — keep the distributed-systems design question separate from the 'idiomatic Go' question so a Go-syntax gap doesn't mask (or be mistaken for) a design gap.
- Reward-shaping and LLM-judge validity (TraceLens) sit partly outside pure systems and lean on RL/ML judgment where he is strong but not expert; calibrate expectations to design reasoning (incentive analysis, eval separation) rather than SOTA RL-algorithm internals.
- There is a real risk of over-testing breadth (16 modules) at the cost of depth; better to run 4-5 modules to full written-defense depth than to survey all 16 shallowly — the defend-and-extend format only pays off with depth.

## Open questions

- Should the curriculum be self-driven (he writes the memos and self-audits, matching his adversarial-QA habit) or dialogic (a partner plays adversary and pushes each answer to failure)? The second is higher-signal but higher-cost.
- What's the right cadence — one module per week tied to active work on that repo, or a concentrated storage-internals block? Tying modules to repos he's actively touching would maximize build-to-learn transfer.
- Should completed module memos feed back into the repos as living design docs (DESIGN_NOTES / ARCHITECTURE), turning the curriculum into shipped documentation and closing his 'benchmark reproducibility' and 'design-ahead' growth edges simultaneously?
- How much should the C++/Java/Python modules push toward NEW builds (e.g. actually implementing MVCC in WALterDB, the weighted ring in GOOGLY) versus staying at design-memo level? His learn-by-building mode argues for building, but that's a much larger time budget.

