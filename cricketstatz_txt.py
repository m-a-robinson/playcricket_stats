"""
cricketstatz_txt.py

Parses CricketStatz plain-text scorecard printouts (one file per match,
e.g. "ELPM_1_v_FH__26.6.10.txt") into the same match-detail shape
Scorecard/SQLiteStore.insert_match() expects -- source="cricketstatz_txt".

A DIFFERENT format from the other two CricketStatz-derived sources this
project already handles:
  - `mxp_parser.py` reads the bulk `.MXP` "File -> Export/Email Matches"
    export: plain Key=Value text, one bulk file for the whole archive,
    carrying real numeric ids.
  - This module reads an individual match's own printed/saved text
    scorecard -- a completely different layout (a human-readable batting/
    bowling table, not Key=Value pairs), with no numeric ids at all.
    Club/team names here are the short codes CricketStatz's print view
    uses ("ELPM", "F&H", "WLM", "SH", "TSJ", ...), not the fuller names
    the .MXP export or Play-Cricket use -- so this source's own
    home_club_id/away_club_id values will NOT automatically line up
    with the other three sources' club rows without a
    `reconcile/decisions.yaml` club merge, same as any other
    same-real-club-different-spelling case elsewhere in this project.

Kept deliberately separate from `mxp_parser.py` (a different source
name, "cricketstatz_txt") rather than merged into "cricketstatz" --
these are individually-saved match printouts a person has kept
locally, not a re-run of the same bulk export, and match ids/
formatting rules genuinely differ.
"""

import re


SOURCE = "cricketstatz_txt"

_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

HEADER_LINE = re.compile(r"^(?P<home>.+?)\s+Vs\s+(?P<away>.+)$")

MATCH_INFO_LINE = re.compile(
    r"^\S*Innings Match Played At (?P<ground>[^,]+),\s*"
    r"(?:(?P<club_tag>[^,]+),\s*)?"
    r"(?P<date>\d{1,2}-\w{3}-\d{2,4}),\s*(?P<competition>.+)$"
)

RESULT_LINE = re.compile(r"^(?P<team>.+?) Win by (?P<margin>.+)$")
DRAW_LINE = re.compile(r"^Match Drawn\.?\s*$", re.IGNORECASE)
TIE_LINE = re.compile(r"^Match Tied\.?\s*$", re.IGNORECASE)

TOSS_LINE = re.compile(r"^Toss won by\s+(?P<team>.+)$")

INNINGS_HEADER = re.compile(
    r"^(?P<team>.+?) (?:1st|2nd) Innings (?P<runs>\d+)/(?P<wickets>\d+)\s+"
    r"(?P<status>Closed|All Out|Declared|Abandoned)\s*\(Overs (?P<overs>[\d.]+)\)$"
)

BATTING_TABLE_HEADER = re.compile(r"^Batsman\s+Fieldsman\s+Bowler\s+Runs\s+4s\s+6s$")
BOWLING_TABLE_HEADER = re.compile(r"^Bowler\s+O\s+M\s+R\s+W\s+wd\s+nb$")

EXTRAS_LINE = re.compile(r"^extras\s+\((?P<detail>[^)]*)\)\s+(?P<total>\d+)$", re.IGNORECASE)
TOTALS_LINE = re.compile(r"^TOTAL\s+(?P<wickets>\d+)\s+wickets?\s+for\s+(?P<runs>\d+)$", re.IGNORECASE)
FOW_HEADER = re.compile(r"^FOW$", re.IGNORECASE)

BOWLING_ROW = re.compile(
    r"^(?P<name>.+?)\s+(?P<overs>[\d.]+)\s+(?P<maidens>\d+)\s+(?P<runs>\d+)\s+"
    r"(?P<wickets>\d+)\s+(?P<wides>\d+|-)\s+(?P<noballs>\d+|-)\s*$"
)

_EXTRAS_LABELS = {"b": "byes", "lb": "leg_byes", "w": "wides", "nb": "no_balls", "pen": "penalty_runs"}
_EXTRAS_TOKEN = re.compile(r"(lb|nb|pen|b|w)(\d+)")


