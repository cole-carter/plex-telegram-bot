# API Reference - Extended Documentation

This file contains extended API documentation, examples, and notes that supplement the main CLAUDE.md file. You (the agent) can add to this as you discover useful patterns.

## Sonarr Extended Examples

*(Add complex Sonarr workflows here)*

## Radarr Extended Examples

*(Add complex Radarr workflows here)*

## qBittorrent Extended Examples

### qBittorrent Web API v2 - Key Endpoints

**List torrents:**
```bash
api-call qbt GET /torrents/info
```

**Get files in a torrent:**
```bash
api-call qbt GET /torrents/files -q "hash=TORRENT_HASH"
```
Returns array of files with: `name`, `size`, `progress`, `priority`, `index`

**Set file priority (selective download):**
```bash
api-call qbt POST /torrents/filePrio -d '{"hash":"TORRENT_HASH","id":"FILE_INDEX","priority":"0"}'
```
- `priority` values:
  - `0` = Do not download
  - `1` = Normal priority
  - `6` = High priority
  - `7` = Maximum priority
- `id` is the file index from `/torrents/files`
- To set multiple files, you can use `id` as array: `"id":"1|2|3"`

**Resume/pause torrents:**
```bash
# Resume
api-call qbt POST /torrents/resume -d '{"hashes":"TORRENT_HASH"}'

# Pause
api-call qbt POST /torrents/pause -d '{"hashes":"TORRENT_HASH"}'
```
- Use `hashes=all` to affect all torrents

**Get torrent properties:**
```bash
api-call qbt GET /torrents/properties -q "hash=TORRENT_HASH"
```
Returns detailed info including save_path, download progress, etc.

### Selective Download Workflow

1. Get torrent hash: `api-call qbt GET /torrents/info`
2. Get file list: `api-call qbt GET /torrents/files -q "hash=HASH"`
3. Find file indices for desired files (match by name pattern)
4. Set unwanted files to priority 0: `api-call qbt POST /torrents/filePrio -d '{"hash":"HASH","id":"INDEX","priority":"0"}'`
5. Set wanted files to priority 1+: `api-call qbt POST /torrents/filePrio -d '{"hash":"HASH","id":"INDEX","priority":"7"}'`
6. Resume torrent: `api-call qbt POST /torrents/resume -d '{"hashes":"HASH"}'`

## Plex Extended Examples

*(Add complex Plex workflows here)*

## Multi-Service Workflows

*(Document workflows that involve multiple services)*

Example:
1. User provides magnet link
2. Add to qBittorrent
3. Monitor for completion
4. Parse downloaded files
5. Move to Plex directories
6. Trigger Plex scan
7. Confirm to user
