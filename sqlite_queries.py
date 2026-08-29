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
      AND (:include_juniors = 1 OR :team_id IS NOT NULL OR ma.team_id NOT IN (SELECT team_id FROM teams WHERE is_juniors = 1))
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
      AND (:include_juniors = 1 OR :team_id IS NOT NULL OR team_id NOT IN (SELECT team_id FROM teams WHERE is_juniors = 1))
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
      AND (:include_juniors = 1 OR :team_id IS NOT NULL OR team_id NOT IN (SELECT team_id FROM teams WHERE is_juniors = 1))
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
      AND (:include_juniors = 1 OR :team_id IS NOT NULL OR fielding_team_id NOT IN (SELECT team_id FROM teams WHERE is_juniors = 1))
    GROUP BY player_id
),
-- NMCL "Final Averages" rows are season-end aggregates, not per-match
-- data, and only cover players who cleared that season's qualification
-- threshold -- see nmcl_stats.py. Only the genuinely additive figures
-- (a season total plus another season total is still a valid total) are
-- summed here: runs, batting dismissals (innings_played - not_outs, the
-- only way this source expresses "times out"), wickets, runs conceded,
-- catches. Deliberately NOT summed: balls_bowled (NMCL gives "overs" as
-- printed text, not a reliable ball count, so economy/bowling strike
-- rate are never recomputed from it) and games_played/fours/sixes/
-- fifties/hundreds (this source doesn't report them at all). See
-- career_stats()'s include_nmcl parameter for how this gets folded in
-- (opt-in, and only into the figures listed above) versus nmcl_season_stats()
-- for the raw rows on their own.
nmcl_agg AS (
    SELECT
        player_id,
        SUM(CASE WHEN discipline = 'batting' THEN runs ELSE 0 END) AS nmcl_runs,
        SUM(CASE WHEN discipline = 'batting'
                 THEN COALESCE(innings_played, 0) - COALESCE(not_outs, 0)
                 ELSE 0 END) AS nmcl_dismissals,
        MAX(CASE WHEN discipline = 'batting' THEN highest_score END) AS nmcl_highest_score,
        SUM(CASE WHEN discipline = 'bowling' THEN wickets ELSE 0 END) AS nmcl_wickets,
        SUM(CASE WHEN discipline = 'bowling' THEN runs_conceded ELSE 0 END) AS nmcl_runs_conceded,
        SUM(CASE WHEN discipline = 'wicketkeeping' THEN catches ELSE 0 END) AS nmcl_catches
    FROM nmcl_season_stats
    WHERE (:season IS NULL OR season = :season)
      AND (:team_id IS NULL OR team_id = :team_id)
    GROUP BY player_id
),
-- Manually-curated individual honours (see club_awards.py) -- season
-- batting/bowling/wicketkeeping average winners, players' player of
-- the year, club captaincy. Team honours (league/cup wins) are looked
-- up separately via team_awards() below rather than folded into a
-- player row: a squad-wide trophy doesn't belong to any one player's
-- career line the way an individual award does. Ordered by season
-- before GROUP_CONCAT so a player's awards list reads chronologically.
awards_agg AS (
    SELECT player_id, GROUP_CONCAT(award_text, '; ') AS awards
    FROM (
        SELECT player_id, season || ' ' || competition || ' ' || award_name AS award_text
        FROM player_awards
        WHERE (:season IS NULL OR season = :season)
        ORDER BY season, competition, award_name
    )
    GROUP BY player_id
)
SELECT
    p.player_id,
    p.known_as AS player_name,
    COALESCE(app.games_played, 0) AS games_played,

    COALESCE(bat.batting_innings, 0) AS batting_innings,
    COALESCE(bat.runs, 0)
        + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_runs, 0) ELSE 0 END AS runs,
    COALESCE(bat.times_dismissed, 0)
        + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_dismissals, 0) ELSE 0 END AS times_dismissed,
    CASE WHEN :include_nmcl = 1 AND nmcl.nmcl_highest_score IS NOT NULL
              AND (bat.highest_score IS NULL OR nmcl.nmcl_highest_score > bat.highest_score)
         THEN nmcl.nmcl_highest_score
         ELSE bat.highest_score
    END AS highest_score,
    CASE WHEN (
             COALESCE(bat.times_dismissed, 0)
             + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_dismissals, 0) ELSE 0 END
         ) > 0
         THEN CAST((
             COALESCE(bat.runs, 0)
             + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_runs, 0) ELSE 0 END
         ) AS REAL) / (
             COALESCE(bat.times_dismissed, 0)
             + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_dismissals, 0) ELSE 0 END
         )
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
    COALESCE(bowl.runs_conceded, 0)
        + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_runs_conceded, 0) ELSE 0 END AS runs_conceded,
    COALESCE(bowl.wickets, 0)
        + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_wickets, 0) ELSE 0 END AS wickets,
    COALESCE(bowl.maidens, 0) AS maidens,
    CASE WHEN (
             COALESCE(bowl.wickets, 0)
             + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_wickets, 0) ELSE 0 END
         ) > 0
         THEN CAST((
             COALESCE(bowl.runs_conceded, 0)
             + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_runs_conceded, 0) ELSE 0 END
         ) AS REAL) / (
             COALESCE(bowl.wickets, 0)
             + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_wickets, 0) ELSE 0 END
         )
    END AS bowling_average,
    -- economy/bowling_strike_rate are never adjusted for NMCL: it gives
    -- overs as printed text, not a reliable ball count, and guessing one
    -- from it risks being wrong in a way runs/wickets addition isn't.
    CASE WHEN COALESCE(bowl.balls_bowled, 0) > 0
         THEN CAST(bowl.runs_conceded AS REAL) * 6.0 / bowl.balls_bowled
    END AS economy,
    CASE WHEN COALESCE(bowl.wickets, 0) > 0
         THEN CAST(bowl.balls_bowled AS REAL) / bowl.wickets
    END AS bowling_strike_rate,
    COALESCE(bowl.wides, 0) AS wides,
    COALESCE(bowl.no_balls, 0) AS no_balls,
    COALESCE(bowl.five_wicket_hauls, 0) AS five_wicket_hauls,

    COALESCE(field.catches, 0)
        + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_catches, 0) ELSE 0 END AS catches,
    COALESCE(field.stumpings, 0) AS stumpings,
    COALESCE(field.run_outs, 0) AS run_outs,
    COALESCE(field.catches, 0) + COALESCE(field.stumpings, 0)
        + COALESCE(field.run_outs, 0)
        + CASE WHEN :include_nmcl = 1 THEN COALESCE(nmcl.nmcl_catches, 0) ELSE 0 END AS fielding_dismissals,

    COALESCE(bat.fifties, 0) + COALESCE(bat.hundreds, 0)
        + COALESCE(bat.double_hundreds, 0)
        + COALESCE(bowl.five_wicket_hauls, 0) AS notable_performances,

    -- True when this row's totals above include an NMCL season-aggregate
    -- contribution (only possible when include_nmcl=True was passed AND
    -- this player actually has an nmcl_season_stats row in scope) -- so a
    -- reader can tell a blended total from a pure match-level one without
    -- re-deriving it themselves.
    CASE WHEN :include_nmcl = 1 AND nmcl.player_id IS NOT NULL THEN 1 ELSE 0 END AS includes_nmcl,

    aw.awards AS awards

