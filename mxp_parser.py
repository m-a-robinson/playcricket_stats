#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
mxp_parser.py

Parses CricketStatz ".MXP" match exports (File -> Export/Email Matches
in the CricketStatz desktop app) into the same match-detail shape used
by Scorecard / sqlite_store.py, so they can be ingested through
SQLiteStore.insert_match() exactly like Play-Cricket data.

Architecture
------------

    CricketStatz .MXP export
          |
          v
    parse_mxp()              <- this module
          |
          v
    Scorecard (unchanged)
          |
          v
    SQLiteStore.insert_match(source="cricketstatz")

Format
------
Unlike the CricHQ PDF, .MXP is a plain, fully-documented `Key=Value`
text format (see `MXP Format.doc` in the repo, read with `antiword`) --
one record per line, no PDF-style row-wrapping to reassemble. Each
match is a flat run of lines from `Record=Match` to `Endmatch=True`,
with per-innings blocks (`Innings=1`, `Innings=2`, ...) nested inside.

Identity
--------
Unlike CricHQ, CricketStatz DOES carry stable numeric ids for players,
clubs, teams, and grounds -- these are used directly as source ids
(e.g. a player's source_player_id is its literal CricketStatz player
id), which is a stronger identity signal than crichq_pdf.py's
name-derived ids. `.MXP` carries no numeric match id of its own, so one
is synthesised from date + the two team ids (unique within one club's
archive, mirroring crichq_pdf.py's synthetic match id).

A source occasionally uses player id "0" with name "?" for a batting
performance by an unidentified (usually opposition) player -- runs are
still recorded, just not attributed to a named person. These are kept
as real batting rows under a synthetic, match/position-scoped id
(never a shared "unknown player" id, which would wrongly merge unrelated
people's stats together) -- see `_unknown_batsman_id()`.

Not modelled
------------
`fow`/`fowpos` on each batsman row look like fall-of-wicket data (score
and wicket number) but are NOT reliably so: sorting a real innings by
`fow` does not give a monotonically increasing sequence matching
`fowpos` (verified against the bundled Bodyline Test demo data), and
the format doc itself warns "They are not necessarily related to the
batsman's record in which they are located." Rather than fabricate
incorrect fall-of-wickets/partnership data, `innings["fow"]` is always
left empty -- this only affects fall_of_wickets()/partnership_table()
display, not career stats or leaderboards. `Special=` (drop catch/hat
trick notes) and `Retirement=` lines are informational extras already
reflected in the batsman's own row (via the retired* how_out codes) and
are not otherwise modelled, matching the internal shape.
"""

import re


# ==================================================================
# HOW-OUT CODES (from MXP Format.doc)
# ==================================================================

_HOWOUT_TEXT = {
    "0": "did not bat",
    "1": "not out",
    "2": "b",
    "3": "ct",
    "4": "ct",                  # caught and bowled -- fielder = bowler
    "5": "hit wicket",
    "6": "lbw",
    "7": "retired hurt",
    "8": "run out",
    "9": "st",
    "10": "obstructed field",
    "11": "handled ball",
    "12": "retired out",
    "13": "retired not out",
    "14": "timed out",
    "15": "hit ball twice",
    "16": "absent hurt",
    "17": "absent ill",
    "18": "ct",                 # caught behind -- fielder = outby (keeper)
}

_CAUGHT_AND_BOWLED = "4"
_CAUGHT_CODES = {"3", "9", "18"}   # ct, st, ct behind -- fielder = outby
_RUN_OUT = "8"
_BOWLER_ONLY_CODES = {"2", "5", "6"}   # b, hit wicket, lbw

# Result codes differ for 1-day/T20 matches (Type 1/3) vs multi-day (Type 2).
_RESULT_1DAY = {
    "0": ("No result", None),
    "1": ("won", "team1"),
    "2": ("won", "team2"),
    "3": ("Match drawn", None),
    "4": ("Match tied", None),
    "5": ("won on forfeit", "team1"),
    "6": ("won on forfeit", "team2"),
    "7": ("Result unknown", None),
    "8": ("Match abandoned", None),
}

_RESULT_MULTIDAY = {
    "0": ("No result", None),
    "1": ("won outright", "team1"),
    "2": ("won outright", "team2"),
    "3": ("won on 1st innings", "team1"),
    "4": ("won on 1st innings", "team2"),
    "5": ("Match drawn", None),
    "6": ("Match tied outright", None),
    "7": ("Match tied on 1st innings", None),
    "8": ("won on forfeit", "team1"),
    "9": ("won on forfeit", "team2"),
    "10": ("Result unknown", None),
    "11": ("Match abandoned", None),
}

# Keys that belong to whichever innings block is currently open.
_INNINGS_EXTRA_KEYS = {
    "LegByes": "extra_leg_byes",
    "Byes": "extra_byes",
    "Wides": "extra_wides",
    "NoBalls": "extra_no_balls",
    "Penalties": "extra_penalty_runs",
}


# ==================================================================
# SMALL VALUE HELPERS
# ==================================================================

def _split_fields(value):
    return [p.strip() for p in value.split(";")]


def _id_name(parts, i):
    id_str = parts[i] if i < len(parts) else ""
    name_str = parts[i + 1] if i + 1 < len(parts) else ""
    return id_str, name_str


def _clean_ref(id_str, name_str):
    """A raw 'id;name' pair with no real player behind it -> (None, None)."""

    if id_str in ("", "0", "-1", "-2") or name_str in ("", "?"):
        return None, None

    return id_str, name_str


def _to_int(value, default=0):

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ==================================================================
# DISMISSAL RESOLUTION
# ==================================================================

def _resolve_dismissal(code, bowler_id, bowler_name, outby_id, outby_name):
    """
    CricketStatz howout code + raw bowler/outby refs
    -> (how_out_text, bowler_id, bowler_name, fielder_id, fielder_name)
    in the vocabulary Scorecard/_standardise_batting expect.
    """

    how_out = _HOWOUT_TEXT.get(code, "did not bat")

    bowler_id_c, bowler_name_c = _clean_ref(bowler_id, bowler_name)
    outby_id_c, outby_name_c = _clean_ref(outby_id, outby_name)

    if code == _CAUGHT_AND_BOWLED:
        return how_out, bowler_id_c, bowler_name_c, bowler_id_c, bowler_name_c

    if code in _CAUGHT_CODES:

        if outby_id == "-2":  # documented sentinel: caught/run out by a substitute
            return how_out, bowler_id_c, bowler_name_c, None, "Sub"

        return how_out, bowler_id_c, bowler_name_c, outby_id_c, outby_name_c

    if code == _RUN_OUT:

        if outby_id == "-2":
            return how_out, None, None, None, "Sub"

        return how_out, None, None, outby_id_c, outby_name_c

    if code in _BOWLER_ONLY_CODES:
        return how_out, bowler_id_c, bowler_name_c, None, None

    # not out / did not bat / retired* / timed out / obstructed field /
    # handled ball / hit ball twice / absent* / unrecognised code
    return how_out, None, None, None, None


# ==================================================================
# RESULT RESOLUTION
# ==================================================================

def _resolve_result(type_code, result_code, team1_id, team1_name, team2_id, team2_name):

    table = _RESULT_1DAY if type_code in ("1", "3") else _RESULT_MULTIDAY
    entry = table.get(result_code)

    if entry is None:
        return None, None, None

    template, winner = entry

    if winner == "team1":
        return template, team1_id, f"{team1_name} {template}"

    if winner == "team2":
        return template, team2_id, f"{team2_name} {template}"

    return template, None, template


# ==================================================================
# ONE MATCH BLOCK -> LIST OF LINES
# ==================================================================

def _split_into_blocks(text):
    """The export is one flat stream; split it on 'Record=Match' lines."""

    blocks = []
    current = None

    for line in text.splitlines():

        line = line.rstrip("\r\n")

        if not line.strip():
            continue

        if line.strip() == "Record=Match":

            if current is not None:
                blocks.append(current)

            current = []
            continue

        if current is not None:
            current.append(line)

    if current is not None:
        blocks.append(current)

    return blocks


_BATSMAN_KEY = re.compile(r"^Batsman(\d+)$")
_BOWLER_KEY = re.compile(r"^Bowler(\d+)$")


# ==================================================================
# ONE MATCH
# ==================================================================

def _unknown_batsman_id(source_match_id, team_key, position):
    """
    A stable id for an anonymous ('0;?') batsman -- scoped to this exact
    match/team/position so distinct unknown players across different
    matches (or even the two teams of one match) never collapse into a
    single shared canonical player.
    """

    return f"unknown|{source_match_id}|{team_key}|{position}"


def _parse_match(lines):

    fields = {}
    innings_list = []
    current_innings = None

    for line in lines:

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        bat_m = _BATSMAN_KEY.match(key)
        bowl_m = _BOWLER_KEY.match(key)

        if key == "Innings":

            current_innings = {
                "innings_number": _to_int(value),
                "bat": [], "bowl": [],
                "extra_leg_byes": 0, "extra_byes": 0,
                "extra_wides": 0, "extra_no_balls": 0,
                "extra_penalty_runs": 0,
                "iresult": None
            }
            innings_list.append(current_innings)
            continue

        if bat_m and current_innings is not None:
            current_innings["bat"].append((int(bat_m.group(1)), value))
            continue

        if bowl_m and current_innings is not None:
            current_innings["bowl"].append((int(bowl_m.group(1)), value))
            continue

        if key in _INNINGS_EXTRA_KEYS and current_innings is not None:
            current_innings[_INNINGS_EXTRA_KEYS[key]] = _to_int(value)
            continue

        if key == "IResult" and current_innings is not None:
            current_innings["iresult"] = value
            continue

        if key in ("Special", "Retirement") or re.match(r"^Retirement\d+$", key):
            continue  # informational only, not part of the internal shape

        fields[key] = value

    # --------------------------------------------------------------
    # Match-level fields
    # --------------------------------------------------------------

    type_code = fields.get("Type", "").strip()
    match_date = fields.get("Date") or None

    ground_id, ground_name = _id_name(_split_fields(fields.get("Ground", "")), 0)
    grade_id, grade_name = _id_name(_split_fields(fields.get("Grade", "")), 0)
    club1_id, club1_name = _id_name(_split_fields(fields.get("Club1", "")), 0)
    club2_id, club2_name = _id_name(_split_fields(fields.get("Club2", "")), 0)
    team1_id, team1_name = _id_name(_split_fields(fields.get("Team1", "")), 0)
    team2_id, team2_name = _id_name(_split_fields(fields.get("Team2", "")), 0)

    source_match_id = f"{match_date}|{team1_id}|{team2_id}"

    toss_code = fields.get("Toss", "").strip()
    toss_won_by_team_id = (
        team1_id if toss_code == "0" else team2_id if toss_code == "1" else None
    )
    toss_winner_name = (
        team1_name if toss_code == "0" else team2_name if toss_code == "1" else None
    )

    result_code = fields.get("Result", "").strip()
    result, result_applied_to, result_description = _resolve_result(
        type_code, result_code, team1_id, team1_name, team2_id, team2_name
    )

    # --------------------------------------------------------------
    # No play at all
    # --------------------------------------------------------------

    if not innings_list:

        return {
            "id": source_match_id,
            "home_club_id": club1_id, "home_club_name": club1_name,
            "home_team_id": team1_id, "home_team_name": team1_name,
            "away_club_id": club2_id, "away_club_name": club2_name,
            "away_team_id": team2_id, "away_team_name": team2_name,
            "match_date": match_date,
            "match_time": None,
            "competition_id": grade_id, "competition_name": grade_name,
            "competition_type": None,
            "league_id": None, "league_name": None,
            "ground_id": ground_id, "ground_name": ground_name,
            "no_of_innings": 0,
            "no_of_overs": None,
            "no_of_days": 1,
            "toss": toss_winner_name,
            "toss_won_by_team_id": toss_won_by_team_id,
            "result": result,
            "result_applied_to": result_applied_to,
            "result_description": result_description or "Abandoned - No Play Possible",
            "status": "Abandoned",
            "last_updated": None,
            "players": [],
            "innings": []
        }

    # --------------------------------------------------------------
    # Team sheets, built up as batting/bowling/captain/keeper rows
    # are encountered (mirrors crichq_pdf.py's _sheet_entry approach)
    # --------------------------------------------------------------

    team_sheets = {team1_id: {}, team2_id: {}}

    def _sheet_entry(team_key, player_id, player_name, position=None,
                      captain=False, wicket_keeper=False):

        sheet = team_sheets.setdefault(team_key, {})

        entry = sheet.setdefault(player_id, {
            "player_name": player_name, "player_id": player_id,
            "position": position, "captain": False, "wicket_keeper": False
        })

        if position is not None and entry["position"] is None:
            entry["position"] = position

        entry["captain"] = entry["captain"] or captain
        entry["wicket_keeper"] = entry["wicket_keeper"] or wicket_keeper

    captain1_id, captain1_name = _clean_ref(*_id_name(_split_fields(fields.get("Captain1", "")), 0))
    captain2_id, captain2_name = _clean_ref(*_id_name(_split_fields(fields.get("Captain2", "")), 0))
    keeper1_id, keeper1_name = _clean_ref(*_id_name(_split_fields(fields.get("Keeper1", "")), 0))
    keeper2_id, keeper2_name = _clean_ref(*_id_name(_split_fields(fields.get("Keeper2", "")), 0))

    if captain1_id:
        _sheet_entry(team1_id, captain1_id, captain1_name, captain=True)
    if captain2_id:
        _sheet_entry(team2_id, captain2_id, captain2_name, captain=True)
    if keeper1_id:
        _sheet_entry(team1_id, keeper1_id, keeper1_name, wicket_keeper=True)
    if keeper2_id:
        _sheet_entry(team2_id, keeper2_id, keeper2_name, wicket_keeper=True)

    # --------------------------------------------------------------
    # Innings
    # --------------------------------------------------------------

    result_innings = []

    for innings in innings_list:

        innings_number = innings["innings_number"]

        # Documented/verified convention: odd innings number = team1
        # batting, even = team2 -- see the module docstring for why
        # this can't instead be inferred from fow/fowpos.
        batting_id = team1_id if innings_number % 2 == 1 else team2_id
        batting_name = team1_name if innings_number % 2 == 1 else team2_name
        bowling_id = team2_id if innings_number % 2 == 1 else team1_id

        bat_rows = []

        for position, raw in innings["bat"]:

            parts = _split_fields(raw)
            parts += [""] * (14 - len(parts))

            (batsman_id, batsman_name, code,
             outby_id, outby_name, bowler_id, bowler_name,
             score, _fow, _fowpos, fours, sixes, balls, _minutes) = parts[:14]

            if batsman_id in ("", "0"):

                if code == "0":
                    # Genuinely unused batting slot (team had fewer than
                    # 11 players available) -- nothing to record.
                    continue

                # A real (usually opposition) batting performance whose
                # player identity wasn't recorded by the scorer.
                batsman_id = _unknown_batsman_id(source_match_id, batting_id, position)
                batsman_name = "Unknown"

            elif code == "0":
                # Did not bat -- on the team sheet, but not a batting row.
                _sheet_entry(batting_id, batsman_id, batsman_name, position=position)
                continue

            how_out, r_bowler_id, r_bowler_name, r_fielder_id, r_fielder_name = (
                _resolve_dismissal(code, bowler_id, bowler_name, outby_id, outby_name)
            )

            _sheet_entry(batting_id, batsman_id, batsman_name, position=position)

            # Whoever is named as bowler/fielder here played for the
            # bowling side, regardless of what the dismissal code
            # credits them with in the batting table.
            raw_bowler_id, raw_bowler_name = _clean_ref(bowler_id, bowler_name)
            raw_outby_id, raw_outby_name = _clean_ref(outby_id, outby_name)

            if raw_bowler_id:
                _sheet_entry(bowling_id, raw_bowler_id, raw_bowler_name)
            if raw_outby_id:
                _sheet_entry(bowling_id, raw_outby_id, raw_outby_name)

            bat_rows.append({
                "position": position,
                "batsman_id": batsman_id, "batsman_name": batsman_name,
                "how_out": how_out,
                "bowler_id": r_bowler_id, "bowler_name": r_bowler_name,
                "fielder_id": r_fielder_id, "fielder_name": r_fielder_name,
                "runs": _to_int(score), "balls": _to_int(balls),
                "fours": _to_int(fours), "sixes": _to_int(sixes)
            })

        bowl_rows = []

        for _position, raw in innings["bowl"]:

            parts = _split_fields(raw)
            parts += [""] * (8 - len(parts))

            bowler_id, bowler_name, overs, maidens, wickets, runs, wides, noballs = parts[:8]

            if bowler_id in ("", "0"):
                continue  # no bowler-identity equivalent of the "unknown batsman" case seen in practice

            _sheet_entry(bowling_id, bowler_id, bowler_name)

            bowl_rows.append({
                "bowler_id": bowler_id, "bowler_name": bowler_name,
                "overs": overs, "maidens": _to_int(maidens),
                "runs": _to_int(runs), "wickets": _to_int(wickets),
                "wides": _to_int(wides), "no_balls": _to_int(noballs)
            })

        extras_total = (
            innings["extra_byes"] + innings["extra_leg_byes"]
            + innings["extra_wides"] + innings["extra_no_balls"]
            + innings["extra_penalty_runs"]
        )

        wickets_down = sum(
            1 for r in bat_rows
            if r["how_out"] not in ("not out", "retired not out", "retired hurt")
        )

        result_innings.append({
            "innings_number": innings_number,
            "team_batting_id": batting_id,
            "team_batting_name": batting_name,
            "runs": sum(r["runs"] for r in bat_rows) + extras_total,
            "wickets": wickets_down,
            "overs": None,
            "declared": 1 if innings["iresult"] == "3" else 0,
            "forfeited_innings": 0,
            "extra_byes": innings["extra_byes"],
            "extra_leg_byes": innings["extra_leg_byes"],
            "extra_wides": innings["extra_wides"],
            "extra_no_balls": innings["extra_no_balls"],
            "extra_penalty_runs": innings["extra_penalty_runs"],
            "total_extras": extras_total,
            "bat": bat_rows,
            "bowl": bowl_rows,
            "fow": []  # see module docstring: fow/fowpos aren't trustworthy
        })

    # --------------------------------------------------------------
    # Players (team sheets)
    # --------------------------------------------------------------

    players = [
        {"home_team": sorted(
            team_sheets.get(team1_id, {}).values(),
            key=lambda p: (p["position"] is None, p["position"])
        )},
        {"away_team": sorted(
            team_sheets.get(team2_id, {}).values(),
            key=lambda p: (p["position"] is None, p["position"])
        )}
    ]

    return {
        "id": source_match_id,
        "home_club_id": club1_id, "home_club_name": club1_name,
        "home_team_id": team1_id, "home_team_name": team1_name,
        "away_club_id": club2_id, "away_club_name": club2_name,
        "away_team_id": team2_id, "away_team_name": team2_name,
        "match_date": match_date,
        "match_time": None,
        "competition_id": grade_id, "competition_name": grade_name,
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": ground_id, "ground_name": ground_name,
        "no_of_innings": len(result_innings),
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": toss_winner_name,
        "toss_won_by_team_id": toss_won_by_team_id,
        "result": result,
        "result_applied_to": result_applied_to,
        "result_description": result_description,
        "status": "Played",
        "last_updated": None,
        "players": players,
        "innings": result_innings
    }


# ==================================================================
# PUBLIC ENTRY POINT
# ==================================================================

def parse_mxp(mxp_path):
    """
    Parse one CricketStatz `.MXP` export (one or more matches).

    Returns
    -------
    list of dict
        One match-detail dict per match found (Play-Cricket shaped), in
        document order.
    """

    with open(mxp_path, "r", encoding="cp1252", errors="replace") as f:
        text = f.read()

    return [_parse_match(block) for block in _split_into_blocks(text)]


# ==================================================================
# CLI
# ==================================================================

if __name__ == "__main__":

    import argparse

    from sqlite_store import SQLiteStore

    parser = argparse.ArgumentParser(
        description="Ingest one or more CricketStatz .MXP exports into the SQLite store."
    )
    parser.add_argument("mxp_paths", nargs="+", help="CricketStatz .MXP file(s) to parse.")
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")

    args = parser.parse_args()

    store = SQLiteStore(args.sqlite_db)

    total_played = 0
    total_abandoned = 0

    for mxp_path in args.mxp_paths:

        print(f"Parsing {mxp_path} ...")
        matches = parse_mxp(mxp_path)

        for match in matches:

            match_date = match.get("match_date")  # dd/mm/yyyy
            season = int(match_date[-4:]) if match_date else None

            store.insert_match(match, source="cricketstatz", season=season)

            if match["status"] == "Abandoned":
                total_abandoned += 1
            else:
                total_played += 1

        print(f"  {len(matches)} matches found in this file.")

    store.conn.commit()
    store.close()

    print(f"Done. Played: {total_played}, Abandoned: {total_abandoned}")