def _parse_extras(detail_text):

    result = {"byes": 0, "leg_byes": 0, "wides": 0, "no_balls": 0, "penalty_runs": 0}

    if not detail_text:
        return result

    for label, value in _EXTRAS_TOKEN.findall(detail_text):
        result[_EXTRAS_LABELS[label]] = int(value)

    return result


def _parse_date(datetext):
    """'26-Jun-2010' -> ('26/06/2010', 2010)."""

    m = re.match(r"^(?P<day>\d{1,2})-(?P<mon>\w{3})-(?P<year>\d{2,4})$", datetext.strip())

    if not m:
        return None, None

    month = _MONTHS.get(m.group("mon").title())

    if month is None:
        return None, None

    day = int(m.group("day"))
    year = int(m.group("year"))

    if year < 100:
        year += 2000 if year < 70 else 1900

    return f"{day:02d}/{month:02d}/{year}", year


_BARE_DIVISION = re.compile(r"^Division\s+\d+$", re.IGNORECASE)


def _normalise_division_name(competition, season):
    """
    Same fix as mxp_parser.py's _normalise_division_name() -- CricketStatz's
    own competition text is a bare "Division N" for every season up to and
    including 2015 (the whole 2010 batch this module ingests included);
    prefixed "NMCL " to disambiguate from GMCL's own "Division N" naming
    from 2016 on, per the user's request (2026-08-28). Only the bare
    "Division N" form is touched -- "Cup" and other competition names are
    left as CricketStatz recorded them.
    """

    if season is not None and season <= 2015 and _BARE_DIVISION.match(competition or ""):
        return f"NMCL {competition}"

    return competition


_TEAM_SUFFIX = re.compile(r"^(?P<club>.+?)\s+(?P<team>\d+(?:st|nd|rd|th)\s+XI)$", re.IGNORECASE)


def _split_team_name(full_name):
    """'ELPM 1st XI' -> ('ELPM', '1st XI'); no trailing 'Nth XI' -> (full_name, full_name)."""

    m = _TEAM_SUFFIX.match(full_name.strip())

    if m:
        return m.group("club").strip(), m.group("team").strip()

    return full_name.strip(), full_name.strip()


def _clean_name(raw):
    """
    Strip role markers from a raw name and return
    (clean_name, captain, wicket_keeper).

    "J Shiels+"  -> ("J Shiels", False, True)   -- '+' marks wicket-keeper
    "S Keyworth*" -> ("S Keyworth", True, False) -- '*' marks captain
    """

    wicket_keeper = raw.rstrip().endswith("+")
    captain = raw.rstrip().rstrip("+").endswith("*")

    name = raw.strip()
    if name.endswith("+"):
        name = name[:-1]
    if name.endswith("*"):
        name = name[:-1]

    name = re.sub(r"\s+", " ", name).strip()

    return name, captain, wicket_keeper


def _parse_dismissal(middle_text):
    """
    Turn the joined "Fieldsman"+"Bowler" column text into
    (how_out, bowler_name, fielder_name). Returns how_out=None (no
    batting_innings row at all -- team-sheet only) for "dnb"/"Absent
    Hurt".
    """

    text = middle_text.strip()
    low = text.lower()

    if low == "not out":
        return "not out", None, None

    if low == "dnb":
        return None, None, None

    if low.startswith("absent"):
        return None, None, None

    if low.startswith("retired hurt"):
        return "retired hurt", None, None

    if low.startswith("retired out"):
        return "retired out", None, None

    if low.startswith("retired"):
        return "retired not out", None, None

    if low.startswith("c&b") or low.startswith("c & b"):
        bowler = re.sub(r"^c\s*&\s*b\s*", "", text, flags=re.IGNORECASE).strip()
        return "ct", bowler, bowler

    if low.startswith("c "):
        m = re.match(r"^c\s+(?:(?P<fielder>.+?)\s+)?b\s+(?P<bowler>.+)$", text)
        if m:
            fielder = (m.group("fielder") or "").strip()
            if fielder == "?":
                fielder = ""
            return "ct", m.group("bowler").strip(), fielder or None
        return "ct", None, None

    if low.startswith("st "):
        m = re.match(r"^st\s+(?:(?P<fielder>.+?)\s+)?b\s+(?P<bowler>.+)$", text)
        if m:
            fielder = (m.group("fielder") or "").strip()
            if fielder == "?":
                fielder = ""
            return "st", m.group("bowler").strip(), fielder or None
        return "st", None, None

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
        # "run out C Greaves/P Part." -- credit the first-named fielder,
        # same convention as crichq_pdf.py's "run out (A/B)".
        rest = text[len("run out"):].strip()
        fielder = rest.split("/")[0].strip() if rest else None
        return "run out", None, fielder or None

    if low.startswith("b "):
        return "b", text[2:].strip(), None

    return text, None, None


