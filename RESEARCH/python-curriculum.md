# Python + Framework Internals Curriculum

> Research track. Faithful rendering of the agent's structured findings.

**Dimension:** Python + framework mastery curriculum (internals-first) for an advanced systems engineer

## Summary

A 9-module deep-internals curriculum for an engineer already fluent in Python/FastAPI/asyncio who wants mastery, not basics. Every module is framed around WHY and the named rejected alternative, biased toward mechanism (CPython bytecode, the pydantic-core Rust boundary, asyncio's event-loop scheduling, mypy's variance rules, SQLAlchemy's unit-of-work). Testable skills are phrased as things he can be quizzed on or made to build from scratch, matching his "reimplement the primitive to understand it" ethos and his Correctness > Reliability > UX > Maintainability > Performance ranking. The spine is a single realistic deliverable — a typed, async, pydantic-v2 FastAPI backend with an async SQLAlchemy 2.0 data layer, SSE + WebSocket endpoints, and a strict ruff+mypy+pytest+hypothesis gate — so every internals topic maps to a load-bearing use in that codebase rather than being studied in isolation.

## Key findings

### Pydantic v2 moved validation into a compiled Rust core (pydantic-core), so 'custom validator' semantics changed shape, not just syntax

v2 builds a CoreSchema that pydantic-core executes; @field_validator/@model_validator with mode='before'|'after'|'wrap' map onto positions in that schema pipeline. Understanding the before/after/wrap split and the validator-vs-serializer asymmetry is the real v1->v2 migration cost, more than the rename churn (validator->field_validator, Config class->model_config, .dict()->.model_dump()).

*Source:* pydantic v2 architecture (pydantic-core + CoreSchema)

### The GIL blocks CPU-bound Python bytecode concurrency but does NOT block during most I/O syscalls or inside well-behaved C extensions that release it

This is the single distinction that decides asyncio-vs-thread-vs-process for a given workload. asyncio wins for many-connection I/O (one thread, cooperative yields at await), threads win when the blocking call releases the GIL (sockets, many DB drivers, numpy), processes are the only real answer for pure-Python CPU parallelism. He should be able to derive the choice from first principles, not memorize a table.

*Source:* CPython GIL semantics + asyncio design

### asyncio cancellation is delivered as a CancelledError raised at the next await point, and structured concurrency (TaskGroup) changes the failure-propagation contract

A cancelled task doesn't stop instantly; the loop schedules a throw of CancelledError into the coroutine at its suspension point, which is why shielding, finally-block cleanup, and 'swallowing CancelledError is a bug' all matter. TaskGroup (3.11+) cancels siblings on first exception and raises ExceptionGroup — a different reliability contract than gather(return_exceptions=...).

*Source:* asyncio Task/TaskGroup cancellation model (3.11+)

### mypy strict correctness rests on variance and the Protocol/nominal split, which most 'fluent' Python users never make explicit

Why List[Dog] is not a List[Animal] (invariance of mutable containers), why Callable args are contravariant, when a Protocol (structural) beats an ABC (nominal), and how @overload lets the return type depend on the argument type — these are the load-bearing rules for typing a generic FastAPI dependency/repository layer without Any leaks.

*Source:* PEP 484/544 variance + Protocol semantics

### SQLAlchemy 2.0 async is asyncio-flavored sugar over a sync core, with lazy-loading as the classic async footgun

AsyncSession wraps the sync Session via greenlet; the ORM's unit-of-work, identity map, and autoflush are unchanged, but implicit lazy-load I/O at attribute access raises MissingGreenlet under async — forcing explicit eager loading (selectinload) or awaitable_attrs. This is exactly his kind of leaky-abstraction seam worth understanding all the way down.

*Source:* SQLAlchemy 2.0 async ORM (greenlet bridge)

## Recommendations

- Build the whole curriculum on ONE spine repo: a typed async FastAPI service with a pydantic-v2 boundary, an async SQLAlchemy 2.0 data layer (aiosqlite in tests, asyncpg-ready), an SSE and a WebSocket endpoint, gated by ruff + mypy --strict + pytest + hypothesis. Every module contributes a load-bearing slice, so nothing is learned in isolation.
- Sequence: 5 (data model) and 6 (generators/coroutines) FIRST as the mechanistic foundation, then 3 (asyncio) since await IS the coroutine protocol from module 6, then 4 (typing), then 1->2->9 (pydantic->FastAPI->DB) as the applied stack, with 7 (packaging) and 8 (testing) threaded throughout as the gate.
- Assess by adversarial verification, not recall: for each module have him either (a) reimplement the primitive from scratch (property as a descriptor, an event-loop driver that calls coroutine.send, a minimal DI resolver) or (b) predict-then-measure (slots memory delta, v2-vs-v1 throughput, N+1 query counts under EXPLAIN), matching how he already works.
- For every 'why' skill, require the NAMED rejected alternative in writing (metaclass vs __init_subclass__, Protocol vs ABC, BackgroundTasks vs queue, gather vs TaskGroup, joinedload vs selectinload) — this is his engineering tell and the fastest way to expose shallow understanding.
- Enforce his values ranking in the rubric: a module is 'done' only when the correctness/reliability failure mode is demonstrated with a test (cancelled-task cleanup, MissingGreenlet on lazy load, freezegun import-capture trap), not just described.
- Keep every claim quantified: report p50/p99 deltas, memory bytes/instance, query counts, and rollout iterations — never 'faster'/'less memory'. Add a per-module Limitations note stating what the exercise does NOT prove (e.g. an aiosqlite-green test says nothing about asyncpg concurrency).

## Proposed modules

### Module 1 — Pydantic v2: the pydantic-core boundary, validation pipeline, and v1->v2 migration

**Objectives**

- Understand that a Pydantic model compiles to a CoreSchema executed by the Rust pydantic-core, and what that buys (throughput) and costs (validator semantics, harder introspection)
- Master the three validator modes (before/after/wrap) and where each sits in the validation pipeline, plus the validator-vs-serializer asymmetry
- Control model behavior via model_config (strict, frozen, extra, populate_by_name, arbitrary_types_allowed) and know each flag's failure mode
- Design serialization deliberately: model_dump vs model_dump_json, by_alias, exclude_unset/exclude_none, computed_field, and custom @field_serializer
- Execute a v1->v2 migration mapping the renamed API and the semantic (not just syntactic) changes

**Testable skills**

- Explain what a CoreSchema is and trace what happens from `Model(**data)` down to pydantic-core and back — where does a `@field_validator(mode='before')` run relative to type coercion?
- Given a field that must be validated against another field's value, show why `mode='after'` on a `@model_validator` is correct and why a `@field_validator` cannot see sibling fields
- Code a `@field_validator(mode='wrap')` that catches the inner ValidationError, logs a surfaced reason, and re-raises — and explain when wrap beats before/after
- Explain why `model_dump(mode='json')` differs from `model_dump()` and when passing the plain dict to FastAPI's response serializer double-serializes / loses type fidelity
- Quantify: benchmark v2 vs a v1-equivalent validation on a 20-field nested model at 100k iterations and report the p50 delta — then explain which part of the win is Rust vs which is schema pre-compilation
- Migrate a v1 model using `class Config`, `@validator`, `.dict()`, and `__root__` to v2 and name every semantic change (not rename) you had to make — e.g. root models, `Optional` no longer implying a default

### Module 2 — FastAPI internals: dependency injection, the ASGI request lifecycle, and streaming

**Objectives**

- Trace a request end-to-end through the ASGI scope/receive/send protocol, Starlette routing, dependency resolution, and response serialization
- Understand the DI system as a resolved dependency graph with caching-per-request and yield-based teardown, not magic
- Implement SSE and WebSocket endpoints and reason about their different lifecycles, backpressure, and disconnect handling
- Distinguish BackgroundTasks from a real task queue and know the failure/durability trade-off
- Write middleware at the correct layer (pure ASGI vs BaseHTTPMiddleware) and know why the latter can break streaming/background tasks

**Testable skills**

- Explain how FastAPI builds the dependency graph for a path operation and when a `Depends(...)` result is cached vs re-evaluated within a single request (`use_cache`), and across requests
- Explain the lifecycle of a `yield` dependency: exactly when does the code after `yield` run, and what happens to it if the endpoint raises vs if the client disconnects mid-stream?
- Code an SSE endpoint with `StreamingResponse` (or EventSourceResponse) that detects client disconnect and cleans up, and explain how you detect disconnect via the ASGI `receive` channel
- Contrast `BackgroundTasks` with an external queue for a 'send email after response' task — name the durability guarantee each does and does NOT give, given his Correctness>Reliability ranking
- Explain why `BaseHTTPMiddleware` can interfere with `StreamingResponse` and background tasks and rewrite a piece of middleware as pure ASGI middleware to avoid it
- Write an httpx + ASGITransport test that exercises a dependency-overridden endpoint without binding a real socket, and explain why `app.dependency_overrides` is the correct seam vs monkeypatching

### Module 3 — asyncio & concurrency internals: the event loop, the GIL, and structured concurrency

**Objectives**

- Explain how the event loop schedules ready callbacks and how a coroutine suspends/resumes at await via the selector/callback machinery
- State precisely what the GIL blocks and does not block, and derive asyncio vs threads vs processes for a given workload from that
- Use structured concurrency (TaskGroup) and understand its cancel-siblings-on-error / ExceptionGroup contract vs gather
- Master cancellation and timeouts: how CancelledError is delivered, shielding, and correct finally-block cleanup
- Diagnose and prevent event-loop blocking (a sync call inside a coroutine starving all tasks)

**Testable skills**

- Explain, mechanically, how the loop moves a coroutine from suspended to running: what registers the wakeup (selector readiness, call_soon), and how does `await` translate to yielding control back to the loop?
- State what the GIL blocks: given (a) 8 CPU-bound hash loops, (b) 8 blocking socket reads, (c) 8 numpy matmuls — for each, pick asyncio/threads/processes and justify from GIL-release behavior
- Explain how cancellation is delivered: when you call `task.cancel()`, when and where does `CancelledError` actually get raised, and why is `except CancelledError: pass` a bug?
- Contrast `asyncio.TaskGroup` with `asyncio.gather(return_exceptions=True)` on failure: what happens to sibling tasks, and what exception type reaches the caller?
- Given a coroutine that calls a blocking `requests.get()`, explain what breaks across ALL concurrent tasks and fix it two ways (`run_in_executor` vs an async client) with the trade-off
- Implement a correct timeout around a critical section using `asyncio.timeout()` that guarantees a compensating cleanup runs even on timeout — and explain the role of `shield`

### Module 4 — Typing & mypy strict: generics, Protocols, variance, and overloads

**Objectives**

- Reason about variance: why mutable containers are invariant, why Callable is contravariant in args / covariant in return
- Choose between structural typing (Protocol) and nominal typing (ABC) with a stated rule
- Write generic functions/classes with TypeVar (bounds and constraints) and the 3.12 `class C[T]` syntax
- Use @overload to make return types depend on argument types, and know its runtime-erasure limits
- Eliminate Any leaks in a generic repository/DI layer and pass `mypy --strict` with zero ignores

**Testable skills**

- Explain why `list[Dog]` is not assignable to `list[Animal]` but `Sequence[Dog]` is — tie it to mutability and the definition of covariance/contravariance/invariance
- Explain why `Callable[[Animal], None]` is assignable where `Callable[[Dog], None]` is expected but not vice versa (contravariant parameters)
- Design a generic `Repository[T]` Protocol and explain why a Protocol beats an ABC here for his package-by-feature seam-first style
- Write `@overload` signatures for a function that returns `str` when `raw=True` and a parsed model otherwise, and explain why the implementation signature is invisible to callers
- Given a bounded `TypeVar('T', bound=BaseModel)`, explain what operations mypy will and won't let you do on a value of type T inside the generic function
- Take a snippet that passes at default mypy but leaks `Any` through an untyped decorator and make it pass `--strict`, naming which strict flag caught it

### Module 5 — The CPython data model: descriptors, __slots__, context managers, metaclasses (WHEN they matter)

**Objectives**

- Understand the descriptor protocol as the mechanism behind methods, property, classmethod, and framework field objects
- Know precisely what __slots__ changes (memory layout, no __dict__) and measure the win/cost
- Implement context managers both ways (__enter__/__exit__ and @contextmanager) and reason about exception propagation through __exit__
- Understand attribute lookup order (type.__getattribute__, data vs non-data descriptors, __getattr__ fallback)
- Judge WHEN a metaclass is the right tool vs __init_subclass__ vs a decorator — and usually reject the metaclass

**Testable skills**

- Explain the difference between a data descriptor and a non-data descriptor and how that difference decides whether an instance `__dict__` entry can shadow a class attribute
- Implement `property` from scratch as a descriptor class and explain where in `__getattribute__` it gets invoked
- Measure: put `__slots__` on a class with 5 fields, instantiate 1M, and report the memory delta vs the `__dict__` version — then name what you gave up (dynamic attrs, some multiple inheritance)
- Explain what the return value of `__exit__` controls, and write a context manager that suppresses only a specific exception type while re-raising others
- Given a requirement to auto-register every subclass in a registry, show the `__init_subclass__` solution and explain why it's preferable to a metaclass here (his 'abstractions are earned' principle)
- State the one or two cases where you genuinely need a metaclass (e.g. controlling class creation / namespace like an ORM/enum) and why a class decorator can't do it

### Module 6 — Generators, iterators, and native coroutines: the send/throw/close protocol

**Objectives**

- Understand the iterator protocol and how a generator frame suspends and resumes preserving local state
- Master generator.send()/throw()/close() and see how this same machinery underlies `await`
- Use `yield from` / delegation and understand what it forwards (values, sends, exceptions, return)
- Build memory-bounded streaming pipelines with generators (relevant to SSE and large result sets)
- Distinguish generator-based coroutines from native `async def` coroutines and know why the ecosystem moved

**Testable skills**

- Explain what a generator's suspended frame retains and how `next()` resumes it — where does the instruction pointer live?
- Write a generator that receives values via `.send()`, and explain the priming requirement (why the first `send` must be `None`)
- Explain the mechanical relationship between a native coroutine `await`ing and a generator `yield`ing to a driver — how is an event loop 'just' a driver calling `.send()`?
- Explain what `close()` does to a suspended generator and how a `finally` block inside the generator interacts with it (resource cleanup guarantee)
- Build a streaming transform pipeline (read -> filter -> batch) using generators that never holds the full dataset in memory, and state the peak-memory bound
- Contrast `yield from subgen` with a manual for-loop re-yield: what does `yield from` additionally forward that the manual loop drops?

### Module 7 — Packaging with uv + pyproject: builds, resolution, and reproducibility

**Objectives**

- Understand pyproject.toml as the single source of truth (PEP 517/518/621) and the build-backend contract
- Use uv for fast resolution, locking, and reproducible environments, and know what its lockfile guarantees
- Distinguish application vs library packaging (pinned lock vs flexible ranges) and dependency groups
- Understand editable installs, entry points/scripts, and the src layout rationale
- Reason about the resolver: version constraints, markers, and why a lock is required for reproducibility

**Testable skills**

- Explain the PEP 517 build-backend boundary: what does `[build-system]` declare and what does the frontend (uv/pip) hand to the backend?
- Explain what `uv.lock` pins that a plain `pyproject.toml` dependency range does not, and why that matters for Correctness/Reliability of a deploy
- Contrast dependency strategy for a deployed FastAPI service vs a reusable library — pinned lock vs open ranges — and justify each
- Explain the src-layout vs flat-layout trade-off and why src-layout prevents accidentally importing the un-built package during tests
- Define a console-script entry point in pyproject and explain how it becomes an executable on install
- Explain what an editable install actually does to `sys.path`/site-packages so that source edits take effect without reinstall

### Module 8 — Testing mastery: pytest internals, property-based (hypothesis), respx, freezegun

**Objectives**

- Understand pytest fixture resolution: scopes, finalization order, and dependency injection between fixtures
- Use parametrize and indirect parametrization to drive table-driven tests deterministically
- Adopt property-based testing with hypothesis: invariants over examples, shrinking, and stateful testing
- Mock external HTTP deterministically with respx (httpx) and freeze time with freezegun, injected via fixtures
- Test async code correctly (event-loop-per-test, async fixtures) and keep the suite deterministic under a strict gate

**Testable skills**

- Explain pytest's fixture resolution and teardown order for nested fixtures of mixed scope (function/module/session) — in what order do finalizers run and why?
- Explain what hypothesis shrinking does when a property fails and why the minimal counterexample it reports is more valuable than a fixed example — write a property that catches a bug a hand-picked example would miss
- Use `@pytest.mark.parametrize` with `indirect=True` and explain when indirect parametrization beats plain parametrization (parametrizing the fixture, not the test arg)
- Write a respx-mocked test for a FastAPI dependency that calls an external API, and explain why respx at the transport layer is more faithful than patching your own client function
- Explain the failure mode of freezegun with already-imported `datetime.now` references and how to freeze time correctly for code that captured `now` at import — matching his injected-FixedClock habit
- Set up async test infrastructure (async fixtures + a per-test event loop) and explain why sharing one loop across tests causes cross-test state bleed

### Module 9 — Async data layer: SQLAlchemy 2.0 async + aiosqlite, unit-of-work and the greenlet seam

**Objectives**

- Understand SQLAlchemy 2.0's Core/ORM 2.0 style (select(), Result) and the unit-of-work with identity map and autoflush
- Understand how AsyncSession bridges to the sync core via greenlet and the concrete failure modes that leak through
- Master eager vs lazy loading under async (selectinload/joinedload, awaitable_attrs) and the N+1 / MissingGreenlet traps
- Manage sessions and transactions correctly per-request in FastAPI (session-per-request dependency, commit/rollback boundaries)
- Reason about connection pooling and driver behavior (aiosqlite for tests/dev, asyncpg for prod) and their concurrency limits

**Testable skills**

- Explain the unit-of-work: what does the identity map guarantee, when does autoflush fire, and why can reading trigger a flush of pending writes?
- Explain the greenlet bridge: why does accessing an unloaded relationship attribute raise `MissingGreenlet` under async, and what does that reveal about how 'async' SQLAlchemy actually is?
- Given an endpoint that serializes a parent with its children, prevent the N+1 with `selectinload` and explain how selectin differs from joined loading in query count and row duplication
- Design a FastAPI `AsyncSession` dependency with correct commit-on-success / rollback-on-exception boundaries as a `yield` dependency, and explain where the transaction actually begins and ends
- Explain why aiosqlite is fine for tests but its single-writer/serialized nature makes it a poor concurrency proxy for asyncpg — name what a passing sqlite test does NOT prove about prod
- Contrast expunge/detached-instance behavior and explain why returning a lazily-attributed ORM object past the session close (into the response serializer) is the same class of bug as the disconnect-mid-stream teardown problem

## Risks & gotchas

- This is a curriculum design deliverable, not researched external facts — version-specific details (pydantic-core internals, asyncio.timeout availability 3.11+, SQLAlchemy 2.0 API) reflect knowledge as of the training cutoff and should be re-verified against the exact library versions pinned in his uv.lock before he relies on any specific API name.
- Modules 5 (metaclasses) and 6 (generator send/throw) risk becoming trivia if divorced from the spine repo — they earn their place ONLY as the mechanism under descriptors/framework fields and under await respectively; drop the parts that don't connect.
- The GIL discussion is a live target: free-threaded/no-GIL CPython (PEP 703, 3.13+ experimental) changes the 'what the GIL blocks' answer — flag this explicitly so he learns the current model AND the direction of travel rather than a soon-stale absolute.
- Hypothesis and property-based testing have a real time cost (slow suites, flaky-looking shrinks) — for a Correctness-first engineer this is worth it, but scope it to invariant-bearing code (validators, serializers, parsers) not every test, or the strict gate becomes painful.
- Async SQLAlchemy's leaky greenlet seam is the single highest-value AND highest-frustration topic; budget extra time there. The MissingGreenlet / detached-instance / lazy-load-in-serializer cluster is where most 'it worked in the test' async backends actually break in prod.

## Open questions

- Target depth per module: is the goal that he can reimplement the primitive (event-loop driver, descriptor-based property, minimal DI graph) from scratch, or read-and-reason about CPython/library source? The reimplement bar roughly doubles time-per-module.
- Postgres in scope? The async DB module uses aiosqlite for the harness, but production concurrency/pooling lessons (asyncpg, pool sizing, statement caching) only land against real Postgres — is standing up a Docker postgres part of the curriculum?
- Free-threaded CPython (no-GIL, 3.13+) — teach the classic GIL model only, or also the experimental free-threaded semantics and what they change for the threads-vs-processes decision?
- Should packaging (module 7) also cover building/publishing a wheel to an index and CI, or stop at reproducible local envs + lockfiles for deployed services?
- Does he want a capstone that deliberately induces each failure mode (cancellation leak, N+1, double-serialization, MissingGreenlet) and requires an adversarial test proving the fix — i.e. the same multi-agent adversarial-audit style he already uses on his own repos?

