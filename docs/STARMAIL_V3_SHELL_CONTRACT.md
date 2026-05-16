# StarMail v3 Shell Contract

Owner:

- Mercury

Authority:

- Mercury is the in-lane authority for STARGATE StarMail and attached gateway-service behavior.
- Euclid or Odin may invoke Mercury through higher directives.
- Mercury owns the lane implementation posture once invoked unless the user explicitly overrides it.

## Purpose

StarMail v3 is the local governed mail and diagnostics surface for Epoch 3.

It should support future orchestration across PriceMESH, PriceSEER, and PriceLIVE/Animal without waking agents for low-value noise.

Initial Epoch 3 identities:

- USER
- LUCY
- ANUBIS
- SAMAEL
- ODIN
- EUCLID
- MERCURY

Topology label:

```text
LIVE / MESH / SEER / ORG
```

This is a gateway shell map.

StarMail can be opened through the same terminal-backed portal convention as the main gateway:

- shell command: `scripts/starmail`
- desktop template: `desktop/stargate-v3-starmail.desktop`

The desktop template does not start a StarMail service. It opens the local governed queue shell only.

## Draft Queue Surface

StarMail v3 uses a local file-backed store before any service rollover:

```text
STARGATE/runtime/starmail/packets.json
```

This store is not a wake service, not a daemon, not a Betfair connector, and not execution authority. It is a governed local packet queue for operator review.

If the store is missing, the interactive TUI shows an empty queue. Seeding starter packets is an explicit CLI action, not a render side effect.

Minimum columns:

- ID
- Owner
- Priority
- Status
- Subject
- Updated

Command dock:

```text
back  q
```

The screen must clearly state that no live wake service is attached.

## Priority Classes

| Class | Meaning | Wake API/agent |
| --- | --- | --- |
| WAKE | immediate current-path action required | yes |
| QUEUE | actionable but not urgent | no by default |
| MONITOR | visible but not actionable | no |
| ARCHIVE | resolved/stale/duplicate/history | no |

## Required Mail Fields

- thread id
- source system
- target owner
- priority
- status
- fault code
- current-path or historical
- created at
- updated at
- action requested
- latest disposition

## Local Backend

The v3 shell has a local file-backed backend only. Opening the TUI is read-only.

Allowed local actions:

- list packets
- open packet detail
- seed local packet store
- archive local packet

These actions are CLI flags until the interactive TUI implements command parsing.

Blocked actions:

- wake agents
- start or stop services
- inspect secrets
- connect to Betfair
- place, cancel, replace, or submit orders
- grant execution authority

## Service Rollover

Before service restart work begins, Mercury must provide:

- storage path
- process command
- port if any
- restart procedure
- migration plan
- rollback procedure
