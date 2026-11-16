# playcricket_stats

A statistics database for East Lancs Paper Mill CC (ELPMCC). It merges
every scorecard the club has, from six different sources, into one SQLite
store, so that career records, leaderboards, printable scorecards and
social-media graphics can all be produced from the same data.

## Status (November 2026)

| Area | State |
|---|---|
| Data import (six sources) | **Done** — 1,003 matches raw, 971 after de-duplication, seasons 2004–2026, zero foreign-key violations |
| Cross-source reconciliation | **Done for confirmed cases** — 165 player, 26 club and 66 team merge groups, 32 duplicate matches removed, all human-confirmed in `reconcile/decisions.yaml` |
| Career stats and leaderboards | **Working** across all sources (`sqlite_queries.py`); team records, club records and player profiles not yet packaged |
| Presentation-night awards | **Working** — shortlist report and PowerPoint deck |
| Scorecard / career / social graphics | **Templates designed**, rendering demo data only — not yet wired to the database |
| Interface (CLI, web, clubhouse TV) | **Not started** — everything is a script or library call |

What comes next, in priority order, is in **[ROADMAP.md](ROADMAP.md)**.

## Data sources

| Source | Module | Covers | Matches |
|---|---|---|---|
| Play-Cricket API (live) | `playcricket_api.py`, `playcricket_database.py` | 2024–2026 | 249 |
| CricHQ PDF archive | `crichq_pdf.py` | 2016–2023 | 374 |
| CricketStatz `.MXP` export | `mxp_parser.py` | 2005–2018 | 304 |
| CricketStatz text scorecards | `cricketstatz_txt.py` | 2010 | 37 |
| Hand-scored scorebook photos | `scorebooks.py` | 2004, 2007, 2010, 2011 | 39 |
| NMCL season averages | `nmcl_stats.py` | 2000–2005, 2010–2013 | 77 season rows, no matches |

Counts are as ingested; 32 fixtures recorded in two sources are removed
by `reconcile.py`. **Known gaps:** no match-level data for 2012–2013, and
2011 and 2014 are partial. Scorebook photos for 2012–2014 are in
`scorebooks/` awaiting transcription.

## Build the database

The `.sqlite` file is never committed; it is rebuilt from the committed
source files. Python 3.9+.

```bash
pip install -r requirements.txt
```

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

The first six steps can run in any order. `reconcile.py` must come after
them, and `club_awards.py` last. Every step is idempotent, so if the
database is ever in doubt, delete it and run the sequence again.

## Use it

```python
import sqlite3
from sqlite_queries import career_stats, SQLPlayerStats

conn = sqlite3.connect("playcricket_stats.sqlite")

career = career_stats(conn)                       # one row per ELPMCC player, all sources
career[career["player_name"] == "Ian Wade"].T

stats = SQLPlayerStats(conn)
stats.top_runs(top_n=10)                          # all-time
stats.top_wickets(season=2026, top_n=10)          # one season
```

Presentation-night shortlists and slide deck for a season:

```bash
python3 presentation_awards.py --sqlite-db playcricket_stats.sqlite --season 2026 --out awards_2026.md
python3 presentation_deck.py --sqlite-db playcricket_stats.sqlite --season 2026 --out awards_2026.pptx
```

Design template previews (demo data, needs Playwright's Chromium):

```bash
python3 design/scripts/render.py
```

Match lookups, team records, milestone lists, every filter option, and
how to keep Play-Cricket in sync are covered in **[USAGE.md](USAGE.md)**.

## How it fits together

```
Play-Cricket API ─> JSON cache ─┐
CricHQ PDF ─────────────────────┤
CricketStatz .MXP / .txt ───────┼─> SQLiteStore ─> reconcile.py ─> sqlite_queries.py ─> awards report / deck
Scorebook photos ───────────────┤   (schema.sql)   (decisions.yaml)                   └> design templates (not yet wired)
NMCL season averages ───────────┘
```

Every parser produces the same match shape that `Scorecard`
(`playcricket_scorecard.py`) renders, and every fact row records its
`source`. Identity across sources is never guessed: clubs and teams with
near-identical names merge automatically at insert, and everything else is
a human-confirmed entry in `reconcile/decisions.yaml`.

### Modules

| Module | Role |
|---|---|
| `playcricket_api.py` | Play-Cricket API client |
| `playcricket_database.py` | Local JSON cache; `sync_season()` fetches only new or changed matches |
| `playcricket_scorecard.py` | `Scorecard`: one match as batting, bowling, partnership and fall-of-wicket tables |
| `schema.sql`, `sqlite_store.py` | The normalised store and its insert logic |
| `crichq_pdf.py`, `mxp_parser.py`, `cricketstatz_txt.py`, `scorebooks.py`, `nmcl_stats.py` | One ingester per archive source |
| `reconcile.py` | Applies `reconcile/decisions.yaml` (merges, duplicate matches, grounds) |
| `reconcile_audit.py` | Writes `reconcile/data_quality_report.md` and proposes new merge candidates |
| `club_awards.py` | Loads club honours (titles, average winners, captains) |
| `sqlite_queries.py` | `career_stats()`, `SQLPlayerStats` leaderboards, awards and milestone queries |
| `presentation_awards.py`, `presentation_deck.py` | Presentation-night shortlists (Markdown) and deck (PowerPoint) |
| `design/` | Brand palette, crest, and HTML templates for the scorecard poster, career sheet and social card |

## Documentation

- **[ROADMAP.md](ROADMAP.md)** — progress review and the prioritised development pipeline.
- **[USAGE.md](USAGE.md)** — querying cookbook and database maintenance.
- **[EXAMPLES.md](EXAMPLES.md)** — step-by-step walkthrough on the small sample files.
- **[development_notes.md](development_notes.md)** — full history: design reasoning, bug stories, validation figures.
- **[design/README.md](design/README.md)** — the graphic templates.
- **`docs/`** — Sphinx API reference (`pip install -r docs/requirements.txt && make -C docs html`).
