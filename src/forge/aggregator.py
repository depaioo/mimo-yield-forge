"""
Yield Aggregator - Discovers and ranks DeFi yield opportunities across chains.

Scans lending protocols, DEX liquidity pools, staking contracts, and yield
vaults to build a unified opportunity feed ranked by risk-adjusted APY.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.utils.logger import get_logger
from src.utils.price_feed import PriceFeed

logger = get_logger(__name__)


class RiskTier(Enum):
    """Risk classification for yield strategies."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    DEGEN = "degen"


@dataclass
class YieldOpportunity:
    """Represents a single DeFi yield opportunity."""
    protocol: str
    chain: str
    pool_address: str
    asset_pair: str
    apy: float
    tvl: float
    risk_tier: RiskTier
    impermanent_loss_risk: float = 0.0
    audit_score: float = 0.0
    discovered_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    @property
    def risk_adjusted_apy(self) -> float:
        """Calculate APY adjusted for risk factors."""
        risk_penalty = {
            RiskTier.CONSERVATIVE: 0.0,
            RiskTier.MODERATE: 0.05,
            RiskTier.AGGRESSIVE: 0.15,
            RiskTier.DEGEN: 0.35,
        }
        base = self.apy * (1 - risk_penalty[self.risk_tier])
        il_deduction = self.impermanent_loss_risk * 0.5
        audit_bonus = (self.audit_score / 100) * 0.1
        return max(0.0, base - il_deduction + audit_bonus)


class YieldAggregator:
    """
    Aggregates yield opportunities from multiple DeFi protocols and chains.

    Continuously monitors on-chain data, protocol APIs, and governance
    proposals to surface the best risk-adjusted farming opportunities.
    """

    SUPPORTED_PROTOCOLS = [
        "aave", "compound", "uniswap", "curve", "convex",
        "lido", "rocket_pool", "gmx", "velodrome", "aerodrome",
        "pancakeswap", "raydium", "jupiter",
    ]

    def __init__(self, chains: list[str] | None = None, price_feed: Optional[PriceFeed] = None):
        self.chains = chains or ["ethereum", "arbitrum", "base", "bsc", "solana"]
        self.price_feed = price_feed or PriceFeed()
        self._opportunities: list[YieldOpportunity] = []
        self._last_scan: float = 0
        self._scan_interval: float = 300  # 5 minutes
        logger.info("YieldAggregator initialized for chains: %s", self.chains)

    async def scan_all(self) -> list[YieldOpportunity]:
        """Scan all supported chains and protocols for yield opportunities."""
        logger.info("Starting full yield scan across %d chains...", len(self.chains))
        tasks = [self._scan_chain(chain) for chain in self.chains]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        self._opportunities = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Chain scan failed: %s", result)
                continue
            self._opportunities.extend(result)

        self._last_scan = time.time()
        self._opportunities.sort(key=lambda o: o.risk_adjusted_apy, reverse=True)
        logger.info("Scan complete: found %d opportunities", len(self._opportunities))
        return self._opportunities

    async def _scan_chain(self, chain: str) -> list[YieldOpportunity]:
        """Scan a specific chain for yield opportunities."""
        logger.debug("Scanning chain: %s", chain)
        await asyncio.sleep(0.1)  # Simulate async I/O
        return []

    def get_top_n(self, n: int = 10, risk_tier: RiskTier | None = None) -> list[YieldOpportunity]:
        """Return top N opportunities, optionally filtered by risk tier."""
        filtered = self._opportunities
        if risk_tier:
            filtered = [o for o in filtered if o.risk_tier == risk_tier]
        return filtered[:n]

    def filter_by_min_tvl(self, min_tvl: float) -> list[YieldOpportunity]:
        """Filter opportunities by minimum TVL threshold."""
        return [o for o in self._opportunities if o.tvl >= min_tvl]

    def get_chain_distribution(self) -> dict[str, int]:
        """Return count of opportunities per chain."""
        dist: dict[str, int] = {}
        for opp in self._opportunities:
            dist[opp.chain] = dist.get(opp.chain, 0) + 1
        return dist

    @property
    def is_stale(self) -> bool:
        """Check if the opportunity data needs refreshing."""
        return (time.time() - self._last_scan) > self._scan_interval
