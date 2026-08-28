"""
nmcl_stats.py

Ingests the North Manchester Cricket League "Final Averages" scanned
sheets (`nmcl stats/*.tif`) into the SQLite store's `nmcl_season_stats`
table -- see schema.sql for why these are a separate, explicitly
season-aggregate table rather than match-level data.

Unlike the other three sources (Play-Cricket API, CricHQ PDF,
CricketStatz .MXP), these sheets are pre-2005 photocopies/scans with no
machine-readable text layer and no consistent enough layout for a
regex/OCR pipeline to be worth the risk of silently mis-reading a
qualification-threshold table (wrong average, wrong player) -- so
ELPM_ROWS below is a direct, manually verified transcription of every
ELPM-relevant row on each sheet, not a parser output. New seasons are
added the same way: read the sheet, add rows here, matching the schema
below exactly (see each dict's keys).

Only ELPM (East Lancs Paper Mill) rows are transcribed -- every other
club appearing on these league-wide sheets is out of scope for this
project, per the same "opposition players aren't tracked as our own
players" boundary the other sources draw (see sqlite_queries.py's
ELPMCC_NAME / elpmcc_only).

"Division One" is this club's 1st XI on every sheet transcribed so
far; "Division Two" would be the 2nd XI. Mapped to team_id via
DIVISION_TEAM_NAMES below, resolved against whatever team rows already
exist in the target store (so it works after the standard "1st XI"/
"2nd XI" club/team dedup key, not by a hardcoded id).
"""

import re


SOURCE = "nmcl_stats"

ELPM_CLUB_CODE = "ELPM"

DIVISION_TEAM_NAMES = {
    1: "1st XI",
    2: "2nd XI",
}


# Every ELPM row transcribed from `nmcl stats/*.tif` so far. Each dict:
#   season, division, discipline ('batting' | 'bowling' | 'wicketkeeping'),
#   name (as printed), source_file, plus the discipline's own columns
#   (see schema.sql's nmcl_season_stats for what each means).
#
# highest_score_not_out is set when the sheet's HS carries a trailing
# "*" (retired/not out at the top score), matching batting_innings.not_out
# elsewhere in the schema.

ELPM_ROWS = [

    # ---- 2003 ----
    {"season": 2003, "division": 1, "discipline": "batting", "name": "J Wade",
     "innings_played": 11, "not_outs": 2, "highest_score": 183, "highest_score_not_out": 1,
     "runs": 574, "average": 63.78, "source_file": "nmcl stats/2003 1.tif"},
    {"season": 2003, "division": 1, "discipline": "batting", "name": "F Daly",
     "innings_played": 13, "not_outs": 2, "highest_score": 109, "highest_score_not_out": 1,
     "runs": 550, "average": 50.00, "source_file": "nmcl stats/2003 1.tif"},
    {"season": 2003, "division": 1, "discipline": "batting", "name": "I Wade",
     "innings_played": 14, "not_outs": 2, "highest_score": 152, "highest_score_not_out": 0,
     "runs": 400, "average": 33.33, "source_file": "nmcl stats/2003 1.tif"},
    {"season": 2003, "division": 1, "discipline": "batting", "name": "J Shiels",
     "innings_played": 15, "not_outs": 4, "highest_score": 84, "highest_score_not_out": 0,
     "runs": 344, "average": 31.27, "source_file": "nmcl stats/2003 1.tif"},
    {"season": 2003, "division": 1, "discipline": "batting", "name": "R Savage",
     "innings_played": 13, "not_outs": 4, "highest_score": 89, "highest_score_not_out": 1,
     "runs": 233, "average": 25.89, "source_file": "nmcl stats/2003 1.tif"},
    {"season": 2003, "division": 1, "discipline": "batting", "name": "G Young",
     "innings_played": 14, "not_outs": 4, "highest_score": 51, "highest_score_not_out": 0,
     "runs": 210, "average": 21.00, "source_file": "nmcl stats/2003 1.tif"},

    {"season": 2003, "division": 1, "discipline": "bowling", "name": "P Hewart",
     "overs": "134", "maidens": 32, "runs_conceded": 422, "wickets": 36,
     "average": 11.72, "source_file": "nmcl stats/2003 2.tif"},

    {"season": 2003, "division": 1, "discipline": "wicketkeeping", "name": "M Robinson",
     "catches": 21, "stumpings": 8, "average": None, "source_file": "nmcl stats/2003 2.tif"},

    # ---- 2004 ----
    {"season": 2004, "division": 1, "discipline": "batting", "name": "J Shiels",
     "innings_played": 16, "not_outs": 1, "highest_score": 104, "highest_score_not_out": 0,
     "runs": 429, "average": 28.60, "source_file": "nmcl stats/2004 1.tif"},
    {"season": 2004, "division": 1, "discipline": "batting", "name": "F Daly",
     "innings_played": 18, "not_outs": 2, "highest_score": 82, "highest_score_not_out": 1,
     "runs": 397, "average": 24.81, "source_file": "nmcl stats/2004 1.tif"},

    {"season": 2004, "division": 1, "discipline": "bowling", "name": "S Dalton",
     "overs": "114.4", "maidens": 22, "runs_conceded": 395, "wickets": 32,
     "average": 12.34, "source_file": "nmcl stats/2004 2.tif"},
    {"season": 2004, "division": 1, "discipline": "bowling", "name": "P Hewart",
     "overs": "176.3", "maidens": 44, "runs_conceded": 549, "wickets": 35,
     "average": 15.69, "source_file": "nmcl stats/2004 2.tif"},

    {"season": 2004, "division": 1, "discipline": "wicketkeeping", "name": "M Robinson",
     "catches": 12, "stumpings": 4, "average": None, "source_file": "nmcl stats/2004 2.tif"},

    # ---- 2005 ----
    {"season": 2005, "division": 1, "discipline": "batting", "name": "F Daly",
     "innings_played": 18, "not_outs": 3, "highest_score": 105, "highest_score_not_out": 1,
     "runs": 635, "average": 42.33, "source_file": "nmcl stats/2005 1.tif"},
    {"season": 2005, "division": 1, "discipline": "batting", "name": "G Greaves",
     "innings_played": 18, "not_outs": 5, "highest_score": 67, "highest_score_not_out": 1,
     "runs": 424, "average": 32.62, "source_file": "nmcl stats/2005 1.tif"},
    {"season": 2005, "division": 1, "discipline": "batting", "name": "J Shiels",
     "innings_played": 14, "not_outs": 0, "highest_score": 66, "highest_score_not_out": 0,
     "runs": 351, "average": 25.07, "source_file": "nmcl stats/2005 1.tif"},

    {"season": 2005, "division": 1, "discipline": "bowling", "name": "P Hewart",
     "overs": "131", "maidens": 40, "runs_conceded": 360, "wickets": 38,
     "average": 9.47, "source_file": "nmcl stats/2005 2.tif"},
    {"season": 2005, "division": 1, "discipline": "bowling", "name": "S Carr",
     "overs": "154.3", "maidens": 29, "runs_conceded": 513, "wickets": 36,
     "average": 14.25, "source_file": "nmcl stats/2005 2.tif"},

    {"season": 2005, "division": 1, "discipline": "wicketkeeping", "name": "M Robinson",
     "catches": 19, "stumpings": 6, "average": None, "source_file": "nmcl stats/2005 2.tif"},
]


