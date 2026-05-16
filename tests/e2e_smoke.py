"""End-to-end smoke test against an in-memory SQLite DB.

Steps:
1. Override DATABASE_URL to sqlite (file in repo, gets cleaned up).
2. Create all tables via Base.metadata.create_all.
3. Seed minimal mock data (Asset / StrategyModel / PortfolioSnapshot /
   SystemHealth).
4. Spin up FastAPI test client.
5. Hit every router endpoint and assert response shape.

Run:  py tests/e2e_smoke.py
"""
import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Make sure backend/ is on sys.path
HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent / "backend"
sys.path.insert(0, str(BACKEND))

# Configure env BEFORE importing the app
DB_PATH = HERE / ".smoke.db"
if DB_PATH.exists():
    DB_PATH.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"
os.environ["ENABLE_LLM_DECISION"] = "false"
os.environ["LOG_LEVEL"] = "WARNING"
# Encryption key required by config.py - dummy for smoke
os.environ.setdefault("ENCRYPTION_KEY", "smoke-test-key-12345678")

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Asset,
    PortfolioSnapshot,
    Signal,
    StrategyModel,
    SystemHealth,
    Trade,
    Position,
    Review,
    ModelStat,
)
from app.models.enums import (  # noqa: E402
    AssetType,
    Direction,
    Market,
    SignalStatus,
    SignalType,
    TradeStatus,
)


# ---- Setup ----

