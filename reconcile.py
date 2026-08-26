#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
reconcile.py

Cross-source player identity reconciliation.

Roadmap item 4 in full is automatic matching across every player/club/
team, still not built. This is deliberately smaller: an explicit,
human-curated list of "these (source, source_player_id) refs are the
same real person" groups (PLAYER_MERGES below), applied by repointing
their player_source_ids rows -- and every fact-table row that
referenced the now-redundant duplicate player_id -- onto one surviving
canonical player.

This is a real mechanism, not a query-time workaround: once merged,
the existing source-agnostic query layer (sqlite_queries.py) needs no
changes at all to return a combined career -- career_stats() already
aggregates by player_id alone, across every source, by design (see its
own docstring). Merging is what makes "by player_id alone" actually
mean "by real person" for an entry in PLAYER_MERGES.

Growing PLAYER_MERGES with more groups, as more players are identified
across sources (e.g. after importing further CricHQ PDFs), is the
intended path towards fuller reconciliation -- not a replacement for
automatic matching, which is still on the roadmap.

Usage
-----
    python3 reconcile.py --sqlite-db demo.sqlite

Re-running is idempotent: a ref already merged into its group's
survivor is a no-op, and newly-ingested matches that reuse an
already-merged (source, source_player_id) resolve straight to the
survivor via player_source_ids, without needing reconcile.py run
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

    player_ids = []

    for source, source_player_id in source_refs:

        row = conn.execute(
            "SELECT player_id FROM player_source_ids WHERE source = ? AND source_player_id = ?",
            (source, str(source_player_id))
        ).fetchone()

        if row is None:
            raise ValueError(f"No player found for (source={source!r}, source_player_id={source_player_id!r})")

        player_ids.append(row[0])

    player_ids = sorted(set(player_ids))
    survivor = player_ids[0]
    duplicates = player_ids[1:]

    if known_as:
        conn.execute("UPDATE players SET known_as = ? WHERE player_id = ?", (known_as, survivor))

    for duplicate in duplicates:

        conn.execute(
            "UPDATE player_source_ids SET player_id = ? WHERE player_id = ?",
            (survivor, duplicate)
        )

        for table, column in _PLAYER_ID_COLUMNS:
            conn.execute(
                f"UPDATE {table} SET {column} = ? WHERE {column} = ?",
                (survivor, duplicate)
            )

        conn.execute("DELETE FROM players WHERE player_id = ?", (duplicate,))

    return survivor


def apply_merges(conn, merges=PLAYER_MERGES):
    """Apply every group in `merges`, committing once at the end."""

    survivors = []

    for merge in merges:

        survivor = merge_players(conn, merge["refs"], known_as=merge.get("known_as"))
        survivors.append((merge.get("known_as"), survivor))

    conn.commit()

    return survivors


# ==================================================================
# CLI
# ==================================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Apply known cross-source player identity merges (PLAYER_MERGES) to the SQLite store."
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")

    args = parser.parse_args()

    conn = sqlite3.connect(args.sqlite_db)
    conn.execute("PRAGMA foreign_keys = ON")

    for known_as, survivor in apply_merges(conn):
        print(f"Merged: {known_as} -> player_id {survivor}")

    conn.close()
