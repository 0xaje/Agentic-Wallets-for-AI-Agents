# AutoYield

AutoYield is a small autonomous agent for the Solana Devnet. It manages its own wallet, handles its own funding via airdrops, and runs simple yield strategies without you having to touch it.

## What is this?

Think of it as a "set and forget" bot for the Solana testing playground. It’s built to demonstrate how an agent can independently sign transactions and manage its balance on-chain. It uses Devnet SOL (test money), so it's completely safe for experimentation.

- **It's independent**: Once it's up, it handles the logic and signing on its own.
- **It's for testing**: Specifically designed for Devnet to get a feel for automated on-chain behavior.
- **It's simple**: No complex UI—just clean logs in your terminal.

## Getting Started

### 1. The Wallet
The agent needs a private key to act as its identity.
- Create a file in the root directory called `agent_state.key`.
- Paste your Solana private key (the base58 string) into that file.

> [!NOTE]
> This file is already in the `.gitignore`, so it won't be pushed to your repo. Keep it private.

### 2. Setup
Install the necessary Python packages:
```bash
pip install -r requirements.txt
```

### 3. Usage
Most of what you'll do is through `agent.py`:

- **Check status**: `python agent.py status` (Shows your address and current SOL)
- **Get funds**: `python agent.py fund` (Asks the Devnet faucet for some test SOL)
- **Run it**: `python agent.py run` (Starts the autonomous loop)
- **Wipe everything**: `python agent.py reset` (Deletes the local key file to start fresh)

If you want to get specific, you can use flags like `--strategy sweep --vault <ADDR>` or set a loop limit with `--rounds 5`.

### 💻 Web Dashboard (Recommended)
You can also monitor and control the agent from a browser:
```bash
python dashboard/app.py
```
Then open `http://localhost:5000` in your browser.

### 🏢 Scaling with Multi-Agent Manager
Want to run multiple agents at once? Use the master orchestrator:
```bash
# Run status for 3 independent agents
python multirun.py --count 3 status

# Run 5 agents concurrently on the random strategy
python multirun.py --count 5 run --rounds 5
```
Each agent will automatically manage its own `.key` file (e.g., `agent_1.key`, `agent_2.key`) to stay independent.

## How it works

The project is split into a few core modules:
- `wallet.py`: The engine that talks to Solana and signs transactions.
- `strategies.py`: Where the actual "behavior" lives (like random transfers).
- `logger.py`: Keeps the terminal output clean and readable.
- `cli.py`: The entry point for all commands.

## Running Tests

If you want to make sure everything is working correctly:
```bash
# Quick local logic tests
python -m pytest tests/test_wallet.py -v

# Live Devnet integration tests (takes a bit longer)
python -m pytest tests/test_harness.py -v
```

## License
MIT
