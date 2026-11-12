"""The analyst quotes tools, and a number it did not get is rejected.

The questions live in tests/agent_evals/cases.json. Expected figures are not
typed here: a reply is accepted when every number in it is in the tool result
or in the question.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent.analyst import answer
from src.agent.grounding import ungrounded
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import protected_files
from src.data.coal import check_composition
from src.data.parameters import Parameters
from src.data.presets import domestic_coal
from src.reporting.export import html_brief, workbook_bytes

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_CASES = os.path.join(os.path.dirname(__file__), "agent_evals", "cases.json")


def _digest(path: str) -> tuple[str, int]:
    with open(path, "rb") as fh:
        data = fh.read()
    return hashlib.sha256(data).hexdigest(), os.stat(path).st_mtime_ns


def test_prompt_states_the_limits():
    assert "parameters.json" in SYSTEM_PROMPT
    assert "validation_targets.json" in SYSTEM_PROMPT
    assert "Do not invent" in SYSTEM_PROMPT
    assert "Metallisation is an input" in SYSTEM_PROMPT
    assert "parameters.json" in protected_files()
    assert "validation_targets.json" in protected_files()


def test_domestic_preset_is_one_closed_coal():
    params = Parameters().with_overrides(domestic_coal())
    check_composition(params)
    assert params["coal_feed.ash"] == 0.30
    assert params["coal_feed.nhv_kj_kg"] == 19500.0
    assert params["coal_inj.ash"] == 0.28
    assert params["coal_inj.nhv_kj_kg"] == 20200.0


def test_rounding_is_grounded_and_an_invented_number_is_not():
    assert ungrounded("The cost is INR 7,234.", [{"cost": 7234.41}], "") == []
    missing = ungrounded("The cost is INR 99999.", [{"cost": 7234.41}], "What is the cost?")
    assert 99999 in missing


def test_session_cap_does_not_call_the_plant():
    reply = answer("What does the baseline plant cost?", turns_so_far=12)
    assert reply["tools"] == []
    assert "limit" in reply["text"]
    assert reply["grounded"]


def test_workbook_and_brief_carry_the_stamp():
    blob = workbook_bytes({"Baseline": [["Model", "0.7.0"], ["Cost", 7234.4]]})
    book = zipfile.ZipFile(io.BytesIO(blob))
    sheet = book.read("xl/worksheets/sheet1.xml").decode()
    assert "0.7.0" in sheet
    assert "7234.4" in sheet
    page = html_brief(
        {"preset": "imported", "capacity_tpd": 100, "coal_t_per_t": 1.025,
         "co2_total_t_per_t": 2.083, "cost_inr_per_t": 7234.41},
        {"label": "WHR", "cost_per_t": 6400.2, "co2_cut_frac": 0.21},
        "0.7.0")
    assert "0.7.0" in page
    assert "WHR" in page
    assert "Metallisation is an input" in page


def test_eval_answers_quote_the_tools_and_do_not_write():
    watched = [os.path.join(_ROOT, "config", name) for name in protected_files()]
    before = {path: _digest(path) for path in watched}
    cases = json.loads(open(_CASES).read())
    assert len(cases) >= 40
    seen = set()
    for case in cases:
        reply = answer(case["question"])
        seen.add(case["tool"])
        assert reply["tools"], case["id"]
        assert reply["tools"][0]["name"] == case["tool"], (case["id"], reply["text"])
        assert reply["grounded"], (case["id"], reply["ungrounded"], reply["text"])
        assert reply["refused"] is case.get("refused", False)
        for phrase in case.get("contains", []):
            assert phrase.lower() in reply["text"].lower(), (case["id"], reply["text"])
        if "contains_any" in case:
            assert any(phrase.lower() in reply["text"].lower()
                       for phrase in case["contains_any"]), (case["id"], reply["text"])
    assert {"run_scenario", "find_least_cost", "refuse", "get_parameter",
            "list_unsourced", "kiln_summary", "waste_heat_finance"} <= seen
    after = {path: _digest(path) for path in watched}
    assert after == before
