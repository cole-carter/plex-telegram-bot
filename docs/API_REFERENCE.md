# API Reference - Extended Documentation

This file contains extended API documentation, examples, and notes that supplement the main CLAUDE.md file. You (the agent) can add to this as you discover useful patterns.

## Sonarr Extended Examples

### Sonarr API v3 - Key Endpoints

**Search for TV show:**
```bash
api-call sonarr GET /series/lookup -q "term=Breaking Bad"
```
Returns array of shows with `title`, `tvdbId`, `year`, `seasons`, etc.

**Add TV show:**
```bash
api-call sonarr POST /series -d '{
  "tvdbId": 81189,
  "title": "Breaking Bad",
  "qualityProfileId": 1,
  "languageProfileId": 1,
  "rootFolderPath": "/mnt/storage/TV Shows",
  "seasonFolder": true,
  "monitored": true,
  "addOptions": {"searchForMissingEpisodes": true}
}'
```

**Get all series:**
```bash
api-call sonarr GET /series
```

**Search for episodes (trigger download):**
```bash
api-call sonarr POST /command -d '{"name": "EpisodeSearch", "episodeIds": [123, 456]}'
```

**Get root folders:**
```bash
api-call sonarr GET /rootfolder
```

**Get quality profiles:**
```bash
api-call sonarr GET /qualityprofile
```

## Radarr Extended Examples

### Radarr API v3 - Key Endpoints

**Search for movie:**
```bash
api-call radarr GET /movie/lookup -q "term=The Matrix"
```
Returns array of movies with `title`, `tmdbId`, `year`, `runtime`, etc.

**Add movie:**
```bash
api-call radarr POST /movie -d '{
  "tmdbId": 603,
  "title": "The Matrix",
  "year": 1999,
  "qualityProfileId": 1,
  "rootFolderPath": "/mnt/storage/Movies",
  "monitored": true,
  "addOptions": {"searchForMovie": true}
}'
```

**Get all movies:**
```bash
api-call radarr GET /movie
```

**Search for movie (trigger download):**
```bash
api-call radarr POST /command -d '{"name": "MoviesSearch", "movieIds": [123]}'
```

**Get root folders:**
```bash
api-call radarr GET /rootfolder
```

**Get quality profiles:**
```bash
api-call radarr GET /qualityprofile
```

**Delete movie:**
```bash
api-call radarr DELETE /movie/123 -q "deleteFiles=true"
```

## qBittorrent Extended Examples

### qBittorrent Web API v2 - Key Endpoints

**⚠️ CRITICAL: Understanding qBittorrent API Responses**

qBittorrent POST endpoints return **empty responses on success**. This is the API's standard behavior:
- Empty response = Success
- Error message in response = Failure
- Status code 200 with empty body = Operation completed successfully

**Do NOT waste turns troubleshooting or verifying when you get empty responses.** Trust the API and move forward with the next step. Only investigate if you receive an actual error message or non-200 status code.

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

### Plex Media Server API - Key Endpoints

**Get all library sections:**
```bash
api-call plex GET /library/sections
```
Returns all libraries with their section IDs (e.g., 1=Movies, 2=TV Shows)

**Get all items in a library:**
```bash
api-call plex GET '/library/sections/1/all'
```
Use section ID from above. Returns all media in that library.

**Get items with pagination:**
```bash
api-call plex GET '/library/sections/1/all' -q 'X-Plex-Container-Start=0&X-Plex-Container-Size=50'
```
Start at index 0, return 50 items.

**Filter by genre:**
```bash
api-call plex GET '/library/sections/1/all?genre=Comedy'
```

**Filter by year:**
```bash
api-call plex GET '/library/sections/1/all?year=2020'
```

**Search across library:**
```bash
api-call plex GET /library/sections/1/search -q 'query=Matrix'
```

**Refresh/scan library:**
```bash
api-call plex GET /library/sections/1/refresh
```
Triggers Plex to scan for new/changed media files.

**Get recently added:**
```bash
api-call plex GET /library/recentlyAdded
```

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
