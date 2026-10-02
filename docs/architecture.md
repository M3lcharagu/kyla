# Architecture

## Agents
Kyla is organized around small, purpose-specific agents. Each agent should have a narrowly defined role, use only the permissions it needs, and pass work through explicit interfaces rather than sharing hidden state.

## Engine
The engine contains the deterministic trading calculations (including EMA and EMA-cross signals) and emits signals for downstream review. It does not make live trades.

## Workflows
Workflow definitions live in `workflows/catalog.yaml`. They describe the intended function and stub status of each agent/workflow; implementations can be added incrementally.

## Approval gates
Require human approval before external side effects, publishing, client-facing commitments, changes to risk settings, or any future trading integration. Keep a pause switch available for alerts and trading-related workflows.

## Secrets
Never commit secrets, credentials, tokens, or private client data to Git. Store real credentials outside the repository and use `config/.env.example` only as a placeholder reference.

## Paper-trading-only rule
Trading functionality is paper-trading-only. Do not connect this project to live brokerage accounts, submit live orders, or enable live trading; any change to this rule requires explicit human review and approval.