FROM players p
LEFT JOIN appearances app ON app.player_id = p.player_id
LEFT JOIN batting_agg bat ON bat.player_id = p.player_id
LEFT JOIN bowling_agg bowl ON bowl.player_id = p.player_id
LEFT JOIN fielding_agg field ON field.player_id = p.player_id
LEFT JOIN nmcl_agg nmcl ON nmcl.player_id = p.player_id
LEFT JOIN awards_agg aw ON aw.player_id = p.player_id
WHERE (
    COALESCE(app.games_played, 0) > 0
    OR COALESCE(bat.batting_innings, 0) > 0
    OR COALESCE(bowl.bowling_innings, 0) > 0
    OR COALESCE(field.catches, 0) + COALESCE(field.stumpings, 0)
        + COALESCE(field.run_outs, 0) > 0
    OR (:include_nmcl = 1 AND nmcl.player_id IS NOT NULL)
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
    -- nmcl_season_stats has no match_appearances row to check (it's a
    -- season aggregate, not a match), but every row in it is already
    -- this club's own league averages by construction (see nmcl_stats.py)
    -- -- only relevant when its contribution is actually being folded in.
    OR (:include_nmcl = 1 AND nmcl.player_id IS NOT NULL)
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


def career_stats(
    conn, season=None, team_id=None, elpmcc_only=True,
    elpmcc_name=ELPMCC_NAME, include_juniors=False, include_nmcl=False
):
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

    By default (include_juniors=False) appearances/batting/bowling/
    fielding for a junior team (teams.is_juniors -- "Under 9", "Under 11",
    see sqlite_store.py's _classify_team()) are excluded from every
    total, the same way opposition players are: junior matches stay in
    the underlying scorecard tables untouched, just not folded into a
    player's main career figures or any leaderboard. Pass
    include_juniors=True to include them, or filter to one junior team
    specifically with team_id instead (which already overrides this).

    By default (include_nmcl=False) `nmcl_season_stats` rows (see
    nmcl_stats.py) are left out entirely -- they're season-end
    qualification-threshold aggregates, not per-match data, so they
    can't honestly contribute to games_played/fours/sixes/fifties/
    hundreds/economy/bowling_strike_rate the way real scorecard rows
    can. Pass include_nmcl=True to fold in the figures that ARE safely
    additive across a season aggregate and real match data (runs,
    times_dismissed, highest_score, wickets, runs_conceded, catches,
    and the averages recomputed from those combined totals) -- a row
    that actually received a contribution this way has `includes_nmcl`
    set to 1, so a blended total is never mistaken for a pure
    match-level one. Use nmcl_season_stats() instead to see the raw
    rows on their own, un-blended.

    Every row also carries `awards` -- a semicolon-separated summary of
    that player's individual honours from `player_awards` (see
    club_awards.py: season batting/bowling/wicketkeeping average
    winners, players' player of the year, club captaincy), `None` if
    they have none. Filtered by `season` the same way every other
    total here is. Team honours (league/cup wins) aren't folded into a
    player row -- look them up separately with team_awards() below.
    """

    params = {
        "season": int(season) if season is not None else None,
        "team_id": int(team_id) if team_id is not None else None,
        "elpmcc_only": 1 if elpmcc_only else 0,
        "elpmcc_name": elpmcc_name,
        "include_juniors": 1 if include_juniors else 0,
        "include_nmcl": 1 if include_nmcl else 0
    }

    return pd.read_sql_query(_CAREER_SQL, conn, params=params)


# ==================================================================
# NMCL SEASON STATS (raw, un-blended)
# ==================================================================

def nmcl_season_stats(conn, player_id=None, season=None):
    """
    Return nmcl_season_stats rows as-is -- one row per (player, season,
    division, discipline) -- with the player's canonical name joined in.
    This is the season-aggregate data career_stats()'s include_nmcl
    folds in on request; use this instead to see it on its own, e.g. to
    check what a blended total in career_stats() is actually made of, or
    to look at a season this club has no match-level data for at all
    (2000-2005, 2011-2013 -- see the README milestone notes) purely on
    its own terms.
    """

    query = """
        SELECT
            s.stat_id, s.player_id, p.known_as AS player_name, s.team_id,
            s.season, s.division, s.discipline,
            s.innings_played, s.not_outs, s.highest_score, s.highest_score_not_out,
            s.runs, s.overs, s.maidens, s.runs_conceded, s.wickets, s.catches
        FROM nmcl_season_stats s
        JOIN players p ON p.player_id = s.player_id
        WHERE (:player_id IS NULL OR s.player_id = :player_id)
          AND (:season IS NULL OR s.season = :season)
        ORDER BY s.season, s.division, s.discipline, p.known_as
    """

    params = {
        "player_id": int(player_id) if player_id is not None else None,
        "season": int(season) if season is not None else None
    }

    return pd.read_sql_query(query, conn, params=params)


# ==================================================================
# CLUB AWARDS (raw, one row per honour)
# ==================================================================
#
# See club_awards.py for how these are ingested (manually curated, not
# parsed from any source file) and schema.sql for why team/player
# honours are two separate tables rather than one with nullable
# team_id/player_id columns.

def player_awards(conn, player_id=None, season=None):
    """
    Return player_awards rows as-is -- one row per individual honour
    (season batting/bowling/wicketkeeping average winner, players'
    player of the year, a single season of club captaincy) -- with the
    player's canonical name joined in. career_stats()'s `awards` column
    summarises the same data per player; use this instead to see it as
    its own table, e.g. to list every captain across the club's history.
    """

    query = """
        SELECT
            a.award_id, a.player_id, p.known_as AS player_name,
            a.season, a.competition, a.award_name, a.notes
        FROM player_awards a
        JOIN players p ON p.player_id = a.player_id
        WHERE (:player_id IS NULL OR a.player_id = :player_id)
          AND (:season IS NULL OR a.season = :season)
        ORDER BY a.season, p.known_as
    """

    params = {
        "player_id": int(player_id) if player_id is not None else None,
        "season": int(season) if season is not None else None
    }

    return pd.read_sql_query(query, conn, params=params)


def team_awards(conn, team_id=None, season=None):
    """
    Return team_awards rows as-is -- one row per team honour (a
    league/cup win) -- with the team and club's names joined in. Not
    folded into career_stats(): a squad-wide trophy doesn't belong to
    any one player's career line the way an individual award does.
    """

    query = """
        SELECT
            a.award_id, a.team_id, t.team_name, c.club_name,
            a.season, a.competition, a.award_name, a.notes
        FROM team_awards a
        JOIN teams t ON t.team_id = a.team_id
        JOIN clubs c ON c.club_id = t.club_id
        WHERE (:team_id IS NULL OR a.team_id = :team_id)
          AND (:season IS NULL OR a.season = :season)
        ORDER BY a.season, c.club_name, t.team_name
    """

    params = {
        "team_id": int(team_id) if team_id is not None else None,
        "season": int(season) if season is not None else None
    }

    return pd.read_sql_query(query, conn, params=params)


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

    def __init__(
        self, conn, elpmcc_only=True, elpmcc_name=ELPMCC_NAME,
        include_juniors=False, include_nmcl=False
    ):
        self.conn = conn
        self.elpmcc_only = elpmcc_only
        self.elpmcc_name = elpmcc_name
        self.include_juniors = include_juniors
        self.include_nmcl = include_nmcl

    # ----------------------------------------------------------

    def career(self, season=None, team_id=None, elpmcc_only=None, include_juniors=None, include_nmcl=None):
        return career_stats(
            self.conn, season=season, team_id=team_id,
            elpmcc_only=self.elpmcc_only if elpmcc_only is None else elpmcc_only,
            elpmcc_name=self.elpmcc_name,
            include_juniors=self.include_juniors if include_juniors is None else include_juniors,
            include_nmcl=self.include_nmcl if include_nmcl is None else include_nmcl
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
