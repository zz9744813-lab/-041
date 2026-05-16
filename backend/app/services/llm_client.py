"""LLM client - unified entry per spec § 17.4.

Workflow:
1. Compute input_hash = sha256(canonical(input_data) + prompt_version)
2. Cache lookup in LlmCallLog by (input_hash, model, prompt_version, status=SUCCESS)
3. On miss: call provider with structured output mode, validate via Pydantic schema
4. Schema fail: retry once asking LLM to fix
5. Persist LlmCallLog
6. Return parsed result + log
"""
import hashlib
import json
import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Type, TypeVar

from loguru import logger
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
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


def _persist_log(
    db: Session,
    purpose: str,
    provider: str,
    model: str,
    prompt_version: str,
    input_hash: str,
    cached: bool,
    status: str,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    cost_usd: Decimal | None = None,
    latency_ms: int | None = None,
    error_message: str | None = None,
    response_payload: dict | None = None,
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
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _call_anthropic(
    model: str, system_prompt: str, user_input: dict, timeout_s: int = 60
) -> tuple[str, int, int]:
    """Returns (text, input_tokens, output_tokens)."""
    from anthropic import Anthropic

    settings = get_settings()
    client = Anthropic(api_key=settings.anthropic_api_key, timeout=timeout_s)
    user_msg = json.dumps(user_input, ensure_ascii=False, default=str)
    resp = client.messages.create(
        model=model,
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "".join(getattr(b, "text", "") for b in resp.content)
    return text, resp.usage.input_tokens, resp.usage.output_tokens


def _call_openai(
    model: str, system_prompt: str, user_input: dict, timeout_s: int = 60
) -> tuple[str, int, int]:
    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key, timeout=timeout_s)
    user_msg = json.dumps(user_input, ensure_ascii=False, default=str)
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
    return text, usage.prompt_tokens, usage.completion_tokens


def _strip_json_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        # remove first fence and last fence
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
) -> tuple[T | None, LlmCallLog]:
    """Call LLM with structured-output validation + cache + retry."""
    settings = get_settings()
    now = now or utc_now()
    provider = settings.llm_provider
    model = model_override or (
        settings.decision_model if purpose == "signal_generation" else settings.narration_model
    )
    user_data = user_input.model_dump(mode="json") if isinstance(user_input, BaseModel) else user_input
    input_hash = compute_input_hash(user_data, prompt_version)

    # 1. Cache lookup
    cached = _cache_lookup(db, input_hash, model, prompt_version)
    if cached and cached.response_payload:
        try:
            parsed = schema.model_validate(cached.response_payload)
            log = _persist_log(
                db, purpose, provider, model, prompt_version, input_hash,
                cached=True, status="SUCCESS",
                input_tokens=cached.input_tokens, output_tokens=cached.output_tokens,
                cost_usd=Decimal("0"),  # cached call = no new cost
                latency_ms=0, response_payload=cached.response_payload,
            )
            return parsed, log
        except ValidationError as e:
            logger.warning("cache hit but schema mismatch: {}", e)

    # 2. Fresh call (with up to 1 retry)
    last_error: str | None = None
    for attempt in range(2):
        start = time.time()
        try:
            if provider == "anthropic":
                text, tin, tout = _call_anthropic(model, system_prompt, user_data)
            else:
                text, tin, tout = _call_openai(model, system_prompt, user_data)
            latency = int((time.time() - start) * 1000)
            cost = estimate_cost(model, tin, tout)
            try:
                parsed_json = json.loads(_strip_json_fence(text))
            except json.JSONDecodeError as e:
                last_error = f"json_decode: {e}"
                continue
            try:
                parsed = schema.model_validate(parsed_json)
            except ValidationError as e:
                last_error = f"schema: {e}"
                continue
            log = _persist_log(
                db, purpose, provider, model, prompt_version, input_hash,
                cached=False, status="SUCCESS",
                input_tokens=tin, output_tokens=tout, cost_usd=cost,
                latency_ms=latency, response_payload=parsed_json,
            )
            return parsed, log
        except Exception as e:
            last_error = f"api: {e}"
            logger.exception("llm api error attempt {}", attempt)

    # All failed
    log = _persist_log(
        db, purpose, provider, model, prompt_version, input_hash,
        cached=False, status="API_ERROR",
        error_message=last_error or "unknown",
    )
    return None, log
