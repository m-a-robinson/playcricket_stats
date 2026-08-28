"""
Ingest hand-scored scorebook pages -- photographed/scanned club scorebook
sheets, transcribed directly (read by eye/vision, not OCR) into match-detail
dicts in the same shape cricketstatz_txt.py/crichq_pdf.py produce.

This is a distinct, sixth source ("scorebook") from the other five: unlike
nmcl_stats.py's scanned sheets (season aggregates only), a scorebook page is
match-level -- it carries real per-innings batting/bowling/dismissal detail,
just like a full scorecard, except transcribed by a human reading a photo of
a physical scorebook rather than parsed from typed text.

Because there is no machine-readable source text to parse, MATCHES below is
a hardcoded, manually-verified list of match-detail dicts -- the same
"manually verified, hardcoded data structure" pattern nmcl_stats.py uses for
its own scanned-sheet rows, extended to full match detail here. Each entry
should note which image(s) it was transcribed from and any reading
decisions worth recording.

============================================================================
11-Jul-2010: East Lancs Paper Mill CC 1st XI away to Failsworth Macedonia CC
============================================================================

Source images: scorebooks/2010-07-11 Failsworth Macedonia Away - FM Innings.jpg
               (FM's innings, batting/bowling/extras/FOW)
               scorebooks/2020-07-11 Failsworth Macedonia Away - ELPM innings.jpg
               (filename has a "2020" vs "2010" typo -- content confirms
               11.7.10; ELPM's innings, with the match header: venue
               "Failsworth M", date "11.7.10", League match no. 13, toss
               won by ELPMCC)

Both innings' printed totals were cross-checked against their own component
figures before transcription (the same self-consistency check used
throughout this project rather than trusting a single uncertain read):

  - ELPM 1st XI: 0+9+170+163+2+0+0+0 = 344 runs off the bat + 40 extras
    (byes 10, leg byes 6, wides 24) = 384, matching the printed grand
    total "384" and declared score "6 dec wkts in 39.3 overs". FM's
    bowling figures (Phelan 15-2-103-3, Shenton 7-0-57-1, Bellfield
    2-0-21-0, Rigney 5-0-54-0, Chambers 5-0-65-0, Cassidy 3-0-42-0,
    Redgrave 2.3-0-26-2) sum to 39.3 overs, 6 wickets, 368 runs conceded
    (+16 in byes/leg byes not charged to any bowler = 384) -- the
    scorebook's own bowling-total note in the margin agrees ("368 +16
    384").
  - Failsworth Macedonia: 24+51+0+24+2+11+4+10+0+0+0 = 126 runs off the
    bat + 22 extras (byes 9, leg byes 1, wides 12) = 148, matching the
    printed grand total "148" all out in 29.1 overs. ELPM's bowling
    figures (Hewart 5-1-33-0, Willett 9-1-33-1, Keyworth 10-3-46-4,
    Shiels 5.1-0-26-3) sum to 29.1 overs and 8 wickets; the FOW table
    records a 9th genuine dismissal (J Cassidy run out, fielder credited
    "(Holt)" in the margin) and an explicit "absent" against S Scott (the
    11th man, who never batted) -- the scorebook's own printed "FOR 10
    WKTS" is the nominal all-out count used when a team finishes one man
    short, not 10 genuine dismissals (8 bowler-credited + 1 run out = 9
    real wickets; Higginson not out; Scott absent).

Confirms the 339-run 3rd-wicket-partnership figure the user recalled
(G Greaves 170, I Wade 163) -- this scorecard did not previously exist
anywhere else in the archive; the only other 2010 Failsworth Macedonia file
(cricketstatz/2010 scorecards/ELPM l v FM  1.5.10.txt) is a different,
earlier fixture (Wade 78, Greaves 18).

Balls-faced figures on both pages are recorded as small handwritten
milestone/over annotations that could not be read with confidence, so are
left out (balls=None throughout) rather than guessed -- runs, dismissals
and boundary counts (where legible) are what matter for career stats and
are the figures that were cross-checked above.
"""

SOURCE = "scorebook"


def _bat(position, name, how_out=None, bowler=None, fielder=None,
         runs=None, fours=None, sixes=None):

    return {
        "position": position,
        "batsman_name": name, "batsman_id": name,
        "how_out": how_out,
        "bowler_name": bowler, "bowler_id": bowler,
        "fielder_name": fielder, "fielder_id": fielder,
        "runs": runs, "balls": None,
        "fours": fours, "sixes": sixes,
    }


def _bowl(name, overs, maidens, runs, wickets, wides=0, no_balls=0):

    return {
        "bowler_name": name, "bowler_id": name,
        "overs": overs, "maidens": maidens, "runs": runs, "wickets": wickets,
        "wides": wides, "no_balls": no_balls,
    }


def _player(name, position, captain=False, wicket_keeper=False):

    return {
        "player_name": name, "player_id": name,
        "position": position, "captain": captain, "wicket_keeper": wicket_keeper,
    }


