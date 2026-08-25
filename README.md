# playcricket_stats

A club cricket statistics database that reconciles three sources of scorecard
data into a single queryable store:

1. **Play-Cricket API** — the live/current source, kept in sync with a
   minimal number of API requests.
2. **CricHQ PDF archive scorecards** — historical matches predating
   Play-Cricket, currently sitting in the club's PDF archive.
3. **A legacy binary-format database** — CricketStatz `.csd` files, an
   older desktop stats package used before Play-Cricket/CricHQ.

Once merged, the goal is to support historical and career stats, records
queryable by team/season/player, leaderboards, printable/frameable scorecard
exports for milestone achievements (centuries, five-wicket hauls, career
milestones), and social-media-formatted summaries of individual performances
and weekend results.

## Current state

The project is a Python library (pandas/numpy/requests, no framework yet)
with a clean layered architecture — each layer depends only on the one
below it and never calls back up or sideways into the API:

```
PlayCricketAPI
      |
      v
PlayCricketDatabase   (local JSON cache + sync)
      |
      v
Scorecard              (one match -> batting/bowling/partnerships/FoW)
      |
      v
PlayerPerformances     (per-player aggregation across matches)
      |
      v
MultiPlayerStats       (cross-player leaderboards/comparisons)
```

### Modules

- **`playcricket_api.py`** — Stateless Play-Cricket API client. Fetches
  season match lists and full match-detail JSON, normalises IDs/dates. No
  storage, no business logic.
- **`playcricket_database.py`** — Local JSON cache
  (`playcricket_database.json`, versioned schema, keyed by season). This is
  where API-call minimisation lives: `sync_season()` makes one call for the
  season's match list, then compares each match's `last_updated` timestamp
  against the locally stored value and only re-downloads match detail for
  new or changed matches. All query methods here are local-only and never
  touch the API.
- **`playcricket_scorecard.py`** — Turns one raw match-detail record into
  structured DataFrames: batting, bowling, partnerships, fall-of-wickets,
  extras. Already detects individual milestone achievements (half-century,
  century, double-century, 4- and 5-wicket hauls) and has a `print_scorecard()`
  plain-text console renderer.
- **`player_performances.py`** — Aggregates scorecards across matches into
  per-player batting/bowling/fielding/participation stats and an overall
  `summary()` table, including a `notable_performances` count fed by the
  milestone detection above.
- **`multi_player_stats.py`** — Cross-player leaderboards built on
  `PlayerPerformances`: qualification-based tables for top runs, batting
  average, strike rate, top scores, fifties, hundreds, wickets, bowling
  average, economy, bowling strike rate, catches, fielding, and highlights.
- **`schema.sql`** / **`sqlite_store.py`** — Normalised SQLite store (clubs,
  teams, players, matches, innings, batting/bowling innings), fed from the
  JSON cache with no API calls. `PlayCricketDatabase`/JSON stays the sync
  layer; SQLite is the canonical query/analysis layer, built for
  cross-source reconciliation (each row carries `source`/`source_*_id`,
  and player identity across sources is resolved through
  `player_source_ids`). Run `python3 sqlite_store.py` to (re)build it from
  `playcricket_database.json`.

### Sample data

- `playcricket_2026.json` — a synced local database (70 matches) showing the
  storage schema in practice.
- `ELPM 1st XI 2019.pdf` — a sample CricHQ-style archive scorecard, used as
  reference material for the PDF ingestion work below.
- `ELPM2018.csd` — a CricketStatz database export, used as reference
  material for the binary-format mapping work below.

### Not built yet

- CricHQ PDF parsing/ingestion.
- Binary-archive-format reader/converter.
- Reconciliation/merge logic across the three sources (dedup, conflict
  resolution, player identity matching across sources).
- Persistent storage beyond flat JSON (fine today, but will strain once
  archive data is merged in).
- Formatted scorecard export (image/PDF) for printing or framing.
- Social-media formatting for player performances and weekend results.
- A player identity model spanning seasons/sources (career stats currently
  only work within what Play-Cricket IDs provide).
- Any CLI/UI entry point — everything today is a library.

## Roadmap

1. **Data foundation** — *SQLite store built* (`schema.sql` /
   `sqlite_store.py`): players, clubs, teams, matches, innings, batting and
   bowling tables, with `source`/`source_*_id` columns on every fact table
   and a `player_source_ids` mapping table so cross-source player identity
   can be resolved without redesigning the schema later. Verified against
   the existing pandas summary — and in doing so found that
   `PlayerPerformances.summary()` splits a player's career totals by team
   (a player who guests for another XI gets counted as a separate person
   per team), which the SQLite build's player-level aggregation avoids.
   Still to do: an explicit name-based reconciliation step for players who
   only appear in the CricHQ/CricketStatz sources (no Play-Cricket id to
   anchor on).
2. **CricHQ PDF ingestion** — Parser to extract scorecards from the archive
   PDFs into the same internal scorecard shape used by `Scorecard`, so
   downstream analysis code can be reused unchanged.
3. **Binary archive ingestion (`.csd` mapping)** — Reverse-engineer the
   CricketStatz `.csd` format and read it into the same internal shape.
   `.csd` is a proprietary multi-table binary flat-file (no dBase/Paradox/
   SQLite header — tables are just concatenated fixed-length records).
   Mapped so far, from `ELPM2018.csd`:
     - A **player table** starting at byte offset `0xbb0`, fixed
       **648-byte records**, each holding a display name (e.g. `"F Daly"`),
       separate padded surname/forename fields (`"Daly"` / `"Franny"`),
       flag bytes, and reserved space — around 1,677 record slots (many
       blank/unused).
     - Immediately after it, a second table of short sequential records
       (record-id followed by several int16 fields) — likely per-player
       career aggregates (batting/bowling totals) keyed by player index.
     - Further tables (matches, innings) are expected later in the file
       and still need mapping.
   Remaining work: map every table and field, then write a parser that
   emits the same internal scorecard/player shape the other two sources
   use.
4. **Reconciliation layer** — Merge the three sources per match/player with
   conflict detection and a clear precedence rule (e.g. Play-Cricket wins on
   overlap, archives fill gaps).
5. **Career & historical stats** — Extend `PlayerPerformances`/
   `MultiPlayerStats` to operate across the merged multi-source database
   (all-time leaderboards, career milestones, team/season filtering).
6. **Scorecard export** — Turn `print_scorecard`'s data into a designed,
   printable artifact (PDF/image) triggerable on milestone detection (which
   already exists) for framing/display.
7. **Social media formatting** — Templated short-form text/image output for
   individual milestone performances and weekend team-result round-ups.
8. **Interface** — CLI (and/or lightweight web UI) tying sync, query, and
   export together, plus scheduling for regular Play-Cricket syncs. If
   published to the club's WordPress site, the SQLite database itself
   won't run there (typical WordPress hosting is MySQL-only, often with a
   read-only filesystem) — instead this stage would add an export/sync
   step: either a small REST endpoint a WordPress shortcode/plugin calls,
   or a scheduled export of computed tables (leaderboards, career stats,
   results) to static JSON/HTML the site consumes.
