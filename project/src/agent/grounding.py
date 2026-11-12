"""A number in an answer has to come from a tool result or from the question.

Rounding is allowed: 7234 matches 7234.41, and 20 matches 0.20 written as a
percent. A number with no such neighbour is ungrounded.
"""
from __future__ import annotations

import json
import re

_NUMBER = re.compile(r"(?<![A-Za-z0-9_.])(-?\d[\d,]*(?:\.\d+)?)(?![A-Za-z_])")


def numbers_in(text: str) -> list[float]:
    found = []
    for match in _NUMBER.finditer(text):
        token = match.group(1).replace(",", "")
        if token in ("-", ".", "-."):
            continue
        found.append(float(token))
    return found


def _values(payload) -> list[float]:
    if isinstance(payload, bool) or payload is None:
        return []
    if isinstance(payload, (int, float)):
        return [float(payload)]
    if isinstance(payload, str):
        return numbers_in(payload)
    if isinstance(payload, dict):
        out = []
        for value in payload.values():
            out.extend(_values(value))
        return out
    if isinstance(payload, (list, tuple)):
        out = []
        for value in payload:
            out.extend(_values(value))
        return out
    return []


def _matches(number: float, source: float) -> bool:
    tolerance = max(0.51, abs(source) * 1e-3)
    if abs(number - source) <= tolerance:
        return True
    percent = 100.0 * source
    return abs(number - percent) <= max(0.6, abs(percent) * 0.01)


def ungrounded(answer: str, tool_results: list, question: str = "") -> list[float]:
    allowed = _values(tool_results) + numbers_in(question)
    missing = []
    for number in numbers_in(answer):
        if not any(_matches(number, source) for source in allowed):
            missing.append(number)
    return missing


def tool_blob(tool_results: list) -> str:
    return json.dumps(tool_results, default=str)
