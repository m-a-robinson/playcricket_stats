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

competition_name is "NMCL Division 1", not the scorebook's own literal
"LEAGUE" label (which names the match TYPE, not which division) -- every
other 2010 1st XI fixture in the archive (cricketstatz_txt) is Division 1,
and NMCL only had one senior division the 1st XI played in that year, so
this is the same evidence-based inference used throughout this project,
not a guess. (Originally shipped as the literal "League" -- corrected
2026-08-28 after the user spotted it reading as a second, phantom
competition when auditing the season-by-season match export; the "NMCL "
prefix followed the same day, matching mxp_parser.py/cricketstatz_txt.py's
own <=2015 "Division N" -> "NMCL Division N" normalisation.)

============================================================================
12-Aug-2007: East Lancs Paper Mill CC 2nd XI vs Bury CC
============================================================================

Source image: scorebooks/2nd XI/2007/2026-08-30 09.47.36.jpg (both innings,
full ECB-style scorebook double-page: East Lancs PM batting/bowling on the
left page, Bury CC's on the right).

The page never states which Bury CC XI this was (no "1st"/"2nd" suffix
anywhere in the header), and East Lancs' own team is likewise unlabelled --
filed here as "2nd XI" purely on the strength of the folder the photo was
uploaded into, not anything printed on the page itself. away_team_name
"1st XI" is a placeholder for the same reason: Bury's specific team is
genuinely unrecorded, so this may need correcting once/if Bury CC's own
teams show up distinctly elsewhere in the archive. competition_name is
left None -- the scorebook gives no league/division, and unlike the 2010
Failsworth Macedonia match above there's no same-season sibling fixture in
the archive to infer one from.

Two batsmen's identities are only partially legible: East Lancs' #9 (out
lbw b A Maxwell for 1) is a second "Birtwistle" -- distinct from #8, A
Birtwistle, who batted two places above him and also bowled in Bury's
innings -- but the initial itself is obscured by the row's own printed
number in the only surviving photo, at a level of blur that survives
re-cropping/zooming, so it is left off (batsman_id/name "Birtwistle"
alone) rather than guessed. East Lancs' #11 (not out 16) is very likely
"G Moore" -- R Moore, the only other Moore who batted, was out at #3, and
"G Moore" is the only other Moore in the bowling figures below -- but the
initial itself has the same illegible-photo problem as #9, so this is
recorded with the same caveat (moderate confidence from elimination,
not a direct read).

