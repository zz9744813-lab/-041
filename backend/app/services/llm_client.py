"""LLM client - unified entry per spec § 17.4 (v2.1: budget guard + per-attempt history).

Workflow:
1. Compute input_hash = sha256(canonical(input_data) + prompt_version)
2. Cache lookup in LlmCallLog by (input_hash, model, prompt_version, status=SUCCESS)
3. Daily-cost guardrail: if today's spend >= settings.max_daily_llm_cost_usd, refuse.
4. On miss: call provider (optionally with extended thinking + streaming),
   capture raw text, validate via Pydantic schema. Each attempt is recorded
   in `attempt_history` so failed retries are auditable.
5. Schema fail: retry once asking LLM to fix
6. Persist LlmCallLog WITH system_prompt / user_input / raw_response_text /
   thinking / attempt_history / symbol so the UI can audit the full trail.
6. Return parsed result + log
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Type, TypeVar

from loguru import logger
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import LlmCallLog
from app.utils.time_utils import utc_now

T = TypeVar("T", bound=BaseModel)

# Approximate per-1k-token pricing (USD). Update as needed.
PRICING: dict[str, dict[str, Decimal]] = {
    "claude-haiku-4-5-20251001":  {"in": Decimal("0.001"),  "out": Decimal("0.005")},
    "claude-sonnet-4-6":          {"in": Decimal("0.003"),  "out": Decimal("0.015")},
    "claude-3-5-haiku-latest":    {"in": Decimal("0.0008"), "out": Decimal("0.004")},
    "claude-3-5-sonnet-latest":   {"in": Decimal("0.003"),  "out": Decimal("0.015")},
    "gpt-4o-mini":                {"in": Decimal("0.00015"), "out": Decimal("0.0006")},
    "gpt-4o":                     {"in": Decimal("0.0025"), "out": Decimal("0.01")},
}


def compute_input_hash(input_data: dict | BaseModel, prompt_version: str) -> str:
    if isinstance(input_data, BaseModel):
        input_data = input_data.model_dump(mode="json")
    payload = json.dumps(input_data, sort_keys=True, default=str)
    payload += f"|prompt={prompt_version}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> Decimal:
    rate = PRICING.get(model)
    if not rate:
        return Decimal("0")
    return (Decimal(input_tokens) * rate["in"] + Decimal(output_tokens) * rate["out"]) / Decimal(
        "1000"
    )


def todays_cost_usd(db: Session, now: datetime | None = None) -> Decimal:
    """Sum of `cost_usd` for non-cached calls created today (UTC)."""
    now = now or utc_now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    stmt = (
        select(func.coalesce(func.sum(LlmCallLog.cost_usd), 0))
        .where(LlmCallLog.created_at >= day_start, LlmCallLog.cached.is_(False))
    )
    val = db.execute(stmt).scalar_one()
    return Decimal(val) if val is not None else Decimal("0")


def _cache_lookup(
    db: Session, input_hash: str, model: str, prompt_version: str
) -> LlmCallLog | None:
    stmt = (
        select(LlmCallLog)
        .where(
            LlmCallLog.input_hash == input_hash,
            LlmCallLog.model == model,
            LlmCallLog.prompt_version == prompt_version,
            LlmCallLog.status == "SUCCESS",
        )
        .order_by(LlmCallLog.created_at.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def _extract_symbol(user_data: Any) -> str | None:
    """Pull `symbol` out of user_input for cost-attribution queries."""
    if isinstance(user_data, dict):
        sym = user_data.get("symbol")
        if isinstance(sym, str):
            return sym[:32]
    return None


def _persist_log(
    db: Session,
    purpose: str,
    provider: str,
    model: str,
    prompt_version: str,
    input_hash: str,
    cached: bool,
    status: str,
    *,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    cost_usd: Decimal | None = None,
    latency_ms: int | None = None,
    error_message: str | None = None,
    response_payload: dict | None = None,
    system_prompt: str | None = None,
    user_input: dict | list | str | None = None,
    raw_response_text: str | None = None,
    thinking: str | None = None,
    attempts: int | None = None,
    attempt_history: list | None = None,
    symbol: str | None = None,
) -> LlmCallLog:
    log = LlmCallLog(
        purpose=purpose,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        input_hash=input_hash,
        cached=cached,
        status=status,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
        error_message=error_message,
        response_payload=response_payload,
        system_prompt=system_prompt,
        user_input=user_input,
        raw_response_text=raw_response_text,
        thinking=thinking,
        attempts=attempts,
        attempt_history=attempt_history,
        symbol=symbol,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _call_anthropic(
    model: str,
    system_prompt: str,
    user_input: dict,
    timeout_s: int = 60,
    *,
    enable_thinking: bool = False,
    on_token: Callable[[dict], None] | None = None,
) -> tuple[str, str, int, int]:
    """Returns (text, thinking, input_tokens, output_tokens)."""
    from anthropic import Anthropic

    settings = get_settings()
    client = Anthropic(api_key=settings.anthropic_api_key, timeout=timeout_s)
    user_msg = json.dumps(user_input, ensure_ascii=False, default=str)

    extra: dict[str, Any] = {}
    if enable_thinking:
        extra["thinking"] = {"type": "enabled", "budget_tokens": 4000}

    if on_token is None:
        resp = client.messages.create(
            model=model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
            **extra,
        )
        text_parts: list[str] = []
        thinking_parts: list[str] = []
        for block in resp.content:
            t = getattr(block, "type", None)
            if t == "thinking":
                thinking_parts.append(getattr(block, "thinking", "") or "")
            elif t == "text":
                text_parts.append(getattr(block, "text", "") or "")
            else:
                fallback = getattr(block, "text", None)
                if fallback:
                    text_parts.append(fallback)
        return (
            "".join(text_parts),
            "".join(thinking_parts),
            resp.usage.input_tokens,
            resp.usage.output_tokens,
        )

    # Streaming path
    text_parts_s: list[str] = []
    thinking_parts_s: list[str] = []
    input_tokens = 0
    output_tokens = 0
    with client.messages.stream(
        model=model,
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
        **extra,
    ) as stream:
        for event in stream:
            etype = getattr(event, "type", "")
            if etype == "content_block_delta":
                delta = getattr(event, "delta", None)
                dtype = getattr(delta, "type", "") if delta else ""
                if dtype == "thinking_delta":
                    chunk = getattr(delta, "thinking", "") or ""
                    if chunk:
                        thinking_parts_s.append(chunk)
                        on_token({"type": "thinking_delta", "text": chunk})
                elif dtype == "text_delta":
                    chunk = getattr(delta, "text", "") or ""
                    if chunk:
                        text_parts_s.append(chunk)
                        on_token({"type": "text_delta", "text": chunk})
        final = stream.get_final_message()
        usage = getattr(final, "usage", None)
        if usage:
            input_tokens = getattr(usage, "input_tokens", 0) or 0
            output_tokens = getattr(usage, "output_tokens", 0) or 0
    return "".join(text_parts_s), "".join(thinking_parts_s), input_tokens, output_tokens


def _call_openai(
    model: str,
    system_prompt: str,
    user_input: dict,
    timeout_s: int = 60,
    *,
    on_token: Callable[[dict], None] | None = None,
) -> tuple[str, str, int, int]:
    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key, timeout=timeout_s)
    user_msg = json.dumps(user_input, ensure_ascii=False, default=str)

    if on_token is None:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
        )
        text = resp.choices[0].message.content or ""
        usage = resp.usage
        return text, "", usage.prompt_tokens, usage.completion_tokens

    text_parts: list[str] = []
    input_tokens = 0
    output_tokens = 0
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        stream=True,
        stream_options={"include_usage": True},
    )
    for chunk in stream:
        delta_obj = (chunk.choices[0].delta if chunk.choices else None)
        delta_text = getattr(delta_obj, "content", None) if delta_obj else None
        if delta_text:
            text_parts.append(delta_text)
            on_token({"type": "text_delta", "text": delta_text})
        usage = getattr(chunk, "usage", None)
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            output_tokens = getattr(usage, "completion_tokens", 0) or 0
    return "".join(text_parts), "", input_tokens, output_tokens


def _strip_json_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        first_nl = t.find("\n")
        if first_nl > 0:
            t = t[first_nl + 1 :]
        if t.endswith("```"):
            t = t[:-3]
    return t.strip()


def call_llm_structured(
    db: Session,
    purpose: str,
    system_prompt: str,
    user_input: dict | BaseModel,
    prompt_version: str,
    schema: Type[T],
    model_override: str | None = None,
    now: datetime | None = None,
    *,
    enable_thinking: bool | None = None,
    on_event: Callable[[dict], None] | None = None,
) -> tuple[T | None, LlmCallLog]:
    """Call LLM with structured-output validation + cache + retry + budget guard."""
    settings = get_settings()
    now = now or utc_now()
    provider = settings.llm_provider
    model = model_override or (
        settings.decision_model if purpose == "signal_generation" else settings.narration_model
    )
    user_data = user_input.model_dump(mode="json") if isinstance(user_input, BaseModel) else user_input
    input_hash = compute_input_hash(user_data, prompt_version)
    sym = _extract_symbol(user_data)

    if enable_thinking is None:
        enable_thinking = provider == "anthropic" and (
            "claude-sonnet" in model
            or "claude-opus" in model
            or model.startswith("claude-3-7")
            or model.startswith("claude-haiku-4")
            or model.startswith("claude-sonnet-4")
        )

    def _emit(ev: dict) -> None:
        if on_event is None:
            return
        try:
            on_event(ev)
        except Exception:
            logger.exception("on_event raised")

    # 1. Cache lookup (always free - happens before budget check)
    cached = _cache_lookup(db, input_hash, model, prompt_version)
    if cached and cached.response_payload:
        try:
            parsed = schema.model_validate(cached.response_payload)
            _emit({"type": "cache_hit"})
            log = _persist_log(
                db, purpose, provider, model, prompt_version, input_hash,
                cached=True, status="SUCCESS",
                input_tokens=cached.input_tokens, output_tokens=cached.output_tokens,
                cost_usd=Decimal("0"),  # cached call = no new cost
                latency_ms=0, response_payload=cached.response_payload,
                system_prompt=cached.system_prompt or system_prompt,
                user_input=cached.user_input if cached.user_input is not None else user_data,
                raw_response_text=cached.raw_response_text,
                thinking=cached.thinking,
                attempts=0,
                symbol=sym or cached.symbol,
            )
            return parsed, log
        except ValidationError as e:
            logger.warning("cache hit but schema mismatch: {}", e)

    # 2. Budget guardrail (only meaningful if max > 0)
    if settings.max_daily_llm_cost_usd and settings.max_daily_llm_cost_usd > 0:
        spent = todays_cost_usd(db, now)
        if spent >= settings.max_daily_llm_cost_usd:
            msg = (
                f"daily cost cap reached: spent ${spent} / cap ${settings.max_daily_llm_cost_usd}"
            )
            logger.warning(msg)
            _emit({"type": "budget_exceeded", "spent_usd": str(spent),
                   "cap_usd": str(settings.max_daily_llm_cost_usd)})
            log = _persist_log(
                db, purpose, provider, model, prompt_version, input_hash,
                cached=False, status="BUDGET_EXCEEDED",
                error_message=msg,
                system_prompt=system_prompt,
                user_input=user_data,
                attempts=0,
                symbol=sym,
            )
            return None, log

    # 3. Fresh call (with up to 1 retry); record per-attempt history
    last_error: str | None = None
    last_text = ""
    last_thinking = ""
    last_input_tokens = 0
    last_output_tokens = 0
    last_latency_ms = 0
    attempt_count = 0
    history: list[dict] = []
    for attempt in range(2):
        attempt_count = attempt + 1
        _emit({"type": "attempt_start", "attempt": attempt_count})
        start = time.time()
        try:
            if provider == "anthropic":
                text, thinking, tin, tout = _call_anthropic(
                    model, system_prompt, user_data,
                    enable_thinking=enable_thinking,
                    on_token=on_event if on_event else None,
                )
            else:
                text, thinking, tin, tout = _call_openai(
                    model, system_prompt, user_data,
                    on_token=on_event if on_event else None,
                )
            latency = int((time.time() - start) * 1000)
            last_text = text
            last_thinking = thinking
            last_input_tokens = tin
            last_output_tokens = tout
            last_latency_ms = latency

            try:
                parsed_json = json.loads(_strip_json_fence(text))
            except json.JSONDecodeError as e:
                last_error = f"json_decode: {e}"
                history.append({
                    "n": attempt_count, "ok": False, "error": last_error,
                    "raw_text": text[:8000], "thinking": thinking[:8000] or None,
                    "input_tokens": tin, "output_tokens": tout, "latency_ms": latency,
                })
                _emit({"type": "attempt_done", "attempt": attempt_count, "ok": False, "error": last_error})
                continue
            try:
                parsed = schema.model_validate(parsed_json)
            except ValidationError as e:
                last_error = f"schema: {e}"
                history.append({
                    "n": attempt_count, "ok": False, "error": last_error,
                    "raw_text": text[:8000], "thinking": thinking[:8000] or None,
                    "input_tokens": tin, "output_tokens": tout, "latency_ms": latency,
                })
                _emit({"type": "attempt_done", "attempt": attempt_count, "ok": False, "error": last_error})
                continue
            cost = estimate_cost(model, tin, tout)
            history.append({
                "n": attempt_count, "ok": True, "error": None,
                "raw_text": text[:8000], "thinking": thinking[:8000] or None,
                "input_tokens": tin, "output_tokens": tout, "latency_ms": latency,
            })
            log = _persist_log(
                db, purpose, provider, model, prompt_version, input_hash,
                cached=False, status="SUCCESS",
                input_tokens=tin, output_tokens=tout, cost_usd=cost,
                latency_ms=latency, response_payload=parsed_json,
                system_prompt=system_prompt,
                user_input=user_data,
                raw_response_text=text,
                thinking=thinking or None,
                attempts=attempt_count,
                attempt_history=history,
                symbol=sym,
            )
            _emit({"type": "attempt_done", "attempt": attempt_count, "ok": True})
            return parsed, log
        except Exception as e:
            last_error = f"api: {e}"
            logger.exception("llm api error attempt {}", attempt)
            history.append({
                "n": attempt_count, "ok": False, "error": last_error,
                "raw_text": None, "thinking": None,
                "input_tokens": None, "output_tokens": None, "latency_ms": None,
            })
            _emit({"type": "attempt_done", "attempt": attempt_count, "ok": False, "error": last_error})

    # All failed - persist what we have for debugging
    cost = estimate_cost(model, last_input_tokens, last_output_tokens)
    log = _persist_log(
        db, purpose, provider, model, prompt_version, input_hash,
        cached=False, status="API_ERROR",
        input_tokens=last_input_tokens or None,
        output_tokens=last_output_tokens or None,
        cost_usd=cost if last_input_tokens or last_output_tokens else None,
        latency_ms=last_latency_ms or None,
        error_message=last_error or "unknown",
        system_prompt=system_prompt,
        user_input=user_data,
        raw_response_text=last_text or None,
        thinking=last_thinking or None,
        attempts=attempt_count or None,
        attempt_history=history if history else None,
        symbol=sym,
    )
    return None, log
