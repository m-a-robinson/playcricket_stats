#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 23 09:19:16 2026

@author: SPSMROBI

MultiPlayerStats

Provides comparative statistical tables for multiple players.

This class sits above PlayerPerformances and is designed to answer
questions such as:

    - How do our players compare for batting average?
    - Who has scored the most runs?
    - Who has the best bowling average?
    - Who has taken the most wickets?
    - Who has played the most games?
    - How do players within a particular team compare?

Club-level results such as win percentage, results against opposition,
and season results are deliberately handled separately by
ClubStatistics.
"""

import pandas as pd


class MultiPlayerStats:
    """
    Creates comparative player statistics from a PlayerPerformances
    object.

    PlayerPerformances remains responsible for calculating individual
    player statistics.

    MultiPlayerRecords is responsible for:

        - selecting players
        - filtering by season/team
        - producing comparison tables
        - sorting players by statistical measures
    """

    # ==========================================================
    # INITIALISATION
    # ==========================================================

    def __init__(self, player_performances):
        """
        Initialise MultiPlayerStats.

        Parameters
        ----------
        player_performances : PlayerPerformances
            An existing PlayerPerformances object.
        """

        self.players = player_performances

    # ==========================================================
    # ALL PLAYER RECORDS
    # ==========================================================

    def all(
        self,
        season=None,
        team_id=None
    ):
        """
        Return complete statistical records for all players.

        Players are selected from participation records, meaning
        players who appeared but did not bat or bowl are retained.
        """

        return self.players.get_all(
            season=season,
            team_id=team_id
        ).copy()

    # ==========================================================
    # PARTICIPATION
    # ==========================================================

    def participation(
        self,
        season=None,
        team_id=None
    ):
        """
        Return a comparison table of player participation.
        """

        data = self.all(
            season=season,
            team_id=team_id
        )

        if data.empty:
            return data

        columns = [
            "player_id",
            "player_name",
            "games_played"
        ]

        return (
            data[columns]
            .sort_values(
                "games_played",
                ascending=False
            )
            .reset_index(drop=True)
        )

    # ==========================================================
    # BATTING
    # ==========================================================

    def batting(
        self,
        season=None,
        team_id=None
    ):
        """
        Return a comparative batting statistics table.
        """

        data = self.all(
            season=season,
            team_id=team_id
        )

        if data.empty:
            return data

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "batting_innings",
            "runs",
            "times_dismissed",
            "batting_average",
            "highest_score",
            "fifties",
            "hundreds",
            "double_hundreds",
            "fours",
            "sixes",
            "balls_faced",
            "strike_rate"
        ]

        return (
            data[columns]
            .sort_values(
                "runs",
                ascending=False
            )
            .reset_index(drop=True)
        )

    # ==========================================================
    # BOWLING
    # ==========================================================

    def bowling(
        self,
        season=None,
        team_id=None
    ):
        """
        Return a comparative bowling statistics table.
        """

        data = self.all(
            season=season,
            team_id=team_id
        )

        if data.empty:
            return data

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "bowling_innings",
            "balls_bowled",
            "runs_conceded",
            "wickets",
            "maidens",
            "bowling_average",
            "economy",
            "bowling_strike_rate",
            "wides",
            "no_balls"
        ]

        return (
            data[columns]
            .sort_values(
                "wickets",
                ascending=False
            )
            .reset_index(drop=True)
        )

    # ==========================================================
    # FIELDING
    # ==========================================================

    def fielding(
        self,
        season=None,
        team_id=None
    ):
        """
        Return a comparative fielding statistics table.
        """

        data = self.all(
            season=season,
            team_id=team_id
        )

        if data.empty:
            return data

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "catches",
            "stumpings",
            "run_outs",
            "fielding_dismissals"
        ]

        return (
            data[columns]
            .sort_values(
                "fielding_dismissals",
                ascending=False
            )
            .reset_index(drop=True)
        )

    # ==========================================================
    # HIGHLIGHTS
    # ==========================================================

    def highlights(
        self,
        season=None,
        team_id=None
    ):
        """
        Return notable performance counts for all players.
        """

        data = self.all(
            season=season,
            team_id=team_id
        )

        if data.empty:
            return data

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "notable_performances"
        ]

        return (
            data[columns]
            .sort_values(
                "notable_performances",
                ascending=False
            )
            .reset_index(drop=True)
        )

    # ==========================================================
    # SUMMARY TABLE
    # ==========================================================

    def summary(
        self,
        season=None,
        team_id=None
    ):
        """
        Return a high-level comparison table combining batting,
        bowling and fielding statistics.
        """

        data = self.all(
            season=season,
            team_id=team_id
        )

        if data.empty:
            return data

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "runs",
            "batting_average",
            "highest_score",
            "wickets",
            "bowling_average",
            "economy",
            "catches",
            "stumpings",
            "run_outs",
            "fielding_dismissals",
            "notable_performances"
        ]

        return (
            data[columns]
            .sort_values(
                "games_played",
                ascending=False
            )
            .reset_index(drop=True)
        )