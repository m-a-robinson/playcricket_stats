# Development notes

This file holds the detailed development history and module-by-module
narrative for `playcricket_stats` — the bug stories, validation numbers,
and design reasoning behind each piece — split out of the main
[README](README.md) so that file can stay focused on how to actually use
the project. See also [ROADMAP.md](ROADMAP.md) for outstanding issues and
planned work, and the [Sphinx API reference](docs/) for generated
docstring documentation of every module.

## Contents

- [Milestone: all original data now imported (2026-08-26)](#milestone-all-original-data-now-imported-2026-08-26)
- [Modules](#modules)
- [Retired](#retired)
- [Sample data](#sample-data)

## Milestone: all original data now imported (2026-08-26)

Every data source this project set out to ingest is now in the store, at
once, end to end: the **complete Play-Cricket history currently reachable**
(seasons 2024-2026, live-synced via the API and kept that way — see
"Maintaining the database" in the README), the **complete CricHQ PDF archive**
(2016 and 2018-2023), and the **complete CricketStatz archive** (2005-2018). That's
**926 matches across all three sources** (248 Play-Cricket + 304 CricketStatz
+ 374 CricHQ, the latter down from an earlier 381 once seven genuinely
content-free abandoned-match placeholders were fixed to be skipped rather
than ingested as empty rows — see `crichq_pdf.py`'s bullet below) built into
one normalised SQLite store with **zero foreign-key violations**. Roadmap
items 1-3 (data foundation, CricHQ ingestion, CricketStatz ingestion) are
accordingly all *Done*, together, not just individually — this is the
point the project moves from "get the data in" to "make the data
trustworthy": reconciling identity across sources (roadmap item 4, in
progress — see `reconcile_audit.py`) and, beyond that, the actual
stats/exports the project exists for (roadmap items 5-8).

Reconciliation itself has already caught real cross-source duplication: 29
of those 926 matches turned out to be the same real fixture entered
independently into both `crichq_pdf` and `cricketstatz` during the
2016/2018 transition between the two systems, doubling their stats until
`reconcile/decisions.yaml`'s `duplicate_matches` deleted the poorer-quality
copy of each pair. The fully-reconciled store was **897 matches** at this
point.

Since this milestone, investigating a genuine gap the three original
sources share — **zero match data of any kind for 2010-2013** — led to a
fourth and fifth source: `cricketstatz_txt.py` (individual CricketStatz
scorecards, filling 2010 with 37 real matches) and `nmcl_stats.py`
(North Manchester Cricket League season averages, supplementing career
stats — not full scorecards — for 2000-2005 and 2010-2013 where
match-level data doesn't exist or is confirmed incomplete). A sixth
source followed the same way: `scorebooks.py`, transcribing hand-scored
scorebook pages the user photographed and uploaded, starting with the
11-Jul-2010 ELPM 1st XI v Failsworth Macedonia CC match (Gavin Greaves
170, Ian Wade 163, a 339-run 3rd-wicket stand) — a match `nmcl_stats.py`'s
2010 residual-total rows already knew was missing but couldn't supply
match-level detail for.

That one match was the start, not the end, of the scorebook-digitisation
effort: the user went on to photograph and upload 71 more scorebook
pages covering the club's 2nd XI across five seasons (2007, 2011-2014),
sorted into `scorebooks/2nd XI/<season>/`. **2011 is now fully
transcribed** — all 13 2nd XI matches that season played (Austerlands,
Failsworth twice, Farnworth Social, Littleborough Lake Sides/Lakeside
twice, Swinton Moorside twice, Westhoughton twice including a tie, a
rain-abandoned game v Roe Green, and Thornham) are in `scorebooks.py`,
each cross-checked innings-by-innings (batsmen runs + extras = team
total, bowling figures reconciled against dismissals and overs) before
being added — plus the one 2007 match (East Lancs PM 2nd XI v Bury CC)
that came in the same photo batch. **2012 and 2013 are photographed but
not yet transcribed** — 19 photos apiece, organised into their own season
folders, awaiting the same treatment. 2014's photos (17) fill a 2nd XI
gap too, though that season already has 1st XI match-level coverage from
CricketStatz. The rest of 2010 beyond what's captured, and the
still-untranscribed years, have no match-level source yet, only season
aggregates; if genuine scorecards or further scorebook pages turn up, the
same `cricketstatz_txt.py`/`scorebooks.py` pipelines would replace the
aggregate figures with real per-match data.

Transcription for a photographed-but-not-typed match goes through an
extra step the other sources don't need: since there's no machine-readable
text at all, each match starts as a single-pass read of the scorebook
photo, presented back as a scorecard for the user to check against the
same photo before it's written into `scorebooks.py` — the arithmetic
cross-check (batsmen + extras = total, bowling figures reconcile against
dismissals) still applies once the reading is confirmed, same as every
other source.

Building a season-by-season match export as an early cross-check tool for
the scorebook-digitisation effort (a workbook with one sheet per season,
2000-2016) surfaced three more genuine crichq_pdf/cricketstatz transition
duplicates that the earlier 29-duplicate sweep had missed — one from the
2005 CricketStatz/CricketStatz-text overlap (see `cricketstatz_txt.py`'s
mislabeled-file note below) and two from 2016, one of which was hiding
behind two never-merged spellings of the same opposition club ("Flixton
CC" vs "Flixton C&SC"). `reconcile/decisions.yaml`'s `duplicate_matches:`
now has 32 entries, not 29, and `reconcile_audit.py` gained a permanent
"Candidate duplicate matches" check (same date, same ELPM team, identical
per-innings runs, two different sources) so this class of bug surfaces on
every future audit instead of needing another by-eye pass. **964 matches
raw, 932 once `reconcile.py` applies `duplicate_matches`.**

The same export also showed CricketStatz's bare "Division 1"/"Division 2"/
etc. reading, out of context, as if they might be the same competition as
GMCL's own later "Division 1"/"Division 2" naming (2016 on) — they aren't:
the club's league was North Manchester CL up to 2015, merging into Greater
Manchester CL from 2016 (the same season boundary `nmcl_stats.py` already
used for the club's own NMCL season averages, and visible in CricketStatz's
own competition text, which starts saying "GMCL Division..." right at that
boundary). `mxp_parser.py` and `cricketstatz_txt.py` now prefix every bare
"Division N" competition name with "NMCL " for seasons up to and including
2015, at the point each parses it, so it reads unambiguously; GMCL's own
already-prefixed 2016+ names are untouched. (`scorebooks.py`'s one 2010
match got the same fix.)

Play-Cricket's own history isn't necessarily fully backfilled yet — 2024-2026
is what's been synced so far; earlier seasons (however far back the club's
Play-Cricket presence goes, likely somewhere in the 2018-2023 range CricHQ
already covers) remain a possible future backfill, see "Maintaining the
database" in the README. CricHQ and CricketStatz, being closed archives, are
complete by definition once ingested.

## Modules

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
  parsing engine. `batting_table()` (display only — the stored
  `batting_innings.balls` figure is untouched) drops the balls-faced
  column entirely for an innings where every row reads 0, rather than
  printing a whole card of misleading zeroes: CricketStatz simply didn't
  record balls-faced before ~2016 (see below), and a genuine
  single 0 next to real values elsewhere is left alone.
- **`schema.sql`** / **`sqlite_store.py`** — Normalised SQLite store (clubs,
  teams, players, matches, innings, batting/bowling innings, match
  appearances/team sheets, milestone views), fed from the JSON cache with no
  API calls. `PlayCricketDatabase`/JSON stays the sync layer; SQLite is the
  canonical query/analysis layer, built for cross-source reconciliation:
  every fact table carries `source`, and canonical identity for players,
  clubs, and teams alike is resolved through a `*_source_ids` mapping table
  (`player_source_ids`, `club_source_ids`, `team_source_ids`) rather than
  reusing Play-Cricket's own numeric ids as primary keys — required once a
  source (CricHQ) has no numeric ids of its own to reuse. Clubs and teams get
  a conservative **automatic** cross-source merge at insert time
  (`_upsert_club()`/`_upsert_team()`): a casefolded, whitespace-collapsed,
  one-trailing-"CC"/"Cricket Club"-suffix-stripped name is the dedup key for
  clubs (e.g. Play-Cricket's "East Lancs Paper Mill CC" and CricHQ's "East
  Lancs Paper Mill" resolve to one canonical club), scoped by the already-
  resolved `club_id` for teams (so "1st XI" is still a different team per
  club, just not split into two rows for the *same* club across sources).
  `teams` also carries `is_juniors` (0/1), set at insert time from the team
  name alone ("Under 9", "Under 11 B", "U9", "Colts", "Juniors", etc. —
  `_classify_team()`) — currently only Play-Cricket's 2024-2026 seasons
  have any junior teams at all; CricHQ and CricketStatz have none. This is
  what `sqlite_queries.py`'s `include_juniors` filter (see below) reads.
  Deliberately conservative — no fuzzy matching, no guessing at dropped
  qualifiers — so it can't plausibly conflate two different real clubs;
  anything it doesn't catch is a candidate for `reconcile_audit.py`/
  `reconcile.py`'s `CLUB_MERGES`/`TEAM_MERGES` instead (see below). Also
  carries `find_players(name_like)` / `merge_players(keep_player_id, merge_player_id)`
  — a pairwise manual player-identity merge, the same underlying repoint
  `reconcile.py` does (see below) but one pair at a time rather than from a
  registry. **The two overlap and haven't been reconciled with each other**
  — pick one as canonical and retire the other is a housekeeping item, not
  yet done (see ROADMAP.md). Run `python3 sqlite_store.py` to (re)build
  the Play-Cricket side of the store from `playcricket_database.json`.
- **`crichq_pdf.py`** — Parses CricHQ "Full Scorecard Report" PDF exports
  into the same match-detail shape `Scorecard` expects, so they load
  through the exact same `SQLiteStore.insert_match()` path as Play-Cricket
  data, with `source="crichq_pdf"`. Handles mid-row PDF line-wraps, partial/
  abandoned matches, and the CricHQ dismissal-text format (`"c X b Y"`,
  `"run out (A/B)"` credited to the first-named fielder, etc.). Player
  identity is deliberately **not** matched against existing players — every
  CricHQ name becomes its own new canonical player for now (see ROADMAP.md).
  Also copes with two report-generator layouts concatenated
  into one archive PDF: most matches have a `"<home> vs <away>"` line
  directly before a single `"Date: X Venue: Y"` line, but an older layout
  (seen on 2016-season pages) omits the `"vs"` line entirely and splits
  `"Date:"`/`"Venue:"` onto separate lines — recovered by inferring the two
  team names from the innings' own `"Batting:"`/`"Bowling:"` headers instead
  when the header's `"vs"` line isn't there (see "Sample data" below and
  the roadmap for how this was found). `INNINGS_HEADER`/`BOWLING_HEADER` also
  tolerate a mid-name PDF line-wrap now (a long club-prefixed nickname like
  "East Lancs Paper Mill CC, East Lancs Millers" occasionally wraps right
  before "1st/2nd Innings" or the bowling column headers) — found by
  spot-checking sample scorecards: whenever that wrap landed inside the
  team-name capture, the header silently failed to match and the whole
  innings vanished rather than erroring, taking real runs/wickets/batting/
  bowling figures with it. Affected 28 real matches in the archive (all
  involving a T20/nickname side long enough to wrap), recovered without
  any change in the 374/328/46 total/played/abandoned counts. Run
  `python3 crichq_pdf.py <pdf-file>... --sqlite-db <path>` to ingest one or
  more PDFs; add `--json-out <path>` to also write every parsed match-detail
  dict to a JSON file — see `crichq/crichq_pdf.json` under "Sample data"
  below for what this is for.
- **`mxp_parser.py`** — Parses CricketStatz `.MXP` exports (File →
  Export/Email Matches in the desktop app — see the roadmap) into
  the same match-detail shape `Scorecard` expects, with
  `source="cricketstatz"`. Unlike the other two sources, `.MXP` is a
  plain, fully-documented `Key=Value` text format (`cricketstatz/MXP
  Format.doc`) and
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
  `cricketstatz/ELPM2018_all_matches.mxp`): zero foreign-key violations, batting/
  bowling figures cross-checked against the bundled historical demo data
  match real cricket records exactly (Larwood 5/96, McCabe's 187\*, and
  all five 1932-33 Bodyline Test results), and career stats for a known
  player (`I Wade`) come back as a plausible multi-season all-rounder
  record end to end through the existing `sqlite_queries.py` layer. Run
  `python3 mxp_parser.py <mxp-file>... --sqlite-db <path>` to ingest one
  or more `.MXP` exports.
- **`cricketstatz_txt.py`** — A **fifth source**, `source="cricketstatz_txt"`:
  individual CricketStatz match scorecards saved/printed as plain text
  (`cricketstatz/2010 scorecards/*.txt`), a completely different layout
  from the bulk `.MXP` export `mxp_parser.py` reads — no numeric ids at
  all, short club codes (`ELPM`, `F&H`, `WLM`, `SH`, `TSJ`, ...) instead
  of the fuller names the other three sources use, and its own
  batting/bowling/extras text format (handles every dismissal type
  found in practice: `not out`, `dnb`, `Absent Hurt`, `retired hurt`,
  `b`, `c` with a named or unknown `?` fielder, `c&b`, `lbw`, `st`, and
  `run out` including the two-fielder relay form `run out A/B`). Filled
  in 2010 — one of the four seasons (2010-2013) with otherwise zero
  match data of any source, see the "Milestone" section above — with 37
  matches, each cross-checked innings-by-innings against its own
  printed total (batting + extras = TOTAL; bowling wickets = total
  wickets minus run-outs) before being trusted. `source_match_id` is
  derived from match content (`home|away|date`), not the filename —
  confirmed necessary: some files in the 2010 batch are byte-identical
  copies of a *different* match saved under the wrong name, which a
  filename-keyed id would have double-counted instead of collapsing
  onto one match via `insert_match()`'s existing idempotency. The CLI
  also cross-checks the date implied by each filename against the
  date the file's own content parses to, and flags a mismatch instead
  of trusting either blindly — this caught two files whose *real*
  fixture (a different date entirely) is still missing. Opposition
  club/team identity needs the same `reconcile/decisions.yaml` merge
  treatment as any other source, same as ELPMCC's own `ELPM` short
  code did. Run `python3 cricketstatz_txt.py <txt-file>... --sqlite-db
  <path>` after the other sources; `--json-out <path>` mirrors
  `crichq_pdf.py`'s backup convention.
- **`nmcl_stats.py`** — Ingests the North Manchester Cricket League's
  own "Final Averages" reports into `nmcl_season_stats` — a separate
  table from `innings`/`batting_innings`/`bowling_innings`/
  `match_appearances`, since these reports only ever give a season-end
  aggregate for players clearing a qualification threshold (or, for the
  2010 rows specifically, a season-end total minus what's actually
  ingested from real scorecards — see below), never a match, an
  innings, or a full squad. Two different provenances feed the same
  `ELPM_ROWS` list, both re-typed into one consistent shape rather than
  parsed at read time: 2000-2005 are `nmcl stats/*.tif` **scans** with
  no machine-readable text layer, transcribed by hand (not OCR'd — see
  the module docstring for why a misread was too risky on a
  qualification-threshold table); 2011-2013 are the same report as a
  **native Excel workbook** (`nmcl stats/NMCL <year> FINAL
  AVERAGES.xls`) and genuinely machine-parsed (`DIV1BAT`/`DIV1BOWL`/
  `DIV2`/`DIV3`/`DIV4` sheets). A third kind of row, only for 2010,
  isn't from an NMCL report at all: the club's own official
  end-of-season player summaries (`cricketstatz/2010_1st_XI_Complete_
  Summary.txt`, `..._2nd_XI_...`) cover every match played that season,
  so the *difference* between a player's official total and what
  `cricketstatz_txt.py` actually ingested from real scorecards is
  exactly the missing matches' combined contribution — the same
  season-aggregate shape as a real NMCL row, just derived by
  subtraction (see the module docstring for why `innings_played`/
  `average` are deliberately left blank on those specific rows). Player
  identity works the same way as every other source —
  `source="nmcl_stats"`, a new canonical player row per (until
  reconciled) printed name via the same `_upsert_player()` every other
  source uses, so a `reconcile/decisions.yaml` merge is what actually
  links e.g. `"F Daly"` here to the `Fran Daly` CricHQ/CricketStatz
  identity, not this module guessing. Run `python3 nmcl_stats.py
  --sqlite-db <path>` after the other sources. Ingested so far: **77
  rows across 10 seasons** (2000-2005, 2010-2013) — every transcribed
  name is linked by `decisions.yaml` to a real identity except `R
  Savage`, `J Bond`, and `D Rushton`, which don't match anyone else in
  the archive and are left as their own new players rather than
  guessed at. 2011-2013 (and 2010, beyond the residual figures already
  captured) still only have season aggregates, not full scorecards —
  real match-level data for those years, if it turns up, would let
  `nmcl_season_stats`' rows for them be replaced with real `matches`/
  `innings` rows instead.
- **`scorebooks.py`** — A **sixth source**, `source="scorebook"`: full
  match-level scorecards transcribed by hand from photographs of physical
  scorebook pages (`scorebooks/*.jpg`) — the club's own paper records,
  used when a match is confirmed missing from every other source and a
  scorebook page for it turns up. Unlike `nmcl_stats.py`'s scanned sheets
  (season aggregates), a scorebook page carries real per-innings batting/
  bowling/dismissal detail, so it produces the same match-detail dict
  shape `cricketstatz_txt.py`/`crichq_pdf.py` do and goes through the same
  `insert_match()` path — no separate table. There is no machine-readable
  text to parse, so (like `nmcl_stats.py`'s pre-2005 scans) `MATCHES` is a
  hardcoded, manually-transcribed list rather than something read at
  runtime; each entry's docstring records which image(s) it came from and
  the innings-total/bowling-total cross-checks used to catch a misread
  before trusting it (the same "verify the sums, don't guess" discipline
  as every other source here) — including one genuine read correction
  this way: a batsman's dismissal that first looked like "absent" only
  reconciled against the bowling-wicket arithmetic once read again more
  carefully. First match: 11-Jul-2010, ELPM 1st XI away
  to Failsworth Macedonia CC — the scorecard behind Gavin Greaves' 170 and
  Ian Wade's 163 in a 339-run 3rd-wicket stand, previously missing from
  every source including `nmcl_stats.py`'s own 2010 residual-total rows
  (which knew matches were missing but not which innings they contained).
  **15 matches total as of this writing**: that one 2010 1st XI match,
  one 2007 2nd XI match (East Lancs PM v Bury CC, team XI unstated on the
  page itself), and all 13 of the 2nd XI's 2011 matches — see the
  "Milestone" section above for the season-by-season breakdown and what's
  still pending (2012/2013 photographed, not yet transcribed). Run
  `python3 scorebooks.py --sqlite-db <path>` after the other sources.
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
  Excludes junior teams by default the same way (`include_juniors=False`) —
  U9/U11 appearances/batting/bowling/fielding stay out of every career
  total and leaderboard, keyed off `teams.is_juniors` (see `sqlite_store.py`
  above); the underlying rows are untouched, so `include_juniors=True` (or
  filtering to one junior `team_id` directly, which already overrides this)
  brings them back. Nothing else in this project treats junior cricket as
  second-class — it's ingested and stored exactly like senior fixtures —
  this is purely a default view on top, not a data restriction.
  `nmcl_stats.py`'s season-aggregate rows (`nmcl_season_stats` — a
  qualification-threshold report, not per-match data, see that module's
  bullet above) are excluded by the same "opt in" pattern
  (`include_nmcl=False`) rather than folded in silently: a season
  aggregate can't honestly contribute `games_played`/fours/sixes/fifties/
  hundreds/economy/bowling strike rate the way a real scorecard row can,
  so `include_nmcl=True` only adds the figures that stay valid when
  summed across a season total and real match data — runs, times
  dismissed, highest score, wickets, runs conceded, catches, and the
  averages recomputed from those combined totals — leaving the rest
  alone. A row that actually received an NMCL contribution this way has
  `includes_nmcl=1` on it, so a blended total is never mistaken for a
  pure match-level one; `nmcl_season_stats(conn, player_id=, season=)`
  returns the raw rows on their own, un-blended, for anyone who wants to
  see exactly what a blend is made of (or look at a season — 2000-2005,
  2011-2013 — this club has no match-level data for at all).
  **`team_id` filtering works the same for every team, including
  once-overlooked ones** — confirmed by actually running it rather than
  assumed: `East Lancs Millers` (the T20 side, `team_id` varies by build
  order — look it up by name, `SELECT team_id FROM teams WHERE
  team_name = 'East Lancs Millers'`) filters cleanly through both
  `career_stats(team_id=...)` (52 players across its 29 CricHQ matches,
  e.g. Ian Wade's 254 runs there — correctly a subset of his ~5900-run
  *overall* career total, not double-counted or missing) and
  `SQLPlayerStats(...).top_runs(team_id=...)`; team-name *aliases*
  confirmed via `reconcile/decisions.yaml` (e.g. `Clifton Kingfishers` —
  a real alternate name for one of Clifton CC's teams, merged from two
  sources into its own canonical team, not folded into "2nd XI") filter
  the same way once merged. No code change was needed for any of this —
  team/club identity resolution never special-cased team names to begin
  with, so a team just needed to actually be tried once to confirm it.
- **`reconcile/decisions.yaml`** — The single, human-curated, human-readable
  record of every reconciliation decision: which `(source, source_*_id)`
  refs are the same real player/club/team/ground (with a `canonical_name`
  you write, not just accept — see its own header for the full "how to
  edit this" guide), a club's confirmed home ground (`club_home_grounds`),
  rules that fix a source's own unusably vague per-match venue text
  for one club's home fixtures (`ground_overrides`), and confirmed
  duplicate fixtures — the same real match entered independently into two
  sources (found concentrated around the 2016 and 2018 crichq_pdf/
  cricketstatz transition period, where both an old and a new
  scorekeeping system were fed the same games) — each recorded as a
  `keep`/`remove` ref pair (`duplicate_matches`) and applied by deleting
  the `remove` side's `matches` row outright (cascading to its own
  innings/batting/bowling/appearances), not a merge — there's no
  ambiguity to preserve, just one copy too many. `pending:` is where
  `reconcile_audit.py` writes every new candidate it finds (see that
  bullet below) — nothing to hand-copy out of a report; work through it
  (correct `canonical_name`, set `status: confirmed`/`audited`) and run
  `python3 reconcile.py --promote` to sweep confirmed entries into the
  real sections below and everything else into `rejected:` — candidates a
  human has looked at and explicitly *not* merged, either confirmed
  different (`status: rejected`) or genuinely undecided (`status: pending`
  there too, i.e. postponed for later) — read by `reconcile_audit.py` to
  keep something already reviewed out of its "new candidates" list without
  losing the decision (or non-decision) already made. This file is data,
  not code: `reconcile.py` applies it exactly as written, and it's the
  "readable file" the reconciliation process produces once populated, not
  a separate report generated from something else. Changing a decision
  later means editing this file and rebuilding the `.sqlite` from scratch
  (see the README's "If in doubt" section) — there's no separate undo,
  since a merge deletes rows. Edited via `ruamel.yaml`'s round-trip mode,
  not plain PyYAML, specifically so `reconcile_audit.py`/`reconcile.py
  --promote` can rewrite it without silently stripping every comment in
  it. Every ref (`{source, id, ...}`) also carries a `name:` — the row's
  display name at that source at the time it was written — so a bare id
  is never the only thing to check a decision against; `reconcile_audit.py`
  fills this in automatically for anything it writes, hand-added refs
  need it added by hand. A given `(source, id)` ref is meant to belong to
  exactly one place in this file at a time (one confirmed merge, one
  `rejected:` entry, or one `pending:` entry, never two) — `python3
  reconcile.py --check` scans for violations without touching anything,
  and `apply`/`--promote` both run the same check first and refuse to
  proceed on a conflict. Found for real once: a `rejected:` entry for
  Ian Wade's father (same name, different real person) had accidentally
  also listed the *real* Ian Wade's own `play_cricket` ref — harmless by
  itself, but a real hazard, since `reconcile_audit.py`'s `rejected:`/
  `pending:` suppression matches on any shared ref, so a ref double-booked
  like that can wrongly suppress a genuinely new candidate touching the
  entry that ref actually belongs to.
- **`reconcile.py`** — Cross-source identity merging for players, clubs,
  teams, *and* grounds (see ROADMAP.md), plus applying club home
  grounds and ground overrides — all read from `reconcile/decisions.yaml`
  (above). `merge_players(conn, source_refs)` / `merge_clubs(...)` /
  `merge_teams(...)` / `merge_grounds(...)` each repoint a confirmed list
  of `(source, source_*_id)` refs, and every fact-table row that
  references them, onto one surviving canonical row — sharing one generic
  `_merge_entities()` implementation. Run `python3 reconcile.py
  --sqlite-db <path>` after ingesting (all) sources to apply every
  decision; re-running is idempotent, including the ground overrides
  (they only touch a match whose `ground_id` doesn't already point at the
  target). Player identity gets no automatic pass at all (names are too
  ambiguous — initials, nicknames, two different people sharing a
  surname+initial — to guess at safely), so every player decision is a
  from-scratch human confirmation; clubs/teams/grounds get a conservative
  automatic merge for the exact/near-exact case already
  (`SQLiteStore._upsert_club()`/`._upsert_team()`/`._upsert_ground()`, see
  above) — `decisions.yaml`'s merge lists are for what that can't safely
  guess at. Candidates for all four come from `reconcile_audit.py`
  (below), not from this module itself. No query-layer changes are needed
  after a merge: `career_stats()`/`SQLPlayerStats` already aggregate by
  `player_id` alone, across every source. `merge_players()` shares its
  underlying mechanism with `SQLiteStore.merge_players()` above, built
  independently — see that bullet for the overlap. `python3 reconcile.py
  --promote` is the other half of the `pending:` workflow (yaml-only,
  doesn't touch the database): sweeps `decisions.yaml`'s `pending:`
  section by each entry's `status` — `confirmed`/`audited` moves it into
  the real merge section, anything else (still `pending`, or explicitly
  `rejected`) moves into `rejected:` — then run `reconcile.py` again
  (without `--promote`) to actually apply what got confirmed. `python3
  reconcile.py --check` runs the same "no ref in two places" validation
  `apply`/`--promote` already run automatically before touching anything
  (see the `decisions.yaml` bullet above), as a standalone dry-run.
- **`reconcile_audit.py`** — Generates a Markdown report over an
  already-built SQLite store: a data-quality scan (distinct competitions/
  leagues/grounds/seasons, rarest-first so a likely typo surfaces near the
  top, plus any crichq_pdf.py "Unknown (...)" placeholder rows; also a
  "Candidate duplicate matches" check — same date, same ELPM team,
  identical per-innings runs, two different sources — that matches on the
  scores themselves rather than opposition club/team identity, so a
  duplicate hiding behind two unmerged spellings of the same opposition
  club still surfaces even before that club's ref merge is written; added
  after three such duplicates were found by hand, see the "Milestone"
  section above) and
  reconciliation candidates for clubs, teams, grounds, and players that
  look like the same real thing split across canonical rows but aren't
  safe to merge automatically. Never writes to the SQLite database — but
  DOES write to `reconcile/decisions.yaml` (see that bullet above):
  every run appends anything new it finds into `pending:`, each with a
  suggested `canonical_name` and `status: pending`, ready to review —
  nothing to hand-copy out of the Markdown report any more (pass
  `--no-write-pending` to skip this and only generate the report, as
  before this existed). Run `python3 reconcile_audit.py --sqlite-db
  <path> --out reconcile/data_quality_report.md` after ingesting (all)
  sources. A candidate already recorded under `decisions.yaml`'s
  `rejected:` (confirmed different, or still undecided) is held out of
  the "new candidates" lists and shown separately instead, so a decision
  already made — including a "not yet" one — doesn't get suggested again
  as if it were new; a candidate already sitting in `pending:` keeps
  whatever `canonical_name`/`status` a human has since set on it rather
  than being overwritten by a fresh run, and a cluster that grows a new
  ref (a third spelling surfaces) gets that ref merged into the existing
  `pending:` entry instead of creating a duplicate — including
  transitively, when two otherwise-unrelated clusters found in the same
  run both overlap a third (confirmed happening in practice: an
  exact-match cluster and a separate, broader first-initial+surname
  cluster both touching "M Partington"/"M.P Partington"/"Mp Partington").
  A ref already claimed anywhere in `decisions.yaml` (a confirmed merge,
  `rejected:`, or `pending:` itself) is stripped out of a fresh candidate
  before it's written — otherwise a confirmed merge's own survivor row
  can look, to the clustering, just like a fresh candidate the moment its
  `canonical_name` gets set (e.g. to "Ian Wade"), re-listing refs the
  survivor already owns and tripping `reconcile.py --check`. That
  filtering has its own follow-on risk, though: a candidate built only
  from the refs it still has left, after the claimed ones are stripped
  out, can end up suggesting a `canonical_name` that matches an entry
  already confirmed elsewhere — promoting it as-is via `--promote` would
  then create a *second*, disconnected entity with the same display name
  rather than folding into the one that already exists. Every such
  collision — freshly found this run, or already sitting unflagged in
  `pending:` from an earlier one — gets a `note:` warning written onto
  the entry (self-healing: re-running the audit restores the note if it's
  ever stripped) and a line printed to the console; the human still has to
  decide by hand whether the refs belong in the existing confirmed entry
  instead. Club/team candidate
  clustering is deliberately exact-equality-only (on a normalised key
  looser than the automatic merge's — e.g. also drops a trailing regional
  qualifier like "Bradshaw CC, **Lancs**") rather than fuzzy/substring
  matching: a bare similarity/containment check was tried during
  development and produced real false positives (short club names being
  substrings of unrelated ones — "Shaw CC" / "Bradshaw CC" / "Walshaw CC"
  are three different real clubs — and "Prestwich 2nd XI" / "Prestwich 3rd
  XI" reading as near-identical text despite the differing ordinal being
  exactly what makes them different teams), so anything that digit-conflicts
  or merely resembles another name without matching it exactly is left out
  rather than risking a wrong suggestion. Ground candidates are grouped by
  home club instead, not by name similarity at all — ground names vary far
  too much in form across sources for text matching to find them
  ("ELPMCC" / "Croft Lane, ELPM" share no substring, despite being the
  same real ground) — filtered to only count a ground as a same-club
  candidate when its name contains that club's own name-initials acronym
  (≥3 letters), after finding that CricketStatz's `home_team_id` isn't a
  reliable "who actually hosted this" signal (it sometimes names the
  visiting side as home even though `ground_name` still correctly shows
  the true venue — discovered via the ground-candidate report itself
  flooding every real club with dozens of unrelated one-off "candidates"
  before this filter existed). A ground shared across many different
  clubs' home matches is reported separately, and split by match-count
  concentration into "likely a vague placeholder" (no club has a
  majority — CricHQ's `"England - Lancashire"` is the example) vs "likely
  that same CricketStatz home/away unreliability" (one club has the clear
  majority) — only the former gets a suggested `ground_overrides` action;
  the latter is a data-quality note about that source's own field, not
  something a merge or override can fix. Player-name candidates are looser
  in exchange for being explicitly labelled non-authoritative — a shared
  initial+surname, or the exact same name after stripping case/whitespace/
  punctuation — sorted by combined appearance count so the highest-signal
  groups surface first. See `reconcile/data_quality_report.md` — a
  committed snapshot from the full archive (see the "Milestone" section
  above for current match/source counts), itself a live
  example of what running this finds — regenerate it any time; it's
  disposable, derived output, not a hand-maintained decision record like
  `decisions.yaml`.

## Retired

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

## Sample data

Reorganised into folders per source. Superseded/duplicate files (the old
single-season CricHQ PDF, the two intermediate CricketStatz `.csd` backups
and their partial `.MXP` exports, and the three CricketStatz installer
`.exe`s — no longer needed once their `.MXP` exports were captured) have
been removed from the repo; only the current, complete file per source
remains.

- `playcricket/playcricket_2026_demo.json` — a synced local database
  (70 matches, season 2026 only) showing the storage schema in practice; the
  fixed, small dataset the README's "Using the example files" walkthrough
  runs against. Frozen as a tutorial sample rather than kept in sync going
  forward — see `playcricket_24_25_26.json` below for the real, maintained
  cache.
- `playcricket/playcricket_24_25_26.json` — the club's Play-Cricket history
  for seasons 2024–2026, synced via `PlayCricketDatabase.sync_season()`
  (see the README's "Using the main database" section): **248 matches** (101 in 2024, 77
  in 2025, 70 in 2026 so far), full scorecards downloaded for every one
  (zero failed downloads). Builds into **48 clubs, 93 teams, 1241 players**
  with zero foreign-key violations. ELPMCC fielded six sides across the
  period (1st/2nd/3rd XI, a one-off Friendly XI, Under 11s, Under 9s) across
  GMCL league divisions (moving division each year), junior sections, and a
  handful of cup competitions. This is the file to rebuild the SQLite store
  from for real reconciliation work, rather than the smaller 2026-only demo
  above.
- `crichq/ALL_CRICHQ_SCORECARDS.pdf` — the club's **complete** CricHQ
  archive in one file (703 pages), replacing the old single-season
  `ELPM 1st XI 2019.pdf`. **374 matches** (328 played, 46 abandoned),
  spanning **seven seasons, 2016 and 2018–2023** (see below — 2016 was
  invisible until the header-splitting bug was fixed), across every level
  the club runs — 1st/2nd/3rd/4th XI, Sunday sides, league and cup
  competitions, and the T20 side (`East Lancs Millers`, GMCL20 cup
  competitions, 29 matches — filters cleanly through `career_stats(team_id=
  ...)`/leaderboards on a par with every other team, confirmed under
  "Modules" above). Parses cleanly at the text level (5725 batting rows, 3225
  bowling rows, 6658 team-sheet entries across all matches) and now
  **ingests cleanly end to end**: `python3 crichq_pdf.py
  crichq/ALL_CRICHQ_SCORECARDS.pdf --sqlite-db <path>` loads all 374
  matches with zero foreign-key violations. (Seven of an original 381
  parsed "matches" turned out to be genuinely content-free abandoned-game
  placeholders — no scorecard, no teams beyond an "Unknown (...)" stand-in
  — and `_parse_match()` now returns `None` for those, skipped by
  `parse_pdf()`, rather than loading an empty row with no stats value.) It
  previously raised
  `ValueError: You are trying to merge on str and float64 columns for key
  'opposition_id'` on the first match, in `Scorecard.get_performances()`'s
  fielding-count merge (`playcricket_scorecard.py`) — that turned out to be
  a symptom, not the root cause. The real bug was in `crichq_pdf.py`'s
  match-splitting: `MATCH_HEADER` required a `"<home> vs <away>"` line
  before every match's `"Date:"/"Venue:"` line, but 42 matches — an entire
  season (2016) exported by an older report-generator layout — omit that
  line and put `"Date:"`/`"Venue:"` on separate lines instead. Every one of
  those 42 unmatched headers meant its whole scorecard silently got
  appended onto the *previous* successfully-matched match's body instead of
  starting a new one, so e.g. one nominal "match" ended up 38,394 characters
  long and contained parts of ~30 different real matches concatenated
  together — wrong runs/wickets attributed to the wrong fixture, `innings`
  numbers up to 30, and (for the one match that happened to crash first) an
  `opposition_id` column that was all-`NaN` for one team because its
  fabricated "batting team" name never matched the real match's `home`/
  `away` ids. Fixed by loosening `MATCH_HEADER` to make the `"vs"` line and
  the same-line-vs-split-line `Date`/`Venue` layout both optional, and
  falling back to the team names from the innings' own `"Batting:"`/
  `"Bowling:"` headers (in that order) when the `"vs"` line is missing — see
  ROADMAP.md for a second, smaller bug (`get_performances()` crashing on a
  match with batting but zero recorded bowling) found once real matches
  started reaching it.
- `crichq/crichq_pdf.json` — a **permanent, git-tracked backup of
  `parse_pdf()`'s output** for the file above: all 374 match-detail dicts
  (Play-Cricket shaped), generated with
  `python3 crichq_pdf.py crichq/ALL_CRICHQ_SCORECARDS.pdf --sqlite-db <path>
  --json-out crichq/crichq_pdf.json`. Plays the same role for the CricHQ
  side that `playcricket/playcricket_24_25_26.json` plays for Play-Cricket — a parsed,
  human-readable/greppable cache one layer above the raw source and below
  SQLite — except with no seasons/versioning wrapper, since the PDF is a
  closed archive parsed once rather than something synced incrementally.
  The point isn't just convenience: it means a future change to
  `crichq_pdf.py`'s regexes shows up as a `git diff` against known-good
  parsed output, rather than only surfacing (if at all) as silently wrong
  stats downstream — exactly the failure mode the header-splitting bug
  above was. Regenerate it (with the same command) any time the PDF is
  re-parsed after a parser fix; nothing currently reads this file back in
  (SQLite ingestion still runs directly off the PDF), so it's a backup/diff
  target today, not (yet) an alternate input path.
- `cricketstatz/ELPM2018.csd` — the club's live CricketStatz database
  export, format version **11**. Opens under CricketStatz build 11.2.49
  (installed under Wine — the installer itself has since been removed from
  the repo, see ROADMAP.md for how it was obtained) — see
  `cricketstatz/ELPM2018_all_matches.mxp` for the full export: the complete
  ELPMCC scorecard history, 2005-04-23 to 2018-07-21, 304 matches, verified
  clean (304/304 `Record=Match`/`Endmatch=True` pairs, zero foreign-key
  violations on ingestion).
- `cricketstatz/MXP Format.doc` — the official Red Axe/CricketStatz `.MXP`
  export format specification (a Word doc; read with `antiword` —
  LibreOffice's headless converter failed to load it in this environment
  for unclear reasons, antiword worked first try). Full field-by-field spec
  including the batsman `howout` codes (0=dnb, 1=Not Out, 2=Bowled,
  3=Caught, 4=C&B, 5=Hit Wicket, 6=LBW, 7=Retired Hurt, 8=Runout, 9=Stumped,
  10=Obstructed Field, 11=Handled Ball, 12=Retired Out, 13=Retired Not Out,
  14=Timed Out, 15=Hit Ball Twice, 16=Absent Hurt, 17=Absent Ill, 18=Caught
  Behind) and match-result codes, dated change-log back to 2000.
- `cricketstatz/bodyline_sample.mxp` — a Cricket Statz `.MXP` export (via
  File → Export/Email Matches, run under Wine), covering all 5 matches of
  the bundled `sample.csd` demo database ("The Bodyline Test Series") —
  what `mxp_parser.py` was validated against for historical accuracy
  (Larwood 5/96, McCabe's 187\*, all five 1932-33 Test results).
- `nmcl stats/*.tif` — twelve scanned A4 pages (2000–2005, two per
  season): North Manchester Cricket League "Final Averages" sheets, the
  club's paper-era stats predating even CricketStatz (whose own earliest
  match is 2005-04-23) — genuinely the only source of any kind for
  2000-2004 (see the "Milestone" section above and `nmcl_stats.py`
  above). Each year: page 1 is Division One batting, page 2 is Division
  One bowling plus a wicketkeeping block — everyone above a stated
  qualification threshold (e.g. "QUAL 11 INNS 200 RUNS AVGE 20.00"), not
  a full scorecard or even a full squad list. No Division Two page
  exists in any of these six scanned years, consistent with ELPM
  fielding no 2nd XI before 2006 (see the match data itself). Ingested —
  see `nmcl_stats.py` above.
- `nmcl stats/NMCL <2011|2012|2013> FINAL AVERAGES.xls` — the same NMCL
  report for three more seasons, this time as native Excel rather than a
  scan (`DIV1BAT`/`DIV1BOWL`/`DIV2`/`DIV3`/`DIV4` sheets — the latter
  three combine batting/bowling/wicketkeeping for whichever division
  isn't Division One). Genuinely machine-parsed, not transcribed by hand
  — see `nmcl_stats.py` above. Division Two/Three/Four rows are both
  real: the club's 2nd XI was relegated across these seasons, so every
  division other than One is still the 2nd XI specifically, confirmed by
  the club rather than assumed (an ELPM "3rd XI" does genuinely exist
  elsewhere in the archive, from 2018 onward, which is exactly why this
  needed asking rather than guessing either way).
- `cricketstatz/2010 scorecards/*.txt` — 40 individual CricketStatz match
  scorecards for the 2010 season (both XIs), covering a year the bulk
  `.MXP` export doesn't reach at all — see `cricketstatz_txt.py` above
  and the "Milestone" section. Confirmed incomplete: 3 of the 40 files
  are byte-identical copies of a different match saved under the wrong
  name (their real fixture's content is missing), and cross-checking
  against the club's own official summaries (next bullet) shows the 1st
  XI specifically is short by more matches than that alone explains —
  at least 2 more 1st XI fixtures were never provided under any
  filename, correct or otherwise.
- `cricketstatz/2010_1st_XI_Complete_Summary.txt`,
  `2010_2nd_XI_Complete_Summary.txt` — the club's own official
  end-of-season player summaries for 2010, covering every match played
  that season (unlike the scorecard files above, which are confirmed
  incomplete). Used once, as a cross-check: the difference between each
  player's official season total here and what `cricketstatz_txt.py`
  actually ingested from the scorecard files is the missing matches'
  combined contribution, added to `nmcl_season_stats` via `nmcl_stats.py`
  (see that bullet for why treating this as a season-aggregate row,
  not a fabricated match, is the honest way to record it).
