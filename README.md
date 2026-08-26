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
      ^
      |                CricHQ PDF -> crichq_pdf.py (parses to the same shape)
      |                CricketStatz .MXP -> mxp_parser.py (same shape)
      |
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
  canonical query/analysis layer, built for cross-source reconciliation:
  every fact table carries `source`, and canonical identity for players,
  clubs, and teams alike is resolved through a `*_source_ids` mapping table
  (`player_source_ids`, `club_source_ids`, `team_source_ids`) rather than
  reusing Play-Cricket's own numeric ids as primary keys — required once a
  source (CricHQ) has no numeric ids of its own to reuse. Run
  `python3 sqlite_store.py` to (re)build the Play-Cricket side of the store
  from `playcricket_database.json`.
- **`crichq_pdf.py`** — Parses CricHQ "Full Scorecard Report" PDF exports
  (one PDF = a season's worth of matches for one team, concatenated across
  pages) into the same match-detail shape `Scorecard` expects, so they load
  through the exact same `SQLiteStore.insert_match()` path as Play-Cricket
  data, with `source="crichq_pdf"`. Handles mid-row PDF line-wraps, partial/
  abandoned matches, and the CricHQ dismissal-text format (`"c X b Y"`,
  `"run out (A/B)"`, etc.). Player identity is deliberately **not** matched
  against existing players — every CricHQ name becomes its own new
  canonical player for now (see "Not built yet" below). Run
  `python3 crichq_pdf.py <pdf-file>... --sqlite-db <path>` to ingest one or
  more PDFs.
- **`mxp_parser.py`** — Parses CricketStatz `.MXP` exports (File →
  Export/Email Matches in the desktop app — see the roadmap below) into
  the same match-detail shape `Scorecard` expects, with
  `source="cricketstatz"`. Unlike the other two sources, `.MXP` is a
  plain, fully-documented `Key=Value` text format (`MXP Format.doc`) and
  carries real numeric ids for players/clubs/teams/grounds, so identity
  is stronger here than the CricHQ PDF's name-derived ids — reused
  directly as source ids. Handles the CricketStatz `howout` code
  vocabulary (18 dismissal types, including caught-and-bowled and
  caught-behind, each with their own fielder/bowler attribution rules)
  and anonymous ("id 0, name `?`") opposition batting performances,
  which are kept as real batting rows under a match/position-scoped
  synthetic id rather than merged into one shared "unknown player" (see
  the module docstring). Deliberately does **not** attempt to derive
  fall-of-wickets from the batsman rows' `fow`/`fowpos` fields — checked
  against the bundled Bodyline Test demo data and they don't reliably
  correspond to an increasing wicket sequence, matching the format doc's
  own caveat that they aren't necessarily tied to the batsman on that
  row. Validated against the club's full real archive (304 matches,
  `ELPM2018_all_matches.mxp`): zero foreign-key violations, batting/
  bowling figures cross-checked against the bundled historical demo data
  match real cricket records exactly (Larwood 5/96, McCabe's 187\*, and
  all five 1932-33 Bodyline Test results), and career stats for a known
  player (`I Wade`) come back as a plausible multi-season all-rounder
  record end to end through the existing `sqlite_queries.py` layer. Run
  `python3 mxp_parser.py <mxp-file>... --sqlite-db <path>` to ingest one
  or more `.MXP` exports.
- **`sqlite_queries.py`** — Career stats and leaderboards computed directly
  from the SQLite store: `career_stats()` (true career totals per player,
  splitting by team only if asked) and `SQLPlayerStats` (qualification-based
  leaderboards — top runs, average, strike rate, wickets, economy, catches,
  milestones, etc). This is now the only stats/leaderboard layer in the
  project — see "Retired" below. Source-agnostic: works the same whether the
  store holds Play-Cricket data, CricHQ data, or both. Excludes opposition
  players by default (`elpmcc_only=True`) — a PDF import brings in every
  player from both teams, but only `ELPMCC_NAME`'s own players are
  wanted as tracked "players" with career stats/leaderboard entries.
  Opposition players still appear in full within the scorecard tables
  (`batting_innings`/`bowling_innings`/`match_appearances` are untouched);
  pass `elpmcc_only=False` to include them in `career_stats()` too, e.g.
  to check one opposition player's record specifically against this club.
