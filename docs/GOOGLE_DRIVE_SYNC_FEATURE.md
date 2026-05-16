# Google Drive Sync Feature

## Purpose

STARGATE exposes Google Drive sync as an operator file-movement feature for the AA launcher.

The feature has two lanes:

- `AA-SG-LAUNCHER` publication: one-way Local -> My Drive mirror for making the current launcher state available to Google Drive and ChatGPT apps.
- `DriveSync` exchange: isolated two-way folder for manual inbound and outbound file transfer.

## Publication Lane

Local source:

```text
/home/user/AA-SG-LAUNCHER
```

Drive target:

```text
pricemeshdev:AA-SG-LAUNCHER
```

Commands:

```bash
scripts/gdrive-dry-run-push.sh
scripts/gdrive-push.sh
```

Contract:

- Local is the source of truth.
- Drive is a published copy.
- Nothing pulls from Drive into the launcher root.
- Replaced/deleted Drive files are backed up under `_rclone-backups/AA-SG-LAUNCHER/<timestamp>`.
- `DriveSync` is excluded from this mirror.

## DriveSync Exchange Lane

Local exchange folder:

```text
/home/user/AA-SG-LAUNCHER/DriveSync
```

Drive exchange target:

```text
pricemeshdev:DriveSync
```

Pull from Drive into the isolated local folder:

```bash
scripts/drivesync-dry-run-pull.sh
scripts/drivesync-pull.sh
```

Push the isolated local folder back to Drive:

```bash
scripts/drivesync-dry-run-push.sh
scripts/drivesync-push.sh
```

Contract:

- `DriveSync` is the only folder where Drive-originated files may be pulled into the launcher workspace.
- Pulls do not write into PriceMESH, PriceSEER, PriceLIVE, Library, or STARGATE.
- Operators review and manually move accepted files from `DriveSync` into another repo surface.
- Pull and push use `rclone copy`, so empty or partial exchange folders do not delete files on the other side.
- Local overwritten files from pull are backed up under `DriveSync/.rclone-backups/`.
- Drive overwritten files from push are backed up under `_rclone-backups/DriveSync/`.

## Operator Rule

Use the publication lane when the launcher needs to be visible in Google Drive.

Use `DriveSync` when a file needs to travel the other way first.
