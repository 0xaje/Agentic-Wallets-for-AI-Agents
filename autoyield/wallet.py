"""
AgentWallet — autonomous key management, RPC connection, and transaction signing.
Supports optional Fernet encryption for the key file.
"""

from __future__ import annotations

import base64
import hashlib
import os
import time
from pathlib import Path

from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction

from autoyield.config import Config
from autoyield.logger import AgentLogger

# ---------------------------------------------------------------------------
# Optional encryption helpers (graceful degradation if no passphrase)
# ---------------------------------------------------------------------------

def _derive_fernet_key(passphrase: str) -> bytes:
    """Derive a Fernet-compatible key from a human passphrase via SHA-256."""
    from cryptography.fernet import Fernet  # noqa: local import — optional dep

    digest = hashlib.sha256(passphrase.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_key(data: str, passphrase: str) -> str:
    from cryptography.fernet import Fernet

    key = _derive_fernet_key(passphrase)
    return Fernet(key).encrypt(data.encode()).decode()


def _decrypt(token: str, passphrase: str) -> str:
    from cryptography.fernet import Fernet

    key = _derive_fernet_key(passphrase)
    return Fernet(key).decrypt(token.encode()).decode()


# ---------------------------------------------------------------------------
# AgentWallet
# ---------------------------------------------------------------------------

class AgentWallet:
    """Autonomous Solana Devnet wallet with key persistence and retry logic."""

    MAX_AIRDROP_RETRIES = 3
    AIRDROP_BACKOFF_SECS = 5

    def __init__(self, config: Config | None = None, logger: AgentLogger | None = None) -> None:
        self.cfg = config or Config()
        self.log = logger or AgentLogger()
        self.client = Client(self.cfg.rpc_url, timeout=self.cfg.rpc_timeout)
        self.keypair = self._load_or_create_keypair()

    def retry_rpc(self, operation: str, func, *args, **kwargs):
        """Helper to retry RPC calls on transient network failures."""
        for attempt in range(1, 4):  # 3 attempts
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if attempt == 3:
                    raise
                self.log.warn(f"RPC {operation} failed (attempt {attempt}/3): {exc}")
                time.sleep(2 * attempt)  # Simple backoff

    # -- Key Management --------------------------------------------------------

    def _load_or_create_keypair(self) -> Keypair:
        wallet_path = Path(self.cfg.wallet_file)

        if wallet_path.exists():
            self.log.info("Agent waking up from local state...")
            raw = wallet_path.read_text().strip()

            if self.cfg.passphrase:
                try:
                    raw = _decrypt(raw, self.cfg.passphrase)
                    self.log.shield("Key decrypted successfully.")
                except Exception:
                    self.log.error(
                        "Failed to decrypt key file -- wrong passphrase? "
                        "Falling back to reading as plaintext."
                    )
            return Keypair.from_base58_string(raw)

        self.log.seed("Birthing new autonomous agent...")
        kp = Keypair()
        secret = str(kp)

        if self.cfg.passphrase:
            secret = encrypt_key(secret, self.cfg.passphrase)
            self.log.shield("Key encrypted before writing to disk.")
        else:
            self.log.warn(
                "No AUTOYIELD_PASSPHRASE set -- key stored in PLAINTEXT. "
                "Set the env var for encrypted storage."
            )

        wallet_path.write_text(secret)
        self.log.key(f"Wallet key saved to {self.cfg.wallet_file}")
        return kp

    # -- Balance ---------------------------------------------------------------

    @property
    def address(self) -> str:
        return str(self.keypair.pubkey())

    @property
    def balance_lamports(self) -> int:
        res = self.retry_rpc(
            "get_balance", self.client.get_balance, self.keypair.pubkey()
        )
        return res.value

    @property
    def balance_sol(self) -> float:
        return self.balance_lamports / 10**9

    # -- Hydration (Airdrop) ---------------------------------------------------

    def hydrate(self) -> None:
        """Top up the wallet if balance is below the configured threshold."""
        bal = self.balance_lamports
        self.log.hydrate(f"Current liquidity: {bal / 10**9:.4f} SOL")

        if bal >= self.cfg.min_balance_lamports:
            self.log.info("Balance sufficient -- no airdrop needed.")
            return

        for attempt in range(1, self.MAX_AIRDROP_RETRIES + 1):
            try:
                self.log.rain(
                    f"Requesting airdrop (attempt {attempt}/{self.MAX_AIRDROP_RETRIES})..."
                )
                res = self.client.request_airdrop(
                    self.keypair.pubkey(), self.cfg.airdrop_lamports
                )
                # Wait for confirmation
                time.sleep(15)
                self.log.success(f"Hydrated. Signature: {res.value}")
                return
            except Exception as exc:
                self.log.warn(f"Airdrop attempt {attempt} failed: {exc}")
                if attempt < self.MAX_AIRDROP_RETRIES:
                    wait = self.AIRDROP_BACKOFF_SECS * attempt
                    self.log.sleep(f"Backing off {wait}s before retry...")
                    time.sleep(wait)

        self.log.error("All airdrop attempts exhausted. Try again later.")

    # -- Transfers -------------------------------------------------------------

    def transfer(self, target: str, lamports: int | None = None) -> str | None:
        """Sign and send an autonomous SOL transfer. Returns sig or None."""
        lamports = lamports or self.cfg.default_transfer_lamports
        sol = lamports / 10**9

        self.log.action(f"Autonomous transfer -> {target[:8]}..{target[-4:]}  ({sol:.4f} SOL)")

        try:
            receiver = Pubkey.from_string(target)
            ix = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=receiver,
                    lamports=lamports,
                )
            )
            # Fetch latest blockhash and build a signed transaction
            blockhash_res = self.retry_rpc(
                "get_latest_blockhash", self.client.get_latest_blockhash
            )
            blockhash = blockhash_res.value.blockhash
            
            msg = Message([ix], self.keypair.pubkey())
            txn = Transaction([self.keypair], msg, blockhash)
            
            response = self.retry_rpc("send_transaction", self.client.send_transaction, txn)
            sig = str(response.value)
            self.log.target(f"On-chain reality altered: {sig}")
            return sig
        except Exception as exc:
            self.log.error(f"Transfer failed: {exc}")
            return None

    # -- Reset -----------------------------------------------------------------

    def reset(self) -> None:
        """Wipe the key file and forget the current identity."""
        wallet_path = Path(self.cfg.wallet_file)
        if wallet_path.exists():
            wallet_path.unlink()
            self.log.warn(f"Key file {self.cfg.wallet_file} deleted.")
        else:
            self.log.info("No key file to delete.")
