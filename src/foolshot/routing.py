"""Task ownership and product model selection shared by all model entry points."""

import json
import os
import re
from pathlib import Path

ROLES = {
    "decision": "thinking",
    "weekly": "thinking",
    "incident": "thinking",
    "trial": "thinking",
    "position": "operations",
    "daily": "operations",
}
FAMILIES = {
    "codex": {"thinking": "astra", "operations": "sol"},
    "claude": {"thinking": "fable", "operations": "opus"},
}


def family_release(client, tier, name):
    family = FAMILIES[client][tier]
    pattern = (
        rf"gpt-(\d+(?:\.\d+)*)-{family}"
        if client == "codex"
        else rf"claude-{family}-(\d+(?:-\d+)*)"
    )
    return re.fullmatch(pattern, name or "")


def selections(client, thinking=None):
    models = dict(FAMILIES[client])
    if client == "codex":
        cache = (
            Path(os.getenv("CODEX_HOME", Path.home() / ".codex")) / "models_cache.json"
        )
        try:
            listed = [
                v["slug"]
                for v in json.loads(cache.read_text())["models"]
                if v.get("visibility") == "list"
            ]
        except (OSError, ValueError, KeyError, TypeError):
            listed = []
        for tier, family in models.copy().items():
            candidates = [
                (tuple(map(int, m[1].split("."))), name)
                for name in listed
                if (m := family_release(client, tier, name))
            ]
            models[tier] = max(candidates)[1] if candidates else f"gpt-6.2-{family}"
    if thinking:
        if (
            not family_release(client, "thinking", thinking)
            and thinking != models["thinking"]
        ):
            raise ValueError(
                "trade decisions require an explicit Astra or Fable release"
            )
        models["thinking"] = thinking
    return models


def route(db, client, task):
    role = ROLES[task]
    registered = db.execute(
        "SELECT payload FROM history WHERE id='registration'"
    ).fetchone()
    plan = json.loads(registered[0]) if registered else {}
    if plan and plan.get("client") != client:
        raise ValueError("client differs from the registered cohort")
    models = plan.get("model_routes") or selections(client)
    requested = models[role]
    return {"client": client, "task": task, "tier": role, "requested_model": requested}


def invocation_model(db, route):
    row = db.execute(
        "SELECT payload FROM history WHERE id=?", (pin_id(route),)
    ).fetchone()
    return json.loads(row[0])["release"] if row else route["requested_model"]


def pin_id(route):
    return f"model-pin/{route['client']}/{route['tier']}"
