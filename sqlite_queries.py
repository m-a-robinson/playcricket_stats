#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
sqlite_queries.py

Career stats and leaderboards computed directly from the SQLite store
(schema.sql / sqlite_store.py).

This module exists to close two gaps identified while comparing the
new store against the existing pandas pipeline (PlayerPerformances /
MultiPlayerStats):

1. PlayerPerformances.summary() aggregates a player's career by
   (player, team), so anyone who turns out for more than one XI is
   silently split into several "people" with fragmented totals.
   career_stats() here aggregates by player_id alone by default (a
   true career total), and only splits by team when a team_id filter
   is explicitly supplied.

2. MultiPlayerStats.top_fifties() / top_hundreds() / highlights()
   reference "fifties" / "hundreds" / "notable_performances" columns
   that PlayerPerformances.summary() never actually produces, so
   those three methods silently return empty results today.
   career_stats() computes fifties/hundreds/double_hundreds/
   five_wicket_hauls/notable_performances directly from the data.

3. Opposition players (from CricHQ PDFs, or any other source) appear
   fully in scorecard data -- batting_innings, bowling_innings,
   match_appearances are untouched -- but aren't wanted as tracked
   "players" with their own career stats/leaderboard entries. By
   default career_stats() only includes players who have ever had a
   match_appearances row for ELPMCC_NAME; pass elpmcc_only=False
   to see everyone (e.g. to check how one specific opposition player
   has fared against this club).

