# playcricket_stats

A club cricket statistics database that reconciles scorecard data from
several sources into a single queryable store:

1. **Play-Cricket API** — the live/current source, kept in sync with a
   minimal number of API requests.
2. **CricHQ PDF archive scorecards** — historical matches predating
   Play-Cricket, currently sitting in the club's PDF archive.
3. **A legacy binary-format database** — CricketStatz `.csd` files, an
   older desktop stats package used before Play-Cricket/CricHQ, read via
   its bulk `.MXP` export (`mxp_parser.py`).
4. **Individual CricketStatz text scorecards** (`cricketstatz_txt.py`) —
   match-by-match printouts in the same CricketStatz era, filling a
   season (2010) the bulk `.MXP` export doesn't cover at all.
5. **North Manchester Cricket League season averages** (`nmcl_stats.py`)
   — not a full scorecard source, but season-aggregate batting/bowling/
   wicketkeeping figures (scanned pre-2005, native Excel 2011-2013) that
   supplement career stats for seasons with no match-level source, or
   fill in specific matches known to be missing from one.
6. **Hand-scored scorebook pages** (`scorebooks.py`) — full match-level
   scorecards that only ever existed on paper, photographed and
   transcribed by hand (read directly, not OCR'd) when a genuinely
   missing match turns up this way rather than as any digital record.

Once merged, the goal is to support historical and career stats, records
queryable by team/season/player, leaderboards, printable/frameable scorecard
exports for milestone achievements (centuries, five-wicket hauls, career
milestones), and social-media-formatted summaries of individual performances
and weekend results.

**All six original data sources are now imported** — 964 matches raw, 932
once reconciled, zero foreign-key violations. See
[development_notes.md](development_notes.md) for the full milestone writeup
and the detailed story behind every module, and [ROADMAP.md](ROADMAP.md) for
what's still outstanding.

## Contents

- [Core structure](#core-structure)
  - [Modules](#modules)
- [Using the example files](#using-the-example-files) — moved to [EXAMPLES.md](EXAMPLES.md)
- [Using the main database](#using-the-main-database)
  - [Build the full database once](#build-the-full-database-once)
  - [Querying the database in ipython](#querying-the-database-in-ipython)
    - [What can you filter by?](#what-can-you-filter-by)
    - [Look up one match's scorecard](#look-up-one-matchs-scorecard)
    - [Search for matches by criteria](#search-for-matches-by-criteria)
    - [Team records by season](#team-records-by-season)
    - [Career stats and leaderboards](#career-stats-and-leaderboards)
- [Documentation](#documentation)

## Core structure

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

Six sources feed the same normalised SQLite store (`source` on every fact
table): `play_cricket`, `crichq_pdf`, `cricketstatz`, `cricketstatz_txt`,
`nmcl_stats` (season-aggregate only, no match-level rows), and `scorebook`.
Cross-source identity (the same real player/club/team/ground under
different names or ids) is resolved by a mix of automatic merging at
insert time (clubs/teams, exact/near-exact names only) and a
human-curated registry, `reconcile/decisions.yaml`, applied by
`reconcile.py` — see [ROADMAP.md](ROADMAP.md) for what's automatic today
versus what still needs a human.

### Modules

- **`playcricket_api.py`** — Stateless Play-Cricket API client: fetches
  season match lists and full match-detail JSON.
- **`playcricket_database.py`** — Local JSON cache with change-aware
  syncing (`sync_season()`), API-call minimisation, no business logic.
- **`playcricket_scorecard.py`** — Turns one raw match-detail record into
  batting/bowling/partnership/fall-of-wickets DataFrames, milestone
  detection, and a `print_scorecard()` renderer.
- **`schema.sql`** / **`sqlite_store.py`** — The normalised SQLite store
  (clubs, teams, players, matches, innings, batting/bowling, team sheets),
  with automatic conservative club/team merging across sources at insert
  time and a `teams.is_juniors` flag driving the `include_juniors` filter.
- **`crichq_pdf.py`** — Parses CricHQ "Full Scorecard Report" PDF exports
  into the same shape `Scorecard` expects (`source="crichq_pdf"`).
- **`mxp_parser.py`** — Parses CricketStatz `.MXP` exports
  (`source="cricketstatz"`), CricketStatz's own documented `Key=Value`
  export format.
- **`cricketstatz_txt.py`** — Parses individual CricketStatz text
  scorecards (`source="cricketstatz_txt"`), filling a season the bulk
  `.MXP` export doesn't reach.
- **`nmcl_stats.py`** — Ingests North Manchester Cricket League season
  "Final Averages" reports into `nmcl_season_stats` — season-aggregate
  figures, not full scorecards, for seasons with no match-level source.
- **`scorebooks.py`** — Transcribes hand-scored scorebook photographs into
  full match-level scorecards (`source="scorebook"`) for matches missing
  from every other source.
- **`sqlite_queries.py`** — The query/leaderboard layer: `career_stats()`
  and `SQLPlayerStats`, with `season`/`team_id`/`elpmcc_only`/
  `include_juniors`/`include_nmcl` filters. See
  [Using the main database](#using-the-main-database) below for the full
  parameter reference and worked examples.
- **`reconcile/decisions.yaml`** — The human-curated record of every
  cross-source identity decision (merges, home grounds, ground overrides,
  confirmed duplicate matches).
- **`reconcile.py`** — Applies `decisions.yaml` to the database
  (`--check`/`--promote` for validating and promoting reviewed
  candidates).
- **`reconcile_audit.py`** — Generates `reconcile/data_quality_report.md`
  and writes new reconciliation candidates into `decisions.yaml`'s
  `pending:` section for review.
- **`club_awards.py`** — Ingests manually-curated club/team/player honours
  (league/cup wins, season average winners, players' player of the year,
  club captaincy) into `team_awards`/`player_awards`. Must be run **after**
  `reconcile.py` — see [Using the main database](#using-the-main-database).

Full development history for each module — bug stories, validation
numbers, and the reasoning behind each design choice — is in
[development_notes.md](development_notes.md#modules); auto-generated
docstring reference is in the [Sphinx docs](#documentation).

## Using the example files

A separate, hands-on walkthrough against the small frozen sample files
already in the repo (build the demo store, look at one scorecard, run
career stats/leaderboards, ingest a CricHQ PDF, reconcile a player,
attach awards, audit for data quality) lives in
**[EXAMPLES.md](EXAMPLES.md)** — start there if you want to see each
piece working in isolation before pointing anything at real data.

The rest of this section is the main event: the real, amalgamated,
continuously-maintained database, and how to actually query it.

## Using the main database

This is the real, amalgamated, continuously-maintained database — every
match the club has any record of, from every source, in one queryable
SQLite file. **It's never committed to this repo** — `.gitignore` excludes
`*.sqlite`/`*.sqlite3` on purpose (see "If in doubt" below for why). What
*is* committed are the ingredients: every source file under `playcricket/`,
`crichq/`, `cricketstatz/`, `nmcl stats/`, `scorebooks/`, plus
`reconcile/decisions.yaml` and `club_awards.py`'s hardcoded honours. You
build the actual queryable database locally, once, from those — amalgamating
**all six sources** (see the intro at the top of this README and the
[Core structure](#core-structure) diagram), not just Play-Cricket.

### Build the full database once (in Terminal)

Run every ingestion script in order, against one persistent filename
(`playcricket_stats.sqlite` below — pick whatever name you like, it's just a
local file, and it doesn't need to exist beforehand: each script creates it
on first use via `schema.sql`):

```bash
python3 sqlite_store.py --json-db playcricket/playcricket_24_25_26.json --sqlite-db playcricket_stats.sqlite
python3 crichq_pdf.py crichq/ALL_CRICHQ_SCORECARDS.pdf --sqlite-db playcricket_stats.sqlite
python3 mxp_parser.py cricketstatz/ELPM2018_all_matches.mxp --sqlite-db playcricket_stats.sqlite
python3 cricketstatz_txt.py cricketstatz/2010\ scorecards/*.txt --sqlite-db playcricket_stats.sqlite
python3 nmcl_stats.py --sqlite-db playcricket_stats.sqlite
python3 scorebooks.py --sqlite-db playcricket_stats.sqlite
python3 reconcile.py --sqlite-db playcricket_stats.sqlite
python3 club_awards.py --sqlite-db playcricket_stats.sqlite
```

Order matters for the last two only — `reconcile.py` needs every source
already loaded so it has something to merge, and `club_awards.py` needs
`reconcile.py` to have already run since it resolves players/teams by exact
match against already-canonical rows — the first six can run in any order.
This is the same six sources listed at the top of this
README, all landing in one store: **248 Play-Cricket + 374 CricHQ + 304
CricketStatz + 37 CricketStatz-text matches, plus 77 NMCL season-aggregate
rows (no match rows of their own) and 1 scorebook match** — see
[development_notes.md](development_notes.md) for the exact reconciled
totals once duplicates are removed. This is a **one-time build**; see
"Play-Cricket — the one source that actually needs re-syncing" below for
what to re-run afterward, rather than repeating this whole sequence.

### Querying the database in ipython

**Run this once, before any example below.** Everything here is plain
Python (no CLI, no server) — `sqlite3` is part of the standard library,
but `pandas` is a separate package, and every example below needs both:

```bash
pip install ipython pandas
cd playcricket_stats
ipython
```

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("playcricket_stats.sqlite")   # the file the build step above created
```

Keep this `conn` (and the `pd`/`sqlite3` imports) alive for the rest of the
session — every example below reuses them, and each one only shows the
*extra* import it specifically needs on top of these two, not these two
again. If you get `NameError: name 'pd' is not defined` (or `conn`), it
means this block hasn't been run yet in your current session — pasting one
query in isolation into a fresh `ipython`/script without it first is the
most common way to hit that. Reconnect (re-run the `conn = ...` line) after
re-building or re-ingesting anything, so you're not reading a stale
connection.

#### What can you filter by?

Every example below is plain SQL against the tables in `schema.sql`, so
"what can I filter by" is really "what columns exist" — the ones that come
up constantly:

| Table | Useful filter columns | Example predicate |
|---|---|---|
| `matches` | `season`, `match_date`, `competition_name`, `league_name`, `source`, `status` | `WHERE m.season = 2024` |
| `matches` (via `teams`/`clubs`) | opponent/home/away club or team name (join, see below) | `WHERE hc.club_name = 'Shaw CC'` |
| `batting_innings` | `runs`, `balls`, `fours`, `sixes`, `how_out`, `not_out` | `WHERE b.runs >= 100` |
| `bowling_innings` | `wickets`, `runs`, `overs`, `maidens` | `WHERE bo.wickets >= 5` |
| `players` | `known_as` (exact name) | `WHERE p.known_as = 'Ian Wade'` |
| `clubs` / `teams` | `club_name` / `team_name` | `WHERE c.club_name = 'East Lancs Paper Mill CC'` |

`matches` doesn't store club/team names directly — only `home_team_id`/
`away_team_id` — so filtering by an opponent's name always means joining
`teams`/`clubs` in, exactly like the Shaw CC example below does. Combine
any of these with plain SQL `AND`/`OR`, e.g. "Ian Wade's centuries" is just
the centuries query below with an extra `AND p.known_as = 'Ian Wade'`.
Player/club/team names must match exactly (`known_as`/`club_name`/
`team_name` as stored) — if a name doesn't return anything, check the exact
spelling with e.g. `SELECT DISTINCT club_name FROM clubs WHERE club_name
LIKE '%shaw%'` first (case-insensitive by default in SQLite's `LIKE`).

#### Look up one match's scorecard

*(needs `conn` and `pd` from the setup above)*

Every match, from every source, carries its original parsed match-detail
dict verbatim in `matches.source_payload` (JSON text) — so `Scorecard`
(`playcricket_scorecard.py`) can render *any* match in the database, not
just Play-Cricket ones, once you have its `match_id`:

```python
import json
from playcricket_scorecard import Scorecard

def scorecard_for(match_id):
    payload = conn.execute(
        "SELECT source_payload FROM matches WHERE match_id = ?", (match_id,)
    ).fetchone()[0]
    return Scorecard(json.loads(payload))

scorecard_for(429).print_scorecard()   # any match_id -- Play-Cricket, CricHQ, CricketStatz, etc.
```

To find a specific match's `match_id` in the first place — by date and
opposition, since that's usually what you actually remember:

```python
pd.read_sql_query(
    """
    SELECT m.match_id, m.season, m.match_date, m.source,
           hc.club_name AS home_club, ht.team_name AS home_team,
           ac.club_name AS away_club, at.team_name AS away_team,
           m.result_description
    FROM matches m
    JOIN teams ht ON ht.team_id = m.home_team_id
    JOIN clubs hc ON hc.club_id = ht.club_id
    JOIN teams at ON at.team_id = m.away_team_id
    JOIN clubs ac ON ac.club_id = at.club_id
    WHERE m.match_date = '07/07/2024'
    """,
    conn
)
```

#### Search for matches by criteria

*(needs `conn` and `pd` from the setup above, plus `scorecard_for()`
defined in the previous section)*

The pattern for any "find matches where..." question is the same: query for
an **index** of matching matches first (id, date, opposition, result — cheap
and quick to scan), then call `scorecard_for(match_id)` above on whichever
one you actually want to look at in full. Two concrete examples:

**Every match against a specific club** (e.g. Shaw CC — matches either home
or away):

```python
vs_shaw = pd.read_sql_query(
    """
    SELECT m.match_id, m.season, m.match_date, m.source,
           hc.club_name AS home_club, ht.team_name AS home_team,
           ac.club_name AS away_club, at.team_name AS away_team,
           m.result_description
    FROM matches m
    JOIN teams ht ON ht.team_id = m.home_team_id
    JOIN clubs hc ON hc.club_id = ht.club_id
    JOIN teams at ON at.team_id = m.away_team_id
    JOIN clubs ac ON ac.club_id = at.club_id
    WHERE hc.club_name = 'Shaw CC' OR ac.club_name = 'Shaw CC'
    ORDER BY m.match_date
    """,
    conn
)
vs_shaw                              # the index -- scan it, pick a match_id
scorecard_for(vs_shaw.iloc[0]["match_id"]).print_scorecard()   # then look at one
```

**Every innings where a player scored a century** (100+), across every
source and every player, most recent/highest first:

```python
centuries = pd.read_sql_query(
    """
    SELECT m.match_id, m.match_date, m.season, p.known_as AS batsman,
           b.runs, b.balls, hc.club_name AS home_club, ac.club_name AS away_club
    FROM batting_innings b
    JOIN innings i ON i.innings_id = b.innings_id
    JOIN matches m ON m.match_id = i.match_id
    JOIN players p ON p.player_id = b.player_id
    JOIN teams ht ON ht.team_id = m.home_team_id
    JOIN clubs hc ON hc.club_id = ht.club_id
    JOIN teams at ON at.team_id = m.away_team_id
    JOIN clubs ac ON ac.club_id = at.club_id
    WHERE b.runs >= 100
    ORDER BY b.runs DESC
    """,
    conn
)
centuries                            # the index -- e.g. 98 centuries across the archive
scorecard_for(centuries.iloc[0]["match_id"]).print_scorecard()   # the highest one, in full
```

The same shape answers most other "find the match(es) where..." questions —
swap the `WHERE` clause for a different table/condition (`bowling_innings`
for a 5-wicket haul, `m.season = 2024` for one season, `m.competition_name
LIKE '%Cup%'` for a specific competition, and so on).

#### Team records by season

*(needs `conn` and `pd` from the setup above)*

There's no dedicated function for this yet (see [ROADMAP.md](ROADMAP.md)
item 5) — it's a plain query over `matches.result_applied_to`, the one
result field that's reliably comparable across every source regardless of
how differently each one formats its own `result` text (Play-Cricket uses
letter codes, CricHQ/CricketStatz free text, etc. — see `schema.sql`):
`result_applied_to` is the winning team's `team_id` whenever a match had a
clear winner, and `NULL` otherwise (a draw, tie, no-result, abandoned game,
**or** simply a match whose result was never recorded by that source — SQL
alone can't tell those apart, so treat this bucket as "not a confirmed win",
not "definitely a draw").

**One team, every season** — find the `team_id` once, then group by season:

```python
team_id = conn.execute(
    "SELECT t.team_id FROM teams t JOIN clubs c ON c.club_id = t.club_id "
    "WHERE c.club_name = ? AND t.team_name LIKE '%' || ?",
    ("East Lancs Paper Mill CC", "1st XI")
).fetchone()[0]

pd.read_sql_query(
    """
    SELECT
        m.season,
        SUM(CASE WHEN m.result_applied_to = :team_id THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN m.result_applied_to IS NOT NULL
                 AND m.result_applied_to != :team_id THEN 1 ELSE 0 END) AS losses,
        SUM(CASE WHEN m.result_applied_to IS NULL THEN 1 ELSE 0 END) AS drawn_or_unrecorded,
        COUNT(*) AS played
    FROM matches m
    WHERE m.home_team_id = :team_id OR m.away_team_id = :team_id
    GROUP BY m.season
    ORDER BY m.season
    """,
    conn, params={"team_id": team_id}
)
```

**Every one of this club's teams, one season** — same shape, grouped by
team instead of season, filtered to one season instead of one team:

```python
pd.read_sql_query(
    """
    SELECT
        t.team_name,
        SUM(CASE WHEN m.result_applied_to = t.team_id THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN m.result_applied_to IS NOT NULL
                 AND m.result_applied_to != t.team_id THEN 1 ELSE 0 END) AS losses,
        SUM(CASE WHEN m.result_applied_to IS NULL THEN 1 ELSE 0 END) AS drawn_or_unrecorded,
        COUNT(*) AS played
    FROM matches m
    JOIN teams t ON t.team_id IN (m.home_team_id, m.away_team_id)
    JOIN clubs c ON c.club_id = t.club_id
    WHERE c.club_name = 'East Lancs Paper Mill CC' AND m.season = 2024
    GROUP BY t.team_id
    ORDER BY wins DESC
    """,
    conn
)
```

Drop the `season`/`team_id` filter from either query (and its `GROUP BY`
column) to get the same breakdown for the **whole database** — one team's
record across every season it's ever played, or every team's combined
record across every season on record.

#### Career stats and leaderboards

*(needs `conn` from the setup above)*

This is the main "what does this player's/team's record actually look
like" check — everything comes from `sqlite_queries.py`'s two entry points:
`career_stats()` (one row per player) and `SQLPlayerStats` (leaderboards
built on top of it).

```python
from sqlite_queries import career_stats, SQLPlayerStats, player_awards, team_awards

career = career_stats(conn, elpmcc_only=False)   # every player, full amalgamated career
career[career["player_name"] == "Ian Wade"].T      # one player, transposed so it's readable

stats = SQLPlayerStats(conn)
stats.top_runs(top_n=10)                       # club-wide, all-time leaderboard
stats.top_runs(season=2024, top_n=10)            # restricted to one season
stats.top_wickets(team_id=team_id, top_n=10)       # restricted to one team (from above)
```

This is a genuine career total across every source a player appears in, not
a per-source figure: `career_stats()` aggregates by `player_id` alone, so
once `reconcile.py` has merged a player's Play-Cricket/CricHQ/CricketStatz
identities into one canonical row, their combined batting/bowling/fielding
totals come back as a single row automatically — no per-source lookup or
manual addition needed.

Every function above takes the same filter keywords:

| Keyword | Default | Effect |
|---|---|---|
| `season=2024` | `None` (all seasons) | Restricts every total to matches in that season. |
| `team_id=5` | `None` (every team) | Restricts to one specific team — splits a player's stats by team instead of a true career total. |
| `elpmcc_only=True` | `True` | Only players who've appeared for `elpmcc_name`'s teams get a career-stats row at all. Pass `False` to include opposition players too. |
| `elpmcc_name="..."` | `"East Lancs Paper Mill CC"` | Which club `elpmcc_only` means — pass any `club_name` to get that club's own combined career stats instead. |
| `include_juniors=False` | `False` | Junior teams (`teams.is_juniors`) are excluded by default. Pass `True` to include them. |
| `include_nmcl=False` | `False` | Whether `nmcl_stats.py`'s season-aggregate rows (seasons with no match-level source) contribute to the totals. |

`SQLPlayerStats(conn, elpmcc_only=..., ...)` sets these once for every
leaderboard method on that instance; `career_stats(conn, ...)` takes them
per call. See [EXAMPLES.md](EXAMPLES.md) step 3 for the full leaderboard
method list (`top_batting_average`, `top_economy`, `highlights`, etc.) and
step 3's "club vs team stats" note for combined-club-not-just-one-team
queries.

Individual honours (season average winners, players' player of the year,
club captaincy — see `club_awards.py`) show up directly in career stats'
`awards` column, and can be queried on their own:

```python
career[career["player_name"] == "Ian Wade"]["awards"].iloc[0]
# '2009 NMCL Bowling Average Winner; 2011 Club Captain; ...'

player_awards(conn, season=2012)   # every individual honour awarded in 2012
team_awards(conn)                    # every team honour (league/cup wins), every season
```

The two source *types* feeding this database need completely different
maintenance rhythms after this first build, because one is closed and one
isn't:

### Archive sources (CricHQ, CricketStatz) — import once, then leave alone

`crichq/ALL_CRICHQ_SCORECARDS.pdf` and `cricketstatz/ELPM2018_all_matches.mxp`
describe matches that have already happened and been fully scored — they
are not going to change. Play-Cricket's own scorecards *can* be edited
after the fact (that's exactly why the live source needs re-syncing, see
below); a CricHQ PDF or a CricketStatz export is a static snapshot someone
generated once and isn't going to be regenerated.

This is why `insert_match()` writes with
`ON CONFLICT(source, source_match_id) DO NOTHING` (`sqlite_store.py`): a
match already in the database, from a given source, is never overwritten.
Concretely, this means:

- **Re-running `crichq_pdf.py`/`mxp_parser.py` against a file you've
  already ingested is always a safe no-op.** Nothing duplicates, nothing
  changes. There's no harm in doing it "just in case" — you'll never need
  to, but it won't corrupt anything if you do.
- **You only need to run them again when there's a genuinely new file** —
  another old CricHQ PDF turns up, another `.csd` backup gets found, etc.
  — or **after a parser bug fix you want reflected in already-loaded
  data**. `ON CONFLICT DO NOTHING` means a bugfix re-import *won't*
  update rows already sitting in the database, so that second case needs
  the old rows removed first:
  `DELETE FROM matches WHERE source = 'crichq_pdf'` (or `'cricketstatz'`)
  before re-running the ingestion script — `ON DELETE CASCADE` on
  `innings`/`batting_innings`/`bowling_innings`/`match_appearances` cleans
  up everything downstream of that match automatically. There's no CLI
  flag for this today; it's a manual SQL statement.
- Once ingested (and reconciled, see below, for any player that needs it),
  an archive source needs **no ongoing maintenance at all**. That's the
  whole point of it being an archive.

### Play-Cricket — the one source that actually needs re-syncing

This is the only source still generating new matches — new fixtures get
added and scored throughout the season, and Play-Cricket lets scorers edit
a scorecard after the original result was entered (which is exactly what
the API's `last_updated` field, and `sync_season()`'s comparison against
it, exist to detect). Keeping this source current is a two-step,
recurring job — pull the latest from the API into the local JSON cache,
then rebuild that source's rows in the SQLite store from the refreshed
cache:

```python
from playcricket_api import PlayCricketAPI
from playcricket_database import PlayCricketDatabase

api = PlayCricketAPI(site_id=9653)   # ELPMCC's Play-Cricket site id
# api_key comes from the PLAY_CRICKET_API_KEY env var by default,
# or pass api_key="..." explicitly here instead

db = PlayCricketDatabase(api=api, filename="playcricket/playcricket_24_25_26.json")
db.sync_season(2026)   # fetches new/changed matches, saves the JSON cache
```

```bash
python3 sqlite_store.py --json-db playcricket/playcricket_24_25_26.json --sqlite-db playcricket_stats.sqlite
```

(`playcricket/playcricket_24_25_26.json` is the real, maintained cache —
currently seasons 2024-2026, 248 matches. One JSON cache file can hold every
season, keyed internally by season number; see the backfill loop below. The
similarly-named `playcricket/playcricket_2026_demo.json` is a separate,
deliberately frozen file — the small fixed dataset the
[Using the example files](#using-the-example-files) walkthrough runs
against — and isn't meant to be kept in sync the way this one is.)

`sync_season()` always requests the current match list (one API call) but
only re-downloads match *detail* for matches that are new, changed
(`last_updated` moved on), or incomplete locally — so a routine re-sync is
cheap regardless of how large the season gets. `sqlite_store.py`'s rebuild
step makes no API calls at all: it deletes and reinserts every
`play_cricket` match from whatever's currently in the JSON cache, so it's
safe and cheap to run after every sync, every time.

**To get the club's full Play-Cricket history**, not just the current
season, call `sync_season()` once per season, back to whenever ELPMCC
started using Play-Cricket. Seasons 2024-2026 are already in
`playcricket/playcricket_24_25_26.json`; earlier seasons (Play-Cricket
presumably starts sometime in the 2018-2023 range CricHQ already covers,
exact start year not yet confirmed) are still a gap if full Play-Cricket
history is wanted rather than relying on CricHQ for that period:

```python
for season in range(2018, 2027):   # adjust the start year to when it began
    db.sync_season(season)
```

Older seasons won't have `last_updated` changes to pick up, so this is a
one-time backfill — after that, only the current season needs a routine
re-sync (a scheduled job, run manually before a stats update, etc. —
nothing in this project schedules it automatically yet, see
[ROADMAP.md](ROADMAP.md) item 8).

**Directly answering "do I just run the API-connect and database
files?"**: not quite as they stand — `playcricket_api.py` and
`playcricket_database.py` are libraries with no CLI entry point (only
`sqlite_store.py` has one, and it deliberately never touches the API — see
its own module docstring). The snippet above is what running them
actually looks like today. A small `sync_playcricket.py` wrapping both
steps into one command (`python3 sync_playcricket.py --season 2026`)
would be a natural, easy addition if this becomes a routine task —
not built yet, flagged in [ROADMAP.md](ROADMAP.md) rather than assumed.

### Reconciliation is a separate, occasional pass

`reconcile.py` (or `SQLiteStore.merge_players()`) only needs re-running
when a **new** source is ingested for the first time, or a freshly-added
archive file introduces a player who needs merging into an existing
identity. A routine Play-Cricket re-sync doesn't need it re-applied:
`player_source_ids` permanently remembers which source ids already point
at which canonical player, so a player merged once stays merged across
every future sync of a source already known to the database.

### If in doubt: everything here is safely rebuildable from scratch

Every step above is idempotent and none of them mutate the source JSON/
PDF/`.MXP`/`.txt`/`.xls`/`.csd` files or `reconcile/decisions.yaml` — only
the derived `.sqlite` file. So if the database ever ends up in a state you
don't trust, just delete it and repeat
["Build the full database once"](#build-the-full-database-once) above —
that same command sequence always gets back to the same result from the
committed source files alone. This is exactly why the `.sqlite` file is
never committed to version control (`.gitignore` excludes `*.sqlite`/
`*.sqlite3`): it's fully and deterministically reproducible from what *is*
committed, so keeping it out of git avoids a large binary file that would
only go stale the moment any source file or `decisions.yaml` changes.

## Documentation

- **[EXAMPLES.md](EXAMPLES.md)** — the hands-on walkthrough against the
  small frozen sample files (build the demo store, look at one scorecard,
  ingest a CricHQ PDF, reconcile a player, attach awards, audit for data
  quality). Start here to see each piece working in isolation; see
  [Using the main database](#using-the-main-database) above for the real
  data.
- **[development_notes.md](development_notes.md)** — the full development
  history: the "all data imported" milestone writeup, every module's
  detailed design/bug notes, retired code, and the full sample-data
  inventory.
- **[ROADMAP.md](ROADMAP.md)** — outstanding issues ("Not built yet") and
  the numbered project roadmap.
- **Sphinx API reference** (`docs/`) — generated from every module's own
  docstrings. Build and view it locally:

  ```bash
  pip install -r docs/requirements.txt
  cd docs
  make html
  open _build/html/index.html   # or just open the file in a browser
  ```
