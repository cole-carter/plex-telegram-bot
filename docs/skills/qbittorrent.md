<!-- name: qBittorrent — Download Management -->
<!-- description: Check torrent status, identify stalled downloads, selective file priority, health checks -->

# qBittorrent — Download Management

## Pattern: List All Torrents
**Script:** `qbt-status` (returns name, state, progress%, GB sizes, speed, ETA)

**With filter:** `qbt-status downloading` (options: downloading, completed, active, inactive)

**Manual fallback:**
```bash
api-call qbt GET /torrents/info | jq '[.[] | {name: .name, hash: .hash, state: .state, progress: ((.progress * 100 | round | tostring) + "%"), downloaded_gb: ((.size / 1073741824 * 100 | round) / 100), total_gb: ((.total_size / 1073741824 * 100 | round) / 100), dlspeed_mbs: ((.dlspeed / 1048576 * 100 | round) / 100), eta: .eta}]'
```

**State meanings:**
- `downloading`: Actively downloading with seeds/peers
- `queuedDL`: Queued, waiting for slot or metadata
- `metaDL`: Fetching metadata (magnet link phase)
- `stoppedUP`: Complete and seeding (or stopped)
- `stalledDL`: Has peers but no data transfer

**Gotcha:** `.progress` is 0.0-1.0 (NOT 0-100). `.total_size` is -1 for torrents still fetching metadata. ETA 8640000 = stalled/unknown.

## Pattern: Filter Torrents by State
```bash
api-call qbt GET /torrents/info -q "filter=downloading"
```
**Gotcha:** `filter=downloading` is broad — includes queued/metadata states. For truly active only, add jq: `| jq '[.[] | select(.state == "downloading")]'`

Other filters: `completed`, `active`, `inactive`

## Pattern: Identify Stalled Downloads
```bash
api-call qbt GET /torrents/info | jq '[.[] | select(.state == "stalledDL" or (.state == "downloading" and .dlspeed == 0 and .num_seeds == 0)) | {name: .name, state: .state, num_seeds: .num_seeds, num_complete: .num_complete}]'
```
**Gotcha:** Check both `.num_seeds` (connected) and `.num_complete` (total in swarm). Both 0 = likely dead torrent.

## Pattern: Get File List for Selective Priority
```bash
api-call qbt GET /torrents/files -q "hash=TORRENT_HASH" | jq '[.[] | {index: .index, name: .name, size: .size, progress: (.progress * 100 | round), priority: .priority}]'
```
**Gotcha:** `.index` is 0-based, used for `filePrio` commands. Priority: 0=skip, 1=normal, 6=high, 7=maximum.
**Pro tip:** For season packs: get file list, identify wanted episodes by name, set priority 7 for wanted and 0 for unwanted.

## Pattern: Check Torrent Health
```bash
api-call qbt GET /torrents/properties -q "hash=TORRENT_HASH" | jq '{total_size: .total_size, dl_speed: .dl_speed, up_speed: .up_speed, seeds: .seeds, seeds_total: .seeds_total, peers: .peers, peers_total: .peers_total, addition_date: .addition_date}'
```
**Gotcha:** `.seeds` = connected, `.seeds_total` = swarm total. If `.seeds_total` is 0, torrent is dead. Speeds in bytes/sec (divide by 1048576 for MB/s).
**Pro tip:** Low connected/total seed ratio usually means VPN/firewall issue, not dead torrent.

## Workflow: Magnet Link

1. Ask user: movie or TV? What title?
2. Add: `api-call qbt POST /torrents/add -d '{"urls":"magnet:...","savepath":"/home/mermanarchy/downloads/"}'`
3. Report download started (empty response = success)

## Workflow: Check Downloads

1. Run: `qbt-status` (or `qbt-status downloading` for active only)
2. Report progress — remember progress is 0.0-1.0, NOT 0-100

## Workflow: Selective Download from Season Pack

1. Get hash: `qbt-status` → find the torrent
2. Get files: `api-call qbt GET /torrents/files -q "hash=HASH"`
3. Set unwanted to priority 0, wanted to priority 7
4. Resume: `api-call qbt POST /torrents/resume -d '{"hashes":"HASH"}'`
