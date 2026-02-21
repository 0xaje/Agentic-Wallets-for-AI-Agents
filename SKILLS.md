# AutoYield Agent — Skills Manifest

> A machine-readable skill descriptor for AI agent frameworks.
> Compatible with LangChain tool schemas, Fetch.ai agent protocols, and generic agentic orchestrators.

---

## Agent Identity

| Field | Value |
|---|---|
| **Name** | AutoYield |
| **Version** | 0.1.0 |
| **Runtime** | Python 3.11+ |
| **Network** | Solana Devnet |
| **Entry Point** | `python agent.py <command>` |

---

## Skills

### `check_balance`

**Description:** Returns the agent's current SOL balance on Solana Devnet.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "address": { "type": "string", "description": "Wallet public key (base58)" },
    "balance_sol": { "type": "number", "description": "Balance in SOL" },
    "balance_lamports": { "type": "integer", "description": "Balance in lamports" }
  }
}
```

**CLI:** `python agent.py status`

---

### `request_airdrop`

**Description:** Request a SOL airdrop from the Devnet faucet. Includes automatic retry with exponential backoff.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "amount_sol": {
      "type": "number",
      "description": "Amount of SOL to request (default: 2.0)",
      "default": 2.0
    }
  },
  "required": []
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "signature": { "type": "string", "description": "Airdrop transaction signature" },
    "new_balance_sol": { "type": "number" }
  }
}
```

**CLI:** `python agent.py fund`

---

### `transfer_sol`

**Description:** Sign and send an autonomous SOL transfer to any Solana address.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "target_address": {
      "type": "string",
      "description": "Recipient's base58 public key"
    },
    "amount_lamports": {
      "type": "integer",
      "description": "Amount in lamports (default: 100,000,000 = 0.1 SOL)",
      "default": 100000000
    }
  },
  "required": ["target_address"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "signature": { "type": "string", "description": "Transaction signature" },
    "target": { "type": "string" },
    "amount_sol": { "type": "number" }
  }
}
```

**CLI:** `python agent.py run --strategy random`

---

### `get_address`

**Description:** Returns the agent's wallet public key.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "address": { "type": "string", "description": "Base58-encoded public key" }
  }
}
```

**CLI:** `python agent.py status`

---

### `sweep_yield`

**Description:** Sweep excess balance above a floor threshold to a designated vault address.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "vault_address": {
      "type": "string",
      "description": "Vault recipient base58 public key"
    },
    "floor_sol": {
      "type": "number",
      "description": "Balance floor in SOL (default: 1.0)",
      "default": 1.0
    }
  },
  "required": ["vault_address"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "swept_sol": { "type": "number" },
    "signature": { "type": "string" }
  }
}
```

**CLI:** `python agent.py run --strategy sweep --vault <VAULT_ADDRESS>`

---

## Integration Examples

### LangChain Tool

```python
from langchain.tools import StructuredTool
from autoyield import AgentWallet, Config

wallet = AgentWallet(config=Config())

check_balance = StructuredTool.from_function(
    func=lambda: {"address": wallet.address, "balance_sol": wallet.balance_sol},
    name="check_balance",
    description="Check the agent wallet's SOL balance on Devnet",
)
```

### Fetch.ai uAgent

```python
from uagents import Agent, Context
from autoyield import AgentWallet, Config

agent = Agent(name="autoyield")
wallet = AgentWallet(config=Config())

@agent.on_interval(period=60.0)
async def report_balance(ctx: Context):
    ctx.logger.info(f"Balance: {wallet.balance_sol:.4f} SOL")
```

---

## Environment Requirements

```
Python >= 3.11
solana >= 0.34.0
solders >= 0.21.0
cryptography >= 42.0.0
python-dotenv >= 1.0.0
```
