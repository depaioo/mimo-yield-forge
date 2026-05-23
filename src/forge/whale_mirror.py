"""
Whale Mirror - Tracks large wallet movements for alpha generation.

Monitors whale wallets and smart money addresses to detect early
yield farming rotations, large deposits into protocols, and
coordinated capital movements that signal opportunity.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class WhaleActivity:
    """Represents a tracked whale wallet activity."""
    wallet_address: str
    label: str
    chain: str
    protocol: str
    action: str  # "deposit", "withdraw", "stake", "swap"
    token: str
    amount: float
    value_usd: float
    timestamp: float = field(default_factory=time.time)
    tx_hash: str = ""


@dataclass
class WhaleSignal:
    """Aggregated signal from whale activity."""
    protocol: str
    signal_type: str  # "accumulation", "distribution", "rotation"
    confidence: float
    whale_count: int
    total_value_usd: float
    description: str


class WhaleMirror:
    """
    Monitors whale wallets to detect yield farming opportunities.

    Aggregates activity from known smart money addresses, protocol
    treasuries, and DeFi fund wallets to generate actionable signals
    about capital flows into yield strategies.
    """

    DEFAULT_WHALE_THRESHOLD_USD = 100_000

    def __init__(self, threshold_usd: float = DEFAULT_WHALE_THRESHOLD_USD):
        self.threshold_usd = threshold_usd
        self._tracked_wallets: dict[str, str] = {}  # address -> label
        self._activities: list[WhaleActivity] = []
        self._signals: list[WhaleSignal] = []
        logger.info("WhaleMirror initialized (threshold=$%.0f)", threshold_usd)

    def add_wallet(self, address: str, label: str = "unknown") -> None:
        """Add a whale wallet to track."""
        self._tracked_wallets[address.lower()] = label
        logger.info("Tracking whale: %s (%s)", address[:10], label)

    def add_wallets(self, wallets: dict[str, str]) -> None:
        """Add multiple whale wallets."""
        for addr, label in wallets.items():
            self.add_wallet(addr, label)

    async def scan_recent_activity(self, chain: str, hours: int = 24) -> list[WhaleActivity]:
        """Scan for recent whale activity on a chain."""
        logger.debug("Scanning whale activity on %s (last %dh)", chain, hours)
        await asyncio.sleep(0.1)  # Simulate RPC call
        return [a for a in self._activities if a.chain == chain]

    def record_activity(self, activity: WhaleActivity) -> None:
        """Record a whale activity event."""
        if activity.value_usd >= self.threshold_usd:
            self._activities.append(activity)
            logger.info(
                "Whale event: %s %s %.2f %s on %s ($%.0f)",
                activity.label, activity.action, activity.amount,
                activity.token, activity.protocol, activity.value_usd,
            )

    def detect_signals(self, window_hours: int = 48) -> list[WhaleSignal]:
        """Analyze recent activity for accumulation/distribution signals."""
        cutoff = time.time() - (window_hours * 3600)
        recent = [a for a in self._activities if a.timestamp >= cutoff]

        protocol_activity: dict[str, list[WhaleActivity]] = {}
        for activity in recent:
            protocol_activity.setdefault(activity.protocol, []).append(activity)

        signals = []
        for protocol, activities in protocol_activity.items():
            deposits = sum(a.value_usd for a in activities if a.action == "deposit")
            withdrawals = sum(a.value_usd for a in activities if a.action == "withdraw")

            if deposits > withdrawals * 1.5:
                signals.append(WhaleSignal(
                    protocol=protocol,
                    signal_type="accumulation",
                    confidence=min(0.95, deposits / (deposits + withdrawals)),
                    whale_count=len(set(a.wallet_address for a in activities)),
                    total_value_usd=deposits,
                    description=f"Whales accumulating in {protocol}: ${deposits:,.0f} deposits",
                ))
            elif withdrawals > deposits * 1.5:
                signals.append(WhaleSignal(
                    protocol=protocol,
                    signal_type="distribution",
                    confidence=min(0.95, withdrawals / (deposits + withdrawals)),
                    whale_count=len(set(a.wallet_address for a in activities)),
                    total_value_usd=withdrawals,
                    description=f"Whales exiting {protocol}: ${withdrawals:,.0f} withdrawals",
                ))

        self._signals = signals
        return signals

    def get_stats(self) -> dict:
        """Return whale tracking statistics."""
        return {
            "tracked_wallets": len(self._tracked_wallets),
            "total_activities": len(self._activities),
            "total_signals": len(self._signals),
            "total_volume_usd": round(sum(a.value_usd for a in self._activities), 2),
        }
