# PlayerPerformances

`PlayerPerformances` is a Python class for aggregating and analysing player-level cricket statistics from multiple `Scorecard` objects.

It is designed for historical Play-Cricket data and separates **player participation**, **batting**, **bowling**, **fielding**, and **notable performances** so that player statistics can be calculated consistently across multiple matches.

## Overview

The class answers questions such as:

- Who played in a season?
- How many games did each player play?
- How many runs did they score?
- How many times were they dismissed?
- What was their batting average and strike rate?
- How many wickets did they take?
- What was their bowling average, economy and strike rate?
- How many catches, stumpings and run-outs did they record?
- Which players achieved notable performances?

A key design principle is that **participation is independent of batting and bowling**.

A player who appears in a match but does not bat or bowl is still counted as having played.

---

## Requirements

- Python 3.9+
- pandas
- `Scorecard` objects containing the relevant Play-Cricket data

Install pandas if required:

```bash
pip install pandas
```

---

## Basic Usage

Import the class:

```python
from player_performances import PlayerPerformances
```

Create a `PlayerPerformances` object using one or more `Scorecard` objects:

```python
players = PlayerPerformances(
    [
        scorecard,
        scorecard_st
    ],
    club_id=9653
)
```

The optional `club_id` restricts the analysis to players belonging to the selected club.

For example, with:

```python
club_id=9653
```

only players belonging to that club are included, even when the scorecards contain opposition players.

---

# Data Model

The class maintains five core datasets.

## 1. Participation

`participation`

Contains players listed as participating in each match.

This is the **master player population**.

It is used to calculate games played and ensures that players are not excluded simply because they did not record a batting or bowling performance.

Example:

```python
players.get_participation(
    player_id=6255486,
    season=2026
)
```

---

## 2. Batting

`batting_records`

Contains batting innings from all supplied scorecards.

Access the data with:

```python
players.batting(
    player_id=6255486,
    season=2026
)
```

Batting statistics include:

- Runs
- Balls faced
- Fours
- Sixes
- Dismissals
- Highest score
- Batting average
- Strike rate
- 50s
- 100s
- 200s

---

## 3. Bowling

`bowling_records`

Contains bowling innings from all supplied scorecards.

Access the data with:

```python
players.bowling(
    player_id=6255486,
    season=2026
)
```

Bowling statistics include:

- Overs/bowling balls
- Maidens
- Runs conceded
- Wickets
- Wides
- No-balls
- Bowling average
- Economy rate
- Bowling strike rate

---

## 4. Fielding

`fielding_records`

Fielding information is derived from the batting dismissal data.

Each dismissal can contain:

- `fielder_id`
- `fielder_name`
- `how_out`

Dismissals are standardised into:

- Catches (`ct`)
- Stumpings (`st`)
- Run-outs (`ro`)

For example:

```python
players.fielding(
    player_id=6255486,
    season=2026
)
```

Fielding statistics are then summarised as:

```text
catches
stumpings
run_outs
fielding_dismissals
```

---

## 5. Highlights

`highlight_records`

Contains notable performances identified by the underlying `Scorecard` objects.

Examples include:

- Fifties
- Centuries
- Large scores
- Three-wicket hauls
- Four-wicket hauls
- Five-wicket hauls

Access them with:

```python
players.highlights(
    player_id=6255486,
    season=2026
)
```

---

# Player Summary

The main method for an individual player is:

```python
players.summary(
    player_id=6255486,
    season=2026
)
```

This returns a one-row pandas DataFrame containing the player's complete statistical summary.

Example columns:

```text
player_id
player_name
games_played

batting_innings
runs
times_dismissed
batting_average
highest_score
fifties
hundreds
double_hundreds
fours
sixes
balls_faced
strike_rate

bowling_innings
balls_bowled
runs_conceded
wickets
maidens
bowling_average
economy
bowling_strike_rate
wides
no_balls

catches
stumpings
run_outs
fielding_dismissals

notable_performances
```

---

# All Player Summaries

To obtain a summary for every player:

```python
players.get_all(
    season=2026
)
```

or:

```python
season = players.season(2026)
```

Example:

```python
print(
    season[
        [
            "player_name",
            "games_played",
            "runs",
            "wickets",
            "catches"
        ]
    ].to_string(index=False)
)
```

---

# Club Filtering

A `club_id` can be supplied when creating the class:

```python
players = PlayerPerformances(
    scorecards,
    club_id=9653
)
```

This is important because a scorecard contains players from **both teams**.

When `club_id` is supplied, the class restricts player analysis to players belonging to that club.

This applies even when individual batting, bowling or fielding datasets do not contain `club_id` directly.

The class uses participation records to identify the players belonging to the selected club.

Therefore:

```python
players.season(2026)
```

returns the selected club's players rather than every player appearing in the supplied scorecards.

---

# Team Filtering

A specific team can also be selected using `team_id`.

For example:

```python
players.season(
    2026,
    team_id=87898
)
```

