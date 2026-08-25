#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
player_performances.py

Player-level performance extraction from Play-Cricket scorecards.

Architecture
------------

    PlayCricketAPI
          |
          v
    PlayCricketDatabase
          |
          v
    Scorecard / raw match detail
          |
          v
    PlayerPerformances
          |
          v
    batting / bowling / fielding / participation


Important
---------

The Play-Cricket match-detail API returns:

{
    "match_details": [
        {
            ...
            "players": [...],
            "innings": [...]
        }
    ]
}

This class therefore works from:

    match["match_details"][0]

rather than assuming that the top-level dictionary is itself
the match record.

The class does NOT:

    - call the Play-Cricket API
    - modify the database
    - save data
    - create Scorecard objects
    - calculate club-wide statistics

It is purely a local analysis/extraction layer.
"""

import pandas as pd
import numpy as np


class PlayerPerformances:

    # ==========================================================
    # INITIALISATION
    # ==========================================================

    def __init__(
        self,
        database,
        season=None,
        match_ids=None,
        club_id=None,
        team_id=None
    ):
        """
        Initialise PlayerPerformances.

        Parameters
        ----------
        database : PlayCricketDatabase
            Local database containing downloaded match details.

        season : int, optional
            Restrict analysis to one season.

        match_ids : list, optional
            Restrict analysis to particular matches.

        club_id : int, optional
            Restrict players to one club.

        team_id : int, optional
            Restrict players to one team.

        Notes
        -----
        No API calls are made.
        """

        self.database = database

        self.season = season
        self.match_ids = (
            set(int(x) for x in match_ids)
            if match_ids is not None
            else None
        )

        self.club_id = (
            int(club_id)
            if club_id is not None
            else None
        )

        self.team_id = (
            int(team_id)
            if team_id is not None
            else None
        )

    # ==========================================================
    # BASIC HELPERS
    # ==========================================================

    @staticmethod
    def _to_int(value):
        """
        Convert a value to int.

        Blank strings and invalid values become None.
        """

        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if value == "":
                return None

        try:
            if pd.isna(value):
                return None
        except Exception:
            pass

        try:
            return int(float(value))

        except (TypeError, ValueError):
            return None

    # ----------------------------------------------------------

    @staticmethod
    def _to_float(value):
        """
        Convert a value to float.

        Blank strings and invalid values become NaN.
        """

        if value is None:
            return np.nan

        if isinstance(value, str):
            value = value.strip()

            if value == "":
                return np.nan

        try:
            return float(value)

        except (TypeError, ValueError):
            return np.nan

    # ----------------------------------------------------------

    @staticmethod
    def _overs_to_balls(value):
        """
        Convert cricket overs notation into legal balls.

        Examples
        --------
        12.0 -> 72
        12.3 -> 75

        IMPORTANT
        ---------
        Cricket notation 12.3 means 12 overs and 3 balls,
        NOT 12.3 decimal overs.

        This method is primarily useful for bowling analysis.
        """

        if value is None:
            return np.nan

        if isinstance(value, str):

            value = value.strip()

            if not value:
                return np.nan

        try:

            value = float(value)

        except (TypeError, ValueError):

            return np.nan

        whole_overs = int(value)

        # Convert decimal representation into the digit after
        # the decimal point.
        decimal_part = round(
            (value - whole_overs) * 10
        )

        return (
            whole_overs * 6
            + decimal_part
        )

    # ==========================================================
    # MATCH EXTRACTION
    # ==========================================================

    @staticmethod
    def _unwrap_match(raw_match):
        """
        Return the actual Play-Cricket match-detail dictionary.
    
        The database stores the raw API response, which normally has
        the structure:
    
            {
                "match_details": [
                    {
                        ...
                    }
                ]
            }
    
        This method unwraps that outer API response.
    
        It also accepts an already-unwrapped match dictionary.
        """
    
        if raw_match is None:
            return None
    
        if not isinstance(raw_match, dict):
            return None
    
        # ----------------------------------------------------------
        # Normal Play-Cricket API response
        # ----------------------------------------------------------
    
        if "match_details" in raw_match:
    
            match_details = raw_match.get(
                "match_details"
            )
    
            if not match_details:
                return None
    
            if isinstance(match_details, list):
    
                if len(match_details) == 0:
                    return None
    
                return match_details[0]
    
            if isinstance(match_details, dict):
                return match_details
    
            return None
    
        # ----------------------------------------------------------
        # Already unwrapped
        # ----------------------------------------------------------
    
        return raw_match

    # ==========================================================
    # MATCH ITERATOR
    # ==========================================================

    def _iter_matches(self):
        """
        Yield locally stored match records which satisfy the
        PlayerPerformances filters.
        """

        seasons = self.database.data.get(
            "seasons",
            {}
        )

        # ------------------------------------------------------
        # Select season
        # ------------------------------------------------------

        if self.season is not None:

            season_key = str(
                int(self.season)
            )

            selected_seasons = {
                season_key:
                    seasons.get(
                        season_key,
                        {}
                    )
            }

        else:

            selected_seasons = seasons

        # ------------------------------------------------------
        # Iterate matches
        # ------------------------------------------------------

        for season_key, season_data in (
            selected_seasons.items()
        ):

            matches = season_data.get(
                "matches",
                {}
            )

            for stored_match_id, raw_match in (
                matches.items()
            ):

                match = self._unwrap_match(
                    raw_match
                )

                if match is None:
                    continue

                match_id = self._to_int(
                    match.get(
                        "match_id",
                        stored_match_id
                    )
                )

                if match_id is None:
                    continue

                # ------------------------------------------------
                # Match ID filter
                # ------------------------------------------------

                if (
                    self.match_ids is not None
                    and match_id not in self.match_ids
                ):
                    continue

                # ------------------------------------------------
                # Club/team filtering is applied later where
                # player team identity is known.
                # ------------------------------------------------

                yield (
                    int(season_key),
                    match
                )

    # ==========================================================
    # TEAM INFORMATION
    # ==========================================================

    @staticmethod
    def _team_information(
        match,
        team_id
    ):
        """
        Return team metadata for a team appearing in a match.

        Returns
        -------
        dict
        """

        team_id = PlayerPerformances._to_int(
            team_id
        )

        home_team_id = (
            PlayerPerformances._to_int(
                match.get(
                    "home_team_id"
                )
            )
        )

        away_team_id = (
            PlayerPerformances._to_int(
                match.get(
                    "away_team_id"
                )
            )
        )

        if team_id == home_team_id:

            return {
                "team_id":
                    home_team_id,

                "team_name":
                    match.get(
                        "home_team_name"
                    ),

                "club_id":
                    PlayerPerformances._to_int(
                        match.get(
                            "home_club_id"
                        )
                    ),

                "club_name":
                    match.get(
                        "home_club_name"
                    ),

                "opposition_id":
                    away_team_id,

                "opposition_name":
                    match.get(
                        "away_team_name"
                    ),

                "opposition_club_id":
                    PlayerPerformances._to_int(
                        match.get(
                            "away_club_id"
                        )
                    ),

                "opposition_club_name":
                    match.get(
                        "away_club_name"
                    )
            }

        if team_id == away_team_id:

            return {
                "team_id":
                    away_team_id,

                "team_name":
                    match.get(
                        "away_team_name"
                    ),

                "club_id":
                    PlayerPerformances._to_int(
                        match.get(
                            "away_club_id"
                        )
                    ),

                "club_name":
                    match.get(
                        "away_club_name"
                    ),

                "opposition_id":
                    home_team_id,

                "opposition_name":
                    match.get(
                        "home_team_name"
                    ),

                "opposition_club_id":
                    PlayerPerformances._to_int(
                        match.get(
                            "home_club_id"
                        )
                    ),

                "opposition_club_name":
                    match.get(
                        "home_club_name"
                    )
            }

        return None

    # ==========================================================
    # PLAYER TEAM SHEET
    # ==========================================================

    def _player_team_records(
        self,
        match,
        season
    ):
        """
        Extract the players recorded on the team sheets.

        Returns
        -------
        list of dict

        One row per:

            match / player / team
        """

        records = []

        players = match.get(
            "players",
            []
        )

        if not isinstance(players, list):
            return records

        for group in players:

            if not isinstance(group, dict):
                continue

            # --------------------------------------------------
            # Home team
            # --------------------------------------------------

            if "home_team" in group:

                team_players = (
                    group.get(
                        "home_team"
                    ) or []
                )

                team_id = self._to_int(
                    match.get(
                        "home_team_id"
                    )
                )

                for player in team_players:

                    if not isinstance(
                        player,
                        dict
                    ):
                        continue

                    player_id = self._to_int(
                        player.get(
                            "player_id"
                        )
                    )

                    if player_id is None:
                        continue

                    records.append({

                        "season":
                            season,

                        "match_id":
                            self._to_int(
                                match.get(
                                    "match_id"
                                )
                            ),

                        "match_date":
                            match.get(
                                "match_date"
                            ),

                        "player_id":
                            player_id,

                        "player_name":
                            player.get(
                                "player_name"
                            ),

                        "team_id":
                            team_id,

                        "team_name":
                            match.get(
                                "home_team_name"
                            ),

                        "club_id":
                            self._to_int(
                                match.get(
                                    "home_club_id"
                                )
                            ),

                        "club_name":
                            match.get(
                                "home_club_name"
                            ),

                        "opposition_id":
                            self._to_int(
                                match.get(
                                    "away_team_id"
                                )
                            ),

                        "opposition_name":
                            match.get(
                                "away_team_name"
                            ),

                        "opposition_club_id":
                            self._to_int(
                                match.get(
                                    "away_club_id"
                                )
                            ),

                        "opposition_club_name":
                            match.get(
                                "away_club_name"
                            ),

                        "position":
                            self._to_int(
                                player.get(
                                    "position"
                                )
                            ),

                        "captain":
                            bool(
                                player.get(
                                    "captain",
                                    False
                                )
                            ),

                        "wicket_keeper":
                            bool(
                                player.get(
                                    "wicket_keeper",
                                    False
                                )
                            )
                    })

            # --------------------------------------------------
            # Away team
            # --------------------------------------------------

            if "away_team" in group:

                team_players = (
                    group.get(
                        "away_team"
                    ) or []
                )

                team_id = self._to_int(
                    match.get(
                        "away_team_id"
                    )
                )

                for player in team_players:

                    if not isinstance(
                        player,
                        dict
                    ):
                        continue

                    player_id = self._to_int(
                        player.get(
                            "player_id"
                        )
                    )

                    if player_id is None:
                        continue

                    records.append({

                        "season":
                            season,

                        "match_id":
                            self._to_int(
                                match.get(
                                    "match_id"
                                )
                            ),

                        "match_date":
                            match.get(
                                "match_date"
                            ),

                        "player_id":
                            player_id,

                        "player_name":
                            player.get(
                                "player_name"
                            ),

                        "team_id":
                            team_id,

                        "team_name":
                            match.get(
                                "away_team_name"
                            ),

                        "club_id":
                            self._to_int(
                                match.get(
                                    "away_club_id"
                                )
                            ),

                        "club_name":
                            match.get(
                                "away_club_name"
                            ),

                        "opposition_id":
                            self._to_int(
                                match.get(
                                    "home_team_id"
                                )
                            ),

                        "opposition_name":
                            match.get(
                                "home_team_name"
                            ),

                        "opposition_club_id":
                            self._to_int(
                                match.get(
                                    "home_club_id"
                                )
                            ),

                        "opposition_club_name":
                            match.get(
                                "home_club_name"
                            ),

                        "position":
                            self._to_int(
                                player.get(
                                    "position"
                                )
                            ),

                        "captain":
                            bool(
                                player.get(
                                    "captain",
                                    False
                                )
                            ),

                        "wicket_keeper":
                            bool(
                                player.get(
                                    "wicket_keeper",
                                    False
                                )
                            )
                    })

        return records

    # ==========================================================
    # PARTICIPATION
    # ==========================================================

    def participation_records(self):
        """
        Return one row per player appearance.

        A player is considered to have participated if they
        appear on the Play-Cricket team sheet.

        This includes players who:

            - did not bat
            - did not bowl
            - did not field

        Returns
        -------
        pandas.DataFrame
        """

        records = []

        for season, match in self._iter_matches():

            records.extend(
                self._player_team_records(
                    match,
                    season
                )
            )

        if not records:

            return pd.DataFrame()

        df = pd.DataFrame(
            records
        )

        # ------------------------------------------------------
        # Apply club/team filters
        # ------------------------------------------------------

        if self.club_id is not None:

            df = df[
                df["club_id"]
                == self.club_id
            ]

        if self.team_id is not None:

            df = df[
                df["team_id"]
                == self.team_id
            ]

        # ------------------------------------------------------
        # Remove accidental duplicates
        # ------------------------------------------------------

        df = df.drop_duplicates(
            subset=[
                "season",
                "match_id",
                "player_id",
                "team_id"
            ]
        )

        # ------------------------------------------------------
        # Sort
        # ------------------------------------------------------

        df = df.sort_values(
            [
                "season",
                "match_date",
                "team_id",
                "position"
            ],
            na_position="last"
        )

        return df.reset_index(
            drop=True
        )

    # ==========================================================
    # BATTING
    # ==========================================================

    def batting(self):
        """
        Return one row per batting performance.

        Data are taken directly from:

            match_details[0]["innings"][n]["bat"]

        Returns
        -------
        pandas.DataFrame
        """

        records = []

        for season, match in self._iter_matches():

            innings_list = match.get(
                "innings",
                []
            )

            if not isinstance(
                innings_list,
                list
            ):
                continue

            for innings in innings_list:

                if not isinstance(
                    innings,
                    dict
                ):
                    continue

                batting_team_id = self._to_int(
                    innings.get(
                        "team_batting_id"
                    )
                )

                team_info = self._team_information(
                    match,
                    batting_team_id
                )

                if team_info is None:
                    continue

                # ------------------------------------------------
                # Apply team filters
                # ------------------------------------------------

                if (
                    self.club_id is not None
                    and team_info["club_id"]
                    != self.club_id
                ):
                    continue

                if (
                    self.team_id is not None
                    and team_info["team_id"]
                    != self.team_id
                ):
                    continue

                batters = innings.get(
                    "bat",
                    []
                )

                if not isinstance(
                    batters,
                    list
                ):
                    continue

                for batter in batters:

                    if not isinstance(
                        batter,
                        dict
                    ):
                        continue

                    player_id = self._to_int(
                        batter.get(
                            "batsman_id"
                        )
                    )

                    if player_id is None:
                        continue

                    how_out = (
                        batter.get(
                            "how_out"
                        )
                    )

                    # ------------------------------------------------
                    # Normalise not-out status
                    # ------------------------------------------------

                    not_out = (
                        str(
                            how_out
                        ).strip().lower()
                        in (
                            "not out",
                            "retired not out"
                        )
                    )

                    records.append({

                        "season":
                            season,

                        "match_id":
                            self._to_int(
                                match.get(
                                    "match_id"
                                )
                            ),

                        "match_date":
                            match.get(
                                "match_date"
                            ),

                        "player_id":
                            player_id,

                        "player_name":
                            batter.get(
                                "batsman_name"
                            ),

                        "team_id":
                            team_info["team_id"],

                        "team_name":
                            team_info["team_name"],

                        "club_id":
                            team_info["club_id"],

                        "club_name":
                            team_info["club_name"],

                        "opposition_id":
                            team_info[
                                "opposition_id"
                            ],

                        "opposition_name":
                            team_info[
                                "opposition_name"
                            ],

                        "opposition_club_id":
                            team_info[
                                "opposition_club_id"
                            ],

                        "opposition_club_name":
                            team_info[
                                "opposition_club_name"
                            ],

                        "innings":
                            self._to_int(
                                innings.get(
                                    "innings_number"
                                )
                            ),

                        "position":
                            self._to_int(
                                batter.get(
                                    "position"
                                )
                            ),

                        "runs":
                            self._to_int(
                                batter.get(
                                    "runs"
                                )
                            ),

                        "balls":
                            self._to_int(
                                batter.get(
                                    "balls"
                                )
                            ),

                        "fours":
                            self._to_int(
                                batter.get(
                                    "fours"
                                )
                            ),

                        "sixes":
                            self._to_int(
                                batter.get(
                                    "sixes"
                                )
                            ),

                        "how_out":
                            how_out,

                        "not_out":
                            not_out,

                        "bowler_id":
                            self._to_int(
                                batter.get(
                                    "bowler_id"
                                )
                            ),

                        "bowler_name":
                            batter.get(
                                "bowler_name"
                            ),

                        "fielder_id":
                            self._to_int(
                                batter.get(
                                    "fielder_id"
                                )
                            ),

                        "fielder_name":
                            batter.get(
                                "fielder_name"
                            )
                    })

        if not records:

            return pd.DataFrame()

        df = pd.DataFrame(
            records
        )

        # ------------------------------------------------------
        # Derived strike rate
        # ------------------------------------------------------

        df["strike_rate"] = np.where(
            df["balls"] > 0,
            (
                df["runs"]
                / df["balls"]
                * 100
            ),
            np.nan
        )

        return (
            df
            .sort_values(
                [
                    "season",
                    "match_date",
                    "team_id",
                    "innings",
                    "position"
                ],
                na_position="last"
            )
            .reset_index(
                drop=True
            )
        )

    # ==========================================================
    # BOWLING
    # ==========================================================

    def bowling(self):
        """
        Return one row per bowling performance.

        Data are taken directly from:

            match_details[0]["innings"][n]["bowl"]

        Returns
        -------
        pandas.DataFrame
        """

        records = []

        for season, match in self._iter_matches():

            innings_list = match.get(
                "innings",
                []
            )

            if not isinstance(
                innings_list,
                list
            ):
                continue

            for innings in innings_list:

                if not isinstance(
                    innings,
                    dict
                ):
                    continue

                batting_team_id = self._to_int(
                    innings.get(
                        "team_batting_id"
                    )
                )

                batting_team_info = (
                    self._team_information(
                        match,
                        batting_team_id
                    )
                )

                if batting_team_info is None:
                    continue

                # ------------------------------------------------
                # Bowling team is opposition to batting team
                # ------------------------------------------------

                bowling_team_id = (
                    batting_team_info[
                        "opposition_id"
                    ]
                )

                team_info = self._team_information(
                    match,
                    bowling_team_id
                )

                if team_info is None:
                    continue

                # ------------------------------------------------
                # Apply team filters
                # ------------------------------------------------

                if (
                    self.club_id is not None
                    and team_info["club_id"]
                    != self.club_id
                ):
                    continue

                if (
                    self.team_id is not None
                    and team_info["team_id"]
                    != self.team_id
                ):
                    continue

                bowlers = innings.get(
                    "bowl",
                    []
                )

                if not isinstance(
                    bowlers,
                    list
                ):
                    continue

                for bowler in bowlers:

                    if not isinstance(
                        bowler,
                        dict
                    ):
                        continue

                    player_id = self._to_int(
                        bowler.get(
                            "bowler_id"
                        )
                    )

                    if player_id is None:
                        continue

                    overs = bowler.get(
                        "overs"
                    )

                    runs = self._to_int(
                        bowler.get(
                            "runs"
                        )
                    )

                    wickets = self._to_int(
                        bowler.get(
                            "wickets"
                        )
                    )

                    balls = (
                        self._overs_to_balls(
                            overs
                        )
                    )

                    records.append({

                        "season":
                            season,

                        "match_id":
                            self._to_int(
                                match.get(
                                    "match_id"
                                )
                            ),

                        "match_date":
                            match.get(
                                "match_date"
                            ),

                        "player_id":
                            player_id,

                        "player_name":
                            bowler.get(
                                "bowler_name"
                            ),

                        "team_id":
                            team_info["team_id"],

                        "team_name":
                            team_info["team_name"],

                        "club_id":
                            team_info["club_id"],

                        "club_name":
                            team_info["club_name"],

                        "opposition_id":
                            team_info[
                                "opposition_id"
                            ],

                        "opposition_name":
                            team_info[
                                "opposition_name"
                            ],

                        "opposition_club_id":
                            team_info[
                                "opposition_club_id"
                            ],

                        "opposition_club_name":
                            team_info[
                                "opposition_club_name"
                            ],

                        "innings":
                            self._to_int(
                                innings.get(
                                    "innings_number"
                                )
                            ),

                        "overs":
                            overs,

                        "balls":
                            balls,

                        "maidens":
                            self._to_int(
                                bowler.get(
                                    "maidens"
                                )
                            ),

                        "runs":
                            runs,

                        "wickets":
                            wickets,

                        "wides":
                            self._to_int(
                                bowler.get(
                                    "wides"
                                )
                            ),

                        "no_balls":
                            self._to_int(
                                bowler.get(
                                    "no_balls"
                                )
                            )
                    })

        if not records:

            return pd.DataFrame()

        df = pd.DataFrame(
            records
        )

        # ------------------------------------------------------
        # Bowling calculations
        # ------------------------------------------------------

        df["economy"] = np.where(
            df["balls"] > 0,
            (
                df["runs"]
                / df["balls"]
                * 6
            ),
            np.nan
        )

        df["bowling_average"] = np.where(
            df["wickets"] > 0,
            (
                df["runs"]
                / df["wickets"]
            ),
            np.nan
        )

        df["bowling_strike_rate"] = np.where(
            df["wickets"] > 0,
            (
                df["balls"]
                / df["wickets"]
            ),
            np.nan
        )

        return (
            df
            .sort_values(
                [
                    "season",
                    "match_date",
                    "team_id",
                    "innings"
                ],
                na_position="last"
            )
            .reset_index(
                drop=True
            )
        )

    # ==========================================================
    # FIELDING
    # ==========================================================

    def fielding(self):
        """
        Return one row per fielding dismissal.

        Fielding information is contained in the batting record
        of the dismissed batsman.

        Examples
        --------
        how_out == "ct"
            -> catch

        how_out == "st"
            -> stumping

        how_out == "run out"
            -> run out

        Returns
        -------
        pandas.DataFrame
        """

        records = []

        for season, match in self._iter_matches():

            innings_list = match.get(
                "innings",
                []
            )

            if not isinstance(
                innings_list,
                list
            ):
                continue

            for innings in innings_list:

                if not isinstance(
                    innings,
                    dict
                ):
                    continue

                batting_team_id = self._to_int(
                    innings.get(
                        "team_batting_id"
                    )
                )

                batting_team_info = (
                    self._team_information(
                        match,
                        batting_team_id
                    )
                )

                if batting_team_info is None:
                    continue

                fielding_team_id = (
                    batting_team_info[
                        "opposition_id"
                    ]
                )

                team_info = self._team_information(
                    match,
                    fielding_team_id
                )

                if team_info is None:
                    continue

                # ------------------------------------------------
                # Apply team filters
                # ------------------------------------------------

                if (
                    self.club_id is not None
                    and team_info["club_id"]
                    != self.club_id
                ):
                    continue

                if (
                    self.team_id is not None
                    and team_info["team_id"]
                    != self.team_id
                ):
                    continue

                batters = innings.get(
                    "bat",
                    []
                )

                if not isinstance(
                    batters,
                    list
                ):
                    continue

                for batter in batters:

                    if not isinstance(
                        batter,
                        dict
                    ):
                        continue

                    how_out = str(
                        batter.get(
                            "how_out",
                            ""
                        )
                    ).strip().lower()

                    fielder_id = self._to_int(
                        batter.get(
                            "fielder_id"
                        )
                    )

                    fielder_name = batter.get(
                        "fielder_name"
                    )

                    # ------------------------------------------------
                    # Only dismissal types involving a named fielder
                    # ------------------------------------------------

                    if how_out in (
                        "ct",
                        "caught",
                        "st",
                        "stumped",
                        "run out"
                    ):

                        if fielder_id is None:
                            continue

                        if how_out in (
                            "ct",
                            "caught"
                        ):

                            dismissal_type = (
                                "catch"
                            )

                        elif how_out in (
                            "st",
                            "stumped"
                        ):

                            dismissal_type = (
                                "stumping"
                            )

                        else:

                            dismissal_type = (
                                "run out"
                            )

                        records.append({

                            "season":
                                season,

                            "match_id":
                                self._to_int(
                                    match.get(
                                        "match_id"
                                    )
                                ),

                            "match_date":
                                match.get(
                                    "match_date"
                                ),

                            "player_id":
                                fielder_id,

                            "player_name":
                                fielder_name,

                            "team_id":
                                team_info["team_id"],

                            "team_name":
                                team_info["team_name"],

                            "club_id":
                                team_info["club_id"],

                            "club_name":
                                team_info["club_name"],

                            "opposition_id":
                                team_info[
                                    "opposition_id"
                                ],

                            "opposition_name":
                                team_info[
                                    "opposition_name"
                                ],

                            "opposition_club_id":
                                team_info[
                                    "opposition_club_id"
                                ],

                            "opposition_club_name":
                                team_info[
                                    "opposition_club_name"
                                ],

                            "innings":
                                self._to_int(
                                    innings.get(
                                        "innings_number"
                                    )
                                ),

                            "dismissal_type":
                                dismissal_type,

                            "dismissed_player_id":
                                self._to_int(
                                    batter.get(
                                        "batsman_id"
                                    )
                                ),

                            "dismissed_player_name":
                                batter.get(
                                    "batsman_name"
                                )
                        })

        if not records:

            return pd.DataFrame()

        df = pd.DataFrame(
            records
        )

        # ------------------------------------------------------
        # Convenience indicator columns
        # ------------------------------------------------------

        df["catch"] = (
            df["dismissal_type"]
            == "catch"
        ).astype(int)

        df["stumping"] = (
            df["dismissal_type"]
            == "stumping"
        ).astype(int)

        df["run_out"] = (
            df["dismissal_type"]
            == "run out"
        ).astype(int)

        return (
            df
            .sort_values(
                [
                    "season",
                    "match_date",
                    "team_id",
                    "innings"
                ],
                na_position="last"
            )
            .reset_index(
                drop=True
            )
        )

    # ==========================================================
    # SUMMARY
    # ==========================================================

    def summary(self):
        """
        Return one row per player with summary performance
        information across the selected matches.

        This is intended as a convenient player comparison table.

        More detailed aggregation remains the responsibility of
        MultiPlayerRecords.
        """

        participation = (
            self.participation_records()
        )

        batting = self.batting()
        bowling = self.bowling()
        fielding = self.fielding()

        # ------------------------------------------------------
        # No participation data
        # ------------------------------------------------------

        if participation.empty:

            return pd.DataFrame()

        # ------------------------------------------------------
        # Base player table
        # ------------------------------------------------------

        group_columns = [
            "player_id",
            "player_name",
            "team_id",
            "team_name",
            "club_id",
            "club_name"
        ]

        summary = (
            participation
            .groupby(
                group_columns,
                dropna=False
            )
            .agg(
                games_played=(
                    "match_id",
                    "nunique"
                )
            )
            .reset_index()
        )

        # ------------------------------------------------------
        # Batting summary
        # ------------------------------------------------------

        if not batting.empty:

            batting_group = (
                batting
                .groupby(
                    [
                        "player_id",
                        "team_id"
                    ],
                    dropna=False
                )
                .agg(

                    batting_innings=(
                        "match_id",
                        "nunique"
                    ),

                    runs=(
                        "runs",
                        "sum"
                    ),

                    times_dismissed=(
                        "not_out",
                        lambda x:
                            int(
                                (~x).sum()
                            )
                    ),

                    highest_score=(
                        "runs",
                        "max"
                    ),

                    balls_faced=(
                        "balls",
                        "sum"
                    ),

                    fours=(
                        "fours",
                        "sum"
                    ),

                    sixes=(
                        "sixes",
                        "sum"
                    )
                )
                .reset_index()
            )

            # --------------------------------------------------
            # Batting average
            # --------------------------------------------------

            batting_group[
                "batting_average"
            ] = np.where(

                batting_group[
                    "times_dismissed"
                ] > 0,

                (
                    batting_group["runs"]
                    /
                    batting_group[
                        "times_dismissed"
                    ]
                ),

                np.nan
            )

            # --------------------------------------------------
            # Strike rate
            # --------------------------------------------------

            batting_group[
                "strike_rate"
            ] = np.where(

                batting_group[
                    "balls_faced"
                ] > 0,

                (
                    batting_group["runs"]
                    /
                    batting_group[
                        "balls_faced"
                    ]
                    * 100
                ),

                np.nan
            )

            summary = summary.merge(
                batting_group,
                on=[
                    "player_id",
                    "team_id"
                ],
                how="left"
            )

        # ------------------------------------------------------
        # Bowling summary
        # ------------------------------------------------------

        if not bowling.empty:

            bowling_group = (
                bowling
                .groupby(
                    [
                        "player_id",
                        "team_id"
                    ],
                    dropna=False
                )
                .agg(

                    bowling_innings=(
                        "match_id",
                        "nunique"
                    ),

                    wickets=(
                        "wickets",
                        "sum"
                    ),

                    runs_conceded=(
                        "runs",
                        "sum"
                    ),

                    balls_bowled=(
                        "balls",
                        "sum"
                    ),

                    maidens=(
                        "maidens",
                        "sum"
                    ),

                    wides=(
                        "wides",
                        "sum"
                    ),

                    no_balls=(
                        "no_balls",
                        "sum"
                    )
                )
                .reset_index()
            )

            # --------------------------------------------------
            # Bowling average
            # --------------------------------------------------

            bowling_group[
                "bowling_average"
            ] = np.where(

                bowling_group[
                    "wickets"
                ] > 0,

                (
                    bowling_group[
                        "runs_conceded"
                    ]
                    /
                    bowling_group[
                        "wickets"
                    ]
                ),

                np.nan
            )

            # --------------------------------------------------
            # Economy
            # --------------------------------------------------

            bowling_group[
                "economy"
            ] = np.where(

                bowling_group[
                    "balls_bowled"
                ] > 0,

                (
                    bowling_group[
                        "runs_conceded"
                    ]
                    /
                    bowling_group[
                        "balls_bowled"
                    ]
                    * 6
                ),

                np.nan
            )

            # --------------------------------------------------
            # Bowling strike rate
            # --------------------------------------------------

            bowling_group[
                "bowling_strike_rate"
            ] = np.where(

                bowling_group[
                    "wickets"
                ] > 0,

                (
                    bowling_group[
                        "balls_bowled"
                    ]
                    /
                    bowling_group[
                        "wickets"
                    ]
                ),

                np.nan
            )

            summary = summary.merge(
                bowling_group,
                on=[
                    "player_id",
                    "team_id"
                ],
                how="left"
            )

        # ------------------------------------------------------
        # Fielding summary
        # ------------------------------------------------------

        if not fielding.empty:

            fielding_group = (
                fielding
                .groupby(
                    [
                        "player_id",
                        "team_id"
                    ],
                    dropna=False
                )
                .agg(

                    catches=(
                        "catch",
                        "sum"
                    ),

                    stumpings=(
                        "stumping",
                        "sum"
                    ),

                    run_outs=(
                        "run_out",
                        "sum"
                    )
                )
                .reset_index()
            )

            fielding_group[
                "fielding_dismissals"
            ] = (
                fielding_group["catches"]
                + fielding_group["stumpings"]
                + fielding_group["run_outs"]
            )

            summary = summary.merge(
                fielding_group,
                on=[
                    "player_id",
                    "team_id"
                ],
                how="left"
            )

        # ------------------------------------------------------
        # Fill numeric performance values
        # ------------------------------------------------------

        numeric_columns = [
            "batting_innings",
            "runs",
            "times_dismissed",
            "highest_score",
            "balls_faced",
            "fours",
            "sixes",
            "bowling_innings",
            "wickets",
            "runs_conceded",
            "balls_bowled",
            "maidens",
            "wides",
            "no_balls",
            "catches",
            "stumpings",
            "run_outs",
            "fielding_dismissals"
        ]

        for column in numeric_columns:

            if column in summary.columns:

                summary[column] = (
                    summary[column]
                    .fillna(0)
                    .astype(int)
                )

        return summary.reset_index(
            drop=True
        )

    # ==========================================================
    # REPRESENTATION
    # ==========================================================

    def __repr__(self):

        return (
            "PlayerPerformances("
            f"season={self.season}, "
            f"match_ids={self.match_ids}, "
            f"club_id={self.club_id}, "
            f"team_id={self.team_id})"
        )