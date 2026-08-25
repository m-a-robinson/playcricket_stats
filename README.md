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
SQLiteStore            (schema.sql + sqlite_store.py: the normalised store)
      |
      v
sqlite_queries.py      (career stats / leaderboards, read via SQL)
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
  new or changed matches. Exposes the raw stored data (`seasons()`,
  `matches()`, `match()`, `match_details()`, `match_metadata()`) for
  `SQLiteStore` to build from — never touches the API itself. Its former
  player/club/team query methods have been retired (see below).
- **`playcricket_scorecard.py`** — Turns one raw match-detail record into
  structured DataFrames: batting, bowling, partnerships, fall-of-wickets,
  extras. Detects individual milestone achievements (half-century, century,
  double-century, 4- and 5-wicket hauls) and has a `print_scorecard()`
  plain-text console renderer. Directly reused by `sqlite_store.py` as its
  parsing engine.
- **`schema.sql`** / **`sqlite_store.py`** — Normalised SQLite store (clubs,
  teams, players, matches, innings, batting/bowling innings, match
  appearances/team sheets, milestone views), fed from the JSON cache with no
  API calls. `PlayCricketDatabase`/JSON stays the sync layer; SQLite is the
  canonical query/analysis layer, built for cross-source reconciliation
  (each row carries `source`/`source_*_id`, and player identity across
  sources is resolved through `player_source_ids`). Run
  `python3 sqlite_store.py` to (re)build it from `playcricket_database.json`.
- **`sqlite_queries.py`** — Career stats and leaderboards computed directly
  from the SQLite store: `career_stats()` (true career totals per player,
  splitting by team only if asked) and `SQLPlayerStats` (qualification-based
  leaderboards — top runs, average, strike rate, wickets, economy, catches,
  milestones, etc). This is now the only stats/leaderboard layer in the
  project — see "Retired" below.

### Retired

- **`player_performances.py`** and **`multi_player_stats.py`** have been
  removed. Both were pandas-over-raw-JSON reimplementations of what the
  SQLite store now does, and were not imported anywhere else in the
  codebase. They're recoverable from git history if needed, but shouldn't
  be resurrected — see the findings below for why.
- **`PlayCricketDatabase.players()`, `.player_appearances()`, `.clubs()`,
  `.teams()`, `.matches_dataframe()`** have been removed for the same
  reason: unused outside their own definitions, and superseded by SQL
  queries against the normalised store.
- Verified before removal, against the sample database: `career_stats()`
  reproduces every figure the retired code produced correctly, fixes the
  career-totals-fragmented-by-team bug found earlier (e.g. a player who
  guests for another XI is now one person, not several), surfaces 10
  fielder-only appearances the old code couldn't see at all (no bat/bowl
  row to hang them on), and `top_fifties()`/`top_hundreds()`/`highlights()`
  — which always silently returned empty from `MultiPlayerStats` because it
  sorted by columns `PlayerPerformances.summary()` never populated — now
  return real results.

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
  resolution, player identity matching for sources with no Play-Cricket id
  to anchor on — the `player_source_ids` mapping table is ready for this,
  the matching logic itself isn't written yet).
- Formatted scorecard export (image/PDF) for printing or framing.
- Social-media formatting for player performances and weekend results.
- Any CLI/UI entry point — everything today is a library.

## Roadmap

1. **Data foundation** — *Done for the Play-Cricket source.* SQLite store
   built (`schema.sql` / `sqlite_store.py`): players, clubs, teams, matches,
   innings, batting/bowling, match appearances (team sheets), and milestone
   views, with `source`/`source_*_id` columns on every fact table and a
   `player_source_ids` mapping table so cross-source player identity can be
   resolved without redesigning the schema later. Query/leaderboard layer
   (`sqlite_queries.py`) built and verified against the old pandas pipeline,
   which has now been retired (`player_performances.py`,
   `multi_player_stats.py`, and the redundant query methods on
   `PlayCricketDatabase` — see "Retired" above). Still to do: an explicit
   name-based reconciliation step for players who only appear in the
   CricHQ/CricketStatz sources (no Play-Cricket id to anchor on).
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
5. **Career & historical stats** — Extend `sqlite_queries.py` to operate
   across the merged multi-source database (all-time leaderboards, career
   milestones, team/season filtering already work for the Play-Cricket-only
   case today).
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
