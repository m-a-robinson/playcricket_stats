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
import sqlite3
from datetime import datetime

from playcricket_scorecard import Scorecard


SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "schema.sql"
)

SOURCE_PLAY_CRICKET = "play_cricket"


class SQLiteStore:

    # ==========================================================
    # INITIALISATION
    # ==========================================================

    def __init__(self, filename="playcricket_stats.sqlite"):

        self.filename = filename

        self.conn = sqlite3.connect(self.filename)
        self.conn.execute("PRAGMA foreign_keys = ON")

        self._apply_schema()

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
    def _clean_id(value):

        if value in (None, "", "0", 0):
            return None

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clean_int(value):

        if value in (None, ""):
            return None

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clean_bool(value):

        if value in (None, ""):
            return None

        if isinstance(value, str):
            return 1 if value.strip().lower() in ("1", "yes", "true") else 0

        return 1 if value else 0

    @staticmethod
    def _clean_text(value):

        if value in (None, ""):
            return None

        return str(value)

    # ==========================================================
    # DIMENSION UPSERTS
    # ==========================================================

    def _upsert_club(self, club_id, club_name):

        club_id = self._clean_id(club_id)

        if club_id is None:
            return None

        self.conn.execute(
            """
            INSERT INTO clubs (club_id, club_name)
            VALUES (?, ?)
            ON CONFLICT(club_id) DO UPDATE SET
                club_name = excluded.club_name
            """,
            (club_id, self._clean_text(club_name))
        )

        return club_id

    def _upsert_team(self, team_id, team_name, club_id):

        team_id = self._clean_id(team_id)

        if team_id is None:
            return None

        self.conn.execute(
            """
            INSERT INTO teams (team_id, team_name, club_id)
            VALUES (?, ?, ?)
            ON CONFLICT(team_id) DO UPDATE SET
                team_name = excluded.team_name,
                club_id = excluded.club_id
            """,
            (team_id, self._clean_text(team_name), club_id)
        )

        return team_id

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
            match.get("home_club_id"), match.get("home_club_name")
        )
        away_club_id = self._upsert_club(
            match.get("away_club_id"), match.get("away_club_name")
        )

        home_team_id = self._upsert_team(
            match.get("home_team_id"), match.get("home_team_name"), home_club_id
        )
        away_team_id = self._upsert_team(
            match.get("away_team_id"), match.get("away_team_name"), away_club_id
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
                self._clean_id(match.get("toss_won_by_team_id")),
                self._clean_text(match.get("result")),
                self._clean_id(match.get("result_applied_to")),
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

            team_batting_id = self._clean_id(
                innings_row.get("team_batting_id")
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
                        self._clean_id(player_row.get("team_id")),
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
                        self._clean_id(bat_row.get("team_id")),
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
                        self._clean_id(bowl_row.get("team_id")),
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