- **`reconcile.py`** — Cross-source player identity merging (see roadmap
  item 4). `merge_players(conn, source_refs)` repoints a confirmed list of
  `(source, source_player_id)` refs, and every fact-table row that
  references them, onto one surviving canonical `player_id`. `PLAYER_MERGES`
  is the growable registry of confirmed groups — run
  `python3 reconcile.py --sqlite-db <path>` after ingesting (all) sources to
  apply every entry; re-running is idempotent. No query-layer changes are
  needed after a merge: `career_stats()`/`SQLPlayerStats` already aggregate
  by `player_id` alone, across every source.

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
- `ELPM 1st XI 2019.pdf` — a CricHQ full-season scorecard export (23
  matches, 16 played + 7 abandoned), used to build and validate
  `crichq_pdf.py`. Ingests cleanly: 295 batting rows, 147 bowling rows, 348
  match appearances, zero unmatched lines, zero foreign-key violations.
- `ELPM2018.csd` — the club's live CricketStatz database export, format
  version **11**. Opens under CricketStatz build 11.2.49 (`cricketstatz11.exe`,
  installed under Wine) — see `ELPM2018_all_matches.mxp` below for the
  full export.
- `ELPM2009 - backup 2015.csd` / `ELPM2015_backup 20170903.csd` — earlier
  club backups, format version **10**, openable by CricketStatz 10.5.1.
  Both are real ELPMCC archive data (not demo data): 169 matches
  (2005-04-23 to 2015-04-25) and 274 matches (2005-04-23 to 2017-09-02)
  respectively — the 2017 backup is a superset of the 2015 one, and
  `ELPM2018.csd` a superset of that again.
- `MXP Format.doc` — the official Red Axe/CricketStatz `.MXP` export
  format specification (a Word doc; read with `antiword` — LibreOffice's
  headless converter failed to load it in this environment for unclear
  reasons, antiword worked first try). Full field-by-field spec including
  the batsman `howout` codes (0=dnb, 1=Not Out, 2=Bowled, 3=Caught, 4=C&B,
  5=Hit Wicket, 6=LBW, 7=Retired Hurt, 8=Runout, 9=Stumped, 10=Obstructed
  Field, 11=Handled Ball, 12=Retired Out, 13=Retired Not Out, 14=Timed
  Out, 15=Hit Ball Twice, 16=Absent Hurt, 17=Absent Ill, 18=Caught Behind)
  and match-result codes, dated change-log back to 2000.
- `bodyline_sample.mxp` — a Cricket Statz `.MXP` export (via File →
  Export/Email Matches, run under Wine), covering all 5 matches of the
  bundled `sample.csd` demo database ("The Bodyline Test Series").
- `ELPM2005-2015_all_matches.mxp` / `ELPM2009-2017_all_matches.mxp` /
  `ELPM2018_all_matches.mxp` — full `.MXP` exports of the three real club
  backups above (169, 274, and **304** matches respectively, each
  verified by counting `Record=Match`/`Endmatch=True` pairs — 304/304 for
  the full archive, no errors). `ELPM2018_all_matches.mxp` is the
  complete ELPMCC scorecard history, 2005-04-23 to 2018-07-21, in the
  same plain-text format described below — the actual ingestion target
  for the `.MXP` parser still to be written.

### Not built yet

- **Automatic** reconciliation/merge logic across the three sources (dedup,
  conflict resolution, player/club/team identity matching for sources with
  no Play-Cricket id to anchor on). `reconcile.py` (see "Modules" above)
  proves the merge *mechanism* works — for players, and only for the ones
  named in its human-curated `PLAYER_MERGES` list — but finding those groups
  automatically isn't built. Concretely: right now the same real
  person/club/team gets a separate canonical row per source unless
  explicitly merged (e.g. "East Lancs Paper Mill CC" exists as both
  `club_id 1` from Play-Cricket and a different `club_id` from CricHQ, and
  club/team identity has no merge tooling at all yet, unlike players) —
  deliberately deferred to a dedicated reconciliation pass across all three
  sources rather than guessed at during ingestion (see the "MR Robinson" /
  seven-Robinsons example this was scoped against).
- Formatted scorecard export (image/PDF) for printing or framing.
- Social-media formatting for player performances and weekend results.
- Any CLI/UI entry point — everything today is a library.

## Basic usage (verifying progress in ipython)

Everything is a plain Python library today, so the easiest way to check
progress is to import the pieces directly in an `ipython` session and look
at what comes back. One-time setup:

```bash
pip install ipython pandas numpy requests pypdf
cd playcricket_stats
ipython
```

The examples below all use the files already in the repo
(`playcricket_2026.json`, `ELPM 1st XI 2019.pdf`) — nothing needs an API key
to run.

### 1. Build the SQLite store from the sample Play-Cricket data

