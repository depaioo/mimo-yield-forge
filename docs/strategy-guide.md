# 📘 MiMo Yield Forge — Strategy Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Risk Profiles](#risk-profiles)
3. [Strategy Selection](#strategy-selection)
4. [Position Sizing](#position-sizing)
5. [Compound Optimization](#compound-optimization)
6. [Rebalancing Rules](#rebalancing-rules)
7. [IL Management](#il-management)
8. [Cross-Chain Bridging](#cross-chain-bridging)

---

## Getting Started

MiMo Yield Forge automates yield farming across 5 blockchains and 13+ DeFi protocols. The system discovers opportunities, manages risk, compounds rewards, and rebalances your portfolio—all without manual intervention.

### Initial Setup

1. Configure RPC endpoints in `.env` for each chain you want to use
2. Set your total capital amount (`FORGE_CAPITAL`)
3. Choose a risk profile (conservative, balanced, aggressive)
4. Define strategies in `examples/sample_strategies.yaml`
5. Start the optimizer

---

## Risk Profiles

### 🟢 Conservative
- **Target APY:** 3–8%
- **Max IL Tolerance:** 5%
- **Protocols:** Blue-chip only (Aave, Compound, Lido, Curve)
- **Chains:** Ethereum mainnet preferred
- Best for: Capital preservation, steady income

### 🟡 Balanced
- **Target APY:** 8–20%
- **Max IL Tolerance:** 10%
- **Protocols:** Mix of blue-chip and mid-tier (GMX, Aerodrome)
- **Chains:** Multi-chain including L2s
- Best for: Growth with managed risk

### 🔴 Aggressive
- **Target APY:** 20%+
- **Max IL Tolerance:** 25%
- **Protocols:** All including newer protocols
- **Chains:** All supported chains
- Best for: Maximum yield, accepts higher risk

---

## Strategy Selection

The aggregator scores strategies on multiple factors:

1. **Risk-Adjusted APY** — APY penalized by risk tier and IL exposure
2. **TVL Score** — Higher TVL = more trust, less rug risk
3. **Audit Score** — Smart contract audit quality
4. **Protocol Track Record** — Historical uptime and exploit history
5. **Whale Activity** — Smart money flow signals

---

## Position Sizing

The liquidity analyzer calculates optimal position size to stay within slippage tolerance:

```
optimal_size = binary_search(max_slippage_pct=1.0)
```

Rules:
- Never exceed 30% of portfolio in a single protocol
- Never exceed 40% on a single chain
- Minimum position: $100 (to justify gas costs)

---

## Compound Optimization

Auto-compound triggers when:

```
reward_value >= gas_cost × gas_multiplier (default: 3x)
```

Chain-specific gas costs:
- Ethereum: ~$15/tx → compound weekly for large positions
- Arbitrum: ~$0.30/tx → compound daily
- Base: ~$0.10/tx → compound every 8 hours
- BSC: ~$0.20/tx → compound daily
- Solana: ~$0.01/tx → compound as often as rewards accrue

---

## Rebalancing Rules

Rebalance triggers when:
1. Any allocation drifts >5% from target weight
2. Scheduled rebalance interval has elapsed (default: 24h)
3. New opportunity significantly outperforms current allocation

The rebalancer minimizes transactions by netting flows between strategies.

---

## IL Management

For LP positions, the IL calculator:
1. Monitors real-time IL exposure
2. Runs Monte Carlo simulations (10K scenarios) for 30-day forward IL
3. Triggers alerts if IL exceeds tolerance
4. Recommends exit when IL + fees < alternative yield

---

## Cross-Chain Bridging

When moving capital between chains:
1. Compare routes across 8 bridge protocols
2. Optimize for cost, speed, or reliability
3. Account for bridge fees in APY calculations
4. Monitor bridge TVL and security track records

---

*For API documentation, see the source code docstrings.*
