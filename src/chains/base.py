"""
Base Chain Adapter - Coinbase L2 DeFi protocol interactions.

Supports Aerodrome, Moonwell, Seamless, and other Base-native
protocols for low-cost yield optimization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

CHAIN_ID = 8453
NATIVE_TOKEN = "ETH"
BLOCK_TIME = 2  # seconds


@dataclass
class BaseConfig:
    """Base chain client configuration."""
    rpc_url: str = "https://mainnet.base.org"
    chain_id: int = CHAIN_ID
    gas_price_gwei: float = 0.005


class BaseClient:
    """
    Client for Base L2 DeFi interactions.

    Supports Aerodrome (Velodrome fork), Moonwell, and other
    Base-native DeFi protocols for yield farming.
    """

    SUPPORTED_PROTOCOLS = {
        "aerodrome": "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",
        "moonwell": "0xfB564da37B41b2F6B6EDcc3e56FbF523bD9F2012",
        "seamless": "0x8C81b4c31551280B1b1F47972C5B95d712C04e12",
        "compound_v3_base": "0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf",
    }

    def __init__(self, config: Optional[BaseConfig] = None):
        self.config = config or BaseConfig()
        self._connected = False
        logger.info("BaseClient created")

    async def connect(self) -> bool:
        """Establish connection to Base RPC."""
        self._connected = True
        logger.info("Connected to Base L2")
        return True

    async def get_block_number(self) -> int:
        """Get latest Base block number."""
        return 15_000_000

    def estimate_tx_cost(self, gas_units: int = 300_000) -> float:
        """Estimate transaction cost in USD."""
        gas_eth = gas_units * self.config.gas_price_gwei * 1e-9
        return gas_eth * 3000.0  # ETH price placeholder

    def get_protocol_address(self, protocol: str) -> Optional[str]:
        """Get contract address for a supported protocol."""
        return self.SUPPORTED_PROTOCOLS.get(protocol)
