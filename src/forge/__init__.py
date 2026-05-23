"""
MiMo Yield Forge - Core DeFi Optimization Engine
=================================================

Autonomous yield farming optimizer that aggregates opportunities
across multiple chains and protocols, auto-compounds rewards,
and dynamically rebalances portfolios for maximum risk-adjusted returns.
"""

__version__ = "1.0.0"
__author__ = "MiMo Team"

from src.forge.aggregator import YieldAggregator
from src.forge.compounder import AutoCompounder
from src.forge.rebalancer import DynamicRebalancer
from src.forge.il_calculator import ImpermanentLossCalculator
from src.forge.bridge_optimizer import BridgeOptimizer
from src.forge.tax_reporter import TaxReporter
from src.forge.whale_mirror import WhaleMirror
from src.forge.liquidity_analyzer import LiquidityAnalyzer
from src.forge.portfolio_manager import PortfolioManager

__all__ = [
    "YieldAggregator",
    "AutoCompounder",
    "DynamicRebalancer",
    "ImpermanentLossCalculator",
    "BridgeOptimizer",
    "TaxReporter",
    "WhaleMirror",
    "LiquidityAnalyzer",
    "PortfolioManager",
]
