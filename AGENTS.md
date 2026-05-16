# STARGATE v3 Agent Policy

This repository is the Epoch 3 local gateway shell and orchestration template.

## Directory Boundary

Active STARGATE v3 development is confined to:

- `/home/user/AA-SG-LAUNCHER/STARGATE`

Do not edit the locked Epoch 2 STARGATE implementation under `/home/user/PriceSEER` while working in this repo.

## Source of Truth

Git is the source of truth for this repository.

The intended remote is:

- `git@github-stargate:pricemeshdev-ops/Stargate.git`

## Runtime Boundary

This repo starts as a blank gateway boilerplate.

STARGATE is the user-facing local CLI for whole-organisation orchestration telemetry across:

- PriceMESH
- PriceSEER
- PriceLIVE/Animal

It may show, route, and organize telemetry from those systems. It must not silently become the data authority for those systems.

It must not:

- place bets
- execute strategy
- mutate PriceMESH truth
- mutate PriceSEER modelling data
- start or stop real production services
- impersonate locked Epoch 2 runtime state

## Agent Ownership

Mercury is the in-lane authority for STARGATE and its attached services.

Higher authorities may invoke Mercury:

- the user
- Euclid for governed planning cycles
- Odin for supervisory runtime work

Once invoked into the STARGATE lane, Mercury owns the implementation posture, diagnostic routing, service shell behavior, and StarMail/gateway service coordination inside this repository unless the user explicitly overrides that authority.

Mercury owns:

- STARGATE local shell behavior
- StarMail shell design
- mailbox templates
- diagnostic routing templates
- gateway diagnostic presentation
- Google Drive sync command posture
- DriveSync exchange boundary
- future StarMail service restart procedure
- attached STARGATE service templates and restart plans

Odin owns:

- final PriceSEER-facing signoff posture
- supervisory interpretation of runtime board truth
- final user-facing confirmation when this gateway reports PriceSEER state

Euclid owns:

- milestone plans
- doctrine alignment
- cross-repo boundary plans
- Epoch 3 cycle planning

## Gateway Role

STARGATE v3 may coordinate across:

- PriceMESH
- PriceSEER
- PriceLIVE/Animal

It is not the data authority for those repos. Each repo remains its own Git authority.

Mercury is the lane authority for how those repo surfaces are represented, routed, and diagnosed inside the local STARGATE shell.

## Development Rule

Add templates and shell contracts before adding live functions. Every live integration must have:

- owner
- data source
- read/write boundary
- failure mode
- dry-run behavior
- operator command
- test fixture

## ORG Terminal Design Rule

Every new terminal surface must declare its launch geometry:

- fixed-size TUI: provide an opener script that launches the terminal at the intended columns and rows
- responsive TUI: document that it should open in the current or full-screen terminal
- embedded shell: document the parent shell and command route

Desktop shortcuts must call opener scripts for fixed-size TUIs. Do not rely on the desktop default terminal size.

## Google Drive Sync Rule

Google Drive sync is an operator-controlled STARGATE feature.

The launcher publication lane is one-way Local -> My Drive. Do not add pull behavior to the launcher root.

The only approved Drive-to-local ingress lane is:

- `/home/user/AA-SG-LAUNCHER/DriveSync`

Files pulled into `DriveSync` must be reviewed before being moved into PriceMESH, PriceSEER, PriceLIVE, Library, or STARGATE.
