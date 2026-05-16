"""Moving Average Trend strategy per spec § 12.4 model C."""
from decimal import Decimal

from app.models.enums import MarketRegimeEnum
from app.strategies.base import BaseStrategy, StrategyInput, StrategyScore


class MovingAverageTrendStrategy(BaseStrategy):
    name = "ma_trend"

    def score(self, input: StrategyInput) -> StrategyScore:
        candles = input.latest_candles_1d
        ind = input.indicators_1d
        if not candles or len(candles) < 200 or ind is None:
            return self._empty_score(input.asset, "insufficient_data")

        last = candles[-1]
        close = float(last.close)
        ma20 = float(ind.ma20) if ind.ma20 else None
        ma50 = float(ind.ma50) if ind.ma50 else None
        ma200 = float(ind.ma200) if ind.ma200 else None
        atr_pct = float(ind.atr14_pct) if ind.atr14_pct else None

        regime = input.market_regime.regime if input.market_regime else None
        if regime in (MarketRegimeEnum.STRONG_BEAR.value, MarketRegimeEnum.HIGH_VOL_PANIC.value):
            return StrategyScore(
                symbol=input.asset.symbol,
                model_name=self.name,
                suggested_action="AVOID",
                raw_reason=f"regime={regime}",
            )

        ma_stack_ok = ma20 is not None and ma50 is not None and ma200 is not None and ma20 > ma50 > ma200
        above_ma20_or_50 = (ma20 is not None and close > ma20) or (ma50 is not None and close > ma50)

        # Volatility ok: ATR_pct under 1.5x recent average; we don't have rolling average so
        # use a simple absolute cap as fallback.
        vol_ok = atr_pct is None or atr_pct < Decimal("0.06")  # < 6% daily atr

        trend = 0
        if ma_stack_ok:
            trend += 60
        if above_ma20_or_50:
            trend += 40

        setup = 70 if ma_stack_ok and above_ma20_or_50 else 30

        # Risk/reward candidate using ATR-based stop
        atr_value = float(ind.atr14) if ind.atr14 else close * 0.02
        stop = Decimal(str(round(close - atr_value * 2, 6)))
        entry_low = Decimal(str(round(close * 0.998, 6)))
        entry_high = Decimal(str(round(close * 1.002, 6)))
        risk_dist = float(entry_low) - float(stop)
        target_1 = None
        target_2 = None
        rr = 0.0
        if risk_dist > 0:
            target_1 = Decimal(str(round(float(entry_high) + 2 * risk_dist, 6)))
            target_2 = Decimal(str(round(float(entry_high) + 3.5 * risk_dist, 6)))
            rr = (float(target_1) - float(entry_high)) / risk_dist
        rr_score = min(100, int(rr * 50))

        risk_score = 70 if risk_dist > 0 else 20
        volume_score = 50  # not heavily used here
        regime_score = {
            MarketRegimeEnum.STRONG_BULL.value: 100,
            MarketRegimeEnum.MILD_BULL.value: 85,
            MarketRegimeEnum.RANGE.value: 50,
            MarketRegimeEnum.MILD_BEAR.value: 30,
        }.get(regime or "", 50)

        final = int(
            trend * 0.30
            + setup * 0.25
            + (100 if vol_ok else 30) * 0.10
            + regime_score * 0.10
            + rr_score * 0.15
            + risk_score * 0.10
        )
        action = "ENTER" if (ma_stack_ok and above_ma20_or_50 and vol_ok and rr >= 1.5) else "WATCH"

        return StrategyScore(
            symbol=input.asset.symbol,
            model_name=self.name,
            trend_score=trend,
            setup_score=setup,
            risk_score=risk_score,
            volume_score=volume_score,
            market_regime_score=regime_score,
            risk_reward_score=rr_score,
            final_score=final,
            suggested_action=action,
            raw_reason=(
                f"close={close:.2f} ma_stack={ma_stack_ok} above_ma={above_ma20_or_50} "
                f"vol_ok={vol_ok} rr={rr:.2f}"
            ),
            entry_low=entry_low,
            entry_high=entry_high,
            stop_loss=stop,
            target_1=target_1,
            target_2=target_2,
        )
