#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
crichq_pdf.py

Parses CricHQ "Full Scorecard Report" PDF exports (one PDF typically
covers a whole team's whole season, with every match's scorecard
concatenated across pages) into the same match-detail shape used by
Scorecard / sqlite_store.py, so they can be ingested through
SQLiteStore.insert_match() exactly like Play-Cricket data.

Architecture
------------

    CricHQ PDF
          |
          v
    parse_pdf()             <- this module
          |
          v
    Scorecard (unchanged)
          |
          v
    SQLiteStore.insert_match(source="crichq_pdf")

Identity
--------
CricHQ PDFs carry no numeric ids for clubs, teams, matches, or players
-- only names and dismissal text. This module manufactures stable
TEXT ids from those names (e.g. a team's source_team_id is its literal
"Club Name, Nth XI" string) so that re-parsing the same PDF is
idempotent, and so schema.sql's club_source_ids/team_source_ids/
player_source_ids mapping tables can resolve them the same way they
resolve Play-Cricket's numeric ids.

Per the project's current approach, player identity is deliberately
NOT matched against existing players here: every distinct name in a
PDF becomes its own new canonical player. Reconciling CricHQ names
against Play-Cricket/CricketStatz players (e.g. "MR Robinson" vs one
of several "... Robinson"s already in the database) is a separate,
later pass across all three sources -- see the README roadmap.
"""

import re
from datetime import datetime

from pypdf import PdfReader


# ==================================================================
# TEXT EXTRACTION
# ==================================================================

def _extract_text(pdf_path):
    """
    Extract all text from the PDF as one string, with page-footer
    "p.N" lines removed. Page boundaries are NOT preserved as markers
    -- a match's scorecard can and does span a page break mid-table,
    so downstream parsing works on the whole concatenated text.
    """

    reader = PdfReader(pdf_path)
    lines = []

    for page in reader.pages:

        text = page.extract_text() or ""

        for line in text.split("\n"):

            if re.fullmatch(r"p\.\d+", line.strip()):
                continue

            lines.append(line)

    return "\n".join(lines)


# ==================================================================
# REGEX PATTERNS
# ==================================================================

# The "home vs away" line and the Date/Venue line layout both vary
# across the report generator versions concatenated into the combined
# archive PDF: most matches have "<home> vs <away>" immediately before
# a single "Date: X Venue: Y" line, but an older report layout (seen
# in the 2016 season pages) omits the "vs" line entirely and puts
# "Date: X" and "Venue: Y ... Match Type: ..." on separate lines.
# Both groups are matched loosely here so every match still gets its
# own header -- see _parse_match()'s team-name fallback for the
# "vs" line being absent.
MATCH_HEADER = re.compile(
    r'^(?P<competition>.+)\n'
    r'(?:(?P<home>.+?) vs (?P<away>.+?)\n)?'
    r'Date: (?P<datetext>.+?)\s+Venue: (?P<venue>.+?)(?:\s+Match Type:.*)?$',
    re.MULTILINE
)

MATCH_TYPE_LINE = re.compile(
    r'Match Type:\s*(?P<overs>\d+)\s*Over'
)

TOSS_LINE = re.compile(
    r'^Toss Details:\s*(?P<winner>.*)$',
    re.MULTILINE
)

RESULT_LINE = re.compile(
    r'^(?P<team>.+?) - (?P<margin>Won by .+|Won \(D/L method\)|Match Tied|Match Drawn)$',
    re.MULTILINE
)

# Rare alternative to RESULT_LINE seen on administratively-decided matches
# (e.g. a walkover) -- no "<team> - Won ..." summary line at all, just
# "<team> Game(s) Awarded as Win"/"...as Loss" sentences for both sides.
AWARDED_WIN_LINE = re.compile(
    r'^(?P<team>.+?) Games? Awarded as Win\.',
    re.MULTILINE
)

INNINGS_HEADER = re.compile(
    r"Batting:\s+(?P<team>.+?)\s+(?P<ordinal>1st|2nd)\s*\n?Innings"
)

BOWLING_HEADER = re.compile(
    r"Bowling:\s+(?P<team>.+?)\s+O\s+M\s+R\s+W\s+EC\s+AV\s+EX"
)

BATTING_ROW = re.compile(
    r"^(?P<rest>.+?)\s+(?P<runs>\d+)\s+(?P<balls>\d+)\s+(?P<fours>\d+)\s+"
    r"(?P<sixes>\d+)\s+(?P<sr>[\d.]+|-)\s*$"
)

BOWLING_ROW = re.compile(
    r"^(?P<name>.+?)\s+(?P<overs>\d+\.\d)\s+(?P<maidens>\d+)\s+(?P<runs>\d+)\s+"
    r"(?P<wickets>\d+)\s+(?P<economy>[\d.]+)\s+(?P<average>[\d.]+|-)\s*"
    r"(?:\((?P<extras>[^)]*)\))?\s*$"
)

EXTRAS_LINE = re.compile(
    r"^Extras\s*(?:\((?P<detail>[^)]*)\))?\s+(?P<total>\d+)\s*$"
)

TOTALS_LINE = re.compile(
    r"^Totals\s+(?P<runs>\d+)(?:\s+(?P<rpo>[\d.]+)\s*RPO)?\s*$"
)

DID_NOT_BAT = re.compile(
    r"^Did not bat:\s*(?P<names>.*)$"
)

NAME_SUFFIX = re.compile(r"\s*\([^)]*\)")

SKIP_LINES = {"R B 4's 6's SR", "Match Notes"}

_DISMISSAL_KEYWORDS = {
    "not", "did", "b", "c", "lbw", "lbw.", "st", "run", "retired", "hit"
}

_MONTHS = {
    m: i for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        start=1
    )
}


# ==================================================================
# ROW MERGING (handles rows wrapped across lines by PDF layout)
# ==================================================================

def _parse_rows(text_block, row_regex, terminators):
    """
    Iterate lines, merging consecutive lines together until the joined
    text matches row_regex -- this absorbs mid-row line wraps (e.g. a
    long "(Os Pro)" name suffix pushed onto its own line). Stops at a
    terminator line (section boundary). A line that never joins into a
    match is treated as a trailing note and dropped.
    """

    rows = []
    buffer = []
    started = False

    for raw_line in text_block.split("\n"):

        line = raw_line.strip()

        if not line or line in SKIP_LINES:
            continue

        if any(line.startswith(t) for t in terminators):
            break

        buffer.append(line)
        joined = " ".join(buffer)
        match = row_regex.match(joined)

        if match:
            rows.append(match)
            buffer = []
            started = True

        elif started and len(buffer) == 1:
            buffer = []

    return rows


# ==================================================================
# NAME / DISMISSAL PARSING
# ==================================================================

def _clean_name(raw):
    """
    Strip role markers from a raw CricHQ name and return
    (clean_name, captain, wicket_keeper).

    "MR Robinson†"    -> ("MR Robinson", False, True)
    "APJ Sajewicz**"  -> ("APJ Sajewicz", True, False)
    "M Smalley (Pro)" -> ("M Smalley", False, False)

    A parenthetical suffix like "(Pro)" / "(Os Pro)" / "(OA)" marks a
    professional/overseas player. It's stripped rather than modelled
    -- there's no schema column for it and it can vary match to match.
    """

    wicket_keeper = "†" in raw
    captain = "*" in raw

    name = raw.replace("†", "")
    name = NAME_SUFFIX.sub("", name)
    name = name.replace("*", "")
    name = re.sub(r"\s+", " ", name).strip()

    return name, captain, wicket_keeper


def _split_dismissal(rest):
    """
    'name-with-markers dismissal-text' -> (name, dismissal_text).

    The first token is always part of the name (initials or a first
    name), so scanning for the dismissal keyword starts at index 1 --
    otherwise a single-letter surname like "B Birtwistle" collides
    with the "b" (bowled) keyword.
    """

    tokens = rest.split(" ")

    for i, tok in enumerate(tokens):

        if i == 0:
            continue

        if tok.lower() in _DISMISSAL_KEYWORDS:

            name = " ".join(tokens[:i]).strip()
            dismissal = " ".join(tokens[i:]).strip()

            return name, dismissal

    return rest.strip(), "not out"


def _parse_dismissal(dismissal_text):
    """
    Turn CricHQ dismissal text into (how_out, bowler_name, fielder_name),
    using the same how_out vocabulary Play-Cricket/Scorecard expect:
    "not out", "retired not out", "ct", "b", "lbw", "st", "run out",
    "hit wicket".
    """

    text = dismissal_text.strip()
    low = text.lower()

    if low == "not out":
        return "not out", None, None

    if low.startswith("retired"):

        # CricHQ's own vocabulary distinguishes "retired hurt" (not out --
        # standard scoring convention), "retired out" (a genuine dismissal
        # -- the fielding side declined the return, or the scorer marked
        # it as out) and bare "retired" (a tactical not-out retirement,
        # e.g. to let a partner bat on). Collapsing all three into one
        # label previously hid a real "retired out" dismissal as a
        # not-out -- see how_out's not-out vocabulary in
        # playcricket_scorecard.py._standardise_batting().
        if low.startswith("retired hurt"):
            return "retired hurt", None, None

        if low.startswith("retired out"):
            return "retired out", None, None

        return "retired not out", None, None

    if low.startswith("c & b") or low.startswith("c and b"):
        bowler = text.split(" ", 2)[-1].strip()
        return "ct", bowler, bowler

    if low.startswith("c "):
        m = re.match(r"^c\s+(?P<fielder>.+?)\s+b\s+(?P<bowler>.+)$", text, re.IGNORECASE)
        if m:
            return "ct", m.group("bowler").strip(), m.group("fielder").strip()
        return "ct", None, text[2:].strip()

    if low.startswith("st "):
        m = re.match(r"^st\s+(?P<fielder>.+?)\s+b\s+(?P<bowler>.+)$", text, re.IGNORECASE)
        if m:
            return "st", m.group("bowler").strip(), m.group("fielder").strip()
        return "st", None, text[3:].strip()

    if low.startswith("lbw"):
        m = re.match(r"^lbw\s+b\s+(?P<bowler>.+)$", text, re.IGNORECASE)
        if m:
            return "lbw", m.group("bowler").strip(), None
        return "lbw", None, None

    if low.startswith("hit wicket"):
        m = re.match(r"^hit wicket\s+b\s+(?P<bowler>.+)$", text, re.IGNORECASE)
        if m:
            return "hit wicket", m.group("bowler").strip(), None
        return "hit wicket", None, None

    if low.startswith("run out"):
        m = re.match(r"^run out(?:\s*\((?P<fielders>.+)\))?$", text, re.IGNORECASE)
        fielders = m.group("fielders") if m else None
        # "run out (A/B)" credits a relay between two fielders. Play-Cricket's
        # own schema (and ours) only has one fielder_id per dismissal, so
        # credit the first named fielder -- the "/B" part must NOT be kept
        # as part of the name, or "A/B" becomes one bogus compound player.
        fielder = fielders.split("/")[0].strip() if fielders else None
        return "run out", None, fielder

    if low.startswith("b "):
        return "b", text[2:].strip(), None

    # Unrecognised -- keep the raw text rather than lose the row.
    return text, None, None


def _parse_extras(detail_text):
    """'w 3, nb 5, b 3, lb 1' -> dict of extra_wides/extra_no_balls/extra_byes/extra_leg_byes."""

    result = {"wides": 0, "no_balls": 0, "byes": 0, "leg_byes": 0, "penalty_runs": 0}

    if not detail_text:
        return result

    labels = {
        "w": "wides", "nb": "no_balls", "b": "byes",
        "lb": "leg_byes", "pen": "penalty_runs"
    }

    for part in detail_text.split(","):

        part = part.strip()
        m = re.match(r"^(?P<label>\w+)\s+(?P<value>\d+)$", part)

        if m and m.group("label") in labels:
            result[labels[m.group("label")]] = int(m.group("value"))

    return result


def _parse_date(datetext):
    """'Sat, 20 April, 2019' -> (dd/mm/yyyy string, season int)."""

    m = re.search(r"(?P<day>\d{1,2})\s+(?P<month>\w+),?\s+(?P<year>\d{4})", datetext)

    if not m:
        return None, None

    month_abbr = m.group("month")[:3].title()
    month = _MONTHS.get(month_abbr)

    if month is None:
        return None, None

    day = int(m.group("day"))
    year = int(m.group("year"))

    return f"{day:02d}/{month:02d}/{year}", year


def _split_team_name(full_name):
    """'East Lancs Paper Mill CC, 1st XI' -> ('East Lancs Paper Mill CC', '1st XI')."""

    if ", " in full_name:
        club, team = full_name.rsplit(", ", 1)
        return club.strip(), team.strip()

    return full_name.strip(), full_name.strip()


# ==================================================================
# ONE MATCH
# ==================================================================

def _parse_match(header_match, body, match_index):

    home_full = header_match.group("home")
    away_full = header_match.group("away")

    home_full = home_full.strip() if home_full else None
    away_full = away_full.strip() if away_full else None

    if home_full is None:

        # The header's "vs" line is missing (see MATCH_HEADER) -- recover
        # team names from the "Batting: <team>"/"Bowling: <team>" lines
        # instead, in the order they appear. Some matches from this era
        # only ever recorded one team's innings (the opposition's batting
        # card was never entered), so the *bowling* header is sometimes
        # the only place the second team's name survives.
        name_matches = sorted(
            list(INNINGS_HEADER.finditer(body))
            + list(BOWLING_HEADER.finditer(body)),
            key=lambda m: m.start()
        )

        inferred = []

        for nm in name_matches:

            name = nm.group("team").strip()

            if name not in inferred:
                inferred.append(name)

        placeholder = (
            f"Unknown ({header_match.group('competition').strip()}, "
            f"{header_match.group('datetext').strip()})"
        )

        if len(inferred) >= 2:
            home_full, away_full = inferred[0], inferred[1]

        elif len(inferred) == 1:
            home_full, away_full = inferred[0], f"{placeholder} - Opponent"

        else:
            # No batting or bowling at all either (a genuinely abandoned
            # match) -- there is no team name left anywhere in the text
            # to recover, so synthesise a stable placeholder from the
            # header fields so the match still gets an idempotent id
            # rather than being silently merged into a neighbour.
            home_full, away_full = f"{placeholder} - Team A", f"{placeholder} - Team B"

    home_club, home_team = _split_team_name(home_full)
    away_club, away_team = _split_team_name(away_full)

    match_date, season = _parse_date(header_match.group("datetext"))

    source_match_id = f"{home_full}|{away_full}|{match_date or header_match.group('datetext')}"

    overs_m = MATCH_TYPE_LINE.search(body)
    no_of_overs = int(overs_m.group("overs")) if overs_m else None

    toss_m = TOSS_LINE.search(body)
    toss_winner_text = toss_m.group("winner").strip() if toss_m else ""
    toss_won_by_team_id = home_full if toss_winner_text == home_full else (
        away_full if toss_winner_text == away_full else None
    )

    # --------------------------------------------------------------
    # Abandoned / no play
    # --------------------------------------------------------------

    if "Batting:" not in body:

        return {
            "id": source_match_id,
            "home_club_id": home_club, "home_club_name": home_club,
            "home_team_id": home_full, "home_team_name": home_team,
            "away_club_id": away_club, "away_club_name": away_club,
            "away_team_id": away_full, "away_team_name": away_team,
            "match_date": match_date,
            "match_time": None,
            "competition_id": None,
            "competition_name": header_match.group("competition").strip(),
            "competition_type": None,
            "league_id": None, "league_name": None,
            "ground_id": None, "ground_name": header_match.group("venue").strip(),
            "no_of_innings": 0,
            "no_of_overs": no_of_overs,
            "no_of_days": 1,
            "toss": toss_winner_text or None,
            "toss_won_by_team_id": toss_won_by_team_id,
            "result": None,
            "result_applied_to": None,
            "result_description": "Abandoned - No Play Possible",
            "status": "Abandoned",
            "last_updated": None,
            "players": [],
            "innings": []
        }

    # --------------------------------------------------------------
    # Result
    # --------------------------------------------------------------

    result_section = body[:body.index("Batting:")]
    result_m = RESULT_LINE.search(result_section)
    awarded_m = None if result_m else AWARDED_WIN_LINE.search(result_section)

    result = None
    result_applied_to = None
    result_description = None

    if result_m:
        result = result_m.group("margin")
        winner_text = result_m.group("team").strip()
    elif awarded_m:
        # No "<team> - Won ..." summary line for a walkover -- recover the
        # winner from the "Game(s) Awarded as Win" sentence instead.
        result = "Won (awarded)"
        winner_text = awarded_m.group("team").strip()
    else:
        winner_text = None

    if winner_text:
        result_applied_to = home_full if winner_text == home_full else (
            away_full if winner_text == away_full else None
        )

        # CricHQ's own summary line states the result from both teams'
        # perspective ("X Won. Y Lost" / "Y Lost. X Won" -- order varies)
        # -- redundant with the winner + margin already parsed above, and
        # reads as noise next to Play-Cricket's own single-team style
        # ("<team> - Won by X"). Build one winner-only sentence instead of
        # keeping both team names.
        result_description = f"{winner_text} {result}"

    # --------------------------------------------------------------
    # Innings
    # --------------------------------------------------------------

    innings_headers = list(INNINGS_HEADER.finditer(body))
    innings_list = []

    # team_name -> list of {player_name, position, captain, wicket_keeper}
    team_sheets = {home_full: {}, away_full: {}}

    def _sheet_entry(team_key, raw_name, position=None):
        name, captain, wk = _clean_name(raw_name)
        sheet = team_sheets.setdefault(team_key, {})
        entry = sheet.setdefault(name, {
            "player_name": name, "player_id": name,
            "position": position, "captain": False, "wicket_keeper": False
        })
        if position is not None and entry["position"] is None:
            entry["position"] = position
        entry["captain"] = entry["captain"] or captain
        entry["wicket_keeper"] = entry["wicket_keeper"] or wk
        return name

    for ii, ih in enumerate(innings_headers):

        i_start = ih.end()
        i_end = innings_headers[ii + 1].start() if ii + 1 < len(innings_headers) else len(body)
        innings_body = body[i_start:i_end]

        batting_team_full = ih.group("team").strip()
        bowling_team_full = away_full if batting_team_full == home_full else home_full

        bowl_h = BOWLING_HEADER.search(innings_body)
        batting_part = innings_body[:bowl_h.start()] if bowl_h else innings_body
        bowling_part = innings_body[bowl_h.end():] if bowl_h else ""

        # ---------------- Batting ----------------

        bat_rows = []
        position = 0

        for bm in _parse_rows(
            batting_part, BATTING_ROW,
            terminators=("Extras", "Totals", "Did not bat", "Fall of wicket")
        ):
            position += 1
            raw_name_and_dismissal = bm.group("rest")
            raw_name, dismissal_text = _split_dismissal(raw_name_and_dismissal)
            clean_name = _sheet_entry(batting_team_full, raw_name, position)

            how_out, bowler_name, fielder_name = _parse_dismissal(dismissal_text)

            bowler_clean = _clean_name(bowler_name)[0] if bowler_name else None
            fielder_clean = _clean_name(fielder_name)[0] if fielder_name else None

            if bowler_clean:
                _sheet_entry(bowling_team_full, bowler_clean)
            if fielder_clean and how_out in ("ct", "st", "run out"):
                _sheet_entry(bowling_team_full, fielder_clean)

            bat_rows.append({
                "position": position,
                "batsman_name": clean_name,
                "batsman_id": clean_name,
                "how_out": how_out,
                "bowler_name": bowler_clean,
                "bowler_id": bowler_clean,
                "fielder_name": fielder_clean,
                "fielder_id": fielder_clean,
                "runs": bm.group("runs"),
                "balls": bm.group("balls"),
                "fours": bm.group("fours"),
                "sixes": bm.group("sixes")
            })

        # Extras / totals / did-not-bat

        extras = {}
        totals = {}
        dnb_names = []

        for line in batting_part.split("\n"):
            line = line.strip()
            em = EXTRAS_LINE.match(line)
            if em:
                extras = _parse_extras(em.group("detail"))
                extras["total"] = int(em.group("total"))
                continue
            tm = TOTALS_LINE.match(line)
            if tm:
                totals = {"runs": int(tm.group("runs"))}
                continue
            dm = DID_NOT_BAT.match(line)
            if dm and dm.group("names").strip():
                dnb_names = [n.strip() for n in dm.group("names").split(",") if n.strip()]

        for raw_name in dnb_names:
            _sheet_entry(batting_team_full, raw_name)

        # ---------------- Bowling ----------------

        bowl_rows = []

        for bm in _parse_rows(
            bowling_part, BOWLING_ROW,
            terminators=("Fall of wicket", "Batting:", "Match Notes")
        ):
            bowler_clean = _sheet_entry(bowling_team_full, bm.group("name"))

            extras_detail = _parse_extras(bm.group("extras"))

            bowl_rows.append({
                "bowler_name": bowler_clean,
                "bowler_id": bowler_clean,
                "overs": bm.group("overs"),
                "maidens": bm.group("maidens"),
                "runs": bm.group("runs"),
                "wickets": bm.group("wickets"),
                "wides": extras_detail["wides"],
                "no_balls": extras_detail["no_balls"]
            })

        wickets_down = sum(
            1 for r in bat_rows
            if r["how_out"] not in ("not out", "retired not out", "retired hurt")
        )

        innings_list.append({
            "innings_number": ii + 1,
            "team_batting_id": batting_team_full,
            "team_batting_name": batting_team_full,
            "runs": totals.get("runs"),
            "wickets": wickets_down,
            "overs": None,
            "declared": 0,
            "forfeited_innings": 0,
            "extra_byes": extras.get("byes", 0),
            "extra_leg_byes": extras.get("leg_byes", 0),
            "extra_wides": extras.get("wides", 0),
            "extra_no_balls": extras.get("no_balls", 0),
            "extra_penalty_runs": extras.get("penalty_runs", 0),
            "total_extras": extras.get("total", 0),
            "bat": bat_rows,
            "bowl": bowl_rows,
            "fow": []
        })

    # --------------------------------------------------------------
    # Players (team sheets)
    # --------------------------------------------------------------

    players = [
        {"home_team": sorted(
            team_sheets.get(home_full, {}).values(),
            key=lambda p: (p["position"] is None, p["position"])
        )},
        {"away_team": sorted(
            team_sheets.get(away_full, {}).values(),
            key=lambda p: (p["position"] is None, p["position"])
        )}
    ]

    return {
        "id": source_match_id,
        "home_club_id": home_club, "home_club_name": home_club,
        "home_team_id": home_full, "home_team_name": home_team,
        "away_club_id": away_club, "away_club_name": away_club,
        "away_team_id": away_full, "away_team_name": away_team,
        "match_date": match_date,
        "match_time": None,
        "competition_id": None,
        "competition_name": header_match.group("competition").strip(),
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": header_match.group("venue").strip(),
        "no_of_innings": len(innings_list),
        "no_of_overs": no_of_overs,
        "no_of_days": 1,
        "toss": toss_winner_text or None,
        "toss_won_by_team_id": toss_won_by_team_id,
        "result": result,
        "result_applied_to": result_applied_to,
        "result_description": result_description,
        "status": "Played",
        "last_updated": None,
        "players": players,
        "innings": innings_list
    }


# ==================================================================
# PUBLIC ENTRY POINT
# ==================================================================

def parse_pdf(pdf_path):
    """
    Parse one CricHQ "Full Scorecard Report" PDF.

    Returns
    -------
    list of dict
        One match-detail dict per match found (Play-Cricket shaped),
        in document order. Abandoned matches are included with empty
        innings/players and status="Abandoned".
    """

    text = _extract_text(pdf_path)
    headers = list(MATCH_HEADER.finditer(text))

    matches = []

    for i, header_match in enumerate(headers):

        start = header_match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[start:end]

        matches.append(_parse_match(header_match, body, i))

    return matches


# ==================================================================
# CLI
# ==================================================================

if __name__ == "__main__":

    import argparse
    import json
    import sys
    from datetime import datetime, timezone

    from sqlite_store import SQLiteStore

    parser = argparse.ArgumentParser(
        description="Ingest one or more CricHQ Full Scorecard Report PDFs into the SQLite store."
    )
    parser.add_argument("pdf_paths", nargs="+", help="CricHQ PDF file(s) to parse.")
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")
    parser.add_argument(
        "--json-out",
        help=(
            "Also write every parsed match-detail dict to this JSON file -- "
            "an indexed, greppable/diffable backup of what the PDF parsed "
            "to, independent of re-running the regex parser against the "
            "PDF again. Unlike playcricket/playcricket_24_25_26.json this has no "
            "seasons/versioning wrapper: the PDF is a closed archive, "
            "parsed once, not something synced incrementally."
        )
    )

    args = parser.parse_args()

    store = SQLiteStore(args.sqlite_db)

    total_played = 0
    total_abandoned = 0
    all_matches = []

    for pdf_path in args.pdf_paths:

        print(f"Parsing {pdf_path} ...")
        matches = parse_pdf(pdf_path)
        all_matches.extend(matches)

        for match in matches:

            match_date = match.get("match_date")
            season = int(match_date[-4:]) if match_date else None

            store.insert_match(match, source="crichq_pdf", season=season)

            if match["status"] == "Abandoned":
                total_abandoned += 1
            else:
                total_played += 1

        print(f"  {len(matches)} matches found in this file.")

    store.conn.commit()
    store.close()

    print(f"Done. Played: {total_played}, Abandoned: {total_abandoned}")

    if args.json_out:

        with open(args.json_out, "w") as f:
            json.dump(
                {
                    "source": "crichq_pdf",
                    "source_pdfs": args.pdf_paths,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "match_count": len(all_matches),
                    "matches": all_matches
                },
                f,
                indent=2
            )

        print(f"Wrote {len(all_matches)} matches to {args.json_out}")
