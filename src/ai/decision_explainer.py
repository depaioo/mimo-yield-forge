"""
Decision Explainer - Generates human-readable explanations for AI decisions.

Provides transparency into the yield optimizer's decision-making by
producing natural language explanations of allocation changes, strategy
selections, and risk management actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Explanation:
    """A human-readable explanation of a decision."""
    decision_type: str  # "allocation", "compound", "rebalance", "exit"
    title: str
    summary: str
    reasoning: list[str]
    risk_notes: list[str] = field(default_factory=list)
    confidence: float = 0.0
    alternatives_considered: int = 0


class DecisionExplainer:
    """
    Generates natural language explanations for optimizer decisions.

    Translates internal decision logic into clear, auditable explanations
    that help users understand why specific actions were taken.
    """

    RISK_LABELS = {
        "low": "🟢 Low Risk",
        "medium": "🟡 Medium Risk",
        "high": "🔴 High Risk",
    }

    def __init__(self, verbosity: str = "normal"):
        self.verbosity = verbosity
        self._explanation_history: list[Explanation] = []
        logger.info("DecisionExplainer initialized (verbosity=%s)", verbosity)

    def explain_allocation(
        self,
        strategy_name: str,
        weight: float,
        apy: float,
        risk_level: str,
        factors: dict[str, float],
    ) -> Explanation:
        """Explain why a strategy was given a specific allocation weight."""
        reasoning = [
            f"Strategy '{strategy_name}' offers {apy:.1%} APY",
            f"Risk classification: {self.RISK_LABELS.get(risk_level, risk_level)}",
        ]

        for factor, score in sorted(factors.items(), key=lambda x: x[1], reverse=True):
            reasoning.append(f"  • {factor.replace('_', ' ').title()}: {score:.2f}")

        reasoning.append(f"Target allocation: {weight:.1%} of portfolio")

        risk_notes = []
        if risk_level == "high":
            risk_notes.append("⚠️ High-risk strategy: consider limiting exposure")
        if apy > 0.30:
            risk_notes.append("⚠️ Very high APY may indicate elevated risk")

        explanation = Explanation(
            decision_type="allocation",
            title=f"Allocation: {strategy_name}",
            summary=f"Allocated {weight:.1%} to {strategy_name} yielding {apy:.1%} APY",
            reasoning=reasoning,
            risk_notes=risk_notes,
            confidence=0.85,
            alternatives_considered=len(factors),
        )
        self._explanation_history.append(explanation)
        return explanation

    def explain_rebalance(
        self,
        from_strategy: str,
        to_strategy: str,
        amount_usd: float,
        reason: str,
    ) -> Explanation:
        """Explain a rebalance action."""
        reasoning = [
            f"Moving ${amount_usd:,.0f} from '{from_strategy}' to '{to_strategy}'",
            f"Reason: {reason}",
        ]

        explanation = Explanation(
            decision_type="rebalance",
            title=f"Rebalance: {from_strategy} → {to_strategy}",
            summary=f"Rebalancing ${amount_usd:,.0f} due to {reason.lower()}",
            reasoning=reasoning,
            confidence=0.80,
        )
        self._explanation_history.append(explanation)
        return explanation

    def explain_compound(
        self,
        strategy_name: str,
        reward_amount: float,
        reward_token: str,
        gas_cost: float,
    ) -> Explanation:
        """Explain a compound action."""
        net = reward_amount - gas_cost
        reasoning = [
            f"Harvesting {reward_amount:.4f} {reward_token} from '{strategy_name}'",
            f"Estimated gas cost: ${gas_cost:.2f}",
            f"Net gain after gas: ${net:.2f}",
            f"Reward/gas ratio: {reward_amount / gas_cost:.1f}x (threshold: 3x)",
        ]

        explanation = Explanation(
            decision_type="compound",
            title=f"Compound: {strategy_name}",
            summary=f"Compounding {reward_amount:.4f} {reward_token} (net ${net:.2f})",
            reasoning=reasoning,
            confidence=0.95,
        )
        self._explanation_history.append(explanation)
        return explanation

    def format_explanation(self, explanation: Explanation) -> str:
        """Format an explanation as readable text."""
        lines = [
            f"═══ {explanation.title} ═══",
            f"📋 {explanation.summary}",
            "",
            "Reasoning:",
        ]
        for r in explanation.reasoning:
            lines.append(f"  {r}")

        if explanation.risk_notes:
            lines.append("")
            lines.append("Risk Notes:")
            for note in explanation.risk_notes:
                lines.append(f"  {note}")

        lines.append("")
        lines.append(f"Confidence: {explanation.confidence:.0%}")
        if explanation.alternatives_considered:
            lines.append(f"Alternatives evaluated: {explanation.alternatives_considered}")

        return "\n".join(lines)

    def get_history(self, decision_type: Optional[str] = None) -> list[Explanation]:
        """Get explanation history, optionally filtered by type."""
        if decision_type:
            return [e for e in self._explanation_history if e.decision_type == decision_type]
        return self._explanation_history
