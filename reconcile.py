#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
reconcile.py

Cross-source identity reconciliation for players, clubs, teams, and
grounds, plus club-home-ground overrides for a source whose own
per-match venue text is too vague to use directly (CricHQ).

Roadmap item 4 in full is automatic matching across every player/club/
team/ground, still not built. This is deliberately smaller: explicit,
human-curated decisions -- "these (source, source_*_id) refs are the
same real player/club/team/ground", or "this club's home ground is X" --
read from reconcile/decisions.yaml (see that file's own header for what
belongs in it and how to edit it) and applied here by repointing
*_source_ids rows -- and every fact-table row that referenced the
now-redundant duplicate id -- onto one surviving canonical row.

Clubs, teams, and grounds also get a conservative *automatic* merge for
free at insert time (SQLiteStore._upsert_club()/._upsert_team()/
._upsert_ground(), keyed by a casefolded, whitespace/"CC"-suffix-
normalised name) -- see that module's docstring. The merge lists in
decisions.yaml are for what that can't safely guess at (e.g. "Bradshaw
CC, Lancs" vs "Bradshaw CC", or "ELPMCC" vs "Croft Lane, ELPM") --
candidates for which are surfaced by reconcile_audit.py, not found
automatically. Player identity has no automatic pass at all: names are
far more ambiguous (initials, nicknames, two different real people who
happen to share a surname+initial) than a club/team/ground name, so
every player decision is a from-scratch human confirmation.

This is a real mechanism, not a query-time workaround: once merged, the
existing source-agnostic query layer (sqlite_queries.py) needs no
changes at all to return a combined career -- career_stats() already
aggregates by player_id alone, across every source, by design (see its
own docstring). Merging is what makes "by player_id alone" actually
mean "by real person" for an entry in decisions.yaml.

Usage
-----
    python3 reconcile.py --sqlite-db demo.sqlite
    python3 reconcile.py --sqlite-db demo.sqlite --decisions reconcile/decisions.yaml