Or:

```python
players.team(
    team_id=87898,
    season=2026
)
```

This allows the same class to analyse either:

- the whole club, or
- an individual team within the club.

---

# Filtering Individual Records

Most methods support:

- `player_id`
- `season`
- `team_id`

For example:

```python
players.batting(
    player_id=6255486,
    season=2026
)
```

```python
players.bowling(
    player_id=6255486,
    season=2026
)
```

```python
players.fielding(
    player_id=6255486,
    season=2026
)
```

```python
players.highlights(
    player_id=6255486,
    season=2026
)
```

Participation also supports `opposition_id`:

```python
players.get_participation(
    player_id=6255486,
    season=2026,
    opposition_id=20941
)
```

---

# Example

A complete example:

```python
from player_performances import PlayerPerformances

players = PlayerPerformances(
    [
        scorecard,
        scorecard_st
    ],
    club_id=9653
)

# Season summary
season = players.season(2026)

print(
    season[
        [
            "player_name",
            "games_played",
            "runs",
            "batting_average",
            "wickets",
            "bowling_average",
            "economy",
            "catches",
            "run_outs",
            "notable_performances"
        ]
    ].to_string(index=False)
)
```

---

# Example Output

A season summary may look like:

```text
       player_name  games_played  runs  batting_average  wickets  bowling_average  economy  catches  run_outs  notable_performances
   Louis Birmingham             2    18              18.0        6             21.00     5.52        1         0                     1
     Tom Partington             2    67              33.5        1             49.00     4.45        2         0                     1
       Rashid Masood             2   175              87.5        7             13.14     5.52        1         0                     4
         Adam Sajewicz           1     0               NaN        2             24.00     6.00        0         0                     0
```

---

# Statistical Definitions

## Games Played

Games played is calculated from participation records:

```python
participation["match_id"].nunique()
```

This means a player counts as having played even if they did not bat or bowl.

## Batting Average

```text
runs / times dismissed
```

If the player has not been dismissed, the batting average is returned as `None`/`NaN`.

## Strike Rate

```text
runs / balls faced × 100
```

## Bowling Average

```text
runs conceded / wickets
```

## Economy Rate

```text
runs conceded / overs bowled
```

The class calculates overs from recorded legal balls:

```text
runs conceded / (balls bowled / 6)
```

## Bowling Strike Rate

```text
balls bowled / wickets
```

## Fielding Dismissals

Currently calculated as:

```text
catches + stumpings + run-outs
```

---

# Design Philosophy

The class deliberately separates the different types of player data.

```text
                    Scorecards
                        │
                        ▼
               PlayerPerformances
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
 Participation       Batting          Bowling
        │               │               │
        └───────────────┼───────────────┘
                        ▼
                    Summary
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
          Fielding             Highlights
```

This structure makes the class suitable for progressively adding historical matches without changing the underlying statistical model.

---

# Why Participation Is Separate

A common problem with cricket statistics is using batting or bowling records to determine whether somebody played.

For example, a player may:

- field but not bat
- bat but not bowl
- bowl but not bat
- play as a substitute/low-order player
- appear in a scorecard without recording a batting or bowling innings

Therefore, games played are calculated from `participation`, while batting and bowling statistics are calculated independently.

This prevents player appearance statistics from being underestimated.

---

# Club and Historical Statistics

`PlayerPerformances` is intended to form the **player-level statistics layer** of a wider cricket statistics system.

The intended architecture is:

```text
Play-Cricket / Scorecard data
            │
            ▼
        Scorecard
            │
            ├───────────────┐
            ▼               ▼
 PlayerPerformances    ClubStatistics
            │               │
            ▼               ▼
     Player statistics   Team/club statistics
```

`PlayerPerformances` focuses on individual players.

A separate `ClubStatistics` class can subsequently use the same scorecards to calculate:

- Match results
- Team wins and losses
- Runs scored/conceded
- Wickets taken/lost
- Team batting and bowling records
- Opposition records
- Season records
- Historical club statistics

---

# Current Status

The class currently supports:

- [x] Player participation
- [x] Games played
- [x] Batting statistics
- [x] Bowling statistics
- [x] Fielding dismissals
- [x] Catches
- [x] Stumpings
- [x] Run-outs
- [x] Notable performances
- [x] Individual player summaries
- [x] Season player summaries
- [x] Team filtering
- [x] Club filtering
- [x] Multiple scorecards
- [x] Historical match aggregation

---

# Future Development

Potential future additions include:

- Career player statistics
- Player records by opposition
- Player records by competition
- Player records by ground
- Best batting performances
- Best bowling performances
- Player milestone reports
- Season comparison
- Career comparison
- Export to CSV/Excel
- Automated club reports
- Integration with `ClubStatistics`
- Automated website/social-media reporting

---

## License

Add the project's chosen licence here.

## Author

Mark Robinson

Developed as part of a wider project to recover, analyse and present historical cricket statistics using Play-Cricket data.