def parse_nmcl_stats():
    """Return the transcribed ELPM row list. See ELPM_ROWS' docstring above."""

    return ELPM_ROWS


def _resolve_elpm_team_id(store, division):
    """
    Look up the ELPM team_id a division maps to, by name -- NOT via
    the usual source_team_id path (this source has no numeric team ids
    of its own, and it's naming an existing team another source
    already created, not creating a new one). Team/club names are
    stable across a rebuild even though their autoincrement ids
    aren't, so this is safe to call at ingest time against whatever
    store already has ELPM's teams loaded from another source.

    Returns None (rather than guessing) if the division has no mapping
    or the target team doesn't exist yet in this store -- callers
    leave nmcl_season_stats.team_id NULL in that case; every row still
    gets inserted regardless, this only affects the optional team_id
    convenience link.
    """

    team_name = DIVISION_TEAM_NAMES.get(division)

    if team_name is None:
        return None

    row = store.conn.execute(
        """
        SELECT t.team_id
        FROM teams t
        JOIN clubs c ON c.club_id = t.club_id
        WHERE c.club_name LIKE 'East Lancs Paper Mill%'
          AND t.team_name LIKE '%' || ?
        """,
        (team_name,)
    ).fetchone()

    return row[0] if row else None


def _source_player_id(name):
    """
    A stable per-name key within this source, the same role a CricHQ
    name plays in crichq_pdf.py: no numeric id exists on these sheets,
    so the (normalised) printed name IS the source's own identifier.
    Reconciliation (reconcile/decisions.yaml) links it to an existing
    canonical player the same way it links any other source's name.
    """

    return re.sub(r"\s+", " ", name.strip()).upper()


def ingest_nmcl_stats(store, rows=None):
    """
    Upsert each row's player (source='nmcl_stats') and insert its
    season-aggregate stat row into nmcl_season_stats.

    Idempotent per (player_id, season, division, discipline) via that
    table's UNIQUE constraint -- re-running against a store that
    already has these rows raises IntegrityError rather than silently
    duplicating, the same "don't guess, fail loud" posture as the rest
    of this project.
    """

    if rows is None:
        rows = parse_nmcl_stats()

    inserted = 0

    for row in rows:

        source_player_id = _source_player_id(row["name"])
        player_id = store._upsert_player(SOURCE, source_player_id, row["name"])

        team_id = _resolve_elpm_team_id(store, row["division"])

        store.conn.execute(
            """
            INSERT INTO nmcl_season_stats (
                player_id, team_id, season, division, discipline,
                innings_played, not_outs, highest_score, highest_score_not_out, runs,
                overs, maidens, runs_conceded, wickets,
                catches, stumpings,
                average, source_club_code, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                player_id, team_id, row["season"], row["division"], row["discipline"],
                row.get("innings_played"), row.get("not_outs"), row.get("highest_score"),
                row.get("highest_score_not_out"), row.get("runs"),
                row.get("overs"), row.get("maidens"), row.get("runs_conceded"), row.get("wickets"),
                row.get("catches"), row.get("stumpings"),
                row.get("average"), ELPM_CLUB_CODE, row["source_file"],
            )
        )

        inserted += 1

    return inserted


if __name__ == "__main__":

    import argparse

    from sqlite_store import SQLiteStore

    parser = argparse.ArgumentParser(
        description="Ingest the transcribed NMCL 'Final Averages' ELPM rows into the SQLite store."
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")

    args = parser.parse_args()

    store = SQLiteStore(args.sqlite_db)

    rows = parse_nmcl_stats()
    count = ingest_nmcl_stats(store, rows)

    store.conn.commit()
    store.close()

    seasons = sorted(set(r["season"] for r in rows))
    print(f"Inserted {count} nmcl_season_stats rows for seasons {seasons}.")