_TRAILING_STATS = re.compile(r"(?P<runs>\d+)\s+(?P<fours>\d+)\s+(?P<sixes>\d+)\s*$")
_TRAILING_DASH = re.compile(r"-\s*$")


def _split_batting_row(line):
    """
    Tokenise one batting-table row. Columns aren't fixed-width, so
    first peel the trailing Runs/4s/6s (or a single '-' for dnb/absent)
    off the back by anchoring on the END of the line, THEN split what's
    left (name + dismissal text) on runs of 2+ spaces.

    Anchoring the trailing numbers matters: they're right-aligned in a
    fixed-width column, so a two-digit value (e.g. a score of 87, or
    16 fours) leaves LESS padding before it than a one-digit value --
    "87 16 1" can be separated by single spaces even though every
    other column boundary on the same row uses 2+. Splitting the whole
    line on a single 2+-space rule first (the previous approach) could
    silently swallow the runs/4s/6s numbers into the dismissal text
    instead of recognising them as separate columns.

    Returns (name_raw, dismissal_text, runs, fours, sixes) with
    runs/fours/sixes as ints, or all None for dnb/absent-hurt rows.
    """

    stripped = line.strip()

    if not stripped:
        return None

    m = _TRAILING_STATS.search(stripped)

    if m:
        runs, fours, sixes = int(m.group("runs")), int(m.group("fours")), int(m.group("sixes"))
        rest = stripped[:m.start()].strip()
    else:
        dm = _TRAILING_DASH.search(stripped)
        runs, fours, sixes = None, None, None
        rest = stripped[:dm.start()].strip() if dm else stripped

    tokens = [t for t in re.split(r" {2,}", rest) if t != ""]

    if not tokens:
        return None

    name_raw = tokens[0]
    dismissal = " ".join(tokens[1:]).strip()

    return name_raw, dismissal, runs, fours, sixes


