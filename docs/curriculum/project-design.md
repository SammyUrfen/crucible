# Curriculum — Design Case-Studies (Defend-and-Extend, mined from his own repos)

This doc specifies the fourth Crucible track: a syllabus of transferable design
concepts, each grounded in a system the learner actually built, tested not by recall but
by **defend-and-extend** — re-derive the decision from first principles, name the rejected
alternative, quantify the trade-off, then push the design into the regime where it inverts.

## Why this track is the unique one

The other three tracks (Go, Python/FastAPI internals, deep system design) can lean on
external graders where they exist — the [landscape doc](../07-landscape.md) records the
orchestrate-over-labs stance: MIT 6.824's autograder, Jepsen Maelstrom / Fly.io Gossip
Glomers, and CodeCrafters already grade code and distributed *conformance* better than any
grader we would hand-roll. This track has no such external oracle. **No tool on earth
grades "defend and extend the storage-engine seam *you* drew in WALterDB, name the rejected
alternative, and give me the crossover point in numbers."** That is the one place a
hand-rolled grader is justified, and it is the track that most directly matches the
learner's stated mode: he already writes `DESIGN_NOTES` memos that reject alternatives in
writing and runs adversarial self-audits against his own code. This track formalizes that
habit into a graded loop.

Because the answers are free-form design essays with no computable oracle, this track is
graded by the **reference-grounded LLM-judge** described in [../04-grading.md](../04-grading.md),
not by deterministic checks. The judge is a hosted Anthropic model (a metered network call,
not an offline component — see R1 in [PLAN.md](../../PLAN.md)); the two structural guards
from that doc apply here unchanged: the judge may only lower or flag a verdict, never raise
one, and it grades strictly against a shown reference answer. The reference for every item
in this track is the same three-part rubric: **the answer must name the rejected
alternative, state its failure mode, and produce a number** (a crossover point, a load
variance, a false-positive budget, a bottleneck bound). An essay that defends the choice
eloquently but names no rival and produces no number fails the rubric regardless of prose
quality. The prototype feature spec ([../02-features.md](../02-features.md)) lists the
design-defense item type this track exercises end-to-end.

## The pedagogy: why "his own tells" are the teachable unit

The load-bearing observation from the source research: his recurring engineering *tells*
each recur across **3+ unrelated systems**, which is exactly what promotes a tell from
"project detail" to "teachable pattern."

- **Seam-first design** appears as WALterDB's `StorageEngine`, JobAggregator's `Source`
  interface, OpenTrace's profiler registry, and NoteLens's OpenAI-compatible client swap.
- **Structural guards** appear as JobAggregator's numeric set-containment anti-fabrication
  check and OpenTrace's sandboxed AST rule DSL.
- **Graceful-degradation-with-a-surfaced-reason** appears in CRAG's keyword-overlap
  fallback, JobAggregator's per-source stale-deletion guard, and OpenTrace's privilege-drop
  collectors.

Teaching the pattern once and testing it across its recurrences is higher-leverage than
walking each project top-to-bottom. Every module below therefore names a *concept*, anchors
it to the primary system that demonstrates it, and — where the pattern recurs — tests the
transfer across systems.

**Chosen format: written defense, graded adversarially.** The rejected alternative is a
*quiz* (MCQ / short-answer recall). A quiz cannot distinguish "understands the trade-off
all the way down" from "memorized the README," and recall is the one thing he explicitly
dislikes. The cost of the written-defense format is that it needs the LLM-judge and cannot
be graded for free; that cost is accepted here because it is the only format that reaches
Bloom Evaluate/Create for a reader who already knows the interview-level answer.

## Module table

Sixteen modules. **Concept** is the transferable design idea; **System** is the repo it is
drawn from; **Defend-and-extend** gives the representative graded prompts (each demands a
named rejected alternative + a derived number). This is a menu, not a fixed march — see the
sequencing and depth-over-breadth notes below.

