#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
presentation_deck.py

Builds the presentation-night PowerPoint from the same award data as
presentation_awards.py -- one slide per award, with its top-5 shortlist
as a native pptx table (built from the DataFrame directly, not rendered
as an image), plus a scorecard slide wherever the shortlist's #1
candidate had a genuine milestone this season (a century/double-century
behind a batting award, a five-wicket haul behind a bowling award) --
also built as a native table, via the Scorecard class's own
batting_table()/bowling_table(), rather than a screenshot of one.

    pip install python-pptx
    python3 presentation_deck.py --sqlite-db playcricket_stats.sqlite --season 2026
    python3 presentation_deck.py --sqlite-db playcricket_stats.sqlite --season 2026 --out presentation_night_2026.pptx

Not every award has an "achievement" a milestone can be found for --
the White Boot Trophy is the ABSENCE of a good performance, so nothing
in v_bowling_achievements applies. --scorecard attaches one manually,
by match_id, for any award's #1 candidate:

    python3 presentation_deck.py --sqlite-db playcricket_stats.sqlite --season 2026 \\
        --scorecard "White Boot Trophy -- Worst Economy Rate=4231"

This is a first pass deliberately kept simple (see the module's own
commit message/PR discussion): plain native tables, no theming, no
per-award picture; a natural next step once the content itself is
signed off.
"""

import argparse
import json
import sqlite3

import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt

from playcricket_scorecard import Scorecard
from presentation_awards import build_report
from sqlite_queries import notable_performances

# award title (exact match against build_report()'s own `award` string) ->
# (discipline, achievements to look for) for automatically finding a
# milestone match for that award's #1 candidate. Awards not listed here
# (Fielding, Six Hit, Duck, Partnership, White Boot, the manual/captain's
# awards) get no automatic scorecard -- either there's no natural
# "achievement" behind them, or the milestone views wouldn't be scoring
# the right thing (a most-catches leader's afternoon isn't a batting or
# bowling achievement) -- use --scorecard for those instead.
AUTO_MILESTONE_RULES = {
    "Batting average": ("batting", ("century", "double_century")),
    "Bowling average": ("bowling", ("five_wicket_haul",)),
}

# Award titles containing these substrings (case-insensitive) default to
# a bowling scorecard for a --scorecard override with no other way to
# tell; everything else defaults to batting. Only matters for manually
# overridden awards -- AUTO_MILESTONE_RULES already states the discipline
# for the awards it covers.
BOWLING_KEYWORDS = ("bowling", "boot")

SLIDE_WIDTH_IN = 13.333
SLIDE_HEIGHT_IN = 7.5


# ==================================================================
# FORMATTING
# ==================================================================

def _format_cell(value):
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _add_title(slide, text):
    slide.shapes.title.text = text


def _add_subtitle(slide, text, top=Inches(1.15)):
    box = slide.shapes.add_textbox(Inches(0.5), top, Inches(SLIDE_WIDTH_IN - 1), Inches(0.5))
    paragraph = box.text_frame.paragraphs[0]
    run = paragraph.add_run()
    run.text = text
    run.font.italic = True
    run.font.size = Pt(16)


def _add_table(slide, data, top=Inches(1.8)):
    if data is None or data.empty:
        box = slide.shapes.add_textbox(Inches(0.5), top, Inches(SLIDE_WIDTH_IN - 1), Inches(1))
        box.text_frame.paragraphs[0].add_run().text = (
            "No qualifying candidates this season." if data is not None
            else "No stats candidates -- decided outside this database."
        )
        return

    rows, cols = data.shape
    left = Inches(0.5)
    width = Inches(SLIDE_WIDTH_IN - 1)
    height = Inches(min(5.3, 0.5 * (rows + 1)))

    table = slide.shapes.add_table(rows + 1, cols, left, top, width, height).table

    font_size = 16 if cols <= 6 else 12

    for col_idx, column_name in enumerate(data.columns):
        cell = table.cell(0, col_idx)
        cell.text = column_name.replace("_", " ").title()
        run = cell.text_frame.paragraphs[0].runs[0]
        run.font.bold = True
        run.font.size = Pt(font_size)

    for row_idx, (_, row) in enumerate(data.iterrows(), start=1):
        for col_idx, value in enumerate(row):
            cell = table.cell(row_idx, col_idx)
            cell.text = _format_cell(value)
            cell.text_frame.paragraphs[0].runs[0].font.size = Pt(font_size)


def _award_slide(prs, section, award, data, criteria):
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    _add_title(slide, f"{section} -- {award}")
    _add_subtitle(slide, criteria)
    _add_table(slide, data)
    return slide


# ==================================================================
# SCORECARD LOOKUP
# ==================================================================

def _best_performance(performances, player_name, discipline=None, achievements=None):
    """The best-qualifying row in `performances` (see
    sqlite_queries.notable_performances()) for `player_name` this season,
    optionally restricted to one discipline/achievement set. Matches by
    name rather than player_id, since the award tables above don't carry
    player_id through to their display columns -- fine within one
    season's shortlist, where a repeated exact name is vanishingly
    unlikely."""

    rows = performances[performances["player_name"] == player_name]

    if discipline is not None:
        rows = rows[rows["discipline"] == discipline]

    if achievements is not None:
        rows = rows[rows["achievement"].isin(achievements)]

    if rows.empty:
        return None

    sort_col = "wickets" if (rows["discipline"] == "bowling").all() else "value"

    return rows.sort_values(sort_col, ascending=False).iloc[0]


def _scorecard_tables(conn, match_id, player_name, discipline, scorecard_cache):
    """(innings_summary, table) for `player_name`'s batting/bowling in
    `match_id` -- the batting_table()/bowling_table() for whichever
    innings they appear in, found by name since Scorecard's own ids are
    the source's raw ids, not this database's player_id (see
    _best_performance()'s docstring for the same reasoning)."""

    if match_id not in scorecard_cache:
        source_payload = conn.execute(
            "SELECT source_payload FROM matches WHERE match_id = ?", (match_id,)
        ).fetchone()[0]
        scorecard_cache[match_id] = Scorecard(json.loads(source_payload))

    scorecard = scorecard_cache[match_id]

    if discipline == "batting":
        raw, name_col, table_fn = scorecard.batting, "batsman_name", scorecard.batting_table
    else:
        raw, name_col, table_fn = scorecard.bowling, "bowler_name", scorecard.bowling_table

    if raw.empty:
        return None, None

    matches = raw[raw[name_col].astype(str).str.strip().str.lower() == player_name.strip().lower()]

    if matches.empty:
        return None, None

    innings_number = matches.iloc[0]["innings"]
    summary = scorecard.innings_summary(innings_number).iloc[0]

    table = table_fn(innings_number)
    id_column = "batsman_id" if discipline == "batting" else "bowler_id"
    table = table.drop(columns=[id_column], errors="ignore")

    return summary, table


def _scorecard_slide(prs, conn, match_id, player_name, discipline, headline, scorecard_cache):
    summary, table = _scorecard_tables(conn, match_id, player_name, discipline, scorecard_cache)

    slide = prs.slides.add_slide(prs.slide_layouts[5])
    _add_title(slide, headline)

    if summary is None:
        _add_subtitle(slide, f"Could not locate {player_name} in match {match_id}'s scorecard.")
        return slide

    _add_subtitle(slide, f"{summary['team']} {summary['runs']}/{summary['wickets']} ({summary['overs']} overs)")
    _add_table(slide, table)

    return slide


# ==================================================================
# DECK
# ==================================================================

def build_deck(conn, season, scorecard_overrides=None):
    scorecard_overrides = scorecard_overrides or {}

    prs = Presentation()
    prs.slide_width = Inches(SLIDE_WIDTH_IN)
    prs.slide_height = Inches(SLIDE_HEIGHT_IN)

    title_slide = prs.slides.add_slide(prs.slide_layouts[0])
    title_slide.shapes.title.text = f"Presentation Evening {season}"

    report = build_report(conn, season)
    performances = notable_performances(conn, season=season)
    scorecard_cache = {}

    for section, award, data, criteria in report:

        _award_slide(prs, section, award, data, criteria)

        if data is None or data.empty or "player_name" not in data.columns:
            # Partnership's shortlist is two players, not one -- there's
            # no single "top candidate" name to attach a scorecard to.
            continue

        top_candidate = data.iloc[0]
        player_name = top_candidate["player_name"]

        if award in scorecard_overrides:
            match_id = scorecard_overrides[award]
            discipline = "bowling" if any(k in award.lower() for k in BOWLING_KEYWORDS) else "batting"
            headline = f"{award} -- {player_name} (match {match_id})"
            _scorecard_slide(prs, conn, match_id, player_name, discipline, headline, scorecard_cache)
            continue

        if award in AUTO_MILESTONE_RULES:
            discipline, achievements = AUTO_MILESTONE_RULES[award]
            best = _best_performance(performances, player_name, discipline, achievements)
        elif award == "Secretary's Cup":
            best = _best_performance(performances, player_name)
        else:
            best = None

        if best is None:
            continue

        headline = f"{best['achievement'].replace('_', ' ').title()}: {player_name} vs {best['opposition']}"
        _scorecard_slide(
            prs, conn, int(best["match_id"]), player_name,
            best["discipline"], headline, scorecard_cache
        )

    return prs


def _parse_scorecard_override(value):
    award, _, match_id = value.rpartition("=")
    if not award or not match_id.strip().lstrip("-").isdigit():
        raise argparse.ArgumentTypeError(
            f"--scorecard expects 'AWARD TITLE=MATCH_ID', got: {value!r}"
        )
    return award, int(match_id)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Build the presentation-night PowerPoint from presentation_awards.py's award data."
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument(
        "--scorecard", action="append", default=[], type=_parse_scorecard_override,
        metavar="AWARD TITLE=MATCH_ID",
        help=(
            "Attach a specific match's scorecard to an award's slide (its #1 "
            "candidate), overriding auto-detection -- repeatable. Award title "
            "must match exactly, e.g. \"White Boot Trophy -- Worst Economy Rate=4231\"."
        )
    )

    args = parser.parse_args()

    conn = sqlite3.connect(args.sqlite_db)

    deck = build_deck(conn, args.season, scorecard_overrides=dict(args.scorecard))

    conn.close()

    out_path = args.out or f"presentation_night_{args.season}.pptx"
    deck.save(out_path)
    print(f"Wrote {out_path}")
