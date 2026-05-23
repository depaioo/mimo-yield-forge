"""
Configuration Management - Loads and validates settings.

Supports YAML config files, environment variables, and
programmatic overrides with validation and type coercion.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CONFIG_PATH = "forge_config.yaml"


@dataclass
class ChainConfig:
    """Configuration for a single blockchain."""
    name: str
    rpc_url: str
    chain_id: int = 0
    enabled: bool = True
    gas_limit: int = 500_000


@dataclass
class ForgeConfig:
    """
    Main configuration for the yield optimizer.

    Loads from environment variables with sensible defaults.
    """

    # Capital management
    total_capital_usd: float = 100_000.0
    max_strategies: int = 10
    min_apy_threshold: float = 0.03

    # Risk management
    max_il_tolerance: float = 0.10
    max_single_protocol_exposure: float = 0.30
    max_single_chain_exposure: float = 0.40

    # Compound settings
    auto_compound: bool = True
    compound_gas_multiplier: float = 3.0
    min_compound_value_usd: float = 10.0

    # Rebalance settings
    auto_rebalance: bool = True
    rebalance_threshold: float = 0.05
    rebalance_interval_hours: int = 24

    # Chain configs
    chains: list[ChainConfig] = field(default_factory=list)

    # API keys
    etherscan_api_key: str = ""
    coingecko_api_key: str = ""
    alchemy_api_key: str = ""

    @classmethod
    def from_env(cls) -> "ForgeConfig":
        """Load configuration from environment variables."""
        config = cls(
            total_capital_usd=float(os.getenv("FORGE_CAPITAL", "100000")),
            max_strategies=int(os.getenv("FORGE_MAX_STRATEGIES", "10")),
            min_apy_threshold=float(os.getenv("FORGE_MIN_APY", "0.03")),
            max_il_tolerance=float(os.getenv("FORGE_MAX_IL", "0.10")),
            auto_compound=os.getenv("FORGE_AUTO_COMPOUND", "true").lower() == "true",
            auto_rebalance=os.getenv("FORGE_AUTO_REBALANCE", "true").lower() == "true",
            etherscan_api_key=os.getenv("ETHERSCAN_API_KEY", ""),
            coingecko_api_key=os.getenv("COINGECKO_API_KEY", ""),
            alchemy_api_key=os.getenv("ALCHEMY_API_KEY", ""),
        )

        # Default chain configs
        default_chains = [
            ChainConfig("ethereum", os.getenv("ETH_RPC", "https://eth.llamarpc.com"), 1),
            ChainConfig("arbitrum", os.getenv("ARB_RPC", "https://arb1.arbitrum.io/rpc"), 42161),
            ChainConfig("base", os.getenv("BASE_RPC", "https://mainnet.base.org"), 8453),
            ChainConfig("bsc", os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org"), 56),
            ChainConfig("solana", os.getenv("SOL_RPC", "https://api.mainnet-beta.solana.com"), 0),
        ]
        config.chains = default_chains
        logger.info("Config loaded from environment (capital=$%.0f)", config.total_capital_usd)
        return config

    def validate(self) -> list[str]:
        """Validate configuration and return list of warnings."""
        warnings = []
        if self.total_capital_usd <= 0:
            warnings.append("Total capital must be positive")
        if self.max_strategies < 1:
            warnings.append("Max strategies must be at least 1")
        if self.max_single_chain_exposure > 1.0:
            warnings.append("Max chain exposure capped at 100%")
        return warnings
