# Deep Distributed-Systems / Cloud / DevOps Curriculum

> Research track. Faithful rendering of the agent's structured findings.

**Dimension:** Deep distributed-systems internals + cloud + DevOps/SRE curriculum (beyond interview-level system design)

## Summary

A 12-module, build-and-break syllabus for an engineer who already owns interview-level system design and wants the internals. It is sequenced so each module hands the next a primitive it depends on: consistency models frame everything, consensus and replication give you the machinery, transactions/time/messaging build coordinated state on top, then caching/observability/orchestration/IaC/cloud/reliability turn it into an operable system. Every module is biased toward WHY, the named rejected alternative, and the canonical paper, and pairs a from-scratch build (his ethos) with an adversarial verification (Jepsen-style linearizability checks, fault injection, `-race`, back-of-envelope capacity math). The hard, load-bearing recommendation: do NOT teach these as reading modules — each one earns its keep only when he implements the primitive and then breaks it under partition/latency/crash. Go is used deliberately as the implementation language for the consensus/replication core (raft, WAL, gossip) so the curriculum doubles as his path from Go early-beginner to fluent, while Python/FastAPI carries the outbox/idempotency/observability service work where he is already deep. Primary spine: DDIA (Kleppmann) as the connective text, with Raft, Dynamo, Spanner, Kafka, Bigtable/GFS, Borg, and the Google SRE book as the per-topic primary sources.

## Key findings

### The learner is past 'know the concept' and needs the failure-mode boundary of each concept, which only implementation-plus-fault-injection exposes.

He already knows consensus/sharding/locking/CAP as vocabulary. The delta from interview-level to internals-level is entirely in the corner cases: what linearizability actually forbids that sequential consistency allows, why Raft needs the no-op-commit-on-election-and-the-commit-index-rule, why 2PC blocks and 3PC's non-blocking claim dies under network partition. These are learned by building the thing and running a linearizability checker (Jepsen/Elle, or Porcupine in Go) against it, not by re-reading summaries.

*Source:* DDIA ch.5/7/9; Raft paper §5.4 (safety); Jepsen analyses (aphyr.com)

### Go is the correct implementation language for the consensus/replication spine, and this curriculum is also his fastest route to Go fluency.

Raft's reference implementations (etcd/raft, hashicorp/raft), the canonical MIT 6.824 labs, and most production consensus code are Go. His concurrency discipline (2PL, @Version, lock-free aggregation, context+WaitGroup in conclave) already exists — goroutines/channels/select are 'new syntax for a problem he's solved.' Building raft in Go under `go test -race` closes his stated Go gaps (interfaces, error wrapping, generics, timers/tickers) on load-bearing code rather than toy drills.

*Source:* MIT 6.824 labs; etcd/raft, hashicorp/raft source; his conclave Go experience

### Python/FastAPI should carry the application-tier distributed patterns where he is already deepest, so cognitive load stays on the concept.

Transactional outbox, idempotency keys, saga orchestration, CDC consumers, RED-metric instrumentation, and SLO burn-rate alerting are service-layer patterns. Building them in FastAPI + asyncio + a real Postgres/Kafka (not mocks) lets him spend attention on delivery semantics and coordination, not language. His mypy-strict/pytest/respx harness discipline transfers directly to deterministic distributed tests with injected clocks and fault proxies (toxiproxy).

*Source:* DDIA ch.11/12; microservices.io outbox/saga patterns; his JobAggregator/OpenTrace test discipline

### The strongest single organizing text is DDIA, but it must be supplemented with primary papers at every internals boundary because DDIA deliberately abstracts.

DDIA gives the map and the honest trade-off framing he values, but stops short of implementation detail. Raft's safety argument, Dynamo's sloppy-quorum + hinted-handoff + vector-clock reconciliation, Spanner's TrueTime commit-wait bound, Kafka's ISR/leader-epoch fencing, and Chubby/ZAB's lease semantics each require the source paper. The pairing (DDIA chapter -> primary paper -> build) is the repeatable module shape.