| # | Concept | System it is drawn from | Representative defend-and-extend prompts |
|---|---|---|---|
| 1 | Interface-seam-first: designing the swappable contract before either side | WALterDB `StorageEngine` (also JobAggregator `Source`, OpenTrace profiler registry) | State the exact operation contract; which single leaked operation (e.g. page-level iteration the LSM can't honor cheaply) makes the heap↔LSM A/B unfair? Does the WAL live above or below the seam — defend, then argue the opposite. Add a columnar/PAX third engine: which methods break, and how do you evolve the interface *without* a versioned breaking change to callers? |
| 2 | Storage-engine abstraction: deriving the LSM-vs-heap crossover and proving it | WALterDB LSM vs heap A/B (~2.7× write throughput) | Derive the read/write/point/range mix where LSM beats heap; predict each engine's write-amp and read-amp and locate the crossover. Decompose the 2.7×: how much is sequential append vs deferred index maintenance vs skipped in-place page writes — design the microbenchmark that isolates each. Size the bloom FP budget for a 1% point-miss target over N SSTables, and name where blooms stop helping (range scans). List everything held fixed for the comparison to be causal. |
| 3 | Buffer pool (LRU-K) + page-backed B+tree: replacement policy and latch discipline | WALterDB LRU-K buffer pool + B+tree | Why LRU-K (K=2) over plain LRU or CLOCK — construct the access pattern where correlated-reference protection saves you and the one where it's pure overhead. Design latch-crabbing for concurrent insert+split; where could it deadlock against 2PL row locks, and how do you keep latch order *provably* disjoint from lock order? Trace a leaf split that evicts its parent mid-split: which invariant (pin counts) protects you, and what corruption appears if pin accounting is off by one? Derive fanout from page/key size. |
| 4 | Volcano executor + cost-based optimizer: cardinality estimation is the real hard part | WALterDB Volcano executor + cost optimizer | Iterator vs vectorized execution: what does WALterDB pay per tuple in virtual-call overhead, at what row count does vectorization win, and what must change in the operator interface? Show a 3-join query where an independence-assumption error compounds multiplicatively — bound the damage instead of chasing a perfect estimate. Design the minimal statistics set (histograms? count-distinct sketches?) justified against storage/refresh cost. Name the query class where a rule-based heuristic makes the cost model wasted complexity. |
| 5 | Concurrency control: strict 2PL + wait-for-graph vs the alternatives | WALterDB 2PL + wait-for-graph deadlock detection | Why detection over timeout-avoidance or wound-wait/wait-die prevention — name the workload where each rival wins and the signal that flips the call. Design victim selection (youngest vs least-work-done vs most-locks-held) against wasted-work and starvation. At what cycle-check frequency does detection cost more than the deadlocks it catches — derive it, propose an adaptive trigger. Quantify 2PL's throughput cost on a hot key, then redesign toward MVCC: what anomaly (write-skew) reappears that 2PL didn't have? |
| 6 | ARIES-lite recovery: WAL invariants and idempotent replay | WALterDB ARIES-lite WAL (Analysis/Redo/Undo) | State the two WAL invariants (write-ahead, force-log-at-commit) as preconditions and exhibit the durability bug each relaxation introduces. Walk Redo's repeat-history phase: why redo *loser* actions before undoing — construct the corrupted state if you skip it. Design the pageLSN idempotency check safe under crash-during-recovery; where does an off-by-one silently double-apply? Name what ARIES-lite drops (CLRs? nested top actions?) and the scenario it can't handle. Does ARIES even apply to the LSM engine, or does its durability fall out of WAL+SSTable for free? |
| 7 | Consistent hashing without a coordinator: the app-layer ring | GOOGLY app-layer ring (SHA-256, 150 vnodes, 3 Redis) | Why an app-layer ring over Redis Cluster — name what you surrendered (online resharding, MOVED/ASK, gossip) and the condition that flips it. Redesign for weighted/heterogeneous nodes (a 2×-RAM Redis): how do vnode counts encode weight, and prove load variance stays bounded. With 150 vnodes over 3 nodes derive the load-imbalance std-dev and show it shrinks with vnode count — cost of pushing to 1500? A node dies: trace which ~1/N of keys remap, then add replication and state the consistency you promise. |
| 8 | Lock-free batch-write aggregation: exactly-once across an atomic buffer swap | GOOGLY ConcurrentHashMap + LongAdder + atomic swap → single UPSERT | Prove exactly-once across the swap: what guarantees a count is neither lost nor double-counted? Exhibit the race where a writer holds the old buffer mid-increment during the swap — prove your design prevents it or reclaims the straggler. LongAdder vs AtomicLong vs a hand-striped counter: derive the contention regime (core count, key skew) where each wins. Redesign flush cadence (time vs size vs backpressure) to bound *both* p99 write latency and UPSERT batch size — failure mode if the DB stalls mid-flush? |
| 9 | Control/data-plane split + elected, migrating SFU (**design-ahead**) | conclave (phases 0–2 of 7; SFU core documented-but-unbuilt) | Server is election *arbiter* only; media is peer data-plane. Where does it break at 50 peers — arbiter, elected-SFU uplink, or fan-out CPU? Show the bottleneck math. Is SFU election leader-election (Raft-lite) or capacity-aware scheduling — name the rejected simpler design (static/lowest-ID) and why it fails under heterogeneous uplinks. Enumerate state that must transfer on mid-call migration (SRTP keys, RTP seq/timestamp continuity, subscription graph); design make-before-break that drops no keyframe — where's the unavoidable glitch? Prove the call survives arbiter death and design a re-election trigger that can't split-brain. **Go-specific:** design the migrating-SFU goroutine lifecycle under `context` cancellation — where does a leaked goroutine / send-on-closed-channel hide, and does `go test -race` actually catch it here? |
| 10 | Graceful degradation with a surfaced reason: never hard-fail on an unreliable call | NoteLens CRAG · JobAggregator stale-deletion guard · OpenTrace collectors | State the degradation invariant shared by all three, and why the reason must be *surfaced*, not swallowed. In CRAG the relevance grader can itself fail — design the fallback-of-the-fallback so the loop terminates and never returns silently-empty context; prove termination, bound worst-case retrieval cost. JobAggregator's stale-deletion is fail-**closed** (guarded on per-source success) but collection is fail-**open** — justify the asymmetry and name where flipping either becomes a correctness bug. Design the surfaced-reason envelope so degradation is measurable: what SLO tells you the safety-net went silently lossy? |
| 11 | Structural guards: making a bad outcome impossible by construction, not by prompting | JobAggregator anti-fabrication guard · OpenTrace sandboxed AST DSL | Formalize the anti-fabrication guard: every number in an output bullet must be in the source's number set. Prove it can't be bypassed — then *find* the bypass (unit conversion, rounding, derived numbers) and patch the invariant. Contrast structural guard vs LLM-judge vs unit test for this property: which is sound, which merely probabilistic, why keep all three? Enumerate the AST node allowlist and argue no allowed subset reaches I/O or unbounded compute — name the node you'd most likely forget. Give the general recipe for turning any "never X" into a post-hoc check, and state precisely when no such check exists (X undecidable from the output alone). |
| 12 | Hybrid deterministic + probabilistic pipelines: model does semantics, code owns the exact part | Set-of-Marks agent · CRAG · JobAggregator résumé pipeline | State the division-of-labor rule across all three (model picks / code locates; model retrieves / code grades overlap; LLM drafts / code checks numbers): what property must the deterministic half *always* own? Design the confidence handoff — when the probabilistic stage is uncertain, does the deterministic stage reject, fall back, or re-ask? Bound the loop and its cost. When does a post-hoc deterministic check beat constraining the model's inputs up front (grounding / constrained decoding), and vice versa — pick per system. Design an eval that separates "model got semantics wrong" from "deterministic check was wrong." |
| 13 | Package-by-feature as an architectural boundary | SideQuests (`auctions/ franchises/ disputes/`) · conclave (`internal/signaling`, `internal/overlay`) | Defend feature-slicing over package-by-layer via change locality and blast radius, then name the cross-cutting concern (auth, transactions) that breaks the clean split and how you place it. In Go, show a feature-to-feature dependency that would force an import cycle and the seam (interface in a third package) that resolves it. When does package-by-feature become *premature modularity* — give the team-size/churn threshold where package-by-layer is honestly better. Which feature packages are microservice-extraction candidates and which must stay co-transactional, and how does the boundary predict that? |
| 14 | Structured error hierarchy → centralized handler → `{code,message,details}` envelope | Cross-repo (C++/Node/Python/Java) reproduced pattern | Define the taxonomy split (client/server, transient/permanent) behind the envelope and show the handler mapping each to an HTTP status + retryability without leaking internals. Translate to idiomatic Go for conclave: `%w` wrapping + `errors.Is/As` at one middleware, sentinel vs typed errors, the single place errors map to a signaling-protocol code. The `details` field can leak stack/SQL/PII — design and *structurally* enforce the redaction boundary (client vs logs vs traces). Show where a wrong retryable classification causes a *correctness* bug (double-apply) vs merely an availability bug, and how the envelope must encode the difference. |
| 15 | A/B baseline-vs-treatment measurement designed in from the start | WALterDB LSM/heap · TraceLens GRPO · GOOGLY (uncommitted suite) | Across LSM-vs-heap, GRPO'd-0.5B-vs-GPT-4o-mini, and single-vs-multi-agent grading — state the one thing each A/B must hold fixed to be causal and the confounder you're most likely to miss. GOOGLY's ~17ms p95 / 1.85K req/s came from an *uncommitted* suite — redesign it reproducible-and-committed: the minimum harness (fixed dataset, warmup, percentile reporting) that makes a p95 claim defensible. Design the stopping rule tied to *measured variance*, not a round number. Name the decision you *can't* fairly A/B (irreversible, or the treatment changes the workload) and what you substitute. |
| 16 | Reward shaping + LLM-as-judge validity: a specification-gaming surface | TraceLens (shaped reward; grader is both reward and eval) | The shaped reward (signal-discovery bonuses, step + early-submit penalties) is a gaming surface — name three ways a 0.5B policy farms reward without diagnosing, and the *structural* fix for each. The grader is both reward signal and eval ground-truth — separate them or defend the coupling, and prove the 0.5B-beats-GPT-4o-mini claim (0.618 vs 0.504 on hard tasks) isn't overfit to the grader's blind spots. Under partial observability with step penalties, does the reward incentivize giving up early on hard incidents — show the incentive and reshape it. GRPO vs PPO for this 0.5B setup: why GRPO, what does dropping the value network cost under sparse/shaped reward, and at what model scale would you switch back? |

## Sequencing: three arcs matched to fluency

Run the modules in three arcs ordered by where he is strongest, so each pass builds
confidence before it stretches him:

1. **Storage-internals arc (C++ / WALterDB)** — modules 1–6. His deepest area; go all the
   way down here.
2. **Distributed/backend arc (Java / Python)** — modules 7, 8, 13, 14. Consistent hashing,
   lock-free aggregation, feature boundaries, error envelopes.
3. **Frontier arc** — modules 9, 10, 11, 12, 15, 16. Control/data-plane SFU (Go), hybrid
   pipelines, structural guards, degradation, A/B design, reward shaping. This arc stretches
   him into distributed internals and his weakest language.

Put the **conclave module (9) last in whatever pass reaches it**: it is design-ahead (its
hard core is doc-comment stubs) and it is his first real Go, so it stacks the two hardest
variables — an unbuilt design and an unfamiliar language — and should not gate the earlier,
more grounded modules.

## Two framing rules the questions must obey

Both come straight from the source research's risk list and are non-negotiable for this
track to be fair:

- **Design-ahead vs measured.** Modules on unbuilt cores (conclave's elected/migrating SFU)
  or unreproducible numbers (GOOGLY's uncommitted suite) are framed as *harness-building /
  design-ahead* exercises — "design the migration" / "make this benchmark defensible" — not
  "defend what you measured." Asking him to defend a number he never committed is a
  false-premise question.
- **Defend *this* design, not *your* design.** WALterDB, SideQuests, and TraceLens are
  team/capstone builds; some decisions may be a collaborator's. Prompts say "defend this
  design" (a valid exercise regardless of authorship), never "defend your decision," to
  avoid a false-premise attribution.

And one calibration rule: **keep the distributed-systems design question separate from the
idiomatic-Go question** in module 9. Conflating them lets a Go-syntax gap masquerade as a
design gap (or hide one). The design essay is graded on distributed reasoning; the Go
lifecycle question is a separate item.

## Limitations / open questions

- **Depth beats breadth, and 16 is a menu.** The defend-and-extend format only pays off with
  depth — running 4–5 modules to full written-defense depth is worth more than surveying all
  16 shallowly. Treat the table as the reservoir, not a completion checklist.
- **This track's grade is the least reproducible in Crucible.** Its verdicts come entirely
  from the hosted LLM-judge, so per R9 in [PLAN.md](../../PLAN.md) they are *not*
  bit-reproducible: retuning this rubric or swapping the judge model invalidates stored
  grades and needs a (non-free, non-deterministic) re-grade. `recompute_from_log()` replays
  scheduler arithmetic, not the judging.
- **The judge can be too lenient on eloquent hand-waving.** The reference-grounding and
  deterministic-wins guards ([../04-grading.md](../04-grading.md)) bound this, and the
  three-part rubric (rejected alternative + failure mode + number) is the concrete anchor —
  but an essay that hits all three formally while missing the point remains the residual
  failure mode. The honest mitigation is that the grade's only value is accurate
  self-knowledge, which he wants; there is no adversary to fool but himself.
- **RL/eval modules (15, 16) sit partly outside pure systems.** Calibrate them to *design
  reasoning* (incentive analysis, eval separation, reward-hacking surfaces) rather than
  SOTA RL-algorithm internals — the area where he is strong but not expert.
- **Open:** should completed module memos feed back into the repos as living `DESIGN_NOTES` /
  `ARCHITECTURE` docs? Doing so would close his "uncommitted benchmark" and "design-ahead"
  growth edges simultaneously and turn the curriculum into shipped documentation — but it
  raises the per-module time budget from "write a memo" to "build the harness / write the
  design." Deferred to the roadmap.

---

*Source research: [../../RESEARCH/project-design.md](../../RESEARCH/project-design.md).
Sibling docs referenced: [../02-features.md](../02-features.md),
[../04-grading.md](../04-grading.md), [../07-landscape.md](../07-landscape.md),
[../../PLAN.md](../../PLAN.md).*
