"""
Liquidity Analyzer - Evaluates pool depth, slippage, and capital efficiency.

Analyzes DEX liquidity pools to estimate execution quality, optimal
position sizing, and capital efficiency metrics for yield strategies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LiquiditySnapshot:
    """Point-in-time liquidity data for a pool."""
    pool_address: str
    protocol: str
    chain: str
    token_a: str
    token_b: str
    reserve_a: float
    reserve_b: float
    total_value_usd: float
    volume_24h: float
    fee_tier: float
    sqrt_price: float = 0.0

    @property
    def utilization_rate(self) -> float:
        """Volume to TVL ratio indicating capital efficiency."""
        return self.volume_24h / self.total_value_usd if self.total_value_usd > 0 else 0.0

    @property
    def estimated_apy(self) -> float:
        """Back-of-envelope APY from fees alone."""
        daily_fees = self.volume_24h * self.fee_tier
        daily_yield = daily_fees / self.total_value_usd if self.total_value_usd > 0 else 0
        return (1 + daily_yield) ** 365 - 1


@dataclass
class SlippageEstimate:
    """Slippage estimate for a trade."""
    input_token: str
    output_token: str
    input_amount: float
    expected_output: float
    actual_output: float
    slippage_pct: float
    price_impact_pct: float


class LiquidityAnalyzer:
    """
    Analyzes DEX liquidity pools for yield optimization.

    Provides depth analysis, slippage estimation, and capital
    efficiency scoring to help select the best pools and optimal
    position sizes for yield farming.
    """

    def __init__(self):
        self._pool_cache: dict[str, LiquiditySnapshot] = {}
        logger.info("LiquidityAnalyzer initialized")

    def update_snapshot(self, snapshot: LiquiditySnapshot) -> None:
        """Cache a pool liquidity snapshot."""
        self._pool_cache[snapshot.pool_address] = snapshot

    def estimate_slippage(
        self,
        pool_address: str,
        input_amount: float,
    ) -> Optional[SlippageEstimate]:
        """Estimate slippage for a trade in a pool using constant-product formula."""
        pool = self._pool_cache.get(pool_address)
        if not pool:
            return None

        # Constant product AMM: x * y = k
        k = pool.reserve_a * pool.reserve_b
        new_reserve_a = pool.reserve_a + input_amount
        new_reserve_b = k / new_reserve_a
        output_amount = pool.reserve_b - new_reserve_b

        spot_price = pool.reserve_b / pool.reserve_a if pool.reserve_a > 0 else 0
        execution_price = output_amount / input_amount if input_amount > 0 else 0
        slippage = abs(spot_price - execution_price) / spot_price if spot_price > 0 else 0

        return SlippageEstimate(
            input_token=pool.token_a,
            output_token=pool.token_b,
            input_amount=input_amount,
            expected_output=input_amount * spot_price,
            actual_output=output_amount,
            slippage_pct=slippage * 100,
            price_impact_pct=slippage * 100,
        )

    def score_pool(self, pool_address: str) -> float:
        """Score a pool from 0-100 based on yield potential and safety."""
        pool = self._pool_cache.get(pool_address)
        if not pool:
            return 0.0

        tvl_score = min(30, math.log10(max(1, pool.total_value_usd)) * 5)
        volume_score = min(30, math.log10(max(1, pool.volume_24h)) * 6)
        utilization_score = min(25, pool.utilization_rate * 500)
        fee_score = min(15, pool.fee_tier * 3000)

        return round(tvl_score + volume_score + utilization_score + fee_score, 1)

    def find_best_pools(
        self,
        chain: str,
        min_tvl: float = 100_000,
        top_n: int = 10,
    ) -> list[tuple[LiquiditySnapshot, float]]:
        """Find and rank the best pools on a chain."""
        candidates = [
            (pool, self.score_pool(pool.pool_address))
            for pool in self._pool_cache.values()
            if pool.chain == chain and pool.total_value_usd >= min_tvl
        ]
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_n]

    def optimal_position_size(
        self,
        pool_address: str,
        max_slippage_pct: float = 1.0,
    ) -> Optional[float]:
        """Find the maximum position size within slippage tolerance."""
        pool = self._pool_cache.get(pool_address)
        if not pool:
            return None

        # Binary search for optimal size
        low, high = 0.0, pool.total_value_usd * 0.1
        for _ in range(50):
            mid = (low + high) / 2
            est = self.estimate_slippage(pool_address, mid)
            if est and est.slippage_pct <= max_slippage_pct:
                low = mid
            else:
                high = mid
        return round(low, 2)
