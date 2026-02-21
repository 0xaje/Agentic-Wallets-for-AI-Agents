"""
Unit tests for AgentWallet — mocked RPC, no network required.
"""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from autoyield.config import Config
from autoyield.logger import AgentLogger
from autoyield.wallet import AgentWallet, _encrypt, _decrypt


TEST_KEY_FILE = "test_agent_state.key"


class TestConfig(unittest.TestCase):
    """Config validation tests."""

    def test_default_config_is_devnet(self):
        cfg = Config()
        self.assertIn("devnet", cfg.rpc_url.lower())

    def test_mainnet_url_rejected(self):
        with self.assertRaises(ValueError):
            os.environ["AUTOYIELD_RPC_URL"] = "https://api.mainnet-beta.solana.com"
            try:
                Config()
            finally:
                os.environ["AUTOYIELD_RPC_URL"] = "https://api.devnet.solana.com"


class TestEncryption(unittest.TestCase):
    """Fernet encryption/decryption round-trip."""

    def test_round_trip(self):
        secret = "somerandombase58keypairstring"
        passphrase = "test-passphrase-123"
        encrypted = _encrypt(secret, passphrase)
        self.assertNotEqual(encrypted, secret)
        decrypted = _decrypt(encrypted, passphrase)
        self.assertEqual(decrypted, secret)

    def test_wrong_passphrase_fails(self):
        secret = "somerandombase58keypairstring"
        encrypted = _encrypt(secret, "correct-passphrase")
        with self.assertRaises(Exception):
            _decrypt(encrypted, "wrong-passphrase")


class TestAgentWallet(unittest.TestCase):
    """Wallet operations with mocked RPC."""

    def setUp(self):
        # Clean up any leftover key files
        p = Path(TEST_KEY_FILE)
        if p.exists():
            p.unlink()
        os.environ["AUTOYIELD_WALLET_FILE"] = TEST_KEY_FILE
        os.environ.pop("AUTOYIELD_PASSPHRASE", None)

    def tearDown(self):
        p = Path(TEST_KEY_FILE)
        if p.exists():
            p.unlink()
        os.environ.pop("AUTOYIELD_WALLET_FILE", None)

    @patch("autoyield.wallet.Client")
    def test_creates_new_keypair(self, mock_client_cls):
        """First boot creates a new key file."""
        cfg = Config()
        log = AgentLogger(quiet=True)
        wallet = AgentWallet(config=cfg, logger=log)

        self.assertTrue(Path(TEST_KEY_FILE).exists())
        self.assertIsNotNone(wallet.keypair)
        self.assertTrue(len(wallet.address) > 30)

    @patch("autoyield.wallet.Client")
    def test_reloads_existing_keypair(self, mock_client_cls):
        """Second boot reloads the same identity."""
        cfg = Config()
        log = AgentLogger(quiet=True)
        wallet1 = AgentWallet(config=cfg, logger=log)
        addr1 = wallet1.address

        wallet2 = AgentWallet(config=cfg, logger=log)
        self.assertEqual(wallet2.address, addr1)

    @patch("autoyield.wallet.Client")
    def test_encrypted_keypair_round_trip(self, mock_client_cls):
        """Encrypted key creates, persists, and reloads correctly."""
        os.environ["AUTOYIELD_PASSPHRASE"] = "devnet-test-passphrase"
        cfg = Config()
        log = AgentLogger(quiet=True)

        wallet1 = AgentWallet(config=cfg, logger=log)
        addr1 = wallet1.address

        # File should contain encrypted (non-base58) data
        raw = Path(TEST_KEY_FILE).read_text().strip()
        self.assertTrue(raw.startswith("gAAAAA"))  # Fernet token prefix

        wallet2 = AgentWallet(config=cfg, logger=log)
        self.assertEqual(wallet2.address, addr1)

        os.environ.pop("AUTOYIELD_PASSPHRASE", None)

    @patch("autoyield.wallet.Client")
    def test_balance_property(self, mock_client_cls):
        """Balance property calls RPC and returns SOL."""
        mock_instance = mock_client_cls.return_value
        mock_resp = MagicMock()
        mock_resp.value = 2_000_000_000  # 2 SOL
        mock_instance.get_balance.return_value = mock_resp

        cfg = Config()
        wallet = AgentWallet(config=cfg, logger=AgentLogger(quiet=True))

        self.assertAlmostEqual(wallet.balance_sol, 2.0)

    @patch("autoyield.wallet.Client")
    def test_reset_deletes_key_file(self, mock_client_cls):
        """Reset wipes the key file."""
        cfg = Config()
        wallet = AgentWallet(config=cfg, logger=AgentLogger(quiet=True))
        self.assertTrue(Path(TEST_KEY_FILE).exists())

        wallet.reset()
        self.assertFalse(Path(TEST_KEY_FILE).exists())


class TestHydrate(unittest.TestCase):
    """Airdrop retry logic."""

    def setUp(self):
        p = Path(TEST_KEY_FILE)
        if p.exists():
            p.unlink()
        os.environ["AUTOYIELD_WALLET_FILE"] = TEST_KEY_FILE
        os.environ.pop("AUTOYIELD_PASSPHRASE", None)

    def tearDown(self):
        p = Path(TEST_KEY_FILE)
        if p.exists():
            p.unlink()
        os.environ.pop("AUTOYIELD_WALLET_FILE", None)

    @patch("autoyield.wallet.time.sleep")  # skip waits in tests
    @patch("autoyield.wallet.Client")
    def test_hydrate_skips_when_funded(self, mock_client_cls, mock_sleep):
        """No airdrop if balance is above threshold."""
        mock_instance = mock_client_cls.return_value
        mock_resp = MagicMock()
        mock_resp.value = 5_000_000_000  # 5 SOL — well above threshold
        mock_instance.get_balance.return_value = mock_resp

        cfg = Config()
        wallet = AgentWallet(config=cfg, logger=AgentLogger(quiet=True))
        wallet.hydrate()

        mock_instance.request_airdrop.assert_not_called()

    @patch("autoyield.wallet.time.sleep")
    @patch("autoyield.wallet.Client")
    def test_hydrate_retries_on_failure(self, mock_client_cls, mock_sleep):
        """Airdrop retries up to MAX_AIRDROP_RETRIES on failure."""
        mock_instance = mock_client_cls.return_value
        mock_bal = MagicMock()
        mock_bal.value = 0  # Empty wallet
        mock_instance.get_balance.return_value = mock_bal
        mock_instance.request_airdrop.side_effect = Exception("faucet down")

        cfg = Config()
        wallet = AgentWallet(config=cfg, logger=AgentLogger(quiet=True))
        wallet.hydrate()

        self.assertEqual(
            mock_instance.request_airdrop.call_count,
            AgentWallet.MAX_AIRDROP_RETRIES,
        )


if __name__ == "__main__":
    unittest.main()
