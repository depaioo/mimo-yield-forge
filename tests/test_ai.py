"""
Tests for AI modules.
"""

import pytest
from src.ai.yield_brain import YieldBrain, YieldPrediction
from src.ai.decision_explainer import DecisionExplainer


class TestYieldBrain:
    def test_initialization(self):
        brain = YieldBrain()
        assert brain.lookback_days == 90

    def test_ingest_and_predict(self):
        brain = YieldBrain()
        import time
        now = time.time()
        timestamps = [now - (30 - i) * 86400 for i in range(30)]
        apys = [0.05 + i * 0.001 for i in range(30)]
        brain.ingest_data("strategy_1", timestamps, apys)
        pred = brain.predict("strategy_1")
        assert pred is not None
        assert pred.strategy_id == "strategy_1"
        assert pred.confidence > 0

    def test_insufficient_data(self):
        brain = YieldBrain()
        brain.ingest_data("strat_1", [1], [0.05])
        assert brain.predict("strat_1") is None

    def test_detect_regime(self):
        brain = YieldBrain()
        regime = brain.detect_regime(market_volatility=0.6, sentiment_score=0.5)
        assert regime.regime_type == "volatile"

    def test_rank_strategies(self):
        brain = YieldBrain()
        import time
        now = time.time()
        for i in range(3):
            ts = [now - (30 - j) * 86400 for j in range(30)]
            apys = [0.05 + i * 0.02 + j * 0.001 for j in range(30)]
            brain.ingest_data(f"strat_{i}", ts, apys)
            brain.predict(f"strat_{i}")
        ranked = brain.rank_strategies()
        assert len(ranked) == 3


class TestDecisionExplainer:
    def test_explain_allocation(self):
        explainer = DecisionExplainer()
        explanation = explainer.explain_allocation(
            strategy_name="Aave USDC",
            weight=0.25,
            apy=0.08,
            risk_level="low",
            factors={"tvl_score": 0.9, "audit_score": 0.95},
        )
        assert "Aave USDC" in explanation.title
        assert len(explanation.reasoning) > 0

    def test_explain_compound(self):
        explainer = DecisionExplainer()
        explanation = explainer.explain_compound("GMX GLP", 50.0, "GLP", 0.30)
        assert "Compound" in explanation.title
        assert explainer.get_history()[-1] == explanation

    def test_format_explanation(self):
        explainer = DecisionExplainer()
        exp = explainer.explain_rebalance("Aave", "GMX", 10000, "Better APY")
        text = explainer.format_explanation(exp)
        assert "Rebalance" in text
        assert "$10,000" in text
