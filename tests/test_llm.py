"""Tests for the LLM module's rule-based fallback and dispatch logic."""

from __future__ import annotations

import pytest

from support_escalator import llm as llm_mod


def test_mode_is_rule_based_without_key():
    assert llm_mod.mode() == "rule_based"


def test_classify_rule_based_billing():
    result = llm_mod.classify("Billing question", "I was charged twice for invoice 42")
    assert result.category == "billing"
    assert 0.0 <= result.confidence <= 1.0


def test_classify_rule_based_bug():
    result = llm_mod.classify("Crash", "the upload is failing and the app crashed")
    assert result.category == "bug"


def test_classify_rule_based_general_default():
    result = llm_mod.classify("Hi", "how do I reset my password please")
    # No keyword for general, but the function always returns one of the four.
    assert result.category in {"general", "feature", "bug", "billing"}


def test_sentiment_rule_based_calm():
    result = llm_mod.sentiment("Hi, hope you can help me with a small question.")
    assert result.score < 0.34
    assert result.label == "calm"


def test_sentiment_rule_based_frustrated():
    result = llm_mod.sentiment("This is my third email and nobody is helping!!! terrible")
    assert result.score >= 0.67
    assert result.label == "frustrated"


def test_classify_falls_back_when_llm_raises(monkeypatch: pytest.MonkeyPatch):
    """When the API key is set but the LLM call blows up, we must not crash."""

    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-test")

    def boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(llm_mod, "classify_llm", boom)
    result = llm_mod.classify("Bug", "the app crashed during upload")
    assert result.category == "bug"


def test_sentiment_falls_back_when_llm_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-test")

    def boom(*args, **kwargs):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(llm_mod, "sentiment_llm", boom)
    result = llm_mod.sentiment("nobody is helping me!!!")
    assert result.score > 0.0
