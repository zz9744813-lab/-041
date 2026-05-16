"""Pullback Trend strategy per spec § 12.4 model B."""
from decimal import Decimal

from app.models.enums import MarketRegimeEnum
from app.strategies.base import BaseStrategy, StrategyInput, StrategyScore


class PullbackTrendStrategy(BaseStrategy):
    name = "pullback_trend"

    def score(self, input: StrategyInput) -> StrategyScore:
        candles = input.latest_candles_1d
        ind = input.indicators_1d
        ind4h = input.indicators_4h
        if not candles or len(candles) < 60 or ind is None:
            return self._empty_score(input.asset, "insufficient_data")

        last = candles[-1]
        close = float(last.close)
        ma50 = float(ind.ma50) if ind.ma50 else None
        ema20 = float(ind.ema20) if ind.ema20 else None
        vol = float(last.volume)
        vol_ma20 = float(ind.volume_ma20) if ind.volume_ma20 else None

        regime = input.market_regime.regime if input.market_regime else None
        if regime in (MarketRegimeEnum.STRONG_BEAR.value, MarketRegimeEnum.HIGH_VOL_PANIC.value):
            return StrategyScore(
                symbol=input.asset.symbol,
                model_name=self.name,
                suggested_action="AVOID",
                raw_reason=f"regime={regime}",
            )

        # Pullback conditions
        in_uptrend = ma50 is not None and close > ma50
        near_ema20 = ema20 is not None and abs(close / ema20 - 1) < 0.02
        near_ma50 = ma50 is not None and abs(close / ma50 - 1) < 0.02
        in_pullback_zone = near_ema20 or near_ma50
        volume_quiet = vol_ma20 is not None and vol_ma20 > 0 and vol < vol_ma20

        # 4h stabilization signal: 4h close above 4h ma20
        four_h_stable = False
        if ind4h is not None and ind4h.ma20 is not None and input.latest_candles_4h:
            last4h_close = float(input.latest_candles_4h[-1].close)
            four_h_stable = last4h_close > float(ind4h.ma20)

        trend = 80 if in_uptrend else 30
        setup = 0
        if in_pullback_zone:
            setup += 50
        if four_h_stable:
            setup += 35
        if volume_quiet:
            setup += 15

        # Stop: pullback low - 0.5%
        recent_low = min(float(c.low) for c in candles[-5:])
        stop = Decimal(str(round(recent_low * 0.995, 6)))
        entry_low = Decimal(str(round(close * 0.998, 6)))
        entry_high = Decimal(str(round(close * 1.002, 6)))
        risk_dist = float(entry_low) - float(stop)

        target_1 = None
        target_2 = None
        rr = 0.0
        if risk_dist > 0:
            target_1 = Decimal(str(round(float(entry_high) + 2 * risk_dist, 6)))
            target_2 = Decimal(str(round(float(entry_high) + 3 * risk_dist, 6)))
            rr = (float(target_1) - float(entry_high)) / risk_dist

        rr_score = min(100, int(rr * 50))
        # Risk score: lower if stop is too far
        if risk_dist <= 0 or risk_dist / close > 0.04:
            risk_score = 20
        else:
            risk_score = 80

        regime_score = {
            MarketRegimeEnum.STRONG_BULL.value: 100,
            MarketRegimeEnum.MILD_BULL.value: 90,
            MarketRegimeEnum.RANGE.value: 60,
            MarketRegimeEnum.MILD_BEAR.value: 40,
        }.get(regime or "", 50)

        volume_score = 80 if volume_quiet else 40

        final = int(
            trend * 0.20
            + setup * 0.35
            + risk_score * 0.15
            + regime_score * 0.10
            + rr_score * 0.15
            + volume_score * 0.05
        )
        action = "ENTER" if (in_uptrend and in_pullback_zone and four_h_stable and rr >= 1.5) else "WATCH"

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
                f"close={close:.2f} ma50={ma50} pullback_zone={in_pullback_zone} "
                f"4h_stable={four_h_stable} rr={rr:.2f}"
            ),
            entry_low=entry_low,
            entry_high=entry_high,
            stop_loss=stop,
            target_1=target_1,
            target_2=target_2,
        )
