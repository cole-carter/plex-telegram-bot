<!-- name: Sonarr — TV Show Operations -->
<!-- description: Search series, find missing episodes, check queue/history, trigger searches -->

# Sonarr — TV Show Operations

## Pattern: Find Series by Title
**Script:** `sonarr-find "Breaking Bad"` (returns id, title, monitored, tvdbId)

**Manual fallback:**
```bash
api-call sonarr GET /series | jq --arg term "SEARCH" '[.[] | select(.title | test($term; "i")) | {id: .id, title: .title, monitored: .monitored, tvdbId: .tvdbId}]'
```
**Gotcha:** Returns nothing if show isn't in your library. Use `/series/lookup` for external search.

## Pattern: List Missing Episodes
**Script:** `sonarr-missing <seriesId>` (returns missing episodes grouped by season)

**Manual fallback:**
```bash
api-call sonarr GET /episode -q "seriesId=X" | jq '[.[] | select(.hasFile == false and .monitored == true) | {season: .seasonNumber, episode: .episodeNumber, title: .title, airDate: .airDate}] | sort_by(.season, .episode) | group_by(.season) | map({season: .[0].season, count: length, episodes: map("\(.episode)")})'
```
**Gotcha:** Include `.monitored == true` or you'll get unmonitored specials/extras.

## Pattern: Check Download Queue
```bash
api-call sonarr GET /queue | jq '[.records[] | {title: .title, season: .episode.seasonNumber, episode: .episode.episodeNumber, quality: .quality.quality.name, status: .status, progress: .sizeleft, total: .size}]'
```
**Gotcha:** Empty array means nothing queued (not an error). `.sizeleft` and `.size` are in bytes.

## Pattern: Check Recent Import History
```bash
api-call sonarr GET /history
```
**Gotcha:** Event types: grabbed, downloadFolderImported, downloadFailed. Filter with `?eventType=downloadFolderImported` for completed imports only.
**Pro tip:** Don't fight the nested structure with jq — executor mode summarizes it better.

## Pattern: Trigger Episode/Season Search
**Single episode:**
```bash
api-call sonarr POST /command -d '{"name":"EpisodeSearch","episodeIds":[123]}'
```
**Entire season:**
```bash
api-call sonarr POST /command -d '{"name":"SeasonSearch","seriesId":456,"seasonNumber":3}'
```
**Gotcha:** EpisodeSearch takes an array of episode IDs. SeasonSearch takes seriesId + seasonNumber. Command returns quickly but actual search takes time — check `/queue` for results.
**Pro tip:** For multiple missing episodes in the same season, use SeasonSearch instead of individual EpisodeSearch calls.

## Pattern: Check Command History
```bash
api-call sonarr GET /command | jq '[.[] | {name: .name, status: .status, started: .started, ended: .ended}] | sort_by(.started) | reverse | .[0:10]'
```
Use when troubleshooting why a search didn't work. Commands fall off quickly — check `/queue` for download status.

## Workflow: Request TV Show

1. Search external: `api-call sonarr GET /series/lookup -q "term=..."`
2. Get episodes: `api-call sonarr GET /episode -q "seriesId=..."`
3. Identify missing episodes
4. Trigger search: `api-call sonarr POST /command -d '{"name":"EpisodeSearch","episodeIds":[...]}'`
5. Report to user

## Workflow: Check What's Missing

1. Find series: `sonarr-find "Show Name"`
2. Check missing: `sonarr-missing <seriesId>`
3. Trigger SeasonSearch for seasons with many missing, EpisodeSearch for individuals
