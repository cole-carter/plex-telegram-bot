# Reference — API Documentation & System Architecture

This file is read-only for the agent. Maintained by developers.

## Docker Architecture & File Workflow

### Docker Stack

All services run in Docker containers defined in `~/arr-stack/docker-compose.yml`:

| Container | Purpose | Network |
|-----------|---------|---------|
| gluetun | VPN (Private Internet Access) | — |
| qbittorrent | Torrent client | Routes through gluetun |
| prowlarr | Indexer manager | — |
| radarr | Movie management | — |
| sonarr | TV show management | — |
| bazarr | Subtitle management | — |

### Container Path Mappings

**qBittorrent:**
- Container `/downloads` → Host `/home/mermanarchy/downloads`
- Storage: system disk (`/dev/sda2`, ~293GB total)

**Radarr:**
- Container `/movies` → Host `/mnt/storage/Movies`
- Container `/downloads` → Host `/home/mermanarchy/downloads`

**Sonarr:**
- Container `/tv` → Host `/mnt/storage/TV Shows`
- Container `/downloads` → Host `/home/mermanarchy/downloads`

**Bazarr:**
- Container `/movies` → Host `/mnt/storage/Movies`
- Container `/tv` → Host `/mnt/storage/TV Shows`

### File Workflow

1. **Download:** qBittorrent downloads to `/downloads` (container) = `/home/mermanarchy/downloads` (host, system disk)
2. **Import:** When complete, Sonarr/Radarr detect the file and **move** it to `/tv` or `/movies` (container) = `/mnt/storage/` (host, big storage)
3. **Final location:** Media lives on `/mnt/storage/{TV Shows,Movies}` (MergerFS pool)

**Important:**
- qBittorrent has NO access to `/mnt/storage` — only sees `/downloads`
- Sonarr/Radarr handle moving files from downloads to final location
- Don't manually move files from downloads unless the *arr apps can't handle it
- When organizing manually: check download is complete first, move to correct Plex path, trigger library refresh

### Storage

- **System disk:** ~293GB total (downloads location — monitor space)
- **Big storage:** 2.8TB MergerFS pool (1TB SSD + 2TB HDD), ~1.3TB free

---

## Sonarr API v3

**Base:** `http://192.168.1.14:8989/api/v3`

### Endpoints

**Search for TV show:**
```bash
api-call sonarr GET /series/lookup -q "term=Breaking Bad"
```
Returns array with `title`, `tvdbId`, `year`, `seasons`.

**Get all series:**
```bash
api-call sonarr GET /series
```

**Get episodes for a series:**
```bash
api-call sonarr GET /episode -q "seriesId=123"
```

**Trigger episode search:**
```bash
api-call sonarr POST /command -d '{"name": "EpisodeSearch", "episodeIds": [123, 456]}'
```

**Rescan series (after manual file addition):**
```bash
api-call sonarr POST /command -d '{"name": "RescanSeries", "seriesId": 123}'
```

**Check missing episodes:**
```bash
api-call sonarr GET /wanted/missing
```

**Get root folders / quality profiles:**
```bash
api-call sonarr GET /rootfolder
api-call sonarr GET /qualityprofile
```

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

**Check service status:**
```bash
api-call sonarr GET /system/status
```

---

## Radarr API v3

**Base:** `http://192.168.1.14:7878/api/v3`

### Endpoints

**Search for movie:**
```bash
api-call radarr GET /movie/lookup -q "term=The Matrix"
```
Returns array with `title`, `tmdbId`, `year`, `runtime`.

**Get all movies:**
```bash
api-call radarr GET /movie
```

**Get root folders / quality profiles (check before adding!):**
```bash
api-call radarr GET /rootfolder
api-call radarr GET /qualityprofile
```

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

**Trigger movie search:**
```bash
api-call radarr POST /command -d '{"name": "MoviesSearch", "movieIds": [123]}'
```

**Delete movie:**
```bash
api-call radarr DELETE /movie/123 -q "deleteFiles=true"
```

---

## qBittorrent Web API v2

**Base:** `http://192.168.1.14:8080/api/v2`

### Critical: POST Responses

qBittorrent POST endpoints return **empty responses on success**. This is normal.
- Empty response = Success
- Error message = Failure
- Do NOT troubleshoot empty responses. Move to next step.

### Download Progress Fields

The `/torrents/info` endpoint returns:
- `progress`: 0.0 to 1.0 scale (NOT 0-100). `0.72` = 72%, `1.0` = complete.
- `state`: `downloading`, `stalledDL`, `pausedDL`, `stoppedUP`, `metaDL`
- `amount_left`: bytes remaining
- `size`: downloaded size, `total_size`: full torrent size

### Endpoints

**List torrents:**
```bash
api-call qbt GET /torrents/info
```

