# 🏦 MiMo Yield Forge

**Autonomous DeFi Yield Optimizer powered by MiMo 100T**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

MiMo Yield Forge is an intelligent, multi-chain yield farming optimizer that automatically discovers, evaluates, and manages DeFi yield strategies across Ethereum, Arbitrum, Base, BSC, and Solana.

## ✨ Key Features

- **🔍 Yield Aggregation** — Scans 13+ protocols across 5 chains for the best risk-adjusted yields
- **🔄 Auto-Compounding** — Gas-aware harvest & reinvest when reward > 3x gas cost
- **📊 Dynamic Rebalancing** — Risk-parity allocation with minimal-transaction rebalancing
- **📈 IL Calculator** — Monte Carlo simulation for impermanent loss estimation
- **🌉 Bridge Optimizer** — Cross-chain routing with cost/speed/reliability optimization
- **🐋 Whale Mirror** — Smart money tracking for alpha generation
- **🧠 AI Yield Brain** — ML-powered yield prediction and regime detection
- **📋 Tax Reporter** — FIFO/LIFO cost basis with CSV export

## Architecture

```
src/
├── forge/           # Core optimization engine
│   ├── aggregator.py      # Yield opportunity scanner
│   ├── compounder.py      # Auto-compound with gas awareness
│   ├── rebalancer.py      # Dynamic portfolio rebalancing
│   ├── il_calculator.py   # Impermanent loss modeling
│   ├── bridge_optimizer.py # Cross-chain bridge routing
│   ├── tax_reporter.py    # Tax event tracking & reporting
│   ├── whale_mirror.py    # Whale activity monitoring
│   ├── liquidity_analyzer.py # Pool depth & slippage analysis
│   └── portfolio_manager.py  # Top-level orchestration
├── ai/              # Machine learning modules
│   ├── yield_brain.py     # Yield prediction engine
│   └── decision_explainer.py # Human-readable AI explanations
├── chains/          # Multi-chain adapters
│   ├── ethereum.py        # Ethereum mainnet
│   ├── arbitrum.py        # Arbitrum L2
│   ├── base.py            # Base L2
│   ├── solana.py          # Solana
│   └── bsc.py             # BNB Smart Chain
└── utils/           # Shared utilities
    ├── price_feed.py      # Multi-source price oracle
    ├── config.py          # Configuration management
    └── logger.py          # Structured logging
```

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/dipeknosybil/mimo-yield-forge.git
cd mimo-yield-forge

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your RPC URLs and API keys

# Run tests
make test

# Start the optimizer
python -m src.forge.portfolio_manager
```

## ⚙️ Configuration

Copy `.env.example` to `.env` and configure:

```env
FORGE_CAPITAL=100000       # Total capital in USD
FORGE_MAX_STRATEGIES=10    # Max concurrent strategies
ETH_RPC=https://...        # Ethereum RPC endpoint
ARB_RPC=https://...        # Arbitrum RPC endpoint
```

## 📊 Supported Protocols

| Chain | Protocols |
|-------|-----------|
| Ethereum | Aave V3, Compound V3, Uniswap V3, Lido, Curve |
| Arbitrum | GMX, Camelot, Radiant, Aave V3 |
| Base | Aerodrome, Moonwell, Seamless, Compound V3 |
| BSC | PancakeSwap V3, Venus, Alpaca, Thena |
| Solana | Jupiter, Raydium, Marinade, Orca |

## 🧪 Testing

```bash
make test          # Run all tests
make coverage      # Run with coverage report
make lint          # Run linters
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

*Built with ❤️ by the MiMo Team*