MATCHES = [
    {
        "id": "FM 1st XI|ELPM 1st XI|11/07/2010",
        "home_club_id": "FM", "home_club_name": "Failsworth Macedonia CC",
        "home_team_id": "FM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "ELPM", "away_club_name": "East Lancs Paper Mill CC",
        "away_team_id": "ELPM 1st XI", "away_team_name": "1st XI",
        "match_date": "11/07/2010",
        "match_time": None,
        "competition_id": None,
        "competition_name": "League",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "Failsworth M",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": "ELPMCC",
        "toss_won_by_team_id": "ELPM 1st XI",
        "result": "Won by 236 runs",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 236 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("A Shenton", 1), _player("L Maddocks", 2), _player("J Cassidy", 3),
                _player("M Chambers", 4, captain=True), _player("R Bellfield", 5),
                _player("L Phelan", 6), _player("D Rigney", 7),
                _player("D Marriott", 8, wicket_keeper=True), _player("S Redgrave", 9),
                _player("P Higginson", 10), _player("S Scott", 11),
            ]},
            {"away_team": [
                _player("A McCheyne", 1), _player("J Shiels", 2), _player("G Greaves", 3),
                _player("I Wade", 4, captain=True), _player("G Wade", 5),
                _player("M Hay", 6, wicket_keeper=True), _player("C Holt", 7),
                _player("S Keyworth", 8), _player("D Willett", 9),
                _player("P Hewart", 10), _player("L Withington", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 384, "wickets": 6, "overs": "39.3",
                "declared": 1, "forfeited_innings": 0,
                "extra_byes": 10, "extra_leg_byes": 6, "extra_wides": 24, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 40,
                "bat": [
                    _bat(1, "A McCheyne", "ct", "Shenton", "Marriott", 0),
                    _bat(2, "J Shiels", "lbw", "Phelan", None, 9),
                    _bat(3, "G Greaves", "ct", "Phelan", "Cassidy", 170),
                    _bat(4, "I Wade", "b", "Phelan", None, 163),
                    _bat(5, "G Wade", "b", "Redgrave", None, 2),
                    _bat(6, "M Hay", "not out", None, None, 0),
                    _bat(7, "C Holt", "b", "Redgrave", None, 0),
                    _bat(8, "S Keyworth", "not out", None, None, 0),
                    _bat(9, "D Willett", "did not bat"),
                    _bat(10, "P Hewart", "did not bat"),
                    _bat(11, "L Withington", "did not bat"),
                ],
                "bowl": [
                    _bowl("L Phelan", "15", 2, 103, 3),
                    _bowl("A Shenton", "7", 0, 57, 1),
                    _bowl("R Bellfield", "2", 0, 21, 0),
                    _bowl("D Rigney", "5", 0, 54, 0),
                    _bowl("M Chambers", "5", 0, 65, 0),
                    _bowl("J Cassidy", "3", 0, 42, 0),
                    _bowl("S Redgrave", "2.3", 0, 26, 2),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "FM 1st XI", "team_batting_name": "1st XI",
                "runs": 148, "wickets": 10, "overs": "29.1",
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 9, "extra_leg_byes": 1, "extra_wides": 12, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 22,
                "bat": [
                    _bat(1, "A Shenton", "ct", "Willett", "Hay", 24, fours=5),
                    _bat(2, "L Maddocks", "ct", "Shiels", "Hewart", 51, fours=8, sixes=1),
                    _bat(3, "J Cassidy", "run out", None, "Holt", 0),
                    _bat(4, "M Chambers", "ct", "Keyworth", "Holt", 24, fours=3),
                    _bat(5, "R Bellfield", "b", "Keyworth", None, 2, fours=2),
                    _bat(6, "L Phelan", "ct", "Shiels", "Shiels", 11, fours=1),
                    _bat(7, "D Rigney", "ct", "Shiels", "Hay", 4, fours=1),
                    _bat(8, "D Marriott", "ct", "Keyworth", "Shiels", 10, fours=1, sixes=1),
                    _bat(9, "S Redgrave", "ct", "Keyworth", "Wade (G)", 0),
                    _bat(10, "P Higginson", "not out", None, None, 0),
                    _bat(11, "S Scott", "absent"),
                ],
                "bowl": [
                    _bowl("P Hewart", "5", 1, 33, 0, wides=1),
                    _bowl("D Willett", "9", 1, 33, 1),
                    _bowl("S Keyworth", "10", 3, 46, 4),
                    _bowl("J Shiels", "5.1", 0, 26, 3),
                ],
                "fow": [],
            },
        ],
    },
]


def parse_scorebooks():
    """Return the transcribed match-detail dict list. See MATCHES' docstring above."""

    return MATCHES


def ingest_scorebooks(store, matches=None):
    """
    Insert each transcribed match via store.insert_match(), the same
    idempotent (source, source_match_id) path every other source uses --
    re-running against a store that already has these matches is a no-op.
    """

    if matches is None:
        matches = parse_scorebooks()

    inserted = 0

    for match in matches:

        season = int(match["match_date"][-4:]) if match.get("match_date") else None
        match_id = store.insert_match(match, source=SOURCE, season=season)

        if match_id is not None:
            inserted += 1

    return inserted


if __name__ == "__main__":

    import argparse

    from sqlite_store import SQLiteStore

    parser = argparse.ArgumentParser(
        description="Ingest transcribed hand-scored scorebook pages (scorebooks/) into the SQLite store."
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")

    args = parser.parse_args()

    store = SQLiteStore(args.sqlite_db)

    matches = parse_scorebooks()
    count = ingest_scorebooks(store, matches)

    store.conn.commit()
    store.close()

    print(f"Ingested {count} scorebook match(es).")
