#!/usr/bin/env python3
"""Crucible Phase 0 pilot harness — deliberately THROWAWAY (docs/09-roadmap.md, Phase 0).

One file on purpose: this is the probe that must prove daily study happens before any engine
gets built (PLAN.md R2). It renders a lesson, grades answers, and appends an attempt log.
Almost none of this survives into the real engine — do not grow it into one.

Grading per strategy (vocabulary from PLAN.md §4 — do not rename):
  deterministic_choice  exact match against the correct option set (mcq / multi_select)
  deterministic_output  run the lesson's program and compare the learner's prediction to the
                        DERIVED output (predict_output), or count DATA RACE reports over N
                        runs (predict_race_verdict — probabilistic per R4, reported as such)
  hidden_tests          compose learner code + the lesson's test_code into a temp Go module
                        and run `go test -race` (plain local per R3: wall timeout + CPU rlimit)
  llm_judge             reference-grounded hosted judge via the OmniRoute gateway; the model
                        rules per rubric criterion and the WEIGHTED SCORE IS COMPUTED HERE, so
                        it cannot invent a total. Unreachable gateway degrades to self-grade
                        against the shown reference at LOW confidence (R1 fail-open).

Press `?` at any prompt for an "explain like I'm 10" hint on whatever is on screen. Hints are
reference-free (they never leak a graded answer) and counted into `hints_used` in the log.

`verify` executes every lesson's gradeable material (references green, buggy code red, predict
outputs derived not hand-typed, race constructions actually tripping) so a broken lesson is
caught before study time — the gradeability-by-construction invariant, pilot-sized.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import resource
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content" / "go"
SCRATCH_DIR = REPO_ROOT / "pilot" / "scratch"
ANSWERS_DIR = REPO_ROOT / "pilot" / "answers"
LOG_PATH = REPO_ROOT / "pilot" / "attempts.jsonl"

# The temp-module preamble every graded Go run gets. `go 1.26` matches the installed toolchain
# (go1.26.4 on this box) and the per-lesson `toolchain: {go: "1.26"}` pin (R10).
GO_MOD = "module crucible/pilot\n\ngo 1.26\n"

# Wall-clock cap per `go` invocation. A cold-cache `-race` compile is the slow case (~2-4 s
# measured on this box); 90 s is an order of magnitude of headroom, not a tuned number.
DEFAULT_TIMEOUT_S = 90.0
# CPU rlimit backstop (R3 asks for timeout + ulimit): an infinite loop burns at most this much
# CPU even if the wall-clock kill misfires.
CPU_LIMIT_S = 120
# predict_race_verdict fallback when a lesson omits `iterations` (R4: N must be >> 2).
DEFAULT_RACE_ITERATIONS = 50
# Per-execution cap for a single compiled race binary run — these programs are tiny; 10 s means
# "hung", not "slow".
RACE_RUN_TIMEOUT_S = 10.0
# How much runner output to show on a failure before truncating — enough for `go test` verdicts
# plus a stack, without flooding the terminal.
MAX_LOG_LINES = 60

# --- hosted judge + hints (OmniRoute) -----------------------------------------------------
# R1 STILL HOLDS. The OmniRoute gateway is local (localhost:20128); the models behind it are
# NOT. Every call below is a network call to a hosted model — never describe this as offline.
# What changed vs. the original Phase 0 note: the fail-open path is no longer the ONLY path.
JUDGE_BASE_URL = os.environ.get("CRUCIBLE_LLM_BASE", "http://localhost:20128/v1")
# Judge: quality over latency — it reads a rubric and a reference and must not be sloppy.
JUDGE_MODEL = os.environ.get("CRUCIBLE_JUDGE_MODEL", "antigravity/claude-sonnet-4-6")
# Hints: latency over quality — a hint you wait 8 s for is a hint you stop asking for.
HINT_MODEL = os.environ.get("CRUCIBLE_HINT_MODEL", "auto/best-fast")
# One sample, not R5's cap of 3. At n=1 attempts, paying 3x latency to measure a spread that
# nothing yet acts on buys nothing; Phase 4's median+spread combiner is where 3 earns its cost.
JUDGE_SAMPLES = 1
# A judge round-trip measured ~3 s on this box; 90 s means "the gateway is wedged", not "slow".
LLM_TIMEOUT_S = 90.0

STRATEGIES = ("deterministic_choice", "deterministic_output", "hidden_tests", "llm_judge")
# Bloom levels allowed on Track A objectives (docs/01-pedagogy.md bans Remember/Understand).
TRACK_A_BLOOM = ("analyze", "evaluate", "create")


# --------------------------------------------------------------------------- terminal styling
# 256-color approximations of the Dracula terminal tokens (docs/theme/dracula-terminal.css).
class C:
    enabled = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

    @classmethod
    def _c(cls, code: str, text: str) -> str:
        return f"\x1b[{code}m{text}\x1b[0m" if cls.enabled else text

    @classmethod
    def purple(cls, t: str) -> str:
        return cls._c("38;5;141", t)

    @classmethod
    def pink(cls, t: str) -> str:
        return cls._c("38;5;212", t)

    @classmethod
    def green(cls, t: str) -> str:
        return cls._c("38;5;84", t)

    @classmethod
    def orange(cls, t: str) -> str:
        return cls._c("38;5;215", t)

    @classmethod
    def red(cls, t: str) -> str:
        return cls._c("38;5;203", t)

    @classmethod
    def cyan(cls, t: str) -> str:
        return cls._c("38;5;117", t)

    @classmethod
    def dim(cls, t: str) -> str:
        return cls._c("38;5;103", t)

    @classmethod
    def bold(cls, t: str) -> str:
        return cls._c("1", t)


def hr(char: str = "─", width: int = 72) -> str:
    return C.dim(char * width)


# ------------------------------------------------------------------------------- llm client
def _load_env_file() -> None:
    """Read repo-root `.env` into os.environ. Five lines instead of a python-dotenv dependency.

    Existing environment wins, so `CRUCIBLE_JUDGE_MODEL=... make lesson ...` overrides the file.
    """
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def llm(prompt: str, *, model: str, max_tokens: int = 1200, system: str = "") -> str | None:
    """One hosted-model call. Returns None on ANY failure — the caller degrades, never crashes.

    Graceful degradation is the point (PLAN.md invariant 5): a wedged gateway, a missing key, or
    an unparseable body must cost you a hint or a confidence level, never the study session.
    """
    key = os.environ.get("OMNIROUTE_API_KEY", "").strip()
    if not key:
        return None
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = json.dumps({
        "model": model,
        "messages": messages,
        # The gateway streams by default; we want one parseable body, not an SSE transcript.
        "stream": False,
        "temperature": 0,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        f"{JUDGE_BASE_URL}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=LLM_TIMEOUT_S) as resp:
            payload = json.loads(resp.read().decode())
        content = payload["choices"][0]["message"]["content"]
        return str(content).strip() or None
    except (urllib.error.URLError, OSError, KeyError, IndexError, ValueError, TypeError):
        return None


def extract_json(text: str) -> dict[str, Any] | None:
    """Pull one JSON object out of a model reply that may be fenced or prefaced with prose."""
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    candidate = fenced.group(1) if fenced else text
    start, end = candidate.find("{"), candidate.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


# --------------------------------------------------------------------------------- content IO
Lesson = dict[str, Any]


def load_lessons() -> dict[str, Lesson]:
    lessons: dict[str, Lesson] = {}
    for path in sorted(CONTENT_DIR.glob("*.yaml")):
        with path.open() as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict) or "id" not in data:
            print(C.red(f"unreadable lesson (no id): {path}"))
            continue
        data["_path"] = str(path)
        lessons[str(data["id"])] = data
    return lessons


def lesson_or_die(lessons: dict[str, Lesson], lesson_id: str) -> Lesson:
    if lesson_id not in lessons:
        known = ", ".join(sorted(lessons)) or "(none)"
        raise SystemExit(f"unknown lesson '{lesson_id}'. Known: {known}")
    return lessons[lesson_id]


# ---------------------------------------------------------------------------------- go runner
@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def combined(self) -> str:
        return self.stdout + self.stderr


def _limit_cpu() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_LIMIT_S, CPU_LIMIT_S))


def run_cmd(args: list[str], cwd: Path, timeout_s: float = DEFAULT_TIMEOUT_S) -> RunResult:
    # GOPROXY=off makes any accidental non-stdlib import fail loudly instead of fetching —
    # pilot content is stdlib-only by convention, and grading must work offline.
    env = dict(os.environ, GOPROXY="off")
    try:
        p = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
            preexec_fn=_limit_cpu,
        )
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return RunResult(124, out, err + f"\n[killed: wall-clock timeout {timeout_s:.0f}s]", True)
    return RunResult(p.returncode, p.stdout, p.stderr)


def new_module(files: dict[str, str]) -> Path:
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    mod = Path(tempfile.mkdtemp(prefix="run-", dir=SCRATCH_DIR))
    (mod / "go.mod").write_text(GO_MOD)
    for name, content in files.items():
        (mod / name).write_text(content if content.endswith("\n") else content + "\n")
    return mod


def go_test(learner_code: str, test_code: str, timeout_ms: int) -> RunResult:
    mod = new_module({"answer.go": learner_code, "lesson_test.go": test_code})
    return run_cmd(
        ["go", "test", "-race", "-count=1", f"-timeout={timeout_ms}ms", "."], cwd=mod
    )


def go_run_program(program: str) -> RunResult:
    mod = new_module({"main.go": program})
    return run_cmd(["go", "run", "."], cwd=mod)


def race_observations(program: str, iterations: int) -> tuple[int, int, str]:
    """Build once with -race, run N times; return (races_observed, runs, sample_report)."""
    mod = new_module({"main.go": program})
    build = run_cmd(["go", "build", "-race", "-o", "prog", "."], cwd=mod)
    if build.returncode != 0:
        raise RuntimeError(f"race program does not build:\n{build.combined}")
    observed = 0
    sample = ""
    for _ in range(iterations):
        r = run_cmd([str(mod / "prog")], cwd=mod, timeout_s=RACE_RUN_TIMEOUT_S)
        if "WARNING: DATA RACE" in r.combined:
            observed += 1
            if not sample:
                sample = r.combined
    return observed, iterations, sample


def tail(text: str, lines: int = MAX_LOG_LINES) -> str:
    parts = text.strip().splitlines()
    if len(parts) <= lines:
        return text.strip()
    return "\n".join([f"[... {len(parts) - lines} lines omitted ...]"] + parts[-lines:])


# ------------------------------------------------------------------------------ envelope + log
def envelope(
    score: float,
    max_score: float,
    verdict: str,
    *,
    grader_id: str,
    confidence: str = "high",
    per_criterion: list[dict[str, Any]] | None = None,
    evidence: str = "",
    logs: str = "",
) -> dict[str, Any]:
    return {
        "score": round(score, 3),
        "max": max_score,
        "verdict": verdict,
        "per_criterion": per_criterion or [],
        "evidence": evidence,
        "confidence": confidence,
        "grader_id": grader_id,
        "logs": logs,
    }


def print_envelope(env: dict[str, Any]) -> None:
    color = C.green if env["verdict"] == "PASS" else C.red
    print(
        f"\n{hr()}\n"
        + color(C.bold(f"  {env['verdict']}"))
        + C.dim(
            f"  score={env['score']}/{env['max']}"
            f"  confidence={env['confidence']}  grader={env['grader_id']}"
        )
    )
    if env["evidence"]:
        print(C.dim("  " + env["evidence"]))
    print(hr())


def log_attempt(lesson: Lesson, assessment: dict[str, Any], env: dict[str, Any], ms: int) -> None:
    record = {
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "lesson": lesson["id"],
        "content_rev": lesson.get("content_rev"),
        "assessment": assessment["id"],
        "type": assessment.get("type"),
        "strategy": assessment["grading"]["strategy"],
        "verdict": env["verdict"],
        "score": env["score"],
        "max": env["max"],
        "confidence": env["confidence"],
        "grader_id": env["grader_id"],
        "hints_used": HINTS.used,
        "latency_ms": ms,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(record) + "\n")


# ------------------------------------------------------------------------------- input helpers
@dataclass
class HintContext:
    """What an ELI10 hint is *about*, plus how many were spent on the current item.

    ponytail: one module-level instance instead of threading context through all eight `ask()`
    call sites. This file is the throwaway probe (PLAN.md R2); when the loop moves into
    `src/crucible/` the context gets passed explicitly and this global goes away.
    """

    lesson_title: str = ""
    topic: str = ""      # the teach block or prompt the learner is staring at
    used: int = 0        # hints spent on the CURRENT assessment; feeds `hints_used` in the log


HINTS = HintContext()

# The hint keystroke. `?` alone on a line — short enough to be reflex when you are stuck, and
# it can never collide with a real answer (options are letters/numbers, predictions are output).
HINT_KEY = "?"
# Quit keystroke. `:q` not `q` — a bare letter is a plausible MCQ option or predicted output,
# and a quit key that can be typed by accident as an answer is worse than no quit key.
QUIT_KEY = ":q"


def eli10() -> None:
    """Explain the thing on screen as if to a smart 10-year-old, then hand control back.

    Reference-free ON PURPOSE: a hint must never leak the graded answer. The prompt forbids it
    and the topic text is the teach material, not the rubric or the reference.
    """
    if not HINTS.topic.strip():
        print(C.dim("  (nothing to explain here)"))
        return
    print(C.dim("  thinking..."))
    reply = llm(
        f"Lesson: {HINTS.lesson_title}\n\nMaterial the learner is stuck on:\n---\n"
        f"{HINTS.topic}\n---\n\nExplain the IDEA above like I am 10 years old.",
        model=HINT_MODEL,
        max_tokens=600,
        system=(
            "You explain Go concurrency to a sharp 10-year-old: everyday analogies, short "
            "sentences, no jargon without unpacking it, at most 150 words. The reader is a "
            "strong programmer who is new to Go, so never condescend about programming itself "
            "— only make the CONCEPT concrete. CRITICAL: if the material contains a question, "
            "quiz, or exercise, explain the underlying idea but NEVER reveal or hint at which "
            "answer is correct."
        ),
    )
    if reply is None:
        print(C.orange("  hint unavailable (judge/gateway unreachable) — continuing without it"))
        return
    HINTS.used += 1
    print()
    render_body(reply, indent="  " + C.dim("│ "))
    print()


class SessionQuit(Exception):
    """Raised to end a study session cleanly. Graded items are already durable in the log."""


def ask(prompt: str) -> str:
    """Read one line, intercepting the hint and quit keys so neither lands in a graded answer."""
    while True:
        try:
            raw = input(C.pink(prompt))
        except (EOFError, KeyboardInterrupt):
            print()
            raise SessionQuit from None
        if raw.strip() == HINT_KEY:
            eli10()
            continue
        if raw.strip() == QUIT_KEY:
            raise SessionQuit
        return raw


def ask_multiline(prompt: str) -> str:
    print(C.pink(prompt) + C.dim("  (finish with a single '.' on its own line)"))
    lines: list[str] = []
    while True:
        line = ask("")
        if line.strip() == ".":
            break
        lines.append(line)
    return "\n".join(lines)


def open_editor(path: Path) -> None:
    editor = os.environ.get("EDITOR", "").strip()
    if editor:
        subprocess.run([*shlex.split(editor), str(path)], check=False)
    else:
        ask(f"$EDITOR unset — edit {path} in another window, then press Enter here... ")


def pause(msg: str = "Enter to continue") -> None:
    ask(C.dim(f"  ⏎ {msg}  ({HINT_KEY} = explain like I'm 10, {QUIT_KEY} = end session) "))


# ---------------------------------------------------------------------------------- rendering
def render_body(body: str, indent: str = "  ") -> None:
    in_code = False
    for line in body.rstrip("\n").splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            print(indent + C.dim(line))
        elif in_code:
            print(indent + C.cyan(line))
        elif line.lstrip().startswith("> [!KEY]"):
            print(indent + C.purple(C.bold(line.lstrip()[2:].strip())))
        else:
            print(indent + line)


def show_code(code: str, indent: str = "  ") -> None:
    for line in code.rstrip("\n").splitlines():
        print(indent + C.cyan(line))


# ------------------------------------------------------------------------------------ graders
def grade_choice(assessment: dict[str, Any]) -> dict[str, Any]:
    g = assessment["grading"]
    options: list[dict[str, Any]] = list(g["options"])
    multi = assessment.get("type") == "multi_select"
    order = list(range(len(options)))
    if not os.environ.get("PILOT_NO_SHUFFLE"):  # scripted-smoke-test hook; humans get shuffles
        random.shuffle(order)
    for shown, idx in enumerate(order, 1):
        print(f"  {C.orange(str(shown) + ')')} {options[idx]['text']}")
    hint = "numbers, comma-separated (e.g. 1,3)" if multi else "one number"
    raw = ask(f"\n  your pick ({hint}): ").strip()
    try:
        picks = {order[int(tok) - 1] for tok in raw.replace(",", " ").split()}
    except (ValueError, IndexError):
        picks = set()
    correct = {i for i, o in enumerate(options) if o.get("correct")}
    if multi:
        inter, union = len(picks & correct), len(picks | correct)
        score = (inter / union) if g.get("partial_credit") == "jaccard" and union else float(picks == correct)
    else:
        score = float(picks == correct)
    print()
    for i, o in enumerate(options):
        mark = C.green("✔") if o.get("correct") else C.red("✘")
        picked = C.pink(" ← you") if i in picks else ""
        print(f"  {mark} {o['text']}{picked}")
        print(C.dim(f"      why: {o['why']}"))
    verdict = "PASS" if score >= 0.999 else "FAIL"
    return envelope(score, 1.0, verdict, grader_id="deterministic_choice",
                    evidence=f"picked {sorted(picks)}; correct {sorted(correct)}")


def _match(mode: str, expected: str, learner: str, derived: str) -> bool:
    if mode == "exact":
        return learner == derived
    if mode == "contains":
        return expected.strip().lower() in learner.strip().lower()
    if mode == "regex":
        return re.search(expected, learner) is not None
    # trimmed (default): per-line trailing-whitespace-insensitive comparison
    def norm(s: str) -> str:
        return "\n".join(ln.rstrip() for ln in s.strip().splitlines())

    return norm(learner) == norm(derived)


def grade_predict_output(assessment: dict[str, Any]) -> dict[str, Any]:
    g = assessment["grading"]
    print(C.dim("\n  --- program ---"))
    show_code(g["program"])
    learner = ask_multiline("\n  predicted output:")
    result = go_run_program(g["program"])
    derived = result.combined if g.get("stream") == "combined" else result.stdout
    mode = g.get("match", "trimmed")
    ok = _match(mode, str(g.get("expected_output", "")), learner, derived)
    print(C.dim("\n  --- actual output (derived by running it) ---"))
    show_code(derived if derived.strip() else "(no output)")
    verdict = "PASS" if ok else "FAIL"
    return envelope(float(ok), 1.0, verdict, grader_id="deterministic_output",
                    evidence=f"match={mode}", logs=tail(derived))


def grade_race_verdict(assessment: dict[str, Any]) -> dict[str, Any]:
    g = assessment["grading"]
    iterations = int(g.get("iterations", DEFAULT_RACE_ITERATIONS))
    print(C.dim("\n  --- program ---"))
    show_code(g["program"])
    raw = ask("\n  will -race report a DATA RACE? [race/clean]: ").strip().lower()
    prediction = "race" if raw.startswith("r") else "clean"
    print(C.dim(f"  running {iterations} iterations under -race..."))
    observed, runs, sample = race_observations(g["program"], iterations)
    truth = "race" if observed > 0 else "clean"
    ok = prediction == truth
    print(f"\n  observed: {C.bold(f'{observed}/{runs}')} runs reported DATA RACE → {C.bold(truth.upper())}")
    if truth == "clean":
        print(C.orange("  R4 caveat: 0 observed races does NOT prove race-freedom — "
                       "-race only reports interleavings it actually sees."))
    if sample and not ok:
        print(C.dim("\n  first race report:"))
        show_code(tail(sample, 25))
    verdict = "PASS" if ok else "FAIL"
    return envelope(float(ok), 1.0, verdict, grader_id="deterministic_output",
                    confidence="probabilistic",
                    evidence=f"predicted {prediction}; observed {observed}/{runs}")


def grade_hidden_tests(assessment: dict[str, Any], review: bool) -> dict[str, Any]:
    g = assessment["grading"]
    aid = assessment["id"]
    ANSWERS_DIR.mkdir(parents=True, exist_ok=True)
    answer_path = ANSWERS_DIR / f"{aid}.go"
    if not answer_path.exists():
        seed = g.get("buggy") if assessment.get("type") == "debug_this" else g.get("starter", "")
        answer_path.write_text(seed or "package crucible\n")
    tests_meta = g.get("tests", [])
    visible = [t for t in tests_meta if t.get("visible")]
    hidden_n = len(tests_meta) - len(visible)
    if visible:
        print(C.dim("\n  checked (visible):"))
        for t in visible:
            print(C.dim(f"    - {t['name']}: {t.get('golden', '')}"))
    if hidden_n:
        print(C.dim(f"    ...plus {hidden_n} hidden check(s)"))
    print(f"\n  your answer file: {C.cyan(str(answer_path))}")
    timeout_ms = int(g.get("timeout_ms", 30000))
    attempts = 0
    last: RunResult | None = None
    while True:
        open_editor(answer_path)
        attempts += 1
        print(C.dim("  go test -race ..."))
        last = go_test(answer_path.read_text(), g["test_code"], timeout_ms)
        if last.returncode == 0:
            print(C.green("  all tests green"))
            return envelope(1.0, 1.0, "PASS", grader_id="hidden_tests",
                            evidence=f"attempts={attempts}", logs=tail(last.combined))
        print(C.red("\n  tests failed:"))
        show_code(tail(last.combined))
        nxt = ask("\n  [e]dit & retry / [f]ail item: ").strip().lower()
        if nxt.startswith("f"):
            break
    if review or ask("  show reference solution? [y/n]: ").strip().lower().startswith("y"):
        print(C.dim("\n  --- reference solution ---"))
        show_code(g.get("reference_solution", "(none)"))
    return envelope(0.0, 1.0, "FAIL", grader_id="hidden_tests",
                    evidence=f"attempts={attempts}", logs=tail(last.combined if last else ""))


def score_from_criteria(
    criteria: list[dict[str, Any]], values: dict[str, float]
) -> tuple[float, list[dict[str, Any]]]:
    """Fold per-criterion met/half/unmet into a weighted score.

    The MODEL never returns a score — it only judges each criterion. The arithmetic happens
    here, in Python, so a judge cannot invent a number that its own per-criterion verdicts do
    not support. Same structural move as the résumé guard: make the bad outcome impossible by
    construction rather than by asking the model nicely.
    """
    score = 0.0
    rows: list[dict[str, Any]] = []
    for crit in criteria:
        weight = float(crit["weight"])
        value = float(values.get(str(crit["id"]), 0.0))
        value = min(1.0, max(0.0, value))
        score += weight * value
        rows.append({"id": crit["id"], "weight": weight, "value": value})
    return score, rows


def collect_essay(assessment: dict[str, Any]) -> tuple[str, Path]:
    """Open the answer file in $EDITOR and read it back. Persists so you can iterate across days."""
    aid = assessment["id"]
    ANSWERS_DIR.mkdir(parents=True, exist_ok=True)
    answer_path = ANSWERS_DIR / f"{aid}.md"
    if not answer_path.exists():
        answer_path.write_text("")
    print(f"\n  write your answer in: {C.cyan(str(answer_path))}")
    open_editor(answer_path)
    return answer_path.read_text().strip(), answer_path


def anti_reward_hacking(assessment: dict[str, Any], answer: str) -> tuple[bool, str]:
    """Deterministic guards that run OUTSIDE the model and can only ever LOWER the outcome.

    Deterministic-wins, applied to the judge's own input: a word-count floor and banned phrases
    are decidable by a machine, so no model opinion is consulted about them.
    """
    g = assessment["grading"]
    rubric = g["rubric"]
    # canonical schema nests anti_reward_hacking inside rubric; tolerate grading-level too
    anti = rubric.get("anti_reward_hacking", g.get("anti_reward_hacking", {}))
    capped = False
    notes: list[str] = []
    min_words = int(anti.get("min_words", 0))
    words = len(answer.split())
    if min_words and words < min_words:
        print(C.orange(f"  under min_words ({words} < {min_words}) — item cannot PASS"))
        notes.append(f"under min_words {words}<{min_words}")
        capped = True
    for phrase in anti.get("penalize_if_contains", []):
        if phrase.lower() in answer.lower():
            print(C.orange(f"  contains penalized phrase '{phrase}' — item cannot PASS"))
            notes.append(f"penalized phrase '{phrase}'")
            capped = True
    return capped, "; ".join(notes)


def judge_essay(
    assessment: dict[str, Any], answer: str
) -> tuple[float, list[dict[str, Any]], str] | None:
    """Ask the hosted judge to rule on each rubric criterion. None => caller must degrade.

    Reference-grounded (R7): the judge never runs without the locked reference answer in its
    prompt, so it grades against a fixed standard rather than its own taste.
    """
    g = assessment["grading"]
    rubric = g["rubric"]
    criteria: list[dict[str, Any]] = list(rubric["criteria"])
    reference = str(assessment.get("reference_answer", g.get("reference_answer", ""))).strip()
    if not reference:
        return None
    criteria_block = "\n".join(
        f'- id "{c["id"]}" (weight {c["weight"]}): {c["text"]}' for c in criteria
    )
    prompt = (
        f"QUESTION\n{assessment.get('prompt', '')}\n\n"
        f"REFERENCE ANSWER (the locked standard — grade against THIS, not your own taste)\n"
        f"{reference}\n\n"
        f"RUBRIC CRITERIA\n{criteria_block}\n\n"
        f"LEARNER ANSWER\n{answer}\n\n"
        'Return ONLY JSON: {"criteria":[{"id":"<id>","value":1|0.5|0,"why":"<one sentence>"}],'
        '"summary":"<one sentence>"}'
    )
    system = (
        "You grade one short design-defense answer for a single advanced engineer studying Go. "
        "Per criterion: 1 = fully met, 0.5 = partially met, 0 = not met. The house bar is "
        "strict — an answer that names no rejected alternative, no concrete failure mode, and "
        "no number does NOT meet a criterion asking for one. Reward correct reasoning that "
        "differs in wording from the reference; punish fluent restatement with no mechanism. "
        "Do not output a total score — only per-criterion values. Output JSON and nothing else."
    )
    for _ in range(JUDGE_SAMPLES):
        reply = llm(prompt, model=JUDGE_MODEL, max_tokens=1500, system=system)
        if reply is None:
            continue
        parsed = extract_json(reply)
        if not parsed or not isinstance(parsed.get("criteria"), list):
            continue
        values: dict[str, float] = {}
        whys: dict[str, str] = {}
        for row in parsed["criteria"]:
            if isinstance(row, dict) and "id" in row:
                try:
                    values[str(row["id"])] = float(row.get("value", 0))
                except (TypeError, ValueError):
                    values[str(row["id"])] = 0.0
                whys[str(row["id"])] = str(row.get("why", ""))
        if not values:
            continue
        score, rows = score_from_criteria(criteria, values)
        for row in rows:
            row["why"] = whys.get(str(row["id"]), "")
        return score, rows, str(parsed.get("summary", ""))
    return None


def self_grade(
    assessment: dict[str, Any]
) -> tuple[float, list[dict[str, Any]]]:
    """The R1 fail-open path: grade yourself against the shown reference, honestly."""
    g = assessment["grading"]
    rubric = g["rubric"]
    print(C.dim("\n  --- reference answer (grade yourself against it, honestly) ---"))
    render_body(str(assessment.get("reference_answer", g.get("reference_answer", "(none)"))))
    print(C.dim("\n  --- rubric ---"))
    values: dict[str, float] = {}
    for crit in rubric["criteria"]:
        raw = ask(f"  [{crit['weight']:.0%}] {crit['text']}\n      met? [y/n/h]: ").strip().lower()
        values[str(crit["id"])] = 1.0 if raw.startswith("y") else 0.5 if raw.startswith("h") else 0.0
    return score_from_criteria(list(rubric["criteria"]), values)


def grade_self_judge(assessment: dict[str, Any]) -> dict[str, Any]:
    """llm_judge strategy: hosted judge first, self-grade when the gateway is unreachable.

    Name kept (PLAN.md §4 forbids silent renames); what changed is that the hosted judge is now
    the primary path and self-grading is the documented degradation, which is the shape R1
    always specified.
    """
    answer, _path = collect_essay(assessment)
    capped, capped_note = anti_reward_hacking(assessment, answer)
    rubric = assessment["grading"]["rubric"]
    threshold = float(rubric.get("pass_threshold", 0.6))
    words = len(answer.split())

    judged = judge_essay(assessment, answer) if answer else None
    if judged is not None:
        score, per_criterion, summary = judged
        grader_id, confidence = f"omniroute:{JUDGE_MODEL}", "high"
        print(C.dim("\n  --- judge ---"))
        for row in per_criterion:
            mark = C.green("met") if row["value"] == 1.0 else (
                C.orange("half") if row["value"] == 0.5 else C.red("miss"))
            print(f"  [{row['weight']:.0%}] {mark}  {row.get('why', '')}")
        if summary:
            print(C.dim(f"\n  {summary}"))
        print(C.dim("\n  --- reference answer (read it either way) ---"))
        render_body(str(assessment.get("reference_answer",
                                       assessment["grading"].get("reference_answer", "(none)"))))
    else:
        if answer:
            print(C.orange("  judge unreachable — degrading to self-grade (confidence LOW)"))
        score, per_criterion = self_grade(assessment)
        grader_id, confidence = "self_grade_v0", "LOW"

    passed = (score >= threshold) and not capped
    return envelope(score, 1.0, "PASS" if passed else "FAIL", grader_id=grader_id,
                    confidence=confidence, per_criterion=per_criterion,
                    evidence=f"threshold={threshold}; words={words}"
                             + (f"; capped: {capped_note}" if capped else ""))


def run_assessment(lesson: Lesson, assessment: dict[str, Any], review: bool) -> None:
    strategy = assessment["grading"]["strategy"]
    print(f"\n{hr('═')}")
    print(C.purple(C.bold(f"  {assessment['id']}")) + C.dim(
        f"  [{assessment.get('type')} · {strategy}"
        f"{' · ' + assessment['difficulty'] if 'difficulty' in assessment else ''}]"))
    print(hr("═"))
    print()
    render_body(assessment.get("prompt", ""))
    HINTS.topic = str(assessment.get("prompt", ""))
    HINTS.used = 0
    t0 = time.monotonic()
    if strategy == "deterministic_choice":
        env = grade_choice(assessment)
    elif strategy == "deterministic_output":
        if assessment.get("type") == "predict_race_verdict":
            env = grade_race_verdict(assessment)
        else:
            env = grade_predict_output(assessment)
    elif strategy == "hidden_tests":
        env = grade_hidden_tests(assessment, review)
    elif strategy == "llm_judge":
        env = grade_self_judge(assessment)
    else:
        raise SystemExit(f"unknown grading strategy '{strategy}' in {assessment['id']}")
    ms = int((time.monotonic() - t0) * 1000)
    print_envelope(env)
    log_attempt(lesson, assessment, env, ms)


# ------------------------------------------------------------------------------ session runner
def run_lesson(
    lessons: dict[str, Lesson],
    lesson_id: str,
    review: bool,
    only: str | None,
    *,
    redo: bool = False,
    teach: bool = False,
) -> None:
    """Run a lesson, resuming past whatever already passed.

    A session you walked away from is the normal case, not the error case: every graded item is
    already durable in the append-only log the instant it is graded, so resuming is a matter of
    *reading* that log rather than storing extra state. Passed items are skipped and the teach
    section is skipped on re-entry (`--teach` re-reads it, `--redo` runs the whole thing again).
    """
    lesson = lesson_or_die(lessons, lesson_id)
    assessments = list(lesson.get("assessments", []))
    done = latest_verdicts().get(lesson_id, {}) if not redo else {}
    passed_ids = {aid for aid, verdict in done.items() if verdict == "PASS"}
    resuming = bool(done) and not only

    print(f"\n{hr('━')}")
    print(C.purple(C.bold(f"  {lesson['title']}")))
    print(C.dim(f"  {lesson.get('week', '')} · {lesson['id']} · rev {lesson.get('content_rev')}"
                f" · {'review (test-first)' if review else 'teach → test'}"))
    print(hr("━"))
    HINTS.lesson_title = str(lesson.get("title", lesson["id"]))

    # Teach on a first visit; on a resume you have already read it — say so instead of replaying.
    show_teach = not review and not only and (teach or not resuming)
    if resuming:
        n_pass = len(passed_ids & {a["id"] for a in assessments})
        print(C.orange(f"\n  resuming — {n_pass}/{len(assessments)} already passed, skipping those"
                       + ("" if show_teach else "; teach skipped (--teach to re-read)")))
    if show_teach:
        print()
        render_body(str(lesson.get("summary", "")))
        HINTS.topic = str(lesson.get("summary", ""))
        for block in lesson.get("teach", []):
            print(f"\n{C.pink(C.bold('  § ' + block['heading']))}\n")
            render_body(block["body"])
            HINTS.topic = f"{block['heading']}\n\n{block['body']}"
            pause()
        for ex in lesson.get("worked_examples", []):
            print(f"\n{C.orange(C.bold('  worked example'))} {C.dim(ex['id'])}\n")
            render_body(ex["prompt"])
            HINTS.topic = str(ex["prompt"])
            pause("think first, then Enter to reveal the solution")
            render_body(ex["solution"])
            HINTS.topic = f"{ex['prompt']}\n\n{ex['solution']}"
            pause()

    if only:
        assessments = [a for a in assessments if a["id"] == only]
        if not assessments:
            raise SystemExit(f"no assessment '{only}' in {lesson_id}")
    todo = [a for a in assessments if a["id"] not in passed_ids]
    if not todo:
        print(C.green("\n  every assessment in this lesson already passed "
                      "— `make redo ID=...` to run it again.\n"))
        return

    for i, a in enumerate(todo):
        # QUIT_KEY unwinds to here so a walked-away session ends with its progress summarised
        # rather than with a bare traceback. Items already graded stay graded.
        try:
            run_assessment(lesson, a, review)
        except SessionQuit:
            remaining = len(todo) - i
            print(C.orange(f"\n  session ended — {remaining} item(s) left in this lesson."))
            print(C.dim(f"  resume with: make lesson ID={lesson_id}\n"))
            return

    print(f"\n{C.purple(C.bold('  session done.'))}")
    if lesson.get("limitations"):
        print(C.orange("\n  Limitations (what a green run does NOT prove):"))
        render_body(str(lesson["limitations"]).strip(), indent="    ")


# ------------------------------------------------------------------------------------- verify
@dataclass
class Findings:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def verify_lesson(lesson: Lesson, all_ids: set[str], quick: bool = False) -> Findings:
    f = Findings()
    lid = lesson["id"]
    path = Path(lesson.get("_path", ""))
    if path.stem != lid:
        f.err(f"id '{lid}' != filename '{path.stem}'")
    if lesson.get("schema_version") != 1:
        f.err(f"unknown schema_version {lesson.get('schema_version')} (gate refuses to guess)")
    tag = str(lesson.get("tag", ""))
    if not lid.startswith(tag + "-"):
        f.err(f"id must start with tag prefix '{tag}-'")
    if not isinstance(lesson.get("content_rev"), int):
        f.err("content_rev must be an int")
    for req in ("title", "track", "summary", "learning_objectives", "teach", "limitations"):
        if not lesson.get(req):
            f.err(f"missing required field '{req}'")
    for pre in lesson.get("prerequisites", []):
        if pre not in all_ids:
            f.err(f"prerequisite '{pre}' does not exist")

    objectives = {o["id"]: o for o in lesson.get("learning_objectives", [])}
    for oid, obj in objectives.items():
        if not oid.startswith(tag):
            f.err(f"objective id '{oid}' missing tag prefix")
        if obj.get("bloom") not in TRACK_A_BLOOM:
            f.warn(f"objective '{oid}' bloom '{obj.get('bloom')}' below Analyze (Track-A ban)")

    taught: set[str] = set()
    for block in lesson.get("teach", []) + lesson.get("worked_examples", []):
        taught.update(block.get("covers", []))
    assessments = lesson.get("assessments", [])
    if not assessments:
        f.err("gradeable-or-reject: lesson has zero assessments")
    assessed: set[str] = set()
    for a in assessments:
        assessed.update(a.get("covers", []))

    # Coverage-closure (docs/05 §4 invariant 2), both directions, plus teach coverage.
    for oid in objectives:
        if oid not in assessed:
            f.err(f"coverage-closure: objective '{oid}' is never assessed")
        if oid not in taught:
            f.err(f"coverage-closure: objective '{oid}' is never taught")
    for cid in assessed | taught:
        if cid not in objectives:
            f.err(f"coverage-closure: covers references unknown objective '{cid}'")

    seen_aids: set[str] = set()
    for a in assessments:
        aid = a.get("id", "?")
        if aid in seen_aids:
            f.err(f"duplicate assessment id '{aid}'")
        seen_aids.add(aid)
        g = a.get("grading", {})
        strategy = g.get("strategy")
        if strategy not in STRATEGIES:
            f.err(f"{aid}: unknown strategy '{strategy}'")
            continue
        if not a.get("prompt"):
            f.err(f"{aid}: missing prompt")

        if strategy == "deterministic_choice":
            opts = g.get("options", [])
            ncorrect = sum(1 for o in opts if o.get("correct"))
            if a.get("type") == "multi_select":
                if ncorrect < 1 or ncorrect == len(opts):
                    f.err(f"{aid}: multi_select needs >=1 correct and >=1 incorrect")
            elif ncorrect != 1:
                f.err(f"{aid}: mcq needs exactly one correct option, has {ncorrect}")
            if len(opts) < 3:
                f.warn(f"{aid}: only {len(opts)} options — weak discrimination")
            for o in opts:
                if not str(o.get("why", "")).strip():
                    f.err(f"{aid}: option '{o.get('text')}' missing its why")
            ref = a.get("reference_answer")
            corrects = sorted(str(o["text"]) for o in opts if o.get("correct"))
            if a.get("type") != "multi_select" and ref and [ref] != corrects:
                f.err(f"{aid}: reference_answer '{ref}' != correct option {corrects}")

        elif strategy == "deterministic_output":
            program = g.get("program", "")
            if "package main" not in program:
                f.err(f"{aid}: program must be a complete 'package main' file")
                continue
            if a.get("type") == "predict_race_verdict":
                expected = g.get("expected_verdict")
                if expected not in ("race", "clean"):
                    f.err(f"{aid}: predict_race_verdict needs expected_verdict: race|clean")
                elif not quick:
                    n = int(g.get("iterations", DEFAULT_RACE_ITERATIONS))
                    if n < 20:
                        f.warn(f"{aid}: iterations={n} is low for R4 (want N>>2, default 50)")
                    try:
                        observed, runs, _ = race_observations(program, n)
                    except RuntimeError as exc:
                        f.err(f"{aid}: {exc}")
                        continue
                    if expected == "race" and observed == 0:
                        f.err(f"{aid}: expected race never tripped in {runs} runs — "
                              "not a reliably-tripping construction (R4)")
                    if expected == "clean" and observed > 0:
                        f.err(f"{aid}: expected clean but {observed}/{runs} runs raced")
                    if expected == "race" and 0 < observed < runs // 2:
                        f.warn(f"{aid}: race trips only {observed}/{runs} — flaky construction")
            else:
                if not quick:
                    r1 = go_run_program(program)
                    r2 = go_run_program(program)
                    stream = g.get("stream", "stdout")
                    d1 = r1.combined if stream == "combined" else r1.stdout
                    d2 = r2.combined if stream == "combined" else r2.stdout
                    if d1 != d2:
                        f.err(f"{aid}: program output is nondeterministic across two runs "
                              "(R4: fix the program — sort/sequence its output)")
                    expected = str(g.get("expected_output", ""))
                    mode = g.get("match", "trimmed")
                    derived_ok = (
                        expected.strip().lower() in d1.strip().lower()
                        if mode == "contains"
                        else _match(mode, expected, expected, d1)
                    )
                    if not derived_ok:
                        f.err(f"{aid}: stored expected_output does not match the DERIVED "
                              f"output (anti-fabrication). derived:\n{tail(d1, 15)}")
                    if r1.returncode != 0 and stream != "combined":
                        f.warn(f"{aid}: program exits non-zero but stream is stdout-only")

        elif strategy == "hidden_tests":
            test_code = g.get("test_code", "")
            if "func Test" not in test_code:
                f.err(f"{aid}: test_code missing (pilot convention: complete _test.go)")
                continue
            tests_meta = g.get("tests", [])
            if not tests_meta:
                f.err(f"{aid}: tests metadata list required")
            if tests_meta and not any(t.get("visible") for t in tests_meta):
                f.warn(f"{aid}: no visible test — learner gets zero signal before submitting")
            if tests_meta and all(t.get("visible") for t in tests_meta):
                f.warn(f"{aid}: no hidden test — overfitting to the checker is free")
            for t in tests_meta:
                if f"func {t['name']}" not in test_code and f"t.Run(\"{t['name']}\"" not in test_code:
                    f.warn(f"{aid}: tests metadata name '{t['name']}' not found in test_code")
            for code_field in ("reference_solution", "test_code"):
                if "package crucible" not in g.get(code_field, ""):
                    f.err(f"{aid}: {code_field} must be a complete file in package crucible")
            if a.get("type") == "debug_this" and "package crucible" not in g.get("buggy", ""):
                f.err(f"{aid}: debug_this needs a complete 'buggy' file in package crucible")
            # leak-guard lite: hidden goldens must not appear verbatim in learner-visible text
            visible_text = str(a.get("prompt", "")) + str(g.get("starter", ""))
            for t in tests_meta:
                if not t.get("visible") and str(t.get("golden", "")) and str(t["golden"]) in visible_text:
                    f.warn(f"{aid}: hidden test golden leaks into prompt/starter")
            if not quick:
                timeout_ms = int(g.get("timeout_ms", 30000))
                ref = go_test(g.get("reference_solution", ""), test_code, timeout_ms)
                if ref.returncode != 0:
                    f.err(f"{aid}: reference-reproduces FAILED — reference solution is not "
                          f"green under -race:\n{tail(ref.combined, 25)}")
                if a.get("type") == "debug_this":
                    bug = go_test(g.get("buggy", ""), test_code, timeout_ms)
                    if bug.returncode == 0:
                        f.err(f"{aid}: debug_this buggy code passes all tests — fake bug")

        elif strategy == "llm_judge":
            rubric = g.get("rubric", {})
            criteria = rubric.get("criteria", [])
            if not criteria:
                f.err(f"{aid}: llm_judge needs rubric.criteria")
            else:
                total = sum(float(c.get("weight", 0)) for c in criteria)
                if abs(total - 1.0) > 0.001:
                    f.err(f"{aid}: rubric weights sum to {total}, not 1.0")
            if not (0 < float(rubric.get("pass_threshold", 0)) <= 1):
                f.err(f"{aid}: pass_threshold must be in (0, 1]")
            ref = str(a.get("reference_answer", g.get("reference_answer", ""))).strip()
            if not ref:
                f.err(f"{aid}: llm_judge needs a non-empty reference_answer (grounding, R1/R7)")
            anti = rubric.get("anti_reward_hacking", g.get("anti_reward_hacking", {}))
            if not anti.get("min_words"):
                f.warn(f"{aid}: no anti_reward_hacking.min_words")
            elif len(ref.split()) < int(anti["min_words"]):
                f.err(f"{aid}: reference_answer itself is under min_words "
                      f"({len(ref.split())} < {anti['min_words']}) — rubric fails its own gold")

    # figures referential integrity
    figures = lesson.get("figures", {}) or {}
    body_text = json.dumps(lesson)
    for token in re.findall(r"\[\[fig:([a-z0-9-]+)\]\]", body_text):
        if token not in figures:
            f.err(f"[[fig:{token}]] has no matching figures entry")
    return f


def cmd_verify(lessons: dict[str, Lesson], lesson_id: str | None, quick: bool) -> int:
    targets = [lesson_or_die(lessons, lesson_id)] if lesson_id else list(lessons.values())
    all_ids = set(lessons)
    total_err = 0
    for lesson in targets:
        f = verify_lesson(lesson, all_ids, quick=quick)
        status = C.green("OK") if not f.errors else C.red(f"{len(f.errors)} error(s)")
        print(f"{lesson['id']:<12} {status}"
              + (C.orange(f"  {len(f.warnings)} warning(s)") if f.warnings else ""))
        for e in f.errors:
            print(C.red(f"    ERROR: {e}"))
        for w in f.warnings:
            print(C.orange(f"    warn:  {w}"))
        total_err += len(f.errors)
    n = len(targets)
    if total_err:
        print(C.red(C.bold(f"\nverify: {total_err} error(s) across {n} lesson(s) — NOT gradeable")))
        return 1
    print(C.green(C.bold(f"\nverify: all {n} lesson(s) gradeable"
                         + (" (quick: executables skipped)" if quick else ""))))
    return 0


# ------------------------------------------------------------------------------- list + status
def latest_verdicts() -> dict[str, dict[str, str]]:
    """lesson -> assessment -> latest verdict, replayed from the append-only log."""
    out: dict[str, dict[str, str]] = {}
    if not LOG_PATH.exists():
        return out
    with LOG_PATH.open() as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            out.setdefault(rec["lesson"], {})[rec["assessment"]] = rec["verdict"]
    return out


def cmd_list(lessons: dict[str, Lesson]) -> None:
    verdicts = latest_verdicts()
    print(f"\n{C.purple(C.bold('Crucible pilot — Go concurrency-discrimination vertical'))}\n")
    for lid in sorted(lessons):
        lesson = lessons[lid]
        aids = [a["id"] for a in lesson.get("assessments", [])]
        got = verdicts.get(lid, {})
        npass = sum(1 for a in aids if got.get(a) == "PASS")
        if npass == len(aids) and aids:
            badge = C.green("● passed")
        elif got:
            badge = C.orange(f"◐ {npass}/{len(aids)}")
        else:
            badge = C.dim("○ new")
        prereqs = ",".join(lesson.get("prerequisites", [])) or "-"
        print(f"  {badge}  {C.bold(lid):<32} {lesson['title']}")
        print(C.dim(f"            prereqs: {prereqs}"))
    print()


def cmd_status(lessons: dict[str, Lesson]) -> None:
    if not LOG_PATH.exists():
        print(C.dim("no attempts logged yet — run `make lesson ID=go04a-...`"))
        return
    records = []
    with LOG_PATH.open() as fh:
        for line in fh:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    days: dict[str, int] = {}
    for rec in records:
        day = rec["ts"][:10]
        days[day] = days.get(day, 0) + 1
    today = datetime.now().date()
    streak = 0
    d = today
    if today.isoformat() not in days:
        d = today - timedelta(days=1)  # a streak survives until a full day is missed
    while d.isoformat() in days:
        streak += 1
        d -= timedelta(days=1)
    verdicts = latest_verdicts()
    total_assessments = sum(len(le.get("assessments", [])) for le in lessons.values())
    passed = sum(1 for m in verdicts.values() for v in m.values() if v == "PASS")
    firsttry: dict[str, str] = {}
    for rec in records:
        firsttry.setdefault(rec["lesson"] + "/" + rec["assessment"], rec["verdict"])
    ftp = sum(1 for v in firsttry.values() if v == "PASS")
    print(f"\n{C.purple(C.bold('pilot status — numbers, not adjectives'))}\n")
    print(f"  study days:          {C.bold(str(len(days)))} distinct "
          f"(current streak {C.bold(str(streak))}; Phase 0 exit bar = 14 daily)")
    print(f"  attempts logged:     {len(records)}")
    print(f"  assessments passed:  {passed}/{total_assessments}")
    if firsttry:
        rate = ftp / len(firsttry)
        print(f"  first-try pass rate: {rate:.0%} "
              + C.dim("(desirable-difficulty band is ~70-85%; lower while interleaving is ON is expected)"))
    print(C.dim(f"\n  log: {LOG_PATH} (append-only; the mastery fold arrives in Phase 2)\n"))


# --------------------------------------------------------------------------------------- main
def main() -> int:
    parser = argparse.ArgumentParser(prog="pilot.py", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="lessons + pass state")
    p_run = sub.add_parser("run", help="run a lesson session (teach → test)")
    p_run.add_argument("lesson_id")
    p_run.add_argument("--review", action="store_true", help="test-first, reveal-on-miss")
    p_run.add_argument("--only", help="run a single assessment id")
    p_run.add_argument("--redo", action="store_true",
                       help="re-run the whole lesson, including items already passed")
    p_run.add_argument("--teach", action="store_true",
                       help="re-read the teach section even when resuming")
    p_ver = sub.add_parser("verify", help="prove every lesson is gradeable by construction")
    p_ver.add_argument("lesson_id", nargs="?")
    p_ver.add_argument("--quick", action="store_true", help="structural checks only, skip go runs")
    sub.add_parser("status", help="streak + honest numbers")
    args = parser.parse_args()

    _load_env_file()
    lessons = load_lessons()
    if args.cmd == "list":
        cmd_list(lessons)
    elif args.cmd == "run":
        run_lesson(lessons, args.lesson_id, args.review, args.only,
                   redo=args.redo, teach=args.teach)
    elif args.cmd == "verify":
        return cmd_verify(lessons, args.lesson_id, args.quick)
    elif args.cmd == "status":
        cmd_status(lessons)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SessionQuit:
        print(C.dim("\n  session ended — nothing logged for the open item\n"))
        raise SystemExit(0) from None
