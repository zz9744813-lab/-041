"""Application settings - all values from env via pydantic-settings."""
from decimal import Decimal
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Database ----
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/mini_hermes"
    )

    # ---- Data sources ----
    alpaca_api_key: str = ""
    alpaca_api_secret: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    polygon_api_key: str = ""
    coinbase_api_key: str = ""

    # ---- LLM ----
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    decision_model: str = "claude-haiku-4-5-20251001"
    narration_model: str = "claude-sonnet-4-6"
    enable_llm_decision: bool = False
    prompt_version: str = "1.0"
    # Per-day USD spending cap. 0 = no cap. When the cumulative
    # cost_usd of today's LlmCallLog rows reaches this value, llm_client
    # short-circuits with status=BUDGET_EXCEEDED instead of calling out.
    max_daily_llm_cost_usd: Decimal = Decimal("0")

    # ---- Risk (defaults from spec § 14.4) ----
    initial_capital_usd: Decimal = Decimal("100000")
    max_per_trade_risk_pct: Decimal = Decimal("0.01")
    max_per_asset_pct: Decimal = Decimal("0.15")
    max_us_stock_pct: Decimal = Decimal("0.70")
    max_crypto_pct: Decimal = Decimal("0.40")
    max_total_pct: Decimal = Decimal("0.80")
    min_cash_reserve_pct: Decimal = Decimal("0.20")
    max_drawdown_pct: Decimal = Decimal("0.10")
    min_confidence: int = 65
    min_rr: Decimal = Decimal("1.5")
    max_per_correlation_group_pct: Decimal = Decimal("0.35")

    # ---- Strategy ----
    strategy_score_threshold: int = 65

    # ---- System ----
    log_level: str = "INFO"
    timezone: str = "UTC"
    alert_webhook_url: str = ""

    # ---- Signal lifecycle (spec § 8.4) ----
    default_signal_decay_hours_us_stock: int = 24
    default_signal_decay_hours_crypto: int = 12

    # ---- Slippage / fees (spec § 15.6) ----
    slippage_us_stock: Decimal = Decimal("0.001")
    slippage_crypto: Decimal = Decimal("0.0015")
    fee_us_stock: Decimal = Decimal("0")
    fee_crypto: Decimal = Decimal("0.001")


@lru_cache
def get_settings() -> Settings:
    return Settings()