This is usually run from the Terminal, not ipython, since it's a one-shot
build step:

```bash
python3 sqlite_store.py --json-db playcricket_2026.json --sqlite-db demo.sqlite
```

```
Built 70 matches into demo.sqlite
```

### 2. Look at one match's scorecard

Good for eyeballing that a match parsed correctly against what you remember
of the game:

```python
from playcricket_database import PlayCricketDatabase
from playcricket_scorecard import Scorecard

db = PlayCricketDatabase(api=None, filename="playcricket_2026.json")

# db.match_details(season=2026) lists every match; db.match(match_id) gets
# one. Both return the raw stored API response, so unwrap ["match_details"][0]
# to get the record Scorecard expects.
raw = db.match(7239375)
sc = Scorecard(raw["match_details"][0])

sc.teams()          # {'home': '...', 'away': '...'}
sc.get_result()      # 'East Lancs Paper Mill CC - 1st XI - Won'
sc.batting_table(1)   # innings-1 batting card as a DataFrame
sc.print_scorecard()   # full scorecard, printed
```

### 3. Query career stats and leaderboards

This is the main "did this actually work" check — cross-check a name or
figure you know against what comes back:

```python
import sqlite3
from sqlite_queries import SQLPlayerStats

conn = sqlite3.connect("demo.sqlite")
stats = SQLPlayerStats(conn)

stats.top_runs(top_n=10)              # leaderboard, ranked
stats.top_wickets(top_n=10)
stats.top_batting_average(top_n=10)
stats.highlights(top_n=10)             # milestone counts (50s/100s/5-fors)

stats.career()                          # every player, full career stats
stats.career(team_id=1)                  # same, restricted to one team
stats.career().query("player_name == 'Ian Wade'")   # look up one player
```

### 4. Ingest a CricHQ PDF and check it landed correctly

```bash
python3 crichq_pdf.py "ELPM 1st XI 2019.pdf" --sqlite-db demo.sqlite
```

```
Parsing ELPM 1st XI 2019.pdf ...
  23 matches found in this file.
Done. Played: 16, Abandoned: 7
```

Then, back in ipython, query it the same way as the Play-Cricket data (the
store now holds both sources side by side):

```python
conn = sqlite3.connect("demo.sqlite")   # reconnect to pick up the new data
stats = SQLPlayerStats(conn)

conn.execute("SELECT source, COUNT(*) FROM matches GROUP BY source").fetchall()
# [('crichq_pdf', 23), ('play_cricket', 70)]

stats.career(season=2019).sort_values("wickets", ascending=False).head(10)
```

A CricHQ PDF brings in every player from **both** teams (opposition included) —
`players` will have far more rows than `stats.career()` returns, since
`career_stats()` only tracks `ELPMCC_NAME`'s own players by default.
Opposition players are still fully present in the scorecard tables, just
excluded from career stats/leaderboards:

```python
conn.execute("SELECT COUNT(*) FROM players").fetchone()   # (736,) -- everyone who appears anywhere
stats.career().shape[0]                                    # 116   -- ELPMCC only (the default)
stats.career(elpmcc_only=False).shape[0]                   # 736   -- lift the filter to see everyone
```

### 5. Ingest a CricketStatz `.MXP` export and check it landed correctly

```bash
python3 mxp_parser.py ELPM2018_all_matches.mxp --sqlite-db demo.sqlite
```

```
Parsing ELPM2018_all_matches.mxp ...
  304 matches found in this file.
Done. Played: 304, Abandoned: 0
```

This source's own club name is `"East Lancs Paper Mill"` (no `"CC"` —
identity reconciliation across sources, see the roadmap, hasn't run
yet), so pass it explicitly to see the club's own players rather than
the default `ELPMCC_NAME`:

```python
conn = sqlite3.connect("demo.sqlite")
stats = SQLPlayerStats(conn, elpmcc_name="East Lancs Paper Mill")

conn.execute("SELECT source, COUNT(*) FROM matches GROUP BY source").fetchall()
# [('cricketstatz', 304), ('crichq_pdf', 23), ('play_cricket', 70)]

stats.top_runs(top_n=10)
stats.top_wickets(top_n=10)
```

### 6. Reconcile a player across sources and pull their full career

`demo.sqlite` now holds the same real person under three different
identities — a Play-Cricket numeric id, a CricHQ PDF name, and two
CricketStatz ids. `reconcile.py` merges known groups (`PLAYER_MERGES`)
so a career query spans all of them:

```bash
python3 reconcile.py --sqlite-db demo.sqlite
```

