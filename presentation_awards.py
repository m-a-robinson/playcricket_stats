#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
presentation_awards.py

Generates the presentation-night awards report for one season: for every
award in "Presentation Evening Awards and Criteria.docx", a top-5
shortlist of candidates computed from the SQLite store, next to that
award's qualification criteria. Awards decided by a person rather than a
stat (a captain's trophy, players' player, shoddy fielding) are listed
with no candidates -- there's nothing in the database that could answer
those, and this script doesn't try to guess.

Run once the season's data is up to date -- see README's "Play-Cricket --
the one source that actually needs re-syncing" for the sync/rebuild
steps, and reconcile.py after that -- then:

    python3 presentation_awards.py --sqlite-db playcricket_stats.sqlite --season 2026
    python3 presentation_awards.py --sqlite-db playcricket_stats.sqlite --season 2026 --out presentation_night_2026.md

QUALIFICATION and SENIOR_TEAMS below are transcribed directly from that
document; edit them here if the club's criteria change season to season.

Judgement calls this script makes that the source document doesn't spell
out (documented again at each function below):

- "Fielding" is scored as most catches -- the document itself calls this
  "subjective", so treat the shortlist as a starting point, not a winner.
- The Miscellaneous/"trophies you don't want to win" awards ("all teams")
  are read as every non-junior ELPMCC team, not just 1st/2nd/3rd XI --
  there's no qualification row restricting them the way the three main
  XIs are restricted.
