#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
reconcile_audit.py

Generates a human-readable Markdown report of two things, over an
already-built SQLite store:

1. A data-quality scan -- distinct competitions/leagues, grounds,
   seasons/date ranges, and suspicious/placeholder values -- so someone
   can eyeball the fields stats get filtered/grouped by (the same
   fields career_stats()/SQLPlayerStats query on) before trusting them.
2. Reconciliation candidates -- clubs, teams, and players that look
   like they might be the same real thing split across two or more
   canonical rows, but aren't safe to merge automatically. SQLiteStore
   already auto-merges exact/near-exact club and team names at insert
   time (see its docstring); what's left here is the fuzzier residue,
   plus players, which get no automatic merging at all.

This script never writes to the database. It only reads and reports.
Confirmed candidates are turned into permanent decisions by hand, added
to reconcile.py's PLAYER_MERGES/CLUB_MERGES/TEAM_MERGES using the
(source, source_*_id) refs listed under each candidate -- then
`python3 reconcile.py --sqlite-db <path>` applies them. Re-run this
script (it's cheap and disposable, not version-controlled output in
itself beyond whatever snapshot you choose to commit) any time after
ingesting a new source or fixing a parser bug, to see what's changed.

Usage
-----
    python3 reconcile_audit.py --sqlite-db playcricket_stats.sqlite \
        --out reconcile/data_quality_report.md

