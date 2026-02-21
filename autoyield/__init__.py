"""
AutoYield Agent — Weightless Solana Devnet Automation.

import antigravity  # 🎈
"""

__version__ = "0.1.0"

from autoyield.config import Config
from autoyield.wallet import AgentWallet
from autoyield.strategies import RandomTransfer, SweepYield, StrategyRunner
from autoyield.logger import AgentLogger

__all__ = [
    "Config",
    "AgentWallet",
    "RandomTransfer",
    "SweepYield",
    "StrategyRunner",
    "AgentLogger",
]
