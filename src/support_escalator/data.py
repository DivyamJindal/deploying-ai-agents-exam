from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .models import Account, KnowledgeBaseEntry

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def _load_json(name: str):
    return json.loads((DATA_DIR / name).read_text())


@lru_cache(maxsize=1)
def load_kb() -> list[KnowledgeBaseEntry]:
    return [KnowledgeBaseEntry.model_validate(item) for item in _load_json("kb.json")]


@lru_cache(maxsize=1)
def load_accounts() -> dict[str, Account]:
    return {item["account_id"]: Account.model_validate(item) for item in _load_json("accounts.json")}


def search_kb(query: str, category: str | None = None, limit: int = 3) -> list[KnowledgeBaseEntry]:
    words = {w.strip(".,!?;:'\"()").lower() for w in query.split()}
    scored: list[tuple[int, KnowledgeBaseEntry]] = []
    for entry in load_kb():
        if category and entry.category not in {category, "general"}:
            continue
        haystack = " ".join([entry.title, entry.body, " ".join(entry.tags)]).lower()
        score = sum(2 for tag in entry.tags if tag.lower() in words) + sum(1 for word in words if word in haystack)
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in scored[:limit]]