Everything here is a *suggestion* for a human to confirm or reject --
none of it is applied automatically, and false positives (two
different real people/clubs/teams that happen to look similar) are
expected and fine; that's exactly what the human review step is for.
"""

import argparse
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher

from sqlite_store import SQLiteStore


# ==================================================================
# NAME NORMALISATION
# ==================================================================

def _normalise_loose(name):
    """Casefold, alphanumeric-only key -- for exact-after-noise comparisons."""

    return re.sub(r"[^a-z0-9]", "", (name or "").casefold())


def _first_initial_surname(name):
    """
    (first-initial, surname) for a "<initial(s)> <Surname>"-shaped
    cricket scorecard name, e.g. "I Wade" / "Ian Wade" -> ("i", "wade").
    Returns None for anything that doesn't look like that shape (single
    token, punctuation-only, etc.) rather than guessing. Requires the
    *surname* to match exactly (see caller) -- deliberately not fuzzy,
    since a fuzzy surname match on top of an already-fuzzy shape check
    compounds into too many false positives (unrelated people who just
    share an initial and a similar-looking surname).
    """

    tokens = re.sub(r"[^\w\s'-]", "", name or "").split()

    if len(tokens) < 2:
        return None

    return tokens[0][0].casefold(), tokens[-1].casefold()


def _club_base_name(name):
    """
    A looser-than-SQLiteStore key for club-merge *candidates*: on top
    of its exact-merge normalisation (casefold, whitespace, "CC"/
    "Cricket Club" suffix), also drops one trailing ", <qualifier>"
    clause -- e.g. "Bradshaw CC, Lancs" -> "bradshaw", matching
    "Bradshaw CC" -> "bradshaw". Still exact-equality only when used
    for clustering (see render_club_candidates) -- no containment, no
    fuzzy ratio: a bare substring/similarity check on club names is
    what produced "Shaw CC" / "Bradshaw CC" / "Walshaw CC" as a false
    "duplicate" during development (short club names that are
    substrings of, or resemble, completely different real clubs).
    """

    name = re.sub(r",\s*[^,]+$", "", name or "")
    return SQLiteStore._normalise_club_name(name)


def _digits(s):
    return re.findall(r"\d+", s)


def _digit_conflict(a, b):
    """
    True if both strings contain a number and the numbers differ --
    "Prestwich 2nd XI" vs "Prestwich 3rd XI" should never be treated as
    a likely typo of each other, however similar the surrounding text:
    a differing ordinal/number is exactly what makes two teams (or two
    competitions/cups) genuinely different, not a spelling variant.
    """

    da, db = _digits(a), _digits(b)
    return bool(da) and bool(db) and da != db


def _similar(a, b, threshold=0.82):

    if _digit_conflict(a, b):
        return False

    return SequenceMatcher(None, a, b).ratio() >= threshold


# ==================================================================
# PART 1 -- DATA QUALITY SCAN
# ==================================================================

def _scan_value_counts(conn, table, column, min_count_to_flag=1):
    """
    Distinct values of one column plus how many matches carry each,
    sorted rarest-first (a value only ever seen once or twice is a
    plausible typo/one-off worth a second look).
    """

    rows = conn.execute(
        f"""
        SELECT {column}, COUNT(*) AS n
        FROM {table}
        WHERE {column} IS NOT NULL AND TRIM({column}) != ''
        GROUP BY {column}
        ORDER BY n ASC, {column} ASC
        """
    ).fetchall()

    return [(value, n) for value, n in rows]


def render_data_quality_section(conn):

    lines = ["## Part 1 -- Data quality scan", ""]
    lines.append(
        "Distinct values actually sitting in fields career stats/leaderboards "
        "group or filter by. Rarest-first within each table, so a likely "
        "typo or one-off surfaces near the top."
    )
    lines.append("")

    # ---- Competitions ----

    lines.append("### Competitions")
    lines.append("")
    comps = _scan_value_counts(conn, "matches", "competition_name")
    lines.append(f"{len(comps)} distinct values, {sum(n for _, n in comps)} matches with one set.")
    lines.append("")
    lines.append("| Competition | Matches |")
    lines.append("|---|---|")
    for value, n in comps:
        lines.append(f"| {value} | {n} |")
    lines.append("")

    # ---- Leagues ----

    lines.append("### Leagues")
    lines.append("")
    leagues = _scan_value_counts(conn, "matches", "league_name")
    lines.append(f"{len(leagues)} distinct values, {sum(n for _, n in leagues)} matches with one set.")
    lines.append("")
    lines.append("| League | Matches |")
    lines.append("|---|---|")
    for value, n in leagues:
        lines.append(f"| {value} | {n} |")
    lines.append("")

    # ---- Grounds ----

    lines.append("### Grounds")
    lines.append("")
    grounds = _scan_value_counts(conn, "matches", "ground_name")
    lines.append(f"{len(grounds)} distinct values, {sum(n for _, n in grounds)} matches with one set.")
    lines.append("")
    lines.append("| Ground | Matches |")
    lines.append("|---|---|")
    for value, n in grounds:
        lines.append(f"| {value} | {n} |")
    lines.append("")

    # ---- Seasons / date ranges ----

    lines.append("### Seasons")
    lines.append("")
    lines.append(
        "One row per (season, source): match count and the match_date range "
        "actually seen, so a season whose dates don't look right (wrong "
        "year, implausible span) stands out."
    )
    lines.append("")
    lines.append("| Season | Source | Matches | Earliest | Latest |")
    lines.append("|---|---|---|---|---|")

    season_rows = conn.execute(
        """
        SELECT season, source, COUNT(*), MIN(match_date), MAX(match_date)
        FROM matches
        GROUP BY season, source
        ORDER BY season, source
        """
    ).fetchall()

    for season, source, n, earliest, latest in season_rows:
        lines.append(f"| {season} | {source} | {n} | {earliest or '?'} | {latest or '?'} |")
    lines.append("")

    # Flag a match whose match_date year disagrees with its stored season.

    mismatches = conn.execute(
        """
        SELECT source, source_match_id, season, match_date
        FROM matches
        WHERE match_date IS NOT NULL
          AND TRIM(match_date) != ''
          AND CAST(substr(match_date, -4) AS INTEGER) != season
        """
    ).fetchall()

    if mismatches:
        lines.append(f"**{len(mismatches)} matches where match_date's year disagrees with `season`:**")
        lines.append("")
        lines.append("| Source | source_match_id | season | match_date |")
        lines.append("|---|---|---|---|")
        for source, source_match_id, season, match_date in mismatches:
            lines.append(f"| {source} | {source_match_id} | {season} | {match_date} |")
        lines.append("")

    # ---- Suspicious / placeholder values ----

    lines.append("### Suspicious or placeholder values")
    lines.append("")
    lines.append(
        "Rows crichq_pdf.py synthesises when a match's team names couldn't "
        "be recovered from the PDF text at all (a genuinely abandoned match "
        "with no batting/bowling either) -- see the README's CricHQ section. "
        "These carry no real identity and will never merge with anything; "
        "listed here so they're not mistaken for a parsing bug. Excluded from "
        "the club/team candidate clustering below for the same reason -- two "
        "different placeholder matches must never be suggested as the same "
        "club/team. (One cosmetic side effect: `_split_team_name()`'s naive "
        "\"last comma\" split puts the `Team A`/`Team B` half of the "
        "placeholder into the *team* name rather than the club name, so "
        "home/away placeholder \"clubs\" for the same synthesised match "
        "collapse into one club_id with two team_ids under it -- harmless, "
        "since there's no batting/bowling/player data attached either way.)"
    )
    lines.append("")

    placeholders = conn.execute(
        "SELECT club_id, club_name FROM clubs WHERE club_name LIKE 'Unknown (%'"
    ).fetchall()

    if placeholders:
        lines.append("| club_id | club_name |")
        lines.append("|---|---|")
        for club_id, club_name in placeholders:
            lines.append(f"| {club_id} | {club_name} |")
    else:
        lines.append("None found.")
    lines.append("")

    short_names = conn.execute(
        """
        SELECT 'club', club_id, club_name FROM clubs WHERE LENGTH(TRIM(club_name)) <= 2
        UNION ALL
        SELECT 'team', team_id, team_name FROM teams WHERE LENGTH(TRIM(team_name)) <= 2
        UNION ALL
        SELECT 'player', player_id, known_as FROM players WHERE LENGTH(TRIM(known_as)) <= 2
        """
    ).fetchall()

    lines.append("**Names two characters or shorter (likely a parsing artefact, not a real name):**")
    lines.append("")
    if short_names:
        lines.append("| Kind | id | Name |")
        lines.append("|---|---|---|")
        for kind, entity_id, name in short_names:
            lines.append(f"| {kind} | {entity_id} | {name!r} |")
    else:
        lines.append("None found.")
    lines.append("")

    return lines


# ==================================================================
# PART 2 -- RECONCILIATION CANDIDATES
# ==================================================================

def _club_source_refs(conn, club_id):
    return conn.execute(
        "SELECT source, source_club_id FROM club_source_ids WHERE club_id = ?",
        (club_id,)
    ).fetchall()


def _team_source_refs(conn, team_id):
    return conn.execute(
        "SELECT source, source_team_id FROM team_source_ids WHERE team_id = ?",
        (team_id,)
    ).fetchall()


def _player_source_refs(conn, player_id):
    return conn.execute(
        "SELECT source, source_player_id FROM player_source_ids WHERE player_id = ?",
        (player_id,)
    ).fetchall()


def _player_appearance_count(conn, player_id):
    row = conn.execute(
        "SELECT COUNT(DISTINCT match_id) FROM match_appearances WHERE player_id = ?",
        (player_id,)
    ).fetchone()
    return row[0] if row else 0


def render_club_candidates(conn):

    lines = ["### Clubs", ""]
    lines.append(
        "Grouped by exact match on a looser key than SQLiteStore's own "
        "automatic merge (see `_club_base_name()`) -- e.g. a trailing "
        "regional qualifier stripped in addition to the \"CC\" suffix. "
        "Deliberately exact-equality only, not fuzzy/substring matching: "
        "short club names being substrings of unrelated ones (\"Shaw\" vs "
        "\"Bradshaw\" vs \"Walshaw\" -- three different real clubs) made "
        "that too unreliable during development to trust even as a "
        "suggestion."
    )
    lines.append("")

    rows = conn.execute(
        "SELECT club_id, club_name FROM clubs WHERE club_name NOT LIKE 'Unknown (%'"
    ).fetchall()

    groups = defaultdict(list)
    for club_id, club_name in rows:
        key = _club_base_name(club_name)
        if key:
            groups[key].append((club_id, club_name))

    clusters = [group for group in groups.values() if len(group) > 1]

    if not clusters:
        lines.append("None found -- SQLiteStore's automatic name-based merge (see its docstring) "
                      "already caught every case in the current data.")
        lines.append("")
        return lines

    lines.append(f"{len(clusters)} candidate group(s) not already unified automatically:")
    lines.append("")

    for group in clusters:

        names = ", ".join(f"{name!r} (club_id {cid})" for cid, name in group)
        lines.append(f"- **{names}**")

        for cid, name in group:
            refs = _club_source_refs(conn, cid)
            ref_text = ", ".join(f"(\"{s}\", \"{sid}\")" for s, sid in refs)
            lines.append(f"  - club_id {cid}: {ref_text}")

        all_refs = [ref for cid, _ in group for ref in _club_source_refs(conn, cid)]
        refs_literal = ",\n        ".join(f"(\"{s}\", \"{sid}\")" for s, sid in all_refs)
        lines.append("  - if confirmed, add to `CLUB_MERGES` in reconcile.py:")
        lines.append("    ```python")
        lines.append("    {")
        lines.append(f"        \"known_as\": {group[0][1]!r},")
        lines.append(f"        \"refs\": [\n        {refs_literal}\n        ],")
        lines.append("    },")
        lines.append("    ```")
        lines.append("")

    return lines


def _near_duplicate_clusters_ids(id_name_pairs):
    """
    Loose-normalised-key clusters among (id, name) pairs, allowing
    containment ("1st XI" within "ELPM 1st XI") as well as exact match
    and high string similarity -- used for TEAM names only, and only
    ever called scoped to one club_id at a time (see
    render_team_candidates()), so the blast radius of a false positive
    is contained to that one club's own teams rather than spanning the
    whole dataset the way it would for club names (see
    render_club_candidates() for why that's handled differently). Still
    guards against a differing ordinal/number ("2nd XI" vs "3rd XI")
    ever counting as a match -- see _digit_conflict().
    """

    clusters = []
    used = set()

    for i, (id_a, name_a) in enumerate(id_name_pairs):

        if id_a in used:
            continue

        norm_a = _normalise_loose(name_a)
        group = [(id_a, name_a)]

        for id_b, name_b in id_name_pairs[i + 1:]:

            if id_b in used:
                continue

            norm_b = _normalise_loose(name_b)

            if not norm_a or not norm_b:
                continue

            if _digit_conflict(norm_a, norm_b):
                continue

            if norm_a == norm_b or norm_a in norm_b or norm_b in norm_a or _similar(norm_a, norm_b):
                group.append((id_b, name_b))
                used.add(id_b)

        if len(group) > 1:
            used.add(id_a)
            clusters.append(group)

    return clusters


def render_team_candidates(conn):

    lines = ["### Teams", ""]

    clubs = conn.execute(
        "SELECT club_id, club_name FROM clubs WHERE club_name NOT LIKE 'Unknown (%'"
    ).fetchall()
    all_clusters = []

    for club_id, club_name in clubs:

        teams = conn.execute(
            "SELECT team_id, team_name FROM teams WHERE club_id = ?", (club_id,)
        ).fetchall()

        for group in _near_duplicate_clusters_ids(teams):
            all_clusters.append((club_id, club_name, group))

    if not all_clusters:
        lines.append("None found.")
        lines.append("")
        return lines

    lines.append(f"{len(all_clusters)} candidate group(s), within a single club each:")
    lines.append("")

    for club_id, club_name, group in all_clusters:

        names = ", ".join(f"{name!r} (team_id {tid})" for tid, name in group)
        lines.append(f"- **{club_name}** (club_id {club_id}): {names}")

        for tid, name in group:
            refs = _team_source_refs(conn, tid)
            ref_text = ", ".join(f"(\"{s}\", \"{sid}\")" for s, sid in refs)
            lines.append(f"  - team_id {tid}: {ref_text}")

        all_refs = [ref for tid, _ in group for ref in _team_source_refs(conn, tid)]
        refs_literal = ",\n        ".join(f"(\"{s}\", \"{sid}\")" for s, sid in all_refs)
        lines.append("  - if confirmed, add to `TEAM_MERGES` in reconcile.py:")
        lines.append("    ```python")
        lines.append("    {")
        lines.append(f"        \"known_as\": {group[0][1]!r},")
        lines.append(f"        \"refs\": [\n        {refs_literal}\n        ],")
        lines.append("    },")
        lines.append("    ```")
        lines.append("")

    return lines


def render_player_candidates(conn):

    lines = ["### Players", ""]
    lines.append(
        "Player identity gets no automatic merging at all (see reconcile.py's "
        "docstring) -- everything below is a suggestion only. A shared "
        "initial+surname is common and does NOT mean the same person; "
        "check appearance counts, dates, and sources before confirming."
    )
    lines.append("")

    players = conn.execute("SELECT player_id, known_as FROM players").fetchall()

    # ---- Section A: identical after stripping case/whitespace/punctuation ----

    loose_groups = defaultdict(list)
    for pid, name in players:
        loose_groups[_normalise_loose(name)].append((pid, name))

    exact_clusters = [
        group for group in loose_groups.values()
        if len(group) > 1 and len({name for _, name in group}) > 1
    ]

    def _evidence(group):
        return sum(_player_appearance_count(conn, pid) for pid, _ in group)

    exact_clusters.sort(key=_evidence, reverse=True)

    lines.append(f"#### Same name, different spelling of whitespace/case/punctuation only ({len(exact_clusters)} groups)")
    lines.append("")

    for group in exact_clusters:

        evidence = _evidence(group)
        lines.append(f"- {' / '.join(repr(n) for _, n in group)} -- {evidence} combined appearances")

        for pid, name in group:
            refs = _player_source_refs(conn, pid)
            ref_text = ", ".join(f"(\"{s}\", \"{sid}\")" for s, sid in refs)
            games = _player_appearance_count(conn, pid)
            lines.append(f"  - player_id {pid} ({games} games): {ref_text}")

    lines.append("")

    # ---- Section B: same first-initial + surname, different full spelling ----

    buckets = defaultdict(list)
    for pid, name in players:
        key = _first_initial_surname(name)
        if key:
            buckets[key].append((pid, name))

    fuzzy_clusters = []

    for key, group in buckets.items():

        if len(group) < 2:
            continue

        distinct_names = {name for _, name in group}

        if len(distinct_names) < 2:
            continue

        # Already-reported in section A (identical apart from
        # case/whitespace/punctuation) -- no need to repeat verbatim.
        if _normalise_loose(group[0][1]) and len({_normalise_loose(n) for _, n in group}) == 1:
            continue

        fuzzy_clusters.append(group)

    fuzzy_clusters.sort(key=_evidence, reverse=True)

    lines.append(f"#### Same first initial + surname, different first name spelling ({len(fuzzy_clusters)} groups)")
    lines.append("")

    for group in fuzzy_clusters:

        evidence = _evidence(group)
        lines.append(f"- {' / '.join(repr(n) for _, n in group)} -- {evidence} combined appearances")

        for pid, name in group:
            refs = _player_source_refs(conn, pid)
            ref_text = ", ".join(f"(\"{s}\", \"{sid}\")" for s, sid in refs)
            games = _player_appearance_count(conn, pid)
            lines.append(f"  - player_id {pid} ({games} games): {ref_text}")

    lines.append("")
    lines.append(
        "To confirm any player group above, add an entry to `PLAYER_MERGES` "
        "in reconcile.py using the `(source, source_player_id)` refs listed "
        "-- see the existing Ian Wade entry for the shape."
    )
    lines.append("")

    return lines


# ==================================================================
# ENTRY POINT
# ==================================================================

def generate_report(conn):

    lines = ["# Data Quality & Reconciliation Report", ""]
    lines.append(
        f"_Generated {datetime.now(timezone.utc).isoformat()} -- "
        "auto-generated by `reconcile_audit.py`, safe to regenerate/"
        "overwrite; the database itself is never written to by this "
        "script. See reconcile.py for how confirmed candidates below "
        "get applied._"
    )
    lines.append("")

    counts = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("clubs", "teams", "players", "matches")
    }
    lines.append(
        f"**{counts['clubs']} clubs, {counts['teams']} teams, "
        f"{counts['players']} players, {counts['matches']} matches.**"
    )
    lines.append("")

    lines.extend(render_data_quality_section(conn))

    lines.append("## Part 2 -- Reconciliation candidates")
    lines.append("")
    lines.extend(render_club_candidates(conn))
    lines.extend(render_team_candidates(conn))
    lines.extend(render_player_candidates(conn))

    return "\n".join(lines) + "\n"


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate a data-quality/reconciliation-candidates Markdown report."
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")
    parser.add_argument("--out", default="reconcile/data_quality_report.md")

    args = parser.parse_args()

    conn = sqlite3.connect(args.sqlite_db)
    conn.execute("PRAGMA foreign_keys = ON")

    report = generate_report(conn)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)

    conn.close()

    print(f"Wrote {args.out}")