```
Merged: Ian Wade -> player_id 5
```

```python
conn = sqlite3.connect("demo.sqlite")   # reconnect to pick up the merge
career = career_stats(conn, elpmcc_only=False)
career[career["player_id"] == 5].T
# games_played 151, runs 3895 @ 31.7 (18 fifties, 7 hundreds),
# 107 wickets @ 15.9, 63 catches -- 2005-2018 (cricketstatz) through
# the current season (play_cricket), with one 2019 match from crichq_pdf
```

Adding another player means adding another entry to `PLAYER_MERGES` (find
their refs with a query like the one in `reconcile.py`'s own investigation
notes) — nothing else changes, including after importing further CricHQ
PDFs: re-running `reconcile.py` is idempotent, and any *new* match for an
already-merged ref resolves straight to the survivor.

### 7. Poke at the raw tables directly

For anything the query helpers don't cover yet, plain SQL against `demo.sqlite`
works — the schema is in `schema.sql`:

```python
conn.execute("SELECT * FROM matches WHERE source='crichq_pdf' LIMIT 1").fetchone()
conn.execute("SELECT * FROM v_batting_achievements LIMIT 5").fetchall()
conn.execute("PRAGMA foreign_key_check").fetchall()   # should always be []
```

Delete `demo.sqlite` and re-run steps 1/4 any time to rebuild from scratch —
nothing in the pipeline is destructive to the source JSON/PDF files.

## Roadmap

1. **Data foundation** — *Done.* SQLite store built (`schema.sql` /
   `sqlite_store.py`): players, clubs, teams, matches, innings,
   batting/bowling, match appearances (team sheets), and milestone views,
   with `source` on every fact table and canonical identity for players,
   clubs, *and* teams resolved through `*_source_ids` mapping tables (not
   just Play-Cricket's own numeric ids as primary keys — necessary once
   CricHQ, which has none, joined the store). Query/leaderboard layer
   (`sqlite_queries.py`) built and verified against the old pandas pipeline,
   which has now been retired (`player_performances.py`,
   `multi_player_stats.py`, and the redundant query methods on
   `PlayCricketDatabase` — see "Retired" above). Still to do: the
   cross-source reconciliation pass itself (see "Not built yet").
2. **CricHQ PDF ingestion** — *Done.* `crichq_pdf.py` parses CricHQ's "Full
   Scorecard Report" PDF export into the same internal shape `Scorecard`
   uses, validated end to end against `ELPM 1st XI 2019.pdf` (23 matches,
   295 batting rows, 147 bowling rows, no unmatched lines). Along the way,
   found and fixed a latent bug in `sqlite_store.py`'s value-cleaning
   helpers: Play-Cricket's raw JSON always uses `""` for a missing
   fielder/bowler, so pandas never introduced `NaN` there, but a Python
   `None` (used by the new PDF parser) gets upgraded to float `NaN` by
   pandas whenever it shares a column with strings — which the old
   `value in (None, "")` checks couldn't catch, since `NaN` compares
   unequal to everything, including itself. Fixed once, centrally, so any
   future source hits the same safety net.