def parse_match_text(text, filename=None):
    """
    Parse one CricketStatz plain-text scorecard into a match-detail
    dict. Returns None if the file doesn't even have a recognisable
    header (not this format).
    """

    lines = [l.rstrip("\n") for l in text.split("\n")]

    header_m = HEADER_LINE.match(lines[0].strip()) if lines else None
    if not header_m:
        return None

    home_full = header_m.group("home").strip()
    away_full = header_m.group("away").strip()

    info_m = None
    for line in lines[1:4]:
        info_m = MATCH_INFO_LINE.match(line.strip())
        if info_m:
            break

    if not info_m:
        return None

    ground = info_m.group("ground").strip()
    competition = info_m.group("competition").strip()
    match_date, season = _parse_date(info_m.group("date"))
    competition = _normalise_division_name(competition, season)

    # Derived from match content (home|away|date), NOT the filename --
    # these are individually-saved files, and duplicate/mislabelled
    # filenames are real (confirmed against a batch of 2010 scans:
    # some files are byte-identical copies of another match under a
    # different name). A content-derived id means a genuine duplicate
    # file collapses onto the same match via insert_match()'s existing
    # (source, source_match_id) idempotency, instead of silently
    # double-counting it as two different matches.
    source_match_id = f"{home_full}|{away_full}|{info_m.group('date')}"

    result = None
    result_applied_to = None
    result_description = None
    toss_winner_text = None
    toss_won_by_team_id = None

    for line in lines:

        stripped = line.strip()

        rm = RESULT_LINE.match(stripped)
        if rm:
            winner_text = rm.group("team").strip()
            result = f"Won by {rm.group('margin').strip()}"
            result_applied_to = home_full if winner_text == home_full else (
                away_full if winner_text == away_full else None
            )
            result_description = f"{winner_text} won by {rm.group('margin').strip()}"
            continue

        if DRAW_LINE.match(stripped):
            result, result_description = "Drawn", "Match drawn"
            continue

        if TIE_LINE.match(stripped):
            result, result_description = "Tied", "Match tied"
            continue

        tm = TOSS_LINE.match(stripped)
        if tm:
            toss_winner_text = tm.group("team").strip()
            toss_won_by_team_id = home_full if toss_winner_text == home_full else (
                away_full if toss_winner_text == away_full else None
            )

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

    innings_headers = []
    for i, line in enumerate(lines):
        ih = INNINGS_HEADER.match(line.strip())
        if ih:
            innings_headers.append((i, ih))

    innings_list = []

    for idx, (line_no, ih) in enumerate(innings_headers):

        i_start = line_no + 1
        i_end = innings_headers[idx + 1][0] if idx + 1 < len(innings_headers) else len(lines)
        innings_lines = lines[i_start:i_end]

        batting_team_full = ih.group("team").strip()
        bowling_team_full = away_full if batting_team_full == home_full else home_full

        bowl_header_idx = None
        for i, line in enumerate(innings_lines):
            if BOWLING_TABLE_HEADER.match(line.strip()):
                bowl_header_idx = i
                break

        batting_lines = innings_lines[:bowl_header_idx] if bowl_header_idx is not None else innings_lines
        bowling_lines = innings_lines[bowl_header_idx + 1:] if bowl_header_idx is not None else []

        bat_rows = []
        position = 0
        extras = {}
        totals = {}
        in_batting_table = False

        for line in batting_lines:

            stripped = line.strip()

            if not stripped:
                continue
            if BATTING_TABLE_HEADER.match(stripped):
                in_batting_table = True
                continue
            if FOW_HEADER.match(stripped):
                break

            em = EXTRAS_LINE.match(stripped)
            if em:
                extras = _parse_extras(em.group("detail"))
                extras["total"] = int(em.group("total"))
                continue

            tm = TOTALS_LINE.match(stripped)
            if tm:
                totals = {"runs": int(tm.group("runs")), "wickets": int(tm.group("wickets"))}
                continue

            if not in_batting_table:
                continue

            parsed = _split_batting_row(line)
            if parsed is None:
                continue

            name_raw, dismissal_text, runs, fours, sixes = parsed
            position += 1
            clean_name = _sheet_entry(batting_team_full, name_raw, position)

            how_out, bowler_name, fielder_name = _parse_dismissal(dismissal_text)

            bowler_clean = _clean_name(bowler_name)[0] if bowler_name else None
            fielder_clean = _clean_name(fielder_name)[0] if fielder_name else None

            if bowler_clean:
                _sheet_entry(bowling_team_full, bowler_clean)
            if fielder_clean and how_out in ("ct", "st", "run out"):
                _sheet_entry(bowling_team_full, fielder_clean)

            if how_out is None:
                # dnb / Absent Hurt -- team sheet only, no batting row.
                continue

            bat_rows.append({
                "position": position,
                "batsman_name": clean_name,
                "batsman_id": clean_name,
                "how_out": how_out,
                "bowler_name": bowler_clean,
                "bowler_id": bowler_clean,
                "fielder_name": fielder_clean,
                "fielder_id": fielder_clean,
                "runs": runs,
                "balls": None,
                "fours": fours,
                "sixes": sixes,
            })

        bowl_rows = []

        for line in bowling_lines:

            stripped = line.strip()
            if not stripped:
                continue

            bm = BOWLING_ROW.match(stripped)
            if not bm:
                continue

            bowler_clean = _sheet_entry(bowling_team_full, bm.group("name"))

            bowl_rows.append({
                "bowler_name": bowler_clean,
                "bowler_id": bowler_clean,
                "overs": bm.group("overs"),
                "maidens": int(bm.group("maidens")),
                "runs": int(bm.group("runs")),
                "wickets": int(bm.group("wickets")),
                "wides": 0 if bm.group("wides") == "-" else int(bm.group("wides")),
                "no_balls": 0 if bm.group("noballs") == "-" else int(bm.group("noballs")),
            })

        wickets_down = totals.get("wickets", int(ih.group("wickets")))

        innings_list.append({
            "innings_number": idx + 1,
            "team_batting_id": batting_team_full,
            "team_batting_name": batting_team_full,
            "runs": totals.get("runs", int(ih.group("runs"))),
            "wickets": wickets_down,
            "overs": ih.group("overs"),
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
            "fow": [],
        })

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

    home_club, home_team = _split_team_name(home_full)
    away_club, away_team = _split_team_name(away_full)

    return {
        "id": source_match_id,
        "home_club_id": home_club, "home_club_name": home_club,
        "home_team_id": home_full, "home_team_name": home_team,
        "away_club_id": away_club, "away_club_name": away_club,
        "away_team_id": away_full, "away_team_name": away_team,
        "match_date": match_date,
        "match_time": None,
        "competition_id": None,
        "competition_name": competition,
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": ground,
        "no_of_innings": len(innings_list),
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": toss_winner_text,
        "toss_won_by_team_id": toss_won_by_team_id,
        "result": result,
        "result_applied_to": result_applied_to,
        "result_description": result_description,
        "status": "Played",
        "last_updated": None,
        "players": players,
        "innings": innings_list,
    }


