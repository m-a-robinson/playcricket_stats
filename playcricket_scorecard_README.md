# Play-Cricket Scorecard Module

A Python module for retrieving, organising and presenting cricket match data from the **Play-Cricket API** using the `playcric` Python package.

The module is designed as the foundation for a larger historical cricket-data project. It keeps the underlying data as **pandas DataFrames**, while adding convenient methods for producing structured scorecard information, readable tables, notable-performance records and eventually personalised player scorecards.

---

## Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation and File Location](#installation-and-file-location)
- [Basic Usage](#basic-usage)
- [Scorecard Object](#scorecard-object)
- [Data Stored in the Scorecard](#data-stored-in-the-scorecard)
- [Match Information](#match-information)
- [Teams](#teams)
- [Innings](#innings)
- [Batting](#batting)
- [Bowling](#bowling)
- [Dismissals and Fielding](#dismissals-and-fielding)
- [Partnerships](#partnerships)
- [Extras](#extras)
- [Fall of Wickets](#fall-of-wickets)
- [Results and Summary](#results-and-summary)
- [Performance Detection](#performance-detection)
- [Performance Types](#performance-types)
- [Description Column](#description-column)
- [Complete Structured Scorecard Data](#complete-structured-scorecard-data)
- [Printable Scorecard](#printable-scorecard)
- [Example Match](#example-match)
- [Data Architecture](#data-architecture)
- [Future Development](#future-development)

---

# Overview

`playcricket_scorecard.py` provides a `Scorecard` class which represents a single Play-Cricket match.

The class takes a Play-Cricket API interface created with `playcric` and a match ID, then retrieves the relevant match data.

The basic workflow is:

```text
Play-Cricket
     │
     ▼
   playcric
     │
     ▼
Scorecard(match_id)
     │
     ├── match
     ├── innings
     ├── batting
     ├── bowling
     ├── partnerships
     └── performances
              │
              ▼
       Personalised scorecards
       / player statistics
       / historical database
```

The important design principle is that the original Play-Cricket data remains available as pandas DataFrames. The `Scorecard` class adds a layer of organisation and presentation rather than replacing the underlying data.

---

# Requirements

The project currently uses:

- Python 3.11
- pandas
- `playcric`
- A valid Play-Cricket API connection/configuration

The module has been developed and tested in an Anaconda environment.

Example environment:

```text
playcricket
Python 3.11
```

---

# Installation and File Location

The file is currently being used from the Desktop:

```text
~/Desktop/playcricket_scorecard.py
```

Python can import the module if the directory containing the file is on the Python path.

For example, if using Jupyter Notebook from the same directory:

```python
from playcricket_scorecard import Scorecard
```

If the module is stored elsewhere, either start Jupyter in that directory or add the directory to the Python path.

For a larger project, the eventual recommended structure would be something like:

```text
playcricket_project/
│
├── playcricket_scorecard.py
├── player_performances.py
├── import_data.py
├── database.py
├── generate_scorecard.py
│
├── data/
│   ├── raw/
│   └── processed/
│
└── notebooks/
    └── development.ipynb
```

---

# Basic Usage

First create the Play-Cricket API object.

For example:

```python
scorecard = Scorecard(
    playc,
    match_id=7240402,
    season=2026
)
```

The match ID comes from the `id` column in the Play-Cricket matches DataFrame.

For example:

```python
matches.columns.tolist()
```

returns:

```text
[
    'id',
    'status',
    'published',
    'last_updated',
    ...
]
```

Therefore:

```python
match_id = matches.iloc[0]["id"]
```

rather than using a column called `match_id`.

---

# Scorecard Object

Once created:

```python
scorecard = Scorecard(
    playc,
    match_id=7240402,
    season=2026
)
```

the object contains the main match datasets:

```python
scorecard.match
scorecard.innings
scorecard.batting
scorecard.bowling
scorecard.partnerships
scorecard.performances
```

All of these are pandas DataFrames.

This allows the data to be explored directly using normal pandas functionality.

For example:

```python
scorecard.batting.columns.tolist()
```

or:

```python
scorecard.batting.head()
```

---

# Data Stored in the Scorecard

## `scorecard.match`

Contains the Play-Cricket match record.

Typical columns include:

```text
id
status
published
last_updated
league_name
league_id
competition_name
competition_id
competition_type
match_type
game_type
season
match_date
match_time
ground_name
ground_id
home_club_name
home_team_name
home_team_id
home_club_id
away_club_name
away_team_name
away_team_id
away_club_id
umpire_1_name
umpire_1_id
...
```

The match ID is:

```python
scorecard.match["id"]
```

---

## `scorecard.innings`

Contains the innings-level totals.

Important columns include:

```text
innings_number
team_batting_name
team_batting_id
extra_byes
extra_leg_byes
extra_wides
extra_no_balls
extra_penalty_runs
total_extras
runs
wickets
overs
declared
forfeited_innings
match_id
```

Example:

```python
scorecard.innings
```

might produce:

```text
innings_number  team_batting_name                         runs  wickets
1               Darcy Lever CC - 2nd XI                  239       10
2               East Lancs Paper Mill CC - 1st XI        241        6
```

---

## `scorecard.batting`

Contains individual batting performances.

Important columns include:

```text
position
batsman_name
batsman_id
how_out
fielder_name
fielder_id
bowler_name
bowler_id
runs
fours
sixes
balls
team_name
team_id
opposition_name
opposition_id
innings
match_id
not_out
initial_name
```

---

## `scorecard.bowling`

Contains individual bowling performances.

Important columns include:

```text
bowler_name
bowler_id
overs
maidens
runs
wides
wickets
no_balls
team_name
team_id
opposition_name
opposition_id
innings
match_id
initial_name
balls
```

---

## `scorecard.partnerships`

Contains partnership information.

Important columns include:

```text
runs
wickets
batsman_out_name
batsman_out_id
batsman_in_name
batsman_in_id
batsman_in_runs
team_name
team_id
opposition_name
opposition_id
innings
match_id
score_added
```

---

# Match Information

The `match_info()` method returns the match record as a pandas Series:

```python
scorecard.match_info()
```

This provides convenient access to the underlying match information.

---

# Teams

The `teams()` method creates readable team names by combining the club and team fields supplied by Play-Cricket.

```python
scorecard.teams()
```

Example:

```python
{
    "home": "East Lancs Paper Mill CC 1st XI",
    "away": "Darcy Lever CC 2nd XI"
}
```

This avoids the problem of Play-Cricket sometimes separating the club name and team name into different fields.

---

# Innings

Use:

```python
scorecard.get_innings(2)
```

to retrieve a particular innings.

The method returns a pandas DataFrame.

A more presentation-oriented version is:

```python
scorecard.innings_summary(2)
```

Example fields:

```text
innings
team
team_id
runs
wickets
overs
balls
byes
leg_byes
wides
no_balls
penalty_runs
total_extras
declared
forfeited
```

---

# Batting

Retrieve all batting data:

```python
scorecard.get_batting()
```

Retrieve a particular innings:

```python
scorecard.get_batting(2)
```

The presentation version is:

```python
scorecard.batting_table(2)
```

This produces a cleaner scorecard-style table containing:

```text
position
batsman_name
dismissal
runs
balls
fours
sixes
batsman_id
```

Dismissals are converted into readable descriptions.

For example:

```text
c Mark Robinson b Joe Bloggs
run out (Mark Robinson)
b Joe Bloggs
lbw b Joe Bloggs
not out
```

---

# Bowling

Retrieve bowling data:

```python
scorecard.get_bowling(2)
```

The presentation table is:

```python
scorecard.bowling_table(2)
```

It returns:

```text
bowler_name
overs
maidens
runs
wides
no_balls
wickets
bowler_id
```

---

# Dismissals and Fielding

## Dismissals

```python
scorecard.get_dismissals(2)
```

returns batsmen who were dismissed.

---

## Catches

```python
scorecard.get_catches(2)
```

returns catches.

---

## Run outs

```python
scorecard.get_run_outs(2)
```

returns run outs.

---

## Fielding table

```python
scorecard.fielding_table(2)
```

provides a readable fielding dataset.

The current performance-detection system deliberately does **not** treat individual catches or run outs as notable performances.

Instead, it identifies exceptional fielding performances such as:

- 5 or more catches
- 5 or more wicketkeeper dismissals, combining catches and stumpings

This prevents a scorecard from becoming cluttered with ordinary fielding events.

---

# Stumpings

Stumpings are identified from the batting data using:

```python
how_out == "st"
```

The `fielder_name` and `fielder_id` identify the wicketkeeper.

For example:

```python
scorecard.batting[
    scorecard.batting["how_out"] == "st"
][
    ["batsman_name", "fielder_name", "fielder_id", "innings"]
]
```

This makes it possible to recognise a wicketkeeper who has, for example:

```text
3 catches + 2 stumpings = 5 dismissals
```

as a notable performance.

---

# Partnerships

Retrieve partnerships:

```python
scorecard.get_partnerships(2)
```

Create a presentation table:

```python
scorecard.partnership_table(2)
```

The presentation table contains:

```text
wicket
score_after_wicket
batsman_out
batsman_in
batsman_in_runs
score_added
```

---

# Extras

Use:

```python
scorecard.extras_table(2)
```

The output contains only extras that actually occurred.

For example:

```text
type          runs
Byes             3
Leg byes         8
Wides            8
No balls         7
```

The method converts API values to numeric values before filtering them. This is necessary because Play-Cricket data can contain blank/string values.

---

# Fall of Wickets

Use:

```python
scorecard.fall_of_wickets(2)
```

Example:

```text
wicket  score  batsman_out
1          0   Kaif Asif
2         20   Tom Partington
3         33   Keron Persaud
4        120   Abhishek Sharma
5        143   Jerome Roith
6        234   Rashid Masood
```

This is derived from the partnership data.

---

# Results and Summary

## Result

```python
scorecard.get_result()
```

returns the Play-Cricket result string.

Example:

```text
East Lancs Paper Mill CC - 1st XI - Won
```

---

## Summary

```python
scorecard.summary()
```

returns a dictionary containing:

```text
match_id
season
date
competition
ground
home_team
away_team
result
```

---

# Performance Detection

One of the main purposes of the module is to identify notable individual performances automatically.

These are stored in:

```python
scorecard.performances
```

The performance table is deliberately kept as a pandas DataFrame.

Example:

```python
scorecard.performances[
    [
        "player_name",
        "performance_type",
        "achievement",
        "value",
        "description"
    ]
]
```

Example output:

```text
player_name          performance_type   achievement          value   description
Rashid Masood       batting             century              109    Century – 109 runs
Louis Birmingham    bowling             four_wicket_haul       4    4-wicket haul
Rashid Masood       bowling             three_wicket_haul      3    3-wicket haul
```

This information will eventually form the bridge between the raw scorecard and the planned `PlayerPerformances` system.

---

# Performance Types

The current system recognises three categories.

## Batting

Thresholds:

```text
50+     Half-century
100+    Century
150+    150
200+    Double century
```

The highest applicable threshold is stored.

For example:

```text
109 runs → century
66 runs  → half-century
```

---

## Bowling

Thresholds:

```text
3+      3-wicket haul
4+      4-wicket haul
5+      5-wicket haul
6+      6-wicket haul
7+      7-wicket haul
10+     10-wicket match
```

The current implementation evaluates bowling performances by innings.

This means the 10-wicket category is currently based on the wickets recorded in an individual innings. A future enhancement could calculate a player's combined wickets across multiple innings in the same match.

---

## Fielding

Ordinary catches and run outs are intentionally excluded.

The current notable fielding thresholds are:

```text
5+ catches
5+ wicketkeeper dismissals
```

For wicketkeepers:

```text
dismissals = catches + stumpings
```

A player with:

```text
3 catches + 2 stumpings
```

therefore receives:

```text
5 dismissals
```

as a notable wicketkeeping performance.

Anyone with at least one stumping is currently treated as a wicketkeeper for this calculation.

---

# Performance Data Structure

Each performance contains:

```text
match_id
player_id
player_name
team_id
team_name
opposition_id
opposition_name
innings
performance_type
achievement
value
detail
description
```

For example:

```text
match_id:          7240402
player_id:         6255486
player_name:       Rashid Masood
team_id:           87898
team_name:         East Lancs Paper Mill CC - 1st XI
performance_type:  batting
achievement:       century
value:              109
description:       Century – 109 runs
```

---

# Description Column

The `description` column provides human-readable text intended for eventual use in scorecards, websites, social media graphics and personalised player summaries.

Examples:

```text
Half-century – 66 runs
Half-century – 58 runs
Century – 109 runs
3-wicket haul
4-wicket haul
5-catch performance
5 dismissals (3 catches, 2 stumpings)
```

The machine-readable `achievement` field should be retained because it is useful for filtering and future database work.

The `description` field is primarily for presentation.

---

# Complete Structured Scorecard Data

The `get_data()` method packages the complete scorecard into a nested Python dictionary while retaining pandas DataFrames.

```python
data = scorecard.get_data()
```

The structure is:

```text
data
│
├── match
│
└── innings
    │
    ├── 1
    │   ├── summary
    │   ├── batting
    │   ├── bowling
    │   ├── fielding
    │   ├── extras
    │   ├── fall_of_wickets
    │   └── partnerships
    │
    └── 2
        ├── summary
        ├── batting
        ├── bowling
        ├── fielding
        ├── extras
        ├── fall_of_wickets
        └── partnerships
```

This is intended to provide a clean structured representation of the complete match.

---

# Printable Scorecard

The `print_scorecard()` method produces a text-based scorecard.

```python
scorecard.print_scorecard()
```

It currently includes:

- Match
- Competition
- Date
- Ground
- Innings
- Batting
- Extras
- Total
- Fall of wickets
- Bowling

This is primarily a development and testing tool.

The longer-term objective is to use the same structured data to produce much more polished outputs.

---

# Example Match

Example match:

```text
East Lancs Paper Mill CC 1st XI
vs
Darcy Lever CC 2nd XI
```

Competition:

```text
GMCL Division 5 West
```

Date:

```text
2026-08-15
```

Result:

```text
East Lancs Paper Mill CC - 1st XI - Won
```

Score:

```text
Darcy Lever CC - 2nd XI
239/10 (38.4 overs)

East Lancs Paper Mill CC - 1st XI
241/6 (45.0 overs)
```

The match produced notable performances including:

```text
Rashid Masood – 109 runs
Louis Birmingham – 4 wickets
Rashid Masood – 3 wickets
```

---

# Data Architecture

The current project deliberately separates three concepts.

## 1. Raw Play-Cricket data

Provided by `playcric`.

Examples:

```python
playc.get_all_matches(...)
playc.get_individual_stats(...)
playc.get_innings_total_scores(...)
playc.get_match_partnerships(...)
```

---

## 2. Match-level Scorecard

Represented by:

```python
Scorecard
```

A `Scorecard` represents one match.

It contains all the data needed to describe that match:

```text
match
innings
batting
bowling
partnerships
performances
```

---

## 3. Player-level Historical Performance

The planned next stage is:

```python
PlayerPerformances
```

This will operate across multiple matches.

Conceptually:

```text
                 Play-Cricket
                       │
                       ▼
                  Scorecard
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       batting      bowling      fielding
          │            │            │
          └────────────┼────────────┘
                       ▼
                 performances
                       │
                       ▼
              PlayerPerformances
                       │
                       ▼
             Player career history
```

This distinction is important.

`Scorecard.performances` answers:

> "What notable performances occurred in this match?"

`PlayerPerformances` will eventually answer:

> "What notable performances has this player produced across their matches?"

---

# Future Development

The next major component is `PlayerPerformances`.

The planned system should allow queries such as:

```python
player = PlayerPerformances(
    playc,
    player_id=6255486,
    seasons=[2024, 2025, 2026]
)
```

and eventually:

```python
player.performances()
```

Potential outputs include:

```text
Date        Opponent             Achievement
2026-08-15  Darcy Lever 2nd XI   Century – 109 runs
2026-07-20  Worsley 2nd XI       Half-century – 66 runs
2026-06-14  Bolton 3rd XI        4-wicket haul
```

This historical information could then be used to personalise a player's scorecard.

For example:

```text
Rashid Masood
109 runs
Century

Career notable performances:
• 3 centuries
• 7 half-centuries
• 5 four-wicket hauls
```

The eventual system could therefore generate personalised scorecards automatically.

---

# Planned Long-Term Workflow

The broader project is intended to become a historical cricket-data system.

Potential workflow:

```text
                    Play-Cricket API
                           │
                           ▼
                    Match extraction
                           │
                           ▼
                     Scorecard
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Batting       Bowling       Fielding
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                     Performances
                           │
                           ▼
                  PlayerPerformances
                           │
                           ▼
                  Historical database
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        Web display    Personalised    Graphics
                         scorecards
```

This architecture should allow historical matches to be imported, analysed and eventually used to create personalised scorecards, club statistics and player records.

---

# Development Philosophy

The project currently follows several principles:

### Keep the original data

Do not throw away Play-Cricket fields simply to make a prettier table.

The raw pandas DataFrames remain available.

### Separate data from presentation

For example:

```python
scorecard.batting
```

contains the underlying data.

Whereas:

```python
scorecard.batting_table(2)
```

creates a presentation-oriented version.

### Use machine-readable performance codes

For example:

```text
achievement = "century"
```

rather than only storing:

```text
"Century – 109 runs"
```

This makes future filtering and database storage easier.

### Add human-readable descriptions

The `description` field is intended for direct use in:

- Scorecards
- Websites
- Social media graphics
- Player profiles
- News reports

### Keep player history separate from match data

A match should know what happened in that match.

A future `PlayerPerformances` class should aggregate those performances across matches.

---

# Current Status

The current `Scorecard` module successfully provides:

- Match retrieval
- Team identification
- Innings summaries
- Batting data
- Bowling data
- Dismissals
- Catches
- Run outs
- Stumpings
- Fielding analysis
- Partnerships
- Extras
- Fall of wickets
- Match result
- Complete structured scorecard data
- Printable scorecards
- Automated notable-performance detection
- Human-readable performance descriptions

The next planned development is the **`PlayerPerformances` module**, which will aggregate the `scorecard.performances` data across multiple matches and seasons.
