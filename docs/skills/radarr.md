<!-- name: Radarr — Movie Operations -->
<!-- description: Search movies, check missing/queue/history, trigger searches, add movies -->

# Radarr — Movie Operations

## Pattern: Find Movie by Title
**Script:** `radarr-find "Matrix"` (returns id, title, year, monitored, hasFile, tmdbId)

**Manual fallback:**
```bash
api-call radarr GET /movie | jq --arg term "SEARCH" '[.[] | select(.title | test($term; "i")) | {id: .id, title: .title, year: .year, monitored: .monitored, hasFile: .hasFile, tmdbId: .tmdbId}]'
```
**Gotcha:** Returns nothing if movie isn't in your library. Use `/movie/lookup` for external search (TMDB).

## Pattern: List Missing Movies
```bash
api-call radarr GET /movie | jq '[.[] | select(.hasFile == false and .monitored == true) | {id: .id, title: .title, year: .year, status: .status}] | sort_by(.title)'
```
**Gotcha:** Include `.monitored == true` or you'll get unmonitored/wishlist items.

## Pattern: Check Download Queue
```bash
api-call radarr GET /queue | jq '{total: .totalRecords, records: [.records[] | {title: .title, quality: .quality.quality.name, status: .status, sizeleft: .sizeleft, size: .size, estimatedCompletionTime: .estimatedCompletionTime}]}'
```
**Gotcha:** Empty records (totalRecords: 0) means nothing queued. `.sizeleft` is bytes remaining.

## Pattern: Check Recent Import History
```bash
api-call radarr GET /history | jq '.records[0:5] | [.[] | {date: .date, eventType: .eventType, movieId: .movieId, sourceTitle: .sourceTitle, quality: .quality.quality.name}]'
```
**Gotcha:** Event types: grabbed, downloadFolderImported, downloadFailed. Filter with `?eventType=downloadFolderImported` for completed imports.
**Pro tip:** History structure is simpler than Sonarr's — raw jq or executor mode both work fine.

## Pattern: Trigger Movie Search
```bash
api-call radarr POST /command -d '{"name":"MoviesSearch","movieIds":[123]}'
```
**Gotcha:** Takes array of movie IDs. Can trigger multiple movies in one command.
**Pro tip:** Unlike Sonarr (SeasonSearch for bulk), Radarr uses MoviesSearch with multiple IDs for bulk operations.

## Pattern: Check Command History
```bash
api-call {sonarr|radarr} GET /command | jq '[.[] | {name: .name, status: .status, started: .started, ended: .ended}] | sort_by(.started) | reverse | .[0:10]'
```
Works identically for both Sonarr and Radarr. Commands fall off quickly — check `/queue` for download status.

## Workflow: Request Movie

1. Search external: `api-call radarr GET /movie/lookup -q "term=..."`
2. Get root folder: `api-call radarr GET /rootfolder`
3. Get quality profile: `api-call radarr GET /qualityprofile`
4. Add movie with results from steps 1-3
5. Report to user
