# STARGATE v3 Organisation Gateway

## Definition

STARGATE v3 is the local user shell for whole-organisation orchestration telemetry.

Mercury is the in-lane authority for STARGATE and attached services. Higher directives may invoke Mercury, but Mercury owns the gateway lane execution posture once invoked.

The user enters one local CLI and can see or route work across:

- PriceMESH
- PriceSEER
- PriceLIVE/Animal
- StarMail
- StarEye
- Pipeline
- Blog Library
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
| Animal Reports | result ledgers, state reports, shaper outputs | SHELL |
| PriceSEER | modelling and research surfaces | SHELL |
| PriceMESH | upstream truth and publication health | SHELL |
| StarMail | governed mail and diagnostics | SHELL |
| StarEye | read-only replay and SP3-style trade forensics | SHELL |
| Pipeline | cross-system board-truth telemetry | SHELL |
| Blog Library | doctrine, studies, public/internal articles | SHELL |
| Epoch 2 Legacy Gateway | locked saved gateway reference | LOCKED_REFERENCE |