def parse_file(path):

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    return parse_match_text(text, filename=path.rsplit("/", 1)[-1])


_FILENAME_DATE = re.compile(r"(?P<day>\d{1,2})\.(?P<month>\d{1,2})\.(?P<year>\d{2,4})(?=\.\w+$)")


def date_from_filename(path):
    """
    Best-effort 'DD.M.YY' pulled from a filename like
    'ELPM l v WLM 11.9.10.txt' -> '11/09/2010'. Used only as a sanity
    check against the date parsed from the file's own content -- these
    files are individually named/saved by hand, and a mismatch is a
    real, previously-found signal (a file saved under the wrong name,
    or two different fixtures' files swapped) worth flagging loudly
    rather than silently trusting either one.
    """

    m = _FILENAME_DATE.search(path.rsplit("/", 1)[-1])

    if not m:
        return None

    day, month, year = int(m.group("day")), int(m.group("month")), int(m.group("year"))

    if year < 100:
        year += 2000 if year < 70 else 1900

    return f"{day:02d}/{month:02d}/{year}"


if __name__ == "__main__":

    import argparse
    import json

    from sqlite_store import SQLiteStore

    parser = argparse.ArgumentParser(
        description="Ingest one or more CricketStatz plain-text match scorecards into the SQLite store."
    )
    parser.add_argument("txt_paths", nargs="+", help="CricketStatz .txt scorecard file(s) to parse.")
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")
    parser.add_argument("--json-out", help="Also write every parsed match-detail dict to this JSON file.")

    args = parser.parse_args()

    store = SQLiteStore(args.sqlite_db)

    all_matches = []
    warnings = []

    for path in args.txt_paths:

        match = parse_file(path)

        if match is None:
            print(f"  {path}: not recognised as this format, skipped.")
            continue

        filename_date = date_from_filename(path)
        if filename_date and match["match_date"] and filename_date != match["match_date"]:
            warnings.append(
                f"  WARNING: {path} -- filename implies {filename_date} but the file's "
                f"own content says {match['match_date']} ({match['home_team_name']} v "
                f"{match['away_team_name']}). Likely saved under the wrong name -- the "
                f"real fixture for {filename_date} may be missing."
            )

        existing = store.conn.execute(
            "SELECT 1 FROM matches WHERE source = ? AND source_match_id = ?",
            (SOURCE, match["id"])
        ).fetchone()
        if existing:
            warnings.append(
                f"  WARNING: {path} -- duplicate content of an already-ingested match "
                f"({match['home_team_name']} v {match['away_team_name']}, {match['match_date']}); skipped."
            )
            continue

        season = match["match_date"][-4:] if match["match_date"] else None
        store.insert_match(match, source=SOURCE, season=int(season) if season else None)
        all_matches.append(match)
        print(f"  {path}: {match['home_team_name']} v {match['away_team_name']}, "
              f"{match['match_date']}, {match['no_of_innings']} innings")

    store.conn.commit()
    store.close()

    if warnings:
        print()
        print("=== Warnings ===")
        for w in warnings:
            print(w)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(all_matches, f, indent=2)

    print(f"Done. {len(all_matches)} matches ingested.")