Both innings' printed totals were cross-checked against their own
component figures before transcription, the same self-consistency check
used throughout this project:

  - East Lancs PM: 50 (retired, C Holt) + 18+0+0+30+12+2+7+1+0+16 (the 10
    completed/not-out innings) = 136 runs off the bat + 9 extras (byes 1,
    leg byes 4, wides 2, no balls 2) = 145 for 8 wickets off their 40
    overs (2 not out at the end, so 8 genuine dismissals, matching the
    fall-of-wicket table's 8 entries -- C Holt's retirement isn't a fall
    of wicket). Bury's bowling figures (Hilton 5-1-19-1, Forman 5-0-20-1,
    Jarvis 5-2-6-1, Maxwell 5-0-21-1, Mulvany 5-1-9-1, Belston 5-1-22-0,
    Allen 5-0-24-1, Ainscoe 5-1-19-1) sum to 40 overs, 140 runs conceded
    (136 batsmen's runs + the 2 no balls + 2 wides that ARE charged to a
    bowler, byes/leg byes aren't) and 7 wickets -- R Moore's run-out
    accounts for the 8th, uncredited to any bowler, so 7+1=8 reconciles.
  - Bury CC: 1+0+66+2+22+16+11+6+0+5+4 = 133 runs off the bat + 16 extras
    (byes 2, leg byes 0, wides 13, no balls 1) = 149 for 9 wickets (A
    Hilton and A Mather both finished not out). East Lancs' bowling
    figures sum to 8 wickets (Simpson 1, Scott 2, Santos-P 1, Birtwistle
    2, Partington 3) against the 9 real dismissals shown against each
    batsman's own name -- one short, because the bowling-summary row
    printed for A Birtwistle reads "3-0-25-1" but two separate batsmen
    are recorded "b Birtwistle" (Forman, ct C Holt; T Jarvis, ct M
    Partington), which only reconciles to the full 9 if Birtwistle in
    fact took 2, not 1 -- the scorer's own summary row looks to be a
    simple mis-add, so the two individually-recorded dismissals (the more
    granular, more reliable figures) are what's used here.

East Lancs' 145 was chased down: Bury reached 149 for 9, meaning Bury CC
won by 2 wickets (2 of their 11 unused when the winning runs were scored).

============================================================================
30-Apr-2011: Austerlands CC vs East Lancs Paper Mill CC 2nd XI
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.07.02.jpg (both
innings; a printed club scorebook -- BATSMAN/HOW OUT/BOWLER/TOTAL columns,
a PENALTY RUNS/BYES/LEG BYES/WIDES/NO BALLS extras panel, and an
OVERS/MDNS/RUNS/WKTS/AVG bowling-analysis table per innings -- much more
directly legible than the 2007 ECB book above, so cross-checks below are
correspondingly quicker.

  - Austerlands: 14+0+0+8+17+4+4+8+34+2+0 = 91 (matches the printed
    "TOTALS 91") + 3 extras (byes 1, no balls 2) = 94 all out in 23.4
    overs. Bowling figures (A Redford 8-1-47-5, A Berry 11-5-28-2, M Young
    4-1-15-2, A Greenwood 0.4-0-3-1) sum to 23.4 overs and all 10 wickets.
  - East Lancs PM: 29+0+9+38+5+2 = 83 (K Dodson's 29 itself cross-checked
    against its own ball-by-ball figures: 11+7+10+1 = 29, matching the
    scorebook's own running subtotals at 11/18/28) + 12 extras (byes 6,
    leg byes 5, wides 1) = 95 for 4 wickets, chasing down Austerlands' 94
    with 6 wickets in hand -- ELPM won by 6 wickets. The printed bowling
    total (84) is 1 run over the batting total (83); a minor scorer's-own
    arithmetic slip judging by how cleanly everything else reconciles,
    not corrected here since it doesn't affect any individual figure.

A Berry's dismissal is recorded as "caught N Green" with bowler also "N
Green" -- i.e. caught and bowled, not a transcription duplicate.

============================================================================
01-May-2011: Failsworth CC vs East Lancs Paper Mill CC 2nd XI (Cup)
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.07.11.jpg (both
innings). Same printed club scorebook as the Austerlands match above.

  - Failsworth: 27+16+55+40+0+28+14+13+2+5+0 = 200 (matches "S.TOTAL 200")
    off the bat. The bowling-analysis totals (D Willett 6-0-21-0, A Redford
    8-2-34-2, B Birtwistle 4-0-30-0, M Young 8-0-36-2, D Scott 2-0-13-0, G
    Young 8-0-48-4, S Keyworth 4-0-25-2) sum to the full 40 overs and all
    10 wickets, and the scorer's own margin note "207 +9" (bowling runs
    conceded + byes not charged to any bowler) gives a final total of 216
    -- used here as "runs" in preference to the batsmen-total-plus-extras
    figure (200+15=215) and the fall-of-wicket table's last entry (211),
    both 1-5 runs short of the scorer's own check, the same kind of minor
    arithmetic slip already seen in the two matches above.
  - ELPM: 20+9+8+49+0+0+1+1+0+6+9 = 103 off the bat (bat), all out for 131
    (used here, again the scorer's own final total in the bowling-analysis
    box, in preference to the fall-of-wicket table's "130" and the
    batsmen-plus-extras figure of 132) in 29.4 overs. Bowling figures for
    T Neatis (7-1-12-2) and T Hinckley (8-1-32-4) are direct reads; I
    Wilson's wickets (3, not the 2 visible in one blurrier crop) and J
    Davis's full figures (his row's own OVERS/RUNS/WKTS cells weren't
    legibly captured, only two overs of his ball-by-ball progression) are
    both recovered by solving against the printed innings totals (29.4
    overs, 116 runs, 9 wickets) once every other bowler's figures are
    fixed -- I Wilson 6-1-23-3 and J Davis 6.4-0-36-0 are the unique
    values that make the totals balance.

Failsworth won this Cup tie by 85 runs.

============================================================================
07-May-2011: East Lancs Paper Mill CC 2nd XI vs Farnworth Social CC
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.08.35.jpg (both
innings). Same printed club scorebook as the two matches above.

  - Farnworth SC: 5+28+59+7+0+9+4+13+9+3+0 = 137 (matches "S.TOTAL 137")
    + 8 extras (byes 5, leg byes 1, wides 2) = 145 all out... for 9, not
    10 -- B Honkroft and P Sutton both finished not out, matching the
    fall-of-wicket table's 9 entries. Bowling figures (A Redford 5-1-29-1,
    A Berry 20-1-63-4, L Birmingham 7-0-18-1, M Young 8-1-27-3) sum to the
    full 40 overs, all 9 wickets, and 137 runs -- exactly the batsmen's
    total, no wides/no-balls added in this particular table (unlike the
    Austerlands and Failsworth matches above, where they were).
  - ELPM: 5+0+3+0+0+5+60+6+4+6+10 = 99 (matches "S.TOTAL 99") + 31 extras
    = 130 all out in 35.2 overs. Bowling figures (A Brookes 18-6-28-6, N
    Felton 6-0-22-3, J Chaana 4-0-32-0, T Sherlock 4-0-16-0, D Robinson
    3.2-0-9-1) sum to 35.2 overs, 107 runs and all 10 wickets; the
    bowler credited with M Young's wicket is illegible as printed ("C
    Lane", a name that matches none of the 5 bowlers who have their own
    analysis row) and is recorded here as D Robinson -- the only bowler
    with a wicket still unassigned to a specific dismissal once the other
    four bowlers' figures are matched to their own dismissals. The extras
    breakdown (byes 22, leg byes 1, wides 5, no balls 1 = 29) is 2 short
    of the printed "TOTAL EXTRAS 31"; not corrected, since which of the
    four tallies is the one under-read isn't recoverable from the photo.

