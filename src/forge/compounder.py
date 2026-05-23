"""
Auto-Compounder - Automatically harvests and reinvests yield rewards.

Monitors reward accrual across positions and triggers compound transactions
when the reward amount exceeds the gas cost threshold, maximizing the
benefit of compound interest for DeFi positions.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from src.utils.logger import get_logger
from src.utils.price_feed import PriceFeed

logger = get_logger(__name__)


@dataclass
class CompoundAction:
    """Records a compound event for tracking and reporting."""
    position_id: str
    protocol: str
    chain: str
    reward_token: str
    reward_amount: float
    reward_value_usd: float
    gas_cost_usd: float
    net_gain_usd: float
    timestamp: float = field(default_factory=time.time)
    tx_hash: str = ""


@dataclass
class Position:
    """Represents a DeFi position eligible for auto-compounding."""
    position_id: str
    protocol: str
    chain: str
    staked_amount: float
    reward_token: str
    pending_rewards: float
    reward_price_usd: float
    apy: float
    last_compound: float = 0.0


class AutoCompounder:
    """
    Harvests and reinvests DeFi yield rewards automatically.

    Implements a gas-aware compound strategy that only executes when
    the reward value exceeds a configurable multiple of the estimated
    gas cost, ensuring profitable compounding.
    """

    DEFAULT_GAS_MULTIPLIER = 3.0  # Only compound when reward >= 3x gas cost

    def __init__(
        self,
        price_feed: Optional[PriceFeed] = None,
        gas_multiplier: float = DEFAULT_GAS_MULTIPLIER,
        min_compound_value: float = 10.0,
    ):
        self.price_feed = price_feed or PriceFeed()
        self.gas_multiplier = gas_multiplier
        self.min_compound_value = min_compound_value
        self._positions: dict[str, Position] = {}
        self._compound_history: list[CompoundAction] = []
        self._total_compounded_usd: float = 0.0
        logger.info("AutoCompounder initialized (gas_mult=%.1f, min=$%.2f)", gas_multiplier, min_compound_value)

    def register_position(self, position: Position) -> None:
        """Register a position for auto-compound monitoring."""
        self._positions[position.position_id] = position
        logger.info("Registered position %s on %s (%s)", position.position_id, position.protocol, position.chain)

    def remove_position(self, position_id: str) -> Optional[Position]:
        """Remove a position from monitoring."""
        return self._positions.pop(position_id, None)

    def get_compoundable_positions(self) -> list[Position]:
        """Return positions where compound conditions are met."""
        compoundable = []
        for pos in self._positions.values():
            reward_value = pos.pending_rewards * pos.reward_price_usd
            gas_estimate = self._estimate_gas(pos.chain)
            if reward_value >= gas_estimate * self.gas_multiplier and reward_value >= self.min_compound_value:
                compoundable.append(pos)
        return compoundable

    async def compound_all(self) -> list[CompoundAction]:
        """Execute compound actions for all eligible positions."""
        eligible = self.get_compoundable_positions()
        if not eligible:
            logger.info("No positions meet compound threshold")
            return []

        logger.info("Compounding %d positions...", len(eligible))
        actions = []
        for pos in eligible:
            action = await self._execute_compound(pos)
            if action:
                actions.append(action)
                self._compound_history.append(action)
                self._total_compounded_usd += action.net_gain_usd
        return actions

    async def _execute_compound(self, position: Position) -> Optional[CompoundAction]:
        """Execute a single compound transaction."""
        gas_cost = self._estimate_gas(position.chain)
        reward_value = position.pending_rewards * position.reward_price_usd

        logger.debug(
            "Compounding %s: %.4f %s ($%.2f) [gas=$%.2f]",
            position.position_id, position.pending_rewards,
            position.reward_token, reward_value, gas_cost,
        )
        await asyncio.sleep(0.05)  # Simulate tx

        action = CompoundAction(
            position_id=position.position_id,
            protocol=position.protocol,
            chain=position.chain,
            reward_token=position.reward_token,
            reward_amount=position.pending_rewards,
            reward_value_usd=reward_value,
            gas_cost_usd=gas_cost,
            net_gain_usd=reward_value - gas_cost,
        )
        position.pending_rewards = 0.0
        position.last_compound = time.time()
        return action

    def _estimate_gas(self, chain: str) -> float:
        """Estimate gas cost in USD for a compound transaction on a given chain."""
        gas_estimates = {
            "ethereum": 15.0,
            "arbitrum": 0.30,
            "base": 0.10,
            "bsc": 0.20,
            "solana": 0.01,
        }
        return gas_estimates.get(chain, 5.0)

    def get_stats(self) -> dict:
        """Return compounder statistics."""
        return {
            "active_positions": len(self._positions),
            "total_compounds": len(self._compound_history),
            "total_compounded_usd": round(self._total_compounded_usd, 2),
            "avg_net_gain": (
                round(self._total_compounded_usd / len(self._compound_history), 2)
                if self._compound_history else 0.0
            ),
        }
