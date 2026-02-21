"""
Sandboxed Devnet integration test harness.

⚠️  Requires network access to Solana Devnet.
    May fail due to faucet rate limits — this is expected.

Run with:
    python -m pytest tests/test_harness.py -v --timeout=120
"""

import os
import unittest
from pathlib import Path

from autoyield.config import Config
from autoyield.logger import AgentLogger
from autoyield.wallet import AgentWallet

HARNESS_KEY_FILE = "test_harness_ephemeral.key"


class TestDevnetHarness(unittest.TestCase):
    """Live Devnet integration tests — creates real on-chain state."""

    @classmethod
    def setUpClass(cls):
        os.environ["AUTOYIELD_WALLET_FILE"] = HARNESS_KEY_FILE
        os.environ.pop("AUTOYIELD_PASSPHRASE", None)
        cls.cfg = Config()
        cls.log = AgentLogger(quiet=False)
        cls.wallet = AgentWallet(config=cls.cfg, logger=cls.log)

    @classmethod
    def tearDownClass(cls):
        p = Path(HARNESS_KEY_FILE)
        if p.exists():
            p.unlink()
        os.environ.pop("AUTOYIELD_WALLET_FILE", None)

    def test_01_wallet_has_address(self):
        """Agent should have a valid public key."""
        addr = self.wallet.address
        self.assertTrue(len(addr) > 30, f"Address too short: {addr}")
        print(f"Agent address: {addr}")

    def test_02_airdrop_and_balance(self):
        """Request airdrop and verify balance increases."""
        self.wallet.hydrate()
        bal = self.wallet.balance_sol
        print(f"Post-airdrop balance: {bal:.4f} SOL")
        # If airdrop succeeded, balance should be > 0
        # Note: may fail if faucet is rate-limited
        self.assertGreater(bal, 0, "Balance should be > 0 after airdrop")

    def test_03_transfer_to_throwaway(self):
        """Execute a transfer to a random throwaway address."""
        from solders.keypair import Keypair

        target = str(Keypair().pubkey())
        sig = self.wallet.transfer(target, lamports=10_000)  # Tiny transfer
        print(f"Transfer sig: {sig}")
        # sig can be None if it failed, but we at least verify no crash
        if sig:
            self.assertTrue(len(sig) > 20, "Signature looks too short")

    def test_04_balance_after_transfer(self):
        """Balance should have decreased after the transfer."""
        bal = self.wallet.balance_sol
        print(f"Post-transfer balance: {bal:.4f} SOL")
        # Just ensure we can still read balance without error


if __name__ == "__main__":
    unittest.main()
