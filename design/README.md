# ELPMCC design templates

Working area for roadmap items 6 and 7 (see repo root `README.md`
"Roadmap"): printable/frameable scorecard exports and social-media
match/performance summaries, built as data-driven HTML/CSS templates
rather than static InDesign files — they render straight from the
SQLite store, so a template never goes stale the way a hand-filled
InDesign document would, and no InDesign licence is needed to update
one. (A true `.indd`/`.idml` template is still an option later for a
designer who wants full manual print control — see "Alternatives
considered" below.)

## Contents

- `palette.md` / `palette.json` / `elpmcc.css` — the 7-colour ELPMCC
  brand palette extracted from `ELPM_Website_Colours_2025.pdf`.
- `assets/` — club crest and other brand assets. **Currently empty** —
  the crest was shared inline in chat rather than as an attachable
  file; re-upload it as a PNG or (ideally) SVG and it belongs here as
  `assets/elpmcc_logo.png` / `.svg`. Every template below draws a
  CSS placeholder shield in its place until then.
- `templates/` — the three Jinja2/HTML templates, one per roadmap
  concept:
  - `scorecard_poster.html` — A4 portrait, for printing/framing a
    single memorable match's full scorecard.
  - `career_stats.html` — A4 portrait, one player's career record
    (batting/bowling/fielding summary + milestone list).
  - `social_card.html` — 1080×1080 square, for a match result or
    "performances of the week" social post.
- `scripts/render.py` — renders the templates to PNG/PDF via
  Playwright + Jinja2. Run as-is for a demo (see below); a real
  pipeline would build the same context dicts from `sqlite_queries.py`
  / `playcricket_scorecard.py` output instead of the hardcoded
  `demo_*()` functions.
- `previews/` — rendered demo output (committed so the look is visible
  without re-running anything).

## The three demo pieces

All three use **real figures** pulled from a locally-built SQLite
store (Play-Cricket 2024-26 + the CricketStatz 2005-18 archive + the
one digitised scorebook match — see repo root `README.md` "Basic
usage" for how to build one; CricHQ wasn't ingestable in this
environment, so these are a partial rebuild, not final reconciled
numbers):

1. **Scorecard poster** — East Lancs Paper Mill CC v Failsworth
   Macedonia CC, 11 Jul 2010: won by 236 runs, Gavin Greaves 170 and
   Ian Wade 163 in a 339-run 3rd-wicket stand (the match already
   flagged in the root README as the first scorebook-digitisation
   result).
2. **Career stats** — Ian Wade, merged across his Play-Cricket,
   CricketStatz and scorebook identities per
   `reconcile/decisions.yaml`'s confirmed entry.
3. **Social card** — East Lancs Paper Mill 1st XI beat Heywood CC by
   8 wickets, 30 Aug 2025: Louis Birmingham 5-35, Ian Wade 43* (21).

## Rendering

```bash
pip install jinja2 playwright   # playwright browsers already present at
                                 # /opt/pw-browsers in this environment
python3 design/scripts/render.py            # all three
python3 design/scripts/render.py --only career
```

Outputs land in `design/previews/`. The A4 templates produce both a
print-ready PDF and a PNG preview; the social card produces a PNG
sized for direct posting.

## Alternatives considered

- **True InDesign template (`.indd`/`.idml`)** — best print fidelity
  and hand-tunable typography, but static: it won't pull new stats
  automatically, requires an InDesign licence to edit, and can't be
  previewed here. Worth doing later for the framed-poster case
  specifically if the HTML/CSS look doesn't hold up at large print
  sizes.
- **Claude Design canvas mockups** — good for iterating on the visual
  design by hand before wiring up real data. Not used for this first
  pass since the brief was to go straight to data-driven templates;
  revisit if the HTML/CSS direction needs a from-scratch visual
  redesign rather than incremental tweaks.

## Not built yet

- Wiring `render.py`'s demo dicts up to live `sqlite_queries.py` /
  `playcricket_scorecard.py` calls (currently hand-copied from query
  output for this preview).
- Milestone-triggered generation (README roadmap item 6: "triggerable
  on milestone detection").
- The real crest asset (see `assets/` above).
- A weekend round-up variant of the social card (currently one-match
  result + top two performances; a multi-fixture round-up would need
  its own layout).