*Source:* Kleppmann DDIA; Ongaro&Ousterhout Raft; DeCandia et al. Dynamo; Corbett et al. Spanner

### Reliability/SRE and capacity math must be woven through as verification, not bolted on as a final module, to match how he defines 'done.'

He treats verification as the definition of done and runs adversarial self-audits. So chaos/fault-injection, back-of-envelope capacity (Little's Law, queueing, tail-latency amplification), and SLO/error-budget math should appear as the acceptance test for each build module, not only in the reliability capstone. This mirrors his A/B-measurement-designed-in-from-the-start habit (LSM vs heap, GRPO vs baseline).

*Source:* Google SRE Book & SRE Workbook; Little's Law; Dean & Barroso 'The Tail at Scale'

## Recommendations

- Sequence, don't cherry-pick: run Modules 1->12 in order. Consistency (1) frames everything; consensus (2) and replication (3) are the machinery the middle modules build on; orchestration/IaC/cloud/reliability (9-12) only make sense once the state-coordination core is real. Skipping ahead to K8s/Terraform without the consensus foundation reproduces exactly the interview-level surface understanding he's trying to escape.
- Use Go as the implementation language for the internals spine (Modules 2, 3, 5, 6-build, 9-build, 12) and treat the curriculum as his Go-fluency path — building raft under `go test -race` closes his stated Go gaps (interfaces, error wrapping with %w, timers/tickers, generics) on load-bearing code. Keep Python/FastAPI for the application-tier patterns (Modules 4, 8) where he is already deep so attention stays on the concept.
- Anchor MIT 6.824 (Distributed Systems) labs as the backbone for Modules 2-4 — they are the gold-standard build-raft-then-build-KV-then-shard progression in Go, with an autograder that is itself adversarial. Pair each lecture with the matching DDIA chapter and primary paper.
- Make DDIA (Kleppmann) the connective read but ALWAYS pair each chapter with its primary paper at the internals boundary (Raft, Dynamo, Spanner, Kafka/ISR, Bigtable, Borg) — DDIA deliberately abstracts away the implementation detail that is the whole point here.
- Bake verification in as the acceptance test for every module, not a final phase: linearizability checking (Porcupine in Go, or Elle/Jepsen), toxiproxy for network fault injection, `go test -race`, and back-of-envelope capacity math. This matches how he already defines done and runs adversarial self-audits.
- For each design-essay skill, require the deliverable to name the rejected alternative and its specific failure — enforce the format he values (WHY + named trade-off + rejected option written down), turning essays into the DESIGN_NOTES.md artifacts he already writes.
- Write it up as a living syllabus doc in the repo (his layered-docs habit): a phase/status table per module with an honest done-marker, a per-module 'primary paper + DDIA chapter + build + verification' row. Keep it LOCAL (per his global instruction — no artifact publishing); I can generate this as a Markdown file on request.
- Budget honestly: the raft lab alone is 40-60 focused hours and the figure-8/snapshot parts are where most people stall — that is the hard part, not the leader election. Tell him to expect the difficulty in the safety proofs and log-compaction, not the happy path.

## Proposed modules

### Module 1 — Consistency Models & CAP/PACELC (the frame for everything)

**Objectives**

- Place linearizability, sequential, causal, and eventual consistency on a single lattice and state precisely what each one FORBIDS (not just what it allows) — the real content is the gap between adjacent models.
- Reframe CAP as the trivial-but-true corner case and PACELC (Abadi) as the operationally useful statement: the latency-vs-consistency tax you pay even when there is NO partition.
- Understand why 'strong consistency' is underspecified and why linearizability (a recency guarantee on single objects) is orthogonal to serializability (a transaction-isolation guarantee) — the classic conflation to kill.

**Testable skills**

- Design-essay: Given a shopping-cart service, argue for causal+eventual over linearizable, name the specific anomaly you accept (e.g. concurrent add/remove reconciliation) and the rejected alternative (linearizable via consensus) with its latency cost.
- Build: Implement a linearizability checker harness (or wire Porcupine/Elle) and run it against a naive read-repair KV store; produce a concrete history that violates linearizability but satisfies sequential consistency.
- Back-of-envelope: A cross-region quorum read spans regions at 40ms one-way RTT. Compute added p50 read latency for a 3-region majority quorum, then state the PACELC 'EL' cost you just quantified.
- Adversarial: Write the minimal history (3 ops, 2 clients) that distinguishes causal from sequential consistency and explain why no single-object test can catch it.
- Recall-free: Explain why CAP's 'CA' is not a real operating point for a networked system, using the partition-is-not-optional argument rather than quoting the theorem.

### Module 2 — Consensus: Raft in depth, Paxos overview, leader election, quorums

**Objectives**

- Implement Raft end to end in Go (leader election, log replication, safety, persistence, snapshotting) and be able to defend every safety rule by constructing the split-brain/stale-leader history it prevents.
- Understand WHY Raft chose understandability over Multi-Paxos's generality: strong leader + log contiguity + the commitment restriction (only commit current-term entries directly). Name what Raft gives up (no out-of-order commit, leader is a throughput bottleneck).
- Map the family: single-decree Paxos -> Multi-Paxos -> Raft -> ZAB/Viewstamped Replication, and where EPaxos/Flexible-Paxos change the quorum-intersection assumption.

**Testable skills**

- Build (spine): Pass MIT 6.824 Lab 2A-2D (or equivalent) — Raft in Go under `go test -race` — including the figure-8 safety test and log-compaction snapshot.
- Design-essay: Explain the §5.4.2 rule 'a leader never commits entries from previous terms by counting replicas.' Construct the exact 5-node history where violating it loses a committed entry.
- Back-of-envelope: With 5 nodes and 150ms election timeout jitter [150,300]ms, estimate expected time-to-elect after a leader crash and the availability hit; then argue 3 vs 5 vs 7 nodes as an availability/throughput/latency trade.
- Design-essay: Contrast Raft's strong leader with EPaxos's leaderless commit — name the workload (geo-distributed, low-conflict) where EPaxos wins and the cost (dependency tracking complexity) that got it rejected in most systems.
- Adversarial: Inject a network partition that isolates the leader; show via logs that the old leader cannot commit (fails to reach quorum) and that reads served by it are stale — then add leader-lease reads and show the fix.

### Module 3 — Replication & Partitioning: log-shipping, CDC, sharding, rebalancing, consistent hashing at scale

**Objectives**

- Build log-based (statement vs WAL vs logical/row) replication and understand why logical replication decoupled from storage format is what makes CDC and heterogeneous replicas possible.
- Master partitioning strategies (range vs hash) and the rebalancing problem: why 'hash mod N' is the canonical WRONG answer and how consistent hashing with virtual nodes, and Dynamo/Cassandra's token rings, bound the keys-moved on membership change.
- Understand real-world consistent hashing beyond the textbook: bounded-load consistent hashing (Google), rendezvous hashing as the rejected-but-simpler alternative, and hot-shard/skew mitigation.

**Testable skills**

- Build: Implement a consistent-hash ring with virtual nodes in Go; measure key-movement on node add/remove and empirically show it is ~1/N vs mod-N's near-total reshuffle. (He has built a ring before — now instrument and stress it.)
- Design-essay: Design CDC from Postgres to a search index via logical decoding + transactional outbox. Name the rejected alternative (dual-write) and the exact failure it prevents (write-to-DB-succeeds, write-to-index-fails).
- Back-of-envelope: 1B keys, 200 nodes, target <5% keys moved per single-node failure — compute required virtual-nodes-per-node and the memory cost of the ring metadata.
- Design-essay: Compare range partitioning (Bigtable/HBase, good for scans, bad for hotspots) vs hash (good spread, no range scans). Pick for a time-series workload and defend against the hotspot on 'now'.
- Adversarial: Simulate a skewed key (celebrity problem) on a hash ring; show the hot vnode and apply bounded-load consistent hashing or key-splitting, quantifying the tail-latency improvement.

### Module 4 — Distributed Transactions: 2PC/3PC, sagas, transactional outbox, idempotency

**Objectives**

- Understand precisely why 2PC blocks (coordinator failure after prepare leaves participants in-doubt holding locks) and why 3PC's non-blocking claim fails under network partition — so you can name when neither is acceptable.
- Build the practical toolkit that replaces distributed ACID in microservices: transactional outbox + relay, idempotency keys, and saga orchestration/choreography with compensating actions.
- Reason about exactly-once as a myth at the transport layer and a real property only as effectively-once = at-least-once delivery + idempotent processing.

**Testable skills**

- Build (Python/FastAPI): Implement transactional outbox with a Postgres outbox table + a relay poller/CDC to Kafka, plus idempotency-key dedup on the consumer; prove no lost/dup message across a crash injected between DB-commit and publish.
- Design-essay: Walk the 2PC in-doubt window step by step; state exactly which failure (coordinator dies post-prepare) causes indefinite blocking and why participant timeouts cannot safely resolve it.
- Back-of-envelope: A saga has 5 steps averaging 80ms each with 2% per-step failure. Compute end-to-end p50, expected compensation frequency, and the lock-hold-time argument for saga over 2PC.
- Design-essay: Design idempotency keys for a payments endpoint — key scope, storage TTL, and the race between two retries arriving concurrently (name the fix: unique constraint / SELECT-FOR-UPDATE / atomic insert).
- Adversarial: Kill the outbox relay mid-batch and show at-least-once redelivery; then show the consumer's idempotency guard making it effectively-once. Contrast with the rejected dual-write baseline's data loss.

### Module 5 — Time & Ordering: logical clocks, vector clocks, hybrid logical clocks, TrueTime

**Objectives**

- Internalize why physical clocks cannot order distributed events (clock skew, NTP jitter) and how Lamport clocks give a consistent total order while vector clocks give the causal partial order needed for conflict detection.
- Understand Hybrid Logical Clocks (HLC) as the engineering sweet spot: causality of logical clocks + closeness-to-physical-time of NTP, in bounded space — and Spanner's TrueTime + commit-wait as the alternative that buys external consistency with hardware (GPS/atomic clocks) instead of coordination.
- Connect vector clocks to Dynamo's conflict reconciliation and to CRDT merge functions.

**Testable skills**

- Build: Implement Lamport and vector clocks in Go; on a simulated 3-node message log, produce two concurrent events vector clocks flag as concurrent but Lamport falsely totally-orders.
- Design-essay: Explain Spanner's commit-wait: given TrueTime uncertainty ε, why does waiting out 2ε guarantee external consistency, and what throughput/latency price does that buy? Name the rejected alternative (coordinate via consensus on every commit).
- Back-of-envelope: TrueTime ε averages 4ms. Compute commit-wait overhead on write throughput for a single-key transaction and the argument for tightening ε with more time masters.
- Design-essay: Choose HLC over pure vector clocks for a multi-region KV store and state the specific benefit (bounded size, meaningful timestamps for debugging/TTL) and the guarantee you give up vs vector clocks (full causal history).
- Adversarial: Introduce 200ms clock skew on one node using physical timestamps for ordering; show the resulting causality violation (effect before cause) and fix it with HLC.

### Module 6 — Messaging & Streaming: Kafka internals, log compaction, exactly-once, backpressure

**Objectives**

- Understand Kafka as a distributed, partitioned, replicated commit log: the ISR (in-sync replica) protocol, leader epochs for fencing zombie leaders, high-watermark advancement, and why the log-as-source-of-truth model unifies messaging and stream processing.
- Master delivery-semantics reality: idempotent producer (PID + sequence numbers), transactions (two-phase commit across partitions + __consumer_offsets) for read-process-write exactly-once, and log compaction for changelog/KTable materialization.
- Reason about backpressure and consumer-lag as a flow-control and capacity problem, not a config knob.

**Testable skills**

- Build: Run a real Kafka; implement a read-process-write pipeline with the transactional producer and consumer isolation.level=read_committed; prove exactly-once by crash-injecting mid-transaction and checking no dup/loss downstream.
- Design-essay: Explain how leader epochs prevent a zombie leader from truncating committed data after a network partition — construct the exact log-divergence scenario they fix (the pre-KIP-101 truncation bug).
- Back-of-envelope: 500K msg/s, 1KB each, replication factor 3, 7-day retention. Compute network bandwidth (produce + replicate), disk needed, and partition count for a consumer that processes 10K msg/s/instance.
- Design-essay: Design log compaction for a user-profile changelog; explain the tombstone + delete-retention semantics and why compaction (not time-retention) is what makes the topic a queryable table.
- Adversarial: Overload a slow consumer and observe growing lag; distinguish the three responses (scale consumers / drop-with-sampling / backpressure the producer) and quantify when each applies via Little's Law.

### Module 7 — Caching & CDNs: invalidation, coherence, thundering herd

**Objectives**

- Treat cache invalidation as the genuinely hard problem it is: understand write-through vs write-back vs write-around vs cache-aside and the staleness/coherence trade each makes, plus why TTL-only is the honest default.
- Master the stampede/thundering-herd failure family (cache miss on a hot key -> origin overload) and the specific mitigations: request coalescing/single-flight, probabilistic early expiration (XFetch), and negative caching.
- Understand CDN mechanics: edge caching, cache keys, purge propagation latency, and stale-while-revalidate as the availability-favoring choice.

**Testable skills**

- Build (Go): Implement single-flight request coalescing in front of an expensive origin call; load-test to show N concurrent misses collapse to 1 origin hit, and measure origin-QPS reduction.
- Design-essay: Choose an invalidation strategy for a feed-ranking service and name the rejected alternative — e.g. cache-aside + TTL + probabilistic early refresh over write-through, justifying via write-amplification and staleness tolerance.
- Back-of-envelope: 95% cache hit ratio, 50K req/s, origin p99 200ms. Compute origin QPS, then recompute the origin-overload spike if a hot key's entry expires and 5K requests miss simultaneously — motivating coalescing.
- Design-essay: Explain why a synchronous cross-region CDN purge is infeasible and how stale-while-revalidate + short TTL bounds staleness while preserving availability during origin failure.
- Adversarial: Trigger a cache stampede on a single hot key; apply XFetch probabilistic early expiration and show the herd flattening, quantifying the p99 origin-latency improvement.

### Module 8 — Observability: metrics/logs/traces, RED/USE, SLO/SLI, error budgets

**Objectives**

- Distinguish the three pillars by what question each answers and their cost/cardinality trade: metrics (cheap, aggregatable, low-cardinality), logs (high-cardinality, expensive at scale), traces (causal request path across services).
- Apply RED (Rate/Errors/Duration, request-centric) and USE (Utilization/Saturation/Errors, resource-centric) as complementary lenses, and design SLIs -> SLOs -> error budgets with multi-window multi-burn-rate alerting rather than threshold alerts.
- Understand distributed tracing propagation (W3C traceparent, span context) and sampling trade-offs (head vs tail sampling).

**Testable skills**

- Build (Python/FastAPI): Instrument a service with RED metrics (Prometheus) + OpenTelemetry traces across two hops; produce a flamegraph/trace showing where p99 latency is spent. (Builds on his OpenTrace flamegraph fluency.)
- Design-essay: Design an SLO for a checkout API (99.9% of requests <300ms over 28d). Derive the error budget in minutes, and the multi-burn-rate alert thresholds (fast-burn 2%/1h vs slow-burn 5%/6h) with why single-threshold alerting is rejected.
- Back-of-envelope: 200K req/s, want p99 latency histograms at 1% head sampling for traces. Compute trace-storage/day and argue head vs tail sampling for catching rare slow requests.
- Design-essay: Explain why you cannot alert on 'CPU > 80%' meaningfully and reframe via USE saturation (run-queue depth) — connect to why saturation predicts latency cliffs before utilization does.
- Recall-free: Given a p50=20ms/p99=800ms latency profile, argue what the gap tells you (tail amplification / GC / queueing / lock contention) and which pillar you'd reach for to localize it.

### Module 9 — Containers & Orchestration: cgroups/namespaces -> Docker -> Kubernetes control loop

**Objectives**

- Build a container FROM SCRATCH (his ethos): implement isolation with Linux namespaces (pid/net/mnt/uts/ipc/user) + cgroups v2 (cpu/memory limits) + pivot_root, to demystify that 'a container is a process, not a VM.'
- Understand Kubernetes as a set of reconciliation control loops over declarative desired-state in etcd (a Raft store — connects to Module 2): the scheduler (predicates/priorities/bin-packing), controllers (level-triggered not edge-triggered), and the kubelet.
- Reason about service mesh (sidecar vs sidecar-less/eBPF) trade-offs: mTLS, retries, circuit-breaking at the infra layer vs the latency/complexity tax.

**Testable skills**

- Build (Go): Write a ~200-line container runtime using namespaces + cgroups v2 that runs a shell with a memory limit and isolated PID/net; prove the memory limit by OOM-killing a hog. (Leverages his uinput/Linux-internals depth.)
- Design-essay: Explain why Kubernetes controllers are level-triggered (reconcile to desired state) not edge-triggered (react to events), and the specific failure (missed event -> permanent drift) edge-triggering causes.
- Back-of-envelope: Schedule 500 pods (each 250m CPU / 512Mi) onto nodes with 8 CPU / 32Gi. Compute nodes needed under bin-packing, headroom for one node failure, and the fragmentation cost of anti-affinity rules.
- Design-essay: Decide sidecar mesh (Istio/Envoy) vs sidecar-less (eBPF/Cilium) for a 300-service cluster; name the rejected option and the trade (per-pod proxy latency+memory vs kernel-level complexity and feature gaps).
- Adversarial: Kill the etcd leader in a test cluster and observe the control plane during re-election; explain why running pods keep serving (data plane independent of control plane) — a direct payoff of the Module-2 Raft understanding.

### Module 10 — IaC & CI/CD: Terraform, GitOps, progressive/canary delivery

**Objectives**

- Understand IaC as declarative desired-state with a reconciliation model (Terraform plan/apply, state as source of truth) and the failure modes: state drift, state-lock contention, and the blast radius of a bad plan.
- Adopt GitOps (git as the single source of truth, a controller continuously reconciling cluster to repo — Argo CD/Flux) and articulate why pull-based reconciliation beats push-based CI-deploys for auditability and drift-correction.
- Design progressive delivery: blue-green vs canary vs rolling, automated canary analysis (metrics-gated promotion), and feature flags as the decoupling of deploy from release.

**Testable skills**

- Build: Author Terraform for a small multi-resource stack (VPC + compute + queue) with remote state + locking; deliberately cause drift (manual console change) and show plan detecting it, then reconcile.
- Design-essay: Contrast canary (fractional traffic + metric-gated promotion) vs blue-green (instant switch, easy rollback, 2x cost) for a stateful service; name which you reject and why (blue-green's DB-migration problem).
- Back-of-envelope: A canary at 5% traffic on a 0.5%-baseline-error endpoint; how many requests must the canary serve to detect a doubled error rate (1%) at 95% confidence? (Motivates canary-duration math.)
- Design-essay: Argue pull-based GitOps over push-based pipeline deploys for a regulated env — name the specific property gained (drift auto-correction + git-as-audit-log) and the rejected push model's gap.
- Adversarial: Wire an automated canary that promotes on SLO metrics (from Module 8) and rolls back on burn-rate breach; inject a latency regression and prove auto-rollback fires before error budget is exhausted.

### Module 11 — Cloud Primitives: compute, storage classes, queues, serverless trade-offs

**Objectives**

- Map the compute spectrum (VM -> container -> serverless/FaaS) by the axes that actually matter: cold-start latency, statefulness, cost-per-idle, and control — and know when each is the wrong tool.
- Understand storage as tiered trade-offs: object (S3-class, 11-nines durability via erasure coding, eventual-then-strong-read consistency), block (EBS-class, single-attach), and the storage-class cost/retrieval-latency ladder (hot/warm/cold/archive).
- Reason about managed queues (SQS/PubSub) vs a log (Kafka/Kinesis): at-least-once + visibility-timeout redelivery vs ordered replayable log, and the FIFO-throughput trade.

**Testable skills**

- Design-essay: Choose serverless vs container for (a) a spiky webhook processor and (b) a steady 24/7 stream consumer; quantify the cold-start and cost-per-idle argument that flips the decision between them.
- Back-of-envelope: Store 50TB with 20% accessed monthly, rest archival. Compute monthly cost across hot vs cold tiers + retrieval fees, and find the access-frequency break-even for tiering a blob.
- Design-essay: Explain S3's durability (erasure coding across AZs) vs its consistency model; contrast with block storage's single-attach constraint and why that shapes stateful-vs-stateless architecture on cloud.
- Design-essay: Pick SQS-style queue vs Kafka-style log for an order pipeline needing replay + ordering; name the rejected option and its specific gap (SQS: no replay/global order; Kafka: ops burden, partition-count rigidity).
- Back-of-envelope: A Lambda at 200ms avg, 512MB, 10M invocations/month vs an always-on container; compute the cost crossover and state the utilization threshold where serverless stops being cheaper.

### Module 12 — Reliability Engineering: failure modes, chaos, capacity math, load balancing (capstone)

**Objectives**

- Build a working model of correlated/cascading failure: retry storms, thundering herds, metastable failures, and why naive retries + timeouts amplify outages — then apply the fixes (exponential backoff + jitter, circuit breakers, load shedding, deadline propagation).
- Master capacity as first-principles math: Little's Law, the M/M/1 latency-vs-utilization knee, tail-latency amplification across fan-out ('The Tail at Scale'), and back-of-envelope sizing you can defend.
- Understand load-balancing algorithms by their failure behavior: round-robin vs least-connections vs least-request vs power-of-two-choices vs consistent-hashing-with-bounded-load, and run real chaos experiments (Jepsen-style) as the acceptance test for the whole curriculum.

**Testable skills**

- Build: Implement power-of-two-choices load balancing in Go and compare tail latency vs round-robin under heterogeneous server speeds; show P2C's near-optimal balancing at O(1) coordination — and name why full least-loaded is rejected (herd-toward-idle).
- Back-of-envelope: A service fans out to 100 shards, each p99=10ms; compute the probability the overall request hits at least one p99 tail and the resulting request-level p99 (tail amplification) — then design hedged requests to fix it.
- Back-of-envelope: Via Little's Law, a service at 80% utilization on 20ms base service time — estimate queueing latency and the latency cliff at 90% and 95%; use it to justify a headroom target.
- Design-essay: Design retry policy for a dependency to AVOID a retry storm — backoff+jitter, retry budget (max % of traffic as retries), and circuit breaker; name the rejected naive-fixed-retry and the metastable failure it triggers.
- Adversarial (capstone): Run a Jepsen/chaos suite against a system you built in Modules 2-6 — inject partitions, clock skew, and process pauses — and either find a linearizability/consistency violation or produce the evidence it holds, reported as p50/p99 + violation-count, matching his 'verification is done' bar.

## Risks & gotchas

- Scope is large — 12 deep modules is a multi-month commitment. Risk of stalling in Module 2 (raft) and never reaching cloud/DevOps. Mitigation: the raft->KV->shard spine (M2-4) is the irreducible core; Modules 7-11 can be time-boxed shallower if needed without breaking the arc.
- The 'build from scratch' ethos he loves can become a time sink in Modules 9-11 (a from-scratch container is great; a from-scratch Kubernetes is not the learning target). Draw the line explicitly: build the container runtime and the raft store from scratch; USE real Kafka/Postgres/K8s/Terraform and study their internals — reaching for the tool where the tool is not the primitive.
- Linearizability checkers (Jepsen/Elle) are Clojure-heavy; Porcupine (Go) or a hand-rolled checker is the lower-friction path and keeps him in Go. Don't let tooling setup become the blocker.
- Cloud-primitive and IaC modules incur real (small) cloud spend for hands-on labs. Use free-tier + localstack/kind/k3d where possible — aligns with his free-tier/self-hosting habit — but some canary/multi-AZ realism genuinely needs a real account.
- Aspirational-framing edge (flagged in his own profile): resist labeling a single-node lab 'production-grade.' Each module's honest Limitations section should name what the build does NOT prove (e.g. 'this raft is correct under the tested fault schedule, not formally verified').
- Exactly-once (M4/M6) is the most common place strong engineers absorb a myth. Keep hammering: exactly-once-delivery does not exist at the transport layer; effectively-once = at-least-once + idempotency. Verify it, don't assert it.

## Open questions

- Target timeline and weekly hours? That determines whether this is a ~4-month intensive (all 12 deep) or a ~9-month part-time arc, and how shallow Modules 7/10/11 can go.
- Does he want a single integrating capstone project (the replicated KV store threaded through M2-6-12) or 12 independent artifacts? The former is more resume-worthy and matches his flagship-project pattern.
- Is career intent SRE/infra-leaning (weight Modules 8-12 heavier) or distributed-systems-engineer-leaning (weight 1-6 heavier)? The syllabus supports both but the depth allocation should follow intent.
- Should I generate the full living-syllabus Markdown doc (phase/status table, per-module paper+build+verification rows) as a local file now, per his layered-docs habit?
- Preferred cloud for M10/M11 labs (AWS, given his existing AWS deploy-guide, vs GCP where Spanner/Borg papers land closest)?

## Citations

- [Designing Data-Intensive Applications (Kleppmann) — the connective spine](https://dataintensive.net/)
- [In Search of an Understandable Consensus Algorithm (Raft) — Ongaro & Ousterhout](https://raft.github.io/raft.pdf)
- [Dynamo: Amazon's Highly Available Key-value Store — DeCandia et al.](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
- [Spanner: Google's Globally-Distributed Database (TrueTime) — Corbett et al.](https://static.googleusercontent.com/media/research.google.com/en//archive/spanner-osdi2012.pdf)
- [Kafka: a Distributed Messaging System / Kafka internals & KIP-101 leader epochs](https://kafka.apache.org/documentation/)
- [MIT 6.824 Distributed Systems — labs (build Raft + KV + sharding in Go)](https://pdos.csail.mit.edu/6.824/)
- [Google SRE Book & SRE Workbook — SLO/SLI, error budgets, burn-rate alerting](https://sre.google/books/)
- [The Tail at Scale — Dean & Barroso (fan-out tail-latency amplification)](https://research.google/pubs/pub40801/)
- [Jepsen — adversarial consistency/linearizability testing analyses](https://jepsen.io/analyses)
- [Consistency Tradeoffs in Modern Distributed Database Design (PACELC) — Abadi](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf)

