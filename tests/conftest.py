"""Test-wide fixtures.

We force rule-based mode during tests so the suite is deterministic, free, and
network-free. Tests that explicitly want to exercise the LLM path can opt back
in via monkeypatch.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _disable_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
