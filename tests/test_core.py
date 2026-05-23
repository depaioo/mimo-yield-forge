"""
Tests for MiMo Yield Forge core modules.
"""

import pytest
import asyncio
from src.forge.aggregator import YieldAggregator, YieldOpportunity, RiskTier
from src.forge.compounder import AutoCompounder, Position
from src.forge.rebalancer import DynamicRebalancer, Allocation
from src.forge.il_calculator import ImpermanentLossCalculator
from src.forge.bridge_optimizer import BridgeOptimizer
from src.forge.tax_reporter import TaxReporter, TaxEvent, TxType
from src.forge.liquidity_analyzer import LiquidityAnalyzer, LiquiditySnapshot


class TestYieldAggregator:
    def test_initialization(self):
        agg = YieldAggregator()
        assert len(agg.chains) == 5
        assert "ethereum" in agg.chains

    def test_get_top_n_empty(self):
        agg = YieldAggregator()
        assert agg.get_top_n(5) == []

    def test_risk_adjusted_apy(self):
        opp = YieldOpportunity(
            protocol="aave", chain="ethereum", pool_address="0x123",
            asset_pair="USDC", apy=0.10, tvl=1_000_000,
            risk_tier=RiskTier.CONSERVATIVE, audit_score=90,
        )
        assert opp.risk_adjusted_apy > 0

    def test_chain_distribution(self):
        agg = YieldAggregator()
        assert agg.get_chain_distribution() == {}


class TestAutoCompounder:
    def test_initialization(self):
        compounder = AutoCompounder()
        assert compounder.gas_multiplier == 3.0

    def test_register_position(self):
        compounder = AutoCompounder()
        pos = Position(
            position_id="pos_1", protocol="aave", chain="ethereum",
            staked_amount=1000, reward_token="AAVE",
            pending_rewards=10, reward_price_usd=100, apy=0.05,
        )
        compounder.register_position(pos)
        assert "pos_1" in compounder._positions

    def test_get_compoundable(self):
        compounder = AutoCompounder(min_compound_value=5.0)
        pos = Position(
            position_id="pos_1", protocol="aave", chain="arbitrum",
            staked_amount=1000, reward_token="ARB",
            pending_rewards=100, reward_price_usd=1.2, apy=0.08,
        )
        compounder.register_position(pos)
        assert len(compounder.get_compoundable_positions()) == 1

    def test_stats(self):
        compounder = AutoCompounder()
        stats = compounder.get_stats()
        assert stats["total_compounds"] == 0


class TestRebalancer:
    def test_compute_weights(self):
        rebalancer = DynamicRebalancer(total_value_usd=100_000)
        allocs = [
            Allocation("s1", "aave", "eth", 0.5, 0.5, 50000, 0.05),
            Allocation("s2", "gmx", "arb", 0.5, 0.5, 50000, 0.15),
        ]
        rebalancer.set_allocations(allocs)
        weights = rebalancer.compute_optimal_weights()
        assert len(weights) == 2
        assert abs(sum(weights) - 1.0) < 0.01


class TestILCalculator:
    def test_no_change(self):
        il = ImpermanentLossCalculator.calculate_il(1.0)
        assert il == 0.0

    def test_2x_price(self):
        il = ImpermanentLossCalculator.calculate_il(2.0)
        assert 0.0 < il < 0.1

    def test_monte_carlo(self):
        calc = ImpermanentLossCalculator(simulation_runs=1000, seed=42)
        result = calc.monte_carlo_il("0x1", "ETH", "USDC", 1.0, 10000)
        assert result.il_percentage >= 0
        assert len(result.confidence_interval) == 2


class TestBridgeOptimizer:
    def test_initialization(self):
        optimizer = BridgeOptimizer()
        assert len(optimizer.SUPPORTED_BRIDGES) > 0

    @pytest.mark.asyncio
    async def test_find_routes(self):
        optimizer = BridgeOptimizer()
        routes = await optimizer.find_routes("ethereum", "arbitrum", "ETH", 1.0)
        assert len(routes) > 0
        assert all(r.fee_usd > 0 for r in routes)


class TestTaxReporter:
    def test_add_event(self):
        reporter = TaxReporter()
        event = TaxEvent(
            timestamp=1700000000, tx_type=TxType.REWARD,
            protocol="aave", chain="ethereum", asset="AAVE",
            amount=10, value_usd=1000,
        )
        reporter.add_event(event)
        summary = reporter.generate_summary()
        assert summary["total_events"] == 1

    def test_export_csv(self):
        reporter = TaxReporter()
        csv = reporter.export_csv()
        assert "Date" in csv
        assert "Type" in csv


class TestLiquidityAnalyzer:
    def test_slippage_estimate(self):
        analyzer = LiquidityAnalyzer()
        snapshot = LiquiditySnapshot(
            pool_address="0x123", protocol="uniswap", chain="ethereum",
            token_a="ETH", token_b="USDC", reserve_a=1000,
            reserve_b=3000000, total_value_usd=6000000,
            volume_24h=500000, fee_tier=0.003,
        )
        analyzer.update_snapshot(snapshot)
        est = analyzer.estimate_slippage("0x123", 10)
        assert est is not None
        assert est.slippage_pct >= 0

    def test_pool_scoring(self):
        analyzer = LiquidityAnalyzer()
        assert analyzer.score_pool("nonexistent") == 0.0
