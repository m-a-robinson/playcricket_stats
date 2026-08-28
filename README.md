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

## Milestone: all original data now imported (2026-08-26)

Every data source this project set out to ingest is now in the store, at
once, end to end: the **complete Play-Cricket history currently reachable**
(seasons 2024-2026, live-synced via the API and kept that way — see
"Maintaining the database"), the **complete CricHQ PDF archive** (2016 and
2018-2023), and the **complete CricketStatz archive** (2005-2018). That's
**926 matches across all three sources** (248 Play-Cricket + 304 CricketStatz
+ 374 CricHQ, the latter down from an earlier 381 once seven genuinely
content-free abandoned-match placeholders were fixed to be skipped rather
than ingested as empty rows — see `crichq_pdf.py`'s bullet below) built into
one normalised SQLite store with **zero foreign-key violations**. Roadmap
items 1-3 below (data foundation, CricHQ ingestion, CricketStatz ingestion)
are accordingly all *Done*, together, not just individually — this is the
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
match-level detail for. That's **964 matches raw, 935 once `reconcile.py`
applies `duplicate_matches`**. 2011-2013, and the rest of 2010 beyond
what's now captured, still have no match-level source, only season
aggregates; if genuine scorecards or scorebook pages for those turn up,
the same `cricketstatz_txt.py`/`scorebooks.py` pipelines would replace
the aggregate figures with real per-match data.

Building a season-by-season match export as an early cross-check tool for
the scorebook-digitisation effort (a workbook with one sheet per season,
2000-2016) surfaced three more genuine crichq_pdf/cricketstatz transition
duplicates that the earlier 29-duplicate sweep had missed — one from the
2005 CricketStatz/CricketStatz-text overlap (see `cricketstatz_txt.py`'s
mislabeled-file note above) and two from 2016, one of which was hiding
behind two never-merged spellings of the same opposition club ("Flixton
CC" vs "Flixton C&SC"). `reconcile/decisions.yaml`'s `duplicate_matches:`
now has 32 entries, not 29, and `reconcile_audit.py` gained a permanent
"Candidate duplicate matches" check (same date, same ELPM team, identical
per-innings runs, two different sources) so this class of bug surfaces on
every future audit instead of needing another by-eye pass. **964 matches
raw, 932 once `reconcile.py` applies `duplicate_matches`.**

Play-Cricket's own history isn't necessarily fully backfilled yet — 2024-2026
is what's been synced so far; earlier seasons (however far back the club's
Play-Cricket presence goes, likely somewhere in the 2018-2023 range CricHQ
already covers) remain a possible future backfill, see "Maintaining the
database" below. CricHQ and CricketStatz, being closed archives, are
complete by definition once ingested.

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
  parsing engine. `batting_table()` (display only — the stored
  `batting_innings.balls` figure is untouched) drops the balls-faced
  column entirely for an innings where every row reads 0, rather than
  printing a whole card of misleading zeroes: CricketStatz simply didn't
  record balls-faced before ~2016 (see "Modules" below), and a genuine
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
  yet done (see "Not built yet"). Run `python3 sqlite_store.py` to (re)build
  the Play-Cricket side of the store from `playcricket_database.json`.
- **`crichq_pdf.py`** — Parses CricHQ "Full Scorecard Report" PDF exports
  into the same match-detail shape `Scorecard` expects, so they load
  through the exact same `SQLiteStore.insert_match()` path as Play-Cricket
  data, with `source="crichq_pdf"`. Handles mid-row PDF line-wraps, partial/
  abandoned matches, and the CricHQ dismissal-text format (`"c X b Y"`,
  `"run out (A/B)"` credited to the first-named fielder, etc.). Player
  identity is deliberately **not** matched against existing players — every
  CricHQ name becomes its own new canonical player for now (see "Not built
  yet" below). Also copes with two report-generator layouts concatenated
  into one archive PDF: most matches have a `"<home> vs <away>"` line
  directly before a single `"Date: X Venue: Y"` line, but an older layout
  (seen on 2016-season pages) omits the `"vs"` line entirely and splits
  `"Date:"`/`"Venue:"` onto separate lines — recovered by inferring the two
  team names from the innings' own `"Batting:"`/`"Bowling:"` headers instead
  when the header's `"vs"` line isn't there (see "Sample data" and the
  roadmap for how this was found). `INNINGS_HEADER`/`BOWLING_HEADER` also
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
  Export/Email Matches in the desktop app — see the roadmap below) into
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
  carefully. First (and so far only) match: 11-Jul-2010, ELPM 1st XI away
  to Failsworth Macedonia CC — the scorecard behind Gavin Greaves' 170 and
  Ian Wade's 163 in a 339-run 3rd-wicket stand, previously missing from
  every source including `nmcl_stats.py`'s own 2010 residual-total rows
  (which knew matches were missing but not which innings they contained).
  Run `python3 scorebooks.py --sqlite-db <path>` after the other sources.
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
  (see "If in doubt" below) — there's no separate undo, since a merge
  deletes rows. Edited via `ruamel.yaml`'s round-trip mode, not plain
  PyYAML, specifically so `reconcile_audit.py`/`reconcile.py --promote`
  can rewrite it without silently stripping every comment in it. Every ref
  (`{source, id, ...}`) also carries a `name:` — the row's display name at
  that source at the time it was written — so a bare id is never the only
  thing to check a decision against; `reconcile_audit.py` fills this in
  automatically for anything it writes, hand-added refs need it added by
  hand. A given `(source, id)` ref is meant to belong to exactly one place
  in this file at a time (one confirmed merge, one `rejected:` entry, or
  one `pending:` entry, never two) — `python3 reconcile.py --check` scans
  for violations without touching anything, and `apply`/`--promote` both
  run the same check first and refuse to proceed on a conflict. Found for
  real once: a `rejected:` entry for Ian Wade's father (same name,
  different real person) had accidentally also listed the *real* Ian
  Wade's own `play_cricket` ref — harmless by itself, but a real hazard,
  since `reconcile_audit.py`'s `rejected:`/`pending:` suppression matches
  on any shared ref, so a ref double-booked like that can wrongly suppress
  a genuinely new candidate touching the entry that ref actually belongs
  to.