def reset_and_seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    now = datetime.now(UTC)

    # Assets
    assets = [
        Asset(symbol="SPY", name="SPDR S&P 500", market=Market.US_STOCK.value,
              asset_type=AssetType.ETF.value, sector="Broad", priority=1),
        Asset(symbol="NVDA", name="NVIDIA", market=Market.US_STOCK.value,
              asset_type=AssetType.STOCK.value, sector="Tech", priority=5),
        Asset(symbol="BTC-USD", name="Bitcoin", market=Market.CRYPTO.value,
              asset_type=AssetType.CRYPTO.value, sector="Crypto", priority=2),
    ]
    db.add_all(assets)

    # Strategy models
    db.add_all([
        StrategyModel(name="trend_breakout", description="20-day breakout",
                      weight=Decimal("1.0"), is_active=True, auto_adjust_weight=True),
        StrategyModel(name="pullback_trend", description="Pullback to MA50",
                      weight=Decimal("1.0"), is_active=True, auto_adjust_weight=True),
        StrategyModel(name="ma_trend", description="MA stack trend follow",
                      weight=Decimal("0.8"), is_active=True, auto_adjust_weight=True),
    ])

    # Portfolio snapshots over 5 days
    for i in range(5):
        db.add(PortfolioSnapshot(
            timestamp=now - timedelta(days=4 - i),
            cash=Decimal("80000") - Decimal(str(i * 100)),
            equity=Decimal("100000") + Decimal(str(i * 250)),
            market_value=Decimal("20000") + Decimal(str(i * 350)),
            us_stock_exposure=Decimal("15000"),
            crypto_exposure=Decimal("5000"),
            daily_pnl=Decimal("250"),
            total_return_pct=Decimal("0.0125") * Decimal(str(i)),
            max_drawdown_pct=Decimal("0.02"),
            open_positions_count=2,
            consecutive_losses=0,
        ))

    # SystemHealth records
    for job in ["sync_market_data", "calculate_indicators", "heartbeat",
                "classify_market_regime", "generate_signals"]:
        db.add(SystemHealth(
            job_name=job,
            started_at=now - timedelta(minutes=10),
            finished_at=now - timedelta(minutes=9),
            status="SUCCESS",
            stats={"checked": 3},
        ))
    # And one failed
    db.add(SystemHealth(
        job_name="sync_market_data",
        started_at=now - timedelta(hours=2),
        finished_at=now - timedelta(hours=2) + timedelta(seconds=5),
        status="FAILED",
        error_message="Alpaca 401",
        stats={},
    ))

    # A signal + a trade + a closed trade + review
    sig_open = Signal(
        symbol="NVDA",
        market=Market.US_STOCK.value,
        direction=Direction.LONG.value,
        signal_type=SignalType.PULLBACK_BUY.value,
        schema_version="1.0",
        current_price=Decimal("142.30"),
        entry_low=Decimal("141.50"),
        entry_high=Decimal("143.00"),
        stop_loss=Decimal("138.00"),
        target_1=Decimal("150.00"),
        target_2=Decimal("155.00"),
        confidence_score=72,
        risk_reward_ratio=Decimal("2.0"),
        position_size_pct=Decimal("5.0"),
        expected_holding_days_min=3,
        expected_holding_days_max=15,
        signal_decay_hours=24,
        model_name="pullback_trend",
        reason="Pullback to MA50 with 4h stabilization",
        risk_note="Stop near recent low",
        invalid_condition="Close below 138",
        input_hash="dummy" * 12,
        prompt_version="1.0",
        status=SignalStatus.EXECUTED.value,
        valid_until=now + timedelta(hours=12),
        generation_batch_id="batch-1",
    )
    db.add(sig_open)
    db.flush()

    trade_open = Trade(
        signal_id=sig_open.id,
        symbol="NVDA",
        market=Market.US_STOCK.value,
        direction=Direction.LONG.value,
        model_name="pullback_trend",
        entry_time=now - timedelta(hours=18),
        entry_price=Decimal("142.50"),
        entry_fill_policy="NEXT_BAR_OPEN_OR_TOUCH",
        quantity=Decimal("35.0"),
        position_value=Decimal("4987.50"),
        slippage_paid=Decimal("0.5"),
        fee_paid=Decimal("0"),
        stop_loss_initial=Decimal("138.00"),
        target_1=Decimal("150.00"),
        target_2=Decimal("155.00"),
        max_holding_days=15,
        stop_loss_current=Decimal("138.00"),
        trailing_stop_activated=False,
        status=TradeStatus.OPEN.value,
    )
    db.add(trade_open)
    db.flush()

    db.add(Position(
        trade_id=trade_open.id,
        symbol="NVDA",
        quantity=Decimal("35.0"),
        avg_entry_price=Decimal("142.50"),
        current_price=Decimal("145.20"),
        stop_loss_current=Decimal("138.00"),
        unrealized_pnl=Decimal("94.50"),
        unrealized_pnl_pct=Decimal("0.019"),
        max_favorable_excursion=Decimal("146.00"),
        max_adverse_excursion=Decimal("141.00"),
        holding_days=1,
        status="OPEN",
    ))

    # A closed (winning) trade for /trades and /reviews
    sig_closed = Signal(
        symbol="BTC-USD",
        market=Market.CRYPTO.value,
        direction=Direction.LONG.value,
        signal_type=SignalType.TREND_BREAKOUT.value,
        schema_version="1.0",
        current_price=Decimal("65000"),
        entry_low=Decimal("65000"),
        entry_high=Decimal("65500"),
        stop_loss=Decimal("63000"),
        target_1=Decimal("70000"),
        confidence_score=78,
        risk_reward_ratio=Decimal("2.5"),
        position_size_pct=Decimal("8.0"),
        signal_decay_hours=12,
        model_name="trend_breakout",
        reason="20-day breakout with strong volume",
        risk_note="ATR-based stop",
        invalid_condition="Close below 63000",
        input_hash="closed" * 10,
        prompt_version="1.0",
        status=SignalStatus.EXECUTED.value,
        valid_until=now,
        generation_batch_id="batch-0",
    )
    db.add(sig_closed)
    db.flush()

    trade_closed = Trade(
        signal_id=sig_closed.id,
        symbol="BTC-USD",
        market=Market.CRYPTO.value,
        direction=Direction.LONG.value,
        model_name="trend_breakout",
        entry_time=now - timedelta(days=5),
        entry_price=Decimal("65300"),
        entry_fill_policy="NEXT_BAR_OPEN_OR_TOUCH",
        quantity=Decimal("0.122"),
        position_value=Decimal("7966.6"),
        slippage_paid=Decimal("9.8"),
        fee_paid=Decimal("8.0"),
        stop_loss_initial=Decimal("63000"),
        target_1=Decimal("70000"),
        max_holding_days=10,
        stop_loss_current=Decimal("65300"),
        trailing_stop_activated=True,
        exit_time=now - timedelta(days=2),
        exit_price=Decimal("70000"),
        exit_reason="TAKE_PROFIT_1",
        exit_fill_policy="DEFAULT",
        pnl_amount=Decimal("573.4"),
        pnl_pct=Decimal("0.072"),
        realized_r_multiple=Decimal("2.04"),
        status=TradeStatus.CLOSED.value,
    )
    db.add(trade_closed)
    db.flush()

    db.add(Review(
        trade_id=trade_closed.id,
        summary="BTC 突破后顺利达到 TP1。入场价位接近最优区间下沿;出场触及预设 TP1 后及时止盈。"
                "波动期间最大浮亏控制在合理范围内,移动止损在 1.5R 时正确激活并保护了利润。",
        entry_quality=4,
        exit_quality=4,
        risk_control_quality=5,
        what_worked=["20 日突破识别精确", "trailing stop 及时激活", "成交量配合"],
        what_failed=[],
        model_adjustment_suggestion="保留模型,可考虑微调突破阈值到 1.5%",
        should_keep_model_signal=True,
    ))

    # ModelStat for one model
    db.add(ModelStat(
        model_name="trend_breakout",
        window="LAST_30D",
        trade_count=8,
        win_count=5,
        loss_count=3,
        win_rate=Decimal("0.625"),
        avg_win_pct=Decimal("0.045"),
        avg_loss_pct=Decimal("-0.018"),
        profit_factor=Decimal("3.5"),
        expectancy=Decimal("0.022"),
        avg_r_multiple=Decimal("1.4"),
        sample_quality="LOW",
    ))
    db.add(ModelStat(
        model_name="pullback_trend",
        window="LAST_30D",
        trade_count=2,
        win_count=1,
        loss_count=1,
        win_rate=Decimal("0.5"),
        sample_quality="INSUFFICIENT",
    ))

    db.commit()
    db.close()
    print("[seed] OK - 3 assets, 3 strategy_models, 5 snapshots, 1 OPEN + 1 CLOSED trade, 1 review")


