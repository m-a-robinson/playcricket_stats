#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
reconcile.py

Cross-source identity reconciliation for players, clubs, and teams.

Roadmap item 4 in full is automatic matching across every player/club/
team, still not built. This is deliberately smaller: explicit,
human-curated lists of "these (source, source_*_id) refs are the same
real player/club/team" groups (PLAYER_MERGES/CLUB_MERGES/TEAM_MERGES
below), applied by repointing their *_source_ids rows -- and every
fact-table row that referenced the now-redundant duplicate id -- onto
one surviving canonical row.

Clubs and teams also get a conservative *automatic* merge for free at
insert time (SQLiteStore._upsert_club()/._upsert_team(), keyed by a
casefolded, whitespace/"CC"-suffix-normalised name) -- see that
module's docstring. CLUB_MERGES/TEAM_MERGES here are for what that
can't safely guess at (e.g. "Bradshaw CC, Lancs" vs "Bradshaw CC", or
a club/team abbreviated differently per source) -- candidates for
which are surfaced by reconcile_audit.py, not found automatically.
Player identity has no automatic pass at all: names are far more
ambiguous (initials, nicknames, two different real people who happen
to share a surname+initial) than a club/team roster, so every
PLAYER_MERGES entry is a from-scratch human confirmation.

This is a real mechanism, not a query-time workaround: once merged,
the existing source-agnostic query layer (sqlite_queries.py) needs no
changes at all to return a combined career -- career_stats() already
aggregates by player_id alone, across every source, by design (see its
own docstring). Merging is what makes "by player_id alone" actually
mean "by real person" for an entry in PLAYER_MERGES.

Growing these lists with more groups, as more players/clubs/teams are
identified across sources (e.g. after importing further CricHQ PDFs --
run reconcile_audit.py first to find new candidates), is the intended
path towards fuller reconciliation -- not a replacement for automatic
matching, which is still on the roadmap.

Usage
-----
    python3 reconcile.py --sqlite-db demo.sqlite

Re-running is idempotent: a ref already merged into its group's
survivor is a no-op, and newly-ingested matches that reuse an
already-merged (source, source_*_id) resolve straight to the survivor
via the relevant *_source_ids table, without needing reconcile.py run
again for that ref.
"""

import sqlite3


# ==================================================================
# KNOWN MERGE GROUPS
# ==================================================================
#
# Each entry is one real person. `refs` are (source, source_player_id)
# pairs already loaded into player_source_ids (run the relevant
# ingestion script first). Only include refs actually confirmed to be
# the same person -- see the investigation notes below for why a
# same-named candidate was deliberately left out.

PLAYER_MERGES = [
    {
        "known_as": "Ian Wade",
        "refs": [
            ("play_cricket", "6216362"),
            ("crichq_pdf", "I Wade"),
            ("cricketstatz", "4"),
            # A second, single-match "I Wade" (cricketstatz id 1062,
            # 74 off the bowling on 09/08/2015, no other appearance
            # under that id) -- almost certainly the same player
            # re-entered under a second internal id at some point in
            # 13 years of manual club data entry, not a different
            # person. cricketstatz id 34 ("Wade,J") is a DIFFERENT
            # real person (different initial) and is correctly not
            # included here.
            ("cricketstatz", "1062"),
        ]
        # NOT included: crichq_pdf "I Wade/MR Robinson". That row only
        # ever appears as a fielder credit for one joint run-out ("run
        # out (I Wade/MR Robinson)") -- crichq_pdf.py's dismissal
        # parser keeps a multi-fielder run-out credit as one combined
        # name rather than crediting both players (the schema only has
        # one fielder_player_id slot per dismissal anyway). Merging it
        # in would wrongly also attribute MR Robinson's share of that
        # run-out to Ian Wade. Leaving it out slightly undercounts
        # Wade's run-out assists by one; that's a smaller, more honest
        # error than misattributing a joint credit to a single player.
    },
]

# Same idea, for clubs. Most cross-source club splits are already
# caught automatically at insert time (SQLiteStore._upsert_club(),
# keyed by a casefolded/whitespace/"CC"-suffix-normalised name) -- see
# that module's docstring. CLUB_MERGES here is for what that isn't
# safe to guess at (a dropped regional qualifier, a genuine
# abbreviation). Run reconcile_audit.py to find candidates; `refs` are
# (source, source_club_id) pairs.
CLUB_MERGES = [
    # e.g. {
    #     "known_as": "Bradshaw CC",
    #     "refs": [
    #         ("play_cricket", "<source_club_id>"),
    #         ("crichq_pdf", "Bradshaw CC, Lancs"),
    #     ],
    # },
]

# Same idea, for teams -- e.g. one source calling East Lancs Paper
# Mill's 1st XI "1st XI" and another calling it "ELPM 1st XI"; the
# automatic merge in SQLiteStore._upsert_team() only catches
# case/whitespace variants of an otherwise-identical name, scoped to
# teams already resolved to the same club. `refs` are (source,
# source_team_id) pairs.
TEAM_MERGES = [
]


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


def _merge_entities(
    conn, entity_table, id_column, source_table, source_id_column,
    source_refs, fact_id_columns, name_column, known_as=None
):
    """
    Shared machinery behind merge_players()/merge_clubs()/merge_teams():
    resolve each (source, source_id) ref to its own canonical row via
    `source_table`, then repoint every fact-table row (and the
    *_source_ids rows themselves) referencing a merged-away duplicate
    onto one surviving id -- the lowest of the resolved ids, for a
    deterministic result regardless of ref order.
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


def apply_merges(
    conn, player_merges=PLAYER_MERGES, club_merges=CLUB_MERGES, team_merges=TEAM_MERGES
):
    """Apply every group in each merge list, committing once at the end."""

    survivors = []

    # Clubs first: a club merge repoints teams.club_id, so any team
    # merge run afterwards sees the final club_id already in place.
    for merge in club_merges:
        survivor = merge_clubs(conn, merge["refs"], known_as=merge.get("known_as"))
        survivors.append(("club", merge.get("known_as"), survivor))

    for merge in team_merges:
        survivor = merge_teams(conn, merge["refs"], known_as=merge.get("known_as"))
        survivors.append(("team", merge.get("known_as"), survivor))

    for merge in player_merges:
        survivor = merge_players(conn, merge["refs"], known_as=merge.get("known_as"))
        survivors.append(("player", merge.get("known_as"), survivor))

    conn.commit()

    return survivors


# ==================================================================
# CLI
# ==================================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Apply known cross-source identity merges (PLAYER_MERGES/"
            "CLUB_MERGES/TEAM_MERGES) to the SQLite store."
        )
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")

    args = parser.parse_args()

    conn = sqlite3.connect(args.sqlite_db)
    conn.execute("PRAGMA foreign_keys = ON")

    for kind, known_as, survivor in apply_merges(conn):
        print(f"Merged: {known_as} -> {kind}_id {survivor}")

    conn.close()
