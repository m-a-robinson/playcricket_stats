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
2. Reconciliation candidates -- clubs, teams, grounds, and players
   that look like they might be the same real thing split across two
   or more canonical rows, but aren't safe to merge automatically.
   SQLiteStore already auto-merges exact/near-exact club, team, and
   ground names at insert time (see its docstring); what's left here
   is the fuzzier residue, plus players, which get no automatic
   merging at all. Player candidates are restricted to players who
   *exclusively* appear for one club (ELPMCC_NAME from
   sqlite_queries.py, by default) -- the only players career_stats()
   tracks by default anyway. A shared name across different clubs is
   excluded rather than suggested: more likely two different real
   people (or a guest/opposition appearance) than the same person
   reconciled across clubs. Different *teams* within that one club
   (1st XI, 2nd XI, ...) are fine -- that's still one club, and
   exactly the case this is meant to catch. Ground candidates are
   grouped by home club rather than by name similarity -- see
   render_ground_candidates() for why.

This script never writes to the database. It only reads and reports.
Confirmed candidates become permanent decisions by hand-copying the
`(source, source_*_id)` refs listed under each candidate into
reconcile/decisions.yaml (see that file's own header for the exact
shape) -- then `python3 reconcile.py --sqlite-db <path>` applies them.
A candidate already recorded in decisions.yaml's `rejected:` section
(confirmed different, or still undecided) is held out of the "new
candidates" lists below and shown separately instead -- see
render_deferred_section() -- so a decision already made, even a
"not yet" one, doesn't get re-suggested as if it were new. Re-run this
script (it's cheap and disposable, not version-controlled output in
itself beyond whatever snapshot you choose to commit) any time after
ingesting a new source, fixing a parser bug, or editing decisions.yaml.

Usage
-----
    python3 reconcile_audit.py --sqlite-db playcricket_stats.sqlite \
        --out reconcile/data_quality_report.md

