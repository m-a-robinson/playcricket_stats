#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 15:13:30 2026

@author: SPSMROBI
"""
import pandas as pd


class PlayerPerformances:
    """
    Aggregates player participation and statistical performance
    across multiple Scorecard objects.

    The class deliberately separates:

        participation
            Players who appeared in a match.

        batting_records
            Players who recorded a batting innings.

        bowling_records
            Players who recorded a bowling innings.

        fielding_records
            Fielding/dismissal records derived from batting data.

        highlight_records
            Notable performances identified by Scorecard.

    This allows games played to be counted independently from
    batting and bowling appearances.
    """

    # ==========================================================
    # INITIALISATION
    # ==========================================================
    def __init__(self, scorecards, club_id=None):

        self.scorecards = scorecards
        self.club_id = club_id

        # Core datasets
        self.participation = self._load_participation()
        self.batting_records = self._load_batting()
        self.bowling_records = self._load_bowling()
        self.fielding_records = self._load_fielding()
        self.highlight_records = self._load_highlights()

    # ==========================================================
    # MATCH METADATA
    # ==========================================================

    def _match_metadata(self, scorecard):
        """
        Return common match metadata for a Scorecard.
        """

        match = scorecard.match.iloc[0]

        return {
            "season": scorecard.season,
            "match_id": scorecard.match_id,
            "match_date": match.get("match_date"),
            "competition_name": match.get("competition_name"),
            "competition_id": match.get("competition_id"),
            "competition_type": match.get("competition_type"),
            "match_type": match.get("match_type"),
            "game_type": match.get("game_type"),
            "ground_name": match.get("ground_name"),
        }

    # ==========================================================
    # PARTICIPATION
    # ==========================================================

    def _load_participation(self):
        """
        Load every player listed as playing in every match.

        This is the master player population.

        A player is considered to have played if they appear in
        scorecard.players, regardless of whether they batted or bowled.
        """

        data = []

        for scorecard in self.scorecards:

            if (
                scorecard.players is None
                or scorecard.players.empty
            ):
                continue

            players = scorecard.players.copy()

            metadata = self._match_metadata(scorecard)

            for key, value in metadata.items():
                players[key] = value

            data.append(players)

        if not data:
            return pd.DataFrame()

        data = pd.concat(
            data,
            ignore_index=True
        )

        # Remove accidental duplicate player/match records
        data = data.drop_duplicates(
            subset=[
                "match_id",
                "player_id",
                "team_id"
            ]
        )

        return data.reset_index(drop=True)
    
    def get_participation(
        self,
        player_id=None,
        season=None,
        team_id=None,
        opposition_id=None
    ):

        return self._filter(
            self.participation,
            player_id=player_id,
            season=season,
            team_id=team_id,
            opposition_id=opposition_id
        )

    # ==========================================================
    # BATTING
    # ==========================================================

    def _load_batting(self):
        """
        Load all batting records from all Scorecards.
        """

        data = []

        for scorecard in self.scorecards:

            if (
                scorecard.batting is None
                or scorecard.batting.empty
            ):
                continue

            batting = scorecard.batting.copy()

            metadata = self._match_metadata(scorecard)

            for key, value in metadata.items():
                batting[key] = value

            data.append(batting)

        if not data:
            return pd.DataFrame()

        return pd.concat(
            data,
            ignore_index=True
        )

    # ==========================================================
    # BOWLING
    # ==========================================================

    def _load_bowling(self):
        """
        Load all bowling records from all Scorecards.
        """

        data = []

        for scorecard in self.scorecards:

            if (
                scorecard.bowling is None
                or scorecard.bowling.empty
            ):
                continue

            bowling = scorecard.bowling.copy()

            metadata = self._match_metadata(scorecard)

            for key, value in metadata.items():
                bowling[key] = value

            data.append(bowling)

        if not data:
            return pd.DataFrame()

        return pd.concat(
            data,
            ignore_index=True
        )

    # ==========================================================
    # FIELDING
    # ==========================================================

    def _load_fielding(self):
        """
        Load fielding/dismissal records.

        Fielding information is contained within the batting
        dataframe because each dismissal records:

            fielder_name
            fielder_id
            how_out

        Individual dismissal records are retained here so that
        catches, stumpings and run outs can be analysed separately.
        """

        data = []

        for scorecard in self.scorecards:

            if (
                scorecard.batting is None
                or scorecard.batting.empty
            ):
                continue

            fielding = scorecard.batting.copy()

            metadata = self._match_metadata(scorecard)

            for key, value in metadata.items():
                fielding[key] = value

            data.append(fielding)

        if not data:
            return pd.DataFrame()

        data = pd.concat(
            data,
            ignore_index=True
        )

        # Only rows where a fielder is recorded
        data = data[
            data["fielder_id"].notna()
            & (
                data["fielder_id"]
                .astype(str)
                .str.strip()
                != ""
            )
        ].copy()

        # Standardise dismissal description
        data["how_out_clean"] = (
            data["how_out"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.strip()
        )

        return data.reset_index(drop=True)

    # ==========================================================
    # HIGHLIGHTS
    # ==========================================================

    def _load_highlights(self):
        """
        Load notable performances identified by Scorecard.
        """

        data = []

        for scorecard in self.scorecards:

            if (
                scorecard.performances is None
                or scorecard.performances.empty
            ):
                continue

            performances = (
                scorecard.performances.copy()
            )

            metadata = self._match_metadata(scorecard)

            for key, value in metadata.items():
                performances[key] = value

            data.append(performances)

        if not data:
            return pd.DataFrame()

        return pd.concat(
            data,
            ignore_index=True
        )

    # ==========================================================
    # FILTERING HELPERS
    # ==========================================================
    
    def _filter(
        self,
        data,
        player_id=None,
        season=None,
        team_id=None,
        opposition_id=None
    ):
        """
        Apply common filters to a player record dataframe.
    
        Player IDs are normalised before comparison so that integer
        and floating-point representations of the same Play-Cricket
        ID are treated as identical.
    
        Club membership is determined from participation records.
        This means batting, bowling, fielding and highlight records
        can all be restricted to the selected club even where those
        records do not contain club_id directly.
        """
    
        result = data.copy()
    
        if result.empty:
            return result
    
        # ------------------------------------------------------
        # HELPER FOR PLAY-CRICKET IDS
        # ------------------------------------------------------
    
        def normalise_id(series):
    
            numeric = pd.to_numeric(
                series,
                errors="coerce"
            )
    
            return numeric.astype("Int64")
    
        # ------------------------------------------------------
        # IDENTIFY PLAYER ID COLUMN
        # ------------------------------------------------------
    
        id_column = None
    
        if "player_id" in result.columns:
            id_column = "player_id"
    
        elif "batsman_id" in result.columns:
            id_column = "batsman_id"
    
        elif "bowler_id" in result.columns:
            id_column = "bowler_id"
    
        elif "fielder_id" in result.columns:
            id_column = "fielder_id"
    
        # ------------------------------------------------------
        # CLUB
        # ------------------------------------------------------
    
        if self.club_id is not None:
    
            # If the dataframe contains club_id directly
            if "club_id" in result.columns:
    
                result = result[
                    normalise_id(result["club_id"])
                    == int(self.club_id)
                ]
    
            # Otherwise determine club membership from
            # participation records
            elif id_column is not None:
    
                club_players = self.participation[
                    normalise_id(
                        self.participation["club_id"]
                    )
                    == int(self.club_id)
                ]
    
                allowed_player_ids = set(
                    normalise_id(
                        club_players["player_id"]
                    ).dropna()
                )
    
                result = result[
                    normalise_id(
                        result[id_column]
                    ).isin(allowed_player_ids)
                ]
    
        # ------------------------------------------------------
        # PLAYER ID
        # ------------------------------------------------------
    
        if player_id is not None:
    
            if id_column is None:
    
                raise KeyError(
                    "Could not identify a player ID column "
                    "in dataframe."
                )
    
            result = result[
                normalise_id(result[id_column])
                == int(player_id)
            ]
    
        # ------------------------------------------------------
        # SEASON
        # ------------------------------------------------------
    
        if season is not None:
    
            if "season" in result.columns:
    
                result = result[
                    result["season"] == season
                ]
    
        # ------------------------------------------------------
        # TEAM
        # ------------------------------------------------------
    
        if team_id is not None:
    
            if "team_id" in result.columns:
    
                result = result[
                    normalise_id(result["team_id"])
                    == int(team_id)
                ]
    
        # ------------------------------------------------------
        # OPPOSITION
        # ------------------------------------------------------
    
        if opposition_id is not None:
    
            if "opposition_id" in result.columns:
    
                result = result[
                    normalise_id(result["opposition_id"])
                    == int(opposition_id)
                ]
    
        return result.copy()
    
    
    # ==========================================================
    # PLAYER IDENTIFICATION
    # ==========================================================

    def get_player(
        self,
        player_id,
        season=None,
        team_id=None
    ):
        """
        Return participation records for a player.

        This is deliberately based on participation rather than
        batting/bowling records.
        """

        return self._filter(
            self.participation,
            player_id=player_id,
            season=season,
            team_id=team_id
        )

    # ==========================================================
    # PARTICIPATION
    # ==========================================================

    def participation_records(
        self,
        player_id=None,
        season=None,
        team_id=None
    ):
        """
        Return player participation records.
        """

        return self._filter(
            self.participation,
            player_id=player_id,
            season=season,
            team_id=team_id
        )

    # ==========================================================
    # BATTING
    # ==========================================================

    def batting(
        self,
        player_id=None,
        season=None,
        team_id=None
    ):
        """
        Return batting records.
        """

        return self._filter(
            self.batting_records,
            player_id=player_id,
            season=season,
            team_id=team_id
        ).copy()

    # ==========================================================
    # BOWLING
    # ==========================================================

    def bowling(
        self,
        player_id=None,
        season=None,
        team_id=None
    ):
        """
        Return bowling records.
        """

        return self._filter(
            self.bowling_records,
            player_id=player_id,
            season=season,
            team_id=team_id
        ).copy()

    # ==========================================================
    # FIELDING
    # ==========================================================

    def fielding(
        self,
        player_id=None,
        season=None,
        team_id=None
    ):
        """
        Return individual fielding/dismissal records.
        """

        return self._filter(
            self.fielding_records,
            player_id=player_id,
            season=season,
            team_id=team_id
        ).copy()

    # ==========================================================
    # HIGHLIGHTS
    # ==========================================================

    def highlights(
        self,
        player_id=None,
        season=None,
        team_id=None
    ):
        """
        Return notable performances.
        """

        return self._filter(
            self.highlight_records,
            player_id=player_id,
            season=season,
            team_id=team_id
        ).copy()

    # ==========================================================
    # PLAYER SUMMARY
    # ==========================================================

    def summary(
        self,
        player_id,
        season=None,
        team_id=None
    ):
        """
        Return a complete statistical summary for one player.

        games_played is calculated independently from batting
        and bowling appearances.
        """

        participation = self._filter(
            self.participation,
            player_id=player_id,
            season=season,
            team_id=team_id
        )

        if participation.empty:
            return pd.DataFrame()

        # ------------------------------------------------------
        # PLAYER NAME
        # ------------------------------------------------------

        player_name = (
            participation["player_name"]
            .iloc[0]
        )

        # ------------------------------------------------------
        # GAMES PLAYED
        # ------------------------------------------------------

        games_played = (
            participation["match_id"]
            .nunique()
        )

        # ------------------------------------------------------
        # BATTING DATA
        # ------------------------------------------------------

        batting = self.batting(
            player_id=player_id,
            season=season,
            team_id=team_id
        )

        batting_innings = 0
        runs = 0
        balls_faced = 0
        fours = 0
        sixes = 0
        times_dismissed = 0
        highest_score = 0

        if not batting.empty:

            batting_innings = (
                batting[
                    ["match_id", "innings"]
                ]
                .drop_duplicates()
                .shape[0]
            )

            runs = int(
                pd.to_numeric(
                    batting["runs"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            balls_faced = int(
                pd.to_numeric(
                    batting["balls"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            fours = int(
                pd.to_numeric(
                    batting["fours"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            sixes = int(
                pd.to_numeric(
                    batting["sixes"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            times_dismissed = int(
                (batting["not_out"] == 0).sum()
            )

            highest_score = int(
                pd.to_numeric(
                    batting["runs"],
                    errors="coerce"
                )
                .fillna(0)
                .max()
            )

        # ------------------------------------------------------
        # BATTING DERIVED STATISTICS
        # ------------------------------------------------------

        batting_average = (
            runs / times_dismissed
            if times_dismissed > 0
            else None
        )

        strike_rate = (
            runs / balls_faced * 100
            if balls_faced > 0
            else None
        )

        fifties = 0
        hundreds = 0
        double_hundreds = 0

        if not batting.empty:

            batting_runs = pd.to_numeric(
                batting["runs"],
                errors="coerce"
            ).fillna(0)

            fifties = int(
                (
                    (batting_runs >= 50)
                    & (batting_runs < 100)
                ).sum()
            )

            hundreds = int(
                (
                    (batting_runs >= 100)
                    & (batting_runs < 200)
                ).sum()
            )

            double_hundreds = int(
                (batting_runs >= 200).sum()
            )

        # ------------------------------------------------------
        # BOWLING DATA
        # ------------------------------------------------------

        bowling = self.bowling(
            player_id=player_id,
            season=season,
            team_id=team_id
        )

        bowling_innings = 0
        balls_bowled = 0
        runs_conceded = 0
        wickets = 0
        maidens = 0
        wides = 0
        no_balls = 0

        if not bowling.empty:

            bowling_innings = (
                bowling[
                    ["match_id", "innings"]
                ]
                .drop_duplicates()
                .shape[0]
            )

            balls_bowled = int(
                pd.to_numeric(
                    bowling["balls"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            runs_conceded = int(
                pd.to_numeric(
                    bowling["runs"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            wickets = int(
                pd.to_numeric(
                    bowling["wickets"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            maidens = int(
                pd.to_numeric(
                    bowling["maidens"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            wides = int(
                pd.to_numeric(
                    bowling["wides"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            no_balls = int(
                pd.to_numeric(
                    bowling["no_balls"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

        # ------------------------------------------------------
        # BOWLING DERIVED STATISTICS
        # ------------------------------------------------------

        bowling_average = (
            runs_conceded / wickets
            if wickets > 0
            else None
        )

        economy = (
            runs_conceded
            / (balls_bowled / 6)
            if balls_bowled > 0
            else None
        )

        bowling_strike_rate = (
            balls_bowled / wickets
            if wickets > 0
            else None
        )

        # ------------------------------------------------------
        # FIELDING
        # ------------------------------------------------------

        fielding = self.fielding(
            player_id=player_id,
            season=season,
            team_id=team_id
        )

        catches = 0
        stumpings = 0
        run_outs = 0
        fielding_dismissals = 0

        if not fielding.empty:

            how_out = (
                fielding["how_out_clean"]
                .astype(str)
            )

            catches = int(
                (how_out == "ct").sum()
            )

            stumpings = int(
                (how_out == "st").sum()
            )

            run_outs = int(
                (how_out == "ro").sum()
            )

            fielding_dismissals = (
                catches
                + stumpings
                + run_outs
            )

        # ------------------------------------------------------
        # HIGHLIGHTS
        # ------------------------------------------------------

        highlights = self.highlights(
            player_id=player_id,
            season=season,
            team_id=team_id
        )

        notable_performances = (
            len(highlights)
            if not highlights.empty
            else 0
        )

        # ------------------------------------------------------
        # RETURN SUMMARY
        # ------------------------------------------------------

        return pd.DataFrame([{

            # Identity
            "player_id": player_id,
            "player_name": player_name,

            # Participation
            "games_played": games_played,

            # Batting
            "batting_innings": batting_innings,
            "runs": runs,
            "times_dismissed": times_dismissed,
            "batting_average": batting_average,
            "highest_score": highest_score,
            "fifties": fifties,
            "hundreds": hundreds,
            "double_hundreds": double_hundreds,
            "fours": fours,
            "sixes": sixes,
            "balls_faced": balls_faced,
            "strike_rate": strike_rate,

            # Bowling
            "bowling_innings": bowling_innings,
            "balls_bowled": balls_bowled,
            "runs_conceded": runs_conceded,
            "wickets": wickets,
            "maidens": maidens,
            "bowling_average": bowling_average,
            "economy": economy,
            "bowling_strike_rate": bowling_strike_rate,
            "wides": wides,
            "no_balls": no_balls,

            # Fielding
            "catches": catches,
            "stumpings": stumpings,
            "run_outs": run_outs,
            "fielding_dismissals": fielding_dismissals,

            # Highlights
            "notable_performances": notable_performances,

        }])

    # ==========================================================
    # ALL PLAYER SUMMARIES
    # ==========================================================
    
    def get_all(
        self,
        season=None,
        team_id=None
    ):
        """
        Return a complete statistical summary for every registered
        Play-Cricket player who participated in the selected
        season/team.
    
        Players without a Play-Cricket player_id are retained in the
        underlying participation data but are currently excluded from
        the statistical summary because they cannot be reliably
        matched across scorecards.
        """
    
        participation = self._filter(
            self.participation,
            season=season,
            team_id=team_id
        )
    
        if participation.empty:
            return pd.DataFrame()
    
        players = (
            participation[
                [
                    "player_id",
                    "player_name"
                ]
            ]
            .dropna(subset=["player_id"])
            .drop_duplicates()
        )
    
        summaries = []
    
        for _, player in players.iterrows():
    
            summary = self.summary(
                player_id=player["player_id"],
                season=season,
                team_id=team_id
            )
    
            if not summary.empty:
                summaries.append(summary)
    
        summaries = [
            s for s in summaries
            if s is not None and not s.empty
        ]
    
        if not summaries:
            return pd.DataFrame()
    
        return pd.concat(
            summaries,
            ignore_index=True
        )
        
    
    # ==========================================================
    # SEASON PLAYER SUMMARY
    # ==========================================================

    def season(
        self,
        season,
        team_id=None
    ):
        """
        Convenience method for a season-wide player summary.
        """

        return self.get_all(
            season=season,
            team_id=team_id
        )

    # ==========================================================
    # TEAM PLAYER SUMMARY
    # ==========================================================

    def team(
        self,
        team_id,
        season=None
    ):
        """
        Convenience method for a team-wide player summary.
        """

        return self.get_all(
            season=season,
            team_id=team_id
        )