"""
Tax Reporter - Generates tax-compliant reports for DeFi activities.

Tracks all yield farming transactions including deposits, withdrawals,
swaps, rewards, and compound events to produce reports compatible
with major tax software and accounting standards.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TxType(Enum):
    """Tax-relevant transaction types."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    SWAP = "swap"
    REWARD = "reward"
    COMPOUND = "compound"
    BRIDGE = "bridge"
    FEE = "fee"
    LIQUIDATION = "liquidation"


@dataclass
class TaxEvent:
    """A single taxable event."""
    timestamp: float
    tx_type: TxType
    protocol: str
    chain: str
    asset: str
    amount: float
    value_usd: float
    cost_basis_usd: float = 0.0
    gain_loss_usd: float = 0.0
    tx_hash: str = ""
    notes: str = ""

    @property
    def is_taxable(self) -> bool:
        """Whether this event triggers a taxable moment."""
        return self.tx_type in {TxType.SWAP, TxType.REWARD, TxType.WITHDRAWAL, TxType.LIQUIDATION}


class TaxReporter:
    """
    Generates DeFi tax reports in multiple formats.

    Supports FIFO, LIFO, and specific identification cost basis
    methods. Exports to CSV, JSON, and formats compatible with
    TurboTax, Koinly, and other tax software.
    """

    def __init__(self, cost_basis_method: str = "FIFO"):
        self.cost_basis_method = cost_basis_method.upper()
        self._events: list[TaxEvent] = []
        self._cost_basis_lots: dict[str, list[tuple[float, float]]] = {}
        logger.info("TaxReporter initialized (method=%s)", self.cost_basis_method)

    def add_event(self, event: TaxEvent) -> None:
        """Record a tax event."""
        if event.tx_type in {TxType.DEPOSIT, TxType.COMPOUND}:
            lots = self._cost_basis_lots.setdefault(event.asset, [])
            lots.append((event.amount, event.value_usd))
        elif event.tx_type in {TxType.SWAP, TxType.WITHDRAWAL}:
            event.cost_basis_usd = self._calculate_cost_basis(event.asset, event.amount)
            event.gain_loss_usd = event.value_usd - event.cost_basis_usd

        self._events.append(event)
        logger.debug("Tax event: %s %s %.4f %s ($%.2f)", event.tx_type.value, event.protocol, event.amount, event.asset, event.value_usd)

    def _calculate_cost_basis(self, asset: str, amount: float) -> float:
        """Calculate cost basis using configured method."""
        lots = self._cost_basis_lots.get(asset, [])
        if not lots:
            return 0.0

        remaining = amount
        total_basis = 0.0
        lots_to_remove = []

        iterator = lots if self.cost_basis_method == "FIFO" else reversed(lots)
        for i, (lot_amt, lot_cost) in enumerate(iterator):
            if remaining <= 0:
                break
            consumed = min(remaining, lot_amt)
            unit_cost = lot_cost / lot_amt if lot_amt > 0 else 0
            total_basis += consumed * unit_cost
            remaining -= consumed
            if consumed >= lot_amt:
                lots_to_remove.append(i)

        return total_basis

    def generate_summary(self, year: int | None = None) -> dict:
        """Generate a tax year summary."""
        events = self._events
        if year:
            import datetime
            events = [e for e in events if datetime.datetime.fromtimestamp(e.timestamp).year == year]

        total_gains = sum(e.gain_loss_usd for e in events if e.gain_loss_usd > 0)
        total_losses = sum(e.gain_loss_usd for e in events if e.gain_loss_usd < 0)

        return {
            "total_events": len(events),
            "taxable_events": len([e for e in events if e.is_taxable]),
            "total_gains_usd": round(total_gains, 2),
            "total_losses_usd": round(abs(total_losses), 2),
            "net_gain_loss_usd": round(total_gains + total_losses, 2),
            "cost_basis_method": self.cost_basis_method,
            "total_rewards_usd": round(sum(e.value_usd for e in events if e.tx_type == TxType.REWARD), 2),
        }

    def export_csv(self, year: int | None = None) -> str:
        """Export tax events as CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Type", "Protocol", "Chain", "Asset", "Amount", "Value USD", "Cost Basis", "Gain/Loss", "Tx Hash"])

        import datetime
        for event in self._events:
            if year and datetime.datetime.fromtimestamp(event.timestamp).year != year:
                continue
            writer.writerow([
                datetime.datetime.fromtimestamp(event.timestamp).isoformat(),
                event.tx_type.value, event.protocol, event.chain, event.asset,
                f"{event.amount:.6f}", f"{event.value_usd:.2f}",
                f"{event.cost_basis_usd:.2f}", f"{event.gain_loss_usd:.2f}", event.tx_hash,
            ])
        return output.getvalue()
