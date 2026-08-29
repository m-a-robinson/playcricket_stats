# Using the example files

This is a hands-on walkthrough against the small, frozen sample files
already in the repo (`playcricket/playcricket_2026_demo.json`,
`crichq/ALL_CRICHQ_SCORECARDS.pdf`) — nothing needs an API key to run, and
nothing here touches the real database. It's the place to start if you want
to see each piece of the pipeline working in isolation before pointing
anything at real data.

For the real, continuously-maintained database — the amalgamated,
six-source store, and how to query it for actual career stats, match
lookups, and team records — see [README.md](README.md#using-the-main-database)'s
"Using the main database" section instead. Everything below uses the same
`sqlite_queries.py`/`playcricket_scorecard.py` functions that section does;
only the data underneath differs.

One-time setup:

```bash
pip install ipython pandas numpy requests pypdf ruamel.yaml
cd playcricket_stats
ipython
```

The examples below all use the files already in the repo
(`playcricket/playcricket_2026_demo.json`, `crichq/ALL_CRICHQ_SCORECARDS.pdf`).

## 1. Build the SQLite store from the sample Play-Cricket data

This is usually run from the Terminal, not ipython, since it's a one-shot
build step:

```bash
python3 sqlite_store.py --json-db playcricket/playcricket_2026_demo.json --sqlite-db demo.sqlite
```

```
Built 70 matches into demo.sqlite
```

## 2. Look at one match's scorecard

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

## 3. Query career stats and leaderboards

This is the main "did this actually work" check — cross-check a name or
figure you know against what comes back. Everything here comes from
`sqlite_queries.py`'s two entry points: `career_stats()` (one row per
player) and `SQLPlayerStats` (leaderboards built on top of it) — see that
module's own bullet under [Modules](README.md#modules) for the full parameter
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
| `include_nmcl=False` | `False` | Whether `nmcl_stats.py`'s season-aggregate rows contribute to the totals — see [Modules](README.md#modules) above for exactly what does and doesn't get folded in. |

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

## 4. Ingest a CricHQ PDF

```bash
python3 crichq_pdf.py "crichq/ALL_CRICHQ_SCORECARDS.pdf" --sqlite-db demo.sqlite
```

```
Parsing crichq/ALL_CRICHQ_SCORECARDS.pdf ...
  374 matches found in this file.
Done. Played: 328, Abandoned: 46
```

## 5. Ingest a CricketStatz `.MXP` export and check it landed correctly

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

## 6. Reconcile a player across sources and pull their full career

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

## 7. Attach club/team/player awards

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

## 8. Audit the database for data-quality issues and reconciliation candidates

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

## 9. Poke at the raw tables directly

For anything the query helpers don't cover yet, plain SQL against `demo.sqlite`
works — the schema is in `schema.sql`:

```python
conn.execute("SELECT * FROM matches WHERE source='cricketstatz' LIMIT 1").fetchone()
conn.execute("SELECT * FROM v_batting_achievements LIMIT 5").fetchall()
conn.execute("PRAGMA foreign_key_check").fetchall()   # should always be []
```

Delete `demo.sqlite` and re-run steps 1/5 any time to rebuild from scratch —
nothing in the pipeline is destructive to the source JSON/PDF/`.MXP` files.
