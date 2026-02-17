<!-- name: Troubleshooting — Diagnostics & Edge Cases -->
<!-- description: Metadata stalls, stalled queues, dead torrent detection, storage checks, empty responses -->

# Troubleshooting — Diagnostics & Edge Cases

## Metadata Stall (Magnet Links Can't Connect)

**Symptom:** Items stuck in Sonarr/Radarr queue with 0 progress indefinitely.

**Detect in qBittorrent:**
```bash
api-call qbt GET /torrents/info | jq '[.[] | select(.total_size == -1)]'
```
You'll see: state `metaDL`/`queuedDL`, total_size `-1`, num_seeds `0`, progress `0`.

**Sonarr/Radarr queue is misleading:** shows `trackedDownloadStatus: "ok"` and `trackedDownloadState: "downloading"` even when stuck. Empty `statusMessages`.

**Decision tree:**
1. `num_complete == 0` in swarm → **Dead torrent** (no seeders anywhere)
2. `num_complete > 0` but `num_seeds == 0` → **Network issue** (VPN/firewall)
3. `time_active > 300` (5 min) with no metadata → Give up, search again

**Fix:**
1. Delete stuck torrent: `api-call qbt POST /torrents/delete -d '{"hashes":"HASH","deleteFiles":"false"}'`
2. Trigger new search in Sonarr/Radarr for a different release
3. If multiple torrents stuck, check VPN/tracker connectivity

## Sonarr Queue "Okay" But Nothing Downloads

**Symptom:** `/queue/status` shows no errors, but `/queue` is full of 0-byte items.

**Expose the truth:**
```bash
api-call sonarr GET /queue/status && api-call sonarr GET /queue | jq '[.records[] | select(.size == 0)] | length'
```
`/queue/status` reports `errors: false, warnings: false` while hundreds of items are stuck.

**Fix:** Use qBittorrent as source of truth for download health, not Sonarr queue.

## Identify Truly Dead Torrents vs Network Issues
```bash
api-call qbt GET /torrents/info | jq '[.[] | select(.total_size == -1) | {name: .name, hash: .hash, num_complete: .num_complete, num_seeds: .num_seeds, time_active: .time_active}]'
```
**Decision tree:**
- `num_complete == 0` → **Dead torrent** (no seeders exist)
- `num_complete > 0` but `num_seeds == 0` → **Network issue** (seeds exist, can't connect)
- `time_active > 300` with no metadata → **Give up, search again**

## Storage Capacity Check
```bash
df -h /mnt/storage | tail -1 | awk '{print $5}' | sed 's/%//'
```
Returns numeric usage percentage. **Warn if >85%** — downloads may slow/fail.

## Empty API Responses That Aren't Errors

Some services return empty on success:

1. **qBittorrent POST** (add/delete/priority): empty string = success
2. **Plex library refresh**: empty/minimal XML = refresh queued
3. **Sonarr/Radarr commands**: `{}` or just `{"id": 123}` = command accepted, processing in background

**Rule:** POST/PUT/DELETE → assume success if HTTP 200 and no error text. Follow up with GET to verify state change.
