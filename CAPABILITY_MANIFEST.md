# Capability Manifest Protocol

ACI provides 600+ tools for AI agents. The Capability Manifest Protocol (CC BY 4.0) standardizes how agents declare *what they can do* before receiving work — complementing ACI's tool discovery with verifiable capability statements.

## Why Capability Manifests

ACI's semantic search finds the right tool. A Capability Manifest proves an agent can actually use it:

```
ACI tool discovery    →  "Here's the Gmail send function"
Capability Manifest   →  "This agent is verified to use Gmail send responsibly"
```

## Manifest Structure

```json
{
  "agent_id": "agent-abc123",
  "public_key": "ed25519:...",
  "capabilities": [
    {
      "tool": "gmail_send_email",
      "provider": "aci",
      "verified_at": "2026-05-06T19:00:00Z",
      "constraints": {
        "max_recipients": 50,
        "rate_limit": "100/hour"
      }
    }
  ],
  "signature": "..."
}
```

Each capability entry includes tool identity, verification proof, and optional constraints — so delegating agents know exactly what the tool can and cannot do.

## How It Works with ACI

1. **Agent A wants to delegate** email sending to Agent B
2. **Agent B serves its Capability Manifest** — signed with its Ed25519 key
3. **Agent A verifies** the manifest was signed by Agent B AND that ACI vouches for the tool access
4. **Delegation proceeds** with cryptographic trust, not blind assumption

## Getting Started

The Capability Manifest specification is open source:

- **Spec:** https://workswithagents.com/specs/capability-manifest.md (CC BY 4.0)
- **Python SDK:** `pip install works-with-agents`
- **Reference implementations:** 6 languages

## Related Specs

- [Identity Protocol](https://workswithagents.com/specs/identity.md) — Ed25519 agent identity (required for manifest signing)
- [Trust Score](https://workswithagents.com/specs/trust-score.md) — Agent reputation scoring
- [Onboarding Protocol](https://workswithagents.com/specs/onboarding.md) — Structured agent provisioning