- **`reconcile.py`** — Cross-source identity merging for players, clubs,
  teams, *and* grounds (see roadmap item 4), plus applying club home
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
  committed snapshot from the full archive (see the milestone note at the
  top of this README for current match/source counts), itself a live
  example of what running this finds — regenerate it any time; it's
  disposable, derived output, not a hand-maintained decision record like
  `decisions.yaml`.

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

Reorganised into folders per source. Superseded/duplicate files (the old
single-season CricHQ PDF, the two intermediate CricketStatz `.csd` backups
and their partial `.MXP` exports, and the three CricketStatz installer
`.exe`s — no longer needed once their `.MXP` exports were captured) have
been removed from the repo; only the current, complete file per source
remains.

- `playcricket/playcricket_2026_demo.json` — a synced local database
  (70 matches, season 2026 only) showing the storage schema in practice; the
  fixed, small dataset the "Basic usage" walkthrough below runs against.
  Frozen as a tutorial sample rather than kept in sync going forward — see
  `playcricket_24_25_26.json` below for the real, maintained cache.
- `playcricket/playcricket_24_25_26.json` — the club's Play-Cricket history
  for seasons 2024–2026, synced via `PlayCricketDatabase.sync_season()`
  (see "Maintaining the database" below): **248 matches** (101 in 2024, 77
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
  competitions, and the T20 side (see the "ELPMCC Millers" note under "Not
  built yet"). Parses cleanly at the text level (5725 batting rows, 3225
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
  the roadmap for a second, smaller bug (`get_performances()` crashing on a
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
  the repo, see the roadmap for how it was obtained) — see
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
  below). Each year: page 1 is Division One batting, page 2 is Division
  One bowling plus a wicketkeeping block — everyone above a stated
  qualification threshold (e.g. "QUAL 11 INNS 200 RUNS AVGE 20.00"), not
  a full scorecard or even a full squad list. No Division Two page
  exists in any of these six scanned years, consistent with ELPM
  fielding no 2nd XI before 2006 (see the match data itself). Ingested —
  see `nmcl_stats.py` below.
- `nmcl stats/NMCL <2011|2012|2013> FINAL AVERAGES.xls` — the same NMCL
  report for three more seasons, this time as native Excel rather than a
  scan (`DIV1BAT`/`DIV1BOWL`/`DIV2`/`DIV3`/`DIV4` sheets — the latter
  three combine batting/bowling/wicketkeeping for whichever division
  isn't Division One). Genuinely machine-parsed, not transcribed by hand
  — see `nmcl_stats.py` below. Division Two/Three/Four rows are both
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

### Not built yet

- **Automatic** reconciliation/merge logic across the three sources for the
  *harder* cases (conflict resolution, and player/club/team identity
  matching beyond exact/near-exact names). Clubs and teams now get an
  automatic merge for the exact/near-exact case at insert time
  (`SQLiteStore._upsert_club()`/`._upsert_team()` — e.g. "East Lancs Paper
  Mill CC" no longer splits into a separate `club_id` per source the way it
  used to), and `reconcile.py`/`reconcile_audit.py` (see "Modules" above)
  cover the fuzzier remainder for clubs/teams and everything for players —
  but only for groups a human has confirmed via `PLAYER_MERGES`/
  `CLUB_MERGES`/`TEAM_MERGES`; finding those groups with no human in the
  loop at all isn't built, and isn't attempted for players (see
  `reconcile_audit.py`'s module notes for why a bare similarity/containment
  check turned out to be actively unreliable even for clubs/teams, let alone
  names). Deliberately deferred to a review step across all three sources
  rather than guessed at during ingestion (see the "MR Robinson" /
  seven-Robinsons example this was scoped against).
- **Two manual player-merge tools that overlap and need reconciling with
  each other**: `SQLiteStore.find_players()`/`.merge_players()` (pairwise)
  and `reconcile.py`'s `merge_players()`/`PLAYER_MERGES` (registry-driven),
  built independently, doing the same underlying repoint. Pick one as
  canonical and retire the other — a housekeeping item, not yet done.
- **`ELPMCC Millers` (the T20 side) needs equal status to the 1st/2nd/3rd/
  4th XIs**, not second-class treatment as an afterthought. It shows up
  correctly as its own team once a source is ingested (confirmed in
  `crichq/ALL_CRICHQ_SCORECARDS.pdf` — 29 matches, club name
  `East Lancs Paper Mill CC`, team name `East Lancs Millers`, competing in
  the GMCL20 T20 cup competitions — team/club identity resolution doesn't
  special-case team names at all, so no code change was needed for that
  much) — but nothing downstream (leaderboards, career stats team
  filtering, any future team-level reporting) has been checked to make
  sure it's actually surfaced on a par with the longer-running XIs rather
  than just quietly present in the data. Worth an explicit check once
  `career_stats(team_id=...)`/team-level views get real use.
- The **2010-2013 season blackout** (see "Milestone" above) is now
  partially filled, not fully: 2010 has real match-level data
  (`cricketstatz_txt.py`, `cricketstatz/2010 scorecards/`; plus one
  further match from a hand-scored scorebook page via `scorebooks.py`),
  topped up with season-aggregate figures for the still-missing 1st XI
  matches (`nmcl_stats.py`, derived from the club's official 2010 season
  summaries). 2011-2013 only have NMCL season averages
  (`nmcl_stats.py`, native Excel this time, not scans) — no match-level
  source has turned up for those three years at all. If real scorecards
  or scorebook pages for 2011-2013 are found, `cricketstatz_txt.py`'s or
  `scorebooks.py`'s pipeline is what would ingest them.
- `nmcl_season_stats` isn't wired into `career_stats()`/leaderboards at
  all yet — it's pure season-aggregate data with no innings/match
  granularity to blend cleanly against per-match figures (no
  balls-faced/strike-rate, no fielding beyond keeping, no distinction
  between a not-out top score and one that just wasn't beaten). Blending
  it in without implying false precision, or misleadingly double-counting
  a season that also has real match-level rows, needs its own design
  pass, not just a UNION.
- Formatted scorecard export (image/PDF) for printing or framing.
- Social-media formatting for player performances and weekend results.
- Any CLI/UI entry point — everything today is a library, including the
  Play-Cricket sync itself (`playcricket_api.py`/`playcricket_database.py`
  have no `__main__` — see "Maintaining the database" above for the
  snippet a `sync_playcricket.py` wrapper would replace).
- **Four data-quality issues found reviewing sample scorecards across all
  three sources (2026-08-27), each a naming/reference-data problem rather
  than a parser bug, so deliberately left for manual reconciliation rather
  than guessed at in code — consistent with this project's existing
  "no fuzzy matching, human confirms it" approach (see roadmap item 4):**
  - **CricHQ's `ground_name` is always county-level, never a real ground**
    — confirmed by checking the raw PDF text directly: only 4 distinct
    values across all 381 matches (`England - Lancashire` ×377,
    `Derbyshire`/`Cheshire`/`Bedfordshire` ×1-2 each). There is no ground
    name anywhere in the source text for `crichq_pdf.py` to extract — the
    PDF's own `Venue:` field never carries one. Inferring a ground from
    the home team would be wrong often enough to matter (cup ties and
    Sunday friendlies aren't always played at the "home" side's own
    ground), so this needs a manual club → home-ground reference table
    instead. 75 distinct clubs appear across the archive (as home or
    away) if that table gets built.
  - **CricHQ's `result_description` now states the winner only** (fixed
    this session — see the commit that added `AWARDED_WIN_LINE` and
    extended `RESULT_LINE` for `"Won (D/L method)"` — previously showed
    both teams, e.g. `"X Lost. Y Won"`). 44 played matches still have no
    result recorded at all: 36 from the 2016-season report layout, which
    never prints a result line of any kind, and 8 marked `"Batting:"`-
    present but actually abandoned mid-match (`"Abandoned - Game
    Unfinished - No Result"`) — the latter are stored with
    `status="Played"` today since that flag only checks for the presence
    of a `Batting:` section, not for an actual result; worth a genuine
    `no_result` status distinction if these matter for stats later.
  - **CricketStatz team names carry their club's abbreviation prefix**
    (e.g. team name `ELPM 1st XI` for club `East Lancs Paper Mill`) where
    Play-Cricket/CricHQ keep the two separate — already surfaced by
    `reconcile_audit.py` as part of its 56 team-name splits (see roadmap
    item 4/step 7); resolved the normal way, via a `TEAM_MERGES` entry,
    not a parser change.
  - **CricketStatz's bare `"Division 1"`/`"Division 2"`/`"Division 3"`/
    `"Cup"` competition names (2005-2015, 223 matches) are missing an
    `NMCL` league prefix** — the club played in the NMCL (North Manchester
    Cricket League — see `nmcl stats/*.tif` above, the pre-CricketStatz
    paper archive from the same era) before moving to the GMCL, and the
    year ranges confirm the split cleanly: every bare `"Division N"`/
    `"Cup"` name falls in 2005-2015, while `"GMCL Division N"`-prefixed
    names only start in 2016. The exact cutover year isn't in the data
    itself, so renaming these needs the club's own confirmation of when
    the move happened before `competition_name` values can be corrected
    (by hand, or a small date-gated rename pass once confirmed).

## Basic usage (verifying progress in ipython)

Everything is a plain Python library today, so the easiest way to check
progress is to import the pieces directly in an `ipython` session and look
at what comes back. One-time setup:

```bash
pip install ipython pandas numpy requests pypdf ruamel.yaml
cd playcricket_stats
ipython
```

The examples below all use the files already in the repo
(`playcricket/playcricket_2026_demo.json`, `crichq/ALL_CRICHQ_SCORECARDS.pdf`)
— nothing needs an API key to run.

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
of the game:

```python
from playcricket_database import PlayCricketDatabase
from playcricket_scorecard import Scorecard

db = PlayCricketDatabase(api=None, filename="playcricket/playcricket_2026_demo.json")

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

### 4. Ingest a CricHQ PDF

```bash
python3 crichq_pdf.py "crichq/ALL_CRICHQ_SCORECARDS.pdf" --sqlite-db demo.sqlite
```

```
Parsing crichq/ALL_CRICHQ_SCORECARDS.pdf ...
  374 matches found in this file.
Done. Played: 328, Abandoned: 46
```

This used to crash on the very first match with `ValueError: You are trying
to merge on str and float64 columns for key 'opposition_id'` in
`Scorecard.get_performances()`'s fielding-count merge
(`playcricket_scorecard.py`) — see "Sample data" above for the real,
upstream bug that caused it (a `crichq_pdf.py` match-splitting bug silently
merging one season's worth of matches into their neighbours) and the
roadmap for the fix.

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
identity reconciliation across sources, see the roadmap, hasn't run
yet), so pass it explicitly to see the club's own players rather than
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

`reconcile.py` merges known player groups (`PLAYER_MERGES`) so a career
query spans every source that contributed to a group:

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

Against the full current archive this now gives a real three-source combined
record: **195 games, 4900 runs @ 30.2 (20 fifties, 9 hundreds), 151 wickets
@ 14.7 (8 five-fors), 85 catches**, spanning 2005-2018 (`cricketstatz`), the
full 2016-2023 CricHQ archive (`crichq_pdf`), and the current `play_cricket`
season — a fresh reproduction, superseding the old single-PDF-era figures
this step used to quote (151 games/3895 runs/107 wickets/63 catches, from
one 2019 `crichq_pdf` match rather than the full archive). One `cricketstatz`
ref originally in this group (id `1062`, a single-match "I Wade" playing for
the opposition, Swinton Moorside) turned out on inspection to be his
father — a different real person who happens to share the name — and has
been removed from `PLAYER_MERGES`; see roadmap item 4.

One thing this run surfaces that `PLAYER_MERGES` doesn't cover yet: the full
archive's greater variety of scorers means `career[career["player_name"] ==
"Ian Wade"]` still returns **two** rows, not one — a second, separate
`crichq_pdf` identity keyed on `"Ian Wade"` (the full first name, 4 games)
alongside the merged group's `"I Wade"` (abbreviated, the ref actually listed
in `PLAYER_MERGES`). Same underlying problem as the cross-source case
`PLAYER_MERGES` already exists to solve — no stable id, name-based matching
only — just occurring *within* one source now that it has enough scorers to
spell the same player two different ways. See "Not built yet"/roadmap item 4.

That exact-string query actually **understates** the gap: there's a *third*,
bigger unmerged identity, `"IW wade"` (48 games) — invisible to the query
above because its `known_as` doesn't literally equal `"Ian Wade"`, even
though it's obviously the same person. This is exactly why
`reconcile_audit.py` (see "Modules") exists rather than relying on ad-hoc
filtering to notice these: it buckets by first-initial + surname (and,
separately, by name after stripping case/whitespace/punctuation) rather than
requiring an exact string match, so `"I Wade"`/`"IW wade"`/`"Ian Wade"` all
land in one reported group together — see
`reconcile/data_quality_report.md`'s Players section.

Adding another player means adding another entry to `PLAYER_MERGES` (find
their refs with a query like the one in `reconcile.py`'s own investigation
notes) — nothing else changes, including after importing further CricHQ
PDFs: re-running `reconcile.py` is idempotent, and any *new* match for an
already-merged ref resolves straight to the survivor.

### 7. Audit the database for data-quality issues and reconciliation candidates

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
the **full archive** (see the milestone note at the top of this README for
current match/source counts — Play-Cricket via the real, live-synced
`playcricket_24_25_26.json` rather than the small demo file this walkthrough
otherwise uses), so it doubles as a worked example: an `"Add New Ground"`
value that's obviously a leaked UI placeholder, on 47 matches — common
enough to be a real gap in 2024's league-fixture ground data, not just a
one-off typo; a `"Bradshaw CC, Lancs"` vs `"Bradshaw CC"` club split (a
dropped regional qualifier neither exact-match nor SQLiteStore's own
automatic merge — see "Modules" — safely catches on its own, one of 9 such
club splits); dozens of team-name splits (one source's `"1st XI"` vs
another's club-prefixed `"ELPM 1st XI"`, 56 in total); and the
`"I Wade"`/`"IW wade"`/`"Ian Wade"` gap from step 6 above.

### 8. Poke at the raw tables directly

For anything the query helpers don't cover yet, plain SQL against `demo.sqlite`
works — the schema is in `schema.sql`:

```python
conn.execute("SELECT * FROM matches WHERE source='cricketstatz' LIMIT 1").fetchone()
conn.execute("SELECT * FROM v_batting_achievements LIMIT 5").fetchall()
conn.execute("PRAGMA foreign_key_check").fetchall()   # should always be []
```

Delete `demo.sqlite` and re-run steps 1/5 any time to rebuild from scratch —
nothing in the pipeline is destructive to the source JSON/PDF/`.MXP` files.

## Maintaining the database

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

`crichq/ALL_CRICHQ_SCORECARDS.pdf` now imports cleanly (see "Sample data"
and the roadmap for the match-splitting bug that used to block it) and
follows the same "import once, done" model as CricketStatz already does.

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
deliberately frozen file — the small fixed dataset the "Basic usage"
walkthrough above runs against — and isn't meant to be kept in sync the way
this one is.)

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
nothing in this project schedules it automatically yet, see "Not built
yet"/roadmap item 8).

**Directly answering "do I just run the API-connect and database
files?"**: not quite as they stand — `playcricket_api.py` and
`playcricket_database.py` are libraries with no CLI entry point (only
`sqlite_store.py` has one, and it deliberately never touches the API — see
its own module docstring). The snippet above is what running them
actually looks like today. A small `sync_playcricket.py` wrapping both
steps into one command (`python3 sync_playcricket.py --season 2026`)
would be a natural, easy addition if this becomes a routine task —
not built yet, flagged in "Not built yet" below rather than assumed.

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
last — always gets back to the same result. The
`.sqlite` file itself doesn't need to be committed to version control —
treat it as a derived build artifact, the same way `demo.sqlite` is
throughout the walkthrough above, and keep it out of git.

## Roadmap

1. **Data foundation** — *Done, and now proven against every original
   source at once* (see the milestone note at the top of this README:
   964 matches raw / 932 reconciled across six sources, zero
   foreign-key violations, all of them live in the store together, not
   just individually validated). SQLite store built
   (`schema.sql` / `sqlite_store.py`): players, clubs, teams, matches, innings,
   batting/bowling, match appearances (team sheets), and milestone views,
   with `source` on every fact table and canonical identity for players,
   clubs, *and* teams resolved through `*_source_ids` mapping tables (not
   just Play-Cricket's own numeric ids as primary keys — necessary once
   CricHQ, which has none, joined the store). Query/leaderboard layer
   (`sqlite_queries.py`) built and verified against the old pandas pipeline,
   which has now been retired (`player_performances.py`,
   `multi_player_stats.py`, and the redundant query methods on
   `PlayCricketDatabase` — see "Retired" above). Two separate manual
   reconciliation paths now exist — `SQLiteStore.find_players()`/
   `.merge_players()` and `reconcile.py`'s `merge_players()`/
   `PLAYER_MERGES` (see "Modules") — both used to unify Ian Wade's
   Play-Cricket, CricHQ, and CricketStatz identities into one career
   record (see Basic usage step 6). Still to do: reconcile the two tools
   with each other (see "Not built yet"), and an automatic reconciliation
   pass — neither manual tool scales to every player across many more
   CricHQ PDFs on its own.
2. **CricHQ PDF ingestion** — ***Done***, including on the club's full
   six-season-turned-seven-season archive — see "Sample data" above for the
   match-splitting bug that used to crash it and how it was found/fixed.
   `crichq_pdf.py` parses CricHQ's "Full Scorecard Report" PDF export into
   the same internal shape `Scorecard` uses; historically validated end to
   end against the club's old single-season export, `ELPM 1st XI 2019.pdf`
   (23 matches, 295 batting rows, 147 bowling rows, no unmatched lines) —
   since removed from the repo, superseded by the seven-season combined
   file above. Getting the full archive ingesting cleanly needed three more
   fixes on top of that original validation:
   - **The real blocker**: `MATCH_HEADER` (`crichq_pdf.py`) required a
     `"<home> vs <away>"` line before every match's `"Date:"/"Venue:"`
     line. An older report-generator layout, used for the entire 2016
     season, omits that line and puts `"Date:"`/`"Venue:"` on separate
     lines instead — 42 matches' worth. Every one of those missing headers
     meant `parse_pdf()`'s header-to-header body slicing silently appended
     that match's whole scorecard onto the *previous* match's body instead
     of starting a new one (one nominal "match" ended up 38,394 characters
     long, containing pieces of roughly 30 real matches with `innings`
     numbers running up to 30) — which is what produced the `opposition_id`
     dtype-mismatch crash below, on whichever match happened to hit it
     first, not a bug in the merge itself. Fixed by loosening
     `MATCH_HEADER` to make the `"vs"` line and the same-line-vs-split-line
     `Date`/`Venue` layout both optional, and — when the `"vs"` line is
     missing — inferring the two team names from the innings' own
     `"Batting:"`/`"Bowling:"` headers instead (checking bowling headers
     too, since a few of these older matches only ever recorded one team's
     batting card).
   - Once matches were split correctly, `Scorecard.get_performances()`
     (`playcricket_scorecard.py`) crashed on a *different* match with a
     `KeyError: 'innings'`: it guarded against a match with *no* batting
     and *no* bowling at all, but not the case of one team recording
     batting with the other side's bowling figures never entered (real for
     a handful of 2016 matches) — `self.bowling` then being an empty
     `DataFrame()` with no columns at all. Fixed by skipping the bowling
     (and, symmetrically, the batting) achievement loop when that side is
     empty, rather than assuming both are non-empty whenever either is.
   - Building the Ian Wade career-record query above also surfaced that
     the full archive's greater variety of scorers means `"I Wade"` and
     `"Ian Wade"` now both exist as separate `crichq_pdf` player identities
     — a `PLAYER_MERGES` gap, not a parser bug; see Basic usage step 6 and
     roadmap item 4.

   Earlier, against the old single-season file, this item also found and
   fixed a latent bug in
   `sqlite_store.py`'s value-cleaning helpers: Play-Cricket's raw JSON
   always uses `""` for a missing fielder/bowler, so pandas never
   introduced `NaN` there, but a Python `None` (used by the new PDF
   parser) gets upgraded to float `NaN` by pandas whenever it shares a
   column with strings — which the old `value in (None, "")` checks
   couldn't catch, since `NaN` compares unequal to everything, including
   itself. Fixed once, centrally, so any future source hits the same
   safety net. Two more identity bugs turned up while building the Ian
   Wade career-record query and are fixed too: (a) the same
   pandas-NaN-coercion trap also turns a *present* whole-number
   Play-Cricket id into `"6216362.0"` instead of `"6216362"` whenever that
   id's column has a missing value on any other row — silently splitting
   one real Play-Cricket player into two canonical players; `_clean_text()`
   now normalises whole-number floats back to plain integers; (b) CricHQ's
   `"run out (A/B)"` two-fielder credit was being stored as one bogus
   compound player named `"A/B"` — now credits the first-named fielder only
   (matching Play-Cricket's own one-fielder-per-dismissal data model) and
   correctly adds them to the team sheet.
3. **CricketStatz `.csd` ingestion** — ***Done.*** `.csd` itself is a
   proprietary multi-table binary flat-file (no dBase/Paradox/SQLite
   header, no public documentation) written by a VB6 desktop app
   (CricketStatz, Red Axe Pty Ltd). Reverse-engineering that binary
   format byte-by-byte directly was the original plan (see git history
   for the partial player-table mapping that work reached) — but turned
   out to be unnecessary and has been **abandoned**: the app itself has a
   **File → Export/Email Matches** feature that writes `.MXP`, a
   plain, fully documented `Key=Value` text format (`cricketstatz/MXP
   Format.doc`), which is what's actually ingested. `mxp_parser.py` parses
   `.MXP` into the same internal shape `Scorecard` expects, exactly like
   `crichq_pdf.py` does for CricHQ PDFs — see "Modules" above for what
   it does and does not model (the `fow`/`fowpos` fields turned out not
   to be trustworthy fall-of-wickets data — verified, not assumed).

   Validated end to end against the club's complete real archive
   (`cricketstatz/ELPM2018_all_matches.mxp`, 304 matches, 2005-04-23 to
   2018-07-21): zero foreign-key violations, and batting/bowling figures
   for the bundled Bodyline Test demo data match real cricket history
   exactly (Larwood 5/96, McCabe's 187\*, all five 1932-33 Test results).

   Getting the export required reverse-engineering-adjacent detective
   work more than binary parsing, worth keeping a note of in case
   another `.csd` ever turns up: the CricketStatz `.exe` installers
   (`cstatz05.exe`/`cstatz10.exe`/`cricketstatz11.exe` — since removed
   from the repo, no longer needed once their `.MXP` exports were
   captured) ran under Wine (wine32/wine64 + a Wine virtual desktop —
   needed for the custom-drawn VB6 popups/menus to render at all;
   without one they paint solid black), registered with a purchased
   club-wide license, opening each `.csd` backup in turn and using File →
   Export/Email Matches. `cricketstatz/ELPM2018.csd` specifically needed
   `cricketstatz11.exe` (build 11.2.49) — CricketStatz refuses to open a
   file newer than the installed version, and its version tag
   (`"11  4\0"`, format version **11**) was newer than the first installer
   tried (10.5.1, format version 10-era). Registering v11 with the same
   code that worked for v10 failed ("still unregistered" — may need a
   v11-specific code), but that turned out not to matter: opening and
   exporting existing data works fine in trial mode; the 10-match limit
   only blocks *entering new* matches. The v11 installer's own
   version-detection dialog (uninstalling 10.5.1 first) also isn't
   always raised above the main window — easy to mistake for a hang.
4. **Reconciliation layer** — *Automatic exact/near-exact matching now done
   for clubs and teams (`SQLiteStore._upsert_club()`/`._upsert_team()`);
   manual, human-confirmed matching done for all three of players/clubs/
   teams (`reconcile.py`); automatic matching for players, and full
   automatic matching for the harder club/team cases, still not built* —
   see below for what "harder" means here and why it's handled by a review
   step rather than guessed at. Full automatic matching across every
   player/club/team remains the hard part in general (initials-only names,
   no stable id across sources — see "Not built yet") and isn't attempted
   for players at all. What exists instead is a small, real mechanism (now
   duplicated by two independently-built tools for players, see "Not built
   yet"): repoint a list of confirmed `(source, source_player_id)` refs —
   already each resolving to their own canonical player from ingestion —
   onto one surviving `player_id`, updating every fact-table column that
   references it (`batting_innings.player_id`/`bowler_player_id`/
   `fielder_player_id`, `bowling_innings.player_id`,
   `match_appearances.player_id`) and `player_source_ids` itself, then
   drops the now-unreferenced duplicate rows. `reconcile.py` generalises
   this same repoint into `merge_clubs()`/`merge_teams()` too, for whatever
   club/team splits the automatic merge below doesn't safely catch.

   **Clubs and teams get an automatic merge where players don't**, because
   a club/team roster is a much smaller, much less ambiguous namespace than
   player names: `_upsert_club()` now dedups on a casefolded, whitespace-
   collapsed, "CC"/"Cricket Club"-suffix-stripped name (catching e.g.
   Play-Cricket's "East Lancs Paper Mill CC" and CricHQ's "East Lancs Paper
   Mill"), and `_upsert_team()` does the same scoped to the already-resolved
   club. Rebuilding the three-source archive from scratch with this in
   place took clubs from 164 rows down to 103 (against the demo-scale
   Play-Cricket data this was developed against; **107** against the full
   archive at the time, 933 matches then, three sources — see the
   milestone note at the top of this README for the current, larger
   figure) and fixed **East Lancs Paper Mill CC itself** — the club this whole
   project is about — being split in two. Deliberately conservative (no
   fuzzy matching): a first version tried
   during development also treated similar-looking or one-substring-of-
   another club/team names as matches, and that produced real false
   positives — "Shaw CC" / "Bradshaw CC" / "Walshaw CC" (three different
   real clubs, short names that are substrings of each other) and
   "Prestwich 2nd XI" / "Prestwich 3rd XI" (different teams; only their
   ordinal differs) both got wrongly suggested as the same thing. Anything
   past exact/near-exact is instead surfaced by `reconcile_audit.py` (see
   "Modules") as a candidate for a human to confirm via `CLUB_MERGES`/
   `TEAM_MERGES`, never merged automatically.

   Running `reconcile_audit.py` against the full archive at the time (933
   matches, three sources) — Play-Cricket included via the real `playcricket_24_25_26.json`
   cache rather than the smaller demo file (see `reconcile/data_quality_report.md`,
   committed as a live example) — found, among other things: 9 remaining
   club splits automatic merging didn't catch (all a dropped regional
   qualifier, e.g. Play-Cricket's "Bradshaw CC, Lancs" vs CricHQ's
   "Bradshaw CC"), 56 team splits (one source naming East Lancs Paper
   Mill's sides "1st XI"/"2nd XI", another "ELPM 1st XI"/"ELPM 2nd XI", and
   many opposition clubs' teams named with a club abbreviation prefix in
   one source but not another), a genuine data gap hiding in plain sight
   (`ground_name` "Add New Ground" — a leaked UI placeholder — on **47**
   matches, not the 1 it showed against the smaller sample; mostly 2024's
   GMCL Division 4/5 league fixtures, common enough now that it no longer
   surfaces near the top of the report's rarest-first Grounds table the way
   a true one-off would), and — directly relevant to this item's own Ian
   Wade example below — that his merge group is still incomplete:
   `"IW wade"` (48 games) and `"Ian Wade"` (4 games) are both separate,
   unmerged `crichq_pdf` identities alongside the `"I Wade"` ref
   `PLAYER_MERGES` already covers. None of this is applied automatically;
   it's each a line in the report for a human to confirm or reject.

   No query-layer changes were needed to prove this out: `career_stats()`
   already aggregates purely by `player_id`, so once a merge lands, a
   genuinely cross-source career total just falls out of the existing
   query. Proved against **Ian Wade**: merging his Play-Cricket id, CricHQ
   PDF name, and one CricketStatz id produced one combined career.
   Originally, against the old single-season `ELPM 1st XI 2019.pdf`, that
   was **151 games, 3895 runs at 31.7 (18 fifties, 7 hundreds), 107 wickets
   at 15.9 (7 five-fors), 63 catches** — spanning 2005-2018 (cricketstatz,
   138 matches), one 2019 match (crichq_pdf), and the 2026 season
   (play_cricket, 12 matches). Now that item 2's crash is fixed and the full
   seven-season `crichq/ALL_CRICHQ_SCORECARDS.pdf` archive ingests, the same
   merge (still just the `"I Wade"` ref) gives **195 games, 4900 runs at
   30.2 (20 fifties, 9 hundreds), 151 wickets at 14.7 (8 five-fors), 85
   catches** against the `demo.sqlite` build Basic usage step 6 walks
   through (CricHQ + CricketStatz + the small, single-season Play-Cricket
   demo file) — including the two more unmerged `crichq_pdf` identities
   (`"IW wade"`, `"Ian Wade"`) that surfaced along the way. Against the real,
   full archive (`playcricket/playcricket_24_25_26.json` in place of the
   demo file — see the milestone note at the top of this README), the same
   merge instead gives **213 games, 5199 runs at 29.9 (22 fifties, 9
   hundreds), 151 wickets at 14.8 (8 five-fors), 97 catches** — the extra
   Play-Cricket seasons (2024-2025, beyond the single 2026 season the demo
   file has) add real games, runs, and catches; the wickets tally happens
   to land on the same 151 either way, coincidentally, not because he
   didn't bowl in those extra matches (bowling innings did rise, 89 to 91).
   Zero foreign-key
   violations after merging either way — the mechanism itself is unaffected
   by any of this.

   A second `cricketstatz` ref (id `1062`, a single-match "I Wade" playing
   for the opposition, Swinton Moorside) was originally included in this
   group too — assumed to be the same player re-entered under a second
   internal id, since there was no independent record under that id to
   check the assumption against. **Confirmed wrong and removed**: it's his
   father, a different real person who happens to share the name and
   played for a different club — caught only once `reconcile_audit.py`'s
   club-exclusivity check (see below) flagged that this "Ian Wade" had an
   appearance for a second club at all, which prompted asking rather than
   assuming. A reminder that "no contradicting evidence" isn't the same as
   "confirmed," even for a single-match ref that looks like the obvious
   explanation.

   Two real data-quality issues turned up along the way, both worth
   recording:
     - **A genuine bug, fixed**: Play-Cricket's own numeric player ids
       were splitting into two canonical rows for the same person
       (`"6216362"` vs `"6216362.0"`) — see item 2 above; the same fix.
     - **A parser edge case**: CricHQ's joint run-out credit
       (`"run out (I Wade/MR Robinson)"`) was originally kept as one
       combined fielder name rather than split between the two players —
       see item 2's fix (b). At the time `reconcile.py`'s Ian Wade merge
       group was built, that fix didn't exist yet, so the compound-name
       row was deliberately left out of the merge rather than
       misattributing MR Robinson's share of the credit to Wade; now that
       the full CricHQ archive ingests cleanly (item 2), this is worth
       revisiting — not yet done.
     - **A newly-surfaced gap, not yet fixed**: with the full seven-season
       archive loaded, `"I Wade"`, `"IW wade"`, and `"Ian Wade"` now exist as
       three separate `crichq_pdf` player identities (see Basic usage step 6
       and `reconcile_audit.py`'s report) — the same no-stable-id
       name-matching problem this item's merge mechanism was built for,
       just occurring *within* one source rather than across sources, since
       a bigger archive has more scorers spelling the same player's name
       differently. `PLAYER_MERGES` only lists the abbreviated `"I Wade"`
       ref today; the other two (48 and 4 games respectively) aren't merged
       in.
   Also see "**ELPMCC Millers**" under "Not built yet" — the T20 side, not
   yet checked for equal treatment once more sources bring it in.
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
