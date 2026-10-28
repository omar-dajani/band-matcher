from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import TASKS, TOOLS, MatchInput, Task, Tool
from plugin import match_bands

ARGS = {
    "documents": [
        {"doc_id": "a", "signature": [1, 2, 3, 4]},
        {"doc_id": "b", "signature": [7, 7, 3, 4]},
        {"doc_id": "c", "signature": [5, 5, 5, 5]},
    ],
    "query": [1, 2, 3, 4],
    "bands": 2,
    "rows": 2,
}


def answer(arguments=ARGS):
    return plain_output(match_bands(build_output(arguments, MatchInput), Path(".")))


def verify_input(value):
    return verifier.verify_input("match_bands", build_output(value, TOOLS[Tool.MATCH_BANDS][0]))


def verify_output(arguments, output):
    given, made = TOOLS[Tool.MATCH_BANDS]
    return verifier.verify_output("match_bands", build_output(arguments, given), build_output(output, made), ".")


def verify_task(arguments, output):
    given, made = TASKS[Task.FIND_LSH_CANDIDATES]
    return verifier.verify_task(
        "find-lsh-candidates", build_output(arguments, given), build_output(output, made), None, "."
    )


def test_accepts_the_correct_answer():
    assert verify_task(ARGS, answer())["valid"] is True
    assert verify_output(ARGS, answer())["valid"] is True


def test_accepts_an_answer_with_no_candidates():
    arguments = ARGS | {"query": [9, 9, 9, 9]}
    made = answer(arguments)
    assert made["pairs"] == [] and verify_task(arguments, made)["valid"] is True


def test_accepts_the_smallest_layout_and_no_documents():
    arguments = {"documents": [], "query": [3], "bands": 1, "rows": 1}
    assert verify_task(arguments, answer(arguments))["valid"] is True


def test_refuses_a_missing_candidate():
    made = answer()
    made["pairs"].pop()
    verdict = verify_task(ARGS, made)
    assert verdict["valid"] is False and verdict["details"]["missing"] == ["b"]
    assert 0 < verdict["score"] < 1


def test_refuses_an_invented_candidate():
    made = answer()
    made["pairs"].append({"doc_id": "c", "bands": [0]})
    verdict = verify_task(ARGS, made)
    assert verdict["valid"] is False and verdict["details"]["extra"] == ["c"]


def test_refuses_wrong_shared_bands_or_order():
    made = answer()
    made["pairs"][1]["bands"] = [0]
    assert verify_task(ARGS, made)["valid"] is False
    swapped = answer()
    swapped["pairs"].reverse()
    assert verify_task(ARGS, swapped)["valid"] is False


def test_refuses_a_wrong_bucket_id():
    made = answer()
    made["query_buckets"][0] = "0" * 16
    assert verify_task(ARGS, made)["valid"] is False
    other = answer()
    other["documents"][1]["buckets"][1] = "f" * 16
    assert "b" in verify_task(ARGS, other)["message"]


def test_refuses_dropped_or_reordered_documents():
    made = answer()
    assert verify_task(ARGS, made | {"documents": made["documents"][:-1]})["valid"] is False
    assert verify_task(ARGS, made | {"documents": made["documents"][::-1]})["valid"] is False


def test_refuses_an_answer_computed_for_another_layout():
    assert verify_task(ARGS, answer(ARGS | {"bands": 4, "rows": 1}))["valid"] is False
    assert verify_task(ARGS, answer(ARGS | {"bands": 1, "rows": 4}))["valid"] is False


@pytest.mark.parametrize(
    "changes",
    [
        {"bands": 0},
        {"rows": 0},
        {"bands": 65, "rows": 1},
        {"query": [1, 2, 3]},
        {"documents": [{"doc_id": "a", "signature": [1, 2]}]},
        {"documents": [{"doc_id": "a", "signature": [1, 2, 3, 4]}] * 2},
        {"documents": [{"doc_id": "", "signature": [1, 2, 3, 4]}]},
    ],
)
def test_refuses_malformed_input(changes):
    assert verify_input(ARGS | changes)["valid"] is False
    assert verify_task(ARGS | changes, answer())["valid"] is False


def test_the_verdict_is_deterministic():
    made = answer()
    assert verify_task(ARGS, made) == verify_task(ARGS, made)
