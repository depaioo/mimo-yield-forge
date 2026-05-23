"""
Bridge Optimizer - Finds the cheapest and fastest cross-chain bridge routes.

Compares fees, speed, and reliability across bridge protocols to
route assets optimally between chains for yield farming operations.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BridgeRoute:
    """A cross-chain bridge transfer route."""
    bridge_name: str
    source_chain: str
    dest_chain: str
    token: str
    amount: float
    fee_usd: float
    estimated_time_seconds: int
    reliability_score: float  # 0-1
    route_path: list[str] = field(default_factory=list)

    @property
    def cost_efficiency(self) -> float:
        """Score combining cost, speed, and reliability."""
        time_penalty = self.estimated_time_seconds / 3600  # hours
        return self.reliability_score / (self.fee_usd + time_penalty + 0.01)


@dataclass
class BridgeQuote:
    """Quote for a cross-chain transfer."""
    route: BridgeRoute
    input_amount: float
    output_amount: float
    price_impact: float


class BridgeOptimizer:
    """
    Optimizes cross-chain asset transfers for yield farming.

    Maintains a registry of bridge protocols and their capabilities,
    then selects optimal routes based on user preferences for cost,
    speed, or reliability.
    """

    SUPPORTED_BRIDGES = [
        "stargate", "wormhole", "across", "hop", "synapse",
        "celer", "multichain", "layerzero",
    ]

    def __init__(self):
        self._bridge_configs: dict[str, dict] = {}
        self._route_cache: dict[str, list[BridgeRoute]] = {}
        self._initialized = False
        logger.info("BridgeOptimizer created with %d bridges", len(self.SUPPORTED_BRIDGES))

    async def initialize(self) -> None:
        """Load bridge configurations and fee schedules."""
        for bridge in self.SUPPORTED_BRIDGES:
            self._bridge_configs[bridge] = {
                "chains": ["ethereum", "arbitrum", "base", "bsc"],
                "fee_bps": 10,
                "avg_time_s": 600,
                "reliability": 0.98,
            }
        self._initialized = True
        logger.info("BridgeOptimizer initialized")

    async def find_routes(
        self,
        source_chain: str,
        dest_chain: str,
        token: str,
        amount: float,
    ) -> list[BridgeRoute]:
        """Find all available bridge routes for a transfer."""
        if not self._initialized:
            await self.initialize()

        cache_key = f"{source_chain}:{dest_chain}:{token}"
        if cache_key in self._route_cache:
            return self._route_cache[cache_key]

        routes = []
        for name, config in self._bridge_configs.items():
            if source_chain in config["chains"] and dest_chain in config["chains"]:
                fee = amount * config["fee_bps"] / 10_000
                routes.append(BridgeRoute(
                    bridge_name=name,
                    source_chain=source_chain,
                    dest_chain=dest_chain,
                    token=token,
                    amount=amount,
                    fee_usd=round(fee, 2),
                    estimated_time_seconds=config["avg_time_s"],
                    reliability_score=config["reliability"],
                    route_path=[source_chain, dest_chain],
                ))

        routes.sort(key=lambda r: r.cost_efficiency, reverse=True)
        self._route_cache[cache_key] = routes
        logger.info("Found %d routes for %s %s→%s", len(routes), token, source_chain, dest_chain)
        return routes

    async def get_best_route(
        self,
        source_chain: str,
        dest_chain: str,
        token: str,
        amount: float,
        optimize_for: str = "cost",
    ) -> Optional[BridgeRoute]:
        """Get the single best route based on optimization criteria."""
        routes = await self.find_routes(source_chain, dest_chain, token, amount)
        if not routes:
            return None

        sort_keys = {
            "cost": lambda r: r.fee_usd,
            "speed": lambda r: r.estimated_time_seconds,
            "reliability": lambda r: -r.reliability_score,
            "balanced": lambda r: -r.cost_efficiency,
        }
        key_fn = sort_keys.get(optimize_for, sort_keys["balanced"])
        return sorted(routes, key=key_fn)[0]

    async def execute_bridge(self, route: BridgeRoute) -> dict:
        """Execute a bridge transfer (stub)."""
        logger.info("Bridging %.2f %s via %s: %s→%s", route.amount, route.token, route.bridge_name, route.source_chain, route.dest_chain)
        await asyncio.sleep(0.1)
        return {
            "status": "submitted",
            "bridge": route.bridge_name,
            "amount": route.amount,
            "fee": route.fee_usd,
            "estimated_arrival": route.estimated_time_seconds,
        }
