# Google Drive Sync Rollout

## Status

Implemented as an operator-controlled STARGATE feature.

## Remote

Configured rclone remote:

```text
pricemeshdev:
```

Google account:

```text
pricemeshdev@gmail.com
```

Current Drive mode:

```text
My Drive
```

Shared Drive is not required for this rollout.

## Rollout Steps

1. Confirm rclone authentication.

```bash
rclone lsd pricemeshdev:
```

2. Publish launcher to My Drive using a dry-run first.

```bash
scripts/gdrive-dry-run-push.sh
scripts/gdrive-push.sh
```

3. Confirm Google Drive contains:

```text
My Drive / AA-SG-LAUNCHER
```

4. Use `DriveSync` for inbound file exchange.

```bash
scripts/drivesync-dry-run-pull.sh
scripts/drivesync-pull.sh
```

5. Use `DriveSync` for outbound exchange files.

```bash
scripts/drivesync-dry-run-push.sh
scripts/drivesync-push.sh
```

## Acceptance Criteria

- `AA-SG-LAUNCHER` appears in My Drive after publication.
- `DriveSync` can be pulled without writing outside `/home/user/AA-SG-LAUNCHER/DriveSync`.
- `DriveSync` can be pushed without changing the main `AA-SG-LAUNCHER` mirror.
- Every destructive sync path has a backup directory.
- Dry-run commands exist for every mutating command.
- `DriveSync` uses copy semantics and does not delete opposite-side files.

## Rollback

For publication mistakes, recover replaced Drive files from:

```text
pricemeshdev:_rclone-backups/AA-SG-LAUNCHER/
```

For DriveSync pull mistakes, recover local files from:

```text
/home/user/AA-SG-LAUNCHER/DriveSync/.rclone-backups/
```

For DriveSync push mistakes, recover Drive files from:

```text
pricemeshdev:_rclone-backups/DriveSync/
```