Farnworth SC batted first and made 137; ELPM, batting second, fell short
on 130 -- Farnworth SC won by 7 runs.

============================================================================
22-May-2011: Swinton Moorside CC vs East Lancs Paper Mill CC 2nd XI
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.08.55.jpg (both
innings). Same printed club scorebook as the matches above.

  - Swinton: 34+27+0+27+9+10+3+0+5+8+12 = 135 (matches "S.TOTAL 135") + 9
    extras (byes 1, leg byes 1, wides 6, no balls 1) = 144 all out in 35
    overs. Bowling figures (A Berry 7-1-30-0, L Birmingham 7-1-23-0, J
    Bailey 11-3-46-8, D Willett 10-1-43-2) sum to the full 35 overs, all
    10 wickets, and 142 runs (135 + the 6 wides + 1 no ball charged to a
    bowler = 142).
  - ELPM: 4+22+12+16+0+0+8+16+0+0+1 = 79 (matches "S.TOTAL 79") + 21
    extras (byes 5, leg byes 4, wides 11, no balls 1) = 100 all out. The
    innings' own "OVERS IN" box was left blank by the scorer, so overs
    are only known per-bowler (C Winstanley 10-5-37-0, D Atkinson
    7-2-19-5, J Brownvil 7.5-2-17-2, G Higham 5-1-18-3, summing to 29.5)
    -- runs (91 = 79 + the 11 wides + 1 no ball charged to a bowler) and
    all 10 wickets (5+2+3 bowler-credited, matching Atkinson/Brownvil/
    Higham's dismissals exactly) both reconcile cleanly even without a
    printed innings-overs total to check against.

Swinton Moorside won by 44 runs.

============================================================================
28-May-2011: East Lancs Paper Mill CC 2nd XI vs Failsworth CC
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.09.05.jpg (both
innings). Same printed club scorebook as the matches above. A very
low-scoring match on both sides.

  - Failsworth: 6+13+2+6+1+4+1+1+0+0+0 = 34 (matches "S.TOTAL 34") + 11
    extras (leg byes 2, wides 9) = 45 all out. Bowling figures (L
    Birmingham 7-3-11-0, A Berry 10-0-10-4, D Willett 8-1-22-6) sum to
    all 10 wickets and 43 runs, which equals batsmen (34) + extras not
    credited to a bowler by this book's own convention seen in the
    earlier matches (34+9=43) -- consistent. A Berry's maiden-over count
    is the one figure in this line not legibly separable from his
    wides/no-balls total in the photo and is left at 0 rather than
    guessed.
  - ELPM: 11+18+1+0+6+0+1+6+0 = 43 (matches "S.TOTAL 43") + 5 extras
    (byes 1, wides 4) = 48 for 7 wickets in 12.1 overs, chasing down
    Failsworth's 45 -- ELPM won by 3 wickets. A Greenwood's bowler is a
    correction in the original (the first name written is struck
    through) and is transcribed here as the corrected name, B Thinkley,
    which also makes his 2 credited wickets (Greenwood, A Berry) match
    his own bowling-analysis row (6-1-14-2) exactly; B Beasconi (Dwyer)
    and D Rigny (G Young, M Thomson, N Warne, B Birtwhistle) account for
    the other 5. The three bowlers' analysis-row runs (14+30+24=68) do
    not reconcile against the batting total plus extras (48) -- a real
    discrepancy in the source that isn't resolvable from this photo, so
    it's left as read rather than adjusted to fit.
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
        "competition_name": "NMCL Division 1",
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
    {
        "id": "ELPM 2nd XI|Bury CC 1st XI|12/08/2007",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 2nd XI", "home_team_name": "2nd XI",
        "away_club_id": "Bury CC", "away_club_name": "Bury CC",
        "away_team_id": "Bury CC 1st XI", "away_team_name": "1st XI",
        "match_date": "12/08/2007",
        "match_time": None,
        "competition_id": None,
        "competition_name": None,
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "East Lancs P.M.",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Bury CC won by 2 wickets",
        "result_applied_to": "Bury CC 1st XI",
        "result_description": "Bury CC won by 2 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("C Holt", 1), _player("M Partington", 2), _player("R Moore", 3),
                _player("P Santos", 4), _player("L Santos", 5), _player("D Scott", 6),
                _player("I Simpson", 7), _player("A Birtwistle", 8), _player("Birtwistle", 9),
                _player("D Salmon", 10), _player("G Moore", 11),
            ]},
            {"away_team": [
                _player("J Ainscoe", 1), _player("S Younis", 2), _player("A Hilton", 3),
                _player("L Jarvis", 4), _player("G Forman", 5), _player("C Belston", 6),
                _player("A Maxwell", 7), _player("S Mulvaney", 8), _player("J Allen", 9),
                _player("T Jarvis", 10), _player("A Mather", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 145, "wickets": 8, "overs": "40",
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 1, "extra_leg_byes": 4, "extra_wides": 2, "extra_no_balls": 2,
                "extra_penalty_runs": 0, "total_extras": 9,
                "bat": [
                    _bat(1, "C Holt", "retired", None, None, 50),
                    _bat(2, "M Partington", "ct", "Forman", "A Ghaffar", 18),
                    _bat(3, "R Moore", "run out", None, None, 0),
                    _bat(4, "P Santos", "b", "Jarvis", None, 0),
                    _bat(5, "L Santos", "ct", "Mulvany", "Mather", 30),
                    _bat(6, "D Scott", "ct", "Ainscoe", "T Jarvis", 12),
                    _bat(7, "I Simpson", "lbw", "Allen", None, 2),
                    _bat(8, "A Birtwistle", "ct", "Hilton", "S Mulvany", 7),
                    _bat(9, "Birtwistle", "lbw", "A Maxwell", None, 1),
                    _bat(10, "D Salmon", "not out", None, None, 0),
                    _bat(11, "G Moore", "not out", None, None, 16),
                ],
                "bowl": [
                    _bowl("A Hilton", "5", 1, 19, 1),
                    _bowl("Forman", "5", 0, 20, 1),
                    _bowl("L Jarvis", "5", 2, 6, 1),
                    _bowl("A Maxwell", "5", 0, 21, 1),
                    _bowl("S Mulvany", "5", 1, 9, 1),
                    _bowl("G Belston", "5", 1, 22, 0),
                    _bowl("J Allen", "5", 0, 24, 1),
                    _bowl("J Ainscoe", "5", 1, 19, 1),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Bury CC 1st XI", "team_batting_name": "1st XI",
                "runs": 149, "wickets": 9, "overs": "39",
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 2, "extra_leg_byes": 0, "extra_wides": 13, "extra_no_balls": 1,
                "extra_penalty_runs": 0, "total_extras": 16,
                "bat": [
                    _bat(1, "J Ainscoe", "ct", "D Scott", "M Partington", 1),
                    _bat(2, "S Younis", "ct", "I Simpson", "M Partington", 0),
                    _bat(3, "A Hilton", "not out", None, None, 66),
                    _bat(4, "L Jarvis", "b", "P Santos", None, 2),
                    _bat(5, "G Forman", "ct", "A Birtwistle", "C Holt", 22),
                    _bat(6, "C Belston", "b", "M Partington", None, 16),
                    _bat(7, "A Maxwell", "ct", "M Partington", "I Simpson", 11),
                    _bat(8, "S Mulvaney", "ct", "M Partington", "I Simpson", 6),
                    _bat(9, "J Allen", "ct", "D Scott", "I Simpson", 0),
                    _bat(10, "T Jarvis", "ct", "A Birtwistle", "M Partington", 5),
                    _bat(11, "A Mather", "not out", None, None, 4),
                ],
                "bowl": [
                    _bowl("I Simpson", "5", 2, 8, 1),
                    _bowl("D Scott", "5", 1, 12, 2),
                    _bowl("L Santos", "5", 0, 14, 0),
                    _bowl("P Santos", "5", 2, 15, 1),
                    _bowl("R Moore", "3", 0, 21, 0),
                    _bowl("G Moore", "4", 0, 24, 0),
                    # Printed bowling-summary row reads 3-0-25-1; corrected to
                    # 2 wickets here per the two individual "b Birtwistle"
                    # dismissals -- see the module docstring above.
                    _bowl("A Birtwistle", "3", 0, 25, 2),
                    _bowl("M Partington", "6", 2, 14, 3),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "Austerlands CC 1st XI|ELPM 2nd XI|30/04/2011",
        "home_club_id": "Austerlands", "home_club_name": "Austerlands CC",
        "home_team_id": "Austerlands CC 1st XI", "home_team_name": "1st XI",
        "away_club_id": "ELPM", "away_club_name": "East Lancs Paper Mill CC",
        "away_team_id": "ELPM 2nd XI", "away_team_name": "2nd XI",
        "match_date": "30/04/2011",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL",
        "competition_type": "League",
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "Austerlands",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": "Austerlands",
        "toss_won_by_team_id": "Austerlands CC 1st XI",
        "result": "East Lancs Paper Mill CC won by 6 wickets",
        "result_applied_to": "ELPM 2nd XI",
        "result_description": "East Lancs Paper Mill CC 2nd XI won by 6 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("A Platt", 1), _player("H Ripley", 2), _player("J Molloy", 3),
                _player("L De Feu", 4), _player("K McDonald", 5), _player("P Mayall", 6),
                _player("S Forshaw", 7), _player("J Kenworthy", 8), _player("G Monoghan", 9),
                _player("N Green", 10), _player("P Palfreyman", 11),
            ]},
            {"away_team": [
                _player("K Dodson", 1, wicket_keeper=True), _player("C Holt", 2), _player("D Dwyer", 3),
                _player("A Berry", 4), _player("A Greenwood", 5), _player("A Redford", 6),
                _player("L Birmingham", 7), _player("W Franus", 8), _player("B Birtwistle", 9),
                _player("M Young", 10), _player("A Birtwistle", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Austerlands CC 1st XI", "team_batting_name": "1st XI",
                "runs": 94, "wickets": 10, "overs": "23.4",
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 1, "extra_leg_byes": 0, "extra_wides": 0, "extra_no_balls": 2,
                "extra_penalty_runs": 0, "total_extras": 3,
                "bat": [
                    _bat(1, "A Platt", "b", "A Berry", None, 14),
                    _bat(2, "H Ripley", "lbw", "A Redford", None, 0),
                    _bat(3, "J Molloy", "ct", "A Redford", "A Birtwistle", 0),
                    _bat(4, "L De Feu", "b", "A Berry", None, 8),
                    _bat(5, "K McDonald", "b", "A Redford", None, 17),
                    _bat(6, "P Mayall", "b", "M Young", None, 4),
                    _bat(7, "S Forshaw", "lbw", "A Redford", None, 4),
                    _bat(8, "J Kenworthy", "b", "A Redford", None, 8),
                    _bat(9, "G Monoghan", "not out", None, None, 34),
                    _bat(10, "N Green", "b", "M Young", None, 2),
                    _bat(11, "P Palfreyman", "ct", "A Greenwood", "K Dodson", 0),
                ],
                "bowl": [
                    _bowl("A Redford", "8", 1, 47, 5, no_balls=2),
                    _bowl("A Berry", "11", 5, 28, 2),
                    _bowl("M Young", "4", 1, 15, 2),
                    _bowl("A Greenwood", "0.4", 0, 3, 1),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 95, "wickets": 4, "overs": "29.3",
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 6, "extra_leg_byes": 5, "extra_wides": 1, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 12,
                "bat": [
                    _bat(1, "K Dodson", "b", "K McDonald", None, 29),
                    _bat(2, "C Holt", "lbw", "P Palfreyman", None, 0),
                    _bat(3, "D Dwyer", "b", "P Palfreyman", None, 9),
                    _bat(4, "A Berry", "ct and b", "N Green", None, 38),
                    _bat(5, "A Greenwood", "not out", None, None, 5),
                    _bat(6, "A Redford", "not out", None, None, 2),
                    _bat(7, "L Birmingham", "did not bat"),
                    _bat(8, "W Franus", "did not bat"),
                    _bat(9, "B Birtwistle", "did not bat"),
                    _bat(10, "M Young", "did not bat"),
                    _bat(11, "A Birtwistle", "did not bat"),
                ],
                "bowl": [
                    _bowl("J Kenworthy", "8", 1, 31, 0),
                    _bowl("P Palfreyman", "9", 3, 17, 2),
                    _bowl("P Mayall", "3", 0, 15, 0),
                    _bowl("K McDonald", "4", 3, 2, 1),
                    _bowl("N Green", "4", 1, 15, 1),
                    _bowl("G Monoghan", "0.4", 0, 4, 0),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "Failsworth CC 1st XI|ELPM 2nd XI|01/05/2011",
        "home_club_id": "Failsworth", "home_club_name": "Failsworth CC",
        "home_team_id": "Failsworth CC 1st XI", "home_team_name": "1st XI",
        "away_club_id": "ELPM", "away_club_name": "East Lancs Paper Mill CC",
        "away_team_id": "ELPM 2nd XI", "away_team_name": "2nd XI",
        "match_date": "01/05/2011",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Cup",
        "competition_type": "Cup",
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "Failsworth",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": "Failsworth",
        "toss_won_by_team_id": "Failsworth CC 1st XI",
        "result": "Failsworth CC won by 85 runs",
        "result_applied_to": "Failsworth CC 1st XI",
        "result_description": "Failsworth CC won by 85 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("J Davies", 1), _player("D Marriott", 2), _player("J Turnbull", 3),
                _player("T Neatis", 4), _player("L Johnson", 5), _player("R Lindon", 6),
                _player("N Reed", 7), _player("I Wilson", 8), _player("T Hinckley", 9),
                _player("A Trotter", 10), _player("B Birtwistle", 11),
            ]},
            {"away_team": [
                _player("D Dwyer", 1), _player("D Scott", 2), _player("K Dodson", 3, wicket_keeper=True),
                _player("G Young", 4), _player("S Keyworth", 5), _player("D Willett", 6),
                _player("D Haocroft", 7), _player("A Redford", 8), _player("B Birtwistle", 9),
                _player("A Birtwistle", 10), _player("M Young", 11, captain=True),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Failsworth CC 1st XI", "team_batting_name": "1st XI",
                "runs": 216, "wickets": 10, "overs": "40",
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 9, "extra_leg_byes": 0, "extra_wides": 6, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 15,
                "bat": [
                    _bat(1, "J Davies", "b", "A Redford", None, 27),
                    _bat(2, "D Marriott", "b", "A Redford", None, 16),
                    _bat(3, "J Turnbull", "st", "M Young", "K Dodson", 55),
                    _bat(4, "T Neatis", "ct", "G Young", "M Young", 40),
                    _bat(5, "L Johnson", "b", "M Young", None, 0),
                    _bat(6, "R Lindon", "b", "G Young", None, 28),
                    _bat(7, "N Reed", "b", "G Young", None, 14),
                    _bat(8, "I Wilson", "b", "G Young", None, 13),
                    _bat(9, "T Hinckley", "not out", None, None, 2),
                    _bat(10, "A Trotter", "lbw", "S Keyworth", None, 5),
                    _bat(11, "B Birtwistle", "b", "S Keyworth", None, 0),
                ],
                "bowl": [
                    _bowl("D Willett", "6", 0, 21, 0),
                    _bowl("A Redford", "8", 2, 34, 2),
                    _bowl("B Birtwistle", "4", 0, 30, 0),
                    _bowl("M Young", "8", 0, 36, 2),
                    _bowl("D Scott", "2", 0, 13, 0),
                    _bowl("G Young", "8", 0, 48, 4),
                    _bowl("S Keyworth", "4", 0, 25, 2),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 131, "wickets": 10, "overs": "29.4",
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 7, "extra_leg_byes": 8, "extra_wides": 14, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 29,
                "bat": [
                    _bat(1, "D Dwyer", "b", "B Bernscough", None, 20),
                    _bat(2, "D Scott", "ct", "T Neatis", "D Marriott", 9),
                    _bat(3, "K Dodson", "ct", "T Hinckley", None, 8),
                    _bat(4, "G Young", "b", "T Hinckley", None, 49),
                    _bat(5, "S Keyworth", "b", "B Bernscough", None, 0),
                    _bat(6, "D Willett", "b", "I Wilson", None, 0),
                    _bat(7, "D Haocroft", "b", "I Wilson", None, 1),
                    _bat(8, "A Redford", "run out", None, "B Bernscough", 1),
                    _bat(9, "B Birtwistle", "b", "I Wilson", None, 0),
                    _bat(10, "A Birtwistle", "ct", "I Wilson", "T Neatis", 6),
                    _bat(11, "M Young", "not out", None, None, 9),
                ],
                "bowl": [
                    _bowl("T Neatis", "7", 1, 12, 2),
                    _bowl("T Hinckley", "8", 1, 32, 4),
                    _bowl("I Wilson", "6", 1, 23, 3),
                    _bowl("B Bernscough", "2", 0, 13, 0),
                    # Back-solved from the innings totals (29.4 overs, 116
                    # runs, 9 wkts) -- his own row's summary cells weren't
                    # legibly captured; see the module docstring above.
                    _bowl("J Davis", "6.4", 0, 36, 0),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 2nd XI|Farnworth Social CC 1st XI|07/05/2011",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 2nd XI", "home_team_name": "2nd XI",
        "away_club_id": "Farnworth Social", "away_club_name": "Farnworth Social CC",
        "away_team_id": "Farnworth Social CC 1st XI", "away_team_name": "1st XI",
        "match_date": "07/05/2011",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL",
        "competition_type": "League",
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": "ELPM",
        "toss_won_by_team_id": "ELPM 2nd XI",
        "result": "Farnworth Social CC won by 7 runs",
        "result_applied_to": "Farnworth Social CC 1st XI",
        "result_description": "Farnworth Social CC won by 7 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"away_team": [
                _player("T Sherlock", 1), _player("D Robinson", 2), _player("G Hipwood", 3),
                _player("S Bradley", 4), _player("A Brookes", 5), _player("N Felton", 6),
                _player("T Kilgour", 7), _player("M Crowders", 8), _player("J Chaana", 9),
                _player("B Honkroft", 10, wicket_keeper=True), _player("P Sutton", 11),
            ]},
            {"home_team": [
                _player("K Dodson", 1, wicket_keeper=True), _player("C Holt", 2), _player("G Young", 3),
                _player("A Berry", 4), _player("A Greenwood", 5), _player("D Dwyer", 6),
                _player("M Young", 7, captain=True), _player("W Francis", 8), _player("D Haocroft", 9),
                _player("L Birmingham", 10), _player("A Redford", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Farnworth Social CC 1st XI", "team_batting_name": "1st XI",
                "runs": 145, "wickets": 9, "overs": "40",
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 5, "extra_leg_byes": 1, "extra_wides": 2, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 8,
                "bat": [
                    _bat(1, "T Sherlock", "b", "A Redford", None, 5),
                    _bat(2, "D Robinson", "ct", "M Young", "L Birmingham", 28),
                    _bat(3, "G Hipwood", "ct", "L Birmingham", "K Dodson", 59),
                    _bat(4, "S Bradley", "ct", "A Berry", "L Birmingham", 7),
                    _bat(5, "A Brookes", "st", "M Young", "K Dodson", 0),
                    _bat(6, "N Felton", "ct", "A Berry", "K Dodson", 9),
                    _bat(7, "T Kilgour", "ct", "M Young", "M Young", 4),
                    _bat(8, "M Crowders", "b", "A Berry", None, 13),
                    _bat(9, "J Chaana", "ct", "A Berry", None, 9),
                    _bat(10, "B Honkroft", "not out", None, None, 3),
                    _bat(11, "P Sutton", "not out", None, None, 0),
                ],
                "bowl": [
                    _bowl("A Redford", "5", 1, 29, 1),
                    _bowl("A Berry", "20", 1, 63, 4),
                    _bowl("L Birmingham", "7", 0, 18, 1),
                    _bowl("M Young", "8", 1, 27, 3),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 130, "wickets": 10, "overs": "35.2",
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 22, "extra_leg_byes": 1, "extra_wides": 5, "extra_no_balls": 1,
                "extra_penalty_runs": 0, "total_extras": 31,
                "bat": [
                    _bat(1, "K Dodson", "ct and b", "A Brookes", None, 5),
                    _bat(2, "C Holt", "ct", "A Brookes", None, 0),
                    _bat(3, "G Young", "ct", "N Felton", "D Robinson", 3),
                    _bat(4, "A Berry", "ct", "N Felton", "S Bradley", 0),
                    _bat(5, "A Greenwood", "b", "A Brookes", None, 0),
                    _bat(6, "D Dwyer", "b", "N Felton", None, 5),
                    # Bowler credited in the scorebook is illegible as
                    # printed -- reassigned to D Robinson, the only
                    # bowler with a wicket left unmatched; see the module
                    # docstring above.
                    _bat(7, "M Young", "b", "D Robinson", None, 60),
                    _bat(8, "W Francis", "b", "A Brookes", None, 6),
                    _bat(9, "D Haocroft", "ct", "A Brookes", "B Honkroft", 4),
                    _bat(10, "L Birmingham", "ct", "A Brookes", "B Honkroft", 6),
                    _bat(11, "A Redford", "not out", None, None, 10),
                ],
                "bowl": [
                    _bowl("A Brookes", "18", 6, 28, 6),
                    _bowl("N Felton", "6", 0, 22, 3),
                    _bowl("J Chaana", "4", 0, 32, 0),
                    _bowl("T Sherlock", "4", 0, 16, 0),
                    _bowl("D Robinson", "3.2", 0, 9, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "Swinton Moorside CC 1st XI|ELPM 2nd XI|22/05/2011",
        "home_club_id": "Swinton Moorside", "home_club_name": "Swinton Moorside CC",
        "home_team_id": "Swinton Moorside CC 1st XI", "home_team_name": "1st XI",
        "away_club_id": "ELPM", "away_club_name": "East Lancs Paper Mill CC",
        "away_team_id": "ELPM 2nd XI", "away_team_name": "2nd XI",
        "match_date": "22/05/2011",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL",
        "competition_type": "League",
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "Swinton",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": "Swinton",
        "toss_won_by_team_id": "Swinton Moorside CC 1st XI",
        "result": "Swinton Moorside CC won by 44 runs",
        "result_applied_to": "Swinton Moorside CC 1st XI",
        "result_description": "Swinton Moorside CC won by 44 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("L Harding", 1), _player("G Higham", 2), _player("P Flatley", 3),
                _player("C Jerrard", 4), _player("T Staniford", 5), _player("J Brownvil", 6),
                _player("D Davies", 7), _player("A Walker", 8), _player("J Saunders", 9),
                _player("D Atkinson", 10), _player("C Winstanley", 11),
            ]},
            {"away_team": [
                _player("J Bailey", 1), _player("A Berry", 2), _player("A Greenwood", 3),
                _player("D Willett", 4), _player("D Haidcroft", 5), _player("A Wilkinson", 6),
                _player("L Birmingham", 7), _player("A Redford", 8), _player("D Pearson", 9),
                _player("B Birtwistle", 10), _player("A Birtwistle", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Swinton Moorside CC 1st XI", "team_batting_name": "1st XI",
                "runs": 144, "wickets": 10, "overs": "35",
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 1, "extra_leg_byes": 1, "extra_wides": 6, "extra_no_balls": 1,
                "extra_penalty_runs": 0, "total_extras": 9,
                "bat": [
                    _bat(1, "L Harding", "b", "J Bailey", None, 34),
                    _bat(2, "G Higham", "ct and b", "J Bailey", None, 27),
                    _bat(3, "P Flatley", "b", "J Bailey", None, 0),
                    _bat(4, "C Jerrard", "b", "J Bailey", None, 27),
                    _bat(5, "T Staniford", "lbw", "J Bailey", None, 9),
                    _bat(6, "J Brownvil", "ct", "D Willett", "A Berry", 10),
                    _bat(7, "D Davies", "b", "J Bailey", None, 3),
                    _bat(8, "A Walker", "ct", "J Bailey", "A Pilkington", 0),
                    _bat(9, "J Saunders", "b", "D Willett", None, 5),
                    _bat(10, "D Atkinson", "lbw", "J Bailey", None, 8),
                    _bat(11, "C Winstanley", "not out", None, None, 12),
                ],
                "bowl": [
                    _bowl("A Berry", "7", 1, 30, 0),
                    _bowl("L Birmingham", "7", 1, 23, 0),
                    _bowl("J Bailey", "11", 3, 46, 8),
                    _bowl("D Willett", "10", 1, 43, 2),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 100, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 5, "extra_leg_byes": 4, "extra_wides": 11, "extra_no_balls": 1,
                "extra_penalty_runs": 0, "total_extras": 21,
                "bat": [
                    _bat(1, "J Bailey", "b", "D Atkinson", None, 4),
                    _bat(2, "A Berry", "b", "D Atkinson", None, 22),
                    _bat(3, "A Greenwood", "ct", "D Atkinson", "L Harding", 12),
                    _bat(4, "D Willett", "lbw", "G Higham", None, 16),
                    _bat(5, "D Haidcroft", "b", "D Atkinson", None, 0),
                    _bat(6, "A Wilkinson", "b", "D Atkinson", None, 0),
                    _bat(7, "L Birmingham", "ct", "J Brownvil", "D Atkinson", 8),
                    _bat(8, "A Redford", "not out", None, None, 16),
                    _bat(9, "D Pearson", "b", "G Higham", None, 0),
                    _bat(10, "B Birtwistle", "lbw", "G Higham", None, 0),
                    _bat(11, "A Birtwistle", "b", "J Brownvil", None, 1),
                ],
                "bowl": [
                    _bowl("C Winstanley", "10", 5, 37, 0),
                    _bowl("D Atkinson", "7", 2, 19, 5),
                    _bowl("J Brownvil", "7.5", 2, 17, 2),
                    _bowl("G Higham", "5", 1, 18, 3),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 2nd XI|Failsworth CC 1st XI|28/05/2011",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 2nd XI", "home_team_name": "2nd XI",
        "away_club_id": "Failsworth", "away_club_name": "Failsworth CC",
        "away_team_id": "Failsworth CC 1st XI", "away_team_name": "1st XI",
        "match_date": "28/05/2011",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL",
        "competition_type": "League",
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": "Failsworth",
        "toss_won_by_team_id": "Failsworth CC 1st XI",
        "result": "ELPM 2nd XI won by 3 wickets",
        "result_applied_to": "ELPM 2nd XI",
        "result_description": "East Lancs Paper Mill CC won by 3 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"away_team": [
                _player("J Davies", 1), _player("D Rigny", 2), _player("T Neatis", 3),
                _player("T Hinkley", 4), _player("N Read", 5), _player("R Stacey", 6),
                _player("A Trotter", 7), _player("E McQue", 8), _player("B Beasconi", 9),
                _player("T Shepeshen", 10), _player("K Shenton", 11),
            ]},
            {"home_team": [
                _player("D Dwyer", 1), _player("G Young", 2), _player("A Greenwood", 3),
                _player("A Berry", 4), _player("M Thomson", 5), _player("N Warne", 6),
                _player("B Birtwhistle", 7), _player("D Willett", 8), _player("W Francis", 9),
                _player("L Birmingham", 10), _player("A Redford", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Failsworth CC 1st XI", "team_batting_name": "1st XI",
                "runs": 45, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 2, "extra_wides": 9, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 11,
                "bat": [
                    _bat(1, "J Davies", "ct", "A Berry", "A Redford", 6),
                    _bat(2, "D Rigny", "b", "A Berry", None, 13),
                    _bat(3, "T Neatis", "ct", "D Willett", "B Birtwhistle", 2),
                    _bat(4, "T Hinkley", "b", "D Willett", None, 6),
                    _bat(5, "N Read", "ct", "D Willett", "W Francis", 1),
                    _bat(6, "R Stacey", "b", "D Willett", None, 4),
                    _bat(7, "A Trotter", "ct", "D Willett", "D Dwyer", 1),
                    _bat(8, "E McQue", "ct", "D Willett", "N Warne", 1),
                    _bat(9, "B Beasconi", "ct", "A Berry", "M Thomson", 0),
                    _bat(10, "T Shepeshen", "b", "A Berry", None, 0),
                    _bat(11, "K Shenton", "not out", None, None, 0),
                ],
                "bowl": [
                    _bowl("L Birmingham", "7", 3, 11, 0),
                    # Maidens not legibly separable from his wides/no-balls
                    # total in the photo; see the module docstring above.
                    _bowl("A Berry", "10", 0, 10, 4),
                    _bowl("D Willett", "8", 1, 22, 6),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 48, "wickets": 7, "overs": "12.1",
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 1, "extra_leg_byes": 0, "extra_wides": 4, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 5,
                "bat": [
                    _bat(1, "D Dwyer", "b", "B Beasconi", None, 11),
                    _bat(2, "G Young", "ct", "D Rigny", "J Davies", 18),
                    # Bowler is a correction in the original (the first
                    # name written is struck through); see the module
                    # docstring above.
                    _bat(3, "A Greenwood", "b", "B Thinkley", None, 1),
                    _bat(4, "A Berry", "b", "B Thinkley", None, 0),
                    _bat(5, "M Thomson", "st", "D Rigny", "J Davies", 6),
                    _bat(6, "N Warne", "ct", "D Rigny", "J Davies", 0),
                    _bat(7, "B Birtwhistle", "ct", "D Rigny", "J Davies", 1),
                    _bat(8, "D Willett", "not out", None, None, 6),
                    _bat(9, "W Francis", "not out", None, None, 0),
                    _bat(10, "L Birmingham", "did not bat"),
                    _bat(11, "A Redford", "did not bat"),
                ],
                "bowl": [
                    _bowl("B Thinkley", "6", 1, 14, 2),
                    _bowl("B Beasconi", "3", 0, 30, 1),
                    _bowl("D Rigny", "3", 0, 24, 4),
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