# ---- Endpoint coverage ----

ENDPOINTS = [
    ("GET", "/health"),
    ("GET", "/api/assets"),
    ("GET", "/api/assets?active_only=true"),
    ("GET", "/api/portfolio"),
    ("GET", "/api/portfolio/equity-curve?days=30"),
    ("GET", "/api/portfolio/drawdown?days=30"),
    ("GET", "/api/portfolio/exposure"),
    ("GET", "/api/signals?limit=50"),
    ("GET", "/api/trades?status=OPEN"),
    ("GET", "/api/trades?status=CLOSED"),
    ("GET", "/api/reviews"),
    ("GET", "/api/models"),
    ("GET", "/api/models/trend_breakout/stats?window=LAST_30D"),
    ("GET", "/api/models/trend_breakout/recent-trades?limit=20"),
    ("GET", "/api/system/health"),
    ("GET", "/api/system/llm-stats?days=7"),
    ("GET", "/api/system/data-freshness"),
    ("GET", "/api/system/reject-reasons?days=7"),
    ("GET", "/api/market/regime"),
]


def run_endpoint_smoke():
    client = TestClient(app)
    failures = []
    successes = []
    for method, path in ENDPOINTS:
        try:
            if method == "GET":
                r = client.get(path)
            else:
                r = client.request(method, path)
            ok = 200 <= r.status_code < 300
            entry = f"{method} {path:60} -> {r.status_code}"
            if not ok:
                entry += f"  body={r.text[:200]}"
                failures.append(entry)
            else:
                # Try to parse json
                try:
                    body = r.json()
                    if isinstance(body, list):
                        entry += f" (list, {len(body)} items)"
                    elif isinstance(body, dict):
                        entry += f" (dict, {len(body)} keys)"
                except Exception as e:
                    entry += f" (json parse fail: {e})"
                    failures.append(entry)
                    continue
                successes.append(entry)
        except Exception as e:
            failures.append(f"{method} {path:60} -> EXC {e}")

    for s in successes:
        print("[ok]   " + s)
    for f in failures:
        print("[FAIL] " + f)
    print(f"\n{len(successes)} ok, {len(failures)} failed")
    return failures


if __name__ == "__main__":
    print("=== Mini Hermes E2E smoke test (SQLite) ===\n")
    reset_and_seed()
    print()
    fails = run_endpoint_smoke()
    print()
    if fails:
        print("RESULT: FAILED")
        sys.exit(1)
    else:
        print("RESULT: PASSED")
