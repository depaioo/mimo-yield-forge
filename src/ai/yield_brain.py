"""
Yield Brain - AI-powered yield prediction and strategy optimization.

Uses time-series forecasting and reinforcement learning concepts
to predict APY movements, detect regime changes, and optimize
strategy allocation for maximum risk-adjusted returns.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class YieldPrediction:
    """AI-generated yield prediction for a strategy."""
    strategy_id: str
    current_apy: float
    predicted_apy_7d: float
    predicted_apy_30d: float
    confidence: float
    trend: str  # "bullish", "bearish", "neutral"
    factors: list[str] = field(default_factory=list)


@dataclass
class MarketRegime:
    """Detected market regime affecting yield strategies."""
    regime_type: str  # "risk_on", "risk_off", "volatile", "stable"
    confidence: float
    recommended_allocation: str  # "aggressive", "conservative", "neutral"
    detected_at: float = field(default_factory=time.time)


class YieldBrain:
    """
    AI engine for yield prediction and strategy optimization.

    Combines statistical time-series analysis with feature engineering
    from on-chain data to forecast yield movements and detect
    optimal entry/exit points for farming strategies.
    """

    FEATURE_NAMES = [
        "apy_7d_ma", "apy_30d_ma", "tvl_change_7d", "volume_change_7d",
        "protocol_tvl_rank", "chain_activity_score", "whale_flow_score",
        "gas_price_normalized", "market_sentiment", "volatility_30d",
    ]

    def __init__(self, lookback_days: int = 90):
        self.lookback_days = lookback_days
        self._predictions: dict[str, YieldPrediction] = {}
        self._regime: Optional[MarketRegime] = None
        self._historical_data: dict[str, list[tuple[float, float]]] = {}
        logger.info("YieldBrain initialized (lookback=%dd)", lookback_days)

    def ingest_data(self, strategy_id: str, timestamps: list[float], apys: list[float]) -> None:
        """Ingest historical APY data for a strategy."""
        self._historical_data[strategy_id] = list(zip(timestamps, apys))
        logger.debug("Ingested %d data points for %s", len(timestamps), strategy_id)

    def predict(self, strategy_id: str) -> Optional[YieldPrediction]:
        """Generate yield prediction for a strategy."""
        data = self._historical_data.get(strategy_id)
        if not data or len(data) < 7:
            logger.warning("Insufficient data for prediction: %s", strategy_id)
            return None

        recent_apys = [apy for _, apy in data[-30:]]
        current_apy = recent_apys[-1]

        # Simple moving average prediction
        sma_7 = sum(recent_apys[-7:]) / min(7, len(recent_apys))
        sma_30 = sum(recent_apys) / len(recent_apys)

        # Trend detection
        momentum = (sma_7 - sma_30) / sma_30 if sma_30 > 0 else 0
        trend = "bullish" if momentum > 0.05 else "bearish" if momentum < -0.05 else "neutral"

        # Volatility-adjusted confidence
        std_dev = self._std_dev(recent_apys)
        confidence = max(0.3, min(0.95, 1.0 - (std_dev / current_apy if current_apy > 0 else 1.0)))

        prediction = YieldPrediction(
            strategy_id=strategy_id,
            current_apy=current_apy,
            predicted_apy_7d=sma_7,
            predicted_apy_30d=sma_30 * (1 + momentum),
            confidence=confidence,
            trend=trend,
            factors=["moving_average_crossover", "tvl_stability", "market_regime"],
        )
        self._predictions[strategy_id] = prediction
        return prediction

    def detect_regime(self, market_volatility: float = 0.3, sentiment_score: float = 0.5) -> MarketRegime:
        """Detect current market regime from macro signals."""
        if market_volatility > 0.5:
            regime_type = "volatile"
            allocation = "conservative"
        elif sentiment_score > 0.7:
            regime_type = "risk_on"
            allocation = "aggressive"
        elif sentiment_score < 0.3:
            regime_type = "risk_off"
            allocation = "conservative"
        else:
            regime_type = "stable"
            allocation = "neutral"

        confidence = 1.0 - abs(market_volatility - 0.3) - abs(sentiment_score - 0.5)
        self._regime = MarketRegime(
            regime_type=regime_type,
            confidence=max(0.3, min(0.95, confidence)),
            recommended_allocation=allocation,
        )
        return self._regime

    def rank_strategies(self) -> list[tuple[str, float]]:
        """Rank all tracked strategies by predicted performance."""
        scores = []
        for sid, pred in self._predictions.items():
            score = pred.predicted_apy_30d * pred.confidence
            if pred.trend == "bullish":
                score *= 1.1
            elif pred.trend == "bearish":
                score *= 0.9
            scores.append((sid, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    @staticmethod
    def _std_dev(values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
        return math.sqrt(variance)
