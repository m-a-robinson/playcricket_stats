#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
sqlite_store.py

Builds and maintains the normalised SQLite cricket stats database.

Architecture
------------

    PlayCricketDatabase (JSON sync cache)
          |
          v
    Scorecard (per match)
          |
          v
    SQLiteStore                <- this module
          |
          v
    schema.sql tables
    (clubs / teams / players / matches / innings / batting / bowling)

This module does NOT call the Play-Cricket API. It only reads whatever
PlayCricketDatabase already holds locally (populated by
PlayCricketDatabase.sync_season()) and writes it into a normalised
SQLite file for querying, career stats, and leaderboards.

Rebuilding is idempotent per source: build_from_database() deletes and
reinserts every match belonging to that source before repopulating it,
so it is safe to re-run after every sync.

CricHQ PDF and CricketStatz .csd ingestion will reuse this same store:
each will produce its own list of "match detail"-shaped dictionaries
and call the same insert_match() method with a different `source`.
"""

import json
import os
import re
import sqlite3
from datetime import datetime

from playcricket_scorecard import Scorecard


SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "schema.sql"
)

SOURCE_PLAY_CRICKET = "play_cricket"

# Strips one trailing "CC"/"C.C."/"Cricket Club" (optionally preceded by
# a comma) so e.g. "East Lancs Paper Mill CC" (play_cricket) and "East
# Lancs Paper Mill" (crichq_pdf) normalise to the same key. Deliberately
# conservative -- only a suffix strip plus casefold/whitespace collapse,
# nothing that guesses at abbreviations or dropped qualifiers (e.g.
# "Bradshaw CC, Lancs" vs "Bradshaw CC" does NOT normalise to the same
# key here) -- so an auto-merge triggered by this can't plausibly
# conflate two different real clubs. Fuzzier cases are surfaced by
# reconcile_audit.py for a human to confirm via reconcile.py's
# CLUB_MERGES/TEAM_MERGES instead of being guessed at here.
_CLUB_SUFFIX_RE = re.compile(r"\s*,?\s*(cricket club|c\.?c\.?)\s*$", re.IGNORECASE)

# Classifies a team as youth cricket from its name alone -- "Under 9",
# "Under 11 B", "U9", "U-11", "Colts", "Juniors" and similar. Checked
# against the full archive: only Play-Cricket (2024-2026) currently has
# any youth teams at all (Under 9/Under 9 B/Under 9 D/Under 11/Under 11
# B) -- CricHQ and CricketStatz have none. Deliberately name-based like
# the club/team merge logic above rather than sourced from a reference
# list, since every youth team name seen so far states its age group
# plainly; a team that doesn't match stays classed as senior.
_YOUTH_TEAM_RE = re.compile(
    r"\bunder[\s-]?\d{1,2}\b|\bu-?\d{1,2}\b|\bcolts?\b|\bjuniors?\b",
    re.IGNORECASE
)


def _classify_team(team_name):
    return 1 if team_name and _YOUTH_TEAM_RE.search(team_name) else 0


class SQLiteStore:

    # ==========================================================
    # INITIALISATION
    # ==========================================================

    def __init__(self, filename="playcricket_stats.sqlite"):

        self.filename = filename

        self.conn = sqlite3.connect(self.filename)
        self.conn.execute("PRAGMA foreign_keys = ON")

        self._apply_schema()

        # In-memory dedup indexes, keyed by normalised name, so a club/
        # team already created (by this source or an earlier one) is
        # reused instead of split into a second row -- see
        # _normalise_club_name()/_normalise_team_name(). Seeded from
        # whatever is already in the tables so this also converges a
        # store that already has split rows, one rebuild at a time.
        self._club_index = {}
        self._team_index = {}

        for club_id, club_name in self.conn.execute("SELECT club_id, club_name FROM clubs"):
            self._club_index.setdefault(self._normalise_club_name(club_name), club_id)

        for team_id, team_name, club_id in self.conn.execute("SELECT team_id, team_name, club_id FROM teams"):
            self._team_index.setdefault((club_id, self._normalise_team_name(team_name)), team_id)

    def _apply_schema(self):

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            self.conn.executescript(f.read())

        self.conn.commit()

    def close(self):
        self.conn.close()

    # ==========================================================
    # SMALL VALUE HELPERS
    # ==========================================================

    @staticmethod
    def _is_missing(value):
        """
        True for None, "", and pandas/float NaN.

        NaN cannot be caught by `value in (None, "")` -- NaN compares
        unequal to everything, including itself -- so a bare Python
        None that pandas has upgraded to NaN (which happens whenever
        it shares a DataFrame column with strings) would otherwise
        slip past every _clean_*() check below as a truthy value.
        """

        if value is None or value == "":
            return True

        if isinstance(value, float) and value != value:
            return True

        return False

    @classmethod
    def _clean_id(cls, value):

        if cls._is_missing(value) or value in ("0", 0):
            return None

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @classmethod
    def _clean_int(cls, value):

        if cls._is_missing(value):
            return None

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @classmethod
    def _clean_bool(cls, value):

        if cls._is_missing(value):
            return None

        if isinstance(value, str):
            return 1 if value.strip().lower() in ("1", "yes", "true") else 0

        return 1 if value else 0

    @classmethod
    def _clean_text(cls, value):
        """
        Same NaN-column trap as _is_missing() documents, one step
        further: a whole-number id (e.g. a Play-Cricket player_id)
        that survives as a *present* value in a column pandas has
        upgraded to float64 -- because some OTHER row in that same
        column was missing -- comes through as 6216362.0, not 6216362.
        Left alone, that turns into a second, spurious source_player_id
        for the exact same real person (str(6216362) != str(6216362.0)).
        Normalise whole-number floats back to plain integer text.
        """

        if cls._is_missing(value):
            return None

        if isinstance(value, float) and value.is_integer():
            return str(int(value))

        return str(value)

    @classmethod
    def _normalise_club_name(cls, name):
        """Dedup key for club names across sources -- see _CLUB_SUFFIX_RE."""

        name = re.sub(r"\s+", " ", (name or "").strip())
        name = _CLUB_SUFFIX_RE.sub("", name)
        return name.strip().casefold()

    @classmethod
    def _normalise_team_name(cls, name):
        """
        Dedup key for team names -- scoped by club_id by the caller,
        since e.g. "1st XI" is legitimately shared by many different
        clubs. Just case/whitespace here: team names ("1st XI", "2nd
        XI", ...) don't carry the club-suffix variation club names do.
        """

        return re.sub(r"\s+", " ", (name or "").strip()).casefold()

    # ==========================================================
    # DIMENSION UPSERTS
    # ==========================================================

    def _upsert_club(self, source, source_club_id, club_name):
        """
        Resolve a source-specific club id (Play-Cricket's numeric id, or
        a normalised club name for sources with no numeric id) to a
        canonical club_id, creating both the canonical row and the
        mapping row the first time this (source, source_club_id) is seen.

        Before creating a brand new club row, checks self._club_index for
        an existing club whose name normalises to the same
        _normalise_club_name() key -- e.g. play_cricket's "East Lancs
        Paper Mill CC" and crichq_pdf's "East Lancs Paper Mill" both
        resolve to the same canonical club instead of splitting into two.
        This is a deliberately conservative, automatic merge; anything
        it doesn't catch is a candidate for reconcile_audit.py /
        reconcile.py's CLUB_MERGES instead.
        """

        source_club_id = self._clean_text(source_club_id)

        if source_club_id is None:
            return None

        row = self.conn.execute(
            "SELECT club_id FROM club_source_ids WHERE source = ? AND source_club_id = ?",
            (source, source_club_id)
        ).fetchone()

        if row:
            return row[0]

        club_name = self._clean_text(club_name) or source_club_id
        norm_key = self._normalise_club_name(club_name)

        club_id = self._club_index.get(norm_key)

        if club_id is None:

            cursor = self.conn.execute(
                "INSERT INTO clubs (club_name) VALUES (?)",
                (club_name,)
            )

            club_id = cursor.lastrowid
            self._club_index[norm_key] = club_id

        self.conn.execute(
            "INSERT INTO club_source_ids (source, source_club_id, club_id) VALUES (?, ?, ?)",
            (source, source_club_id, club_id)
        )

        return club_id

    def _upsert_team(self, source, source_team_id, team_name, club_id):
        """
        Resolve a source-specific team id to a canonical team_id, the
        same way _upsert_club() resolves clubs -- via self._team_index,
        keyed by (club_id, _normalise_team_name()) so e.g. "1st XI" is
        still a different team per club, but not split into two rows
        for the same club across sources.
        """

        source_team_id = self._clean_text(source_team_id)

        if source_team_id is None:
            return None

        row = self.conn.execute(
            "SELECT team_id FROM team_source_ids WHERE source = ? AND source_team_id = ?",
            (source, source_team_id)
        ).fetchone()

        if row:
            return row[0]

        team_name = self._clean_text(team_name) or source_team_id
        index_key = (club_id, self._normalise_team_name(team_name))

        team_id = self._team_index.get(index_key)

        if team_id is None:

            cursor = self.conn.execute(
                "INSERT INTO teams (team_name, club_id, is_youth) VALUES (?, ?, ?)",
                (team_name, club_id, _classify_team(team_name))
            )

            team_id = cursor.lastrowid
            self._team_index[index_key] = team_id

        self.conn.execute(
            "INSERT INTO team_source_ids (source, source_team_id, team_id) VALUES (?, ?, ?)",
            (source, source_team_id, team_id)
        )

        return team_id

    def _resolve_team_id(self, source, source_team_id):
        """
        Look up a canonical team_id for a source-specific team id that
        should already have been upserted (e.g. a team_batting_id that
        must be one of the two teams already upserted for this match).
        Returns None rather than creating anything -- an unresolvable
        reference here means the source data is inconsistent, not that
        a new team should be invented.
        """

        source_team_id = self._clean_text(source_team_id)

        if source_team_id is None:
            return None

        row = self.conn.execute(
            "SELECT team_id FROM team_source_ids WHERE source = ? AND source_team_id = ?",
            (source, source_team_id)
        ).fetchone()

        return row[0] if row else None

    def _upsert_player(self, source, source_player_id, known_as):
        """
        Resolve a source-specific player id to a canonical player_id.

        Creates both the canonical player row and the source-id mapping
        row the first time a given (source, source_player_id) is seen.

        This is deliberately the ONLY place player identity is decided.
        Cross-source reconciliation (roadmap item 4) will extend this,
        not replace it: it will add extra rows to player_source_ids
        that point additional (source, source_player_id) pairs at an
        existing canonical player_id instead of always creating a new
        one.
        """

        source_player_id = self._clean_text(source_player_id)
        known_as = self._clean_text(known_as)

        if source_player_id is None:
            return None

        row = self.conn.execute(
            """
            SELECT player_id FROM player_source_ids
            WHERE source = ? AND source_player_id = ?
            """,
            (source, source_player_id)
        ).fetchone()

        if row:
            return row[0]

        cursor = self.conn.execute(
            "INSERT INTO players (known_as) VALUES (?)",
            (known_as or source_player_id,)
        )

        player_id = cursor.lastrowid

        self.conn.execute(
            """
            INSERT INTO player_source_ids (source, source_player_id, player_id)
            VALUES (?, ?, ?)
            """,
            (source, source_player_id, player_id)
        )

        return player_id

    # ==========================================================
    # SOURCE RESET
    # ==========================================================

    def _delete_source_matches(self, source):
        """
        Remove every match (and, via ON DELETE CASCADE, its innings/
        batting/bowling rows) previously loaded from this source.

        Dimension tables (clubs/teams/players) are intentionally left
        alone: they are shared across sources and rebuilt idempotently
        via upsert.
        """

        self.conn.execute(
            "DELETE FROM matches WHERE source = ?",
            (source,)
        )

    # ==========================================================
    # INSERT ONE MATCH
    # ==========================================================

    def insert_match(self, detail, source=SOURCE_PLAY_CRICKET, season=None):
        """
        Insert one match (in Play-Cricket match-detail shape) and all
        of its innings/batting/bowling rows.

        Parameters
        ----------
        detail : dict
            Raw match-detail dictionary, as returned by the Play-Cricket
            API / stored in PlayCricketDatabase. Future PDF/.csd parsers
            are expected to produce dictionaries in this same shape.

        source : str
            'play_cricket' | 'crichq_pdf' | 'cricketstatz'

        season : int, optional
            Overrides the season derived from match_date, for sources
            that don't carry a season field of their own.
        """

        scorecard = Scorecard(detail)
        match = scorecard.match_info()

        source_match_id = self._clean_text(match.get("id"))

        if source_match_id is None:
            return None

        # ------------------------------------------------------
        # Clubs / teams
        # ------------------------------------------------------

        home_club_id = self._upsert_club(
            source, match.get("home_club_id"), match.get("home_club_name")
        )
        away_club_id = self._upsert_club(
            source, match.get("away_club_id"), match.get("away_club_name")
        )

        home_team_id = self._upsert_team(
            source, match.get("home_team_id"), match.get("home_team_name"), home_club_id
        )
        away_team_id = self._upsert_team(
            source, match.get("away_team_id"), match.get("away_team_name"), away_club_id
        )

        # ------------------------------------------------------
        # Season
        # ------------------------------------------------------

        if season is None:

            match_date = self._clean_text(match.get("match_date"))

            if match_date:
                season = int(str(match_date)[:4])

        # ------------------------------------------------------
        # Match row
        # ------------------------------------------------------

        cursor = self.conn.execute(
            """
            INSERT INTO matches (
                source, source_match_id, season,
                match_date, match_time,
                competition_id, competition_name, competition_type,
                league_id, league_name,
                home_team_id, away_team_id,
                ground_id, ground_name,
                no_of_innings, no_of_overs, no_of_days,
                toss, toss_won_by_team_id,
                result, result_applied_to, result_description,
                status,
                source_last_updated, source_payload
            ) VALUES (
                ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?,
                ?, ?
            )
            ON CONFLICT(source, source_match_id) DO NOTHING
            """,
            (
                source, source_match_id, season,
                self._clean_text(match.get("match_date")),
                self._clean_text(match.get("match_time")),
                self._clean_id(match.get("competition_id")),
                self._clean_text(match.get("competition_name")),
                self._clean_text(match.get("competition_type")),
                self._clean_id(match.get("league_id")),
                self._clean_text(match.get("league_name")),
                home_team_id, away_team_id,
                self._clean_id(match.get("ground_id")),
                self._clean_text(match.get("ground_name")),
                self._clean_int(match.get("no_of_innings")),
                self._clean_int(match.get("no_of_overs")),
                self._clean_int(match.get("no_of_days")),
                self._clean_text(match.get("toss")),
                self._resolve_team_id(source, match.get("toss_won_by_team_id")),
                self._clean_text(match.get("result")),
                self._resolve_team_id(source, match.get("result_applied_to")),
                self._clean_text(match.get("result_description")),
                self._clean_text(match.get("status")),
                self._clean_text(match.get("last_updated")),
                json.dumps(detail, default=str)
            )
        )

        row = self.conn.execute(
            "SELECT match_id FROM matches WHERE source = ? AND source_match_id = ?",
            (source, source_match_id)
        ).fetchone()

        match_id = row[0]

        if cursor.rowcount == 0:
            # Match already present from an earlier build in this run.
            return match_id

        # ------------------------------------------------------
        # Innings
        # ------------------------------------------------------

        innings_id_by_number = {}

        for _, innings_row in scorecard.innings.iterrows():

            innings_number = int(innings_row["innings_number"])

            team_batting_id = self._resolve_team_id(
                source, innings_row.get("team_batting_id")
            )

            cursor = self.conn.execute(
                """
                INSERT INTO innings (
                    match_id, innings_number, team_batting_id,
                    runs, wickets, overs, balls, declared, forfeited_innings,
                    extra_byes, extra_leg_byes, extra_wides, extra_no_balls,
                    extra_penalty_runs, total_extras
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    match_id, innings_number, team_batting_id,
                    self._clean_int(innings_row.get("runs")),
                    self._clean_int(innings_row.get("wickets")),
                    self._clean_text(innings_row.get("overs")),
                    self._clean_int(innings_row.get("balls")),
                    self._clean_bool(innings_row.get("declared")),
                    self._clean_bool(innings_row.get("forfeited_innings")),
                    self._clean_int(innings_row.get("extra_byes")),
                    self._clean_int(innings_row.get("extra_leg_byes")),
                    self._clean_int(innings_row.get("extra_wides")),
                    self._clean_int(innings_row.get("extra_no_balls")),
                    self._clean_int(innings_row.get("extra_penalty_runs")),
                    self._clean_int(innings_row.get("total_extras"))
                )
            )

            innings_id_by_number[innings_number] = cursor.lastrowid

        # ------------------------------------------------------
        # Match appearances (team sheet)
        #
        # This is the source of truth for "games played" and covers
        # players who fielded but never got a batting or bowling row
        # (e.g. never came in to bat, wasn't required to bowl).
        # ------------------------------------------------------

        if not scorecard.players.empty:

            for _, player_row in scorecard.players.iterrows():

                player_id = self._upsert_player(
                    source, player_row.get("player_id"), player_row.get("player_name")
                )

                if player_id is None:
                    continue

                self.conn.execute(
                    """
                    INSERT INTO match_appearances (
                        match_id, player_id, team_id,
                        position, captain, wicket_keeper
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(match_id, player_id) DO NOTHING
                    """,
                    (
                        match_id, player_id,
                        self._resolve_team_id(source, player_row.get("team_id")),
                        self._clean_int(player_row.get("position")),
                        self._clean_bool(player_row.get("captain")),
                        self._clean_bool(player_row.get("wicket_keeper"))
                    )
                )

        # ------------------------------------------------------
        # Batting
        # ------------------------------------------------------

        if not scorecard.batting.empty:

            for _, bat_row in scorecard.batting.iterrows():

                innings_id = innings_id_by_number.get(
                    int(bat_row["innings"])
                )

                if innings_id is None:
                    continue

                player_id = self._upsert_player(
                    source, bat_row.get("batsman_id"), bat_row.get("batsman_name")
                )

                bowler_player_id = self._upsert_player(
                    source, bat_row.get("bowler_id"), bat_row.get("bowler_name")
                )

                fielder_player_id = self._upsert_player(
                    source, bat_row.get("fielder_id"), bat_row.get("fielder_name")
                )

                self.conn.execute(
                    """
                    INSERT INTO batting_innings (
                        innings_id, player_id, team_id,
                        position, runs, balls, fours, sixes,
                        how_out, not_out,
                        bowler_player_id, fielder_player_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        innings_id, player_id,
                        self._resolve_team_id(source, bat_row.get("team_id")),
                        self._clean_int(bat_row.get("position")),
                        self._clean_int(bat_row.get("runs")),
                        self._clean_int(bat_row.get("balls")),
                        self._clean_int(bat_row.get("fours")),
                        self._clean_int(bat_row.get("sixes")),
                        self._clean_text(bat_row.get("how_out")),
                        self._clean_int(bat_row.get("not_out")),
                        bowler_player_id,
                        fielder_player_id
                    )
                )

        # ------------------------------------------------------
        # Bowling
        # ------------------------------------------------------

        if not scorecard.bowling.empty:

            for _, bowl_row in scorecard.bowling.iterrows():

                innings_id = innings_id_by_number.get(
                    int(bowl_row["innings"])
                )

                if innings_id is None:
                    continue

                player_id = self._upsert_player(
                    source, bowl_row.get("bowler_id"), bowl_row.get("bowler_name")
                )

                self.conn.execute(
                    """
                    INSERT INTO bowling_innings (
                        innings_id, player_id, team_id,
                        overs, balls, maidens, runs, wickets, wides, no_balls
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        innings_id, player_id,
                        self._resolve_team_id(source, bowl_row.get("team_id")),
                        self._clean_text(bowl_row.get("overs")),
                        self._clean_int(bowl_row.get("balls")),
                        self._clean_int(bowl_row.get("maidens")),
                        self._clean_int(bowl_row.get("runs")),
                        self._clean_int(bowl_row.get("wickets")),
                        self._clean_int(bowl_row.get("wides")),
                        self._clean_int(bowl_row.get("no_balls"))
                    )
                )

        return match_id

    # ==========================================================
    # BUILD FROM PlayCricketDatabase
    # ==========================================================

    def build_from_database(self, database, source=SOURCE_PLAY_CRICKET):
        """
        Rebuild every match belonging to `source` from a
        PlayCricketDatabase instance (or anything exposing the same
        match_details()/matches() local-query interface).

        Makes NO API calls: it only reads what is already stored
        locally. Safe to call after every PlayCricketDatabase.sync_season().
        """

        self._delete_source_matches(source)

        matches_built = 0

        for season_key in database.seasons():

            season = int(season_key)

            for detail in database.match_details(season=season):

                match = detail.get("match_details", [detail])[0] \
                    if "match_details" in detail else detail

                self.insert_match(match, source=source, season=season)

                matches_built += 1

        self.conn.execute(
            "INSERT INTO build_log (built_at, source, matches_built) VALUES (?, ?, ?)",
            (datetime.now().isoformat(), source, matches_built)
        )

        self.conn.commit()

        return matches_built

    # ==========================================================
    # MANUAL PLAYER RECONCILIATION
    # ==========================================================

    def find_players(self, name_like):
        """
        Look up players by a case-insensitive substring of known_as,
        showing every source identity for each -- the usual first step
        before merge_players(). Returns a list of
        {player_id, known_as, sources: [(source, source_player_id), ...]}.
        """

        rows = self.conn.execute(
            "SELECT player_id, known_as FROM players WHERE known_as LIKE ? ORDER BY player_id",
            (f"%{name_like}%",)
        ).fetchall()

        results = []

        for player_id, known_as in rows:

            sources = self.conn.execute(
                "SELECT source, source_player_id FROM player_source_ids WHERE player_id = ?",
                (player_id,)
            ).fetchall()

            results.append({
                "player_id": player_id,
                "known_as": known_as,
                "sources": sources
            })

        return results

    def merge_players(self, keep_player_id, merge_player_id):
        """
        Merge merge_player_id into keep_player_id: the same real person,
        currently split across sources because cross-source player
        reconciliation (roadmap item 4) is a manual/deliberate step, not
        an automatic one -- see README "Not built yet" for why.

        Re-points every player_source_ids row and every fact-table
        reference (batting_innings.player_id/bowler_player_id/
        fielder_player_id, bowling_innings.player_id,
        match_appearances.player_id) from merge_player_id onto
        keep_player_id, then deletes the now-orphaned merge_player_id
        row from players. After this, career_stats() for keep_player_id
        covers both sources with no further steps needed.

        This mutates the derived SQLite file only -- the source JSON/PDF
        files are untouched, so if a merge turns out to be wrong the fix
        is simply to delete the .sqlite file and rebuild from source.
        """

        if keep_player_id == merge_player_id:
            raise ValueError("keep_player_id and merge_player_id must differ")

        self.conn.execute(
            "UPDATE player_source_ids SET player_id = ? WHERE player_id = ?",
            (keep_player_id, merge_player_id)
        )

        self.conn.execute(
            "UPDATE batting_innings SET player_id = ? WHERE player_id = ?",
            (keep_player_id, merge_player_id)
        )
        self.conn.execute(
            "UPDATE batting_innings SET bowler_player_id = ? WHERE bowler_player_id = ?",
            (keep_player_id, merge_player_id)
        )
        self.conn.execute(
            "UPDATE batting_innings SET fielder_player_id = ? WHERE fielder_player_id = ?",
            (keep_player_id, merge_player_id)
        )
        self.conn.execute(
            "UPDATE bowling_innings SET player_id = ? WHERE player_id = ?",
            (keep_player_id, merge_player_id)
        )

        # match_appearances has UNIQUE(match_id, player_id) -- a match
        # where both identities somehow already have a row (shouldn't
        # normally happen, since they come from different sources/
        # matches) would violate it. Drop the merge-side duplicate
        # rather than fail the whole merge.
        self.conn.execute(
            """
            DELETE FROM match_appearances
            WHERE player_id = ?
              AND match_id IN (
                  SELECT match_id FROM match_appearances WHERE player_id = ?
              )
            """,
            (merge_player_id, keep_player_id)
        )
        self.conn.execute(
            "UPDATE match_appearances SET player_id = ? WHERE player_id = ?",
            (keep_player_id, merge_player_id)
        )

        self.conn.execute("DELETE FROM players WHERE player_id = ?", (merge_player_id,))

        self.conn.commit()

    # ==========================================================
    # REPRESENTATION
    # ==========================================================

    def __repr__(self):
        return f"SQLiteStore(filename='{self.filename}')"


# ==================================================================
# CLI ENTRY POINT
# ==================================================================

if __name__ == "__main__":

    import argparse
    from playcricket_database import PlayCricketDatabase

    parser = argparse.ArgumentParser(
        description="Build the SQLite stats database from the local "
                    "Play-Cricket JSON cache. Makes no API calls."
    )

    parser.add_argument(
        "--json-db",
        default="playcricket_database.json",
        help="Path to the PlayCricketDatabase JSON cache."
    )

    parser.add_argument(
        "--sqlite-db",
        default="playcricket_stats.sqlite",
        help="Path to the SQLite database to build/update."
    )

    args = parser.parse_args()

    class _LocalOnlyDatabase(PlayCricketDatabase):
        """PlayCricketDatabase subclass that never needs a live API client."""

        def __init__(self, filename):
            self.api = None
            self.filename = filename
            self.data = {"database_version": 2, "last_updated": None, "seasons": {}}
            self.last_sync = None
            self.load()

    json_db = _LocalOnlyDatabase(args.json_db)

    store = SQLiteStore(args.sqlite_db)

    built = store.build_from_database(json_db)

    print(f"Built {built} matches into {args.sqlite_db}")

    store.close()
