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
- [Using the example files](#using-the-example-files)
- [Using the main database](#using-the-main-database)
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
  [Using the example files](#using-the-example-files) below for the full
  walkthrough.
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

Everything is a plain Python library today, so the easiest way to check
progress is to import the pieces directly in an `ipython` session and look
at what comes back. This section works entirely against the small,
frozen sample files already in the repo — nothing needs an API key to run.
For the real, continuously-maintained database, see
[Using the main database](#using-the-main-database) below.

One-time setup:

```bash
pip install ipython pandas numpy requests pypdf ruamel.yaml
cd playcricket_stats
ipython
```

The examples below all use the files already in the repo
(`playcricket/playcricket_2026_demo.json`, `crichq/ALL_CRICHQ_SCORECARDS.pdf`).

### 1. Build the SQLite store from the sample Play-Cricket data

This is usually run from the Terminal, not ipython, since it's a one-shot
build step:

```bash
python3 sqlite_store.py --json-db playcricket/playcricket_2026_demo.json --sqlite-db demo.sqlite
```

```
Built 70 matches into demo.sqlite
```

### 2. Look at one match's scorecard

Good for eyeballing that a match parsed correctly against what you remember
of the game. `Scorecard` (`playcricket_scorecard.py`) turns one raw
match-detail dict — from the JSON cache, or from any source's own parser
before it reaches SQLite (`crichq_pdf.parse_pdf()`,
`mxp_parser.parse_mxp()`, etc. all produce the same shape) — into
DataFrames and a printable card, with no database involved:

```python
from playcricket_database import PlayCricketDatabase
from playcricket_scorecard import Scorecard

db = PlayCricketDatabase(api=None, filename="playcricket/playcricket_2026_demo.json")

# db.match_details(season=2026) lists every match; db.match(match_id) gets
# one. Both return the raw stored API response, so unwrap ["match_details"][0]
# to get the record Scorecard expects.
raw = db.match(7239375)
sc = Scorecard(raw["match_details"][0])
```

The most useful calls, roughly in the order you'd reach for them:

```python
sc.teams()               # {'home': '...', 'away': '...'}
sc.get_result()           # 'East Lancs Paper Mill CC - 1st XI - Won'
sc.summary()                # dict: date, competition, ground, teams, result -- one glance

sc.batting_table(1)           # innings-1 batting card as a DataFrame (name, runs, balls, 4s, 6s, how out)
sc.bowling_table(1)            # innings-1 bowling figures (overs, maidens, runs, wickets, economy)
sc.fall_of_wickets(1)           # innings-1 partnership breaks, one row per wicket (score, batsman out)
sc.get_performances()             # milestones this match crossed: fifties, hundreds, 5-wicket hauls

sc.print_scorecard()                # the whole thing, both innings, plain text -- start here
```

`print_scorecard()` is almost always the right first call — it renders
both innings' batting, extras, fall of wickets, and bowling in one
readable block, the same shape a scorer would recognise from a real
scorecard. The individual methods above (`batting_table`/`bowling_table`/
etc.) are for when you want one piece of it as a DataFrame to filter,
sort, or feed into something else, rather than the whole printed card.

**This is a single-match, single-source view** — `Scorecard` reads one raw
match-detail dict, so it only ever shows one match from wherever that dict
came from (here, the Play-Cricket JSON cache). Once a match is in the
unified SQLite store (any of the five match-level sources — everything
except `nmcl_stats.py`'s season aggregates), looking
it up works the same way regardless of which source it came from, via
plain SQL against the normalised tables instead:

```python
import sqlite3
conn = sqlite3.connect("demo.sqlite")

match_id = conn.execute(
    "SELECT match_id FROM matches WHERE source='play_cricket' AND source_match_id='7239375'"
).fetchone()[0]

conn.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()

# One innings' batting card, any source, straight from the normalised tables:
import pandas as pd
pd.read_sql_query(
    """
    SELECT p.known_as AS batsman, b.runs, b.balls, b.fours, b.sixes, b.how_out
    FROM batting_innings b
    JOIN innings i ON i.innings_id = b.innings_id
    JOIN players p ON p.player_id = b.player_id
    WHERE i.match_id = ? AND i.innings_number = 1
    ORDER BY b.position
    """,
    conn, params=(match_id,)
)
```

### 3. Query career stats and leaderboards

This is the main "did this actually work" check — cross-check a name or
figure you know against what comes back. Everything here comes from
`sqlite_queries.py`'s two entry points: `career_stats()` (one row per
player) and `SQLPlayerStats` (leaderboards built on top of it) — see that
module's own bullet under [Modules](#modules) for the full parameter
reference.

**Multi-player stats (leaderboards)** — `SQLPlayerStats` is the "many
players at once, ranked" view. Every method below returns the top `top_n`
players by that metric, and most take a `min_*` qualification threshold
(the same defaults `MultiPlayerStats`, the retired pandas equivalent,
used) so someone with 2 games and a lucky 80\* doesn't outrank a
top-order regular:

```python
import sqlite3
from sqlite_queries import SQLPlayerStats

conn = sqlite3.connect("demo.sqlite")
stats = SQLPlayerStats(conn)

stats.top_runs(top_n=10)                    # most career runs
stats.top_batting_average(top_n=10)          # min_batting_innings=5 by default
stats.top_strike_rate(top_n=10)               # min_batting_innings=5, min_runs=50
stats.top_scores(top_n=10)                     # single highest innings
stats.top_fifties(top_n=10)                     # most 50s (counts both 50s and 100s toward "fifties")
stats.top_hundreds(top_n=10)                     # most 100s (200s count too)

stats.top_wickets(top_n=10)                       # most career wickets
stats.top_bowling_average(top_n=10)                # min_bowling_innings=5, min_wickets=5; lowest wins
stats.top_economy(top_n=10)                         # same thresholds; lowest wins
stats.top_bowling_strike_rate(top_n=10)              # same thresholds; lowest wins

stats.top_catches(top_n=10)                           # fielding dismissals credited via how_out
stats.top_fielding(top_n=10)                           # catches + stumpings + run-outs combined
stats.highlights(top_n=10)                              # most milestones total (50s+100s+200s+5-fors)
```

Every leaderboard method also takes `season=`/`team_id=` (see filtering
below), and its own `min_*`/`top_n` keyword — check the method signature
in `sqlite_queries.py` for the exact name (they're not all called the
same thing, e.g. `min_batting_innings` vs `min_games`).

**One player's full career** — `career_stats()` (or `stats.career()`,
same thing) returns every batting/bowling/fielding total in one row per
player, not just whatever one leaderboard ranks by:

```python
from sqlite_queries import career_stats

career = career_stats(conn)                                    # every (in-scope) player, full career stats
career[career["player_name"] == "Ian Wade"].T                    # one player, transposed so it's readable
career[career["player_id"] == 5]                                    # by id instead, if the name's ambiguous
```

**Basic querying and filtering** — every function above takes the same
filter keywords, so they compose the same way everywhere:

| Keyword | Default | Effect |
|---|---|---|
| `season=2024` | `None` (all seasons) | Restricts every total to matches in that season. |
| `team_id=5` | `None` (every team) | Restricts to one specific team (e.g. just the 1st XI) — see below for finding a `team_id`. Splits a player's stats by team instead of giving a true career total. |
| `elpmcc_only=True` | `True` | Only players who've appeared for `elpmcc_name`'s teams are included at all — opposition players are excluded as *tracked players*, not deleted (their innings still exist in `batting_innings`/`bowling_innings`, they just don't get a career-stats row of their own). Pass `False` to include everyone, e.g. to check one opposition player's record against this club specifically. |
| `elpmcc_name="..."` | `"East Lancs Paper Mill CC"` | Which club `elpmcc_only` means — despite the name, this isn't hardcoded to one club: pass any `club_name` in the database to get that club's own combined career stats instead (all its teams together — see "club vs team stats" below). |
| `include_juniors=False` | `False` | Junior teams (`teams.is_juniors`, e.g. Under 9/Under 11) are excluded from career totals and leaderboards by default. Pass `True` to include them, or filter to a junior `team_id` directly (which already overrides this). |
| `include_nmcl=False` | `False` | Whether `nmcl_stats.py`'s season-aggregate rows contribute to the totals — see [Modules](#modules) above for exactly what does and doesn't get folded in. |

`SQLPlayerStats(conn, elpmcc_only=..., elpmcc_name=..., include_juniors=..., include_nmcl=...)` sets these once for every leaderboard method on that instance; `career_stats(conn, ...)` takes them per call. `season`/`team_id` are always per-call (there's no instance-level default for those) since you're usually comparing across them, not fixing one for a whole session.

**Club stats vs team stats — no separate file needed.** "One club's combined
stats across every team it runs" and "one specific team's stats" are both
already just `career_stats()`/`SQLPlayerStats` calls, not a different kind
of query:

```python
# The whole club (every team, seniors + juniors if asked), by name --
# this is just elpmcc_only/elpmcc_name pointed at whichever club you want:
career_stats(conn, elpmcc_name="Prestwich CC")

# One specific team only (e.g. just the 1st XI) -- find its team_id first:
team_id = conn.execute(
    "SELECT t.team_id FROM teams t JOIN clubs c ON c.club_id = t.club_id "
    "WHERE c.club_name = ? AND t.team_name = ?",
    ("East Lancs Paper Mill CC", "1st XI")
).fetchone()[0]

career_stats(conn, team_id=team_id)                     # that team's players, stats split to just this team
SQLPlayerStats(conn).top_runs(team_id=team_id, top_n=10)   # leaderboard, same team
```

What genuinely doesn't exist yet, and would need new code rather than a
different call: **team-level results** (win/loss/draw records, run rates,
season standings) — everything above is player stats grouped by team/club,
not match outcomes aggregated by team. That's a `matches.result`/
`result_applied_to` query nobody has written, not a missing file — it
belongs as a new function in `sqlite_queries.py` alongside `career_stats()`
when it's needed, not a separate module: same store, same "SQL query over
the normalised tables" shape as everything else here.

### 4. Ingest a CricHQ PDF

```bash
python3 crichq_pdf.py "crichq/ALL_CRICHQ_SCORECARDS.pdf" --sqlite-db demo.sqlite
```

```
Parsing crichq/ALL_CRICHQ_SCORECARDS.pdf ...
  374 matches found in this file.
Done. Played: 328, Abandoned: 46
```

### 5. Ingest a CricketStatz `.MXP` export and check it landed correctly

```bash
python3 mxp_parser.py "cricketstatz/ELPM2018_all_matches.mxp" --sqlite-db demo.sqlite
```

```
Parsing cricketstatz/ELPM2018_all_matches.mxp ...
  304 matches found in this file.
Done. Played: 304, Abandoned: 0
```

This source's own club name is `"East Lancs Paper Mill"` (no `"CC"` —
identity reconciliation across sources hasn't run yet in this walkthrough),
so pass it explicitly to see the club's own players rather than
the default `ELPMCC_NAME`:

```python
conn = sqlite3.connect("demo.sqlite")
stats = SQLPlayerStats(conn, elpmcc_name="East Lancs Paper Mill")

conn.execute("SELECT source, COUNT(*) FROM matches GROUP BY source").fetchall()
# [('cricketstatz', 304), ('play_cricket', 70), ('crichq_pdf', 374)]

stats.top_runs(top_n=10)
stats.top_wickets(top_n=10)
```

### 6. Reconcile a player across sources and pull their full career

`reconcile.py` merges known player groups (from `reconcile/decisions.yaml`)
so a career query spans every source that contributed to a group:

```bash
python3 reconcile.py --sqlite-db demo.sqlite
```

```
Merged: Ian Wade -> player_id 5
```

```python
conn = sqlite3.connect("demo.sqlite")   # reconnect to pick up the merge
career = career_stats(conn, elpmcc_only=False)
career[career["player_name"] == "Ian Wade"].T
```

Against the demo-scale build above this gives a combined record spanning
Play-Cricket, CricHQ, and CricketStatz — see
[development_notes.md](development_notes.md) and [ROADMAP.md](ROADMAP.md)
item 4 for the exact figures, the remaining unmerged name variants
(`"IW wade"`, `"Ian Wade"` as separate `crichq_pdf` identities), and why
one CricketStatz ref was removed from this merge after turning out to be a
different real person (Ian Wade's father) sharing the same name.

Adding another player means adding another entry to
`reconcile/decisions.yaml` (find their refs with a query like the one in
`reconcile.py`'s own investigation notes) — nothing else changes, including
after importing further CricHQ PDFs: re-running `reconcile.py` is
idempotent, and any *new* match for an already-merged ref resolves straight
to the survivor.

### 7. Attach club/team/player awards

`club_awards.py` holds the club's own manually-curated honours — league/cup
wins, season batting/bowling/wicketkeeping average winners, players' player
of the year, club captaincy — as hardcoded `TEAM_AWARDS`/`PLAYER_AWARDS`
lists, since there's no source file for these to parse from. **Run this
after `reconcile.py`** (step 6): player/team names are resolved by exact
match against the store's canonical rows, so an unmerged duplicate raises a
clear error rather than guessing which row an award belongs to.

```bash
python3 club_awards.py --sqlite-db demo.sqlite
```

```
Inserted 4 new team_awards row(s), 26 new player_awards row(s).
```

Once attached, individual honours show up directly in `career_stats()`
(the `awards` column) — this is what the user meant by "when generating
career stats for Ian Wade these awards should be noted":

```python
conn = sqlite3.connect("demo.sqlite")   # reconnect to pick up the awards
career = career_stats(conn, elpmcc_only=False)
career[career["player_name"] == "Ian Wade"][["player_name", "awards"]]
# 2009 NMCL Bowling Average Winner; 2011 Club Captain; 2012 Club Captain;
# 2012 NMCL Batting Average Winner; 2012 NMCL Players' Player of the Year;
# 2013 Club Captain; 2014 Club Captain; 2015 Club Captain
```

Team honours (league/cup wins) aren't folded into a player row — a
squad-wide trophy doesn't belong to any one player's career line the way an
individual award does — so look those up with `team_awards()`, and see any
player's raw award rows on their own with `player_awards()`:

```python
from sqlite_queries import player_awards, team_awards

player_awards(conn, season=2012)   # every individual honour awarded in 2012
team_awards(conn)                   # every team honour, every season
```

Adding a new honour means adding a new dict to `club_awards.py`'s
`TEAM_AWARDS`/`PLAYER_AWARDS` (or a range to `CAPTAINCY_TENURES`) and
re-running the script — it's idempotent (`INSERT OR IGNORE`), so re-running
after adding one new entry only inserts that entry.

### 8. Audit the database for data-quality issues and reconciliation candidates

Run after ingesting (all) sources, ideally before trusting any stats off the
result — a read-only scan, never writes to `demo.sqlite`:

```bash
python3 reconcile_audit.py --sqlite-db demo.sqlite --out reconcile/data_quality_report.md
```

```
Wrote reconcile/data_quality_report.md
```

The report has two parts: a data-quality scan (distinct competitions,
leagues, grounds, seasons, and any crichq_pdf.py "Unknown (...)" placeholder
rows — rarest-first, so a likely typo surfaces near the top) and
reconciliation candidates for clubs, teams, grounds, and players that look
like the same real thing split across two or more canonical rows. This same
run also writes every one of those candidates into
`reconcile/decisions.yaml`'s `pending:` section — nothing to hand-copy out
of the report. Confirming a candidate means correcting its `canonical_name`
there and setting `status: confirmed` (or `audited`), then running
`python3 reconcile.py --promote` to sweep it into the real merge section,
followed by `python3 reconcile.py --sqlite-db demo.sqlite` (step 6) to
actually apply it — the report itself never edits anything, and is cheap
enough to regenerate any time after ingesting a new source or fixing a
parser bug.

`reconcile/data_quality_report.md` in this repo is a committed snapshot from
the **full archive**, so it doubles as a worked example — see
[development_notes.md](development_notes.md) for the full narrative behind
what it finds.

### 9. Poke at the raw tables directly

For anything the query helpers don't cover yet, plain SQL against `demo.sqlite`
works — the schema is in `schema.sql`:

```python
conn.execute("SELECT * FROM matches WHERE source='cricketstatz' LIMIT 1").fetchone()
conn.execute("SELECT * FROM v_batting_achievements LIMIT 5").fetchall()
conn.execute("PRAGMA foreign_key_check").fetchall()   # should always be []
```

Delete `demo.sqlite` and re-run steps 1/5 any time to rebuild from scratch —
nothing in the pipeline is destructive to the source JSON/PDF/`.MXP` files.

## Using the main database

`demo.sqlite` above is a throwaway name for the walkthrough. In real use
there's one persistent file — `playcricket_stats.sqlite` (or whatever you
call it) — that every query in this project reads from, built once and
then kept up to date rather than rebuilt from scratch each time. The two
source *types* need completely different maintenance rhythms, because one
is closed and one isn't:

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
PDF/`.MXP`/`.txt`/`.xls`/`.csd` files or `reconcile/decisions.yaml` —
only the derived `.sqlite` file. So if the database ever ends up in a
state you don't trust, deleting it and re-running ingestion, in order —
`sqlite_store.py` (Play-Cricket JSON), `crichq_pdf.py`, `mxp_parser.py`,
`cricketstatz_txt.py`, `nmcl_stats.py`, `scorebooks.py`, then `reconcile.py`
and finally `club_awards.py` (it depends on reconciliation having already
run — see [Using the example files](#using-the-example-files) step 7) —
always gets back to the same result. The
`.sqlite` file itself doesn't need to be committed to version control —
treat it as a derived build artifact, the same way `demo.sqlite` is
throughout the walkthrough above, and keep it out of git.

## Documentation

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
