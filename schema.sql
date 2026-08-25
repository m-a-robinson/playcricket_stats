-- schema.sql
--
-- Normalised SQLite schema for the cricket stats database.
--
-- This is the canonical, queryable store. It is fed FROM the existing
-- PlayCricketDatabase JSON cache (which stays as the sync/API-minimisation
-- layer) and, in time, from the CricHQ PDF and CricketStatz .csd sources.
--
-- Design notes
-- ------------
-- Every fact table carries a `source` + `source_*_id` pair so rows from
-- different origins (play_cricket / crichq_pdf / cricketstatz) can coexist
-- before reconciliation (roadmap item 4) links them together.
--
-- `players` is the canonical player identity. `player_source_ids` maps
-- each source system's own identifier (or, for sources with no numeric
-- id, a derived key such as a normalised name) onto one canonical player.
-- Batting/bowling rows always point at the canonical player_id, so
-- career stats can span sources once reconciliation fills the mapping in.
--
-- Raw source payloads are preserved on `matches.source_payload` (JSON
-- text) so nothing is lost if a normalised column turns out to be
-- insufficient later.

PRAGMA foreign_keys = ON;

-- ================================================================
-- CLUBS / TEAMS
-- ================================================================

CREATE TABLE IF NOT EXISTS clubs (
    club_id     INTEGER PRIMARY KEY,
    club_name   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS teams (
    team_id     INTEGER PRIMARY KEY,
    team_name   TEXT NOT NULL,
    club_id     INTEGER REFERENCES clubs (club_id)
);

-- ================================================================
-- PLAYERS
-- ================================================================

CREATE TABLE IF NOT EXISTS players (
    player_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    known_as        TEXT NOT NULL,
    first_name      TEXT,
    last_name       TEXT
);

-- Maps a source system's own player identifier onto a canonical player.
CREATE TABLE IF NOT EXISTS player_source_ids (
    source              TEXT NOT NULL,
    source_player_id    TEXT NOT NULL,
    player_id           INTEGER NOT NULL REFERENCES players (player_id),
    PRIMARY KEY (source, source_player_id)
);

CREATE INDEX IF NOT EXISTS idx_player_source_ids_player
    ON player_source_ids (player_id);

-- ================================================================
-- MATCHES
-- ================================================================

CREATE TABLE IF NOT EXISTS matches (
    match_id                INTEGER PRIMARY KEY AUTOINCREMENT,

    source                  TEXT NOT NULL,      -- 'play_cricket' | 'crichq_pdf' | 'cricketstatz'
    source_match_id         TEXT NOT NULL,

    season                  INTEGER NOT NULL,
    match_date               TEXT,
    match_time                TEXT,

    competition_id             INTEGER,
    competition_name           TEXT,
    competition_type           TEXT,
    league_id                    INTEGER,
    league_name                   TEXT,

    home_team_id                    INTEGER REFERENCES teams (team_id),
    away_team_id                     INTEGER REFERENCES teams (team_id),

    ground_id                         INTEGER,
    ground_name                        TEXT,

    no_of_innings                       INTEGER,
    no_of_overs                          INTEGER,
    no_of_days                            INTEGER,

    toss                                   TEXT,
    toss_won_by_team_id                     INTEGER REFERENCES teams (team_id),

    result                                    TEXT,
    result_applied_to                          INTEGER REFERENCES teams (team_id),
    result_description                          TEXT,

    status                                        TEXT,

    source_last_updated                             TEXT,   -- source's own change-tracking timestamp
    source_payload                                    TEXT,  -- raw match-detail JSON for this source

    UNIQUE (source, source_match_id)
);

CREATE INDEX IF NOT EXISTS idx_matches_season ON matches (season);
CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches (home_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches (away_team_id);

-- ================================================================
-- INNINGS
-- ================================================================

CREATE TABLE IF NOT EXISTS innings (
    innings_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id              INTEGER NOT NULL REFERENCES matches (match_id) ON DELETE CASCADE,
    innings_number          INTEGER NOT NULL,

    team_batting_id            INTEGER REFERENCES teams (team_id),

    runs                          INTEGER,
    wickets                        INTEGER,
    overs                            TEXT,
    balls                             INTEGER,
    declared                           INTEGER,   -- 0/1
    forfeited_innings                    INTEGER,   -- 0/1

    extra_byes                             INTEGER,
    extra_leg_byes                           INTEGER,
    extra_wides                               INTEGER,
    extra_no_balls                             INTEGER,
    extra_penalty_runs                          INTEGER,
    total_extras                                 INTEGER,

    UNIQUE (match_id, innings_number)
);

CREATE INDEX IF NOT EXISTS idx_innings_match ON innings (match_id);

-- ================================================================
-- BATTING
-- ================================================================

CREATE TABLE IF NOT EXISTS batting_innings (
    batting_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    innings_id           INTEGER NOT NULL REFERENCES innings (innings_id) ON DELETE CASCADE,

    player_id               INTEGER REFERENCES players (player_id),
    team_id                    INTEGER REFERENCES teams (team_id),

    position                     INTEGER,
    runs                           INTEGER,
    balls                           INTEGER,
    fours                             INTEGER,
    sixes                              INTEGER,

    how_out                             TEXT,
    not_out                               INTEGER,   -- 0/1

    bowler_player_id                        INTEGER REFERENCES players (player_id),
    fielder_player_id                        INTEGER REFERENCES players (player_id)
);

CREATE INDEX IF NOT EXISTS idx_batting_innings_innings ON batting_innings (innings_id);
CREATE INDEX IF NOT EXISTS idx_batting_innings_player ON batting_innings (player_id);

-- ================================================================
-- BOWLING
-- ================================================================

CREATE TABLE IF NOT EXISTS bowling_innings (
    bowling_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    innings_id           INTEGER NOT NULL REFERENCES innings (innings_id) ON DELETE CASCADE,

    player_id               INTEGER REFERENCES players (player_id),
    team_id                    INTEGER REFERENCES teams (team_id),

    overs                        TEXT,
    balls                          INTEGER,
    maidens                          INTEGER,
    runs                               INTEGER,
    wickets                             INTEGER,
    wides                                 INTEGER,
    no_balls                               INTEGER
);

CREATE INDEX IF NOT EXISTS idx_bowling_innings_innings ON bowling_innings (innings_id);
CREATE INDEX IF NOT EXISTS idx_bowling_innings_player ON bowling_innings (player_id);

-- ================================================================
-- MATCH APPEARANCES (team sheet)
-- ================================================================
--
-- One row per player named on a team sheet for a match, independent
-- of whether they went on to bat or bowl. This is the source of truth
-- for "games played" and captures information (captain, wicket-keeper)
-- that batting/bowling rows alone cannot: a player who only fielded
-- has a match_appearances row but no batting_innings/bowling_innings
-- row at all.

CREATE TABLE IF NOT EXISTS match_appearances (
    appearance_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id             INTEGER NOT NULL REFERENCES matches (match_id) ON DELETE CASCADE,

    player_id               INTEGER REFERENCES players (player_id),
    team_id                    INTEGER REFERENCES teams (team_id),

    position                     INTEGER,
    captain                        INTEGER,   -- 0/1
    wicket_keeper                    INTEGER, -- 0/1

    UNIQUE (match_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_match_appearances_match ON match_appearances (match_id);
CREATE INDEX IF NOT EXISTS idx_match_appearances_player ON match_appearances (player_id);

-- ================================================================
-- ACHIEVEMENTS (milestone views)
-- ================================================================
--
-- Declarative, always-in-sync-with-the-data replacement for
-- Scorecard.get_performances(): rather than compute milestone flags
-- once at parse time and store them, these are derived on read from
-- the batting/bowling rows already in the database.

CREATE VIEW IF NOT EXISTS v_batting_achievements AS
SELECT
    b.batting_id,
    b.innings_id,
    b.player_id,
    i.match_id,
    b.runs,
    CASE
        WHEN b.runs >= 200 THEN 'double_century'
        WHEN b.runs >= 100 THEN 'century'
        WHEN b.runs >= 50  THEN 'half_century'
    END AS achievement
FROM batting_innings b
JOIN innings i ON i.innings_id = b.innings_id
WHERE b.runs >= 50;

CREATE VIEW IF NOT EXISTS v_bowling_achievements AS
SELECT
    bo.bowling_id,
    bo.innings_id,
    bo.player_id,
    i.match_id,
    bo.wickets,
    'five_wicket_haul' AS achievement
FROM bowling_innings bo
JOIN innings i ON i.innings_id = bo.innings_id
WHERE bo.wickets >= 5;

-- ================================================================
-- SYNC / BUILD BOOKKEEPING
-- ================================================================

CREATE TABLE IF NOT EXISTS build_log (
    build_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    built_at       TEXT NOT NULL,
    source         TEXT NOT NULL,
    matches_built  INTEGER NOT NULL
);