3. **CricketStatz `.csd` ingestion** — *Done, via `.MXP` rather than the
   raw binary format.* `.csd` is a proprietary multi-table binary
   flat-file (no dBase/Paradox/SQLite header — tables are just
   concatenated fixed-length records), written by a VB6 desktop app
   (CricketStatz, Red Axe Pty Ltd) using fixed-length random-access record
   I/O — which is why the player table (partially mapped below, now
   superseded) is uniform 648-byte records.

   What actually shipped is `mxp_parser.py`, parsing the app's own
   **File → Export/Email Matches** output (`.MXP` — plain, fully
   documented `Key=Value` text, see `MXP Format.doc`) into the same
   internal shape `Scorecard` expects, exactly like `crichq_pdf.py` does
   for CricHQ PDFs. Validated end to end against the club's complete
   real archive (`ELPM2018_all_matches.mxp`, 304 matches, 2005-04-23 to
   2018-07-21): zero foreign-key violations, and batting/bowling figures
   for the bundled Bodyline Test demo data match real cricket history
   exactly (Larwood 5/96, McCabe's 187\*, all five 1932-33 Test results).
   See "Modules" above for what the parser does and does not model (the
   `fow`/`fowpos` fields turned out not to be trustworthy fall-of-wickets
   data — verified, not assumed).

   Getting there required reverse-engineering-adjacent detective work
   more than binary parsing: the CricketStatz `.exe` installers
   (`cstatz05.exe`/`cstatz10.exe`/`cricketstatz11.exe`) run under Wine
   (wine32/wine64 + a Wine virtual desktop — needed for the custom-drawn
   VB6 popups/menus to render at all; without one they paint solid
   black), registered with a purchased club-wide license, opening each
   of the four `.csd` backups in the repo in turn and using File →
   Export/Email Matches. The 2018 archive specifically needed
   `cricketstatz11.exe` (build 11.2.49) — CricketStatz refuses to open a
   file newer than the installed version, and `ELPM2018.csd`'s version
   tag (`"11  4\0"`, format version **11**) was newer than the first
   installer tried (10.5.1, format version 10-era, matching the
   `"2005\x04\0"` tag in the installer's own bundled `sample.csd`).
   Registering v11 with the same code that worked for v10 failed ("still
   unregistered" — may need a v11-specific code), but that turned out not
   to matter: opening and exporting existing data works fine in trial
   mode; the 10-match limit only blocks *entering new* matches. The
   v11 installer's own version-detection dialog (uninstalling 10.5.1
   first) also isn't always raised above the main window — easy to
   mistake for a hang.

   The raw-binary mapping below is now superseded (`.MXP` covers
   everything needed) but kept as a record of what was found, in case a
   `.csd` ever needs reading without the app available:
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
     - The first bytes of the file are a version tag: `ELPM2018.csd` starts
       `"11  4\0"` (format version **11**), vs. `"2005\x04\0"` in the
       installer's bundled `sample.csd` (format version 2005). The
       CricketStatz app refuses to open a file newer than itself.

4. **Reconciliation layer** — *Proof of concept done for players
   (`reconcile.py`); automatic matching, and club/team reconciliation,
   still not built.* Full automatic matching across every player/club/
   team is the hard part (initials-only names, no stable id across
   sources — see "Not built yet") and isn't attempted. What exists
   instead is a small, real mechanism: `merge_players()` repoints a
   list of confirmed `(source, source_player_id)` refs — already each
   resolving to their own canonical player from ingestion — onto one
   surviving `player_id`, updating every fact-table column that
   references it (`batting_innings.player_id`/`bowler_player_id`/
   `fielder_player_id`, `bowling_innings.player_id`,
   `match_appearances.player_id`) and `player_source_ids` itself, then
   drops the now-unreferenced duplicate rows. A human-curated
   `PLAYER_MERGES` list in the same file is the growable registry of
   confirmed groups — this is the intended path to add more reconciled
   players later (e.g. after importing further CricHQ PDFs), not a
   replacement for automatic matching.

   No query-layer changes were needed to prove this out:
   `career_stats()` already aggregates purely by `player_id`, so once
   a merge lands, a genuinely cross-source career total just falls out
   of the existing query. Proved against **Ian Wade**: merging his
   Play-Cricket id, CricHQ PDF name, and two CricketStatz ids (see
   below) produces one combined career — **151 games, 3895 runs at
   31.7 (18 fifties, 7 hundreds), 107 wickets at 15.9 (7 five-fors),
   63 catches** — spanning 2005-2018 (cricketstatz, 138 matches), one
   2019 match (crichq_pdf), and the current 2026 season (play_cricket,
   12 matches). Zero foreign-key violations after merging.

   Two real data-quality issues turned up along the way, both worth
   recording:
     - **A genuine bug, fixed**: Play-Cricket's own numeric player ids
       were splitting into two canonical rows for the same person
       (`"6216362"` vs `"6216362.0"`). Cause: `pd.json_normalize()`
       upgrades a whole int column to float64 the moment *any* row in
       it is missing (the same NaN-upgrade behaviour already
       documented in `sqlite_store.py` for fielder/bowler ids), so the
       same real id str()'d differently match to match, depending on
       whether some *other* player in that particular match had a gap.
       Fixed centrally in `SQLiteStore._clean_text()` (whole-number
       floats, real or already stringified, normalise back to plain
       int form) — affects every source, not just Play-Cricket, and
       every id-like text column, not just players.
     - **A parser edge case, deliberately left unmerged**: CricHQ
       credits a joint run-out to both fielders as one combined dismissal
       string (`"run out (I Wade/MR Robinson)"`); `crichq_pdf.py` keeps
       that as a single fielder name rather than splitting it (the
       schema only has one `fielder_player_id` slot per dismissal
       either way). That row was deliberately left out of Ian Wade's
       merge group — including it would misattribute MR Robinson's
       share of the credit to Wade, which is a worse error than
       under-counting his run-out assists by one.
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
