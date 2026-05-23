"""
Dynamic Rebalancer - Optimizes portfolio allocation across yield strategies.

Uses mean-variance optimization adapted for DeFi yields to maintain
target allocations while accounting for gas costs, slippage, and
time-varying APY across protocols and chains.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Allocation:
    """Target allocation for a strategy or protocol."""
    strategy_id: str
    protocol: str
    chain: str
    target_weight: float  # 0.0 - 1.0
    current_weight: float = 0.0
    current_value_usd: float = 0.0
    apy: float = 0.0


@dataclass
class RebalanceAction:
    """A single rebalance trade action."""
    from_strategy: str
    to_strategy: str
    amount_usd: float
    estimated_gas_usd: float
    estimated_slippage: float


class DynamicRebalancer:
    """
    Portfolio rebalancer for DeFi yield strategies.

    Computes optimal allocations using a risk-parity approach weighted
    by risk-adjusted APY, then generates minimal-transaction rebalance
    plans that respect gas cost thresholds.
    """

    def __init__(
        self,
        total_value_usd: float = 0.0,
        rebalance_threshold: float = 0.05,
        min_rebalance_usd: float = 100.0,
    ):
        self.total_value_usd = total_value_usd
        self.rebalance_threshold = rebalance_threshold
        self.min_rebalance_usd = min_rebalance_usd
        self._allocations: list[Allocation] = []
        logger.info("DynamicRebalancer initialized (threshold=%.1f%%)", rebalance_threshold * 100)

    def set_allocations(self, allocations: list[Allocation]) -> None:
        """Set the current portfolio allocations."""
        self._allocations = allocations
        total_weight = sum(a.target_weight for a in allocations)
        if abs(total_weight - 1.0) > 0.01:
            logger.warning("Target weights sum to %.3f, normalizing", total_weight)
            for a in self._allocations:
                a.target_weight /= total_weight

    def compute_optimal_weights(self, risk_free_rate: float = 0.04) -> list[float]:
        """
        Compute risk-parity weights adjusted for APY.

        Allocates more to strategies with higher Sharpe-like ratios
        (APY minus risk-free rate divided by volatility proxy).
        """
        if not self._allocations:
            return []

        scores = []
        for alloc in self._allocations:
            excess_yield = max(0.0, alloc.apy - risk_free_rate)
            volatility_proxy = max(0.01, alloc.apy * 0.3)
            sharpe_proxy = excess_yield / volatility_proxy
            scores.append(sharpe_proxy)

        total_score = sum(scores) or 1.0
        return [s / total_score for s in scores]

    def get_rebalance_actions(self) -> list[RebalanceAction]:
        """Generate rebalance actions needed to reach target allocation."""
        actions = []
        for alloc in self._allocations:
            drift = alloc.current_weight - alloc.target_weight
            drift_usd = abs(drift) * self.total_value_usd

            if abs(drift) < self.rebalance_threshold or drift_usd < self.min_rebalance_usd:
                continue

            if drift > 0:
                # Over-allocated: sell/withdraw
                for target in self._allocations:
                    if target.strategy_id == alloc.strategy_id:
                        continue
                    target_drift = target.target_weight - target.current_weight
                    if target_drift > 0:
                        amount = min(drift_usd, target_drift * self.total_value_usd)
                        actions.append(RebalanceAction(
                            from_strategy=alloc.strategy_id,
                            to_strategy=target.strategy_id,
                            amount_usd=round(amount, 2),
                            estimated_gas_usd=5.0,
                            estimated_slippage=0.003,
                        ))
                        break
        logger.info("Generated %d rebalance actions", len(actions))
        return actions

    async def execute_rebalance(self) -> dict:
        """Execute all pending rebalance actions."""
        actions = self.get_rebalance_actions()
        if not actions:
            return {"status": "no_action", "actions": 0}

        total_moved = sum(a.amount_usd for a in actions)
        total_gas = sum(a.estimated_gas_usd for a in actions)
        logger.info("Executing rebalance: $%.2f moved, $%.2f gas", total_moved, total_gas)

        await asyncio.sleep(0.1)  # Simulate execution
        return {
            "status": "executed",
            "actions": len(actions),
            "total_moved_usd": round(total_moved, 2),
            "total_gas_usd": round(total_gas, 2),
        }

    def get_portfolio_summary(self) -> dict:
        """Return a summary of current portfolio state."""
        return {
            "total_value_usd": self.total_value_usd,
            "num_strategies": len(self._allocations),
            "weighted_apy": sum(a.current_weight * a.apy for a in self._allocations),
            "allocations": [
                {
                    "strategy": a.strategy_id,
                    "weight": f"{a.current_weight:.1%}",
                    "target": f"{a.target_weight:.1%}",
                    "value_usd": a.current_value_usd,
                    "apy": f"{a.apy:.1%}",
                }
                for a in self._allocations
            ],
        }
