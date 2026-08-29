#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
club_awards.py

Ingests the club's own manually-curated honours -- league/cup wins,
season batting/bowling/wicketkeeping average winners, players' player
of the year, club captaincy -- into the SQLite store's `team_awards`/
`player_awards` tables (see schema.sql). Unlike every other ingestion
module in this project, there is no source file to parse: TEAM_AWARDS/
PLAYER_AWARDS below are transcribed directly from what the user knows
of the club's own history, the same "manually curated, not guessed at"
discipline `reconcile/decisions.yaml` follows for identity decisions.

Player identity is resolved by exact `known_as` match against the
canonical `players` table -- NOT via the usual `_upsert_player()`
source-id path, since an award isn't itself a data source with its own
per-source identifiers; it's a fact about a player who (should) already
exist in the store from a real source. This means **club_awards.py
must be run after `reconcile.py`**: before reconciliation, a name like
"Ian Wade" can exist as several unmerged rows across sources (see
development_notes.md), and `_resolve_player_id()` raises rather than
guessing which one an award belongs to. Team names are resolved the
same way, scoped to a club, via `_resolve_team_id()`.

Both ingest functions use `INSERT OR IGNORE`, keyed on each table's own
UNIQUE constraint (team_id/player_id, season, competition, award_name)
-- so re-running after adding a new season's honours to the lists below
is always a safe no-op for everything already stored, matching the
"safe to re-run" convention the rest of this project's ingestion
scripts follow.
"""

from sqlite_queries import ELPMCC_NAME


# ==================================================================
# TEAM HONOURS
# ==================================================================
#
# Every entry is the 1st XI unless team_name says otherwise -- NMCL/GMCL
# Division 1 is this club's 1st XI throughout its known history (see
# nmcl_stats.py's DIVISION_TEAM_NAMES), and every entry the user gave
# was this team.

TEAM_AWARDS = [
    {"season": 2003, "club_name": ELPMCC_NAME, "team_name": "1st XI",
     "competition": "NMCL Division 1", "award_name": "Winners"},
    {"season": 2012, "club_name": ELPMCC_NAME, "team_name": "1st XI",
     "competition": "NMCL Division 1", "award_name": "Winners"},
    {"season": 2013, "club_name": ELPMCC_NAME, "team_name": "1st XI",
     "competition": "NMCL Calverley Cup", "award_name": "Winners"},
    {"season": 2017, "club_name": ELPMCC_NAME, "team_name": "1st XI",
     "competition": "GMCL Division 4 N&W", "award_name": "Winners"},
]


# ==================================================================
# INDIVIDUAL HONOURS
# ==================================================================
#
# Season batting/bowling/wicketkeeping average winners and players'
# player of the year, plus club captaincy tenures expanded one row per
# season captained (e.g. "2011-2015 Ian Wade Club Captain" below
# becomes five rows, one per season) so a season lookup
# (player_awards(conn, season=...)) finds a serving captain the same
# way it finds any other single-season honour.

PLAYER_AWARDS = [
    {"season": 2012, "player_name": "Ian Wade",
     "competition": "NMCL", "award_name": "Batting Average Winner"},
    {"season": 2009, "player_name": "Ian Wade",
     "competition": "NMCL", "award_name": "Bowling Average Winner"},
    {"season": 2012, "player_name": "Ian Wade",
     "competition": "NMCL", "award_name": "Players' Player of the Year"},

    {"season": 2003, "player_name": "Mark Robinson",
     "competition": "NMCL Division 1", "award_name": "Wicketkeeping Winner"},
    {"season": 2005, "player_name": "Mark Robinson",
     "competition": "NMCL Division 1", "award_name": "Wicketkeeping Winner"},
    {"season": 2006, "player_name": "Mark Robinson",
     "competition": "NMCL Division 1", "award_name": "Wicketkeeping Winner"},
    {"season": 2016, "player_name": "Mark Robinson",
     "competition": "GMCL Division 4", "award_name": "Wicketkeeping Winner"},
    {"season": 2023, "player_name": "Mark Robinson",
     "competition": "GMCL Division 4", "award_name": "Wicketkeeping Winner"},
]

# Club captaincy tenures, as given (start-end season inclusive; a
# single season is its own one-year range). Kept separate from
# PLAYER_AWARDS above so the ranges stay readable, then flattened into
# the same shape (one row per season) below.
CAPTAINCY_TENURES = [
    {"player_name": "Ian Wade", "start_season": 2011, "end_season": 2015},
    {"player_name": "Mark Robinson", "start_season": 2006, "end_season": 2008},
    {"player_name": "Paul Hewart", "start_season": 2016, "end_season": 2018},
    # Canonical name is "Matty Partington" in reconcile/decisions.yaml
    # (the user gave "Matt Partington" -- same person, informal form).
    {"player_name": "Matty Partington", "start_season": 2021, "end_season": 2023},
    {"player_name": "Louis Birmingham", "start_season": 2020, "end_season": 2020},
    {"player_name": "Louis Birmingham", "start_season": 2024, "end_season": 2026},
]

for _tenure in CAPTAINCY_TENURES:
    for _season in range(_tenure["start_season"], _tenure["end_season"] + 1):
        PLAYER_AWARDS.append({
            "season": _season,
            "player_name": _tenure["player_name"],
            "competition": "Club",
            "award_name": "Captain",
        })


def _resolve_team_id(store, club_name, team_name):
    """
    Look up an existing team_id for (club_name, team_name). Matches on
    a trailing-substring LIKE, the same "%<name>" pattern
    nmcl_stats.py's _resolve_elpm_team_id() uses, rather than an exact
    string -- team-name reconciliation across sources is a manual,
    incomplete pass (see reconcile_audit.py's team-split candidates in
    development_notes.md), so this club's 1st XI can legitimately still
    be two different canonical rows today, "1st XI" (some sources) and
    "East Lancs Paper Mill CC 1st XI" (others, club-prefixed) -- both of
    which end in "1st XI". Raises ValueError (rather than silently
    skipping or guessing) if that finds zero or more than one team, since
    either case means the award can't be attached to exactly one row
    without a human deciding which.
    """

    rows = store.conn.execute(
        """
        SELECT t.team_id, t.team_name
        FROM teams t
        JOIN clubs c ON c.club_id = t.club_id
        WHERE c.club_name = ? AND t.team_name LIKE '%' || ?
        """,
        (club_name, team_name)
    ).fetchall()

    if len(rows) == 0:
        raise ValueError(
            f"No team ending in {team_name!r} found for club {club_name!r} -- "
            "build/ingest the store first, or check the club/team name."
        )

    if len(rows) > 1:
        names = [r[1] for r in rows]
        raise ValueError(
            f"{team_name!r} for club {club_name!r} matches {len(rows)} teams "
            f"({names}) -- not yet merged into one canonical team (see "
            "reconcile/decisions.yaml's teams: section). Merge them first, "
            "or attach the award to the specific team_name that survives."
        )

    return rows[0][0]


def _resolve_player_id(store, player_name):
    """
    Look up an existing canonical player_id by exact `known_as` match.

    Deliberately does not create a new player or guess between
    candidates: raises ValueError if the name matches zero or more than
    one player row, since either case means reconcile.py needs running
    (or re-running against a fresh decisions.yaml) before awards can be
    attached unambiguously -- see the module docstring.
    """

    rows = store.conn.execute(
        "SELECT player_id FROM players WHERE known_as = ?",
        (player_name,)
    ).fetchall()

    if len(rows) == 0:
        raise ValueError(
            f"No player named {player_name!r} found in the store -- "
            "ingest the relevant source(s) and run reconcile.py first."
        )

    if len(rows) > 1:
        ids = [r[0] for r in rows]
        raise ValueError(
            f"{player_name!r} matches {len(rows)} player rows ({ids}) -- "
            "not yet merged into one canonical player. Run reconcile.py "
            "(with an up-to-date reconcile/decisions.yaml) before "
            "attaching awards to this name."
        )

    return rows[0][0]


def ingest_team_awards(store, rows=None):
    """Insert each row into team_awards. Safe to re-run (INSERT OR IGNORE)."""

    if rows is None:
        rows = TEAM_AWARDS

    inserted = 0

    for row in rows:
        team_id = _resolve_team_id(store, row["club_name"], row["team_name"])

        cursor = store.conn.execute(
            """
            INSERT OR IGNORE INTO team_awards
                (team_id, season, competition, award_name, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (team_id, row["season"], row["competition"], row["award_name"], row.get("notes"))
        )

        if cursor.rowcount:
            inserted += 1

    return inserted


def ingest_player_awards(store, rows=None):
    """Insert each row into player_awards. Safe to re-run (INSERT OR IGNORE)."""

    if rows is None:
        rows = PLAYER_AWARDS

    inserted = 0

    for row in rows:
        player_id = _resolve_player_id(store, row["player_name"])

        cursor = store.conn.execute(
            """
            INSERT OR IGNORE INTO player_awards
                (player_id, season, competition, award_name, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (player_id, row["season"], row["competition"], row["award_name"], row.get("notes"))
        )

        if cursor.rowcount:
            inserted += 1

    return inserted


if __name__ == "__main__":

    import argparse

    from sqlite_store import SQLiteStore

    parser = argparse.ArgumentParser(
        description=(
            "Ingest manually-curated club/team/player honours into the SQLite "
            "store. Run this after reconcile.py, once every player named "
            "below is a single canonical row."
        )
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")

    args = parser.parse_args()

    store = SQLiteStore(args.sqlite_db)

    team_count = ingest_team_awards(store)
    player_count = ingest_player_awards(store)

    store.conn.commit()
    store.close()

    print(f"Inserted {team_count} new team_awards row(s), {player_count} new player_awards row(s).")
