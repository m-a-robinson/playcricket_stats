import pandas as pd


class Scorecard:
    """
    Represents one Play-Cricket match.

    Uses the playcric API to retrieve:
        - Match information
        - Innings totals
        - Batting
        - Bowling
        - Partnerships
    """

    def __init__(self, playc, match_id, season):
        self.playc = playc
        self.match_id = match_id
        self.season = season

        self.match = None
        self.players = None
        self.innings = None
        self.batting = None
        self.bowling = None
        self.partnerships = None
        self.performances = None


        self._load()

    # --------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------

    def _load(self):

        # Match information
        matches = self.playc.get_all_matches(
            season=self.season
        )

        self.match = matches[
            matches["id"] == self.match_id
        ].copy()

        if self.match.empty:
            raise ValueError(
                f"Match {self.match_id} "
                f"was not found in season {self.season}."
            )

        # Players used in match
        self.players = self.playc._get_players_used_in_match(
            self.match_id
        )

        # Batting and bowling
        (
            self.batting,
            self.bowling
        ) = self.playc.get_individual_stats(
            match_id=self.match_id,
            stat_string=False
        )

        # Innings
        self.innings = (
            self.playc.get_innings_total_scores(
                self.match_id
            )
        )

        # Partnerships
        self.partnerships = (
            self.playc.get_match_partnerships(
                self.match_id
            )
        )
   
        # Notable performances / highlights
        self.performances = self.get_performances()
        


    # --------------------------------------------------
    # MATCH INFORMATION
    # --------------------------------------------------

    def match_info(self):

        return self.match.iloc[0]

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


    # --------------------------------------------------
    # INNINGS
    # --------------------------------------------------

    def get_innings(self, innings_number):

        return self.innings[
            self.innings["innings_number"]
            == innings_number
        ].copy()

    # --------------------------------------------------
    # BATTING
    # --------------------------------------------------

    def get_batting(self, innings_number=None):

        data = self.batting.copy()

        if innings_number is not None:
            data = data[
                data["innings"] == innings_number
            ]

        return data
    
    # --------------------------------------------------
    #       PRESENTATION BATTING TABLE
    # --------------------------------------------------
    
    def batting_table(self, innings_number):
    
        data = self.get_batting(innings_number).copy()
    
        # Create a readable dismissal description
        def dismissal(row):
    
            how_out = str(row["how_out"]).strip().lower()
    
            if how_out == "not out":
                return "not out"
    
            if how_out == "did not bat":
                return "did not bat"
    
            if how_out == "ct":
                return f"c {row['fielder_name']} b {row['bowler_name']}"
    
            if how_out == "run out":
                return f"run out ({row['fielder_name']})"
    
            if how_out == "b":
                return f"b {row['bowler_name']}"
    
            if how_out == "lbw":
                return f"lbw b {row['bowler_name']}"
    
            return how_out
    
        data["dismissal"] = data.apply(
            dismissal,
            axis=1
        )
    
        # Keep only the useful scorecard columns
        data = data[
            [
                "position",
                "batsman_name",
                "dismissal",
                "runs",
                "balls",
                "fours",
                "sixes",
                "batsman_id"
            ]
        ]
    
        return data

    # --------------------------------------------------
    # BOWLING
    # --------------------------------------------------

    def get_bowling(self, innings_number=None):

        data = self.bowling.copy()

        if innings_number is not None:
            data = data[
                data["innings"] == innings_number
            ]

        return data

    # --------------------------------------------------
    #       PRESENTATION BOWLING TABLE
    # --------------------------------------------------

    def bowling_table(self, innings_number):

        data = self.get_bowling(innings_number).copy()

        data = data[
            [
                "bowler_name",
                "overs",
                "maidens",
                "runs",
                "wides",
                "no_balls",
                "wickets",
                "bowler_id"
            ]
        ]

        return data

    # --------------------------------------------------
    # DISMISSALS
    # --------------------------------------------------

    def get_dismissals(self, innings_number=None):

        data = self.get_batting(innings_number)

        return data[
            ~data["how_out"].isin(
                ["not out", "did not bat"]
            )
        ].copy()

    # --------------------------------------------------
    # FIELDING / CATCHES
    # --------------------------------------------------

    def get_catches(self, innings_number=None):

        data = self.get_dismissals(innings_number)

        return data[
            data["how_out"].str.lower() == "ct"
        ].copy()

    # --------------------------------------------------
    # FIELDING / RUN OUTS
    # --------------------------------------------------

    def get_run_outs(self, innings_number=None):

        data = self.get_dismissals(innings_number)

        return data[
            data["how_out"].str.lower() == "run out"
        ].copy()
    
    # --------------------------------------------------
    #       FIELDING TABLE
    # --------------------------------------------------

    def fielding_table(self, innings_number):

        data = self.get_batting(innings_number).copy()

        # Catches
        catches = data[
            data["how_out"].str.lower() == "ct"
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
            data["how_out"].str.lower() == "run out"
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

        return pd.concat(
            [catches, run_outs],
            ignore_index=True
        )    

    # --------------------------------------------------
    # PARTNERSHIPS
    # --------------------------------------------------

    def get_partnerships(self, innings_number=None):

        data = self.partnerships.copy()

        if innings_number is not None:
            data = data[
                data["innings"] == innings_number
            ]

        return data
    
    # --------------------------------------------------
    # PARTNERSHIP TABLE
    # --------------------------------------------------

    def partnership_table(self, innings_number):

        data = self.get_partnerships(
            innings_number
        ).copy()

        if data.empty:
            return data

        data = data[
            [
                "wickets",
                "runs",
                "batsman_out_name",
                "batsman_in_name",
                "batsman_in_runs",
                "score_added"
            ]
        ].copy()

        data = data.rename(
            columns={
                "wickets": "wicket",
                "runs": "score_after_wicket",
                "batsman_out_name": "batsman_out",
                "batsman_in_name": "batsman_in",
                "batsman_in_runs": "batsman_in_runs"
            }
        )

        return data

    # --------------------------------------------------
    # RESULT
    # --------------------------------------------------

    def get_result(self):

        return self.playc.get_match_result_string(
            self.match_id
        )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    def summary(self):

        row = self.match_info()

        return {
            "match_id": self.match_id,
            "season": self.season,
            "date": row["match_date"],
            "competition": row["competition_name"],
            "ground": row["ground_name"],
            "home_team": row["home_team_name"],
            "away_team": row["away_team_name"],
            "result": self.get_result()
        }

    # --------------------------------------------------
    # DISPLAY SUMMARY
    # --------------------------------------------------

    def show(self):

        row = self.match_info()

        print("=" * 70)

        teams = self.teams()
    
        print(
            f"{teams['home']} vs {teams['away']}"
        )

        print("=" * 70)

        print(
            f"Competition: "
            f"{row['competition_name']}"
        )

        print(
            f"Date: "
            f"{row['match_date']}"
        )

        print(
            f"Ground: "
            f"{row['ground_name']}"
        )

        print()

        print(
            f"Result: {self.get_result()}"
        )

        print()

        for _, innings in self.innings.iterrows():

            print(
                f"{innings['team_batting_name']}: "
                f"{innings['runs']}/"
                f"{innings['wickets']} "
                f"({innings['overs']} overs)"
            )

        print("=" * 70)
    
    # --------------------------------------------------
    # INNINGS SUMMARY
    # --------------------------------------------------

    def innings_summary(self, innings_number):

        data = self.get_innings(innings_number)

        if data.empty:
            raise ValueError(
                f"Innings {innings_number} not found."
            )

        row = data.iloc[0]

        summary = pd.DataFrame([{
            "innings": innings_number,
            "team": row["team_batting_name"],
            "team_id": row["team_batting_id"],
            "runs": row["runs"],
            "wickets": row["wickets"],
            "overs": row["overs"],
            "balls": row["balls"],
            "byes": row["extra_byes"],
            "leg_byes": row["extra_leg_byes"],
            "wides": row["extra_wides"],
            "no_balls": row["extra_no_balls"],
            "penalty_runs": row["extra_penalty_runs"],
            "total_extras": row["total_extras"],
            "declared": row["declared"],
            "forfeited": row["forfeited_innings"]
        }])

        return summary

    # --------------------------------------------------
    # EXTRAS
    # --------------------------------------------------

    def extras_table(self, innings_number):

        summary = self.innings_summary(innings_number).iloc[0]

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

        # Replace missing values with zero
        extras["runs"] = extras["runs"].fillna(0).astype(int)

        # Only return extras that actually occurred
        extras = extras[
            extras["runs"] > 0
        ].reset_index(drop=True)

        return extras

    # --------------------------------------------------
    # FALL OF WICKETS
    # --------------------------------------------------

    def fall_of_wickets(self, innings_number):

        data = self.get_partnerships(innings_number).copy()

        if data.empty:
            return pd.DataFrame(
                columns=[
                    "wicket",
                    "score",
                    "batsman_out",
                    "batsman_out_id"
                ]
            )

        fow = data[
            [
                "wickets",
                "runs",
                "batsman_out_name",
                "batsman_out_id"
            ]
        ].copy()

        fow = fow.rename(
            columns={
                "wickets": "wicket",
                "runs": "score",
                "batsman_out_name": "batsman_out"
            }
        )

        return fow[
            [
                "wicket",
                "score",
                "batsman_out",
                "batsman_out_id"
            ]
        ]

    # --------------------------------------------------
    # COMPLETE STRUCTURED SCORECARD DATA
    # --------------------------------------------------

    def get_data(self):

        result = {
            "match": self.match.copy(),
            "innings": {}
        }

        for innings_number in self.innings["innings_number"]:

            result["innings"][int(innings_number)] = {
                "summary": self.innings_summary(innings_number),
                "batting": self.batting_table(innings_number),
                "bowling": self.bowling_table(innings_number),
                "fielding": self.fielding_table(innings_number),
                "extras": self.extras_table(innings_number),
                "fall_of_wickets": self.fall_of_wickets(
                    innings_number
                ),
                "partnerships": self.partnership_table(
                    innings_number
                )
            }

        return result

    # --------------------------------------------------
    # PRINTABLE SCORECARD
    # --------------------------------------------------

    def print_scorecard(self):

        print("=" * 70)

        # Match information
        match = self.match.iloc[0]

        home = (
            f"{match['home_club_name']} "
            f"{match['home_team_name']}"
        )

        away = (
            f"{match['away_club_name']} "
            f"{match['away_team_name']}"
        )

        print(f"{home} vs {away}")
        print("=" * 70)

        print(
            f"Competition: {match['competition_name']}"
        )

        print(
            f"Date: {match['match_date']}"
        )

        print(
            f"Ground: {match['ground_name']}"
        )

        print()

        # --------------------------------------------------
        # EACH INNINGS
        # --------------------------------------------------

        for innings_number in self.innings[
            "innings_number"
        ]:

            summary = self.innings_summary(
                innings_number
            ).iloc[0]

            print("-" * 70)

            print(
                f"{summary['team']} "
                f"{summary['runs']}/{summary['wickets']} "
                f"({summary['overs']} overs)"
            )

            print()

            # Batting
            batting = self.batting_table(
                innings_number
            )

            print("BATTING")
            print("-" * 70)

            for _, row in batting.iterrows():

                print(
                    f"{row['batsman_name']:<25} "
                    f"{row['dismissal']:<30} "
                    f"{row['runs']:>3} "
                    f"{row['balls']:>3} "
                    f"{row['fours']:>2} "
                    f"{row['sixes']:>2}"
                )

            print()

            # Extras
            extras = self.extras_table(
                innings_number
            )

            if not extras.empty:

                extras_text = ", ".join(
                    f"{row['type']}: {row['runs']}"
                    for _, row in extras.iterrows()
                )

                total_extras = extras["runs"].sum()

                print(
                    f"Extras: {extras_text} "
                    f"(Total {total_extras})"
                )

            print(
                f"Total: {summary['runs']}/"
                f"{summary['wickets']}"
            )

            print()

            # Fall of wickets
            fow = self.fall_of_wickets(
                innings_number
            )

            if not fow.empty:

                fow_text = ", ".join(
                    f"{row['wicket']}-{row['score']} "
                    f"({row['batsman_out']})"
                    for _, row in fow.iterrows()
                )

                print(
                    f"Fall of wickets: {fow_text}"
                )

            print()

            # Bowling
            bowling = self.bowling_table(
                innings_number
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
        
    def get_performances(self):
        """
        Identify notable individual performances in this match.

        Returns
        -------
        pandas.DataFrame
            One row per notable performance.
        """

        performances = []

        # ------------------------------------------------------------
        # BATTING
        # ------------------------------------------------------------

        for innings_number in sorted(
            self.batting["innings"].dropna().unique()
        ):

            batting = self.get_batting(innings_number)

            for _, row in batting.iterrows():

                runs = pd.to_numeric(
                    row["runs"],
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
                        "match_id": self.match_id,
                        "player_id": row["batsman_id"],
                        "player_name": row["batsman_name"],
                        "team_id": row["team_id"],
                        "team_name": row["team_name"],
                        "opposition_id": row["opposition_id"],
                        "opposition_name": row["opposition_name"],
                        "innings": innings_number,
                        "performance_type": "batting",
                        "achievement": achievement,
                        "value": int(runs),
                        "detail": f"{int(runs)} runs",
                    })

        # ------------------------------------------------------------
        # BOWLING
        # ------------------------------------------------------------

        for innings_number in sorted(
            self.bowling["innings"].dropna().unique()
        ):

            bowling = self.get_bowling(innings_number)

            for _, row in bowling.iterrows():

                wickets = pd.to_numeric(
                    row["wickets"],
                    errors="coerce"
                )

                if pd.isna(wickets):
                    continue

                achievement = None

                if wickets >= 10:
                    achievement = "10_wicket_match"

                elif wickets >= 7:
                    achievement = "7_wicket_haul"

                elif wickets >= 6:
                    achievement = "6_wicket_haul"

                elif wickets >= 5:
                    achievement = "five_wicket_haul"

                elif wickets >= 4:
                    achievement = "four_wicket_haul"

                elif wickets >= 3:
                    achievement = "three_wicket_haul"

                if achievement:

                    performances.append({
                        "match_id": self.match_id,
                        "player_id": row["bowler_id"],
                        "player_name": row["bowler_name"],
                        "team_id": row["team_id"],
                        "team_name": row["team_name"],
                        "opposition_id": row["opposition_id"],
                        "opposition_name": row["opposition_name"],
                        "innings": innings_number,
                        "performance_type": "bowling",
                        "achievement": achievement,
                        "value": int(wickets),
                        "detail": f"{int(wickets)} wickets",
                    })

        # ------------------------------------------------------------
        # FIELDING
        #
        # Notable fielding performances:
        #
        #   - 5+ catches by any fielder
        #   - 5+ total dismissals by a wicketkeeper
        #     (catches + stumpings)
        #
        # Individual catches and run outs are NOT stored as
        # performances.
        # ------------------------------------------------------------

        fielding = self.batting.copy()

        fielding["how_out_clean"] = (
            fielding["how_out"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.strip()
        )

        fielding = fielding[
            fielding["fielder_name"].notna()
            & (
                fielding["fielder_name"]
                .astype(str)
                .str.strip()
                != ""
            )
        ].copy()

        # ------------------------------------------------------------
        # CATCHES
        # ------------------------------------------------------------

        catches = fielding[
            fielding["how_out_clean"] == "ct"
        ].copy()

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
                    "innings",
                ],
                dropna=False
            )
            .size()
            .reset_index(name="catches")
        )

        # ------------------------------------------------------------
        # STUMPINGS
        # ------------------------------------------------------------

        stumpings = fielding[
            fielding["how_out_clean"] == "st"
        ].copy()

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
                    "innings",
                ],
                dropna=False
            )
            .size()
            .reset_index(name="stumpings")
        )

        # ------------------------------------------------------------
        # COMBINE CATCHES + STUMPINGS
        # ------------------------------------------------------------

        if not catch_counts.empty or not stumping_counts.empty:

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
                    "innings",
                ],
                how="outer"
            )

            fielding_counts["catches"] = (
                fielding_counts["catches"]
                .fillna(0)
                .astype(int)
            )

            fielding_counts["stumpings"] = (
                fielding_counts["stumpings"]
                .fillna(0)
                .astype(int)
            )

            fielding_counts["dismissals"] = (
                fielding_counts["catches"]
                + fielding_counts["stumpings"]
            )

            # --------------------------------------------------------
            # WICKETKEEPER
            #
            # Anyone with a stumping is identified as a wicketkeeper.
            #
            # A notable wicketkeeping performance is 5 or more
            # dismissals in the match, combining catches and stumpings.
            # --------------------------------------------------------

            wicketkeepers = fielding_counts[
                fielding_counts["stumpings"] > 0
            ]

            notable_keepers = wicketkeepers[
                wicketkeepers["dismissals"] >= 5
            ]

            for _, row in notable_keepers.iterrows():

                performances.append({
                    "match_id": self.match_id,
                    "player_id": row["fielder_id"],
                    "player_name": row["fielder_name"],
                    "team_id": row["team_id"],
                    "team_name": row["team_name"],
                    "opposition_id": row["opposition_id"],
                    "opposition_name": row["opposition_name"],
                    "innings": row["innings"],
                    "performance_type": "fielding",
                    "achievement": "wicketkeeper_dismissals",
                    "value": int(row["dismissals"]),
                    "detail": (
                        f"{int(row['dismissals'])} dismissals "
                        f"({int(row['catches'])} catches, "
                        f"{int(row['stumpings'])} stumpings)"
                    ),
                })

            # --------------------------------------------------------
            # NON-WICKETKEEPER 5+ CATCHES
            #
            # Wicketkeepers are handled separately above.
            # --------------------------------------------------------

            notable_catches = fielding_counts[
                (fielding_counts["catches"] >= 5)
                & (fielding_counts["stumpings"] == 0)
            ]

            for _, row in notable_catches.iterrows():

                performances.append({
                    "match_id": self.match_id,
                    "player_id": row["fielder_id"],
                    "player_name": row["fielder_name"],
                    "team_id": row["team_id"],
                    "team_name": row["team_name"],
                    "opposition_id": row["opposition_id"],
                    "opposition_name": row["opposition_name"],
                    "innings": row["innings"],
                    "performance_type": "fielding",
                    "achievement": "five_catch_performance",
                    "value": int(row["catches"]),
                    "detail": (
                        f"{int(row['catches'])} catches"
                    ),
                })

        # ------------------------------------------------------------
        # CREATE PERFORMANCE DATAFRAME
        # ------------------------------------------------------------

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
            "detail",
        ]

        performances_df = pd.DataFrame(
            performances,
            columns=columns
        )

        # ------------------------------------------------------------
        # READABLE DESCRIPTION
        # ------------------------------------------------------------

        if not performances_df.empty:

            def make_description(row):

                achievement = row["achievement"]
                value = row["value"]

                if achievement == "half_century":
                    return f"Half-century – {value} runs"

                elif achievement == "century":
                    return f"Century – {value} runs"

                elif achievement == "double_century":
                    return f"Double-century – {value} runs"

                elif achievement == "150":
                    return f"150 runs – {value} runs"

                elif achievement == "three_wicket_haul":
                    return "3-wicket haul"

                elif achievement == "four_wicket_haul":
                    return "4-wicket haul"

                elif achievement == "five_wicket_haul":
                    return "5-wicket haul"

                elif achievement == "six_wicket_haul":
                    return "6-wicket haul"

                elif achievement == "7_wicket_haul":
                    return "7-wicket haul"

                elif achievement == "10_wicket_match":
                    return "10-wicket match"

                elif achievement == "five_catch_performance":
                    return f"{value}-catch performance"

                elif achievement == "wicketkeeper_dismissals":
                    return row["detail"]

                else:
                    return row["detail"]

            performances_df["description"] = (
                performances_df
                .apply(make_description, axis=1)
            )

        return performances_df