"""LLM-backed decision helpers for suffix, path, and directory review."""

from __future__ import annotations

import json

from src.ai.router import classify_batch


def llm_suffix_risk(
    extensions: list[str],
    *,
    model: str,
    provider: str = "",
    base_url: str = "",
    api_key: str = "",
    auth_method: str = "api_key",
    google_client_id: str = "",
    google_client_secret: str = "",
    google_refresh_token: str = "",
) -> dict[str, dict[str, object]]:
    """Classify suffix risk with one LLM call and parse JSON output."""
    if not extensions:
        return {}

    prompt = (
        "Return strict JSON only. "
        'Schema: {"items":[{"key":".ext","decision":"keep|drop|not_sure",'
        '"confidence":0.0,"reason":"..."}]}. '
        f"Input suffixes: {json.dumps(sorted(set(extensions)))}"
    )
    raw = classify_batch(
        model=model,
        prompt=prompt,
        temperature=0.0,
        provider=provider,
        base_url=base_url,
        api_key=api_key,
        auth_method=auth_method,
        google_client_id=google_client_id,
        google_client_secret=google_client_secret,
        google_refresh_token=google_refresh_token,
    )
    payload = _try_parse_json(raw)

    default = {
        ext: {"risk": "neutral", "confidence": 0.0, "reason": "LLM parse fallback"}
        for ext in extensions
    }
    if not payload:
        return default

    for item in _payload_items(payload):
        key = str(item.get("key") or item.get("suffix") or item.get("ext") or "")
        if key not in default:
            continue
        decision = _normalize_decision(str(item.get("decision", "not_sure")))
        default[key] = {
            "risk": _decision_to_risk(decision),
            "confidence": float(item.get("confidence", 0.0)),
            "reason": str(item.get("reason", "")),
        }
    return default


def llm_path_risk(
    paths: list[str],
    *,
    model: str,
    provider: str = "",
    base_url: str = "",
    api_key: str = "",
    auth_method: str = "api_key",
    google_client_id: str = "",
    google_client_secret: str = "",
    google_refresh_token: str = "",
) -> dict[str, dict[str, object]]:
    """Classify path risk for Stage 2."""
    if not paths:
        return {}

    prompt = (
        "Return strict JSON only. "
        'Schema: {"items":[{"key":"path","decision":"keep|drop|not_sure",'
        '"score":0.0,"confidence":0.0,"reason":"..."}]}. '
        f"Input paths: {json.dumps(paths)}"
    )
    raw = classify_batch(
        model=model,
        prompt=prompt,
        temperature=0.0,
        provider=provider,
        base_url=base_url,
        api_key=api_key,
        auth_method=auth_method,
        google_client_id=google_client_id,
        google_client_secret=google_client_secret,
        google_refresh_token=google_refresh_token,
    )
    payload = _try_parse_json(raw)

    default = {
        path: {
            "risk": "neutral",
            "score": 0.5,
            "confidence": 0.0,
            "reason": "LLM parse fallback",
        }
        for path in paths
    }
    if not payload:
        return default

    for item in _payload_items(payload):
        key = str(item.get("key") or item.get("path") or "")
        if key not in default:
            continue
        decision = _normalize_decision(str(item.get("decision", "not_sure")))
        score = float(item.get("score", _decision_to_score(decision)))
        default[key] = {
            "risk": _decision_to_risk(decision),
            "score": score,
            "confidence": float(item.get("confidence", 0.0)),
            "reason": str(item.get("reason", "")),
        }
    return default


def llm_directory_decision(
    directory: str,
    child_directories: list[str],
    sample_files: list[str],
    *,
    model: str,
    provider: str = "",
    base_url: str = "",
    api_key: str = "",
    auth_method: str = "api_key",
    google_client_id: str = "",
    google_client_secret: str = "",
    google_refresh_token: str = "",
) -> dict[str, object]:
    """Classify one directory for Stage 3 DFS decision."""
    prompt = (
        "Return strict JSON only. "
        'Schema: {"decision":"keep|drop|not_sure","confidence":0.0,"reason":"..."}. '
        f"Directory: {directory}. Child directories: {json.dumps(child_directories[:20])}. "
        f"Sample files: {json.dumps(sample_files[:20])}."
    )
    raw = classify_batch(
        model=model,
        prompt=prompt,
        temperature=0.0,
        provider=provider,
        base_url=base_url,
        api_key=api_key,
        auth_method=auth_method,
        google_client_id=google_client_id,
        google_client_secret=google_client_secret,
        google_refresh_token=google_refresh_token,
    )
    payload = _try_parse_json(raw)
    if not payload:
        return {
            "decision": "not_sure",
            "confidence": 0.0,
            "reason": "LLM parse fallback",
        }
    return {
        "decision": _normalize_decision(str(payload.get("decision", "not_sure"))),
        "confidence": float(payload.get("confidence", 0.0)),
        "reason": str(payload.get("reason", "")),
    }


def _try_parse_json(raw: str) -> dict[str, object] | None:
    text = _extract_json_candidate(raw.strip())
    if not text:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _extract_json_candidate(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    if text.startswith("{") or text.startswith("["):
        return text

    first_obj = text.find("{")
    first_arr = text.find("[")
    candidates = [idx for idx in [first_obj, first_arr] if idx >= 0]
    if not candidates:
        return text
    return text[min(candidates) :]


def _payload_items(payload: dict[str, object]) -> list[dict[str, object]]:
    raw_items = payload.get("items")
    if isinstance(raw_items, list):
        return [item for item in raw_items if isinstance(item, dict)]
    return []


def _normalize_decision(value: str) -> str:
    item = value.lower().strip()
    if item in {"keep", "drop", "not_sure"}:
        return item
    return "not_sure"


def _decision_to_risk(decision: str) -> str:
    if decision == "keep":
        return "high_value"
    if decision == "drop":
        return "low_value"
    return "neutral"


def _decision_to_score(decision: str) -> float:
    if decision == "keep":
        return 0.85
    if decision == "drop":
        return 0.2
    return 0.5
