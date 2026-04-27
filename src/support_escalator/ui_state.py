"""UI-safe normalization helpers for the Streamlit app.

The Streamlit layer can receive a mix of Pydantic models, dataclasses,
LangGraph ``Interrupt`` objects, and raw dicts. These helpers convert
arbitrary state into JSON-safe structures and provide attribute-or-key
field access so view code can render any of those shapes uniformly.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Iterable

try:
    from pydantic import BaseModel
except Exception:  # pragma: no cover - pydantic is required at runtime
    BaseModel = None  # type: ignore[assignment]


_PRIMITIVES = (str, int, float, bool, type(None))


def to_plain(value: Any) -> Any:
    """Recursively convert ``value`` into JSON-safe primitives.

    Pydantic models become dicts, datetimes become ISO strings, enums
    become their values, and LangGraph Interrupt-like objects expose
    their ``value`` attribute.
    """

    if isinstance(value, _PRIMITIVES):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if BaseModel is not None and isinstance(value, BaseModel):
        return to_plain(value.model_dump(mode="json"))
    if hasattr(value, "model_dump"):
        try:
            return to_plain(value.model_dump(mode="json"))
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_plain(item) for item in value]
    if hasattr(value, "value") and value.__class__.__name__ == "Interrupt":
        return to_plain(value.value)
    if hasattr(value, "__dict__"):
        return {k: to_plain(v) for k, v in vars(value).items() if not k.startswith("_")}
    return str(value)


def get_field(obj: Any, key: str, default: Any = None) -> Any:
    """Return ``obj[key]`` or ``obj.key`` if available, otherwise ``default``."""

    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    if hasattr(obj, key):
        return getattr(obj, key)
    return default


def extract_interrupt(result: Any) -> dict[str, Any] | None:
    """Pull the first interrupt payload out of a graph result, if any."""

    interrupts = get_field(result, "__interrupt__")
    if not interrupts:
        return None
    if isinstance(interrupts, Iterable):
        first = next(iter(interrupts), None)
    else:
        first = interrupts
    if first is None:
        return None
    payload = get_field(first, "value", first)
    return to_plain(payload)


def summarize_run(state: dict[str, Any]) -> dict[str, Any]:
    """Produce a lightweight summary used by KPI cards and charts."""

    state = to_plain(state) if not isinstance(state, dict) else state
    attempts = state.get("resolution_attempts") or []
    last_attempt = attempts[-1] if attempts else None
    return {
        "ticket_title": (state.get("ticket") or {}).get("title", ""),
        "account_id": (state.get("ticket") or {}).get("account_id", ""),
        "category": state.get("category"),
        "sentiment_score": float(state.get("sentiment_score") or 0.0),
        "escalation_reason": state.get("escalation_reason"),
        "supervisor_input": state.get("supervisor_input"),
        "solver": (last_attempt or {}).get("node"),
        "solver_resolved": bool((last_attempt or {}).get("resolved")) if last_attempt else False,
        "final_response": state.get("final_response", ""),
        "ticket_metadata": state.get("ticket_metadata", {}),
    }
