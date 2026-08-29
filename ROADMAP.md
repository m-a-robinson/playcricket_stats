# Roadmap and outstanding issues

Planned work and known gaps for `playcricket_stats`, split out of the main
[README](README.md) to keep that file focused on how to use the project
today. See [development_notes.md](development_notes.md) for the detailed
history behind the items marked *Done* below.

## Contents

- [Not built yet](#not-built-yet)
- [Roadmap](#roadmap)

## Not built yet

- **Automatic** reconciliation/merge logic across the sources for the
  *harder* cases (conflict resolution, and player/club/team identity
  matching beyond exact/near-exact names). Clubs and teams now get an
  automatic merge for the exact/near-exact case at insert time
  (`SQLiteStore._upsert_club()`/`._upsert_team()` — e.g. "East Lancs Paper
  Mill CC" no longer splits into a separate `club_id` per source the way it
  used to), and `reconcile.py`/`reconcile_audit.py` (see development_notes.md's
  "Modules" section) cover the fuzzier remainder for clubs/teams and everything for players —
  but only for groups a human has confirmed via `reconcile/decisions.yaml`;
  finding those groups with no human in the
  loop at all isn't built, and isn't attempted for players (see
  `reconcile_audit.py`'s module notes for why a bare similarity/containment
  check turned out to be actively unreliable even for clubs/teams, let alone
  names). Deliberately deferred to a review step across all sources
  rather than guessed at during ingestion (see the "MR Robinson" /
  seven-Robinsons example this was scoped against).
- **Two manual player-merge tools that overlap and need reconciling with
  each other**: `SQLiteStore.find_players()`/`.merge_players()` (pairwise)
  and `reconcile.py`'s `merge_players()`/`reconcile/decisions.yaml` (registry-driven),
  built independently, doing the same underlying repoint. Pick one as
  canonical and retire the other — a housekeeping item, not yet done.
- The **2010-2013 season blackout** (see development_notes.md's "Milestone"
  section) is now
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
- `nmcl_season_stats` blending into `career_stats()`/leaderboards is now
  built (`include_nmcl=True`, see the README's "Using the main database"
  and "Using the example files" sections) for the figures that stay valid
  when summed with real match data (runs, times dismissed, highest score,
  wickets, runs conceded, catches, and the averages recomputed from those).
  What's still not attempted: anything that needs innings/match granularity
  a season aggregate doesn't have (balls-faced/strike-rate, fielding beyond
  keeping, distinguishing a not-out top score from one that just wasn't
  beaten).
- Formatted scorecard export (image/PDF) for printing or framing.
- Social-media formatting for player performances and weekend results.
- Any CLI/UI entry point — everything today is a library, including the
  Play-Cricket sync itself (`playcricket_api.py`/`playcricket_database.py`
  have no `__main__` — see the README's "Using the main database" section for the
  snippet a `sync_playcricket.py` wrapper would replace).
- **Four data-quality issues found reviewing sample scorecards across all
  three original sources (2026-08-27), each a naming/reference-data problem rather
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
    item 4/step 7); resolved the normal way, via a merge entry in
    `reconcile/decisions.yaml`, not a parser change.
  - **CricketStatz's bare `"Division 1"`/`"Division 2"`/`"Division 3"`/
    `"Cup"` competition names (2005-2015, 223 matches) are missing an
    `NMCL` league prefix** — the club played in the NMCL (North Manchester
    Cricket League — see `nmcl stats/*.tif` in development_notes.md, the pre-CricketStatz
    paper archive from the same era) before moving to the GMCL, and the
    year ranges confirm the split cleanly: every bare `"Division N"`/
    `"Cup"` name falls in 2005-2015, while `"GMCL Division N"`-prefixed
    names only start in 2016. The exact cutover year isn't in the data
    itself, so renaming these needs the club's own confirmation of when
    the move happened before `competition_name` values can be corrected
    (by hand, or a small date-gated rename pass once confirmed).

## Roadmap

