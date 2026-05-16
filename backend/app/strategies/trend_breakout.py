"""Trend Breakout strategy per spec § 12.4 model A."""
from decimal import Decimal

from app.models.enums import MarketRegimeEnum
from app.strategies.base import BaseStrategy, StrategyInput, StrategyScore


class TrendBreakoutStrategy(BaseStrategy):
    name = "trend_breakout"

    def score(self, input: StrategyInput) -> StrategyScore:
        candles = input.latest_candles_1d
        ind = input.indicators_1d
        if not candles or len(candles) < 30 or ind is None:
            return self._empty_score(input.asset, "insufficient_data")

        last = candles[-1]
        close = float(last.close)
        prior = candles[-21:-1]  # last 20 bars before today (already-closed)
        if not prior:
            return self._empty_score(input.asset, "insufficient_prior")
        prior_high = max(float(c.high) for c in prior)

        ma20 = float(ind.ma20) if ind.ma20 else None
        ma50 = float(ind.ma50) if ind.ma50 else None
        rsi = float(ind.rsi14) if ind.rsi14 else None
        vol = float(last.volume)
        vol_ma20 = float(ind.volume_ma20) if ind.volume_ma20 else None
        atr = float(ind.atr14) if ind.atr14 else None

        # Hard regime gate
        regime_is_bad = input.market_regime is not None and input.market_regime.regime in (
            MarketRegimeEnum.STRONG_BEAR.value,
            MarketRegimeEnum.HIGH_VOL_PANIC.value,
        )
        if regime_is_bad:
            return StrategyScore(
                symbol=input.asset.symbol,
                model_name=self.name,
                suggested_action="AVOID",
                raw_reason=f"regime={input.market_regime.regime}",
            )

        # Conditions
        broke_high = close > prior_high
        above_ma20 = ma20 is not None and close > ma20
        above_ma50 = ma50 is not None and close > ma50
        volume_strong = vol_ma20 is not None and vol_ma20 > 0 and vol >= vol_ma20 * 1.2
        rsi_ok = rsi is not None and 50 <= rsi <= 75

        # Score components
        trend = 0
        if above_ma20:
            trend += 35
        if above_ma50:
            trend += 30
        if ma20 is not None and ma50 is not None and ma20 > ma50:
            trend += 35

        setup = 0
        if broke_high:
            setup += 60
        if rsi_ok:
            setup += 40

        volume_score = 100 if volume_strong else 40
        regime_score = 80
        if input.market_regime and input.market_regime.regime == MarketRegimeEnum.STRONG_BULL.value:
            regime_score = 100
        elif input.market_regime and input.market_regime.regime == MarketRegimeEnum.MILD_BEAR.value:
            regime_score = 40

        # R/R candidate prices
        entry_high = Decimal(str(round(close * 1.005, 6)))
        entry_low = Decimal(str(round(close * 0.998, 6)))
        # Stop = max(prior 10-bar low, entry - 1.5 * ATR)
        prior_10_low = min(float(c.low) for c in candles[-11:-1]) if len(candles) >= 11 else close * 0.97
        atr_stop = close - 1.5 * (atr or close * 0.02)
        stop = Decimal(str(round(max(prior_10_low, atr_stop), 6)))
        risk_dist = float(entry_low) - float(stop)
        target_1 = Decimal(str(round(float(entry_high) + 2 * risk_dist, 6))) if risk_dist > 0 else None
        target_2 = Decimal(str(round(float(entry_high) + 3 * risk_dist, 6))) if risk_dist > 0 else None

        rr = 0.0
        if risk_dist > 0 and target_1 is not None:
            rr = (float(target_1) - float(entry_high)) / risk_dist
        rr_score = min(100, int(rr * 50))
        risk_score = 60 if risk_dist > 0 and risk_dist / close < 0.05 else 30

        # Final
        final = int(
            trend * 0.25
            + setup * 0.30
            + volume_score * 0.10
            + regime_score * 0.10
            + rr_score * 0.15
            + risk_score * 0.10
        )
        action = "ENTER" if (broke_high and above_ma20 and above_ma50 and rr >= 1.5) else "WATCH"

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
                f"close={close:.2f} prior20H={prior_high:.2f} ma20={ma20} "
                f"vol_strong={volume_strong} rsi={rsi} rr={rr:.2f}"
            ),
            entry_low=entry_low,
            entry_high=entry_high,
            stop_loss=stop,
            target_1=target_1,
            target_2=target_2,
        )
