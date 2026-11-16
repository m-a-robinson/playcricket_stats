# Roadmap

Progress review and prioritised development pipeline for
`playcricket_stats`, as of November 2026. This replaces the earlier
numbered roadmap, which is archived in
[development_notes.md](development_notes.md#archived-roadmap-to-october-2026).

- [Progress review](#progress-review)
- [Development pipeline](#development-pipeline)
- [Data backlog](#data-backlog)

## Progress review

183 commits and 30 merged pull requests between 26 August and 17 October
2026. Almost all of that effort went into getting data in and making it
trustworthy; the features the club will actually see are mostly still
ahead.

### What is done

| Area | Result |
|---|---|
| Data foundation | Normalised SQLite schema with `source` on every fact row and source-id mapping tables for players, clubs, teams and grounds. A full rebuild from the repo gives 1,003 matches raw and 971 reconciled, with zero foreign-key violations. |
| Ingestion | Six sources: Play-Cricket API (249 matches), CricHQ PDF (374), CricketStatz `.MXP` (304), CricketStatz text (37), scorebook photos (39), NMCL season averages (77 season rows). |
| Reconciliation | `reconcile/decisions.yaml` holds 165 player, 26 club and 66 team merge groups and 32 duplicate matches, all human-confirmed. `reconcile_audit.py` proposes new candidates and writes a data-quality report. |
| Career stats | `career_stats()` and 12 `SQLPlayerStats` leaderboards work across all sources, filterable by season, team, juniors and NMCL aggregates. Milestone views cover fifties, hundreds and five-wicket hauls. |
| Honours | `club_awards.py` loads 26 player and 4 team honours into career records. |
| Presentation night | `presentation_awards.py` (shortlist report) and `presentation_deck.py` (PowerPoint) run from the database. These are the only finished end-user outputs. |
| Design | ELPMCC palette, crest and three HTML templates (A4 scorecard poster, A4 career sheet, 1080×1080 social card), rendered to PNG and PDF from hand-written demo data. |

### What is partly done

| Key feature | State | Missing |
|---|---|---|
| Career and historical stats | Player careers and leaderboards work | Team records, club records, head-to-head, season-by-season player profile, and a match search function; these exist only as SQL examples in [USAGE.md](USAGE.md) |
| Scorecard export | Template and renderer exist | Not connected to the database; no command to export a given match or player |
| Social media formatting | One result-card template exists | Not connected to the database; no weekend round-up or milestone card; no caption text |
| Interface | None | No single command, no Play-Cricket sync command, no web view |
| Clubhouse TV (Raspberry Pi) | None | Not started; depends on the items above |

### Weaknesses found in this review

1. **No automated tests.** Correctness rests on manual checks recorded in
   the notes. Any change to the schema or a parser is unprotected.
2. **Batting strike rate is wrong for long careers.** `career_stats()`
   divides runs from every innings by balls from only the innings where
   balls were recorded (most CricketStatz, all text and scorebook innings
   have none). Example: Ian Wade shows 257. Economy and averages are
   unaffected.
3. **154 of 971 matches have no winner recorded**, so team win/loss
   records cannot yet be trusted. Abandoned CricHQ games are stored as
   `Played`.
4. **Coverage gaps.** No match data for 2012–2013; 2011 is 2nd XI only
   and 2014 is 1st XI only. 92 scorebook photos for 2012–2014 are in the
   repo but not transcribed.
5. **No one-command build or sync.** Eight commands to build; the
   Play-Cricket sync is a code snippet and the API key handling is ad hoc.
6. **Documentation had drifted.** The previous README quoted 964/932
   matches and did not mention the presentation scripts. Figures now come
   from a fresh build.
7. **Housekeeping.** Two overlapping player-merge tools
   (`SQLiteStore.merge_players()` and `reconcile.py`); `.DS_Store` files
   committed; a hardcoded Chromium path in `design/scripts/render.py`;
   `scorebooks.py` is 280 KB of match data held as Python code.

## Development pipeline

Phases are in priority order. Each one delivers something usable and is
a prerequisite for the next. Sizes: S is about a day, M a few days, L a
week or more.

### Phase 0 — Make it safe to build on

Small, and it protects everything after it.

| # | Task | Size | Done when |
|---|---|---|---|
| 0.1 | `build_db.py`: one command that runs the eight build steps | S | `python3 build_db.py` produces the 971-match database |
| 0.2 | `sync_playcricket.py --season N`, reading `PLAY_CRICKET_API_KEY` from the environment or a `.env` file | S | One command syncs a season and refreshes the store; no key in code or notebooks |
| 0.3 | Smoke tests with `pytest`: demo build, zero FK violations, match counts per source, three known career totals, every parser on a sample file | M | Tests run in a GitHub Action on every push |
| 0.4 | Fix batting strike rate to use only innings with balls recorded | S | Ian Wade's strike rate is plausible; test added |
| 0.5 | Housekeeping: remove `.DS_Store`, locate Chromium automatically, retire `SQLiteStore.merge_players()` in favour of `reconcile.py` | S | One merge path; `render.py` runs on any machine |

### Phase 1 — Career and historical stats

Every later output draws on these functions, so they come first.

| # | Task | Size | Done when |
|---|---|---|---|
| 1.1 | Match results clean-up: add a `no_result` status, fill winners for the 2016 CricHQ layout from innings totals, flag the remainder for review | M | Matches without a recorded outcome fall from 154 to a reviewed list |
| 1.2 | `team_records()`: played, won, lost, no result by team and season | S | Replaces the SQL in USAGE.md |
| 1.3 | `player_profile()`: career totals, season-by-season table, milestones, honours, debut and latest match | M | One call returns everything the career sheet and TV need |
| 1.4 | `club_records()`: highest and lowest team totals, best individual scores and bowling, record partnerships, most appearances | M | Returns record tables for club and per team |
| 1.5 | `find_matches()` and `get_scorecard(match_id)`: search by date, opponent, season, competition or player | S | Replaces the copy-paste helpers in USAGE.md |
| 1.6 | `head_to_head(opponent)` and `on_this_day(date)` | S | Feeds social posts and the TV rotation |
| 1.7 | Career milestone detection: 1,000-run and 100-wicket steps, appearance landmarks, approaching-milestone list | S | Lists who passed or is near a landmark after each sync |

The [data backlog](#data-backlog) runs alongside this phase.

### Phase 2 — Scorecard export

| # | Task | Size | Done when |
|---|---|---|---|
| 2.1 | Replace the demo dictionaries in `render.py` with context builders that read from Phase 1 functions | M | No hand-typed figures remain in `design/` |
| 2.2 | `export.py scorecard --match-id N` and `export.py career --player "Name"`, producing PDF and PNG | S | Any match or player exports with one command |
| 2.3 | Handle sparse cards: no balls faced, missing bowling, one-innings matches, long names | S | Renders cleanly for one sample match from each source |
| 2.4 | `export.py milestones --season N`: batch-export every century and five-wicket-haul scorecard | S | One folder of frame-ready PDFs per season |
| 2.5 | Print check at A4 and A3, then adjust type and margins | S | A framed test print is approved by the club |

### Phase 3 — Social media formatting

| # | Task | Size | Done when |
|---|---|---|---|
| 3.1 | Wire the result card to live data: `social.py result --match-id N` | S | PNG produced for any match |
| 3.2 | Weekend round-up card: all ELPMCC fixtures for a weekend with top performers | M | `social.py weekend --date 2026-08-29` gives one PNG |
| 3.3 | Milestone card for a century, five-for or career landmark | S | Produced from Phase 1.7 output |
| 3.4 | Caption text with each image (result, performers, hashtags), plus a 1080×1920 story size | S | Each PNG has a matching `.txt` caption |
| 3.5 | Generate the weekend pack automatically after a sync | S | Sunday-evening sync leaves a ready-to-post folder |

Posting stays manual. Automatic posting to social platforms is out of
scope until the output has been used for a season.

### Phase 4 — Interface

| # | Task | Size | Done when |
|---|---|---|---|
| 4.1 | One CLI, `elpmcc`, with `build`, `sync`, `stats`, `export`, `social` and `awards` subcommands wrapping the existing scripts | M | A non-developer can run the weekly routine from a short written list |
| 4.2 | Read-only local web app (Flask or FastAPI with Jinja, reusing `design/elpmcc.css`): home, player page, match scorecard, leaderboards, records, seasons | L | Browsable at `http://localhost:8000` with search by player and match |
| 4.3 | Download buttons on player and match pages that call the Phase 2 and 3 exporters | S | PDF and PNG available from the browser |
| 4.4 | Scheduled sync and rebuild (cron or systemd timer) | S | Database updates itself weekly in season |
| 4.5 | Optional: static HTML or JSON export for the club WordPress site | M | Leaderboards and records publish without WordPress needing SQLite |

### Phase 5 — Clubhouse TV on a Raspberry Pi

The TV is a full-screen view of the Phase 4 web app, so it needs little
new logic.

| # | Task | Size | Done when |
|---|---|---|---|
| 5.1 | `/tv` route: auto-rotating 1920×1080 slides with large type, no interaction needed | M | Runs unattended in a desktop browser |
| 5.2 | Slide types: historic scorecard, "on this day", player career card, all-time leaderboards, club records, honours boards, last weekend's results | M | Each slide type renders from live data |
| 5.3 | Playlist config (YAML): slide types, duration, featured players and matches, match-day mode | S | The club can change the rotation without code |
| 5.4 | Pi setup script: install the app, run it as a systemd service, start Chromium in kiosk mode on boot, disable screen blanking | M | Pi powers on straight into the slideshow |
| 5.5 | Offline operation with a scheduled `git pull`, sync and rebuild when Wi-Fi is available | S | TV keeps working if the clubhouse network is down |
| 5.6 | Soak test on the target Pi and TV for a week | S | No crashes, memory growth or burn-in issues |

Recommended hardware: Raspberry Pi 4 or 5 with 4 GB RAM, running
Raspberry Pi OS with desktop. The database is about 30 MB and the app is
light; Chromium is the main memory user.

**Optional early win:** once Phase 2 is finished, a folder of exported
scorecard PNGs can be shown on the Pi with any slideshow program. This
gives the clubhouse a display months before Phase 5, at the cost of a
manual refresh.

### Order and dependencies

```
Phase 0 ─> Phase 1 ─┬─> Phase 2 ─> Phase 3 ─┐
                    │                       ├─> Phase 4 ─> Phase 5
                    └─> data backlog ───────┘
```

Phases 2 and 3 share the rendering code and can overlap. Phase 4.1 (the
CLI) can start as soon as Phase 0 is done.

## Data backlog

Ongoing work that improves the numbers but does not block features.
Highest value first.

| Item | Detail |
|---|---|
| Transcribe 2012–2014 scorebooks | 92 photos: 1st XI 2012 (37), 2nd XI 2012 (19), 2013 (19), 2014 (17). Fills the only seasons with no match data. |
| Find 1st XI 2011 and 2013 scorebooks | No source of any kind in the repo yet. |
| Review pending merges | 2 team candidates in `decisions.yaml`; re-run `reconcile_audit.py` after each new season of scorebooks. |
| Player name variants within CricHQ | Different scorers spell one player several ways (for example "I Wade", "IW wade", "Ian Wade"). Work through the audit report by appearances, highest first. |
| Competition names | 223 CricketStatz matches (2005–2015) say "Division N" or "Cup" without the NMCL prefix. Needs the club to confirm the year it moved to the GMCL. |
| Grounds | CricHQ gives county only; 47 Play-Cricket matches have the placeholder "Add New Ground". Build a club-to-home-ground table in `decisions.yaml`. |
| Play-Cricket backfill | Sync seasons before 2024 if the club used Play-Cricket then, and compare with CricHQ. |
| 2010 text scorecards | Five files have a filename date that disagrees with their content (see the `cricketstatz_txt.py` warnings), so up to five 2010 fixtures may be missing. |
| Move scorebook data out of code | Convert `scorebooks.py` match data to YAML or JSON files, one per match. Do this before the next large transcription batch. |
