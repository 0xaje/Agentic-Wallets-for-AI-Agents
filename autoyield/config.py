"""
Centralized configuration — loads from environment / .env file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    """Load .env from the project root if it exists."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


_load_env()


def _sol_to_lamports(sol: float) -> int:
    return int(sol * 10**9)


@dataclass(frozen=True)
class Config:
    """Immutable configuration snapshot for the agent."""

    rpc_url: str = field(
        default_factory=lambda: os.getenv(
            "AUTOYIELD_RPC_URL", "https://api.devnet.solana.com"
        )
    )
    wallet_file: str = field(
        default_factory=lambda: os.getenv("AUTOYIELD_WALLET_FILE", "agent_state.key")
    )
    passphrase: str | None = field(
        default_factory=lambda: os.getenv("AUTOYIELD_PASSPHRASE") or None
    )
    min_balance_lamports: int = field(
        default_factory=lambda: _sol_to_lamports(
            float(os.getenv("AUTOYIELD_MIN_BALANCE_SOL", "0.5"))
        )
    )
    airdrop_lamports: int = field(
        default_factory=lambda: _sol_to_lamports(
            float(os.getenv("AUTOYIELD_AIRDROP_SOL", "2.0"))
        )
    )
    default_transfer_lamports: int = field(
        default_factory=lambda: _sol_to_lamports(
            float(os.getenv("AUTOYIELD_TRANSFER_SOL", "0.1"))
        )
    )
    rpc_timeout: int = field(
        default_factory=lambda: int(os.getenv("AUTOYIELD_RPC_TIMEOUT", "30"))
    )
    agent_key: str | None = field(
        default_factory=lambda: os.getenv("AUTOYIELD_AGENT_KEY") or None
    )

    def __post_init__(self) -> None:
        if "devnet" not in self.rpc_url.lower():
            raise ValueError(
                f"Safety check failed — RPC URL must target Devnet, got: {self.rpc_url}"
            )
