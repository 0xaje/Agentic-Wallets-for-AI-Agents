"""
CLI entry point -- argparse-based subcommands for the AutoYield Agent.
"""

from __future__ import annotations

import argparse
import sys

from autoyield.config import Config
from autoyield.logger import AgentLogger
from autoyield.wallet import AgentWallet
from autoyield.strategies import (
    BUILTIN_STRATEGIES,
    RandomTransfer,
    SweepYield,
    StrategyRunner,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autoyield",
        description="""
AutoYield Agent — Solana Devnet Automation.
"""
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress informational output"
    )
    parser.add_argument(
        "--rpc-url", default=None, help="Override Solana RPC endpoint"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # -- run -------------------------------------------------------------------
    run_p = sub.add_parser("run", help="Boot agent, hydrate, and execute strategy loop")
    run_p.add_argument(
        "--strategy",
        choices=list(BUILTIN_STRATEGIES.keys()),
        default="random",
        help="Strategy to execute (default: random)",
    )
    run_p.add_argument(
        "--rounds",
        type=int,
        default=1,
        help="Number of strategy rounds (0 = infinite)",
    )
    run_p.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconds between rounds (default: 30)",
    )
    run_p.add_argument(
        "--vault",
        default=None,
        help="Vault address for sweep_yield strategy",
    )

    # -- status ----------------------------------------------------------------
    sub.add_parser("status", help="Print wallet address and balance")

    # -- fund ------------------------------------------------------------------
    sub.add_parser("fund", help="Request a Devnet airdrop")

    # -- reset -----------------------------------------------------------------
    sub.add_parser("reset", help="Wipe wallet key file and start fresh")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    log = AgentLogger(quiet=args.quiet)

    # Build config, optionally overriding RPC URL
    import os
    if args.rpc_url:
        os.environ["AUTOYIELD_RPC_URL"] = args.rpc_url
    cfg = Config()

    if args.command == "reset":
        # Reset doesn't need a wallet object -- just delete the key file
        from pathlib import Path

        wallet_path = Path(cfg.wallet_file)
        if wallet_path.exists():
            wallet_path.unlink()
            log.warn(f"Key file '{cfg.wallet_file}' deleted.")
        else:
            log.info("No key file found -- nothing to reset.")
        return 0

    # All other commands need a wallet
    log.boot("--- Booting AutoYield Protocol ---")
    wallet = AgentWallet(config=cfg, logger=log)
    log.boot(f"Identity: {wallet.address}")

    if args.command == "status":
        log.hydrate(f"Balance: {wallet.balance_sol:.4f} SOL")
        return 0

    if args.command == "fund":
        wallet.hydrate()
        log.hydrate(f"Post-fund balance: {wallet.balance_sol:.4f} SOL")
        return 0

    if args.command == "run":
        wallet.hydrate()

        # Resolve strategy
        if args.strategy == "sweep":
            if not args.vault:
                log.error("--vault is required for sweep_yield strategy.")
                return 1
            strategy = SweepYield(vault_address=args.vault)
        else:
            strategy = RandomTransfer()

        runner = StrategyRunner(
            wallet=wallet,
            strategy=strategy,
            interval_secs=args.interval,
            max_rounds=args.rounds,
            logger=log,
        )
        runner.run()
        return 0

    return 0