Everything here is a *suggestion* for a human to confirm or reject --
none of it is applied automatically, and false positives (two
different real people/clubs/teams/grounds that happen to look similar)
are expected and fine; that's exactly what the human review step is for.
"""

import argparse
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher

import yaml

from sqlite_store import SQLiteStore
from sqlite_queries import ELPMCC_NAME
from reconcile import DEFAULT_DECISIONS_PATH


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
# ALREADY-REVIEWED (decisions.yaml's `rejected:` section)
# ==================================================================

def _load_rejected(decisions_path=DEFAULT_DECISIONS_PATH):
    """
    decisions.yaml's `rejected:` section, keyed by entity type, as a
    list of {refs: frozenset of (source, id) tuples, status, reason}.
    Missing file / missing section -> no entries, same as an empty one.
    """

    try:
        with open(decisions_path, "r", encoding="utf-8") as f:
            rejected_raw = (yaml.safe_load(f) or {}).get("rejected") or {}
    except FileNotFoundError:
        rejected_raw = {}

    result = {}

    for entity in ("players", "clubs", "teams", "grounds"):

        entries = []

        for entry in rejected_raw.get(entity) or []:

            refs = frozenset(
                (ref["source"], str(ref["id"])) for ref in entry["refs"]
            )

            entries.append({
                "refs": refs,
                "status": entry.get("status", "pending"),
                "reason": (entry.get("reason") or "").strip(),
            })

        result[entity] = entries

    return result


def _match_rejected(cluster_refs, rejected_entries):
    """
    The rejected entry whose ref set is fully contained in this
    candidate cluster's refs, if any -- so a pair rejected/deferred
    once is still recognised even if the cluster around it later grows
    (e.g. a third spelling of the same name appears). None if this
    cluster hasn't been reviewed before.
    """

    cluster_set = frozenset(cluster_refs)

    for entry in rejected_entries:
        if entry["refs"] and entry["refs"] <= cluster_set:
            return entry

    return None


def render_deferred_section(rejected_by_entity):
    """
    Everything already looked at and held back (status: pending) or
    confirmed different (status: rejected) -- kept visible so review
    work already done isn't lost or silently repeated, but out of the
    way of genuinely new candidates.
    """

    lines = ["### Already reviewed (deferred / rejected)", ""]

    any_entries = any(rejected_by_entity.values())

    if not any_entries:
        lines.append("None recorded in decisions.yaml's `rejected:` section.")
        lines.append("")
        return lines

    for entity, entries in rejected_by_entity.items():

        if not entries:
            continue

        lines.append(f"**{entity.capitalize()}**")
        lines.append("")

        for entry in entries:
            refs_text = ", ".join(f"(\"{s}\", \"{i}\")" for s, i in sorted(entry["refs"]))
            lines.append(f"- `{entry['status']}` -- {refs_text}")
            if entry["reason"]:
                lines.append(f"  - {entry['reason']}")

        lines.append("")

    return lines


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


def _ground_source_refs(conn, ground_id):
    return conn.execute(
        "SELECT source, source_ground_key FROM ground_source_ids WHERE ground_id = ?",
        (ground_id,)
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


def _elpmcc_exclusive_player_ids(conn, elpmcc_name):
    """
    player_ids whose match_appearances are ALL for a team belonging to
    `elpmcc_name` -- i.e. every real club they've turned out for, on any
    team (1st XI, 2nd XI, ...), is this one club. Career stats here are
    only tracked for this club's own players (see sqlite_queries.py's
    ELPMCC_NAME/elpmcc_only), and only they should ever be reconciled: a
    name that also appears for a genuinely different club is more likely
    two different real people (or a guest/opposition appearance) than
    the same person, and merging it in would pull a different club's
    appearances into what's meant to be one club's player record.

    A player who never has a match_appearances row at all (shouldn't
    happen given the schema, but not guaranteed) is excluded rather than
    assumed to qualify.
    """

    rows = conn.execute(
        """
        SELECT ma.player_id
        FROM match_appearances ma
        JOIN teams t ON t.team_id = ma.team_id
        JOIN clubs c ON c.club_id = t.club_id
        GROUP BY ma.player_id
        HAVING SUM(CASE WHEN c.club_name != ? THEN 1 ELSE 0 END) = 0
        """,
        (elpmcc_name,)
    ).fetchall()

    return {row[0] for row in rows}


def render_club_candidates(conn, rejected_entries=()):

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

    all_clusters = [group for group in groups.values() if len(group) > 1]
    clusters = [
        group for group in all_clusters
        if _match_rejected(
            [ref for cid, _ in group for ref in _club_source_refs(conn, cid)],
            rejected_entries
        ) is None
    ]
    deferred_count = len(all_clusters) - len(clusters)

    if not clusters:
        note = "None found -- SQLiteStore's automatic name-based merge (see its docstring) already caught every case in the current data."
        if deferred_count:
            note += f" ({deferred_count} already reviewed -- see \"Already reviewed\" below.)"
        lines.append(note)
        lines.append("")
        return lines

    lines.append(
        f"{len(clusters)} candidate group(s) not already unified automatically"
        + (f" ({deferred_count} more already reviewed -- see below)" if deferred_count else "")
        + ":"
    )
    lines.append("")

    for group in clusters:

        names = ", ".join(f"{name!r} (club_id {cid})" for cid, name in group)
        lines.append(f"- **{names}**")

        for cid, name in group:
            refs = _club_source_refs(conn, cid)
            ref_text = ", ".join(f"(\"{s}\", \"{sid}\")" for s, sid in refs)
            lines.append(f"  - club_id {cid}: {ref_text}")

        all_refs = [ref for cid, _ in group for ref in _club_source_refs(conn, cid)]
        refs_literal = "\n".join(f"      - {{source: {s}, id: \"{sid}\"}}" for s, sid in all_refs)
        lines.append("  - if confirmed, add to `clubs:` in reconcile/decisions.yaml:")
        lines.append("    ```yaml")
        lines.append(f"    - canonical_name: {group[0][1]!r}")
        lines.append(f"      refs:\n{refs_literal}")
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


def render_team_candidates(conn, rejected_entries=()):

    lines = ["### Teams", ""]

    clubs = conn.execute(
        "SELECT club_id, club_name FROM clubs WHERE club_name NOT LIKE 'Unknown (%'"
    ).fetchall()
    found_clusters = []

    for club_id, club_name in clubs:

        teams = conn.execute(
            "SELECT team_id, team_name FROM teams WHERE club_id = ?", (club_id,)
        ).fetchall()

        for group in _near_duplicate_clusters_ids(teams):
            found_clusters.append((club_id, club_name, group))

    all_clusters = [
        (club_id, club_name, group) for club_id, club_name, group in found_clusters
        if _match_rejected(
            [ref for tid, _ in group for ref in _team_source_refs(conn, tid)],
            rejected_entries
        ) is None
    ]
    deferred_count = len(found_clusters) - len(all_clusters)

    if not all_clusters:
        note = "None found."
        if deferred_count:
            note += f" ({deferred_count} already reviewed -- see \"Already reviewed\" below.)"
        lines.append(note)
        lines.append("")
        return lines

    lines.append(
        f"{len(all_clusters)} candidate group(s), within a single club each"
        + (f" ({deferred_count} more already reviewed -- see below)" if deferred_count else "")
        + ":"
    )
    lines.append("")

    for club_id, club_name, group in all_clusters:

        names = ", ".join(f"{name!r} (team_id {tid})" for tid, name in group)
        lines.append(f"- **{club_name}** (club_id {club_id}): {names}")

        for tid, name in group:
            refs = _team_source_refs(conn, tid)
            ref_text = ", ".join(f"(\"{s}\", \"{sid}\")" for s, sid in refs)
            lines.append(f"  - team_id {tid}: {ref_text}")

        all_refs = [ref for tid, _ in group for ref in _team_source_refs(conn, tid)]
        refs_literal = "\n".join(f"      - {{source: {s}, id: \"{sid}\"}}" for s, sid in all_refs)
        lines.append("  - if confirmed, add to `teams:` in reconcile/decisions.yaml:")
        lines.append("    ```yaml")
        lines.append(f"    - canonical_name: {group[0][1]!r}")
        lines.append(f"      refs:\n{refs_literal}")
        lines.append("    ```")
        lines.append("")

    return lines


def _club_acronym(club_name):
    """
    Initials of a club's significant name words (trailing "CC"/"Cricket
    Club" dropped first, same as _CLUB_SUFFIX_RE) -- "East Lancs Paper
    Mill CC" -> "elpm". A weak but useful signal for "is this ground
    plausibly named after/abbreviated from this club's own name" --
    see render_ground_candidates() for why that signal is needed at all.
    """

    name = re.sub(r"\s*,?\s*(cricket club|c\.?c\.?)\s*$", "", club_name or "", flags=re.IGNORECASE)
    words = re.findall(r"[A-Za-z]+", name)
    return "".join(w[0] for w in words).casefold()


def render_ground_candidates(conn, rejected_entries=()):
    """
    Grouped by home club, NOT by name similarity: ground names vary far
    too much in form across sources for text matching to find these
    reliably (e.g. "ELPMCC" vs "Croft Lane, ELPM" share no substring or
    close spelling at all, despite being the same real ground). What's
    reliable instead is that a club's own home matches should mostly
    resolve to one ground -- so for each club, every distinct ground
    recorded across sources for its home matches is one candidate
    group.

    BUT: a single-club archive (CricketStatz here) records "home_team"
    from that one club's own perspective, not true host/venue -- so
    e.g. every away fixture ELPMCC played at an opponent's ground still
    shows ELPMCC as "home_team_id" in this data, which would otherwise
    flood every real club with dozens of one-off "candidate" grounds
    that are actually just other clubs' real venues (confirmed by
    inspecting the raw output: ~38 clearly-unrelated one-to-few-match
    grounds appeared under East Lancs Paper Mill CC alone before this
    filter existed). Guarded against by requiring the ground name to
    contain the club's own acronym (_club_acronym()) before it counts
    as a same-club candidate at all -- conservative in the safe
    direction: real cross-source alternate names this misses (no shared
    club-name text at all) stay findable some other way, rather than
    risking a wall of false candidates that makes the real ones hard to
    spot.

    A ground shared across MANY different clubs' home matches (not
    just one) is a different situation, flagged separately: that's a
    generic/vague placeholder (CricHQ's county-only "Venue:" field is
    the known example), not a real single venue -- merging it into any
    one club's ground would be wrong, since it's also recording every
    OTHER club's home matches under that source. That case wants a
    `ground_overrides` rule scoped to one club's home matches, not a
    `grounds:` merge -- see reconcile/decisions.yaml's own header.
    """

    lines = ["### Grounds", ""]
    lines.append(
        "Grouped by home club rather than by name similarity -- see this "
        "function's docstring for why. A ground recorded for only one "
        "club's home matches is a same-ground merge candidate; a ground "
        "shared across several different clubs' home matches is flagged "
        "separately below as a likely vague/generic placeholder, which "
        "wants a `ground_overrides` rule instead of a merge."
    )
    lines.append("")

    rows = conn.execute(
        """
        SELECT c.club_id, c.club_name, g.ground_id, g.ground_name, COUNT(*)
        FROM matches m
        JOIN teams t ON t.team_id = m.home_team_id
        JOIN clubs c ON c.club_id = t.club_id
        JOIN grounds g ON g.ground_id = m.ground_id
        WHERE c.club_name NOT LIKE 'Unknown (%'
        GROUP BY c.club_id, g.ground_id
        """
    ).fetchall()

    by_club = defaultdict(list)
    by_ground_clubs = defaultdict(dict)

    for club_id, club_name, ground_id, ground_name, count in rows:
        by_club[(club_id, club_name)].append((ground_id, ground_name, count))
        by_ground_clubs[(ground_id, ground_name)][(club_id, club_name)] = count

    shared_grounds = {
        ground: clubs for ground, clubs in by_ground_clubs.items()
        if len(clubs) > 2   # a handful of genuine away/neutral-venue matches is normal; many clubs is the vague-placeholder signal
    }

    found_clusters = []

    for (club_id, club_name), grounds in by_club.items():

        acronym = _club_acronym(club_name)

        # A one- or two-letter acronym (a club with only one short
        # significant word in its name) is too weak a signal -- likely
        # to appear inside an unrelated ground name by pure chance
        # (seen in practice: "Rochdalians CC" -> "r" matched CricHQ's
        # placeholder "England - Bedfordshire"). Skip clustering for
        # that club entirely rather than risk a misleading suggestion.
        own_grounds = [
            (gid, gname, cnt) for gid, gname, cnt in grounds
            if (gid, gname) not in shared_grounds
            and len(acronym) >= 3 and acronym in _normalise_loose(gname)
        ]

        if len(own_grounds) > 1:
            found_clusters.append((club_id, club_name, own_grounds))

    clusters = [
        (cid, cname, group) for cid, cname, group in found_clusters
        if _match_rejected(
            [ref for gid, _, _ in group for ref in _ground_source_refs(conn, gid)],
            rejected_entries
        ) is None
    ]
    deferred_count = len(found_clusters) - len(clusters)

    if clusters:

        lines.append(
            f"{len(clusters)} club(s) with more than one distinct ground recorded "
            "for their own home matches"
            + (f" ({deferred_count} more already reviewed -- see below)" if deferred_count else "")
            + ":"
        )
        lines.append("")

        for club_id, club_name, group in clusters:

            names = ", ".join(f"{gname!r} ({cnt} home matches)" for gid, gname, cnt in group)
            lines.append(f"- **{club_name}** (club_id {club_id}): {names}")

            for gid, gname, cnt in group:
                refs = _ground_source_refs(conn, gid)
                ref_text = ", ".join(f"(\"{s}\", \"{sid}\")" for s, sid in refs)
                lines.append(f"  - ground_id {gid}: {ref_text}")

            all_refs = [ref for gid, _, _ in group for ref in _ground_source_refs(conn, gid)]
            refs_literal = "\n".join(f"      - {{source: {s}, id: \"{sid}\"}}" for s, sid in all_refs)
            lines.append("  - if confirmed the same ground, add to `grounds:` in reconcile/decisions.yaml:")
            lines.append("    ```yaml")
            lines.append(f"    - canonical_name: \"???\"  # what should this actually read as?")
            lines.append(f"      refs:\n{refs_literal}")
            lines.append("    ```")
            lines.append("")

    else:
        note = "No club has more than one distinct (non-shared) ground recorded for its home matches."
        if deferred_count:
            note += f" ({deferred_count} already reviewed -- see \"Already reviewed\" below.)"
        lines.append(note)
        lines.append("")

    if shared_grounds:

        lines.append(
            f"**{len(shared_grounds)} ground(s) shared across more than 2 clubs' home "
            "matches** -- two different explanations, and the match-count split "
            "below tells them apart: (a) a vague/generic placeholder, several clubs "
            "each with a handful of matches and no clear majority (CricHQ's "
            "county-only text is the known example) -- wants a `ground_overrides` "
            "rule; or (b) one club with the large majority of matches (its own real "
            "ground) and a long tail of 1-few-match \"other clubs\" -- that's not a "
            "placeholder at all, it means the SOURCE's own home/away field isn't "
            "reliable for those matches (confirmed for CricketStatz: it sometimes "
            "names the visiting side as \"home\" even though the match was played "
            "at the true home side's ground, which the `ground_name` itself still "
            "gets right). (b) is a data-quality note about that source's home/away "
            "field, not something this file can fix -- nothing to add here."
        )
        lines.append("")

        for (ground_id, ground_name), clubs in sorted(shared_grounds.items(), key=lambda kv: -sum(kv[1].values())):

            ranked = sorted(clubs.items(), key=lambda kv: -kv[1])
            total = sum(clubs.values())
            top_name, top_count = ranked[0][0][1], ranked[0][1]
            likely_b = top_count >= total * 0.5

            club_text = ", ".join(f"{name} ({count})" for (_, name), count in ranked)
            lines.append(
                f"- {ground_name!r} (ground_id {ground_id}) -- {total} matches across "
                f"{len(clubs)} clubs, {top_name} the largest at {top_count} "
                f"({'likely (b) -- unreliable home/away field, not a placeholder' if likely_b else 'likely (a) -- vague placeholder'}): "
                f"{club_text}"
            )
            if not likely_b:
                lines.append(
                    "  - if this club's home matches should really point at a real "
                    "ground, add a `ground_overrides` rule in reconcile/decisions.yaml "
                    "(see the CricHQ example already there) rather than merging this row."
                )

        lines.append("")

    return lines


def render_player_candidates(conn, elpmcc_name=ELPMCC_NAME, rejected_entries=()):

    lines = ["### Players", ""]
    lines.append(
        "Player identity gets no automatic merging at all (see reconcile.py's "
        "docstring) -- everything below is a suggestion only. A shared "
        "initial+surname is common and does NOT mean the same person; "
        "check appearance counts, dates, and sources before confirming."
    )
    lines.append("")
    lines.append(
        f"Restricted to players who **exclusively** appear for "
        f"`{elpmcc_name}` (on any of its teams -- 1st XI, 2nd XI, ... all "
        "count as the same club) -- the only players career_stats()/"
        "SQLPlayerStats track by default anyway (see sqlite_queries.py's "
        "`elpmcc_only`). A name also appearing for a genuinely different "
        "club is excluded rather than suggested: that's more likely two "
        "different real people (or a guest/opposition appearance) than "
        "the same person, and merging would pull another club's "
        "appearances into what should be a single-club player record."
    )
    lines.append("")

    elpmcc_ids = _elpmcc_exclusive_player_ids(conn, elpmcc_name)

    players = [
        row for row in conn.execute("SELECT player_id, known_as FROM players")
        if row[0] in elpmcc_ids
    ]

    # ---- Section A: identical after stripping case/whitespace/punctuation ----

    loose_groups = defaultdict(list)
    for pid, name in players:
        loose_groups[_normalise_loose(name)].append((pid, name))

    def _refs(group):
        return [ref for pid, _ in group for ref in _player_source_refs(conn, pid)]

    found_exact = [
        group for group in loose_groups.values()
        if len(group) > 1 and len({name for _, name in group}) > 1
    ]
    exact_clusters = [
        group for group in found_exact
        if _match_rejected(_refs(group), rejected_entries) is None
    ]
    exact_deferred = len(found_exact) - len(exact_clusters)

    def _evidence(group):
        return sum(_player_appearance_count(conn, pid) for pid, _ in group)

    exact_clusters.sort(key=_evidence, reverse=True)

    lines.append(
        f"#### Same name, different spelling of whitespace/case/punctuation only "
        f"({len(exact_clusters)} groups"
        + (f", {exact_deferred} more already reviewed -- see below" if exact_deferred else "")
        + ")"
    )
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

    found_fuzzy = fuzzy_clusters
    fuzzy_clusters = [
        group for group in found_fuzzy
        if _match_rejected(_refs(group), rejected_entries) is None
    ]
    fuzzy_deferred = len(found_fuzzy) - len(fuzzy_clusters)

    fuzzy_clusters.sort(key=_evidence, reverse=True)

    lines.append(
        f"#### Same first initial + surname, different first name spelling "
        f"({len(fuzzy_clusters)} groups"
        + (f", {fuzzy_deferred} more already reviewed -- see below" if fuzzy_deferred else "")
        + ")"
    )
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
        "To confirm any player group above, add an entry to `players:` in "
        "reconcile/decisions.yaml using the `(source, source_player_id)` refs "
        "listed -- see the existing Ian Wade entry for the shape. Not sure, or "
        "looked at it and decided these are different people? Add it to "
        "`rejected: players:` instead (`status: pending` or `status: rejected`) "
        "so it's held here rather than suggested again next time."
    )
    lines.append("")

    return lines


# ==================================================================
# ENTRY POINT
# ==================================================================

def generate_report(conn, elpmcc_name=ELPMCC_NAME, decisions_path=DEFAULT_DECISIONS_PATH):

    rejected = _load_rejected(decisions_path)

    lines = ["# Data Quality & Reconciliation Report", ""]
    lines.append(
        f"_Generated {datetime.now(timezone.utc).isoformat()} -- "
        "auto-generated by `reconcile_audit.py`, safe to regenerate/"
        "overwrite; the database itself is never written to by this "
        "script. See reconcile.py and reconcile/decisions.yaml for how "
        "confirmed candidates below get applied._"
    )
    lines.append("")

    counts = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("clubs", "teams", "players", "grounds", "matches")
    }
    lines.append(
        f"**{counts['clubs']} clubs, {counts['teams']} teams, "
        f"{counts['grounds']} grounds, {counts['players']} players, "
        f"{counts['matches']} matches.**"
    )
    lines.append("")

    lines.extend(render_data_quality_section(conn))

    lines.append("## Part 2 -- Reconciliation candidates")
    lines.append("")
    lines.extend(render_club_candidates(conn, rejected["clubs"]))
    lines.extend(render_team_candidates(conn, rejected["teams"]))
    lines.extend(render_ground_candidates(conn, rejected["grounds"]))
    lines.extend(render_player_candidates(conn, elpmcc_name, rejected["players"]))
    lines.extend(render_deferred_section(rejected))

    return "\n".join(lines) + "\n"


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate a data-quality/reconciliation-candidates Markdown report."
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")
    parser.add_argument("--out", default="reconcile/data_quality_report.md")
    parser.add_argument(
        "--elpmcc-name", default=ELPMCC_NAME,
        help="Club name player candidates are restricted to (see sqlite_queries.py's ELPMCC_NAME)."
    )
    parser.add_argument("--decisions", default=DEFAULT_DECISIONS_PATH)

    args = parser.parse_args()

    conn = sqlite3.connect(args.sqlite_db)
    conn.execute("PRAGMA foreign_keys = ON")

    report = generate_report(conn, elpmcc_name=args.elpmcc_name, decisions_path=args.decisions)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)

    conn.close()

    print(f"Wrote {args.out}")
