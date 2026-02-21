"""
Pluggable yield strategies — the agent's decision engine.

Each strategy implements `execute(wallet) -> str` (a human-readable summary).
The StrategyRunner loops through registered strategies on a timer.
"""

from __future__ import annotations

import time
from typing import Protocol, runtime_checkable

from solders.keypair import Keypair

from autoyield.logger import AgentLogger


# ---------------------------------------------------------------------------
# Strategy protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class Strategy(Protocol):
    """Any object with an `execute(wallet) -> str` method is a valid strategy."""

    name: str

    def execute(self, wallet) -> str:  # noqa: ANN001 — avoids circular import
        ...


# ---------------------------------------------------------------------------
# Built-in strategies
# ---------------------------------------------------------------------------

class RandomTransfer:
    """Pick a random throwaway address and send a small SOL amount."""

    name = "random_transfer"

    def __init__(self, lamports: int | None = None) -> None:
        self._lamports = lamports  # None ⇒ use wallet default

    def execute(self, wallet) -> str:
        target = str(Keypair().pubkey())  # Ephemeral address
        sig = wallet.transfer(target, self._lamports)
        return f"Transferred to {target[:8]}… — sig: {sig or 'FAILED'}"


class SweepYield:
    """Transfer excess balance above a floor to a designated vault address."""

    name = "sweep_yield"

    def __init__(self, vault_address: str, floor_lamports: int = 1_000_000_000) -> None:
        self.vault = vault_address
        self.floor = floor_lamports

    def execute(self, wallet) -> str:
        bal = wallet.balance_lamports
        excess = bal - self.floor

        if excess <= 0:
            wallet.log.info(f"Balance {bal / 1e9:.4f} SOL <= floor -- nothing to sweep.")
            return "No excess to sweep."

        # Leave a tiny buffer for tx fees
        sweep_amount = excess - 5_000
        if sweep_amount <= 0:
            return "Excess too small after accounting for fees."

        sig = wallet.transfer(self.vault, sweep_amount)
        swept_sol = sweep_amount / 1e9
        return f"Swept {swept_sol:.4f} SOL to vault — sig: {sig or 'FAILED'}"


# ---------------------------------------------------------------------------
# Strategy runner
# ---------------------------------------------------------------------------

BUILTIN_STRATEGIES = {
    "random": RandomTransfer,
    "sweep": SweepYield,
}


class StrategyRunner:
    """Execute a strategy in a loop with a configurable interval."""

    def __init__(
        self,
        wallet,
        strategy: Strategy,
        interval_secs: int = 30,
        max_rounds: int = 0,  # 0 = infinite
        logger: AgentLogger | None = None,
    ) -> None:
        self.wallet = wallet
        self.strategy = strategy
        self.interval = interval_secs
        self.max_rounds = max_rounds
        self.log = logger or wallet.log

    def run(self) -> None:
        self.log.loop(
            f"Strategy '{self.strategy.name}' engaged — "
            f"interval {self.interval}s, "
            f"{'∞' if self.max_rounds == 0 else self.max_rounds} rounds"
        )
        round_num = 0
        try:
            while True:
                round_num += 1
                self.log.action(f"Round {round_num}")
                result = self.strategy.execute(self.wallet)
                self.log.success(result)

                if self.max_rounds and round_num >= self.max_rounds:
                    self.log.info(f"Completed {self.max_rounds} rounds — stopping.")
                    break

                self.log.sleep(f"Sleeping {self.interval}s …")
                time.sleep(self.interval)

        except KeyboardInterrupt:
            self.log.warn("Interrupted by operator — shutting down gracefully.")
