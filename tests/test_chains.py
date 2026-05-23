"""
Tests for chain adapters and utility modules.
"""

import pytest
from src.chains.ethereum import EthereumClient
from src.chains.arbitrum import ArbitrumClient
from src.chains.base import BaseClient
from src.chains.solana import SolanaClient
from src.chains.bsc import BSCClient
from src.utils.price_feed import PriceFeed
from src.utils.config import ForgeConfig


class TestChainClients:
    @pytest.mark.asyncio
    async def test_ethereum_connect(self):
        client = EthereumClient()
        assert await client.connect()

    @pytest.mark.asyncio
    async def test_arbitrum_connect(self):
        client = ArbitrumClient()
        assert await client.connect()

    @pytest.mark.asyncio
    async def test_base_connect(self):
        client = BaseClient()
        assert await client.connect()

    @pytest.mark.asyncio
    async def test_solana_connect(self):
        client = SolanaClient()
        assert await client.connect()

    @pytest.mark.asyncio
    async def test_bsc_connect(self):
        client = BSCClient()
        assert await client.connect()

    def test_ethereum_protocols(self):
        client = EthereumClient()
        assert client.get_protocol_address("aave_v3") is not None

    def test_gas_estimation(self):
        eth = EthereumClient()
        arb = ArbitrumClient()
        assert arb.estimate_tx_cost() < eth.estimate_tx_cost()


class TestPriceFeed:
    @pytest.mark.asyncio
    async def test_get_price(self):
        feed = PriceFeed()
        price = await feed.get_price("ETH")
        assert price == 3000.0

    @pytest.mark.asyncio
    async def test_get_prices(self):
        feed = PriceFeed()
        prices = await feed.get_prices(["ETH", "BTC"])
        assert "ETH" in prices
        assert "BTC" in prices

    def test_cache(self):
        feed = PriceFeed()
        assert feed.get_cached_price("ETH") is None


class TestForgeConfig:
    def test_from_env(self):
        config = ForgeConfig.from_env()
        assert config.total_capital_usd > 0
        assert len(config.chains) == 5

    def test_validate(self):
        config = ForgeConfig(total_capital_usd=-1)
        warnings = config.validate()
        assert len(warnings) > 0
