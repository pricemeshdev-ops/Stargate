# Organisation Surface Map

## PriceMESH

Role:

- upstream truth
- feed capture
- normalization
- publication
- SP truth material
- PMesh runtime health

STARGATE v3 initial surfaces:

- PriceMESH status shell
- feed truth shell
- publication health shell
- PMesh-to-PriceSEER handoff shell

## PriceSEER

Role:

- downstream modelling
- datasets
- feature weights
- reports
- research surfaces

STARGATE v3 initial surfaces:

- modelling shell
- report index shell
- runtime board truth shell
- Odin signoff shell

## PriceLIVE / Animal

Role:

- live shadow reporting
- result ledger
- state classification
- future live-key observation surfaces

STARGATE v3 initial surfaces:

- Animal Live shell
- Animal Reports shell
- state ledger shell
- shaper report shell
- E3I-0001 report/TUI shell contract: `STARGATE/docs/E3I_0001_REPORT_TUI_CONTRACT.md`

## Cross-System

Shared local operator surfaces:

- StarMail
- StarEye
- Pipeline
- Blog Library
- Google Drive Sync
- legacy Epoch 2 gateway handoff

## Google Drive Sync

Role:

- publish the launcher workspace to My Drive
- expose files to Google Drive and ChatGPT apps
- isolate inbound Drive files before they enter repo surfaces

STARGATE v3 initial surfaces:

- `AA-SG-LAUNCHER` one-way publication shell
- `DriveSync` two-way exchange shell
- dry-run-first rclone command contract
- backup-protected sync operations