Re-running is idempotent: a ref already merged into its group's
survivor is a no-op, and newly-ingested matches that reuse an
already-merged (source, source_*_id) resolve straight to the survivor
via the relevant *_source_ids table, without needing reconcile.py run
again for that ref. Ground overrides are also idempotent -- they just
set matches.ground_id/ground_name to the same resolved values again.
"""

import argparse
import os
import sqlite3

import yaml


DEFAULT_DECISIONS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "reconcile", "decisions.yaml"
)


def _as_ref_tuples(merge_entries):
    """
    decisions.yaml writes each ref as {source: ..., id: ...} for
    readability -- _merge_entities()/merge_*() expect plain
    (source, id) tuples, matching PLAYER_MERGES' old shape.
    """

    for entry in merge_entries:
        entry["refs"] = [(ref["source"], ref["id"]) for ref in entry["refs"]]

    return merge_entries


def load_decisions(path=DEFAULT_DECISIONS_PATH):
    """
    Read reconcile/decisions.yaml. Missing optional sections default to
    empty so a decisions file doesn't need to spell out every section
    it isn't using.
    """

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return {
        "players": _as_ref_tuples(data.get("players") or []),
        "clubs": _as_ref_tuples(data.get("clubs") or []),
        "teams": _as_ref_tuples(data.get("teams") or []),
        "grounds": _as_ref_tuples(data.get("grounds") or []),
        "club_home_grounds": data.get("club_home_grounds") or [],
        "ground_overrides": data.get("ground_overrides") or [],
    }


# ==================================================================
# MERGE
# ==================================================================

# Every column across the schema that references players.player_id,
# beyond player_source_ids itself.
_PLAYER_ID_COLUMNS = [
    ("batting_innings", "player_id"),
    ("batting_innings", "bowler_player_id"),
    ("batting_innings", "fielder_player_id"),
    ("bowling_innings", "player_id"),
    ("match_appearances", "player_id"),
]

# Every column that references clubs.club_id, beyond club_source_ids.
_CLUB_ID_COLUMNS = [
    ("teams", "club_id"),
    ("club_grounds", "club_id"),
]

# Every column that references teams.team_id, beyond team_source_ids.
_TEAM_ID_COLUMNS = [
    ("matches", "home_team_id"),
    ("matches", "away_team_id"),
    ("matches", "toss_won_by_team_id"),
    ("matches", "result_applied_to"),
    ("innings", "team_batting_id"),
    ("batting_innings", "team_id"),
    ("bowling_innings", "team_id"),
    ("match_appearances", "team_id"),
]

# Every column that references grounds.ground_id, beyond ground_source_ids.
_GROUND_ID_COLUMNS = [
    ("matches", "ground_id"),
    ("club_grounds", "ground_id"),
]


def _merge_entities(
    conn, entity_table, id_column, source_table, source_id_column,
    source_refs, fact_id_columns, name_column, known_as=None
):
    """
    Shared machinery behind merge_players()/merge_clubs()/merge_teams()/
    merge_grounds(): resolve each (source, source_id) ref to its own
    canonical row via `source_table`, then repoint every fact-table row
    (and the *_source_ids rows themselves) referencing a merged-away
    duplicate onto one surviving id -- the lowest of the resolved ids,
    for a deterministic result regardless of ref order.
    """

    ids = []

    for source, source_id in source_refs:

        row = conn.execute(
            f"SELECT {id_column} FROM {source_table} WHERE source = ? AND {source_id_column} = ?",
            (source, str(source_id))
        ).fetchone()

        if row is None:
            raise ValueError(
                f"No {entity_table[:-1]} found for "
                f"(source={source!r}, {source_id_column}={source_id!r})"
            )

        ids.append(row[0])

    ids = sorted(set(ids))
    survivor = ids[0]
    duplicates = ids[1:]

    if known_as:
        conn.execute(
            f"UPDATE {entity_table} SET {name_column} = ? WHERE {id_column} = ?",
            (known_as, survivor)
        )

    for duplicate in duplicates:

        conn.execute(
            f"UPDATE {source_table} SET {id_column} = ? WHERE {id_column} = ?",
            (survivor, duplicate)
        )

        for table, column in fact_id_columns:
            conn.execute(
                f"UPDATE {table} SET {column} = ? WHERE {column} = ?",
                (survivor, duplicate)
            )

        conn.execute(f"DELETE FROM {entity_table} WHERE {id_column} = ?", (duplicate,))

    return survivor


def merge_players(conn, source_refs, known_as=None):
    """
    Merge multiple (source, source_player_id) refs -- each already
    pointing at its own canonical player row -- onto a single
    surviving canonical player_id.

    Every fact-table row referencing a merged-away duplicate is
    repointed at the survivor, the duplicate's player_source_ids rows
    are repointed too, and the now-unreferenced duplicate player rows
    are deleted.

    Parameters
    ----------
    conn : sqlite3.Connection
    source_refs : list of (source, source_player_id) tuples
    known_as : str, optional
        Display name for the surviving player row. Defaults to
        whatever known_as it already has.

    Returns
    -------
    int
        The surviving player_id.
    """

    return _merge_entities(
        conn, "players", "player_id", "player_source_ids", "source_player_id",
        source_refs, _PLAYER_ID_COLUMNS, "known_as", known_as
    )


def merge_clubs(conn, source_refs, known_as=None):
    """Merge (source, source_club_id) refs onto one surviving club_id -- see merge_players()."""

    return _merge_entities(
        conn, "clubs", "club_id", "club_source_ids", "source_club_id",
        source_refs, _CLUB_ID_COLUMNS, "club_name", known_as
    )


def merge_teams(conn, source_refs, known_as=None):
    """Merge (source, source_team_id) refs onto one surviving team_id -- see merge_players()."""

    return _merge_entities(
        conn, "teams", "team_id", "team_source_ids", "source_team_id",
        source_refs, _TEAM_ID_COLUMNS, "team_name", known_as
    )


def merge_grounds(conn, source_refs, known_as=None):
    """Merge (source, source_ground_key) refs onto one surviving ground_id -- see merge_players()."""

    return _merge_entities(
        conn, "grounds", "ground_id", "ground_source_ids", "source_ground_key",
        source_refs, _GROUND_ID_COLUMNS, "ground_name", known_as
    )


# ==================================================================
# CLUB HOME GROUNDS / GROUND OVERRIDES
# ==================================================================

def _resolve_club_id(conn, club_name):

    row = conn.execute(
        "SELECT club_id FROM clubs WHERE club_name = ?", (club_name,)
    ).fetchone()

    if row is None:
        raise ValueError(f"No club found named {club_name!r}")

    return row[0]


def _resolve_ground_id(conn, ground_name):

    row = conn.execute(
        "SELECT ground_id FROM grounds WHERE ground_name = ?", (ground_name,)
    ).fetchone()

    if row is None:
        raise ValueError(f"No ground found named {ground_name!r}")

    return row[0]


def apply_club_home_grounds(conn, club_home_grounds):
    """
    Populate club_grounds from decisions.yaml's club_home_grounds
    section -- a plain fact, not a merge. Idempotent (INSERT OR IGNORE
    on the (club_id, ground_id) primary key).
    """

    applied = []

    for entry in club_home_grounds:

        club_id = _resolve_club_id(conn, entry["club"])
        ground_id = _resolve_ground_id(conn, entry["ground"])

        conn.execute(
            "INSERT OR IGNORE INTO club_grounds (club_id, ground_id, is_home) VALUES (?, ?, 1)",
            (club_id, ground_id)
        )

        applied.append((entry["club"], entry["ground"]))

    return applied


def apply_ground_overrides(conn, ground_overrides):
    """
    Apply decisions.yaml's ground_overrides: for each rule, set
    matches.ground_id (and, if overwrite_name is set, ground_name too)
    on every match from `when.source` where `when.home_club` is the
    HOME side. Only touches matches whose current ground_id doesn't
    already point at the target ground, so re-running is a no-op.
    """

    applied = []

    for rule in ground_overrides:

        when = rule["when"]
        ground_id = _resolve_ground_id(conn, rule["ground"])
        overwrite_name = bool(rule.get("overwrite_name"))

        params = [ground_id]
        set_clause = "ground_id = ?"

        if overwrite_name:
            set_clause += ", ground_name = ?"
            params.append(rule["ground"])

        params.extend([when["source"], when["home_club"], ground_id])

        cursor = conn.execute(
            f"""
            UPDATE matches
            SET {set_clause}
            WHERE source = ?
              AND home_team_id IN (
                  SELECT t.team_id FROM teams t
                  JOIN clubs c ON c.club_id = t.club_id
                  WHERE c.club_name = ?
              )
              AND (ground_id IS NULL OR ground_id != ?)
            """,
            params
        )

        applied.append((when["source"], when["home_club"], rule["ground"], cursor.rowcount))

    return applied


# ==================================================================
# APPLY EVERYTHING
# ==================================================================

def apply_decisions(conn, decisions=None, decisions_path=DEFAULT_DECISIONS_PATH):
    """
    Apply every section of decisions.yaml, committing once at the end.
    `rejected` is deliberately not read here -- it's never applied,
    only used by reconcile_audit.py to keep already-reviewed candidates
    out of its "new candidates" section.
    """

    if decisions is None:
        decisions = load_decisions(decisions_path)

    survivors = []

    # Clubs first: a club merge repoints teams.club_id and
    # club_grounds.club_id, so anything run afterwards sees the final
    # club_id already in place.
    for merge in decisions["clubs"]:
        survivor = merge_clubs(conn, merge["refs"], known_as=merge.get("canonical_name"))
        survivors.append(("club", merge.get("canonical_name"), survivor))

    for merge in decisions["teams"]:
        survivor = merge_teams(conn, merge["refs"], known_as=merge.get("canonical_name"))
        survivors.append(("team", merge.get("canonical_name"), survivor))

    for merge in decisions["grounds"]:
        survivor = merge_grounds(conn, merge["refs"], known_as=merge.get("canonical_name"))
        survivors.append(("ground", merge.get("canonical_name"), survivor))

    for merge in decisions["players"]:
        survivor = merge_players(conn, merge["refs"], known_as=merge.get("canonical_name"))
        survivors.append(("player", merge.get("canonical_name"), survivor))

    # Club home grounds and ground overrides need clubs/grounds already
    # merged above, so they run last.
    apply_club_home_grounds(conn, decisions["club_home_grounds"])
    override_results = apply_ground_overrides(conn, decisions["ground_overrides"])

    conn.commit()

    return survivors, override_results


# ==================================================================
# CLI
# ==================================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Apply reconcile/decisions.yaml (player/club/team/ground merges, "
            "club home grounds, ground overrides) to the SQLite store."
        )
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")
    parser.add_argument("--decisions", default=DEFAULT_DECISIONS_PATH)

    args = parser.parse_args()

    conn = sqlite3.connect(args.sqlite_db)
    conn.execute("PRAGMA foreign_keys = ON")

    survivors, override_results = apply_decisions(conn, decisions_path=args.decisions)

    for kind, canonical_name, survivor in survivors:
        print(f"Merged: {canonical_name} -> {kind}_id {survivor}")

    for source, home_club, ground, rowcount in override_results:
        print(f"Ground override: {source} / {home_club} -> {ground!r} ({rowcount} matches updated)")

    conn.close()
