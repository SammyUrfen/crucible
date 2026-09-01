#!/usr/bin/env python3
"""Self-check for the pilot's non-obvious pure logic. Run: python pilot/test_pilot.py

Deliberately assert-based and framework-free — this is the throwaway probe, not the engine.
Covers the two functions where a silent bug would corrupt a grade: JSON extraction from a
model reply, and the weighted fold the judge is structurally forbidden from doing itself.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot import ANSWER_MARKER, build_header, extract_json, score_from_criteria  # noqa: E402

CRITERIA = [
    {"id": "c1", "weight": 0.5, "text": "names the rejected alternative"},
    {"id": "c2", "weight": 0.3, "text": "states a concrete failure mode"},
    {"id": "c3", "weight": 0.2, "text": "includes a number"},
]


def test_extract_json() -> None:
    assert extract_json('{"a":1}') == {"a": 1}
    assert extract_json('```json\n{"a":1}\n```') == {"a": 1}
    assert extract_json('Sure!\n```\n{"a":1}\n```\nHope that helps') == {"a": 1}
    assert extract_json('Here you go: {"a":[1,2]} done') == {"a": [1, 2]}
    # a reply with no object at all, or unparseable, must be None so the caller degrades
    assert extract_json("no json here") is None
    assert extract_json("{not valid}") is None
    assert extract_json('[1,2,3]') is None  # top-level array is not a grade envelope


def test_strip_header_round_trip() -> None:
    """The brief we inject must never survive into the graded answer — in either comment syntax."""
    from pilot import strip_header

    item = {"id": "go04a-a4", "type": "explain_tradeoff", "prompt": "Defend the closer goroutine."}
    answer = "My answer.\nSecond line."

    md = build_header(item, ["GRADED ON", "  [50%] names it"], wrap=("<!--", " -->")) + answer
    assert strip_header(md).strip() == answer
    assert "QUESTION" not in strip_header(md) and "-->" not in strip_header(md)

    go = build_header(item, [], line_prefix="// ") + "package crucible\n"
    assert strip_header(go).strip() == "package crucible"
    # the Go brief must be valid Go even if stripping never happened
    assert all(ln.startswith("//") or not ln.strip() for ln in go.split(ANSWER_MARKER)[0].splitlines())

    # no marker => the text is already all the learner's, return it untouched
    assert strip_header("just my answer") == "just my answer"
    # a learner who deletes the marker keeps their whole answer rather than losing it
    assert strip_header(answer) == answer


def test_score_from_criteria() -> None:
    score, rows = score_from_criteria(CRITERIA, {"c1": 1.0, "c2": 1.0, "c3": 1.0})
    assert score == 1.0 and len(rows) == 3
    score, _ = score_from_criteria(CRITERIA, {"c1": 1.0, "c2": 0.5, "c3": 0.0})
    assert abs(score - 0.65) < 1e-9
    # a criterion the judge silently omitted counts as NOT met — never as free credit
    score, _ = score_from_criteria(CRITERIA, {"c1": 1.0})
    assert abs(score - 0.5) < 1e-9
    # out-of-range values are clamped, so a judge cannot inflate past its own criteria
    score, _ = score_from_criteria(CRITERIA, {"c1": 99.0, "c2": -5.0, "c3": 0.0})
    assert abs(score - 0.5) < 1e-9
    # an unknown id is ignored rather than added
    score, _ = score_from_criteria(CRITERIA, {"c1": 1.0, "bogus": 1.0})
    assert abs(score - 0.5) < 1e-9


if __name__ == "__main__":
    test_extract_json()
    test_strip_header_round_trip()
    test_score_from_criteria()
    print("pilot self-check: all assertions passed")
