"""
Portfolio Manager - Top-level orchestration of yield farming operations.

Coordinates the aggregator, compounder, rebalancer, and risk modules
into a unified portfolio management system with automated execution.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from src.forge.aggregator import YieldAggregator, YieldOpportunity, RiskTier
from src.forge.compounder import AutoCompounder
from src.forge.rebalancer import DynamicRebalancer, Allocation
from src.forge.il_calculator import ImpermanentLossCalculator
from src.forge.liquidity_analyzer import LiquidityAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PortfolioConfig:
    """Configuration for the portfolio manager."""
    total_capital_usd: float = 100_000.0
    max_strategies: int = 10
    min_apy: float = 0.05
    max_risk_tier: RiskTier = RiskTier.AGGRESSIVE
    auto_compound: bool = True
    auto_rebalance: bool = True
    rebalance_interval_hours: int = 24
    max_il_tolerance: float = 0.10  # 10%


@dataclass
class PortfolioState:
    """Current state of the managed portfolio."""
    total_value_usd: float = 0.0
    total_yield_earned_usd: float = 0.0
    weighted_apy: float = 0.0
    active_positions: int = 0
    chains_used: int = 0
    uptime_hours: float = 0.0
    last_rebalance: float = 0.0
    last_compound: float = 0.0


class PortfolioManager:
    """
    Orchestrates all yield optimization modules into a unified system.

    Manages the full lifecycle of yield farming: discovery, entry,
    monitoring, compounding, rebalancing, and exit strategies.
    """

    def __init__(self, config: PortfolioConfig):
        self.config = config
        self.aggregator = YieldAggregator()
        self.compounder = AutoCompounder()
        self.rebalancer = DynamicRebalancer(total_value_usd=config.total_capital_usd)
        self.il_calculator = ImpermanentLossCalculator()
        self.liquidity_analyzer = LiquidityAnalyzer()
        self._state = PortfolioState()
        self._start_time = time.time()
        self._running = False
        logger.info("PortfolioManager initialized with $%.0f capital", config.total_capital_usd)

    async def start(self) -> None:
        """Start the automated portfolio management loop."""
        self._running = True
        logger.info("Starting portfolio manager...")
        await self._initial_allocation()

        while self._running:
            await self._tick()
            await asyncio.sleep(60)  # Check every minute

    async def stop(self) -> None:
        """Stop the portfolio manager."""
        self._running = False
        logger.info("Portfolio manager stopped")

    async def _initial_allocation(self) -> None:
        """Perform initial capital allocation across strategies."""
        opportunities = await self.aggregator.scan_all()
        filtered = [
            opp for opp in opportunities
            if opp.risk_adjusted_apy >= self.config.min_apy
            and opp.risk_tier.value <= self.config.max_risk_tier.value
        ][:self.config.max_strategies]

        if not filtered:
            logger.warning("No suitable strategies found for initial allocation")
            return

        weight = 1.0 / len(filtered)
        allocations = [
            Allocation(
                strategy_id=f"{opp.protocol}_{opp.chain}_{opp.pool_address[:8]}",
                protocol=opp.protocol,
                chain=opp.chain,
                target_weight=weight,
                current_weight=0.0,
                current_value_usd=0.0,
                apy=opp.apy,
            )
            for opp in filtered
        ]
        self.rebalancer.set_allocations(allocations)
        logger.info("Initial allocation: %d strategies, weight=%.1f%% each", len(allocations), weight * 100)

    async def _tick(self) -> None:
        """Execute one cycle of portfolio management."""
        now = time.time()

        # Auto-compound check
        if self.config.auto_compound:
            compoundable = self.compounder.get_compoundable_positions()
            if compoundable:
                await self.compounder.compound_all()
                self._state.last_compound = now

        # Auto-rebalance check
        if self.config.auto_rebalance:
            hours_since = (now - self._state.last_rebalance) / 3600
            if hours_since >= self.config.rebalance_interval_hours:
                result = await self.rebalancer.execute_rebalance()
                if result.get("status") == "executed":
                    self._state.last_rebalance = now

        self._state.uptime_hours = (now - self._start_time) / 3600

    def get_state(self) -> PortfolioState:
        """Return current portfolio state."""
        return self._state

    def get_dashboard(self) -> dict:
        """Generate a dashboard-friendly state dictionary."""
        return {
            "total_value_usd": self._state.total_value_usd,
            "yield_earned_usd": self._state.total_yield_earned_usd,
            "weighted_apy": f"{self._state.weighted_apy:.1%}",
            "active_positions": self._state.active_positions,
            "chains_used": self._state.chains_used,
            "uptime_hours": round(self._state.uptime_hours, 1),
            "config": {
                "capital": self.config.total_capital_usd,
                "max_strategies": self.config.max_strategies,
                "auto_compound": self.config.auto_compound,
                "auto_rebalance": self.config.auto_rebalance,
            },
        }
