#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MultiPlayerStats
================

Comparative statistical tables for multiple players.

This class does NOT access the Play-Cricket API.

It relies entirely on an existing PlayerPerformances object.

Architecture:

    Database
        |
        v
    PlayerPerformances
        |
        v
    MultiPlayerStats

MultiPlayerStats is responsible for:

    - comparing players
    - filtering by season
    - filtering by team
    - applying qualification criteria
    - ranking players
    - producing comparative tables

Club-level statistics such as:

    - wins
    - losses
    - draws
    - results against opposition
    - win percentage

should be handled separately by ClubStatistics.
"""

import pandas as pd


class MultiPlayerStats:

    # ==========================================================
    # INITIALISATION
    # ==========================================================

    def __init__(self, player_performances):

        self.players = player_performances

    # ==========================================================
    # INTERNAL DATA ACCESS
    # ==========================================================

    def _all(
        self,
        season=None,
        team_id=None
    ):
        """
        Return complete player summaries.
    
        PlayerPerformances defines the match/season selection.
        MultiPlayerStats applies any additional team filtering.
        """
    
        data = self.players.summary().copy()
    
        # ------------------------------------------------------
        # Optional season filter
        # ------------------------------------------------------
    
        if season is not None and "season" in data.columns:
    
            data = data[
                data["season"] == season
            ]
    
        # ------------------------------------------------------
        # Optional team filter
        # ------------------------------------------------------
    
        if team_id is not None:
    
            data = data[
                data["team_id"] == team_id
            ]
    
        return data.reset_index(
            drop=True
        )

    # ==========================================================
    # INTERNAL TABLE BUILDER
    # ==========================================================

    def _table(
        self,
        columns,
        sort_by,
        season=None,
        team_id=None,
        ascending=False
    ):
        """
        Build a standard comparative player table.
        """

        data = self._all(
            season=season,
            team_id=team_id
        )

        if data.empty:
            return data

        columns = [
            column
            for column in columns
            if column in data.columns
        ]

        if sort_by not in data.columns:

            return data[
                columns
            ].reset_index(
                drop=True
            )

        return (
            data[
                columns
            ]
            .sort_values(
                sort_by,
                ascending=ascending,
                na_position="last"
            )
            .reset_index(
                drop=True
            )
        )

    # ==========================================================
    # INTERNAL LEADERBOARD BUILDER
    # ==========================================================

    def _leaderboard(
        self,
        columns,
        sort_by,
        season=None,
        team_id=None,
        top_n=10,
        ascending=False,
        filters=None,
        data=None
    ):
        """
        Build a ranked leaderboard.

        Parameters
        ----------
        columns : list
            Columns to display.

        sort_by : str
            Statistic used for ranking.

        season : int, optional
            Season filter.

        team_id : int, optional
            Team filter.

        top_n : int
            Number of ranking positions to return.
            
            Tied players share the same rank, so the returned
            dataframe may contain more than top_n players.

        ascending : bool
            False = highest is best.
            True = lowest is best.

        filters : callable, optional
            Additional dataframe filter.

        data : DataFrame, optional
            Existing dataframe. If supplied, this is used instead
            of loading the data again.
        """

        if data is None:

            data = self._all(
                season=season,
                team_id=team_id
            )

        else:

            data = data.copy()

        if data.empty:

            return pd.DataFrame(
                columns=[
                    "rank"
                ] + columns
            )

        if sort_by not in data.columns:

            return pd.DataFrame(
                columns=[
                    "rank"
                ] + columns
            )

        # ------------------------------------------------------
        # Apply optional qualification filter
        # ------------------------------------------------------

        if filters is not None:

            data = filters(
                data
            )

        if data.empty:

            return pd.DataFrame(
                columns=[
                    "rank"
                ] + columns
            )

        # ------------------------------------------------------
        # Only rank actual values
        # ------------------------------------------------------

        data = data[
            data[sort_by].notna()
        ].copy()

        if data.empty:

            return pd.DataFrame(
                columns=[
                    "rank"
                ] + columns
            )

        # ------------------------------------------------------
        # Keep valid columns
        # ------------------------------------------------------

        columns = [
            column
            for column in columns
            if column in data.columns
        ]

        # ------------------------------------------------------
        # Sort
        # ------------------------------------------------------

        data = data.sort_values(
            sort_by,
            ascending=ascending,
            na_position="last"
        )

        # ------------------------------------------------------
        # Rank
        # ------------------------------------------------------

        data["rank"] = (
            data[sort_by]
            .rank(
                method="min",
                ascending=ascending
            )
            .astype(int)
        )

        # ------------------------------------------------------
        # Keep top ranking positions
        # ------------------------------------------------------


        # Ties are deliberately retained. For example, if two
        # players are joint 10th, both are returned.
        data = data[
            data["rank"] <= int(top_n)
        ]

        return data[
            ["rank"] + columns
        ].reset_index(
            drop=True
        )

    # ==========================================================
    # ALL PLAYER STATISTICS
    # ==========================================================

    def all(
        self,
        season=None,
        team_id=None
    ):

        return self._all(
            season=season,
            team_id=team_id
        )

    # ==========================================================
    # PARTICIPATION
    # ==========================================================

    def participation(
        self,
        season=None,
        team_id=None
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played"
        ]

        return self._table(
            columns=columns,
            sort_by="games_played",
            season=season,
            team_id=team_id
        )

    # ==========================================================
    # BATTING
    # ==========================================================

    def batting(
        self,
        season=None,
        team_id=None
    ):

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

        return self._table(
            columns=columns,
            sort_by="runs",
            season=season,
            team_id=team_id
        )

    # ==========================================================
    # BOWLING
    # ==========================================================

    def bowling(
        self,
        season=None,
        team_id=None
    ):

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

        return self._table(
            columns=columns,
            sort_by="wickets",
            season=season,
            team_id=team_id
        )

    # ==========================================================
    # FIELDING
    # ==========================================================

    def fielding(
        self,
        season=None,
        team_id=None
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "catches",
            "stumpings",
            "run_outs",
            "fielding_dismissals"
        ]

        return self._table(
            columns=columns,
            sort_by="fielding_dismissals",
            season=season,
            team_id=team_id
        )

    # ==========================================================
    # HIGHLIGHTS
    # ==========================================================

    def highlights(
        self,
        season=None,
        team_id=None
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "notable_performances"
        ]

        return self._table(
            columns=columns,
            sort_by="notable_performances",
            season=season,
            team_id=team_id
        )

    # ==========================================================
    # OVERALL SUMMARY
    # ==========================================================

    def summary(
        self,
        season=None,
        team_id=None
    ):

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

        return self._table(
            columns=columns,
            sort_by="games_played",
            season=season,
            team_id=team_id
        )

    # ==========================================================
    # TOP GAMES
    # ==========================================================

    def top_games(
        self,
        season=None,
        team_id=None,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played"
        ]

        return self._leaderboard(
            columns=columns,
            sort_by="games_played",
            season=season,
            team_id=team_id,
            top_n=top_n
        )

    # ==========================================================
    # TOP RUNS
    # ==========================================================

    def top_runs(
        self,
        season=None,
        team_id=None,
        top_n=10,
        min_batting_innings=0
    ):

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
            "balls_faced",
            "strike_rate"
        ]

        def qualification(data):

            return data[
                data["batting_innings"]
                >= min_batting_innings
            ].copy()

        return self._leaderboard(
            columns=columns,
            sort_by="runs",
            season=season,
            team_id=team_id,
            top_n=top_n,
            filters=qualification
        )

    # ==========================================================
    # TOP BATTING AVERAGE
    # ==========================================================

    def top_batting_average(
        self,
        season=None,
        team_id=None,
        min_batting_innings=5,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "batting_innings",
            "runs",
            "times_dismissed",
            "batting_average",
            "highest_score",
            "strike_rate"
        ]

        def qualification(data):

            return data[
                (data["batting_innings"]
                 >= min_batting_innings)
                &
                (data["batting_average"].notna())
            ].copy()

        return self._leaderboard(
            columns=columns,
            sort_by="batting_average",
            season=season,
            team_id=team_id,
            top_n=top_n,
            filters=qualification
        )

    # ==========================================================
    # TOP STRIKE RATE
    # ==========================================================

    def top_strike_rate(
        self,
        season=None,
        team_id=None,
        min_batting_innings=5,
        min_runs=50,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "batting_innings",
            "runs",
            "balls_faced",
            "strike_rate"
        ]

        def qualification(data):

            return data[
                (data["batting_innings"]
                 >= min_batting_innings)
                &
                (data["runs"]
                 >= min_runs)
                &
                (data["strike_rate"].notna())
            ].copy()

        return self._leaderboard(
            columns=columns,
            sort_by="strike_rate",
            season=season,
            team_id=team_id,
            top_n=top_n,
            filters=qualification
        )

    # ==========================================================
    # TOP SCORES
    # ==========================================================

    def top_scores(
        self,
        season=None,
        team_id=None,
        min_batting_innings=0,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "batting_innings",
            "runs",
            "highest_score"
        ]

        def qualification(data):

            return data[
                (data["batting_innings"]
                 >= min_batting_innings)
                &
                (data["highest_score"].notna())
            ].copy()

        return self._leaderboard(
            columns=columns,
            sort_by="highest_score",
            season=season,
            team_id=team_id,
            top_n=top_n,
            filters=qualification
        )

    # ==========================================================
    # TOP FIFTIES
    # ==========================================================

    def top_fifties(
        self,
        season=None,
        team_id=None,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "runs",
            "fifties",
            "hundreds",
            "highest_score"
        ]

        return self._leaderboard(
            columns=columns,
            sort_by="fifties",
            season=season,
            team_id=team_id,
            top_n=top_n
        )

    # ==========================================================
    # TOP HUNDREDS
    # ==========================================================

    def top_hundreds(
        self,
        season=None,
        team_id=None,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "runs",
            "fifties",
            "hundreds",
            "double_hundreds",
            "highest_score"
        ]

        return self._leaderboard(
            columns=columns,
            sort_by="hundreds",
            season=season,
            team_id=team_id,
            top_n=top_n
        )

    # ==========================================================
    # TOP WICKETS
    # ==========================================================

    def top_wickets(
        self,
        season=None,
        team_id=None,
        min_bowling_innings=0,
        top_n=10
    ):

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
            "bowling_strike_rate"
        ]

        def qualification(data):

            return data[
                data["bowling_innings"]
                >= min_bowling_innings
            ].copy()

        return self._leaderboard(
            columns=columns,
            sort_by="wickets",
            season=season,
            team_id=team_id,
            top_n=top_n,
            filters=qualification
        )

    # ==========================================================
    # TOP BOWLING AVERAGE
    # ==========================================================

    def top_bowling_average(
        self,
        season=None,
        team_id=None,
        min_bowling_innings=5,
        min_wickets=5,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "bowling_innings",
            "wickets",
            "runs_conceded",
            "bowling_average",
            "economy",
            "bowling_strike_rate"
        ]

        def qualification(data):

            return data[
                (data["bowling_innings"]
                 >= min_bowling_innings)
                &
                (data["wickets"]
                 >= min_wickets)
                &
                (data["bowling_average"].notna())
            ].copy()

        return self._leaderboard(
            columns=columns,
            sort_by="bowling_average",
            season=season,
            team_id=team_id,
            top_n=top_n,
            ascending=True,
            filters=qualification
        )

    # ==========================================================
    # TOP ECONOMY
    # ==========================================================

    def top_economy(
        self,
        season=None,
        team_id=None,
        min_bowling_innings=5,
        min_wickets=5,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "bowling_innings",
            "balls_bowled",
            "wickets",
            "runs_conceded",
            "economy",
            "bowling_average",
            "bowling_strike_rate"
        ]

        def qualification(data):

            return data[
                (data["bowling_innings"]
                 >= min_bowling_innings)
                &
                (data["wickets"]
                 >= min_wickets)
                &
                (data["economy"].notna())
            ].copy()

        return self._leaderboard(
            columns=columns,
            sort_by="economy",
            season=season,
            team_id=team_id,
            top_n=top_n,
            ascending=True,
            filters=qualification
        )

    # ==========================================================
    # TOP BOWLING STRIKE RATE
    # ==========================================================

    def top_bowling_strike_rate(
        self,
        season=None,
        team_id=None,
        min_bowling_innings=5,
        min_wickets=5,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "bowling_innings",
            "balls_bowled",
            "wickets",
            "bowling_strike_rate",
            "bowling_average",
            "economy"
        ]

        def qualification(data):

            return data[
                (data["bowling_innings"]
                 >= min_bowling_innings)
                &
                (data["wickets"]
                 >= min_wickets)
                &
                (data["bowling_strike_rate"].notna())
            ].copy()

        return self._leaderboard(
            columns=columns,
            sort_by="bowling_strike_rate",
            season=season,
            team_id=team_id,
            top_n=top_n,
            ascending=True,
            filters=qualification
        )

    # ==========================================================
    # TOP CATCHES
    # ==========================================================

    def top_catches(
        self,
        season=None,
        team_id=None,
        min_games=0,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "catches",
            "stumpings",
            "run_outs",
            "fielding_dismissals"
        ]

        def qualification(data):

            return data[
                data["games_played"]
                >= min_games
            ].copy()

        return self._leaderboard(
            columns=columns,
            sort_by="catches",
            season=season,
            team_id=team_id,
            top_n=top_n,
            filters=qualification
        )

    # ==========================================================
    # TOP FIELDING
    # ==========================================================

    def top_fielding(
        self,
        season=None,
        team_id=None,
        min_games=0,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "catches",
            "stumpings",
            "run_outs",
            "fielding_dismissals"
        ]

        def qualification(data):

            return data[
                data["games_played"]
                >= min_games
            ].copy()

        return self._leaderboard(
            columns=columns,
            sort_by="fielding_dismissals",
            season=season,
            team_id=team_id,
            top_n=top_n,
            filters=qualification
        )

    # ==========================================================
    # TOP HIGHLIGHTS
    # ==========================================================

    def top_highlights(
        self,
        season=None,
        team_id=None,
        top_n=10
    ):

        columns = [
            "player_id",
            "player_name",
            "games_played",
            "runs",
            "highest_score",
            "wickets",
            "notable_performances"
        ]

        return self._leaderboard(
            columns=columns,
            sort_by="notable_performances",
            season=season,
            team_id=team_id,
            top_n=top_n
        )