"""Smoke tests - verifies app starts and DB schemas are coherent."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_signal_plan_validates_long_consistency():
    from decimal import Decimal

    from pydantic import ValidationError

    from app.models.enums import Direction, Market, SignalType
    from app.schemas.signal_schema import SignalPlan

    # Valid LONG
    plan = SignalPlan(
        symbol="BTC-USD",
        market=Market.CRYPTO,
        direction=Direction.LONG,
        signal_type=SignalType.PULLBACK_BUY,
        current_price=Decimal("100"),
        entry_low=Decimal("99"),
        entry_high=Decimal("101"),
        stop_loss=Decimal("95"),
        target_1=Decimal("110"),
        confidence_score=70,
        reason="test reason",
        invalid_condition="if price drops below 95",
    )
    assert plan.entry_low <= plan.entry_high

    # Invalid: stop_loss > entry_low
    try:
        SignalPlan(
            symbol="BTC-USD",
            market=Market.CRYPTO,
            direction=Direction.LONG,
            signal_type=SignalType.PULLBACK_BUY,
            current_price=Decimal("100"),
            entry_low=Decimal("99"),
            entry_high=Decimal("101"),
            stop_loss=Decimal("105"),  # > entry_low
            target_1=Decimal("110"),
            confidence_score=70,
            reason="test",
            invalid_condition="x",
        )
        assert False, "should have raised"
    except ValidationError:
        pass


def test_signal_plan_no_trade_allows_nulls():
    from decimal import Decimal

    from app.models.enums import Direction, Market, SignalType
    from app.schemas.signal_schema import SignalPlan

    plan = SignalPlan(
        symbol="NVDA",
        market=Market.US_STOCK,
        direction=Direction.WATCH,
        signal_type=SignalType.NO_TRADE,
        current_price=Decimal("500"),
        confidence_score=10,
        reason="market unclear",
        invalid_condition="when clearer regime emerges",
    )
    assert plan.entry_low is None
    assert plan.stop_loss is None
