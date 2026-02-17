<!-- name: Plex — Library Operations -->
<!-- description: Browse libraries, check recently added, refresh/scan after file changes -->

# Plex — Library Operations

**Library IDs:** Section 1 = Movies, Section 2 = TV Shows

## Pattern: Check Recently Added
```bash
api-call plex GET /library/recentlyAdded
```
Returns 50 most recent additions (mixed: movies, seasons, episodes). Ordered by `addedAt` descending.

**Key fields:** `.title`, `.type` (season/movie/episode), `.addedAt` (Unix timestamp), `.librarySectionID`, `.parentTitle` (show name for seasons/episodes).
**Pro tip:** For "what imported in last X hours", filter by `.addedAt` within time window.

## Pattern: List Library Contents
**TV Shows:**
```bash
api-call plex GET /library/sections/2/all
```
**Movies:**
```bash
api-call plex GET /library/sections/1/all
```
**Key fields per item:** `.ratingKey` (Plex ID), `.title`, `.year`, `.childCount` (seasons), `.leafCount` (total episodes), `.viewedLeafCount` (watched).
**Pro tip:** Unwatched count = `leafCount - viewedLeafCount`. Large libraries — use executor mode.

## Pattern: Refresh Library
**Single library:**
```bash
api-call plex GET /library/sections/2/refresh
```
**Both libraries:**
```bash
api-call plex GET /library/sections/1/refresh && api-call plex GET /library/sections/2/refresh
```
**Gotcha:** No response body = success. Refresh runs async in background. No bulk "all libraries" endpoint — refresh each section individually.

## Workflow: Organize Files

1. List downloads: `ls -lh /home/mermanarchy/downloads/`
2. Parse filenames — determine show/movie, season, episode
3. Move to Plex naming convention:
   - Movies: `/mnt/storage/Movies/Title (Year)/Title (Year).ext`
   - TV: `/mnt/storage/TV Shows/Title (Year)/Season XX/Title - SXXEXX - Episode Name.ext`
4. Scan library: `api-call plex GET /library/sections/{1|2}/refresh`
5. Report what was organized