SQLPlayerStats mirrors MultiPlayerStats' public method names and
qualification thresholds (same defaults) so it is a like-for-like
comparison, not a redesign of the leaderboard rules -- only the data
plumbing underneath has changed. It is a standalone read path; nothing
in the existing .py files has been modified to use it.
"""

import sqlite3

import pandas as pd


# ==================================================================
# CAREER STATS
# ==================================================================

_CAREER_SQL = """
WITH batting_base AS (
    SELECT b.*, m.season AS season, m.match_id AS match_id
    FROM batting_innings b
    JOIN innings i ON i.innings_id = b.innings_id
    JOIN matches m ON m.match_id = i.match_id
),
bowling_base AS (
    SELECT bo.*, m.season AS season, m.match_id AS match_id
    FROM bowling_innings bo
    JOIN innings i ON i.innings_id = bo.innings_id
    JOIN matches m ON m.match_id = i.match_id
),
appearances AS (
    SELECT ma.player_id, COUNT(DISTINCT ma.match_id) AS games_played
    FROM match_appearances ma
    JOIN matches m ON m.match_id = ma.match_id
    WHERE (:season IS NULL OR m.season = :season)
      AND (:team_id IS NULL OR ma.team_id = :team_id)
    GROUP BY ma.player_id
),
batting_agg AS (
    SELECT
        player_id,
        COUNT(*) AS batting_innings,
        SUM(runs) AS runs,
        SUM(CASE WHEN not_out = 0 THEN 1 ELSE 0 END) AS times_dismissed,
        MAX(runs) AS highest_score,
        SUM(balls) AS balls_faced,
        SUM(fours) AS fours,
        SUM(sixes) AS sixes,
        SUM(CASE WHEN runs >= 50 AND runs < 100 THEN 1 ELSE 0 END) AS fifties,
        SUM(CASE WHEN runs >= 100 AND runs < 200 THEN 1 ELSE 0 END) AS hundreds,
        SUM(CASE WHEN runs >= 200 THEN 1 ELSE 0 END) AS double_hundreds
    FROM batting_base
    WHERE COALESCE(how_out, '') != 'did not bat'
      AND (:season IS NULL OR season = :season)
      AND (:team_id IS NULL OR team_id = :team_id)
    GROUP BY player_id
),
bowling_agg AS (
    SELECT
        player_id,
        COUNT(*) AS bowling_innings,
        SUM(balls) AS balls_bowled,
        SUM(runs) AS runs_conceded,
        SUM(wickets) AS wickets,
        SUM(maidens) AS maidens,
        SUM(wides) AS wides,
        SUM(no_balls) AS no_balls,
        SUM(CASE WHEN wickets >= 5 THEN 1 ELSE 0 END) AS five_wicket_hauls
    FROM bowling_base
    WHERE (:season IS NULL OR season = :season)
      AND (:team_id IS NULL OR team_id = :team_id)
    GROUP BY player_id
),
-- A fielding dismissal is credited to the fielder's OWN team, which is
-- the opposite side to the batter they dismissed (batting_innings.team_id
-- is the batter's team).
fielding_base AS (
    SELECT
        b.fielder_player_id AS player_id,
        b.how_out AS how_out,
        b.season AS season,
        CASE WHEN b.team_id = m2.home_team_id
             THEN m2.away_team_id
             ELSE m2.home_team_id
        END AS fielding_team_id
    FROM batting_base b
    JOIN matches m2 ON m2.match_id = b.match_id
    WHERE b.fielder_player_id IS NOT NULL
),
fielding_agg AS (
    SELECT
        player_id,
        SUM(CASE WHEN LOWER(how_out) = 'ct' THEN 1 ELSE 0 END) AS catches,
        SUM(CASE WHEN LOWER(how_out) = 'st' THEN 1 ELSE 0 END) AS stumpings,
        SUM(CASE WHEN LOWER(how_out) = 'run out' THEN 1 ELSE 0 END) AS run_outs
    FROM fielding_base
    WHERE (:season IS NULL OR season = :season)
      AND (:team_id IS NULL OR fielding_team_id = :team_id)
    GROUP BY player_id
)
SELECT
    p.player_id,
    p.known_as AS player_name,
    COALESCE(app.games_played, 0) AS games_played,

    COALESCE(bat.batting_innings, 0) AS batting_innings,
    COALESCE(bat.runs, 0) AS runs,
    COALESCE(bat.times_dismissed, 0) AS times_dismissed,
    bat.highest_score AS highest_score,
    CASE WHEN COALESCE(bat.times_dismissed, 0) > 0
         THEN CAST(bat.runs AS REAL) / bat.times_dismissed
    END AS batting_average,
    COALESCE(bat.balls_faced, 0) AS balls_faced,
    CASE WHEN COALESCE(bat.balls_faced, 0) > 0
         THEN CAST(bat.runs AS REAL) * 100.0 / bat.balls_faced
    END AS strike_rate,
    COALESCE(bat.fours, 0) AS fours,
    COALESCE(bat.sixes, 0) AS sixes,
    COALESCE(bat.fifties, 0) AS fifties,
    COALESCE(bat.hundreds, 0) AS hundreds,
    COALESCE(bat.double_hundreds, 0) AS double_hundreds,

    COALESCE(bowl.bowling_innings, 0) AS bowling_innings,
    COALESCE(bowl.balls_bowled, 0) AS balls_bowled,
    COALESCE(bowl.runs_conceded, 0) AS runs_conceded,
    COALESCE(bowl.wickets, 0) AS wickets,
    COALESCE(bowl.maidens, 0) AS maidens,
    CASE WHEN COALESCE(bowl.wickets, 0) > 0
         THEN CAST(bowl.runs_conceded AS REAL) / bowl.wickets
    END AS bowling_average,
    CASE WHEN COALESCE(bowl.balls_bowled, 0) > 0
         THEN CAST(bowl.runs_conceded AS REAL) * 6.0 / bowl.balls_bowled
    END AS economy,
    CASE WHEN COALESCE(bowl.wickets, 0) > 0
         THEN CAST(bowl.balls_bowled AS REAL) / bowl.wickets
    END AS bowling_strike_rate,
    COALESCE(bowl.wides, 0) AS wides,
    COALESCE(bowl.no_balls, 0) AS no_balls,
    COALESCE(bowl.five_wicket_hauls, 0) AS five_wicket_hauls,

    COALESCE(field.catches, 0) AS catches,
    COALESCE(field.stumpings, 0) AS stumpings,
    COALESCE(field.run_outs, 0) AS run_outs,
    COALESCE(field.catches, 0) + COALESCE(field.stumpings, 0)
        + COALESCE(field.run_outs, 0) AS fielding_dismissals,

    COALESCE(bat.fifties, 0) + COALESCE(bat.hundreds, 0)
        + COALESCE(bat.double_hundreds, 0)
        + COALESCE(bowl.five_wicket_hauls, 0) AS notable_performances

FROM players p
LEFT JOIN appearances app ON app.player_id = p.player_id
LEFT JOIN batting_agg bat ON bat.player_id = p.player_id
LEFT JOIN bowling_agg bowl ON bowl.player_id = p.player_id
LEFT JOIN fielding_agg field ON field.player_id = p.player_id
WHERE (
    COALESCE(app.games_played, 0) > 0
    OR COALESCE(bat.batting_innings, 0) > 0
    OR COALESCE(bowl.bowling_innings, 0) > 0
    OR COALESCE(field.catches, 0) + COALESCE(field.stumpings, 0)
        + COALESCE(field.run_outs, 0) > 0
)
AND (
    :elpmcc_only = 0
    OR EXISTS (
        SELECT 1
        FROM match_appearances elpmcc_ma
        JOIN teams elpmcc_t ON elpmcc_t.team_id = elpmcc_ma.team_id
        JOIN clubs elpmcc_c ON elpmcc_c.club_id = elpmcc_t.club_id
        WHERE elpmcc_ma.player_id = p.player_id
          AND elpmcc_c.club_name = :elpmcc_name
    )
)
"""

# The club these career stats are FOR. Opposition players appear fully in
# scorecards (batting_innings/bowling_innings/match_appearances -- nothing
# about ingestion changes) but, by default, career_stats() excludes anyone
# who has never had a match_appearances row for this club: their stats
# aren't tracked as a "player record" the way this club's own players are.
# Pass elpmcc_only=False to lift the filter (e.g. to look up how a
# specific opposition player has fared against this club specifically).
ELPMCC_NAME = "East Lancs Paper Mill CC"


def career_stats(conn, season=None, team_id=None, elpmcc_only=True, elpmcc_name=ELPMCC_NAME):
    """
    Return one row per player with career (or, if team_id is given,
    per-team) batting/bowling/fielding/appearance totals.

    With no filters this is a TRUE career total across every team the
    player has turned out for -- unlike PlayerPerformances.summary(),
    which always splits a player's totals by team.

    By default (elpmcc_only=True) only players who have ever
    appeared for `elpmcc_name` are included -- opposition players
    still appear in full within scorecard data (batting_innings,
    bowling_innings, match_appearances), just not as tracked "players"
    with their own career stats/leaderboard entries.
    """

    params = {
        "season": int(season) if season is not None else None,
        "team_id": int(team_id) if team_id is not None else None,
        "elpmcc_only": 1 if elpmcc_only else 0,
        "elpmcc_name": elpmcc_name
    }

    return pd.read_sql_query(_CAREER_SQL, conn, params=params)


# ==================================================================
# LEADERBOARDS
# ==================================================================

class SQLPlayerStats:
    """
    Leaderboards computed from the SQLite store.

    Method names and default qualification thresholds match
    MultiPlayerStats exactly, so results can be compared directly.
    Only the underlying data path differs (SQL aggregation over the
    normalised store, rather than pandas aggregation over
    PlayerPerformances.summary()).
    """

    def __init__(self, conn, elpmcc_only=True, elpmcc_name=ELPMCC_NAME):
        self.conn = conn
        self.elpmcc_only = elpmcc_only
        self.elpmcc_name = elpmcc_name

    # ----------------------------------------------------------

    def career(self, season=None, team_id=None, elpmcc_only=None):
        return career_stats(
            self.conn, season=season, team_id=team_id,
            elpmcc_only=self.elpmcc_only if elpmcc_only is None else elpmcc_only,
            elpmcc_name=self.elpmcc_name
        )

    # ----------------------------------------------------------

    @staticmethod
    def _leaderboard(data, columns, sort_by, top_n=10, ascending=False, filters=None):

        if data.empty or sort_by not in data.columns:
            return pd.DataFrame(columns=["rank"] + columns)

        if filters is not None:
            data = filters(data)

        data = data[data[sort_by].notna()].copy()

        if data.empty:
            return pd.DataFrame(columns=["rank"] + columns)

        columns = [c for c in columns if c in data.columns]

        data = data.sort_values(sort_by, ascending=ascending, na_position="last")

        data["rank"] = (
            data[sort_by].rank(method="min", ascending=ascending).astype(int)
        )

        data = data[data["rank"] <= int(top_n)]

        return data[["rank"] + columns].reset_index(drop=True)

    # ----------------------------------------------------------
    # TOP RUNS
    # ----------------------------------------------------------

    def top_runs(self, season=None, team_id=None, top_n=10, min_batting_innings=0):

        data = self.career(season=season, team_id=team_id)

        columns = [
            "player_id", "player_name", "games_played", "batting_innings",
            "runs", "times_dismissed", "batting_average", "highest_score",
            "fifties", "hundreds", "balls_faced", "strike_rate"
        ]

        def qualification(d):
            return d[d["batting_innings"] >= min_batting_innings].copy()

        return self._leaderboard(data, columns, "runs", top_n=top_n, filters=qualification)

    # ----------------------------------------------------------
    # TOP BATTING AVERAGE
    # ----------------------------------------------------------

    def top_batting_average(self, season=None, team_id=None, min_batting_innings=5, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = [
            "player_id", "player_name", "games_played", "batting_innings",
            "runs", "times_dismissed", "batting_average", "highest_score",
            "strike_rate"
        ]

        def qualification(d):
            return d[
                (d["batting_innings"] >= min_batting_innings)
                & (d["batting_average"].notna())
            ].copy()

        return self._leaderboard(data, columns, "batting_average", top_n=top_n, filters=qualification)

    # ----------------------------------------------------------
    # TOP STRIKE RATE
    # ----------------------------------------------------------

    def top_strike_rate(self, season=None, team_id=None, min_batting_innings=5, min_runs=50, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = [
            "player_id", "player_name", "games_played", "batting_innings",
            "runs", "balls_faced", "strike_rate"
        ]

        def qualification(d):
            return d[
                (d["batting_innings"] >= min_batting_innings)
                & (d["runs"] >= min_runs)
                & (d["strike_rate"].notna())
            ].copy()

        return self._leaderboard(data, columns, "strike_rate", top_n=top_n, filters=qualification)

    # ----------------------------------------------------------
    # TOP SCORES
    # ----------------------------------------------------------

    def top_scores(self, season=None, team_id=None, min_batting_innings=0, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = [
            "player_id", "player_name", "games_played", "batting_innings",
            "runs", "highest_score"
        ]

        def qualification(d):
            return d[
                (d["batting_innings"] >= min_batting_innings)
                & (d["highest_score"].notna())
            ].copy()

        return self._leaderboard(data, columns, "highest_score", top_n=top_n, filters=qualification)

    # ----------------------------------------------------------
    # TOP FIFTIES / HUNDREDS
    #
    # These always returned empty from MultiPlayerStats because
    # PlayerPerformances.summary() never produced a "fifties" /
    # "hundreds" column for it to sort by.
    # ----------------------------------------------------------

    def top_fifties(self, season=None, team_id=None, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = ["player_id", "player_name", "games_played", "runs", "fifties", "hundreds", "highest_score"]

        return self._leaderboard(data, columns, "fifties", top_n=top_n)

    def top_hundreds(self, season=None, team_id=None, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = [
            "player_id", "player_name", "games_played", "runs",
            "fifties", "hundreds", "double_hundreds", "highest_score"
        ]

        return self._leaderboard(data, columns, "hundreds", top_n=top_n)

    # ----------------------------------------------------------
    # TOP WICKETS
    # ----------------------------------------------------------

    def top_wickets(self, season=None, team_id=None, min_bowling_innings=0, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = [
            "player_id", "player_name", "games_played", "bowling_innings",
            "balls_bowled", "runs_conceded", "wickets", "maidens",
            "bowling_average", "economy", "bowling_strike_rate"
        ]

        def qualification(d):
            return d[d["bowling_innings"] >= min_bowling_innings].copy()

        return self._leaderboard(data, columns, "wickets", top_n=top_n, filters=qualification)

    # ----------------------------------------------------------
    # TOP BOWLING AVERAGE / ECONOMY / STRIKE RATE
    # (lowest is best -- ascending=True)
    # ----------------------------------------------------------

    def top_bowling_average(self, season=None, team_id=None, min_bowling_innings=5, min_wickets=5, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = [
            "player_id", "player_name", "games_played", "bowling_innings",
            "wickets", "runs_conceded", "bowling_average", "economy", "bowling_strike_rate"
        ]

        def qualification(d):
            return d[
                (d["bowling_innings"] >= min_bowling_innings)
                & (d["wickets"] >= min_wickets)
                & (d["bowling_average"].notna())
            ].copy()

        return self._leaderboard(data, columns, "bowling_average", top_n=top_n, ascending=True, filters=qualification)

    def top_economy(self, season=None, team_id=None, min_bowling_innings=5, min_wickets=5, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = [
            "player_id", "player_name", "games_played", "bowling_innings",
            "balls_bowled", "wickets", "runs_conceded", "economy",
            "bowling_average", "bowling_strike_rate"
        ]

        def qualification(d):
            return d[
                (d["bowling_innings"] >= min_bowling_innings)
                & (d["wickets"] >= min_wickets)
                & (d["economy"].notna())
            ].copy()

        return self._leaderboard(data, columns, "economy", top_n=top_n, ascending=True, filters=qualification)

    def top_bowling_strike_rate(self, season=None, team_id=None, min_bowling_innings=5, min_wickets=5, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = [
            "player_id", "player_name", "games_played", "bowling_innings",
            "balls_bowled", "wickets", "bowling_strike_rate", "bowling_average", "economy"
        ]

        def qualification(d):
            return d[
                (d["bowling_innings"] >= min_bowling_innings)
                & (d["wickets"] >= min_wickets)
                & (d["bowling_strike_rate"].notna())
            ].copy()

        return self._leaderboard(data, columns, "bowling_strike_rate", top_n=top_n, ascending=True, filters=qualification)

    # ----------------------------------------------------------
    # TOP CATCHES / FIELDING
    # ----------------------------------------------------------

    def top_catches(self, season=None, team_id=None, min_games=0, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = ["player_id", "player_name", "games_played", "catches", "stumpings", "run_outs", "fielding_dismissals"]

        def qualification(d):
            return d[d["games_played"] >= min_games].copy()

        return self._leaderboard(data, columns, "catches", top_n=top_n, filters=qualification)

    def top_fielding(self, season=None, team_id=None, min_games=0, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = ["player_id", "player_name", "games_played", "catches", "stumpings", "run_outs", "fielding_dismissals"]

        def qualification(d):
            return d[d["games_played"] >= min_games].copy()

        return self._leaderboard(data, columns, "fielding_dismissals", top_n=top_n, filters=qualification)

    # ----------------------------------------------------------
    # HIGHLIGHTS (notable performances)
    #
    # Also always empty from MultiPlayerStats for the same reason as
    # top_fifties/top_hundreds above.
    # ----------------------------------------------------------

    def highlights(self, season=None, team_id=None, top_n=10):

        data = self.career(season=season, team_id=team_id)

        columns = ["player_id", "player_name", "games_played", "notable_performances"]

        return self._leaderboard(data, columns, "notable_performances", top_n=top_n)


# ==================================================================
# CLI SMOKE TEST
# ==================================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Print a quick leaderboard from the SQLite stats database."
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")
    parser.add_argument("--season", type=int, default=None)

    args = parser.parse_args()

    conn = sqlite3.connect(args.sqlite_db)
    stats = SQLPlayerStats(conn)

    print("Top run scorers:")
    print(stats.top_runs(season=args.season).to_string(index=False))

    print("\nTop wicket takers:")
    print(stats.top_wickets(season=args.season).to_string(index=False))

    print("\nHighlights (notable performances):")
    print(stats.highlights(season=args.season).to_string(index=False))

    conn.close()
