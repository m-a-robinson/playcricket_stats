import pandas as pd
import numpy as np


class Scorecard:
    """
    Represents one Play-Cricket match.

    The complete match-detail response is supplied when the object
    is created. No API calls are made by this class.

    The supplied match detail contains:

        - Match information
        - Players
        - Innings
            - Batting
            - Bowling
            - Fall of wickets / partnerships

    All scorecard tables and performance information are derived
    locally from this data.
    """

    def __init__(self, detail):

        self.detail = detail

        self.match_id = detail["id"]

        self.match = None
        self.players = None
        self.innings = None
        self.batting = None
        self.bowling = None
        self.partnerships = None
        self.performances = None

        self._load()

    # ==========================================================
    # LOAD DATA
    # ==========================================================

    def _load(self):
        """
        Extract all scorecard information from the supplied
        match-detail dictionary.

        IMPORTANT:
            No API requests are made here.
        """

        # --------------------------------------------------
        # MATCH INFORMATION
        # --------------------------------------------------

        self.match = pd.DataFrame([
            {
                key: value
                for key, value in self.detail.items()
                if key not in ["players", "innings"]
            }
        ])  

        # --------------------------------------------------
        # PLAYERS
        # --------------------------------------------------

        self.players = self._extract_players()

        # --------------------------------------------------
        # INNINGS
        # --------------------------------------------------

        innings_data = self.detail.get(
            "innings",
            []
        )

        if not innings_data:

            self.innings = pd.DataFrame()

            self.batting = pd.DataFrame()

            self.bowling = pd.DataFrame()

            self.partnerships = pd.DataFrame()

            self.performances = pd.DataFrame()

            return

        # --------------------------------------------------
        # BUILD DATAFRAMES
        # --------------------------------------------------

        batting_frames = []
        bowling_frames = []
        partnership_frames = []
        innings_frames = []

        for innings_number, innings in enumerate(
            innings_data,
            start=1
        ):

            # ----------------------------------------------
            # INNINGS SUMMARY
            # ----------------------------------------------

            innings_row = {
                key: value
                for key, value in innings.items()
                if key not in [
                    "bat",
                    "bowl",
                    "fow"
                ]
            }

            innings_row["innings_number"] = (
                innings_number
            )

            innings_row["match_id"] = (
                self.match_id
            )

            innings_frames.append(
                innings_row
            )

            # ----------------------------------------------
            # TEAM INFORMATION
            # ----------------------------------------------

            batting_team_id = self._normalise_id(
                innings.get("team_batting_id")
            )

            batting_team_name = (
                innings.get("team_batting_name")
            )

            if batting_team_name is None:

                batting_team_name = self._team_name(
                    batting_team_id
                )

            bowling_team_id = self._opposition_team_id(
                batting_team_id
            )

            bowling_team_name = self._team_name(
                bowling_team_id
            )

            # ----------------------------------------------
            # BATTING
            # ----------------------------------------------

            bat = pd.json_normalize(
                innings.get("bat", [])
            )

            if not bat.empty:

                bat = self._add_context(
                    bat,
                    team_name=batting_team_name,
                    team_id=batting_team_id,
                    opposition_name=bowling_team_name,
                    opposition_id=bowling_team_id,
                    innings_number=innings_number
                )

                batting_frames.append(
                    bat
                )

            # ----------------------------------------------
            # BOWLING
            # ----------------------------------------------

            bowl = pd.json_normalize(
                innings.get("bowl", [])
            )

            if not bowl.empty:

                bowl = self._add_context(
                    bowl,
                    team_name=bowling_team_name,
                    team_id=bowling_team_id,
                    opposition_name=batting_team_name,
                    opposition_id=batting_team_id,
                    innings_number=innings_number
                )

                bowling_frames.append(
                    bowl
                )

            # ----------------------------------------------
            # FALL OF WICKETS
            # ----------------------------------------------

            fow = pd.json_normalize(
                innings.get("fow", [])
            )

            if not fow.empty:

                fow = self._add_context(
                    fow,
                    team_name=batting_team_name,
                    team_id=batting_team_id,
                    opposition_name=bowling_team_name,
                    opposition_id=bowling_team_id,
                    innings_number=innings_number
                )

                partnership_frames.append(
                    fow
                )

        # --------------------------------------------------
        # COMBINE INNINGS
        # --------------------------------------------------

        self.innings = pd.DataFrame(
            innings_frames
        )

        # --------------------------------------------------
        # COMBINE BATTING
        # --------------------------------------------------

        if batting_frames:

            self.batting = self._standardise_batting(
                pd.concat(
                    batting_frames,
                    ignore_index=True
                )
            )

        else:

            self.batting = pd.DataFrame()

        # --------------------------------------------------
        # COMBINE BOWLING
        # --------------------------------------------------

        if bowling_frames:

            self.bowling = self._standardise_bowling(
                pd.concat(
                    bowling_frames,
                    ignore_index=True
                )
            )

        else:

            self.bowling = pd.DataFrame()

        # --------------------------------------------------
        # COMBINE PARTNERSHIPS
        # --------------------------------------------------

        if partnership_frames:

            self.partnerships = pd.concat(
                partnership_frames,
                ignore_index=True
            )

            self.partnerships = (
                self._calculate_partnership_scores(
                    self.partnerships
                )
            )

        else:

            self.partnerships = pd.DataFrame()

        # --------------------------------------------------
        # PERFORMANCES
        # --------------------------------------------------

        self.performances = (
            self.get_performances()
        )

    # ==========================================================
    # INTERNAL HELPERS
    # ==========================================================

    @staticmethod
    def _normalise_id(value):

        if value in [None, ""]:
            return None

        try:
            return int(value)
        except (ValueError, TypeError):
            return value

    # ----------------------------------------------------------

    def _team_name(self, team_id):

        if team_id is None:
            return None

        home_id = self._normalise_id(
            self.detail.get("home_team_id")
        )

        away_id = self._normalise_id(
            self.detail.get("away_team_id")
        )

        if team_id == home_id:

            return (
                f"{self.detail.get('home_club_name')} "
                f"- "
                f"{self.detail.get('home_team_name')}"
            )

        if team_id == away_id:

            return (
                f"{self.detail.get('away_club_name')} "
                f"- "
                f"{self.detail.get('away_team_name')}"
            )

        return None

    # ----------------------------------------------------------

    def _opposition_team_id(self, team_id):

        home_id = self._normalise_id(
            self.detail.get("home_team_id")
        )

        away_id = self._normalise_id(
            self.detail.get("away_team_id")
        )

        if team_id == home_id:
            return away_id

        if team_id == away_id:
            return home_id

        return None

    # ----------------------------------------------------------

    @staticmethod
    def _add_context(
        df,
        team_name,
        team_id,
        opposition_name,
        opposition_id,
        innings_number
    ):

        df = df.copy()

        df["team_name"] = team_name
        df["team_id"] = team_id

        df["opposition_name"] = (
            opposition_name
        )

        df["opposition_id"] = (
            opposition_id
        )

        df["innings"] = innings_number

        return df

    # ==========================================================
    # PLAYERS
    # ==========================================================

    def _extract_players(self):

        players = []

        player_data = self.detail.get(
            "players",
            []
        )

        # Home team

        if len(player_data) >= 1:

            home_players = player_data[0].get(
                "home_team",
                []
            )

            home = pd.json_normalize(
                home_players
            )

            if not home.empty:

                home["team_id"] = self._normalise_id(
                    self.detail.get("home_team_id")
                )

                home["club_id"] = self._normalise_id(
                    self.detail.get("home_club_id")
                )

                players.append(home)

        # Away team

        if len(player_data) >= 2:

            away_players = player_data[1].get(
                "away_team",
                []
            )

            away = pd.json_normalize(
                away_players
            )

            if not away.empty:

                away["team_id"] = self._normalise_id(
                    self.detail.get("away_team_id")
                )

                away["club_id"] = self._normalise_id(
                    self.detail.get("away_club_id")
                )

                players.append(away)

        if not players:

            return pd.DataFrame()

        return pd.concat(
            players,
            ignore_index=True
        )

    # ==========================================================
    # STANDARDISE BATTING
    # ==========================================================

    def _standardise_batting(self, data):

        if data.empty:
            return data

        data = data.copy()

        # Numeric columns

        for column in [
            "runs",
            "fours",
            "sixes",
            "balls",
            "position"
        ]:

            if column in data.columns:

                data[column] = (
                    pd.to_numeric(
                        data[column],
                        errors="coerce"
                    )
                    .fillna(0)
                    .astype(int)
                )

        # Not out

        if "how_out" in data.columns:

            data["not_out"] = np.where(
                data["how_out"].isin(
                    [
                        "not out",
                        "retired not out",
                        "retired hurt",
                        "did not bat"
                    ]
                ),
                1,
                0
            )

        return data

    # ==========================================================
    # STANDARDISE BOWLING
    # ==========================================================

    def _standardise_bowling(self, data):

        if data.empty:
            return data

        data = data.copy()

        for column in [
            "runs",
            "wickets",
            "maidens",
            "no_balls",
            "wides"
        ]:

            if column in data.columns:

                data[column] = (
                    pd.to_numeric(
                        data[column],
                        errors="coerce"
                    )
                    .fillna(0)
                    .astype(int)
                )

        # Convert overs to balls

        if "overs" in data.columns:

            data["balls"] = (
                data["overs"]
                .apply(self._count_balls)
            )

        return data

    # ----------------------------------------------------------

    @staticmethod
    def _count_balls(overs):

        if pd.isna(overs):
            return 0

        try:

            overs = str(overs)

            if "." in overs:

                whole, remainder = (
                    overs.split(".")
                )

                return (
                    int(whole) * 6
                    + int(remainder)
                )

            return int(overs) * 6

        except (
            ValueError,
            TypeError
        ):

            return 0

    # ==========================================================
    # PARTNERSHIPS
    # ==========================================================

    def _calculate_partnership_scores(
        self,
        data
    ):

        if data.empty:
            return data

        data = data.copy()

        if "runs" not in data.columns:

            return data

        data["runs"] = (
            pd.to_numeric(
                data["runs"],
                errors="coerce"
            )
        )

        shifted = (
            data
            .groupby("innings")["runs"]
            .shift(1)
            .fillna(0)
        )

        data["score_added"] = (
            data["runs"] - shifted
        )

        return data

    # ==========================================================
    # MATCH INFORMATION
    # ==========================================================

    def match_info(self):

        return self.match.iloc[0]

    # ----------------------------------------------------------

    def teams(self):

        row = self.match_info()

        return {
            "home": (
                f"{row['home_club_name']} "
                f"{row['home_team_name']}"
            ),
            "away": (
                f"{row['away_club_name']} "
                f"{row['away_team_name']}"
            )
        }

    # ==========================================================
    # INNINGS
    # ==========================================================

    def get_innings(
        self,
        innings_number
    ):

        if self.innings.empty:
            return pd.DataFrame()

        return self.innings[
            self.innings["innings_number"]
            == innings_number
        ].copy()

    # ==========================================================
    # BATTING
    # ==========================================================

    def get_batting(
        self,
        innings_number=None
    ):

        data = self.batting.copy()

        if (
            innings_number is not None
            and not data.empty
        ):

            data = data[
                data["innings"]
                == innings_number
            ]

        return data

    # ==========================================================
    # BATTING TABLE
    # ==========================================================

    def batting_table(
        self,
        innings_number
    ):

        data = self.get_batting(
            innings_number
        ).copy()

        if data.empty:
            return data

        def dismissal(row):

            how_out = (
                str(row.get("how_out", ""))
                .strip()
                .lower()
            )

            if how_out == "not out":
                return "not out"

            if how_out == "did not bat":
                return "did not bat"

            if how_out == "ct":

                if row.get("fielder_name") == row.get("bowler_name"):
                    return (
                        f"c & b {row.get('bowler_name')}"
                    )

                return (
                    f"c {row.get('fielder_name')} "
                    f"b {row.get('bowler_name')}"
                )

            if how_out == "run out":
                return (
                    f"run out "
                    f"({row.get('fielder_name')})"
                )

            if how_out == "b":
                return (
                    f"b {row.get('bowler_name')}"
                )

            if how_out == "lbw":
                return (
                    f"lbw b "
                    f"{row.get('bowler_name')}"
                )

            if how_out == "st":
                return (
                    f"st {row.get('fielder_name')} "
                    f"b {row.get('bowler_name')}"
                )

            if how_out == "hit wicket":
                return (
                    f"hit wicket b "
                    f"{row.get('bowler_name')}"
                )

            return how_out

        data["dismissal"] = data.apply(
            dismissal,
            axis=1
        )

        columns = [
            "position",
            "batsman_name",
            "dismissal",
            "runs",
            "balls",
            "fours",
            "sixes",
            "batsman_id"
        ]

        columns = [
            column
            for column in columns
            if column in data.columns
        ]

        return data[columns]

    # ==========================================================
    # BOWLING
    # ==========================================================

    def get_bowling(
        self,
        innings_number=None
    ):

        data = self.bowling.copy()

        if (
            innings_number is not None
            and not data.empty
        ):

            data = data[
                data["innings"]
                == innings_number
            ]

        return data

    # ==========================================================
    # BOWLING TABLE
    # ==========================================================

    def bowling_table(
        self,
        innings_number
    ):

        data = self.get_bowling(
            innings_number
        ).copy()

        if data.empty:
            return data

        columns = [
            "bowler_name",
            "overs",
            "maidens",
            "runs",
            "wides",
            "no_balls",
            "wickets",
            "bowler_id"
        ]

        columns = [
            column
            for column in columns
            if column in data.columns
        ]

        return data[columns]

    # ==========================================================
    # DISMISSALS
    # ==========================================================

    def get_dismissals(
        self,
        innings_number=None
    ):

        data = self.get_batting(
            innings_number
        )

        if data.empty:
            return data

        return data[
            ~data["how_out"].isin(
                [
                    "not out",
                    "did not bat"
                ]
            )
        ].copy()

    # ==========================================================
    # CATCHES
    # ==========================================================

    def get_catches(
        self,
        innings_number=None
    ):

        data = self.get_dismissals(
            innings_number
        )

        if data.empty:
            return data

        return data[
            data["how_out"]
            .astype(str)
            .str.lower()
            == "ct"
        ].copy()

    # ==========================================================
    # RUN OUTS
    # ==========================================================

    def get_run_outs(
        self,
        innings_number=None
    ):

        data = self.get_dismissals(
            innings_number
        )

        if data.empty:
            return data

        return data[
            data["how_out"]
            .astype(str)
            .str.lower()
            == "run out"
        ].copy()

    # ==========================================================
    # FIELDING TABLE
    # ==========================================================

    def fielding_table(
        self,
        innings_number
    ):

        data = self.get_batting(
            innings_number
        ).copy()

        if data.empty:
            return pd.DataFrame()

        # Catches

        catches = data[
            data["how_out"]
            .astype(str)
            .str.lower()
            == "ct"
        ][
            [
                "fielder_name",
                "fielder_id",
                "batsman_name",
                "batsman_id",
                "bowler_name",
                "bowler_id"
            ]
        ].copy()

        catches["dismissal"] = "catch"

        # Run outs

        run_outs = data[
            data["how_out"]
            .astype(str)
            .str.lower()
            == "run out"
        ][
            [
                "fielder_name",
                "fielder_id",
                "batsman_name",
                "batsman_id",
                "bowler_name",
                "bowler_id"
            ]
        ].copy()

        run_outs["dismissal"] = "run out"

        # Stumpings

        stumpings = data[
            data["how_out"]
            .astype(str)
            .str.lower()
            == "st"
        ][
            [
                "fielder_name",
                "fielder_id",
                "batsman_name",
                "batsman_id",
                "bowler_name",
                "bowler_id"
            ]
        ].copy()

        stumpings["dismissal"] = "stumping"

        return pd.concat(
            [
                catches,
                run_outs,
                stumpings
            ],
            ignore_index=True
        )

    # ==========================================================
    # PARTNERSHIPS
    # ==========================================================

    def get_partnerships(
        self,
        innings_number=None
    ):

        data = self.partnerships.copy()

        if (
            innings_number is not None
            and not data.empty
        ):

            data = data[
                data["innings"]
                == innings_number
            ]

        return data

    # ==========================================================
    # PARTNERSHIP TABLE
    # ==========================================================

    def partnership_table(
        self,
        innings_number
    ):

        data = self.get_partnerships(
            innings_number
        ).copy()

        if data.empty:
            return data

        columns = [
            "wickets",
            "runs",
            "batsman_out_name",
            "batsman_in_name",
            "batsman_in_runs",
            "score_added"
        ]

        columns = [
            column
            for column in columns
            if column in data.columns
        ]

        data = data[columns].copy()

        data = data.rename(
            columns={
                "wickets": "wicket",
                "runs": "score_after_wicket",
                "batsman_out_name": "batsman_out",
                "batsman_in_name": "batsman_in"
            }
        )

        return data

    # ==========================================================
    # RESULT
    # ==========================================================

    def get_result(self):

        return self.detail.get(
            "result_description"
        ) or self.detail.get(
            "result"
        )

    # ==========================================================
    # SUMMARY
    # ==========================================================

    def summary(self):

        row = self.match_info()

        return {
            "match_id": self.match_id,
            "date": row.get("match_date"),
            "competition": row.get(
                "competition_name"
            ),
            "ground": row.get(
                "ground_name"
            ),
            "home_team": row.get(
                "home_team_name"
            ),
            "away_team": row.get(
                "away_team_name"
            ),
            "result": self.get_result()
        }

    # ==========================================================
    # INNINGS SUMMARY
    # ==========================================================

    def innings_summary(
        self,
        innings_number
    ):

        data = self.get_innings(
            innings_number
        )

        if data.empty:

            raise ValueError(
                f"Innings {innings_number} "
                f"not found."
            )

        row = data.iloc[0]

        return pd.DataFrame([
            {
                "innings": innings_number,
                "team": row.get(
                    "team_batting_name"
                ),
                "team_id": row.get(
                    "team_batting_id"
                ),
                "runs": row.get(
                    "runs"
                ),
                "wickets": row.get(
                    "wickets"
                ),
                "overs": row.get(
                    "overs"
                ),
                "balls": row.get(
                    "balls"
                ),
                "byes": row.get(
                    "extra_byes"
                ),
                "leg_byes": row.get(
                    "extra_leg_byes"
                ),
                "wides": row.get(
                    "extra_wides"
                ),
                "no_balls": row.get(
                    "extra_no_balls"
                ),
                "penalty_runs": row.get(
                    "extra_penalty_runs"
                ),
                "total_extras": row.get(
                    "total_extras"
                ),
                "declared": row.get(
                    "declared"
                ),
                "forfeited": row.get(
                    "forfeited_innings"
                )
            }
        ])

    # ==========================================================
    # EXTRAS
    # ==========================================================

    def extras_table(
        self,
        innings_number
    ):

        summary = (
            self.innings_summary(
                innings_number
            ).iloc[0]
        )

        extras = pd.DataFrame([
            {
                "type": "Byes",
                "runs": pd.to_numeric(
                    summary["byes"],
                    errors="coerce"
                )
            },
            {
                "type": "Leg byes",
                "runs": pd.to_numeric(
                    summary["leg_byes"],
                    errors="coerce"
                )
            },
            {
                "type": "Wides",
                "runs": pd.to_numeric(
                    summary["wides"],
                    errors="coerce"
                )
            },
            {
                "type": "No balls",
                "runs": pd.to_numeric(
                    summary["no_balls"],
                    errors="coerce"
                )
            },
            {
                "type": "Penalty",
                "runs": pd.to_numeric(
                    summary["penalty_runs"],
                    errors="coerce"
                )
            }
        ])

        extras["runs"] = (
            extras["runs"]
            .fillna(0)
            .astype(int)
        )

        return extras[
            extras["runs"] > 0
        ].reset_index(drop=True)

    # ==========================================================
    # FALL OF WICKETS
    # ==========================================================

    def fall_of_wickets(
        self,
        innings_number
    ):

        data = self.get_partnerships(
            innings_number
        ).copy()

        if data.empty:

            return pd.DataFrame(
                columns=[
                    "wicket",
                    "score",
                    "batsman_out",
                    "batsman_out_id"
                ]
            )

        columns = [
            "wickets",
            "runs",
            "batsman_out_name",
            "batsman_out_id"
        ]

        data = data[columns].copy()

        data = data.rename(
            columns={
                "wickets": "wicket",
                "runs": "score",
                "batsman_out_name": "batsman_out"
            }
        )

        return data[
            [
                "wicket",
                "score",
                "batsman_out",
                "batsman_out_id"
            ]
        ]

    # ==========================================================
    # COMPLETE STRUCTURED SCORECARD DATA
    # ==========================================================

    def get_data(self):

        result = {
            "match": self.match.copy(),
            "innings": {}
        }

        if self.innings.empty:
            return result

        for innings_number in (
            self.innings[
                "innings_number"
            ].dropna().unique()
        ):

            innings_number = int(
                innings_number
            )

            result["innings"][
                innings_number
            ] = {

                "summary":
                    self.innings_summary(
                        innings_number
                    ),

                "batting":
                    self.batting_table(
                        innings_number
                    ),

                "bowling":
                    self.bowling_table(
                        innings_number
                    ),

                "fielding":
                    self.fielding_table(
                        innings_number
                    ),

                "extras":
                    self.extras_table(
                        innings_number
                    ),

                "fall_of_wickets":
                    self.fall_of_wickets(
                        innings_number
                    ),

                "partnerships":
                    self.partnership_table(
                        innings_number
                    )
            }

        return result

    # ==========================================================
    # PRINTABLE SCORECARD
    # ==========================================================

    def print_scorecard(self):

        print("=" * 70)

        match = self.match.iloc[0]

        home = (
            f"{match['home_club_name']} "
            f"{match['home_team_name']}"
        )

        away = (
            f"{match['away_club_name']} "
            f"{match['away_team_name']}"
        )

        print(
            f"{home} vs {away}"
        )

        print("=" * 70)

        print(
            f"Competition: "
            f"{match['competition_name']}"
        )

        print(
            f"Date: "
            f"{match['match_date']}"
        )

        print(
            f"Ground: "
            f"{match['ground_name']}"
        )

        print()

        print(
            f"Result: {self.get_result()}"
        )

        print()

        # --------------------------------------------------
        # NO PLAY
        # --------------------------------------------------

        if self.innings.empty:

            print(
                "No innings recorded."
            )

            print("=" * 70)

            return

        # --------------------------------------------------
        # EACH INNINGS
        # --------------------------------------------------

        for innings_number in (
            self.innings[
                "innings_number"
            ]
        ):

            summary = (
                self.innings_summary(
                    innings_number
                ).iloc[0]
            )

            print("-" * 70)

            print(
                f"{summary['team']} "
                f"{summary['runs']}/"
                f"{summary['wickets']} "
                f"({summary['overs']} overs)"
            )

            print()

            # ----------------------------------------------
            # BATTING
            # ----------------------------------------------

            batting = (
                self.batting_table(
                    innings_number
                )
            )

            print("BATTING")
            print("-" * 70)

            for _, row in batting.iterrows():

                print(
                    f"{str(row.get('batsman_name', '')):<25} "
                    f"{str(row.get('dismissal', '')):<30} "
                    f"{row.get('runs', 0):>3} "
                    f"{row.get('balls', 0):>3} "
                    f"{row.get('fours', 0):>2} "
                    f"{row.get('sixes', 0):>2}"
                )

            print()

            # ----------------------------------------------
            # EXTRAS
            # ----------------------------------------------

            extras = (
                self.extras_table(
                    innings_number
                )
            )

            if not extras.empty:

                extras_text = ", ".join(
                    f"{row['type']}: {row['runs']}"
                    for _, row
                    in extras.iterrows()
                )

                total_extras = (
                    extras["runs"].sum()
                )

                print(
                    f"Extras: {extras_text} "
                    f"(Total {total_extras})"
                )

            print(
                f"Total: "
                f"{summary['runs']}/"
                f"{summary['wickets']}"
            )

            print()

            # ----------------------------------------------
            # FALL OF WICKETS
            # ----------------------------------------------

            fow = (
                self.fall_of_wickets(
                    innings_number
                )
            )

            if not fow.empty:

                fow_text = ", ".join(
                    f"{row['wicket']}-"
                    f"{row['score']} "
                    f"({row['batsman_out']})"
                    for _, row
                    in fow.iterrows()
                )

                print(
                    f"Fall of wickets: "
                    f"{fow_text}"
                )

            print()

            # ----------------------------------------------
            # BOWLING
            # ----------------------------------------------

            bowling = (
                self.bowling_table(
                    innings_number
                )
            )

            if not bowling.empty:

                print("BOWLING")
                print("-" * 70)

                for _, row in bowling.iterrows():

                    print(
                        f"{row['bowler_name']:<25} "
                        f"{row['overs']:>5} "
                        f"{row['maidens']:>3} "
                        f"{row['runs']:>4} "
                        f"{row['wickets']:>3}"
                    )

            print()

        print("=" * 70)

    # ==========================================================
    # NOTABLE PERFORMANCES
    # ==========================================================

    def get_performances(self):

        performances = []

        # --------------------------------------------------
        # NO PLAY
        # --------------------------------------------------

        if self.batting.empty and self.bowling.empty:

            return pd.DataFrame(
                columns=[
                    "match_id",
                    "player_id",
                    "player_name",
                    "team_id",
                    "team_name",
                    "opposition_id",
                    "opposition_name",
                    "innings",
                    "performance_type",
                    "achievement",
                    "value",
                    "detail",
                    "description"
                ]
            )

        # ==================================================
        # BATTING
        # ==================================================

        for innings_number in sorted(
            self.batting["innings"]
            .dropna()
            .unique()
        ) if not self.batting.empty else []:

            batting = self.get_batting(
                innings_number
            )

            for _, row in batting.iterrows():

                runs = pd.to_numeric(
                    row.get("runs"),
                    errors="coerce"
                )

                if pd.isna(runs):
                    continue

                achievement = None

                if runs >= 200:
                    achievement = "double_century"

                elif runs >= 150:
                    achievement = "150"

                elif runs >= 100:
                    achievement = "century"

                elif runs >= 50:
                    achievement = "half_century"

                if achievement:

                    performances.append({

                        "match_id":
                            self.match_id,

                        "player_id":
                            row.get("batsman_id"),

                        "player_name":
                            row.get("batsman_name"),

                        "team_id":
                            row.get("team_id"),

                        "team_name":
                            row.get("team_name"),

                        "opposition_id":
                            row.get("opposition_id"),

                        "opposition_name":
                            row.get("opposition_name"),

                        "innings":
                            innings_number,

                        "performance_type":
                            "batting",

                        "achievement":
                            achievement,

                        "value":
                            int(runs),

                        "detail":
                            f"{int(runs)} runs"
                    })

        # ==================================================
        # BOWLING
        # ==================================================

        for innings_number in sorted(
            self.bowling["innings"]
            .dropna()
            .unique()
        ) if not self.bowling.empty else []:

            bowling = self.get_bowling(
                innings_number
            )

            for _, row in bowling.iterrows():

                wickets = pd.to_numeric(
                    row.get("wickets"),
                    errors="coerce"
                )

                if pd.isna(wickets):
                    continue

                achievement = None

                if wickets >= 10:
                    achievement = (
                        "10_wicket_match"
                    )

                elif wickets >= 7:
                    achievement = (
                        "7_wicket_haul"
                    )

                elif wickets >= 6:
                    achievement = (
                        "6_wicket_haul"
                    )

                elif wickets >= 5:
                    achievement = (
                        "five_wicket_haul"
                    )

                elif wickets >= 4:
                    achievement = (
                        "four_wicket_haul"
                    )

                elif wickets >= 3:
                    achievement = (
                        "three_wicket_haul"
                    )

                if achievement:

                    performances.append({

                        "match_id":
                            self.match_id,

                        "player_id":
                            row.get("bowler_id"),

                        "player_name":
                            row.get("bowler_name"),

                        "team_id":
                            row.get("team_id"),

                        "team_name":
                            row.get("team_name"),

                        "opposition_id":
                            row.get("opposition_id"),

                        "opposition_name":
                            row.get("opposition_name"),

                        "innings":
                            innings_number,

                        "performance_type":
                            "bowling",

                        "achievement":
                            achievement,

                        "value":
                            int(wickets),

                        "detail":
                            f"{int(wickets)} wickets"
                    })

        # ==================================================
        # FIELDING
        # ==================================================

        fielding = self.batting.copy()

        if not fielding.empty:

            fielding["how_out_clean"] = (
                fielding["how_out"]
                .fillna("")
                .astype(str)
                .str.lower()
                .str.strip()
            )

            fielding = fielding[
                fielding["fielder_name"]
                .notna()
            ].copy()

            # ----------------------------------------------
            # CATCHES
            # ----------------------------------------------

            catches = fielding[
                fielding["how_out_clean"]
                == "ct"
            ]

            catch_counts = (
                catches
                .groupby(
                    [
                        "fielder_id",
                        "fielder_name",
                        "team_id",
                        "team_name",
                        "opposition_id",
                        "opposition_name",
                        "innings"
                    ],
                    dropna=False
                )
                .size()
                .reset_index(
                    name="catches"
                )
            )

            # ----------------------------------------------
            # STUMPINGS
            # ----------------------------------------------

            stumpings = fielding[
                fielding["how_out_clean"]
                == "st"
            ]

            stumping_counts = (
                stumpings
                .groupby(
                    [
                        "fielder_id",
                        "fielder_name",
                        "team_id",
                        "team_name",
                        "opposition_id",
                        "opposition_name",
                        "innings"
                    ],
                    dropna=False
                )
                .size()
                .reset_index(
                    name="stumpings"
                )
            )

            if (
                not catch_counts.empty
                or not stumping_counts.empty
            ):

                fielding_counts = pd.merge(
                    catch_counts,
                    stumping_counts,
                    on=[
                        "fielder_id",
                        "fielder_name",
                        "team_id",
                        "team_name",
                        "opposition_id",
                        "opposition_name",
                        "innings"
                    ],
                    how="outer"
                )

                fielding_counts["catches"] = (
                    fielding_counts[
                        "catches"
                    ]
                    .fillna(0)
                    .astype(int)
                )

                fielding_counts["stumpings"] = (
                    fielding_counts[
                        "stumpings"
                    ]
                    .fillna(0)
                    .astype(int)
                )

                fielding_counts[
                    "dismissals"
                ] = (
                    fielding_counts[
                        "catches"
                    ]
                    +
                    fielding_counts[
                        "stumpings"
                    ]
                )

                # ------------------------------------------
                # WICKETKEEPERS
                # ------------------------------------------

                wicketkeepers = (
                    fielding_counts[
                        fielding_counts[
                            "stumpings"
                        ] > 0
                    ]
                )

                notable_keepers = (
                    wicketkeepers[
                        wicketkeepers[
                            "dismissals"
                        ] >= 5
                    ]
                )

                for _, row in (
                    notable_keepers.iterrows()
                ):

                    performances.append({

                        "match_id":
                            self.match_id,

                        "player_id":
                            row["fielder_id"],

                        "player_name":
                            row["fielder_name"],

                        "team_id":
                            row["team_id"],

                        "team_name":
                            row["team_name"],

                        "opposition_id":
                            row["opposition_id"],

                        "opposition_name":
                            row["opposition_name"],

                        "innings":
                            row["innings"],

                        "performance_type":
                            "fielding",

                        "achievement":
                            "wicketkeeper_dismissals",

                        "value":
                            int(
                                row["dismissals"]
                            ),

                        "detail":
                            (
                                f"{int(row['dismissals'])} "
                                f"dismissals "
                                f"("
                                f"{int(row['catches'])} "
                                f"catches, "
                                f"{int(row['stumpings'])} "
                                f"stumpings)"
                            )
                    })

                # ------------------------------------------
                # NON-WICKETKEEPER CATCHES
                # ------------------------------------------

                notable_catches = (
                    fielding_counts[
                        (
                            fielding_counts[
                                "catches"
                            ] >= 5
                        )
                        &
                        (
                            fielding_counts[
                                "stumpings"
                            ] == 0
                        )
                    ]
                )

                for _, row in (
                    notable_catches.iterrows()
                ):

                    performances.append({

                        "match_id":
                            self.match_id,

                        "player_id":
                            row["fielder_id"],

                        "player_name":
                            row["fielder_name"],

                        "team_id":
                            row["team_id"],

                        "team_name":
                            row["team_name"],

                        "opposition_id":
                            row["opposition_id"],

                        "opposition_name":
                            row["opposition_name"],

                        "innings":
                            row["innings"],

                        "performance_type":
                            "fielding",

                        "achievement":
                            "five_catch_performance",

                        "value":
                            int(
                                row["catches"]
                            ),

                        "detail":
                            f"{int(row['catches'])} catches"
                    })

        # ==================================================
        # CREATE DATAFRAME
        # ==================================================

        columns = [
            "match_id",
            "player_id",
            "player_name",
            "team_id",
            "team_name",
            "opposition_id",
            "opposition_name",
            "innings",
            "performance_type",
            "achievement",
            "value",
            "detail"
        ]

        performances_df = pd.DataFrame(
            performances,
            columns=columns
        )

        # ==================================================
        # DESCRIPTIONS
        # ==================================================

        if not performances_df.empty:

            def make_description(row):

                achievement = (
                    row["achievement"]
                )

                value = row["value"]

                descriptions = {

                    "half_century":
                        f"Half-century – {value} runs",

                    "century":
                        f"Century – {value} runs",

                    "double_century":
                        f"Double-century – {value} runs",

                    "150":
                        f"150 runs – {value} runs",

                    "three_wicket_haul":
                        "3-wicket haul",

                    "four_wicket_haul":
                        "4-wicket haul",

                    "five_wicket_haul":
                        "5-wicket haul",

                    "six_wicket_haul":
                        "6-wicket haul",

                    "7_wicket_haul":
                        "7-wicket haul",

                    "10_wicket_match":
                        "10-wicket match",

                    "five_catch_performance":
                        f"{value}-catch performance",

                    "wicketkeeper_dismissals":
                        row["detail"]
                }

                return descriptions.get(
                    achievement,
                    row["detail"]
                )

            performances_df[
                "description"
            ] = performances_df.apply(
                make_description,
                axis=1
            )

        else:

            performances_df[
                "description"
            ] = pd.Series(
                dtype="object"
            )

        return performances_df