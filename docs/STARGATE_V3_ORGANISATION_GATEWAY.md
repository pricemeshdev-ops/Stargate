# STARGATE v3 Organisation Gateway

## Definition

STARGATE v3 is the local user shell for whole-organisation orchestration telemetry.

Mercury is the in-lane authority for STARGATE and attached services. Higher directives may invoke Mercury, but Mercury owns the gateway lane execution posture once invoked.

The user enters one local CLI and can see or route work across:

- USER
- LUCY
- ANUBIS
- SAMAEL
- ODIN
- EUCLID
- MERCURY
- PriceMESH
- PriceSEER
- PriceLIVE/Animal
- StarMail
- StarEye
- Pipeline
- Blog Library
- Google Drive Sync
- locked Epoch 2 legacy gateway reference

## Local Shell, Not Data Authority

STARGATE is allowed to coordinate the organisation from the operator seat.

It is not allowed to:

- redefine PriceMESH truth
- redefine PriceSEER modelling outputs
- redefine PriceLIVE/Animal execution telemetry
- hide source ownership behind one green status
- mutate remote runtime state without a documented live command contract

Each system remains its own Git and runtime authority.

## Epoch 3 First Shape

The first v3 shape is a blank boilerplate:

- shell surfaces exist
- maps and templates exist
- local command grammar exists
- live integrations are disabled
- StarMail service restart is not implemented yet
- no production action is available
- Google Drive sync is operator-controlled through dry-run-first shell scripts

The desktop portal identity is red STARGATE, with a local icon at:

- `assets/stargate-v3-red-inverted-pentagram.svg`

Desktop entry templates:

- `desktop/stargate-v3.desktop`
- `desktop/stargate-v3-starmail.desktop`

Both entries open terminal-backed shell commands. They do not start services.

Runtime topology is presented as:

```text
LIVE / MESH / SEER / ORG
```

This is a gateway shell map. It is not a live runtime assertion.

Primary Desktop portal shell surfaces:

| Surface | Owner | Initial State | Purpose |
| --- | --- | --- | --- |
| USER | USER | SHELL | Operator |
| LUCY | LUCY | SHELL | ORG |
| ANUBIS | ANUBIS | SHELL | LIVE |
| SAMAEL | SAMAEL | SHELL | MESH |
| ODIN | ODIN | SHELL | SEER |
| EUCLID | EUCLID | SHELL | Research |
| MERCURY | MERCURY | SHELL | Gateway |

Runtime topology shell stages:

| Stage | Owner | Initial State | Contract |
| --- | --- | --- | --- |
| LIVE | ANUBIS | SHELL | PriceLIVE / Animal |
| MESH | SAMAEL | SHELL | PriceMESH |
| SEER | ODIN | SHELL | PriceSEER |
| ORG | LUCY | SHELL | PRICEORG |

## Core Operator Contract

The main gateway must always answer:

- What system am I looking at?
- Who owns this surface?
- Is this live, shell, locked, or stale?
- What action is available?
- Is that action read-only, dry-run, or mutating?
- Where is the source of truth?

## Initial Section Contract

| Section | Purpose | Initial State |
| --- | --- | --- |
| Animal Live | live shadow telemetry and future live-key observation | SHELL |
| Animal Reports | result ledgers, state reports, E3I-0001 report contract, shaper outputs | SHELL |
| PriceSEER | modelling and research surfaces | SHELL |
| PriceMESH | upstream truth and publication health | SHELL |
| StarMail | governed mail and diagnostics | SHELL |
| StarEye | read-only replay and SP3-style trade forensics | SHELL |
| Pipeline | cross-system board-truth telemetry | SHELL |
| Blog Library | doctrine, studies, public/internal articles | SHELL |
| Google Drive Sync | My Drive publication and isolated DriveSync exchange | OPERATOR_CONTROLLED |
| Epoch 2 Legacy Gateway | locked saved gateway reference | LOCKED_REFERENCE |

## Google Drive Sync Contract

STARGATE treats Google Drive as an operator file-movement surface, not a source authority.

The main launcher publication lane is one-way:

```text
/home/user/AA-SG-LAUNCHER -> pricemeshdev:AA-SG-LAUNCHER
```

The inbound exchange lane is isolated:

```text
pricemeshdev:DriveSync <-> /home/user/AA-SG-LAUNCHER/DriveSync
```

Drive-originated files must land in `DriveSync` first. Operators review and manually move accepted files into PriceMESH, PriceSEER, PriceLIVE, Library, or STARGATE.
