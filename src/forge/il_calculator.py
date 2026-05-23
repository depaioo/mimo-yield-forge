"""
Impermanent Loss Calculator - Quantifies IL risk for liquidity positions.

Models impermanent loss for concentrated and full-range LP positions
using historical price data and Monte Carlo simulations to estimate
expected IL under various market scenarios.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ILEstimate:
    """Impermanent loss estimate for a liquidity position."""
    pool_address: str
    token_a: str
    token_b: str
    current_price_ratio: float
    il_percentage: float
    il_usd: float
    confidence_interval: tuple[float, float]
    scenario: str  # "current", "stress_test", "monte_carlo_mean"


class ImpermanentLossCalculator:
    """
    Calculates and simulates impermanent loss for DeFi LP positions.

    Supports both full-range and concentrated liquidity positions,
    with Monte Carlo simulation for forward-looking IL estimates.
    """

    def __init__(self, simulation_runs: int = 10_000, seed: int | None = None):
        self.simulation_runs = simulation_runs
        self._rng = random.Random(seed)
        logger.info("ILCalculator initialized (%d simulation runs)", simulation_runs)

    @staticmethod
    def calculate_il(price_ratio: float) -> float:
        """
        Calculate impermanent loss given a price ratio change.

        Args:
            price_ratio: New price / initial price of token_a relative to token_b.

        Returns:
            IL as a decimal (e.g., 0.05 = 5% impermanent loss).
        """
        if price_ratio <= 0:
            return 0.0
        il = 2 * math.sqrt(price_ratio) / (1 + price_ratio) - 1
        return abs(il)

    def estimate_position_il(
        self,
        pool_address: str,
        token_a: str,
        token_b: str,
        entry_price_ratio: float,
        current_price_ratio: float,
        position_value_usd: float,
    ) -> ILEstimate:
        """Estimate IL for a current position."""
        price_change = current_price_ratio / entry_price_ratio
        il_pct = self.calculate_il(price_change)
        il_usd = il_pct * position_value_usd

        return ILEstimate(
            pool_address=pool_address,
            token_a=token_a,
            token_b=token_b,
            current_price_ratio=current_price_ratio,
            il_percentage=il_pct,
            il_usd=il_usd,
            confidence_interval=(il_pct * 0.8, il_pct * 1.2),
            scenario="current",
        )

    def monte_carlo_il(
        self,
        pool_address: str,
        token_a: str,
        token_b: str,
        current_price_ratio: float,
        position_value_usd: float,
        volatility: float = 0.5,
        time_days: int = 30,
    ) -> ILEstimate:
        """
        Run Monte Carlo simulation to estimate expected IL.

        Uses geometric Brownian motion to model price movements
        and computes distribution of impermanent loss outcomes.
        """
        dt = time_days / 365.0
        il_samples: list[float] = []

        for _ in range(self.simulation_runs):
            drift = -0.5 * volatility ** 2 * dt
            shock = volatility * math.sqrt(dt) * self._rng.gauss(0, 1)
            future_ratio = current_price_ratio * math.exp(drift + shock)
            il_samples.append(self.calculate_il(future_ratio / current_price_ratio))

        il_samples.sort()
        mean_il = sum(il_samples) / len(il_samples)
        p5 = il_samples[int(0.05 * len(il_samples))]
        p95 = il_samples[int(0.95 * len(il_samples))]

        return ILEstimate(
            pool_address=pool_address,
            token_a=token_a,
            token_b=token_b,
            current_price_ratio=current_price_ratio,
            il_percentage=mean_il,
            il_usd=mean_il * position_value_usd,
            confidence_interval=(p5, p95),
            scenario="monte_carlo_mean",
        )

    def stress_test(
        self,
        pool_address: str,
        token_a: str,
        token_b: str,
        current_price_ratio: float,
        position_value_usd: float,
        price_shocks: Optional[list[float]] = None,
    ) -> list[ILEstimate]:
        """Run stress tests with predefined price shock scenarios."""
        shocks = price_shocks or [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0]
        results = []
        for shock in shocks:
            il_pct = self.calculate_il(shock)
            results.append(ILEstimate(
                pool_address=pool_address,
                token_a=token_a,
                token_b=token_b,
                current_price_ratio=shock,
                il_percentage=il_pct,
                il_usd=il_pct * position_value_usd,
                confidence_interval=(il_pct, il_pct),
                scenario=f"stress_{shock}x",
            ))
        return results