**Get files in a torrent:**
```bash
api-call qbt GET /torrents/files -q "hash=TORRENT_HASH"
```
Returns array with `name`, `size`, `progress`, `priority`, `index`.

**Set file priority (selective download):**
```bash
api-call qbt POST /torrents/filePrio -d '{"hash":"HASH","id":"FILE_INDEX","priority":"0"}'
```
Priority values: `0` = skip, `1` = normal, `6` = high, `7` = maximum.
Multiple files: `"id":"1|2|3"` (pipe-separated indices).

**Resume / pause:**
```bash
api-call qbt POST /torrents/resume -d '{"hashes":"HASH"}'
api-call qbt POST /torrents/pause -d '{"hashes":"HASH"}'
```
Use `hashes=all` for all torrents.

**Add magnet:**
```bash
api-call qbt POST /torrents/add -d '{"urls":"magnet:?xt=...","savepath":"/home/mermanarchy/downloads/"}'
```

**Get torrent properties:**
```bash
api-call qbt GET /torrents/properties -q "hash=HASH"
```

**Delete torrent (keep files):**
```bash
api-call qbt POST /torrents/delete -d '{"hashes":"HASH","deleteFiles":false}'
```

### Selective Download Workflow

1. Get torrent hash: `api-call qbt GET /torrents/info`
2. Get file list: `api-call qbt GET /torrents/files -q "hash=HASH"`
3. Set unwanted files to priority 0
4. Set wanted files to priority 7
5. Resume torrent: `api-call qbt POST /torrents/resume -d '{"hashes":"HASH"}'`

---

## Plex Media Server API

**Base:** `http://192.168.1.14:32400`

### Library Section IDs

- Section 1: Movies
- Section 2: TV Shows

### Endpoints

**List all libraries:**
```bash
api-call plex GET /library/sections
```

**Get all items in a library:**
```bash
api-call plex GET '/library/sections/1/all'
```

**Pagination:**
```bash
api-call plex GET '/library/sections/1/all' -q 'X-Plex-Container-Start=0&X-Plex-Container-Size=50'
```

**Filter by genre / year:**
```bash
api-call plex GET '/library/sections/1/all?genre=Comedy'
api-call plex GET '/library/sections/1/all?year=2020'
```

**Search:**
```bash
api-call plex GET /library/sections/1/search -q 'query=Matrix'
```

**Refresh/scan library:**
```bash
api-call plex GET /library/sections/1/refresh
api-call plex GET /library/sections/2/refresh
```

**Recently added:**
```bash
api-call plex GET /library/recentlyAdded
```

---

## Bazarr API (Subtitles)

**Base:** `http://192.168.1.14:6767/api`

### Quick Status

**Badge counts (missing subtitle totals):**
```bash
api-call bazarr GET /badges
```
Returns `episodes` and `movies` counts of items missing subtitles, plus provider/connection status.

**System status:**
```bash
api-call bazarr GET /system/status
```

### List What's Missing

**Episodes missing subtitles:**
```bash
api-call bazarr GET /episodes/wanted
```
Returns `data` array with `seriesTitle`, `episode_number`, `missing_subtitles`, `sonarrSeriesId`, `sonarrEpisodeId`.

**Movies missing subtitles:**
```bash
api-call bazarr GET /movies/wanted
```
Returns `data` array with `title`, `missing_subtitles`, `radarrId`.

### Download Subtitles

**Auto-download for an episode (Bazarr picks best match):**
```bash
api-call bazarr PATCH /episodes/subtitles -d '{"seriesid": 1, "episodeid": 100, "language": "en", "forced": "False", "hi": "False"}'
```
Returns `204 No Content` on success.

**Auto-download for a movie:**
```bash
api-call bazarr PATCH /movies/subtitles -d '{"radarrid": 42, "language": "en", "forced": "False", "hi": "False"}'
```

### Bulk Search

**Search all missing for a series:**
```bash
api-call bazarr PATCH /series -d '{"seriesid": 1, "action": "search-missing"}'
```

**Search all missing for a movie:**
```bash
api-call bazarr PATCH /movies -d '{"radarrid": 42, "action": "search-missing"}'
```

### Browse Library (Subtitle Status)

**List series with subtitle counts:**
```bash
api-call bazarr GET /series
```
Returns `episodeFileCount`, `episodeMissingCount` per series.

**List episodes for a series:**
```bash
api-call bazarr GET /episodes -q "seriesid[]=1"
```
Returns `subtitles` (existing) and `missing_subtitles` per episode.

**List movies:**
```bash
api-call bazarr GET /movies
```

### Provider Status

**Check if providers are throttled:**
```bash
api-call bazarr GET /providers
```

**Reset throttled providers:**
```bash
api-call bazarr POST /providers -d '{"action": "reset"}'
```