- "White Boot Trophy" (worst bowling performance) is split into two
  shortlists -- most runs conceded, and worst economy rate -- since
  either can be the "worse" spell (a long spell that's merely expensive
  throughout vs. a short one that's truly dreadful), and each ranks
  single-innings figures among spells of at least MIN_BALLS_BOWLED
  balls, so one expensive over doesn't crowd out a genuinely bad spell.
- "Most improved player" has no defined metric in the document at all;
  the batting-average-improvement shortlist here is offered as an aid to
  the captain's decision, not a replacement for it.
"""

import argparse
import json
import sqlite3

import pandas as pd

from playcricket_scorecard import Scorecard
from sqlite_queries import ELPMCC_NAME, career_stats, notable_performances_summary


SENIOR_TEAMS = ["1st XI", "2nd XI", "3rd XI"]

# Transcribed from "Presentation Evening Awards and Criteria.docx"'s
# "Criteria" section: minimum batting innings + runs to qualify for that
# team's batting average award, minimum wickets for its bowling average
# award (the document gives no separate bowling-innings minimum).
QUALIFICATION = {
    "1st XI": {"min_batting_innings": 11, "min_runs": 300, "min_wickets": 30},
    "2nd XI": {"min_batting_innings": 11, "min_runs": 200, "min_wickets": 20},
    "3rd XI": {"min_batting_innings": 11, "min_runs": 200, "min_wickets": 20},
}

TOP_N = 5

# Minimum balls bowled in a single innings to be considered for the White
# Boot Trophy
# Adjustable; not given by the source document.
MIN_BALLS_BOWLED = 6

# Minimum batting innings in each of two seasons to be considered for the
# "most improved player" shortlist. Not given by the source document.
MIN_IMPROVEMENT_INNINGS = 5


# ==================================================================
# TEAM LOOKUP
# ==================================================================

def _short_team_name(team_name, club_name=ELPMCC_NAME):
    """Strip a leading club name off `team_name`, however it's joined --
    "<club> - <team>", "<club> <team>", or not joined at all -- so
    "1st XI", "East Lancs Paper Mill CC 1st XI" and "East Lancs Paper
    Mill CC - 1st XI" all normalise to the same "1st XI".

    Real data here is inconsistent: for this club, 1st/2nd XI happen to
    be stored with the club name embedded in team_name (apparently
    however Play-Cricket's API returned them for those matches), while
    3rd XI/Friendly XI/juniors aren't. Rather than editing the stored
    team_name (see the module-level note on why that's not durable --
    _upsert_team() re-matches by source-provided name on every rebuild,
    not by what's in the database), every lookup below normalises
    through this function instead."""

    for prefix in (f"{club_name} - ", f"{club_name} "):
        while team_name.startswith(prefix):
            team_name = team_name[len(prefix):]

    return team_name


def _team_ids(conn, team_names, club_name=ELPMCC_NAME):
    """Map each of `team_names` (short form, e.g. "1st XI") to its team_id
    for this club, in this build -- matched via _short_team_name() since
    team_name isn't stored consistently (see its docstring). A name with
    no matching team is simply left out of the result."""

    rows = conn.execute(
        """
        SELECT t.team_name, t.team_id
        FROM teams t
        JOIN clubs c ON c.club_id = t.club_id
        WHERE c.club_name = ?
        """,
        (club_name,)
    ).fetchall()

    by_short_name = {
        _short_team_name(raw_name, club_name): team_id
        for raw_name, team_id in rows
    }

    return {name: by_short_name[name] for name in team_names if name in by_short_name}


def _nonjunior_team_ids(conn, club_name=ELPMCC_NAME):
    """Every non-junior team_id this club has ever fielded (1st/2nd/3rd XI
    and any other senior/social side -- 5th XI, Friendly XI, etc.), for the
    Miscellaneous awards, which the document scopes to "all teams" rather
    than just the three XIs with their own qualification criteria."""

    rows = conn.execute(
        """
        SELECT t.team_id
        FROM teams t
        JOIN clubs c ON c.club_id = t.club_id
        WHERE c.club_name = ? AND t.is_juniors = 0
        """,
        (club_name,)
    ).fetchall()

    return [row[0] for row in rows]


# ==================================================================
# 1ST / 2ND / 3RD XI AWARDS
# ==================================================================

def best_batting_average(conn, season, team_id, team_name):
    q = QUALIFICATION[team_name]
    data = career_stats(conn, season=season, team_id=team_id)

    data = data[
        (data["batting_innings"] >= q["min_batting_innings"])
        & (data["runs"] >= q["min_runs"])
        & (data["batting_average"].notna())
    ]

    data = data.sort_values("batting_average", ascending=False)

    columns = [
        "player_name", "batting_innings", "runs", "times_dismissed",
        "highest_score", "batting_average"
    ]

    return data.head(TOP_N)[columns]


def best_bowling_average(conn, season, team_id, team_name):
    q = QUALIFICATION[team_name]
    data = career_stats(conn, season=season, team_id=team_id)

    data = data[
        (data["wickets"] >= q["min_wickets"])
        & (data["bowling_average"].notna())
    ]

    data = data.sort_values("bowling_average", ascending=True)

    columns = [
        "player_name", "bowling_innings", "wickets", "runs_conceded",
        "bowling_average", "economy"
    ]

    return data.head(TOP_N)[columns]


def top_fielding(conn, season, team_id):
    """Most catches -- the document itself flags this award as "subjective",
    so this is a starting shortlist, not a result."""

    data = career_stats(conn, season=season, team_id=team_id)
    data = data[data["catches"] > 0]
    data = data.sort_values("catches", ascending=False)

    columns = ["player_name", "games_played", "catches", "stumpings", "run_outs"]

    return data.head(TOP_N)[columns]


# ==================================================================
# MISCELLANEOUS ("all teams") AWARDS
# ==================================================================

def most_sixes(conn, season):
    """Most sixes, all teams -- alongside what share of the player's runs
    that season actually came from sixes, since two players tied on sixes
    can have earned them very differently (a big-hitting cameo vs. sixes
    scattered through a much longer, more measured innings total)."""

    data = career_stats(conn, season=season)
    data = data[data["sixes"] > 0]
    data["pct_runs_from_sixes"] = data["sixes"] * 6 * 100.0 / data["runs"]
    data = data.sort_values("sixes", ascending=False)

    columns = ["player_name", "games_played", "sixes", "runs", "pct_runs_from_sixes"]

    return data.head(TOP_N)[columns]


def most_ducks(conn, season, team_ids):
    """Most ducks, all teams -- ties broken by fewest batting innings, so
    the "winner" is whoever racked up that many ducks in the fewest trips
    to the crease, not just whoever batted the most often."""

    placeholders = ", ".join("?" * len(team_ids))

    query = f"""
        SELECT
            p.known_as AS player_name,
            SUM(CASE
                    WHEN b.runs = 0 AND b.not_out = 0 AND b.how_out IS NOT NULL
                    THEN 1 ELSE 0
                END) AS ducks,
            COUNT(*) AS batting_innings
        FROM batting_innings b
        JOIN innings i ON i.innings_id = b.innings_id
        JOIN matches m ON m.match_id = i.match_id
        JOIN players p ON p.player_id = b.player_id
        WHERE m.season = ?
          AND b.team_id IN ({placeholders})
          AND COALESCE(b.how_out, '') != 'did not bat'
        GROUP BY b.player_id
        HAVING ducks > 0
        ORDER BY ducks DESC, batting_innings ASC
        LIMIT {TOP_N}
    """

    return pd.read_sql_query(query, conn, params=[season] + team_ids)


def worst_bowling_by_runs(conn, season, team_ids, min_balls=MIN_BALLS_BOWLED):
    """Single-innings figures, ranked by total runs conceded, among spells
    of at least `min_balls` balls -- see MIN_BALLS_BOWLED. Rewards being
    taken for plenty over a long spell; see worst_bowling_by_economy() for
    the same idea scored by rate instead of total, which can surface a
    shorter, more expensive-per-over spell this misses."""

    placeholders = ", ".join("?" * len(team_ids))

    query = f"""
        SELECT
            p.known_as AS player_name, m.match_date,
            bo.overs, bo.wickets, bo.runs AS runs_conceded
        FROM bowling_innings bo
        JOIN innings i ON i.innings_id = bo.innings_id
        JOIN matches m ON m.match_id = i.match_id
        JOIN players p ON p.player_id = bo.player_id
        WHERE m.season = ?
          AND bo.team_id IN ({placeholders})
          AND bo.balls >= ?
        ORDER BY bo.runs DESC, bo.wickets ASC
        LIMIT {TOP_N}
    """

    return pd.read_sql_query(query, conn, params=[season] + team_ids + [min_balls])


def worst_bowling_by_economy(conn, season, team_ids, min_balls=MIN_BALLS_BOWLED):
    """Single-innings figures, ranked by economy rate (runs per over),
    among spells of at least `min_balls` balls -- see MIN_BALLS_BOWLED.
    Catches a spell that was expensive throughout even if the bowler
    wasn't kept on long enough to rack up worst_bowling_by_runs()'s total."""

    placeholders = ", ".join("?" * len(team_ids))

    query = f"""
        SELECT
            p.known_as AS player_name, m.match_date,
            bo.overs, bo.wickets, bo.runs AS runs_conceded,
            bo.runs * 6.0 / bo.balls AS economy
        FROM bowling_innings bo
        JOIN innings i ON i.innings_id = bo.innings_id
        JOIN matches m ON m.match_id = i.match_id
        JOIN players p ON p.player_id = bo.player_id
        WHERE m.season = ?
          AND bo.team_id IN ({placeholders})
          AND bo.balls >= ?
        ORDER BY economy DESC, bo.wickets ASC
        LIMIT {TOP_N}
    """

    return pd.read_sql_query(query, conn, params=[season] + team_ids + [min_balls])


def top_partnerships(conn, season, club_name=ELPMCC_NAME):
    """Top individual-wicket partnerships of the season, any team, any
    wicket -- reconstructed match by match via Scorecard/fall-of-wickets,
    since partnership totals aren't persisted in the SQLite store itself
    (see schema.sql/sqlite_store.py)."""

    team_names = conn.execute(
        """
        SELECT t.team_name
        FROM teams t
        JOIN clubs c ON c.club_id = t.club_id
        WHERE c.club_name = ? AND t.is_juniors = 0
        """,
        (club_name,)
    ).fetchall()

    # Short names (see _short_team_name()) -- matched against partnerships'
    # own team_name column the same way, since neither is guaranteed to
    # carry (or not carry) the club name as a prefix.
    allowed_short_names = {_short_team_name(name, club_name) for (name,) in team_names}

    rows = conn.execute(
        "SELECT match_id, match_date, source_payload FROM matches WHERE season = ?",
        (season,)
    ).fetchall()

    candidates = []

    for match_id, match_date, source_payload in rows:

        scorecard = Scorecard(json.loads(source_payload))

        partnerships = scorecard.partnerships

        if partnerships.empty:
            continue

        short_names = partnerships["team_name"].apply(_short_team_name, club_name=club_name)
        ours = partnerships[short_names.isin(allowed_short_names)]

        for _, row in ours.iterrows():
            candidates.append({
                "match_date": match_date,
                "team": _short_team_name(row["team_name"], club_name),
                "opposition": row["opposition_name"],
                "wicket": row["wickets"],
                "partnership": f"{row['batsman_out_name']} & {row['batsman_in_name']}",
                "runs": row["score_added"]
            })

    data = pd.DataFrame(candidates)

    if data.empty:
        return data

    return data.sort_values("runs", ascending=False).head(TOP_N).reset_index(drop=True)


def secretarys_cup_shortlist(conn, season):
    """Notable performances (centuries, five-wicket hauls, ...) of the
    season, with what they actually were (see
    sqlite_queries.notable_performances_summary()) rather than just a
    count, as an aid to the committee's choice -- "notable performance of
    the year" is inherently a judgement call, not something a season total
    alone can settle."""

    data = career_stats(conn, season=season)
    data = data[data["notable_performances"] > 0]

    summary = notable_performances_summary(conn, season=season)
    data = data.merge(summary, on="player_id", how="left")

    data = data.sort_values("notable_performances", ascending=False)

    columns = [
        "player_name", "games_played", "fifties", "hundreds",
        "double_hundreds", "five_wicket_hauls", "notable_performances",
        "performances"
    ]

    return data.head(TOP_N)[columns]


def most_improved_batting(conn, season, min_innings=MIN_IMPROVEMENT_INNINGS):
    """Biggest rise in batting average versus the previous season, among
    players qualifying (>= min_innings) in both -- an aid, not a metric the
    source document defines."""

    this_season = career_stats(conn, season=season)
    last_season = career_stats(conn, season=season - 1)

    this_season = this_season[this_season["batting_innings"] >= min_innings]
    last_season = last_season[last_season["batting_innings"] >= min_innings]

    merged = this_season.merge(
        last_season, on="player_id", suffixes=("", "_prev")
    )

    merged["improvement"] = merged["batting_average"] - merged["batting_average_prev"]
    merged = merged.sort_values("improvement", ascending=False)

    columns = [
        "player_name", "batting_average_prev", "batting_average", "improvement", "runs"
    ]

    return merged.head(TOP_N)[columns]


# ==================================================================
# REPORT
# ==================================================================

def build_report(conn, season):
    """Return an ordered list of (section, award, dataframe_or_None,
    criteria_or_note) tuples -- one entry per award in the source document,
    in the same order it lists them."""

    team_ids = _team_ids(conn, SENIOR_TEAMS)
    nonjunior_ids = _nonjunior_team_ids(conn)

    report = []

    for team_name in SENIOR_TEAMS:

        team_id = team_ids.get(team_name)
        q = QUALIFICATION[team_name]

        if team_id is None:
            report.append((
                team_name, "Batting average", None,
                f"No '{team_name}' team found for {ELPMCC_NAME} in this build."
            ))
            continue

        report.append((
            team_name, "Batting average",
            best_batting_average(conn, season, team_id, team_name),
            f"Min {q['min_batting_innings']} innings, {q['min_runs']} runs"
        ))

        report.append((
            team_name, "Bowling average",
            best_bowling_average(conn, season, team_id, team_name),
            f"Min {q['min_wickets']} wickets"
        ))

        report.append((
            team_name, "Fielding (top catches)",
            top_fielding(conn, season, team_id),
            "No fixed criteria -- subjective per the source document"
        ))

    report.append(("1st XI", "Captain's Trophy", None, "Chosen by captain"))
    report.append(("2nd XI", "Captain's Cup", None, "Chosen by captain"))
    report.append(("3rd XI", "Captain's Trophy", None, "Chosen by captain"))

    report.append((
        "Miscellaneous", "Most improved player",
        most_improved_batting(conn, season),
        "Chosen by captain -- batting-average improvement shown as an aid"
    ))

    report.append((
        "Miscellaneous", "Secretary's Cup",
        secretarys_cup_shortlist(conn, season),
        "Notable performance of the year -- shortlist shown as an aid"
    ))

    report.append((
        "Miscellaneous", "Six Hit",
        most_sixes(conn, season),
        "Most sixes, all teams"
    ))

    report.append((
        "Miscellaneous", "Partnership",
        top_partnerships(conn, season),
        "Top partnership, all teams, any wicket"
    ))

    report.append((
        "Miscellaneous", "Players' Player", None,
        "Voted by players -- no vote data in this database"
    ))

    report.append((
        "Trophies you don't want to win", "Duck",
        most_ducks(conn, season, nonjunior_ids),
        "Most ducks, all teams (ties broken by fewest batting innings)"
    ))

    report.append((
        "Trophies you don't want to win", "Lurpak Award", None,
        "Shoddy fielding -- dropped catches aren't tracked in this database"
    ))

    report.append((
        "Trophies you don't want to win", "White Boot Trophy -- Most Runs Conceded",
        worst_bowling_by_runs(conn, season, nonjunior_ids),
        f"Worst single-innings bowling figures by total runs conceded (min {MIN_BALLS_BOWLED} balls bowled)"
    ))

    report.append((
        "Trophies you don't want to win", "White Boot Trophy -- Worst Economy Rate",
        worst_bowling_by_economy(conn, season, nonjunior_ids),
        f"Worst single-innings economy rate (min {MIN_BALLS_BOWLED} balls bowled)"
    ))

    return report


# Column names to round to 2dp for display -- every average/economy-rate
# column any award above can produce, in one place, rather than rounding
# ad hoc inside each award function (and forgetting one).
RATE_COLUMNS = ["batting_average", "batting_average_prev", "improvement", "bowling_average", "economy"]


def _round_rates(data):
    data = data.copy()

    for column in RATE_COLUMNS:
        if column in data.columns:
            data[column] = data[column].round(2)

    return data


def render_markdown(report, season):
    lines = [f"# Presentation Evening {season} -- Awards Shortlists", ""]

    current_section = None

    for section, award, data, criteria in report:

        if section != current_section:
            lines.append(f"## {section}")
            lines.append("")
            current_section = section

        lines.append(f"### {award}")
        lines.append(f"*{criteria}*")
        lines.append("")

        if data is None:
            lines.append("_No stats candidates -- see criteria above._")
        elif data.empty:
            lines.append("_No qualifying candidates this season._")
        else:
            lines.append("```")
            lines.append(_round_rates(data).to_string(index=False))
            lines.append("```")

        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Generate the presentation-night awards shortlist report for one "
            "season, per 'Presentation Evening Awards and Criteria.docx'."
        )
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--out", default=None, help="Write the report to this file instead of stdout.")

    args = parser.parse_args()

    conn = sqlite3.connect(args.sqlite_db)

    report = build_report(conn, args.season)
    markdown = render_markdown(report, args.season)

    conn.close()

    if args.out:
        with open(args.out, "w") as f:
            f.write(markdown)
        print(f"Wrote {args.out}")
    else:
        print(markdown)
