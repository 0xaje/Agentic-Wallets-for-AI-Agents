
"""
AutoYield Agent — main entry point.

Usage:
    python agent.py status          # Print wallet address + balance
    python agent.py fund            # Request Devnet airdrop
    python agent.py run             # Boot, hydrate, execute strategy
    python agent.py run --strategy sweep --vault <ADDR>
    python agent.py reset           # Wipe wallet key file
"""

import sys

from autoyield.cli import main

if __name__ == "__main__":
    sys.exit(main())