1. **Data foundation** — *Done, and now proven against every original
   source at once* (see development_notes.md's "Milestone" section:
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
   `PlayCricketDatabase` — see development_notes.md's "Retired" section).
   Two separate manual
   reconciliation paths now exist — `SQLiteStore.find_players()`/
   `.merge_players()` and `reconcile.py`'s `merge_players()`/
   `reconcile/decisions.yaml` (see development_notes.md's "Modules" section) —
   both used to unify Ian Wade's
   Play-Cricket, CricHQ, and CricketStatz identities into one career
   record (see the README's "Using the example files" section, step 6). Still to do: reconcile the two tools
   with each other (see "Not built yet" above), and an automatic reconciliation
   pass — neither manual tool scales to every player across many more
   CricHQ PDFs on its own.
2. **CricHQ PDF ingestion** — ***Done***, including on the club's full
   six-season-turned-seven-season archive — see development_notes.md's "Sample data" section for the
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
   - Building the Ian Wade career-record query also surfaced that
     the full archive's greater variety of scorers means `"I Wade"` and
     `"Ian Wade"` now both exist as separate `crichq_pdf` player identities
     — a `reconcile/decisions.yaml` gap, not a parser bug; see the README's
     "Using the example files" section, step 6, and roadmap item 4 below.

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
   `crichq_pdf.py` does for CricHQ PDFs — see development_notes.md's "Modules" section for what
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
   see "Not built yet" above for what "harder" means here and why it's
   handled by a review step rather than guessed at. Full automatic matching
   across every player/club/team remains the hard part in general
   (initials-only names, no stable id across sources — see "Not built
   yet") and isn't attempted for players at all. What exists instead is a
   small, real mechanism (now duplicated by two independently-built tools
   for players, see "Not built yet"): repoint a list of confirmed
   `(source, source_player_id)` refs — already each resolving to their own
   canonical player from ingestion — onto one surviving `player_id`,
   updating every fact-table column that references it
   (`batting_innings.player_id`/`bowler_player_id`/`fielder_player_id`,
   `bowling_innings.player_id`, `match_appearances.player_id`) and
   `player_source_ids` itself, then drops the now-unreferenced duplicate
   rows. `reconcile.py` generalises this same repoint into
   `merge_clubs()`/`merge_teams()` too, for whatever club/team splits the
   automatic merge below doesn't safely catch.

   **Clubs and teams get an automatic merge where players don't**, because
   a club/team roster is a much smaller, much less ambiguous namespace than
   player names: `_upsert_club()` now dedups on a casefolded, whitespace-
   collapsed, "CC"/"Cricket Club"-suffix-stripped name (catching e.g.
   Play-Cricket's "East Lancs Paper Mill CC" and CricHQ's "East Lancs Paper
   Mill"), and `_upsert_team()` does the same scoped to the already-resolved
   club. Rebuilding the three-source archive from scratch with this in
   place took clubs from 164 rows down to 103 (against the demo-scale
   Play-Cricket data this was developed against; **107** against the full
   archive at the time, 933 matches then, three sources — see
   development_notes.md's "Milestone" section for the current, larger
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
   development_notes.md's "Modules" section) as a candidate for a human to
   confirm via `reconcile/decisions.yaml`, never merged automatically.

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
   unmerged `crichq_pdf` identities alongside the `"I Wade"` ref already
   merged. None of this is applied automatically;
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
   catches** against the demo-scale build the README's "Using the example
   files" section, step 6, walks
   through (CricHQ + CricketStatz + the small, single-season Play-Cricket
   demo file) — including the two more unmerged `crichq_pdf` identities
   (`"IW wade"`, `"Ian Wade"`) that surfaced along the way. Against the real,
   full archive (`playcricket/playcricket_24_25_26.json` in place of the
   demo file — see development_notes.md's "Milestone" section), the same
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
       see item 2's fix (b). At the time the Ian Wade merge group was
       first built, that fix didn't exist yet, so the compound-name
       row was deliberately left out of the merge rather than
       misattributing MR Robinson's share of the credit to Wade; now that
       the full CricHQ archive ingests cleanly (item 2), this is worth
       revisiting — not yet done.
     - **A newly-surfaced gap, not yet fixed**: with the full seven-season
       archive loaded, `"I Wade"`, `"IW wade"`, and `"Ian Wade"` now exist as
       three separate `crichq_pdf` player identities (see the README's
       "Using the example files" section, step 6, and
       `reconcile_audit.py`'s report) — the same no-stable-id
       name-matching problem this item's merge mechanism was built for,
       just occurring *within* one source rather than across sources, since
       a bigger archive has more scorers spelling the same player's name
       differently. Only the abbreviated `"I Wade"` ref is merged in today;
       the other two (48 and 4 games respectively) aren't merged
       in.
   The T20 side (`East Lancs Millers`) is confirmed to get equal treatment
   here too, not second-class status as an afterthought — see
   `sqlite_queries.py`'s bullet in development_notes.md's "Modules" section
   for the `team_id` filtering check.
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
