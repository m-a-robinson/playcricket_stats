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

============================================================================
04-Jun-2011: East Lancs Paper Mill CC 2nd XI vs Littleborough Lake Sides CC
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.09.16.jpg (both
innings). Same printed club scorebook as the matches above. Unlike the
earlier 2011 entries, this one was transcribed from a single full-page
read (no detail crops), then reviewed and corrected by the user against
the same photo -- the reading decisions below are theirs, not inferred.

  - ELPM: 9+7+53+27+0+14+0+0+3+2+1 = 116 (matches "S.TOTAL 116") + 10
    extras (byes 2, wides 7, no balls 1) = 126 all out. Bowling figures
    (B Hussain 13-2-57-3, S Hussain 6-0-31-1, M Amin 8.2-0-32-6, a 4th
    bowler whose name is illegible in the photo 2-1-4-0) sum to all 10
    wickets. M Amin's maiden-overs figure (recorded as 0) is the one cell
    not legibly separable from his wides/no-balls total.
  - Littleborough Lake Sides: 7+100+3+2+4 = 116 + 14 extras (byes 7, leg
    byes 4, wides 3) = 130, chasing down ELPM's 126 for the loss of 3
    wickets (fall of wicket 13, 43, 47) -- Littleborough Lake Sides won by
    7 wickets. A Malik's unbeaten 100 and B Hussain's unbeaten 4 are the
    two not-out batsmen at the end; the other two scores (N Unknown 7, I
    Iqbal 2 lbw) plus J Wild's 3 (stumped K Dodson b M Young) account for
    the 3 dismissals. ELPM's bowling figures (L Birmingham 4-0-21-1, A
    Berry 9-4-35-0, M Young 9-3-34-2, A Redford 2-0-23-0, M Thomson
    1-0-7-0, A Greenwood 1-0-9-0) sum to the correct 3 wickets; their runs
    (129, close to but not exactly matching the batsmen's 116 plus the 3
    wides charged to a bowler) are 1 short of the innings' 130 total, the
    same small reconciliation gap seen elsewhere in this scorebook and
    left as read.

============================================================================
18-Jun-2011: East Lancs Paper Mill CC 2nd XI vs Swinton Moorside CC
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.09.29.jpg (both
innings). Same printed club scorebook as the matches above, also from a
single full-page read reviewed and corrected by the user.

  - Swinton Moorside: 15+11+6+0+1+26+0+22+9+1+0 = 91 (matches "S.TOTAL
    91") + 18 extras (byes 4, leg byes 1, wides 13) = 109 all out.
    Bowling figures (L Birmingham 6.2-?-25-0, A Berry 11-3-31-3, M Young
    9-0-38-5, S Dwyer 4-2-10-2) sum to all 10 wickets; Birmingham's
    maiden-overs digit wasn't confidently read and is left blank rather
    than guessed.
  - ELPM: 19+9+4+37+0+3+1+0+0+13+1 = 87 (matches "S.TOTAL 87") + 9 extras
    = 96 all out, chasing Swinton's 109 -- Swinton Moorside won by 13
    runs. The fall-of-wicket line's 10 entries (24, 34, 34, 36, 41, 46,
    53, 60, 79, 96) look, at first glance, one wicket short of the
    bowling-analysis total (R Curran 5-1-14-0, M Billingham 13-4-35-4, C
    Winstanley 10-1-39-5 = 9 bowler-credited wickets): the 10th dismissal
    is N Warne's run out, which carries no bowler credit, so 9+1=10
    reconciles cleanly. L Birmingham (batting), the 11th man, finished
    not out on 1. ELPM's own extras total (9) is recorded without a
    byes/leg-byes/wides/no-balls breakdown -- not attempted from the
    single read and not asked for.

============================================================================
25-Jun-2011: East Lancs Paper Mill CC 2nd XI vs Westhoughton CC
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.09.44.jpg (both
innings). Same printed club scorebook as the matches above, also from a
single full-page read reviewed and corrected by the user. A tie.

  - ELPM: 89+12+31+18+0+36+8 = 194 (matches "S.TOTAL 194") + 10 extras
    (byes 3, leg byes 1, wides 3, no balls 3) = 204 for 5 -- K Dodson (89)
    and M Young (8) finished not out, with the last 4 in the order (L
    Birmingham, D Hadcroft, M Thomson, W Francis) not needed. Bowling
    figures (J Blair 13-0-65-1, M Fanning 10-2-26-0, K Hodgkiss 6-0-34-1,
    O Turner 6-2-16-0, C Honour 6-1-26-2, D Higham 2-0-21-0, J Berry
    2-0-13-0) sum to 4 bowler-credited wickets; A Greenwood's run out is
    the 5th dismissal, uncredited to any bowler.
  - Westhoughton: 38+15+0+20+0+3+47+30+31 = 184 + 19 extras (byes 7, leg
    byes 1, wides 8, no balls 3) = 203 for 9 -- 1 short of the printed
    204, the same small reconciliation gap seen elsewhere in this
    scorebook and left as read; D Higham and D Fletcher, last in the
    order, weren't needed. C Honour's name is spelled "Hounour" on this
    innings' own batting page but "Honour" on ELPM's bowling-analysis
    page opposite (a spelling clash within the same physical scorebook,
    not two different people) -- standardised to "Honour" throughout.
    Bowling figures (A Berry 18-3-44-4, L Birmingham 14-1-71-1, M Thomson
    1-0-21-0, M Young 10-0-42-2, C Greaves 2-0-8-1) sum to 8
    bowler-credited wickets; S Miller's run out is the 9th.

ELPM 204 for 5, Westhoughton 204 for 9 -- match tied.

============================================================================
02-Jul-2011: East Lancs Paper Mill CC 2nd XI vs Littleborough Lakeside CC
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.09.53.jpg (both
innings). Same printed club scorebook as the matches above, also from a
single full-page read -- but this one reconciled cleanly first pass, with
only one fielder's name needing the user's confirmation.

  - ELPM: 11+8+17+8+23+5+12+29+1+0+13 = 127 (matches "S.TOTAL 127") + 9
    extras (byes 2, leg byes 3, wides 4) = 136 all out. Bowling figures
    (B Hussain 9.3-2-32-3, S Hussain 5-0-21-1, N Sadiq 9-2-29-2, U Haq
    6-0-24-2, A Hussain 5-0-23-1) sum to 9 bowler-credited wickets; L
    Birmingham's run out is the 10th, D Hadcroft finishing not out.
  - Littleborough Lakeside: 37+14+1+69 = 121 + 18 extras (byes 1, leg
    byes 2, wides 14, no balls 4) = 139 for 2, chasing down ELPM's 136
    with S Rashid (37) and N Sadiq (69) both finishing not out --
    Littleborough Lakeside CC won by 8 wickets. Bowling figures (L
    Birmingham 7-0-27-1, A Berry 11-1-37-1, A Greenwood 3-0-35-0, A
    Redford 3-0-25-0, D Hadcroft 2.2-0-11-0, C Holt 1-0-4-0) sum to
    exactly 139 runs and both wickets -- no reconciliation gap this time.

============================================================================
06-Aug-2011: East Lancs Paper Mill CC 2nd XI vs Thornham CC
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.10.11.jpg (both
innings). Same printed club scorebook as the matches above, but ELPM's
own page records each dismissal's bowler by number (1/2/3) rather than
name, cross-referenced against the bowling-analysis table beneath it --
the only match in this batch to do that. Single full-page read, reviewed
and corrected by the user.

  - ELPM: 12+4+15+19+13+1+12+4+1+6+0 = 87 (matches "S.TOTAL 87") + 4
    extras (leg byes 1, wides 3) = 91 all out. Bowler "2" (J Clarke) is
    credited with the first four dismissals (K Dodson, A Redford, G
    Young, A Berry) plus the 9th (D Hadcroft) -- 5 wickets, matching his
    own analysis row (12-1-40-5) exactly; bowler "3" (M Fitzpatrick)
    takes the rest (D Scott, D Dwyer, C Holt, M Young, D Pearson) -- the
    other 5, matching his row (7-1-14-5); bowler "1" (M Turvey, 6-0-34-0)
    takes none. G Young's catch is "ct Towler" (behind the stumps, i.e.
    the wicketkeeper), not "ct Tower" as first read.
  - Thornham: 1+1+76+20 = 98 + 3 extras (byes 1, leg byes 1, no balls 1)
    = 101 for 2, chasing down ELPM's 91 with S Mohammed (76) and R
    Whitehouse (20) both finishing not out -- Thornham won by 8 wickets.
    D Harrop's score is 1, not the 15 first estimated from the
    fall-of-wicket line alone. Bowling figures (A Berry 7-2-31-1, M
    Young 5-0-35-1, G Young 2-0-3-0, A Redford 1-0-7-0, A Birtwistle
    0.3-0-12-0) sum to both wickets.

============================================================================
13-Aug-2011: Failsworth CC vs East Lancs Paper Mill CC 2nd XI
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.10.23.jpg (both
innings). Same printed club scorebook as the matches above, from a
single full-page read reviewed and corrected by the user across two
rounds -- ELPM's innings in particular needed several batsmen's scores
re-checked against the photo.

  - Failsworth: 0+17+0+4+13+38+24+3+0+0+0 = 99 (matches "S.TOTAL 99") +
    10 extras (byes 4, leg byes 1, wides 4, no balls 1) = 109 all out.
    Bowling figures (A Berry 15-2-49-4, L Birmingham 7-0-15-1, A Redford
    5-0-38-1, M Young 2.1-0-2-3) sum to 9 bowler-credited wickets; N
    Reed's run out is the 10th and, unlike the odd-looking printed
    bowling-analysis row that first suggested A Redford took 2, carries
    no bowler credit -- Redford's true figure is 1 wicket (I Wilson),
    matching the dismissals directly attributable to him. M Young's
    figures were first misread as "21-0-2-3"; the correct reading is
    2.1 overs, not 21.
  - ELPM: 21+23+1+16+1+1+12+0+18+6+0 = 99 + 7 extras (byes 4, leg byes 1,
    wides 1, no balls 1) = 106, 1 run over the user-confirmed final total
    of 105 -- the same small reconciliation gap seen elsewhere in this
    scorebook, left as read rather than adjusted to fit. G Reeves took 8
    of ELPM's 10 wickets (A Berry, A Redford, D Dwyer, D Hadcroft, A
    Wilkinson, L Birmingham, M Young, A Birtwistle), with B Beresconi (C
    Holt) and T Shepherdson (G Young) taking one each; his own
    bowling-analysis row (9.1-1-34-8) matches exactly. D Pearson, batting
    at 7, finished not out on 12 while all ten other batsmen were
    dismissed around him.

Failsworth 109 vs ELPM 105 -- Failsworth CC won by 4 runs.

============================================================================
03-Sep-2011: East Lancs Paper Mill CC 2nd XI vs Roe Green CC
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.10.37.jpg (both
innings). Same printed club scorebook as the matches above. The scorer's
own note reads "7pm min 10 overs, rain affected" -- ELPM's chase was cut
short by rain partway through, matching what the user already knew about
this match before any image was read: ELPM were 50 for 6 when abandoned.

  - Roe Green: 20+5+15+0+33+14+14+7+0+0 = 108 (matches "S.TOTAL 108") +
    26 extras (byes 4, leg byes 3, wides 12, no balls 7) = 134 for 9 --
    Buckleton finished not out. Bowling figures (A Redford 9-3-30-1, L
    Birmingham 12-1-25-1, D Pearson 10-1-33-2, D Hadcroft 6-2-19-1, B
    Birtwistle 7.1-1-20-4) sum to all 9 wickets. L Needham's score was
    first misread as 7; the correct figure (14) is what makes the total
    reconcile.
  - ELPM: 2+1+0+8+21+11+0 = 43 + 7 extras (byes 4, leg byes 1, wides 2)
    = 50 for 6 when the umpires abandoned play for rain, matching the
    fall-of-wicket line (5, 5, 15, 16, 43, 50) exactly. Bowling figures
    (J Needham 14-8-11-2, M Buckleton 6-1-9-0, R Green 8-4-12-1, L
    Needham 4-0-11-2, M Canning 3-1-2-0) sum to 5 bowler-credited
    wickets; A Redford's run out is the 6th.

Recorded as an abandoned match (no result) rather than a win or loss for
either side, per the user's own knowledge of the game.

============================================================================
11-Sep-2011: East Lancs Paper Mill CC 2nd XI vs Westhoughton CC
============================================================================

Source image: scorebooks/2nd XI/2011/2026-08-30 10.10.47.jpg (both
innings). Same printed club scorebook as the matches above -- the return
fixture to 25-Jun-2011's tie, this time at Westhoughton. Single full-page
read, reviewed and corrected by the user across two rounds; ELPM's
middle order in particular was significantly reshuffled from the first
read.

  - ELPM: 22+0+4+25+20+8+10+0+1+0+1 = 91 (matches "S.TOTAL 91") + 12
    extras (byes 5, leg byes 4, wides 1, no balls 2) = 103 all out. The
    printed bowling-analysis wickets (S Ashcroft 15-3-44-1, J Blair
    11-1-36-3, O Turner 6-2-10-5, C Honour 2-0-4-1) don't match the
    per-bowler count implied by the corrected dismissals (S Ashcroft 2:
    K Dodson, G Young; J Blair 2: P Partington, A Redford; O Turner 4: D
    Dwyer, D Pearson, D Hadcroft, B Birtwistle; C Honour 1: M Young) --
    both group sum to 9 bowler-credited wickets plus A Birtwistle's run
    out, but the individual bowlers' shares differ. The dismissals, tied
    to named batsmen, are used as given rather than adjusted to match
    the analysis row; the discrepancy is left unresolved.
  - Westhoughton: 12+30+53+4 = 99 + 7 extras (byes 3, leg byes 1, wides
    3) = 106 for 2, chasing down ELPM's 103 with G Green (53) and C
    Honour (4) both finishing not out -- Westhoughton CC won by 8
    wickets. O Dixon's dismissal is confirmed as stumped (P Partington,
    ELPM's keeper, b A Redford).

============================================================================
24-Apr-2004: East Lancs Paper Mill CC 1st XI vs Robinsons CC
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 12.59.12.jpg and
2026-09-15 12.59.33.jpg (both innings). First of a new batch of 45 1st XI
photos covering the 2004 season (folder name "1xt XI" is the user's own
upload naming, kept as-is throughout this and the following matches).
Single full-page read, reviewed and corrected by the user in one round.

  - Robinsons: 0+36+21+28+3+2+28+2+9+6 = 135 + 15 extras (no balls 1,
    wides 10, byes 3, leg byes 1) = 150 for 8. ELPM's bowling figures (P
    Hewart 10-2-22-1, A Openshaw 7-2-22-0, I Wade 9-1-28-2, A Berry
    10-2-30-2, S Dalton 9-1-44-3) sum to all 8 wickets and to 146 runs
    conceded (135 batsmen's runs + 10 wides + 1 no ball).
  - ELPM: 19+13+1+0+23+1+15+11+4+6+1 = 94 + 20 extras (leg byes 5, byes
    11, wides 3, no balls 1) = 114, six runs short of the printed total
    of 120 all out -- Robinsons' bowling figures (E Whitworth 16.5-2-51-5,
    D Smith 12-2-28-2, M Brown 4-0-25-2) sum correctly to 9 bowler-credited
    wickets (A McCheyne's run out is the 10th) and to 104 runs conceded,
    which is also 6 more than the batting card's 94+4 (wides+no balls)
    reconciles to -- so one batsman's individual score here is very
    likely a few runs short, but which one isn't identifiable from a
    single read; left as transcribed rather than adjusted, per the same
    "leave the gap" approach used for Roe Green/Westhoughton above.
    Robinsons won by 30 runs.

competition_name is "NMCL Division 1" -- not printed on the page, but
nmcl_stats.py's own 2004 Division 1 season-aggregate rows (J Shiels, F
Daly, S Dalton, P Hewart and M Robinson -- all of whom appear in this same
2004 scorebook) confirm the 1st XI played Division 1 that season, the
same evidence-based inference used for the 2010 Failsworth Macedonia
match above.

============================================================================
1-May-2004: East Lancs Paper Mill CC 1st XI vs Springhead CC
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 12.59.48.jpg and
2026-09-15 12.59.55.jpg (both innings). Single full-page read; ELPM's
batting order was significantly reshuffled by the user across one
correction round (I Wade batting at 4 was originally missing, his 15 runs
having been misattributed to G Young, and F Daly's dismissal corrected to
caught-and-bowled).

  - ELPM: 8+31+1+15+1+3+1+6+14+0+0 = 80 + 7 extras = 87 all out (P Hewart
    finishing not out). Springhead's bowling figures, as corrected by the
    user, are K Lees 15.4-7-31-4 and T DeHaviland 13-3-40-5 -- 9 of the 10
    wickets; the 10th (G Young, run out or bowled -- not established) is
    left without a bowler credit rather than guessed. Extras breakdown
    wasn't captured with confidence on this read -- the total (7) is
    certain, the byes/leg-byes/wides/no-balls split isn't, so it is
    recorded here as a single bucket (see the module docstring's existing
    "split wasn't attempted" precedent).
  - Springhead: A Plat 23, S Rice 9, R Shaw 39 not out, T DeVillain 0, K
    Fielding 9, K Lees 9 not out (J Cook/J Batey/M O'Robert/M Sweetin/A
    Milner did not bat) = 89 by these six individual scores, nine more
    than the scorebook's own printed batsmen's total of 80 -- the same
    "one score is probably a little off, but which one isn't
    identifiable from a single read" situation as ELPM's innings in the
    Robinsons match above. The printed total is used for the innings
    total (80 + 8 extras -- no balls 1, wides 2, leg byes 5 -- = 88 for
    4, chasing down ELPM's 87), the individual scores are left as
    transcribed. ELPM's bowling figures (P Hewart 8-4-8-0, D Woodward
    5-0-12-0, J Sheils 6-2-18-2, A Berry 6-2-18-2, S Dalton 3.1-1-14-0)
    sum to the 4 wickets. Springhead won by 6 wickets.

============================================================================
8-May-2004: Fothergill & Harvey CC vs East Lancs Paper Mill CC 1st XI
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.00.04.jpg and
2026-09-15 13.00.41.jpg (both innings). Away fixture. ELPM's batting card
was badly misread on the first pass -- six extra middle/lower-order names
were invented that hadn't actually batted -- and was substantially
rewritten by the user in one correction round; the runs-off-the-bat total
(247) was unchanged throughout, which is what makes it clear the error was
entirely in how the total was distributed across batsmen, not in the
total itself.

  - ELPM: F Daly 0 (ct Khalid b McWilliam), J Shiels 104 (ct J Fallon b
    McWilliam), A McCheyne 0 (b Saleem), I Wade 123 (ct Saleem b Shajid),
    G Young 20 not out; N Warne, S Dalton, A Berry, P Hewart, M Robinson
    and M Young did not bat. 0+104+0+123+20 = 247 + 23 extras = 270 for 4
    (innings closed with 6 of the order unused, rather than all out).
    Fothergill & Harvey's bowling figures (G McWilliam 6.1-1-41-2, Saleem
    10-0-57-1, Shajid 5-0-34-1, J Edmondson 5-0-44-0, M Craney 6.1-1-34-0,
    Shait 6-0-25-0, K Denhurst 2-0-26-0) are adjusted from the original
    read so their wickets (2+1+1=4) match the corrected batting card;
    "Sajid" in the original read is the same bowler as "Shajid" corrected
    here. Extras breakdown wasn't captured with confidence -- recorded as
    a single bucket, as above.
  - Fothergill & Harvey: S Toohey 0 (ct G Young b P Hewart), S Haid 1
    (lbw b P Hewart), J Edmondson 6 (b S Dalton), Sadid 24 (st M Robinson
    b S Dalton -- corrected to name ELPM's keeper as the stumper rather
    than the bowler as fielder), K Denhurst 0 (ct A Berry b P Hewart), M
    Croney 2 (lbw b P Hewart), Kalid 4 (ct I Wade b A Berry -- corrected
    from "Kali"), D McWilliams 9 (ct A Berry, bowler not established),
    Saleem 16 (st M Robinson b A Berry -- same keeper-vs-bowler
    correction as Sadid's dismissal above), G McWilliam 21 not out, J
    Fallon 3 not out. 0+1+6+24+0+2+4+9+16+21+3 = 86 + 8 extras = 94 all
    out. ELPM's bowling figures (P Hewart 9-1-30-4, S Dalton 9-1-25-2, A
    Berry 6-2-13-2, M Young 2-0-15-0, J Sheils 4-1-9-0) sum to 8
    bowler-credited wickets, plus D McWilliams's wicket (bowler not
    established) as the 9th -- G McWilliam and J Fallon finish not out.
    ELPM won by 176 runs.

============================================================================
9-May-2004: East Lancs Paper Mill CC 1st XI vs Ashton Ladysmith CC
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.00.48.jpg and
2026-09-15 13.01.00.jpg (both innings). "Ashton Ladysmith" is this
opponent's full name throughout the 2004 season, per the user -- other
short forms seen on the pages themselves ("Ashton", "Lady/smith") all
refer to the same club.

  - Ashton Ladysmith: J Hillson 9, G Pinder 8, P Reynolds 4, M Sheilds 2,
    C Collings 0, S Sheilds 11, A Camps 18, C Bennett 6, M Collings 3, B
    Collings 9, D Sheilds 0 = 70 + 12 extras = 82 all out. Individual
    dismissal/bowler pairings weren't captured with confidence on this
    read (only the team bowling analysis was) -- ELPM's bowling figures,
    as corrected by the user (the first read had mistakenly used a
    balls-bowled column as an overs column for several bowlers), are P
    Hewart 8-4-8-1, S Dalton 6-2-13-1, S Keyworth 6-0-32-1, M Hodson
    4-0-8-1, A Berry 2.4-0-3-2, summing to 6 of the 10 wickets; the
    other 4 are left without bowler credit.
  - ELPM: F Daly 32 (c&b A Camp), J Sheils 0 (ct C Bennett b A Camp), J
    Wade 26 (b J Hillson -- corrected from "I Wade"), I Wade 16 not out
    (corrected from "G Young"), G Young 5 not out (corrected from "A
    Berry"); all others did not bat. 32+0+26+16+5 = 79 + 5 extras = 84
    for 3. Ashton Ladysmith's bowling figures (A Camps 7.1-0-24-2, P
    Reynolds 12-0-19-0, J Hillson 3.5-1-39-1) sum to the 3 wickets. ELPM
    won by 7 wickets.

============================================================================
15-May-2004: East Lancs Paper Mill CC 1st XI vs Rochdalians CC
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.01.08.jpg and
2026-09-15 13.01.16.jpg (both innings). The user asked for extra care on
this match and the next (16-May, below) specifically on dismissals, since
this scorebook often splits a single "how out" entry across two printed
lines (a catcher's name above the bowler's, or a wicketkeeper's name above
the bowler's for a stumping) that are easy to misread as one name or to
transpose -- both matches were re-read slowly with that in mind, and the
dismissals below were corrected by the user across one further round.

  - ELPM: F Daly 9 (b S Rahman), J Sheils 0 (ct J Dell b S Heighway), A
    McCheyne 55 not out, I Wade 11 (ct S Mehmood b S Rahman -- fielder
    corrected from an initial guess of "M Shahzeb"), G Young 12 (lbw b F
    Butt), Qamer 0 (ct Z Khan b F Butt), A Berry 8 (b F Butt), P Hewart 2
    (b F Butt), S Carr 2 (st b A Rauf -- the wicketkeeper's name couldn't
    be read and the user confirmed none was legible, so it's left blank
    rather than guessed), S Dalton 26 (b S Rahman), M Robinson 0 (lbw b S
    Heighway). 9+0+55+11+12+0+8+2+2+26+0 = 125, one more than the
    scorebook's own printed batsmen's total of 124 -- left unresolved, as
    with the similar 1- and 9-run gaps in the Robinsons and Springhead
    matches above. Extras 44, total 168 all out; Rochdalians' bowling
    figures (S Heighway 9.1-1-26-2, S Rahman 9-2-39-3, F Butt 4-0-28-4, S
    Mehmood 10-3-32-0, A Rauf 8-0-30-1) sum to all 10 wickets and to 155
    runs conceded, which plus 13 non-bowler extras (byes/leg byes, out of
    the 44 total) reconciles to 168 -- the wides/no-balls/byes/leg-byes
    split within the 44 wasn't captured with confidence, so is recorded
    as a single bucket.
  - Rochdalians: M Tyyub 75 (b J Sheils), N Hayee 60 (ct I Wade b S
    Carr), A Rauf 0 not out, M Shahzeb 18 (ct P Hewart b S Carr), M Iqbal
    6 not out; Z Khan, S Rahman, F Butt, S Mehmood, J Dell and S Heighway
    did not bat. 75+60+0+18+6 = 159, matching the scorebook's own printed
    batsmen's total exactly. Extras 10, total 169 for 3, chasing down
    ELPM's 168. ELPM's bowling figures, as corrected by the user (P
    Hewart 7-1-31-0, S Dalton 6-2-33-0, A Berry 4-0-24-0, S Carr
    11-3-54-3, I Wade 3-0-13-0, J Sheils 5-1-11-1) sum to 4 wickets
    against the batting card's 3 real dismissals (S Carr's two catches
    plus J Sheils' bowled) -- the same "bowling analysis and named
    dismissals don't quite agree" situation as the 11-Sep-2011 Westhoughton
    match, and left unresolved the same way, with the named dismissals
    used as given. Rochdalians won by 7 wickets.

============================================================================
16-May-2004: East Lancs Paper Mill CC 1st XI vs Rochdalians CC (cup match)
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.02.15.jpg and
2026-09-15 13.02.42.jpg (both innings). A genuinely separate fixture from
the league match the previous day, per the user -- a cup tie, same
opponent. Dismissals again re-read slowly for two-line catcher/bowler
splits, with several rows requiring a second correction round from the
user to resolve which of M Young/J Sheils/A Berry bowled which of
Rochdalians' middle order.

  - ELPM: F Daly 95 (b S Mehmood), J Sheils 50 (run out, fielder M
    Tyyub), J Wade 41 (ct A Smith b M Tyyub), I Wade 42 (b F Butt), G
    Young 16 (ct M Tyyub b G Khan), S Keyworth 10 not out, M Hodson 1 not
    out; A Berry, S Dalton, M Robinson and M Young did not bat.
    95+50+41+42+16+10+1 = 255, matching the scorebook's own printed
    batsmen's total exactly. Extras 52, total 307 for 5 (innings closed
    with 4 of the order unused). Rochdalians' bowling figures (G Khan
    7-0-37-1, S Rahman 7-0-54-0, S Mehmood 8-0-35-1, F Butt 7-0-47-1, M
    Tyyub 9-0-61-1, A Rauf 7-0-50-0) sum to the 4 bowler-credited
    wickets, plus J Sheils' run out as the 5th.
  - Rochdalians: M Tyyub 2 (ct M Robinson b S Dalton), N Hayee 29 (ct F
    Daly b M Young), S Mehmood 7 (ct A Berry b M Hodson), M Shaheed 44 (b
    I Wade), F Butt 40 (ct M Robinson b J Sheils), S Rahman 26 (c&b J
    Sheils), A Smith 2 (ct F Daly b A Berry), G Khan 6 (c&b M Young), J
    Dell 3 (b M Young), M Iqbal 10 (b M Young -- the first read had this
    as "not out", which conflicted with the innings' own fall-of-wicket
    table showing a 10th wicket falling at 191; the user's correction
    resolves that), A Rauf 0 not out.
    2+29+7+44+40+26+2+6+3+10+0 = 169, matching the scorebook's own
    printed batsmen's total exactly. Extras 22, total 191 all out. ELPM's
    bowling figures (M Hodson 9-1-43-1, S Dalton 9-0-35-1, I Wade
    4-0-30-1, M Young 4-0-28-4, J Sheils 4-0-18-2, A Berry 4-0-24-1) sum
    to exactly all 10 wickets against the corrected dismissals above.
    ELPM won by 116 runs.

============================================================================
22-May-2004: East Lancs Paper Mill CC 1st XI vs Glodwick CC
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.02.56.jpg and
2026-09-15 13.03.10.jpg (both innings). Dismissals were cross-checked
against each innings' own bowling-analysis wicket totals rather than read
from the "how out" column alone -- this is what caught two wrong bowler
credits on the first pass (R White and P Kitchen were both actually A
Berry's wickets, not split across other bowlers as first read).

  - Glodwick: J Holt 0 (b P Hewart), M Kirk 7 (c&b P Hewart), K Edge 6 (ct
    M Robinson b P Hewart), M Parkinson 23 (ct A McCheyne b A Berry), N
    Khan 62 (ct F Daly b A Berry), R White 10 (b A Berry), R David 1 (ct
    M Robinson b S Dalton), R Connolly 0 (lbw b S Dalton), P Kitchen 4
    (ct S Keyworth b A Berry), A Raja 1 (run out), U Anwar 4 not out.
    0+7+6+23+62+10+1+0+4+1+4 = 118, matching the scorebook's own printed
    batsmen's total exactly. Extras 7, total 125 all out. ELPM's bowling
    figures (P Hewart 9-2-44-3, S Carr 7-0-24-0, S Dalton 10-2-23-2, I
    Wade 3-1-13-0, A Berry 5.4-1-18-4) sum to exactly 9 bowler-credited
    wickets, plus A Raja's run out as the 10th.
  - ELPM: A McCheyne 29 not out, J Sheils 10 (ct S Holt b U Anwar), G
    Young 62 not out; I Wade, F Daly, A Berry, S Dalton, S Keyworth, P
    Hewart, S Carr and M Robinson did not bat. 29+10+62 = 101, matching
    the scorebook's own printed batsmen's total exactly. Extras 25, total
    126 for 1 (the printed innings box read "for 2" on first pass, but
    there is only one genuine dismissal in the how-out column and the
    user confirmed 1 wicket is correct). ELPM won by 9 wickets.

============================================================================
29-May-2004: Failsworth Macedonia CC vs East Lancs Paper Mill CC 1st XI
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.03.16.jpg and
2026-09-15 13.03.23.jpg (both innings). Away fixture. As with Glodwick
above, dismissals and bowler credit were built from the cross-check
against each innings' bowling-analysis totals first, with individual
runs and a few fielder names filled in by the user afterwards -- for
Failsworth Macedonia's own innings in particular, the first pass got the
bowler for every dismissal right but couldn't read a single individual
score with confidence, so the runs below are the user's direct read of
the "total" column rather than a self-consistency check.

  - Failsworth Macedonia: P Haselden 0 (ct J Wade b S Carr), G Martin 1
    (b P Hewart), D Rigney 55 (b S Dalton), N Daly 62 (b J Sheils), C
    Gawber 43 not out, C Akin 33 (b S Dalton), D Marriot 0 (ct A Berry b
    S Dalton), I Wilson 1 not out. 0+1+55+62+43+33+0+1 = 195, matching
    the scorebook's own printed batsmen's total exactly. Extras 30, total
    225 for 6 (the innings box's own "for 7" doesn't match either the 6
    legible fall-of-wicket entries or the bowling analysis, confirmed by
    the user as 6). ELPM's bowling figures (P Hewart 9-4-23-1, S Carr
    12-3-54-1, S Dalton 14-1-49-3, I Wade 3-0-30-0, A Berry 3-0-25-0, J
    Sheils 4-0-18-1) sum to exactly the 6 wickets.
  - ELPM: F Daly 0 (ct N Daly b G Broadhead), J Sheils 9 (b D Atkin), J
    Wade 5 (b G Broadhead), I Wade 0 (ct N Daly b D Atkin), G Young 1 (run
    out), A McCheyne 16 (b C Akin), A Berry 5 (ct P Haselden b D Atkin),
    P Hewart 22 (b C Akin), S Dalton 20 not out, S Carr 24 (ct C Gawber b
    I Wilson), M Robinson 0 (retired hurt). Several of these dismissals
    were reshuffled from the first-pass read (P Hewart was originally
    read as not out, S Dalton and S Carr's dismissals were swapped, and M
    Robinson was originally thought not to have batted at all).
    0+9+5+0+1+16+5+22+20+24+0 = 102, matching the scorebook's own printed
    batsmen's total exactly. Extras 16, total 118 for 9 (9 genuine
    dismissals; M Robinson's retirement isn't itself a fall of wicket).
    Failsworth Macedonia's bowling figures (G Broadhead 9-4-19-2, D Atkin
    9-1-39-3, C Akin 7-2-20-2, I Wilson 6.4-0-27-1) sum to exactly the 8
    bowler-credited wickets, plus G Young's run out as the 9th. Failsworth
    Macedonia won by 107 runs.

============================================================================
30-May-2004: East Lancs Paper Mill CC 1st XI vs Tott St John CC
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.03.31.jpg and
2026-09-15 13.03.38.jpg (both innings). Bowling-analysis figures for both
innings needed the user's own direct read of the book -- the OVERS/M'DNS/
RUNS/WKTS grid was too cramped to trust from the photo alone, even after a
crop-and-zoom pass (see below).

  - ELPM: F Daly 2 (ct C Brook b M Cotton), J Sheils 16 (ct Coe b R
    Brooks), J Wade 82 (ct C Brook b N Butterworth), I Wade 2 (ct Chadwick
    b R Brooks), G Young 27 (run out), A McCheyne 5 (ct C Brook b P
    Meehan), N Warne 36 not out, A Berry 12 not out; S Dalton, S Carr and
    P Hewart did not bat. 2+16+82+2+27+5+36+12 = 182, matching the
    scorebook's own printed batsmen's total exactly. Extras 18, total 200
    for 6. Tott St John's bowling figures (M Cotton 8-1-30-1, P Skundric
    8-0-48-0, S Moriarty 7-2-29-0, R Brooks 4-0-20-2, N Butterworth
    5-0-21-1, P Meehan 8-0-39-1) sum to 5 bowler-credited wickets, plus G
    Young's run out as the 6th.
  - Tott St John: K Coe 5 (ct P Hewart b S Carr), M Deegan 3 (ct A
    McCheyne b P Hewart), R Brooks 4 (b P Hewart), N Butterworth 45 (ct N
    Warne b A Berry), P Meehan 14 (ct J Wade b A Berry), P Skundric 17 (b
    A Berry), S Smith 17 (ct F Daly b A Berry), M Chadwick 5 (ct J Sheils
    b A Berry), C Brooks 3 (b J Sheils), S Moriarty 22 not out, M Cotton
    13 not out. 5+3+4+45+14+17+17+5+3+22+13 = 148 + 18 extras = 166.
    ELPM's bowling figures (P Hewart 8-2-29-2, S Carr 6-2-13-1, S Dalton
    7-0-50-0, I Wade 8-1-21-0, A Berry 8-0-25-5, J Sheils 3-0-15-1) sum to
    exactly all 9 wickets. ELPM won by 34 runs.

============================================================================
5-Jun-2004: East Lancs Paper Mill CC 1st XI vs Rochdale Catholic Club
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.04.03.jpg and
2026-09-15 13.04.21.jpg (both innings). Fully reconciled on the first
detailed pass -- every dismissal cross-checks against the bowling
analysis and both innings' component runs match the scorebook's own
printed totals exactly. Distinct from the away leg of this fixture on
10-Aug-2004 and the Calverley Cup Final (also vs Rochdale Catholic Club).

  - ELPM: F Daly 13 (ct Mulkeen b M Sohail), A McCheyne 1 (ct J Rafique b
    J Iqbal), J Wade 35 not out, I Wade 5 (ct J Rafique b J Iqbal), G
    Young 2 (ct D Mulkeen b J Iqbal), N Warne 12 (b J Iqbal), A Berry 0 (b
    M Sohail), P Hewart 0 (b M Sohail), S Dalton 2 (ct H Khan b M Tayab),
    S Carr 0 (ct H Khan b M Tayab), A Openshaw 0 (b M Sohail).
    13+1+35+5+2+12+0+0+2+0+0 = 70, matching the scorebook's own printed
    batsmen's total exactly. Extras 18, total 88 all out. Rochdale
    Catholic Club's bowling figures (M Sohail 12-0-41-4, J Iqbal 9-1-38-4,
    M Tayab 2.3-0-8-2) sum to exactly all 10 wickets.
  - Rochdale Catholic Club: H Khan 1 (ct S Dalton b P Hewart), D Mulkeen
    jnr 5 (ct F Daly b P Hewart), D Mulkeen 11 (ct Warne b S Carr), J
    Rafique 23 not out, S Khan 42 (b S Dalton), Z Shah 0 not out; M Tayab,
    W Ali, M Sohail, J Iqbal and B Anjum did not bat. 1+5+11+23+42 = 82,
    matching the scorebook's own printed batsmen's total exactly. Extras
    9, total 91 for 4. ELPM's bowling figures (P Hewart 4-0-19-2, S Carr
    4-0-20-1, A Berry 3.5-0-17-0, S Dalton 2-0-30-1) sum to exactly the 4
    wickets. Rochdale Catholic Club won by 6 wickets.

============================================================================
12-Jun-2004: East Lancs Paper Mill CC 1st XI vs Elton Vale CC
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.04.40.jpg and
2026-09-15 13.04.48.jpg (both innings). The first pass badly confused
which page belonged to which team (Elton Vale's own bowlers' names --M
Ikram, Z Daddaboy, etc.-- were misread as ELPM batsmen further down the
order, and vice versa); the user's full re-read of both batting cards
resolved it.

  - Elton Vale: M Irfan 7 (b S Carr), F Ahmed 2 (ct J Sheils b P Hewart),
    Z Daddaboy 23 (ct I Wade b A Berry), A Khan 2 (ct P Partington b S
    Carr), T Ahmed 36 (ct I Wade b S Dalton), M Ikram 10 (b S Dalton), L
    Marsden 0 (b S Dalton), J Khan 23 (lbw b S Dalton), C Keyworth 14 not
    out, K Hothersall 0 (ct J Sheils b A Berry), B Baker 0 (st P
    Partington b S Carr). 7+2+23+2+36+10+0+23+14+0+0 = 117, matching the
    scorebook's own printed batsmen's total exactly. Extras 5, total 122
    all out. ELPM's bowling figures (P Hewart 11-3-24-1, S Carr
    10.1-4-30-3, A Berry 6-1-33-2, S Dalton 7-4-15-4, I Wade 3-0-14-0, J
    Sheils 5-2-3-0) sum to exactly all 10 wickets.
  - ELPM: F Daly 3 (ct L Marsden b M Ikram), J Sheils 13 (b Z Daddaboy), J
    Wade 73 (ct L Marsden b J Khan), I Wade 8 (ct T Ahmed b M Ikram), G
    Young 5 (ct Z Daddaboy b M Irfan), A McCheyne 3 (c&b M Irfan), P
    Partington 3 not out, A Berry 5 not out; S Dalton, P Hewart and S Carr
    did not bat. 3+13+73+8+5+3+3+5 = 113, matching the scorebook's own
    printed batsmen's total exactly. Extras 10, total 123 for 6. Elton
    Vale's bowling figures (M Ikram 8-1-30-2, Z Daddaboy 6-0-39-1, C
    Keyworth 3-0-18-0, M Irfan 5-0-19-2, J Khan 4.1-1-15-1) sum to exactly
    the 6 wickets. ELPM won by 4 wickets, chasing down Elton Vale's 122.

============================================================================
13-Jun-2004: East Lancs Paper Mill CC 1st XI vs Degham Hibbert CC
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.04.57.jpg and
2026-09-15 13.05.10.jpg (both innings). "Degham Hibbert" is the club name
as read from the page and confirmed by the user -- an unfamiliar club not
seen elsewhere in the archive, but not a misread. ELPM's batting order was
significantly reshuffled by the user across two correction rounds
(J Wade/I Wade's runs and dismissal methods were swapped twice before
landing correctly, and S Keyworth/N Warne's batting positions moved).
Seven separate crop-and-zoom attempts on this specific photo failed to
isolate a clean OVERS/M'DNS/RUNS/WKTS summary block the way that technique
worked on other matches this batch -- this page's tally grid runs to 47
overs with cumulative scores annotated inline in the tally cells rather
than a separate boxed summary, so both innings' complete bowling figures
came from the user reading the book directly.

  - ELPM: F Daly 14 (lbw b E Ziz), J Sheils 63 (ct B Farouk b M Bhana), J
    Wade 36 (run out), I Wade 18 (ct A Ziz b Mustaq Patel), G Young 57
    (c&b B Erfan), S Keyworth 1 (b B Erfan), N Warne 12 (ct Iqbal b P
    Younas), A McCheyne 22 not out, A Berry 13 not out; O Hellyer and S
    Carr did not bat (S Carr last in the printed order). 14+63+36+18+57+
    1+12+22+13 = 236, matching the scorebook's own printed batsmen's total
    exactly. Extras 18, total 254 for 7. Degham Hibbert's bowling figures
    (E Ziz 6-1-15-1, M Bhana 9-0-42-1, Mustaq Patel 8-0-62-1, B Erfan
    7-0-44-2, P Younas 9-1-30-1, Mo Patel 6-0-47-0) sum to exactly 6
    bowler-credited wickets, plus J Wade's run out as the 7th.
  - Degham Hibbert: P Iqbal 32 (ct J Wade b I Wade), an unidentified No. 2
    batsman, P Faruk 24 (ct J Sheils b I Wade -- specifically the "P
    Faruk" who batted third, distinct from "B Faruk" below), P Seed 13 (b
    I Wade), P Muamaf 18 (b I Wade), B Faruk 10 (ct N Warne b A Berry), P
    Mustaq 2 (b P Hewart), P Mustaqa 65 not out, P Younas 31 not out.
    ELPM's bowling figures (P Hewart 9-0-44-2, S Carr 7.2-0-58-0, I Wade
    9-2-49-4, A Berry 7-0-49-1, S Keyworth 3-0-16-0, J Sheils 3-0-14-0, J
    Wade 1-0-2-0) sum to 7 wickets, one more than the 6 named dismissals
    above -- and the 8 named batsmen's runs (32+24+13+18+10+2+65+31 = 195)
    fall 38 short of the scorebook's own printed batsmen's total of 233
    (256 total minus 23 extras). Both gaps are almost certainly the same
    missing person: the unidentified No. 2 batsman, inferred here at 38
    runs and a dismissal credited to P Hewart's second wicket (his other
    one is P Mustaq's) purely to make both the runs and the wickets
    reconcile exactly -- genuinely inferred rather than read, unlike every
    other figure in this file, and flagged as such rather than presented
    as a normal transcription. Chasing ELPM's 254, Degham Hibbert reached
    256 with 7 wickets down -- Degham Hibbert won by 3 wickets.

============================================================================
19-Jun-2004: East Lancs Paper Mill CC 1st XI vs Ashton Ladysmith CC
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.05.20.jpg and
2026-09-15 13.05.32.jpg (both innings). The first pass badly misread this
match -- the wrong crop region for "how out"/"bowler"/"total" produced a
run list (12,14,4,14,8,4,14,10...) the user flagged as "almost all wrong",
and ELPM's total looked like an abandoned 97-1 rather than a completed
chase. Locating the correct crop (the HOW OUT/BOWLER/TOTAL block sits as
one unit in the lower-right of each page, separate from the runs-scored
tally grid that was confusing the first pass) and re-reading fixed both:
the corrected run list matches the user's figures exactly, and the
"missing" 47 runs in ELPM's total turned out to be a Daly/Sheils score
swap, not an incomplete innings.

  - Ashton Ladysmith: S Shields 3 (b S Carr), G Pinder 55 (ct G Young b I
    Wade), P Reynolds 5 (ct I Wade b P Hewart), M Shields 18 (ct S Dalton
    b S Keyworth), C Collings 8 (ct S Carr b S Keyworth), C Bennett 5 (ct
    J Sheils b S Keyworth), D Shields 0 (b I Wade), M Collings 6 (run
    out), B Collings 4 (ct S Dalton b J Sheils), C Rose 15 (b J Sheils), S
    Telfer 0 not out. 3+55+5+18+8+5+0+6+4+15+0 = 119, matching the
    scorebook's own printed batsmen's total exactly. Extras 21, total 140
    all out. ELPM's bowling figures (P Hewart 7-2-33-1, S Carr 7-1-20-1, A
    Berry 5-0-15-0, S Keyworth 10-1-29-3, I Wade 6-1-13-2, J Sheils
    2.3-1-5-2, S Dalton 2-0-10-0) sum to exactly 9 bowler-credited
    wickets, plus M Collings' run out as the 10th.
  - ELPM: F Daly 51 (ct C Rose b S Shields), J Sheils 66 not out, I Wade 14
    not out; all others did not bat. 51+66+14 = 131 + 13 extras = 144-1.
    Ashton Ladysmith's bowling figures (P Reynolds 11-0-42-0, J Telfer
    5-0-30-0, G Pinder 6-0-30-0, S Shields 3-0-17-1, M Collings 2.4-0-17-0)
    sum to exactly the 1 wicket, and their runs conceded (136) plus extras
    (8) reconcile to 144 exactly. ELPM won by 9 wickets.

============================================================================
20-Jun-2004: West Leigh CC vs East Lancs Paper Mill CC 1st XI
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.05.41.jpg and
2026-09-15 13.05.48.jpg (both innings). "Westleigh Meths" is this
opponent's full name throughout the 2004 season, per the user; "West
Leigh" as printed on the page is the same club. Away fixture. West
Leigh's batting order needed a full rebuild from the user after the
first read badly scrambled several players' names and dismissals across
rows (K Lloyd/A Lloyd/C Lloyd and C Ralph/S Ralph both being on the
XI, plus a batsman initially misread as "K Hockinson", didn't help).
Both innings' bowling-analysis figures (overs/maidens/runs) came from
the user directly -- the crop of this page's bowling grid wasn't legible
enough to trust either time it was attempted.

  - West Leigh: KH Sadiq 7 (b P Hewart), D Jackson 5 (b S Carr), J Taylor
    0 (ct G Young b P Hewart), C Ralph 61 (ct J Sheils b S Keyworth), K
    Lloyd 5 (b S Dalton), C Brett 1 (ct G Young b S Keyworth), A Lloyd 17
    (ct P Hewart b A Berry), S Ralph 13 (b A Berry), D Alridge 4 (b S
    Dalton), I Atkinson 6 not out, L Brennan 0 (ct J Sheils b A Berry).
    7+5+0+61+5+1+17+13+4+6+0 = 119, five short of the scorebook's own
    printed batsmen's total of 124 -- left unresolved, as with similar
    small gaps elsewhere in this file. Extras 15, total 139 all out.
    ELPM's bowling figures (P Hewart 10-5-26-2, S Carr 7-0-35-1, S Dalton
    9-0-37-2, S Keyworth 4-1-20-2, A Berry 3-0-9-3) sum to exactly all 10
    wickets.
  - ELPM: F Daly 24 (ct A Lloyd b KH Sadiq), J Sheils 17 (b A Lloyd), I
    Wade 14 (ct C Lloyd b I Atkinson), G Young 13 (ct J Taylor b A Lloyd),
    A McCheyne 11 (lbw b C Ralph), S Keyworth 34 not out, P Hewart 20 not
    out; K Hocking, S Dalton, S Carr and A Berry did not bat.
    24+17+14+13+11+34+20 = 133, matching the scorebook's own printed
    batsmen's total exactly. Extras 8, total 141 for 5. West Leigh's
    bowling figures (A Lloyd 11.3-1-66-2, I Atkinson 8-2-23-1, C Ralph
    8-0-24-1, KH Sadiq 5-0-23-1) sum to exactly the 5 wickets. ELPM won by
    5 wickets.

============================================================================
3-Jul-2004: East Lancs Paper Mill CC 1st XI vs Springhead CC
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.05.54.jpg and
2026-09-15 13.06.00.jpg (both innings). Return fixture to 1-May-2004's
match. Both batting orders were significantly wrong on the first pass --
the how-out/bowler/total column was read correctly but matched against
the wrong names, most visibly having G Young batting 3rd instead of J
Wade. Rebuilt from a direct read of the batsmen-names column (the same
technique used throughout this batch), plus the user's own read of both
bowling analyses, neither of which cropped legibly.

  - ELPM: F Daly 50 (ct D Percival b DeHavilland), J Sheils 16 (c&b
    DeHavilland), J Wade 39 (ct Milner b J Cook), G Young 40 (b
    DeHavilland), A McCheyne 4 (b DeHavilland), S Keyworth 7 (b M
    Sweeting), K Hocking 8 not out, P Partington 18 (lbw b M Sweeting), N
    Warne 17 (b M Sweeting), P Hewart 4 not out; S Carr did not bat. A
    McCheyne's own score isn't something the user stated directly -- it's
    the one value that makes 50+16+39+40+4+7+8+18+17+4 = 203 match the
    scorebook's own printed batsmen's total exactly, so it's inferred
    rather than read, the same "reconcile then flag" approach used for
    Degham Hibbert's unidentified batsman earlier in this file. Extras
    26, total 229 for 8. Springhead's bowling figures (K Lees 14-2-46-0,
    DeHavilland 16-2-76-4, J Cook 6-0-54-1, M Sweeting 9-1-38-3) sum to
    exactly the 8 wickets -- K Lees bowled but took none, which is why he
    hadn't shown up in the dismissals at all until the bowling card
    confirmed his figures.
  - Springhead: J Batey 17 (ct J Sheils b S Keyworth), K Fielding 0 (ct J
    Wade b P Hewart), D Percival 8 (b P Hewart), R Shaw 8 (b P Hewart), K
    DeHavilland 0 (c&b P Hewart), K Lees 0 (b P Hewart), A Milner 21 (run
    out, fielder J Wade), J Walmesly 12 (st P Partington b N Warne), J
    Cook 14 (b S Carr), M Sweeting 6 not out.
    17+0+8+8+0+0+21+12+14+6 = 86, eight short of the scorebook's own
    printed batsmen's total of 94 -- left unresolved, same pattern as
    elsewhere in this file. Extras 5, total 99 for 9. ELPM's bowling
    figures (P Hewart 16-7-26-5, S Carr 11-1-25-1, S Keyworth 8-3-23-1, J
    Wade 4-0-10-0, J Sheils 3-1-13-0, N Warne 0.1-0-0-1) sum to exactly 8
    bowler-credited wickets, plus A Milner's run out as the 9th. ELPM won
    by 130 runs.

============================================================================
10-Jul-2004: Robinsons CC vs East Lancs Paper Mill CC 1st XI
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.06.25.jpg and
2026-09-15 13.06.37.jpg (both innings). Return fixture to 24-Apr-2004's
match. Away for ELPM, despite the user's initial ambiguity about which
page belonged to which team -- ELPM's own card just had less-familiar
handwriting on a couple of names/initials than usual, not a genuinely
different team.

  - ELPM: F Daly 3 (b A Hodson), J Sheils 50 (ct A Hodson b N Clarke), K
    Hocking 16 (lbw b E Whitworth), I Wade 11 (lbw b N Clarke), G Young 0
    (b E Whitworth), P Smith 1 (b E Whitworth), T Birtwistle 3 (ct Hughes
    b N Clarke), P Hewart 1 (b E Whitworth), S Dalton 0 (b N Clarke), S
    Carr 0 not out, M Robinson 0 not out. 3+50+16+11+0+1+3+1+0+0+0 = 85,
    matching the scorebook's own printed batsmen's total exactly. Extras
    25, total 110 for 9. Robinsons' bowling figures (A Hodson 9-1-25-1, D
    Faulkner 4-0-22-0, E Whitworth 9-3-25-4, N Clarke 4.4-0-15-4) sum to
    exactly 9 wickets -- S Dalton's dismissal is recorded here as bowled
    (N Clarke) rather than the run out first assumed, since crediting
    Clarke's 4th wicket to him is the only way the bowling analysis and
    the batting card's 9 real dismissals reconcile without a 10th.
  - Robinsons: W Hughes 8 (b P Hewart), L Brook 17 (lbw b P Hewart), M
    Massey 8 (ct I Wade b S Carr), R Hild 20 (ct K Hocking b J Sheils), R
    Congalhor 10 (lbw b P Hewart), A Alletson 5 (ct S Dalton b P Hewart),
    D Faulkner 10 not out, C Betts 1 (b P Hewart), A Hodson 0 (lbw b J
    Sheils), N Clarke 2 (b J Sheils), E Whitworth 0 (b P Hewart).
    8+17+8+20+10+5+10+1+0+2+0 = 81, matching the scorebook's own printed
    batsmen's total exactly (the first-pass read had Massey, Faulkner and
    Betts' scores scrambled, which is what produced an 8-run gap the user
    then closed). Extras 4, total 85 all out. ELPM's bowling figures (P
    Hewart 13.3-4-37-6, S Carr 7-2-15-1, I Wade 3-0-14-0, J Sheils
    3-0-16-3) sum to exactly all 10 wickets. ELPM won by 25 runs.

============================================================================
24-Jul-2004: East Lancs Paper Mill CC 1st XI vs Rochdalians CC
============================================================================

Source images: scorebooks/1xt XI/2004 1st XI/2026-09-15 13.06.45.jpg and
2026-09-15 13.07.09.jpg (both innings). ELPM's third meeting with
Rochdalians this season, following the two May fixtures -- the same pool
of Rochdalians players recurs (N Hayee, M Tayyab, S Rahman, M Iqbal, A
Rauf and G Khan all appear in the earlier matches too).

  - Rochdalians: M Shahid 58 (ct M Robinson b P Hewart), N Hayee 21 (ct P
    Partington b P Hewart), M Tayyab 1 (ct A McCheyne b P Hewart), M Iqbal
    39 (c&b J Wade), S Rahman 32 (lbw b J Wade), A Dar 4 (ct P Hewart b J
    Wade), K Ali 16 (ct I Wade b S Keyworth), G Khan 35 not out, M Buxton
    8 (b S Keyworth), A Rauf 2 (b S Keyworth), T Khan 0 not out.
    58+21+1+39+32+4+16+35+8+2+0 = 216, matching the scorebook's own
    printed batsmen's total exactly. Extras 16, total 232 for 9. ELPM's
    bowling figures (I Wade 3-1-15-0, S Carr 4-1-26-0, P Hewart
    13-2-65-3, S Keyworth 15-2-64-3, J Wade 7-0-51-3) sum to exactly the 9
    real dismissals (P Hewart 3, J Wade 3, S Keyworth 3; no run outs).
  - ELPM: F Daly 1 (ct M Tayyab b T Khan), P Partington 15 (b A Dar), J
    Wade 120 (b G Khan), I Wade 40 (b N Hayee), A McCheyne 11 not out, S
    Keyworth 31 not out; P Hewart, S Carr and M Robinson did not bat.
    1+15+120+40+11+31 = 218, matching the scorebook's own printed
    batsmen's total exactly (the first-pass read had McCheyne's and
    Keyworth's scores swapped). Extras 20, total 238 for 4. Rochdalians'
    bowling figures (S Rahman 0.1-0-0-0, T Khan 3-0-51-1, A Dar 4-0-40-1,
    A Rauf 3-0-24-0, G Khan 7-0-51-1, N Hayee 8-0-69-1) sum to exactly the
    4 real dismissals, matching the bowler credited against each of
    Daly/Partington/J Wade/I Wade above -- N Hayee's wicket (I Wade) was
    initially misread as an ELPM player's name ("Warne") before a closer
    crop of the bowler-name column confirmed it was Rochdalians' own N
    Hayee. ELPM won by 6 wickets.
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
    {
        "id": "ELPM 2nd XI|Littleborough Lake Sides CC 1st XI|04/06/2011",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 2nd XI", "home_team_name": "2nd XI",
        "away_club_id": "Littleborough Lake Sides", "away_club_name": "Littleborough Lake Sides CC",
        "away_team_id": "Littleborough Lake Sides CC 1st XI", "away_team_name": "1st XI",
        "match_date": "04/06/2011",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL",
        "competition_type": "League",
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "Littleborough Lake Sides",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": "Littleborough",
        "toss_won_by_team_id": "Littleborough Lake Sides CC 1st XI",
        "result": "Littleborough Lake Sides CC won by 7 wickets",
        "result_applied_to": "Littleborough Lake Sides CC 1st XI",
        "result_description": "Littleborough Lake Sides CC won by 7 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("K Dodson", 1, wicket_keeper=True), _player("A Redford", 2), _player("D Dwyer", 3),
                _player("A Berry", 4), _player("A Greenwood", 5), _player("D Hadcoft", 6),
                _player("M Young", 7, captain=True), _player("W Francis", 8), _player("A Birtwistle", 9),
                _player("L Birmingham", 10), _player("M Thomson", 11),
            ]},
            {"away_team": [
                _player("N Unknown", 1), _player("A Malik", 2), _player("J Wild", 3),
                _player("I Iqbal", 4), _player("B Hussain", 5), _player("Z Javaid", 6),
                _player("M Hafeez", 7), _player("U Haq", 8), _player("T Jeffs", 9),
                _player("A Hussain", 10), _player("S Hussain", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 126, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 2, "extra_leg_byes": 0, "extra_wides": 7, "extra_no_balls": 1,
                "extra_penalty_runs": 0, "total_extras": 10,
                "bat": [
                    _bat(1, "K Dodson", "b", "S Hussain", None, 9),
                    _bat(2, "A Redford", "b", "B Hussain", None, 7),
                    _bat(3, "D Dwyer", "ct", "M Amin", "Z Javaid", 53),
                    _bat(4, "A Berry", "ct", "M Amin", "I Iqbal", 27),
                    _bat(5, "A Greenwood", "b", "B Hussain", None, 0),
                    _bat(6, "D Hadcoft", "b", "M Amin", None, 14),
                    _bat(7, "M Young", "b", "B Hussain", None, 0),
                    _bat(8, "W Francis", "b", "M Amin", None, 0),
                    _bat(9, "A Birtwistle", "b", "M Amin", None, 3),
                    _bat(10, "L Birmingham", "b", "M Amin", None, 2),
                    _bat(11, "M Thomson", "not out", None, None, 1),
                ],
                "bowl": [
                    _bowl("B Hussain", "13", 2, 57, 3),
                    _bowl("S Hussain", "6", 0, 31, 1),
                    _bowl("M Amin", "8.2", 0, 32, 6),
                    # Bowler's name illegible in the photo; see the
                    # module docstring above.
                    _bowl("Unknown", "2", 1, 4, 0),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Littleborough Lake Sides CC 1st XI", "team_batting_name": "1st XI",
                "runs": 130, "wickets": 3, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 7, "extra_leg_byes": 4, "extra_wides": 3, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 14,
                "bat": [
                    _bat(1, "N Unknown", "b", None, None, 7),
                    _bat(2, "A Malik", "not out", None, None, 100),
                    _bat(3, "J Wild", "st", "M Young", "K Dodson", 3),
                    _bat(4, "I Iqbal", "lbw", None, None, 2),
                    _bat(5, "B Hussain", "not out", None, None, 4),
                    _bat(6, "Z Javaid", "did not bat"),
                    _bat(7, "M Hafeez", "did not bat"),
                    _bat(8, "U Haq", "did not bat"),
                    _bat(9, "T Jeffs", "did not bat"),
                    _bat(10, "A Hussain", "did not bat"),
                    _bat(11, "S Hussain", "did not bat"),
                ],
                "bowl": [
                    _bowl("L Birmingham", "4", 0, 21, 1),
                    _bowl("A Berry", "9", 4, 35, 0),
                    _bowl("M Young", "9", 3, 34, 2),
                    _bowl("A Redford", "2", 0, 23, 0),
                    _bowl("M Thomson", "1", 0, 7, 0),
                    _bowl("A Greenwood", "1", 0, 9, 0),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 2nd XI|Swinton Moorside CC 1st XI|18/06/2011",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 2nd XI", "home_team_name": "2nd XI",
        "away_club_id": "Swinton Moorside", "away_club_name": "Swinton Moorside CC",
        "away_team_id": "Swinton Moorside CC 1st XI", "away_team_name": "1st XI",
        "match_date": "18/06/2011",
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
        "result": "Swinton Moorside CC won by 13 runs",
        "result_applied_to": "Swinton Moorside CC 1st XI",
        "result_description": "Swinton Moorside CC won by 13 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"away_team": [
                _player("T Walker", 1), _player("D Davies", 2), _player("F Blakley", 3),
                _player("T Staniford", 4), _player("A Eckersley", 5), _player("M Howard", 6),
                _player("S Davies", 7), _player("M Billingham", 8), _player("C Carter", 9),
                _player("R Curran", 10), _player("M Winstanley", 11),
            ]},
            {"home_team": [
                _player("K Dodson", 1, wicket_keeper=True), _player("C Holt", 2), _player("D Dwyer", 3),
                _player("A Berry", 4), _player("C Greaves", 5), _player("A Redford", 6),
                _player("N Warne", 7), _player("S Dwyer", 8), _player("D Hadcroft", 9),
                _player("M Young", 10, captain=True), _player("L Birmingham", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Swinton Moorside CC 1st XI", "team_batting_name": "1st XI",
                "runs": 109, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 4, "extra_leg_byes": 1, "extra_wides": 13, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 18,
                "bat": [
                    _bat(1, "T Walker", "b", "M Young", None, 15),
                    _bat(2, "D Davies", "lbw", "A Berry", None, 11),
                    _bat(3, "F Blakley", "b", "M Young", None, 6),
                    _bat(4, "T Staniford", "ct", "M Young", "C Greaves", 0),
                    _bat(5, "A Eckersley", "ct", "A Berry", "C Holt", 1),
                    _bat(6, "M Howard", "b", "M Young", None, 26),
                    _bat(7, "S Davies", "ct", "A Berry", "S Dwyer", 0),
                    _bat(8, "M Billingham", "ct", "M Young", "A Redford", 22),
                    _bat(9, "C Carter", "b", "S Dwyer", None, 9),
                    _bat(10, "R Curran", "not out", None, None, 1),
                    _bat(11, "M Winstanley", "b", "S Dwyer", None, 0),
                ],
                "bowl": [
                    # Maidens not confidently read; see the module
                    # docstring above.
                    _bowl("L Birmingham", "6.2", 0, 25, 0),
                    _bowl("A Berry", "11", 3, 31, 3),
                    _bowl("M Young", "9", 0, 38, 5),
                    _bowl("S Dwyer", "4", 2, 10, 2),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 96, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                # Total extras (9) confirmed; the byes/leg-byes/wides/
                # no-balls split wasn't attempted -- see the module
                # docstring above.
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 9, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 9,
                "bat": [
                    _bat(1, "K Dodson", "ct", "M Billingham", "D Davies", 19),
                    _bat(2, "C Holt", "b", "C Winstanley", None, 9),
                    _bat(3, "D Dwyer", "ct", "M Billingham", "S Carter", 4),
                    _bat(4, "A Berry", "ct", "C Winstanley", "S Davies", 37),
                    _bat(5, "C Greaves", "b", "M Billingham", None, 0),
                    _bat(6, "A Redford", "ct", "C Winstanley", "M Billingham", 3),
                    _bat(7, "N Warne", "run out", None, "S Davies", 1),
                    _bat(8, "S Dwyer", "b", "C Winstanley", None, 0),
                    _bat(9, "D Hadcroft", "b", "M Billingham", None, 0),
                    _bat(10, "M Young", "b", "C Winstanley", None, 13),
                    _bat(11, "L Birmingham", "not out", None, None, 1),
                ],
                "bowl": [
                    _bowl("R Curran", "5", 1, 14, 0),
                    _bowl("M Billingham", "13", 4, 35, 4),
                    _bowl("C Winstanley", "10", 1, 39, 5),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 2nd XI|Westhoughton CC 1st XI|25/06/2011",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 2nd XI", "home_team_name": "2nd XI",
        "away_club_id": "Westhoughton", "away_club_name": "Westhoughton CC",
        "away_team_id": "Westhoughton CC 1st XI", "away_team_name": "1st XI",
        "match_date": "25/06/2011",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL",
        "competition_type": "League",
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": "Westhoughton",
        "toss_won_by_team_id": "Westhoughton CC 1st XI",
        "result": "Match tied",
        "result_applied_to": None,
        "result_description": "Match tied: ELPM 204 for 5, Westhoughton CC 204 for 9",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("K Dodson", 1, wicket_keeper=True), _player("A Greenwood", 2), _player("D Dwyer", 3),
                _player("A Berry", 4), _player("D Scott", 5), _player("C Greaves", 6),
                _player("M Young", 7, captain=True), _player("L Birmingham", 8), _player("D Hadcroft", 9),
                _player("M Thomson", 10), _player("W Francis", 11),
            ]},
            {"away_team": [
                _player("J Yearn", 1), _player("C Honour", 2), _player("M Horrocks", 3),
                _player("J Blair", 4), _player("J Berry", 5), _player("K Hodgkiss", 6),
                _player("M Fanning", 7), _player("O Turner", 8), _player("S Miller", 9),
                _player("D Higham", 10), _player("D Fletcher", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 204, "wickets": 5, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 3, "extra_leg_byes": 1, "extra_wides": 3, "extra_no_balls": 3,
                "extra_penalty_runs": 0, "total_extras": 10,
                "bat": [
                    _bat(1, "K Dodson", "not out", None, None, 89),
                    _bat(2, "A Greenwood", "run out", None, "K Dodson", 12),
                    _bat(3, "D Dwyer", "ct", "K Hodgkiss", "D Higham", 31),
                    _bat(4, "A Berry", "b", "C Honour", None, 18),
                    _bat(5, "D Scott", "b", "C Honour", None, 0),
                    _bat(6, "C Greaves", "b", "J Blair", None, 36),
                    _bat(7, "M Young", "not out", None, None, 8),
                    _bat(8, "L Birmingham", "did not bat"),
                    _bat(9, "D Hadcroft", "did not bat"),
                    _bat(10, "M Thomson", "did not bat"),
                    _bat(11, "W Francis", "did not bat"),
                ],
                "bowl": [
                    _bowl("J Blair", "13", 0, 65, 1),
                    _bowl("M Fanning", "10", 2, 26, 0),
                    _bowl("K Hodgkiss", "6", 0, 34, 1),
                    _bowl("O Turner", "6", 2, 16, 0),
                    _bowl("C Honour", "6", 1, 26, 2),
                    _bowl("D Higham", "2", 0, 21, 0),
                    _bowl("J Berry", "2", 0, 13, 0),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Westhoughton CC 1st XI", "team_batting_name": "1st XI",
                "runs": 204, "wickets": 9, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 7, "extra_leg_byes": 1, "extra_wides": 8, "extra_no_balls": 3,
                "extra_penalty_runs": 0, "total_extras": 19,
                "bat": [
                    _bat(1, "J Yearn", "ct", "A Berry", "M Young", 38),
                    _bat(2, "C Honour", "ct", "A Berry", "C Greaves", 15),
                    _bat(3, "M Horrocks", "ct", "L Birmingham", "D Dwyer", 0),
                    _bat(4, "J Blair", "ct", "M Young", "D Dwyer", 20),
                    _bat(5, "J Berry", "ct", "A Berry", "D Dwyer", 0),
                    _bat(6, "K Hodgkiss", "b", "M Young", None, 3),
                    _bat(7, "M Fanning", "b", "C Greaves", None, 47),
                    _bat(8, "O Turner", "ct", "A Berry", "C Greaves", 30),
                    _bat(9, "S Miller", "run out", None, "A Berry", 31),
                    _bat(10, "D Higham", "did not bat"),
                    _bat(11, "D Fletcher", "did not bat"),
                ],
                "bowl": [
                    _bowl("A Berry", "18", 3, 44, 4),
                    _bowl("L Birmingham", "14", 1, 71, 1),
                    _bowl("M Thomson", "1", 0, 21, 0),
                    _bowl("M Young", "10", 0, 42, 2),
                    _bowl("C Greaves", "2", 0, 8, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 2nd XI|Littleborough Lakeside CC 1st XI|02/07/2011",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 2nd XI", "home_team_name": "2nd XI",
        "away_club_id": "Littleborough Lakeside", "away_club_name": "Littleborough Lakeside CC",
        "away_team_id": "Littleborough Lakeside CC 1st XI", "away_team_name": "1st XI",
        "match_date": "02/07/2011",
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
        "result": "Littleborough Lakeside CC won by 8 wickets",
        "result_applied_to": "Littleborough Lakeside CC 1st XI",
        "result_description": "Littleborough Lakeside CC won by 8 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("K Dodson", 1, wicket_keeper=True), _player("A Greenwood", 2), _player("D Dwyer", 3),
                _player("A Berry", 4), _player("D Scott", 5), _player("C Holt", 6),
                _player("N Warne", 7), _player("D Hadcroft", 8), _player("L Birmingham", 9),
                _player("M Thomson", 10), _player("A Redford", 11),
            ]},
            {"away_team": [
                _player("S Rashid", 1), _player("N Dadd", 2), _player("I Iqbal", 3, captain=True),
                _player("N Sadiq", 4),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 136, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 2, "extra_leg_byes": 3, "extra_wides": 4, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 9,
                "bat": [
                    _bat(1, "K Dodson", "ct", "S Hussain", "F Rashid", 11),
                    _bat(2, "A Greenwood", "ct", "B Hussain", "N Dadd", 8),
                    _bat(3, "D Dwyer", "ct", "N Sadiq", "H Rashid", 17),
                    _bat(4, "A Berry", "b", "B Hussain", None, 8),
                    _bat(5, "D Scott", "b", "U Haq", None, 23),
                    _bat(6, "C Holt", "b", "N Sadiq", None, 5),
                    _bat(7, "N Warne", "ct", "U Haq", "N Dadd", 12),
                    _bat(8, "D Hadcroft", "not out", None, None, 29),
                    _bat(9, "L Birmingham", "run out", None, "D Hadcroft", 1),
                    _bat(10, "M Thomson", "b", "A Hussain", None, 0),
                    _bat(11, "A Redford", "b", "B Hussain", None, 13),
                ],
                "bowl": [
                    _bowl("B Hussain", "9.3", 2, 32, 3),
                    _bowl("S Hussain", "5", 0, 21, 1),
                    _bowl("N Sadiq", "9", 2, 29, 2),
                    _bowl("U Haq", "6", 0, 24, 2),
                    _bowl("A Hussain", "5", 0, 23, 1),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Littleborough Lakeside CC 1st XI", "team_batting_name": "1st XI",
                "runs": 139, "wickets": 2, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 1, "extra_leg_byes": 2, "extra_wides": 14, "extra_no_balls": 4,
                "extra_penalty_runs": 0, "total_extras": 18,
                "bat": [
                    _bat(1, "S Rashid", "not out", None, None, 37),
                    _bat(2, "N Dadd", "b", "L Birmingham", None, 14),
                    _bat(3, "I Iqbal", "lbw", "A Berry", None, 1),
                    _bat(4, "N Sadiq", "not out", None, None, 69),
                ],
                "bowl": [
                    _bowl("L Birmingham", "7", 0, 27, 1),
                    _bowl("A Berry", "11", 1, 37, 1),
                    _bowl("A Greenwood", "3", 0, 35, 0),
                    _bowl("A Redford", "3", 0, 25, 0),
                    _bowl("D Hadcroft", "2.2", 0, 11, 0),
                    _bowl("C Holt", "1", 0, 4, 0),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 2nd XI|Thornham CC 1st XI|06/08/2011",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 2nd XI", "home_team_name": "2nd XI",
        "away_club_id": "Thornham", "away_club_name": "Thornham CC",
        "away_team_id": "Thornham CC 1st XI", "away_team_name": "1st XI",
        "match_date": "06/08/2011",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL",
        "competition_type": "League",
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": "Thornham",
        "toss_won_by_team_id": "Thornham CC 1st XI",
        "result": "Thornham CC won by 8 wickets",
        "result_applied_to": "Thornham CC 1st XI",
        "result_description": "Thornham CC won by 8 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("K Dodson", 1, wicket_keeper=True), _player("A Redford", 2), _player("G Young", 3),
                _player("A Berry", 4), _player("D Scott", 5), _player("D Dwyer", 6),
                _player("C Holt", 7), _player("M Young", 8, captain=True), _player("D Hadcroft", 9),
                _player("D Pearson", 10), _player("A Birtwistle", 11),
            ]},
            {"away_team": [
                _player("J Carnegie", 1), _player("D Harrop", 2), _player("S Mohammed", 3),
                _player("R Whitehouse", 4), _player("J Clarke", 5), _player("M Fitzpatrick", 6),
                _player("M Chadderton", 7), _player("D Parr", 8), _player("M Turvey", 9),
                _player("P Speedy", 10), _player("A Towler", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 91, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 1, "extra_wides": 3, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 4,
                "bat": [
                    _bat(1, "K Dodson", "b", "J Clarke", None, 12),
                    _bat(2, "A Redford", "b", "J Clarke", None, 4),
                    _bat(3, "G Young", "ct", "J Clarke", "A Towler", 15),
                    _bat(4, "A Berry", "b", "J Clarke", None, 19),
                    _bat(5, "D Scott", "b", "M Fitzpatrick", None, 13),
                    _bat(6, "D Dwyer", "ct", "M Fitzpatrick", "D Harrop", 1),
                    _bat(7, "C Holt", "ct", "M Fitzpatrick", "M Turvey", 12),
                    _bat(8, "M Young", "b", "M Fitzpatrick", None, 4),
                    _bat(9, "D Hadcroft", "b", "J Clarke", None, 1),
                    _bat(10, "D Pearson", "ct", "M Fitzpatrick", "P Speedy", 6),
                    _bat(11, "A Birtwistle", "not out", None, None, 0),
                ],
                "bowl": [
                    _bowl("M Turvey", "6", 0, 34, 0),
                    _bowl("J Clarke", "12", 1, 40, 5),
                    _bowl("M Fitzpatrick", "7", 1, 14, 5),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Thornham CC 1st XI", "team_batting_name": "1st XI",
                "runs": 101, "wickets": 2, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 1, "extra_leg_byes": 1, "extra_wides": 0, "extra_no_balls": 1,
                "extra_penalty_runs": 0, "total_extras": 3,
                "bat": [
                    _bat(1, "J Carnegie", "b", "M Young", None, 1),
                    _bat(2, "D Harrop", "ct", "A Berry", None, 1),
                    _bat(3, "S Mohammed", "not out", None, None, 76),
                    _bat(4, "R Whitehouse", "not out", None, None, 20),
                    _bat(5, "J Clarke", "did not bat"),
                    _bat(6, "M Fitzpatrick", "did not bat"),
                    _bat(7, "M Chadderton", "did not bat"),
                    _bat(8, "D Parr", "did not bat"),
                    _bat(9, "M Turvey", "did not bat"),
                    _bat(10, "P Speedy", "did not bat"),
                    _bat(11, "A Towler", "did not bat"),
                ],
                "bowl": [
                    _bowl("A Berry", "7", 2, 31, 1),
                    _bowl("M Young", "5", 0, 35, 1),
                    _bowl("G Young", "2", 0, 3, 0),
                    _bowl("A Redford", "1", 0, 7, 0),
                    _bowl("A Birtwistle", "0.3", 0, 12, 0),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "Failsworth CC 1st XI|ELPM 2nd XI|13/08/2011",
        "home_club_id": "Failsworth", "home_club_name": "Failsworth CC",
        "home_team_id": "Failsworth CC 1st XI", "home_team_name": "1st XI",
        "away_club_id": "ELPM", "away_club_name": "East Lancs Paper Mill CC",
        "away_team_id": "ELPM 2nd XI", "away_team_name": "2nd XI",
        "match_date": "13/08/2011",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL",
        "competition_type": "League",
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "Failsworth",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": "ELPM",
        "toss_won_by_team_id": "ELPM 2nd XI",
        "result": "Failsworth CC won by 4 runs",
        "result_applied_to": "Failsworth CC 1st XI",
        "result_description": "Failsworth CC won by 4 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("J Turnbull", 1), _player("J Davies", 2), _player("T Wood", 3),
                _player("A Trotter", 4), _player("N Reed", 5), _player("T Shepherdson", 6),
                _player("I Wilson", 7, captain=True), _player("R Stacey", 8), _player("G Reeves", 9),
                _player("C Shenton", 10), _player("B Beresconi", 11),
            ]},
            {"away_team": [
                _player("C Holt", 1), _player("A Berry", 2), _player("A Redford", 3),
                _player("D Dwyer", 4), _player("G Young", 5), _player("D Hadcroft", 6),
                _player("D Pearson", 7), _player("A Wilkinson", 8), _player("L Birmingham", 9),
                _player("M Young", 10, captain=True), _player("A Birtwistle", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Failsworth CC 1st XI", "team_batting_name": "1st XI",
                "runs": 109, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 4, "extra_leg_byes": 1, "extra_wides": 4, "extra_no_balls": 1,
                "extra_penalty_runs": 0, "total_extras": 10,
                "bat": [
                    _bat(1, "J Turnbull", "ct", "A Berry", "G Young", 0),
                    _bat(2, "J Davies", "b", "A Berry", None, 17),
                    _bat(3, "T Wood", "lbw", "A Berry", None, 0),
                    _bat(4, "A Trotter", "b", "L Birmingham", None, 4),
                    _bat(5, "N Reed", "run out", None, "G Young", 13),
                    _bat(6, "T Shepherdson", "b", "M Young", None, 38),
                    _bat(7, "I Wilson", "ct", "A Redford", "D Dwyer", 24),
                    _bat(8, "R Stacey", "b", "M Young", None, 3),
                    _bat(9, "G Reeves", "lbw", "A Berry", None, 0),
                    _bat(10, "C Shenton", "b", "M Young", None, 0),
                    _bat(11, "B Beresconi", "not out", None, None, 0),
                ],
                "bowl": [
                    _bowl("A Berry", "15", 2, 49, 4),
                    _bowl("L Birmingham", "7", 0, 15, 1),
                    _bowl("A Redford", "5", 0, 38, 1),
                    _bowl("M Young", "2.1", 0, 2, 3),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 105, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 4, "extra_leg_byes": 1, "extra_wides": 1, "extra_no_balls": 1,
                "extra_penalty_runs": 0, "total_extras": 7,
                "bat": [
                    _bat(1, "C Holt", "b", "B Beresconi", None, 21),
                    _bat(2, "A Berry", "b", "G Reeves", None, 23),
                    _bat(3, "A Redford", "lbw", "G Reeves", None, 1),
                    _bat(4, "D Dwyer", "st", "G Reeves", "J Turnbull", 16),
                    _bat(5, "G Young", "ct", "T Shepherdson", "B Beresconi", 1),
                    _bat(6, "D Hadcroft", "b", "G Reeves", None, 1),
                    _bat(7, "D Pearson", "not out", None, None, 12),
                    _bat(8, "A Wilkinson", "lbw", "G Reeves", None, 0),
                    _bat(9, "L Birmingham", "lbw", "G Reeves", None, 18),
                    _bat(10, "M Young", "b", "G Reeves", None, 6),
                    _bat(11, "A Birtwistle", "b", "G Reeves", None, 0),
                ],
                "bowl": [
                    _bowl("I Wilson", "7", 1, 27, 0),
                    _bowl("B Beresconi", "7", 1, 24, 1),
                    _bowl("G Reeves", "9.1", 1, 34, 8),
                    _bowl("T Shepherdson", "4", 3, 16, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 2nd XI|Roe Green CC 1st XI|03/09/2011",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 2nd XI", "home_team_name": "2nd XI",
        "away_club_id": "Roe Green", "away_club_name": "Roe Green CC",
        "away_team_id": "Roe Green CC 1st XI", "away_team_name": "1st XI",
        "match_date": "03/09/2011",
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
        "result": None,
        "result_applied_to": None,
        "result_description": "Abandoned (rain) -- ELPM 50 for 6, chasing Roe Green's 134",
        "status": "Abandoned",
        "last_updated": None,
        "players": [
            {"away_team": [
                _player("R Bradshaw", 1), _player("R Green", 2), _player("P Shannon", 3),
                _player("N Pine", 4), _player("T Vast", 5), _player("J Needham", 6, wicket_keeper=True),
                _player("L Needham", 7, captain=True), _player("N Pane", 8), _player("M Canning", 9),
                _player("M Buckleton", 10),
            ]},
            {"home_team": [
                _player("A Redford", 1), _player("D Scott", 2), _player("D Dwyer", 3),
                _player("N Warne", 4, wicket_keeper=True), _player("L Birmingham", 5), _player("D Pearson", 6),
                _player("A Wilkinson", 7), _player("D Hadcroft", 8), _player("A Birtwistle", 9),
                _player("B Birtwistle", 10), _player("W Francis", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Roe Green CC 1st XI", "team_batting_name": "1st XI",
                "runs": 134, "wickets": 9, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 4, "extra_leg_byes": 3, "extra_wides": 12, "extra_no_balls": 7,
                "extra_penalty_runs": 0, "total_extras": 26,
                "bat": [
                    _bat(1, "R Bradshaw", "ct and b", "D Pearson", None, 20),
                    _bat(2, "R Green", "ct", "A Redford", "N Warne", 5),
                    _bat(3, "P Shannon", "b", "D Pearson", None, 15),
                    _bat(4, "N Pine", "st", "D Hadcroft", "N Warne", 0),
                    _bat(5, "T Vast", "st", "B Birtwistle", "N Warne", 33),
                    _bat(6, "J Needham", "b", "B Birtwistle", None, 14),
                    _bat(7, "L Needham", "b", "L Birmingham", None, 14),
                    _bat(8, "N Pane", "ct", "B Birtwistle", "N Warne", 7),
                    _bat(9, "M Canning", "ct", "B Birtwistle", "L Needham", 0),
                    _bat(10, "M Buckleton", "not out", None, None, 0),
                ],
                "bowl": [
                    _bowl("A Redford", "9", 3, 30, 1),
                    _bowl("L Birmingham", "12", 1, 25, 1),
                    _bowl("D Pearson", "10", 1, 33, 2),
                    _bowl("D Hadcroft", "6", 2, 19, 1),
                    _bowl("B Birtwistle", "7.1", 1, 20, 4),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 50, "wickets": 6, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 4, "extra_leg_byes": 1, "extra_wides": 2, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 7,
                "bat": [
                    _bat(1, "A Redford", "run out", None, None, 2),
                    _bat(2, "D Scott", "b", "J Needham", None, 1),
                    _bat(3, "D Dwyer", "lbw", "J Needham", None, 0),
                    _bat(4, "N Warne", "ct", "R Green", "R Bradshaw", 8),
                    _bat(5, "L Birmingham", "ct", "L Needham", "M Buckleton", 21),
                    _bat(6, "D Pearson", "not out", None, None, 11),
                    _bat(7, "A Wilkinson", "st", "L Needham", "N Pine", 0),
                    _bat(8, "D Hadcroft", "did not bat"),
                    _bat(9, "A Birtwistle", "did not bat"),
                    _bat(10, "B Birtwistle", "did not bat"),
                    _bat(11, "W Francis", "did not bat"),
                ],
                "bowl": [
                    _bowl("J Needham", "14", 8, 11, 2),
                    _bowl("M Buckleton", "6", 1, 9, 0),
                    _bowl("R Green", "8", 4, 12, 1),
                    _bowl("L Needham", "4", 0, 11, 2),
                    _bowl("M Canning", "3", 1, 2, 0),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 2nd XI|Westhoughton CC 1st XI|11/09/2011",
        "home_club_id": "Westhoughton", "home_club_name": "Westhoughton CC",
        "home_team_id": "Westhoughton CC 1st XI", "home_team_name": "1st XI",
        "away_club_id": "ELPM", "away_club_name": "East Lancs Paper Mill CC",
        "away_team_id": "ELPM 2nd XI", "away_team_name": "2nd XI",
        "match_date": "11/09/2011",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL",
        "competition_type": "League",
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "Westhoughton",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": "Westhoughton",
        "toss_won_by_team_id": "Westhoughton CC 1st XI",
        "result": "Westhoughton CC won by 8 wickets",
        "result_applied_to": "Westhoughton CC 1st XI",
        "result_description": "Westhoughton CC won by 8 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"away_team": [
                _player("K Dodson", 1, wicket_keeper=True), _player("P Partington", 2), _player("A Redford", 3),
                _player("G Young", 4), _player("L Birmingham", 5), _player("D Dwyer", 6),
                _player("D Pearson", 7), _player("M Young", 8, captain=True), _player("D Hadcroft", 9),
                _player("B Birtwistle", 10), _player("A Birtwistle", 11),
            ]},
            {"home_team": [
                _player("H Entwistle", 1), _player("O Dixon", 2), _player("G Green", 3),
                _player("C Honour", 4), _player("C Trom", 5), _player("B Naylor", 6, captain=True),
                _player("L Ashcroft", 7, wicket_keeper=True), _player("S Ashcroft", 8), _player("O Turner", 9),
                _player("J Blair", 10), _player("J Yearn", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 2nd XI", "team_batting_name": "2nd XI",
                "runs": 103, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 5, "extra_leg_byes": 4, "extra_wides": 1, "extra_no_balls": 2,
                "extra_penalty_runs": 0, "total_extras": 12,
                "bat": [
                    _bat(1, "K Dodson", "b", "S Ashcroft", None, 22),
                    _bat(2, "P Partington", "ct", "J Blair", "J Yearn", 0),
                    _bat(3, "A Redford", "b", "J Blair", None, 4),
                    _bat(4, "G Young", "lbw", "S Ashcroft", None, 25),
                    _bat(5, "L Birmingham", "not out", None, None, 20),
                    _bat(6, "D Dwyer", "ct", "O Turner", "H Entwistle", 8),
                    _bat(7, "D Pearson", "lbw", "O Turner", None, 10),
                    _bat(8, "M Young", "ct", "C Honour", "G Green", 0),
                    _bat(9, "D Hadcroft", "b", "O Turner", None, 1),
                    _bat(10, "B Birtwistle", "b", "O Turner", None, 0),
                    _bat(11, "A Birtwistle", "run out", None, None, 1),
                ],
                "bowl": [
                    _bowl("S Ashcroft", "15", 3, 44, 1),
                    _bowl("J Blair", "11", 1, 36, 3),
                    _bowl("O Turner", "6", 2, 10, 5),
                    _bowl("C Honour", "2", 0, 4, 1),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Westhoughton CC 1st XI", "team_batting_name": "1st XI",
                "runs": 106, "wickets": 2, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 3, "extra_leg_byes": 1, "extra_wides": 3, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 7,
                "bat": [
                    _bat(1, "H Entwistle", "b", "M Young", None, 12),
                    _bat(2, "O Dixon", "st", "A Redford", "P Partington", 30),
                    _bat(3, "G Green", "not out", None, None, 53),
                    _bat(4, "C Honour", "not out", None, None, 4),
                    _bat(5, "C Trom", "did not bat"),
                    _bat(6, "B Naylor", "did not bat"),
                    _bat(7, "L Ashcroft", "did not bat"),
                    _bat(8, "S Ashcroft", "did not bat"),
                    _bat(9, "O Turner", "did not bat"),
                    _bat(10, "J Blair", "did not bat"),
                    _bat(11, "J Yearn", "did not bat"),
                ],
                "bowl": [
                    _bowl("M Young", "14.1", 1, 63, 1),
                    _bowl("L Birmingham", "7", 2, 16, 0),
                    _bowl("D Pearson", "5", 1, 20, 0),
                    _bowl("A Redford", "2", 0, 18, 1),
                    _bowl("B Birtwistle", "0.5", 0, 5, 0),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Robinsons 1st XI|24/04/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Robinsons", "away_club_name": "Robinsons CC",
        "away_team_id": "Robinsons 1st XI", "away_team_name": "1st XI",
        "match_date": "24/04/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Lost by 30 runs",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "Robinsons CC won by 30 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("A McCheyne", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("N Warne", 6),
                _player("A Berry", 7), _player("P Hewart", 8), _player("S Dalton", 9),
                _player("M Robinson", 10, wicket_keeper=True), _player("A Openshaw", 11),
            ]},
            {"away_team": [
                _player("M Bamford", 1), _player("B Hughes", 2), _player("D Smith", 3),
                _player("L Brook", 4), _player("P Diggle", 5), _player("D Lyons", 6),
                _player("A Alletson", 7), _player("E Whitworth", 8), _player("O Williams", 9),
                _player("J Glover", 10), _player("M Brown", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Robinsons 1st XI", "team_batting_name": "1st XI",
                "runs": 150, "wickets": 8, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 3, "extra_leg_byes": 1, "extra_wides": 10, "extra_no_balls": 1,
                "extra_penalty_runs": 0, "total_extras": 15,
                "bat": [
                    _bat(1, "M Bamford", "ct", "P Hewart", "M Robinson", 0),
                    _bat(2, "B Hughes", "lbw", "A Berry", None, 36),
                    _bat(3, "D Smith", "b", "I Wade", None, 21),
                    _bat(4, "L Brook", "ct", "S Dalton", "N Warne", 28),
                    _bat(5, "P Diggle", "ct", "A Berry", "J Sheils", 3),
                    _bat(6, "D Lyons", "lbw", "S Dalton", None, 2),
                    _bat(7, "A Alletson", "not out", None, None, 28),
                    _bat(8, "E Whitworth", "ct", "S Dalton", "I Wade", 2),
                    _bat(9, "O Williams", "ct", "I Wade", "A Berry", 9),
                    _bat(10, "J Glover", "not out", None, None, 6),
                    _bat(11, "M Brown", "did not bat"),
                ],
                "bowl": [
                    _bowl("P Hewart", "10", 2, 22, 1),
                    _bowl("A Openshaw", "7", 2, 22, 0),
                    _bowl("I Wade", "9", 1, 28, 2),
                    _bowl("A Berry", "10", 2, 30, 2),
                    _bowl("S Dalton", "9", 1, 44, 3),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 120, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                # byes/leg-byes/wides/no-balls as corrected by the user; the
                # component runs are 6 short of the printed total -- see the
                # module docstring above.
                "extra_byes": 11, "extra_leg_byes": 5, "extra_wides": 3, "extra_no_balls": 1,
                "extra_penalty_runs": 0, "total_extras": 20,
                "bat": [
                    _bat(1, "F Daly", "lbw", "D Smith", None, 19),
                    _bat(2, "J Sheils", "lbw", "E Whitworth", None, 13),
                    _bat(3, "A McCheyne", "run out", None, None, 1),
                    _bat(4, "I Wade", "ct", "E Whitworth", "M Bamford", 0),
                    _bat(5, "G Young", "ct", "M Brown", "M Bamford", 23),
                    _bat(6, "N Warne", "ct", "E Whitworth", "O Williams", 1),
                    _bat(7, "A Berry", "b", "M Brown", None, 15),
                    _bat(8, "P Hewart", "ct", "E Whitworth", "O Williams", 11),
                    _bat(9, "S Dalton", "b", "E Whitworth", None, 4),
                    _bat(10, "M Robinson", "ct", "E Whitworth", "O Williams", 6),
                    _bat(11, "A Openshaw", "not out", None, None, 1),
                ],
                "bowl": [
                    _bowl("E Whitworth", "16.5", 2, 51, 5),
                    _bowl("D Smith", "12", 2, 28, 2),
                    _bowl("M Brown", "4", 0, 25, 2),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Springhead 1st XI|01/05/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Springhead", "away_club_name": "Springhead CC",
        "away_team_id": "Springhead 1st XI", "away_team_name": "1st XI",
        "match_date": "01/05/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Lost by 6 wickets",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "Springhead CC won by 6 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("A McCheyne", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("N Warne", 6),
                _player("D Woodward", 7), _player("A Berry", 8), _player("P Hewart", 9),
                _player("S Dalton", 10), _player("M Robinson", 11, wicket_keeper=True),
            ]},
            {"away_team": [
                _player("A Plat", 1), _player("S Rice", 2), _player("R Shaw", 3),
                _player("T DeVillain", 4), _player("K Fielding", 5), _player("K Lees", 6),
                _player("J Cook", 7), _player("J Batey", 8), _player("M O'Robert", 9),
                _player("M Sweetin", 10), _player("A Milner", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 87, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                # total (7) confirmed; byes/leg-byes/wides/no-balls split
                # wasn't attempted -- see the module docstring above.
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 7, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 7,
                "bat": [
                    _bat(1, "F Daly", "c&b", "T DeHaviland", None, 8),
                    _bat(2, "J Sheils", "lbw", "K Lees", None, 31),
                    _bat(3, "A McCheyne", "ct", "T DeHaviland", "B Milner", 1),
                    _bat(4, "I Wade", "b", "T DeHaviland", None, 15),
                    _bat(5, "G Young", None, None, None, 1),
                    _bat(6, "N Warne", "ct", "T DeHaviland", "S Rice", 3),
                    _bat(7, "D Woodward", "b", "K Lees", None, 1),
                    _bat(8, "A Berry", "ct", "K Lees", "J Beaty", 6),
                    _bat(9, "P Hewart", "not out", None, None, 14),
                    _bat(10, "S Dalton", "b", "T DeHaviland", None, 0),
                    _bat(11, "M Robinson", "b", "K Lees", None, 0),
                ],
                "bowl": [
                    _bowl("K Lees", "15.4", 7, 31, 4),
                    _bowl("T DeHaviland", "13", 3, 40, 5),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Springhead 1st XI", "team_batting_name": "1st XI",
                "runs": 88, "wickets": 4, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 5, "extra_wides": 2, "extra_no_balls": 1,
                "extra_penalty_runs": 0, "total_extras": 8,
                "bat": [
                    _bat(1, "A Plat", "lbw", "J Sheils", None, 23),
                    _bat(2, "S Rice", "ct", "J Sheils", "M Robinson", 9),
                    _bat(3, "R Shaw", "not out", None, None, 39),
                    _bat(4, "T DeVillain", "b", "A Berry", None, 0),
                    _bat(5, "K Fielding", "lbw", "A Berry", None, 9),
                    _bat(6, "K Lees", "not out", None, None, 9),
                    _bat(7, "J Cook", "did not bat"),
                    _bat(8, "J Batey", "did not bat"),
                    _bat(9, "M O'Robert", "did not bat"),
                    _bat(10, "M Sweetin", "did not bat"),
                    _bat(11, "A Milner", "did not bat"),
                ],
                "bowl": [
                    _bowl("P Hewart", "8", 4, 8, 0),
                    _bowl("D Woodward", "5", 0, 12, 0),
                    _bowl("J Sheils", "6", 2, 18, 2),
                    _bowl("A Berry", "6", 2, 18, 2),
                    _bowl("S Dalton", "3.1", 1, 14, 0),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "Fothergill and Harvey 1st XI|ELPM 1st XI|08/05/2004",
        "home_club_id": "Fothergill and Harvey", "home_club_name": "Fothergill & Harvey CC",
        "home_team_id": "Fothergill and Harvey 1st XI", "home_team_name": "1st XI",
        "away_club_id": "ELPM", "away_club_name": "East Lancs Paper Mill CC",
        "away_team_id": "ELPM 1st XI", "away_team_name": "1st XI",
        "match_date": "08/05/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "Fothergill and Harvey",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Won by 176 runs",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 176 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("S Toohey", 1), _player("S Haid", 2), _player("J Edmondson", 3),
                _player("Sadid", 4), _player("K Denhurst", 5), _player("M Croney", 6),
                _player("Kalid", 7), _player("D McWilliams", 8), _player("Saleem", 9),
                _player("G McWilliam", 10), _player("J Fallon", 11),
            ]},
            {"away_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("A McCheyne", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("N Warne", 6),
                _player("S Dalton", 7), _player("A Berry", 8), _player("P Hewart", 9),
                _player("M Robinson", 10, wicket_keeper=True), _player("M Young", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 270, "wickets": 4, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                # total (23) confirmed by arithmetic; byes/leg-byes/wides/
                # no-balls split wasn't attempted -- see the module
                # docstring above.
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 23, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 23,
                "bat": [
                    _bat(1, "F Daly", "ct", "G McWilliam", "Khalid", 0),
                    _bat(2, "J Sheils", "ct", "G McWilliam", "J Fallon", 104),
                    _bat(3, "A McCheyne", "b", "Saleem", None, 0),
                    _bat(4, "I Wade", "ct", "Shajid", "Saleem", 123),
                    _bat(5, "G Young", "not out", None, None, 20),
                    _bat(6, "N Warne", "did not bat"),
                    _bat(7, "S Dalton", "did not bat"),
                    _bat(8, "A Berry", "did not bat"),
                    _bat(9, "P Hewart", "did not bat"),
                    _bat(10, "M Robinson", "did not bat"),
                    _bat(11, "M Young", "did not bat"),
                ],
                "bowl": [
                    _bowl("G McWilliam", "6.1", 1, 41, 2),
                    _bowl("Saleem", "10", 0, 57, 1),
                    _bowl("Shajid", "5", 0, 34, 1),
                    _bowl("J Edmondson", "5", 0, 44, 0),
                    _bowl("M Croney", "6.1", 1, 34, 0),
                    _bowl("Shait", "6", 0, 25, 0),
                    _bowl("K Denhurst", "2", 0, 26, 0),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Fothergill and Harvey 1st XI", "team_batting_name": "1st XI",
                "runs": 94, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 8, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 8,
                "bat": [
                    _bat(1, "S Toohey", "ct", "P Hewart", "G Young", 0),
                    _bat(2, "S Haid", "lbw", "P Hewart", None, 1),
                    _bat(3, "J Edmondson", "b", "S Dalton", None, 6),
                    _bat(4, "Sadid", "st", "S Dalton", "M Robinson", 24),
                    _bat(5, "K Denhurst", "ct", "P Hewart", "A Berry", 0),
                    _bat(6, "M Croney", "lbw", "P Hewart", None, 2),
                    _bat(7, "Kalid", "ct", "A Berry", "I Wade", 4),
                    _bat(8, "D McWilliams", "ct", None, "A Berry", 9),
                    _bat(9, "Saleem", "st", "A Berry", "M Robinson", 16),
                    _bat(10, "G McWilliam", "not out", None, None, 21),
                    _bat(11, "J Fallon", "not out", None, None, 3),
                ],
                "bowl": [
                    _bowl("P Hewart", "9", 1, 30, 4),
                    _bowl("S Dalton", "9", 1, 25, 2),
                    _bowl("A Berry", "6", 2, 13, 2),
                    _bowl("M Young", "2", 0, 15, 0),
                    _bowl("J Sheils", "4", 1, 9, 0),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Ashton Ladysmith 1st XI|09/05/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Ashton Ladysmith", "away_club_name": "Ashton Ladysmith CC",
        "away_team_id": "Ashton Ladysmith 1st XI", "away_team_name": "1st XI",
        "match_date": "09/05/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Won by 7 wickets",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 7 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("J Wade", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("A Berry", 6),
                _player("P Hewart", 7), _player("S Keyworth", 8), _player("M Hodson", 9),
                _player("S Dalton", 10), _player("M Robinson", 11, wicket_keeper=True),
            ]},
            {"away_team": [
                _player("J Hillson", 1), _player("G Pinder", 2), _player("P Reynolds", 3),
                _player("M Sheilds", 4), _player("C Collings", 5), _player("S Sheilds", 6),
                _player("A Camps", 7), _player("C Bennett", 8), _player("M Collings", 9),
                _player("B Collings", 10), _player("D Sheilds", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Ashton Ladysmith 1st XI", "team_batting_name": "1st XI",
                "runs": 82, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 12, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 12,
                # individual dismissal/bowler pairings weren't captured with
                # confidence on this read -- see the module docstring above.
                "bat": [
                    _bat(1, "J Hillson", runs=9),
                    _bat(2, "G Pinder", runs=8),
                    _bat(3, "P Reynolds", runs=4),
                    _bat(4, "M Sheilds", runs=2),
                    _bat(5, "C Collings", runs=0),
                    _bat(6, "S Sheilds", runs=11),
                    _bat(7, "A Camps", runs=18),
                    _bat(8, "C Bennett", runs=6),
                    _bat(9, "M Collings", runs=3),
                    _bat(10, "B Collings", runs=9),
                    _bat(11, "D Sheilds", runs=0),
                ],
                "bowl": [
                    _bowl("P Hewart", "8", 4, 8, 1),
                    _bowl("S Dalton", "6", 2, 13, 1),
                    _bowl("S Keyworth", "6", 0, 32, 1),
                    _bowl("M Hodson", "4", 0, 8, 1),
                    _bowl("A Berry", "2.4", 0, 3, 2),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 84, "wickets": 3, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 5, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 5,
                "bat": [
                    _bat(1, "F Daly", "c&b", "A Camp", None, 32),
                    _bat(2, "J Sheils", "ct", "A Camp", "C Bennett", 0),
                    _bat(3, "J Wade", "b", "J Hillson", None, 26),
                    _bat(4, "I Wade", "not out", None, None, 16),
                    _bat(5, "G Young", "not out", None, None, 5),
                    _bat(6, "A Berry", "did not bat"),
                    _bat(7, "P Hewart", "did not bat"),
                    _bat(8, "S Keyworth", "did not bat"),
                    _bat(9, "M Hodson", "did not bat"),
                    _bat(10, "S Dalton", "did not bat"),
                    _bat(11, "M Robinson", "did not bat"),
                ],
                "bowl": [
                    _bowl("A Camps", "7.1", 0, 24, 2),
                    _bowl("P Reynolds", "12", 0, 19, 0),
                    _bowl("J Hillson", "3.5", 1, 39, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Rochdalians 1st XI|15/05/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Rochdalians", "away_club_name": "Rochdalians CC",
        "away_team_id": "Rochdalians 1st XI", "away_team_name": "1st XI",
        "match_date": "15/05/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Lost by 7 wickets",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "Rochdalians CC won by 7 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("A McCheyne", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("Qamer", 6),
                _player("A Berry", 7), _player("P Hewart", 8), _player("S Carr", 9),
                _player("S Dalton", 10), _player("M Robinson", 11, wicket_keeper=True),
            ]},
            {"away_team": [
                _player("M Tyyub", 1), _player("N Hayee", 2), _player("A Rauf", 3),
                _player("M Shahzeb", 4), _player("M Iqbal", 5), _player("Z Khan", 6),
                _player("S Rahman", 7), _player("F Butt", 8), _player("S Mehmood", 9),
                _player("J Dell", 10), _player("S Heighway", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 168, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                # total (44) confirmed by arithmetic; byes/leg-byes/wides/
                # no-balls split wasn't attempted -- see the module
                # docstring above.
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 44, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 44,
                "bat": [
                    _bat(1, "F Daly", "b", "S Rahman", None, 9),
                    _bat(2, "J Sheils", "ct", "S Heighway", "J Dell", 0),
                    _bat(3, "A McCheyne", "not out", None, None, 55),
                    _bat(4, "I Wade", "ct", "S Rahman", "S Mehmood", 11),
                    _bat(5, "G Young", "lbw", "F Butt", None, 12),
                    _bat(6, "Qamer", "ct", "F Butt", "Z Khan", 0),
                    _bat(7, "A Berry", "b", "F Butt", None, 8),
                    _bat(8, "P Hewart", "b", "F Butt", None, 2),
                    _bat(9, "S Carr", "st", "A Rauf", None, 2),
                    _bat(10, "S Dalton", "b", "S Rahman", None, 26),
                    _bat(11, "M Robinson", "lbw", "S Heighway", None, 0),
                ],
                "bowl": [
                    _bowl("S Heighway", "9.1", 1, 26, 2),
                    _bowl("S Rahman", "9", 2, 39, 3),
                    _bowl("F Butt", "4", 0, 28, 4),
                    _bowl("S Mehmood", "10", 3, 32, 0),
                    _bowl("A Rauf", "8", 0, 30, 1),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Rochdalians 1st XI", "team_batting_name": "1st XI",
                "runs": 169, "wickets": 3, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 10, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 10,
                "bat": [
                    _bat(1, "M Tyyub", "b", "J Sheils", None, 75),
                    _bat(2, "N Hayee", "ct", "S Carr", "I Wade", 60),
                    _bat(3, "A Rauf", "not out", None, None, 0),
                    _bat(4, "M Shahzeb", "ct", "S Carr", "P Hewart", 18),
                    _bat(5, "M Iqbal", "not out", None, None, 6),
                    _bat(6, "Z Khan", "did not bat"),
                    _bat(7, "S Rahman", "did not bat"),
                    _bat(8, "F Butt", "did not bat"),
                    _bat(9, "S Mehmood", "did not bat"),
                    _bat(10, "J Dell", "did not bat"),
                    _bat(11, "S Heighway", "did not bat"),
                ],
                "bowl": [
                    # sums to 4 wickets against 3 real dismissals -- see
                    # the module docstring above.
                    _bowl("P Hewart", "7", 1, 31, 0),
                    _bowl("S Dalton", "6", 2, 33, 0),
                    _bowl("A Berry", "4", 0, 24, 0),
                    _bowl("S Carr", "11", 3, 54, 3),
                    _bowl("I Wade", "3", 0, 13, 0),
                    _bowl("J Sheils", "5", 1, 11, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Rochdalians 1st XI|16/05/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Rochdalians", "away_club_name": "Rochdalians CC",
        "away_team_id": "Rochdalians 1st XI", "away_team_name": "1st XI",
        "match_date": "16/05/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": "Cup",
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Won by 116 runs",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 116 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("J Wade", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("S Keyworth", 6),
                _player("M Hodson", 7), _player("A Berry", 8), _player("S Dalton", 9),
                _player("M Robinson", 10, wicket_keeper=True), _player("M Young", 11),
            ]},
            {"away_team": [
                _player("M Tyyub", 1), _player("N Hayee", 2), _player("S Mehmood", 3),
                _player("M Shaheed", 4), _player("F Butt", 5), _player("S Rahman", 6),
                _player("A Smith", 7), _player("G Khan", 8), _player("J Dell", 9),
                _player("M Iqbal", 10), _player("A Rauf", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 307, "wickets": 5, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                # total (52) confirmed by arithmetic; byes/leg-byes/wides/
                # no-balls split wasn't attempted -- see the module
                # docstring above.
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 52, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 52,
                "bat": [
                    _bat(1, "F Daly", "b", "S Mehmood", None, 95),
                    _bat(2, "J Sheils", "run out", None, "M Tyyub", 50),
                    _bat(3, "J Wade", "ct", "M Tyyub", "A Smith", 41),
                    _bat(4, "I Wade", "b", "F Butt", None, 42),
                    _bat(5, "G Young", "ct", "G Khan", "M Tyyub", 16),
                    _bat(6, "S Keyworth", "not out", None, None, 10),
                    _bat(7, "M Hodson", "not out", None, None, 1),
                    _bat(8, "A Berry", "did not bat"),
                    _bat(9, "S Dalton", "did not bat"),
                    _bat(10, "M Robinson", "did not bat"),
                    _bat(11, "M Young", "did not bat"),
                ],
                "bowl": [
                    _bowl("G Khan", "7", 0, 37, 1),
                    _bowl("S Rahman", "7", 0, 54, 0),
                    _bowl("S Mehmood", "8", 0, 35, 1),
                    _bowl("F Butt", "7", 0, 47, 1),
                    _bowl("M Tyyub", "9", 0, 61, 1),
                    _bowl("A Rauf", "7", 0, 50, 0),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Rochdalians 1st XI", "team_batting_name": "1st XI",
                "runs": 191, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 22, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 22,
                "bat": [
                    _bat(1, "M Tyyub", "ct", "S Dalton", "M Robinson", 2),
                    _bat(2, "N Hayee", "ct", "M Young", "F Daly", 29),
                    _bat(3, "S Mehmood", "ct", "M Hodson", "A Berry", 7),
                    _bat(4, "M Shaheed", "b", "I Wade", None, 44),
                    _bat(5, "F Butt", "ct", "J Sheils", "M Robinson", 40),
                    _bat(6, "S Rahman", "c&b", "J Sheils", None, 26),
                    _bat(7, "A Smith", "ct", "A Berry", "F Daly", 2),
                    _bat(8, "G Khan", "c&b", "M Young", None, 6),
                    _bat(9, "J Dell", "b", "M Young", None, 3),
                    _bat(10, "M Iqbal", "b", "M Young", None, 10),
                    _bat(11, "A Rauf", "not out", None, None, 0),
                ],
                "bowl": [
                    _bowl("M Hodson", "9", 1, 43, 1),
                    _bowl("S Dalton", "9", 0, 35, 1),
                    _bowl("I Wade", "4", 0, 30, 1),
                    _bowl("M Young", "4", 0, 28, 4),
                    _bowl("J Sheils", "4", 0, 18, 2),
                    _bowl("A Berry", "4", 0, 24, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Glodwick 1st XI|22/05/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Glodwick", "away_club_name": "Glodwick CC",
        "away_team_id": "Glodwick 1st XI", "away_team_name": "1st XI",
        "match_date": "22/05/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Won by 9 wickets",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 9 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("A McCheyne", 1), _player("J Sheils", 2), _player("G Young", 3),
                _player("I Wade", 4), _player("F Daly", 5), _player("A Berry", 6),
                _player("S Dalton", 7), _player("S Keyworth", 8), _player("P Hewart", 9),
                _player("S Carr", 10), _player("M Robinson", 11, wicket_keeper=True),
            ]},
            {"away_team": [
                _player("J Holt", 1), _player("M Kirk", 2), _player("K Edge", 3),
                _player("M Parkinson", 4), _player("N Khan", 5), _player("R White", 6),
                _player("R David", 7), _player("R Connolly", 8), _player("P Kitchen", 9),
                _player("A Raja", 10), _player("U Anwar", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Glodwick 1st XI", "team_batting_name": "1st XI",
                "runs": 125, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 7, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 7,
                "bat": [
                    _bat(1, "J Holt", "b", "P Hewart", None, 0),
                    _bat(2, "M Kirk", "c&b", "P Hewart", None, 7),
                    _bat(3, "K Edge", "ct", "P Hewart", "M Robinson", 6),
                    _bat(4, "M Parkinson", "ct", "A Berry", "A McCheyne", 23),
                    _bat(5, "N Khan", "ct", "A Berry", "F Daly", 62),
                    _bat(6, "R White", "b", "A Berry", None, 10),
                    _bat(7, "R David", "ct", "S Dalton", "M Robinson", 1),
                    _bat(8, "R Connolly", "lbw", "S Dalton", None, 0),
                    _bat(9, "P Kitchen", "ct", "A Berry", "S Keyworth", 4),
                    _bat(10, "A Raja", "run out", None, None, 1),
                    _bat(11, "U Anwar", "not out", None, None, 4),
                ],
                "bowl": [
                    _bowl("P Hewart", "9", 2, 44, 3),
                    _bowl("S Carr", "7", 0, 24, 0),
                    _bowl("S Dalton", "10", 2, 23, 2),
                    _bowl("I Wade", "3", 1, 13, 0),
                    _bowl("A Berry", "5.4", 1, 18, 4),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 126, "wickets": 1, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 25, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 25,
                "bat": [
                    _bat(1, "A McCheyne", "not out", None, None, 29),
                    _bat(2, "J Sheils", "ct", "U Anwar", "S Holt", 10),
                    _bat(3, "G Young", "not out", None, None, 62),
                    _bat(4, "I Wade", "did not bat"),
                    _bat(5, "F Daly", "did not bat"),
                    _bat(6, "A Berry", "did not bat"),
                    _bat(7, "S Dalton", "did not bat"),
                    _bat(8, "S Keyworth", "did not bat"),
                    _bat(9, "P Hewart", "did not bat"),
                    _bat(10, "S Carr", "did not bat"),
                    _bat(11, "M Robinson", "did not bat"),
                ],
                "bowl": [],
                "fow": [],
            },
        ],
    },
    {
        "id": "Failsworth Macedonia 1st XI|ELPM 1st XI|29/05/2004",
        "home_club_id": "Failsworth Macedonia", "home_club_name": "Failsworth Macedonia CC",
        "home_team_id": "Failsworth Macedonia 1st XI", "home_team_name": "1st XI",
        "away_club_id": "ELPM", "away_club_name": "East Lancs Paper Mill CC",
        "away_team_id": "ELPM 1st XI", "away_team_name": "1st XI",
        "match_date": "29/05/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "Failsworth",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Lost by 107 runs",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "Failsworth Macedonia CC won by 107 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("P Haselden", 1), _player("G Martin", 2), _player("D Rigney", 3),
                _player("N Daly", 4), _player("C Gawber", 5), _player("C Akin", 6),
                _player("D Marriot", 7), _player("I Wilson", 8), _player("G Broadhead", 9),
                _player("D Atkin", 10),
                # only 10 names are legible for Failsworth Macedonia's XI --
                # G Broadhead and D Atkin bowled but the innings closed
                # (6 wickets, 2 not out) before either needed to bat, and
                # no 11th name is visible anywhere else on the page.
            ]},
            {"away_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("J Wade", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("A McCheyne", 6),
                _player("A Berry", 7), _player("P Hewart", 8), _player("S Dalton", 9),
                _player("S Carr", 10), _player("M Robinson", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Failsworth Macedonia 1st XI", "team_batting_name": "1st XI",
                "runs": 225, "wickets": 6, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 30, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 30,
                "bat": [
                    _bat(1, "P Haselden", "ct", "S Carr", "J Wade", 0),
                    _bat(2, "G Martin", "b", "P Hewart", None, 1),
                    _bat(3, "D Rigney", "b", "S Dalton", None, 55),
                    _bat(4, "N Daly", "b", "J Sheils", None, 62),
                    _bat(5, "C Gawber", "not out", None, None, 43),
                    _bat(6, "C Akin", "b", "S Dalton", None, 33),
                    _bat(7, "D Marriot", "ct", "S Dalton", "A Berry", 0),
                    _bat(8, "I Wilson", "not out", None, None, 1),
                ],
                "bowl": [
                    _bowl("P Hewart", "9", 4, 23, 1),
                    _bowl("S Carr", "12", 3, 54, 1),
                    _bowl("S Dalton", "14", 1, 49, 3),
                    _bowl("I Wade", "3", 0, 30, 0),
                    _bowl("A Berry", "3", 0, 25, 0),
                    _bowl("J Sheils", "4", 0, 18, 1),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 118, "wickets": 9, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 16, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 16,
                "bat": [
                    _bat(1, "F Daly", "ct", "G Broadhead", "N Daly", 0),
                    _bat(2, "J Sheils", "b", "D Atkin", None, 9),
                    _bat(3, "J Wade", "b", "G Broadhead", None, 5),
                    _bat(4, "I Wade", "ct", "D Atkin", "N Daly", 0),
                    _bat(5, "G Young", "run out", None, None, 1),
                    _bat(6, "A McCheyne", "b", "C Akin", None, 16),
                    _bat(7, "A Berry", "ct", "D Atkin", "P Haselden", 5),
                    _bat(8, "P Hewart", "b", "C Akin", None, 22),
                    _bat(9, "S Dalton", "not out", None, None, 20),
                    _bat(10, "S Carr", "ct", "I Wilson", "C Gawber", 24),
                    _bat(11, "M Robinson", "retired hurt", None, None, 0),
                ],
                "bowl": [
                    _bowl("G Broadhead", "9", 4, 19, 2),
                    _bowl("D Atkin", "9", 1, 39, 3),
                    _bowl("C Akin", "7", 2, 20, 2),
                    _bowl("I Wilson", "6.4", 0, 27, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Tott St John 1st XI|30/05/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Tott St John", "away_club_name": "Tott St John CC",
        "away_team_id": "Tott St John 1st XI", "away_team_name": "1st XI",
        "match_date": "30/05/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Won by 34 runs",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 34 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("J Wade", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("A McCheyne", 6),
                _player("N Warne", 7), _player("A Berry", 8), _player("S Dalton", 9),
                _player("S Carr", 10), _player("P Hewart", 11),
            ]},
            {"away_team": [
                _player("K Coe", 1), _player("M Deegan", 2), _player("R Brooks", 3),
                _player("N Butterworth", 4), _player("P Meehan", 5), _player("P Skundric", 6),
                _player("S Smith", 7), _player("M Chadwick", 8), _player("C Brooks", 9),
                _player("S Moriarty", 10), _player("M Cotton", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 200, "wickets": 6, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 18, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 18,
                "bat": [
                    _bat(1, "F Daly", "ct", "M Cotton", "C Brook", 2),
                    _bat(2, "J Sheils", "ct", "R Brooks", "Coe", 16),
                    _bat(3, "J Wade", "ct", "N Butterworth", "C Brook", 82),
                    _bat(4, "I Wade", "ct", "R Brooks", "Chadwick", 2),
                    _bat(5, "G Young", "run out", None, None, 27),
                    _bat(6, "A McCheyne", "ct", "P Meehan", "C Brook", 5),
                    _bat(7, "N Warne", "not out", None, None, 36),
                    _bat(8, "A Berry", "not out", None, None, 12),
                    _bat(9, "S Dalton", "did not bat"),
                    _bat(10, "S Carr", "did not bat"),
                    _bat(11, "P Hewart", "did not bat"),
                ],
                "bowl": [
                    _bowl("M Cotton", "8", 1, 30, 1),
                    _bowl("P Skundric", "8", 0, 48, 0),
                    _bowl("S Moriarty", "7", 2, 29, 0),
                    _bowl("R Brooks", "4", 0, 20, 2),
                    _bowl("N Butterworth", "5", 0, 21, 1),
                    _bowl("P Meehan", "8", 0, 39, 1),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Tott St John 1st XI", "team_batting_name": "1st XI",
                "runs": 166, "wickets": 9, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 18, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 18,
                "bat": [
                    _bat(1, "K Coe", "ct", "S Carr", "P Hewart", 5),
                    _bat(2, "M Deegan", "ct", "P Hewart", "A McCheyne", 3),
                    _bat(3, "R Brooks", "b", "P Hewart", None, 4),
                    _bat(4, "N Butterworth", "ct", "A Berry", "N Warne", 45),
                    _bat(5, "P Meehan", "ct", "A Berry", "J Wade", 14),
                    _bat(6, "P Skundric", "b", "A Berry", None, 17),
                    _bat(7, "S Smith", "ct", "A Berry", "F Daly", 17),
                    _bat(8, "M Chadwick", "ct", "A Berry", "J Sheils", 5),
                    _bat(9, "C Brooks", "b", "J Sheils", None, 3),
                    _bat(10, "S Moriarty", "not out", None, None, 22),
                    _bat(11, "M Cotton", "not out", None, None, 13),
                ],
                "bowl": [
                    _bowl("P Hewart", "8", 2, 29, 2),
                    _bowl("S Carr", "6", 2, 13, 1),
                    _bowl("S Dalton", "7", 0, 50, 0),
                    _bowl("I Wade", "8", 1, 21, 0),
                    _bowl("A Berry", "8", 0, 25, 5),
                    _bowl("J Sheils", "3", 0, 15, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Rochdale Catholic Club 1st XI|05/06/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Rochdale Catholic Club", "away_club_name": "Rochdale Catholic Club",
        "away_team_id": "Rochdale Catholic Club 1st XI", "away_team_name": "1st XI",
        "match_date": "05/06/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Lost by 6 wickets",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "Rochdale Catholic Club won by 6 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("A McCheyne", 2), _player("J Wade", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("N Warne", 6),
                _player("A Berry", 7), _player("P Hewart", 8), _player("S Dalton", 9),
                _player("S Carr", 10), _player("A Openshaw", 11),
            ]},
            {"away_team": [
                _player("H Khan", 1), _player("D Mulkeen jnr", 2), _player("D Mulkeen", 3),
                _player("J Rafique", 4), _player("S Khan", 5), _player("Z Shah", 6),
                _player("M Tayab", 7), _player("W Ali", 8), _player("M Sohail", 9),
                _player("J Iqbal", 10), _player("B Anjum", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 88, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 18, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 18,
                "bat": [
                    _bat(1, "F Daly", "ct", "M Sohail", "Mulkeen", 13),
                    _bat(2, "A McCheyne", "ct", "J Iqbal", "J Rafique", 1),
                    _bat(3, "J Wade", "not out", None, None, 35),
                    _bat(4, "I Wade", "ct", "J Iqbal", "J Rafique", 5),
                    _bat(5, "G Young", "ct", "J Iqbal", "D Mulkeen", 2),
                    _bat(6, "N Warne", "b", "J Iqbal", None, 12),
                    _bat(7, "A Berry", "b", "M Sohail", None, 0),
                    _bat(8, "P Hewart", "b", "M Sohail", None, 0),
                    _bat(9, "S Dalton", "ct", "M Tayab", "H Khan", 2),
                    _bat(10, "S Carr", "ct", "M Tayab", "H Khan", 0),
                    _bat(11, "A Openshaw", "b", "M Sohail", None, 0),
                ],
                "bowl": [
                    _bowl("M Sohail", "12", 0, 41, 4),
                    _bowl("J Iqbal", "9", 1, 38, 4),
                    _bowl("M Tayab", "2.3", 0, 8, 2),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Rochdale Catholic Club 1st XI", "team_batting_name": "1st XI",
                "runs": 91, "wickets": 4, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 9, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 9,
                "bat": [
                    _bat(1, "H Khan", "ct", "P Hewart", "S Dalton", 1),
                    _bat(2, "D Mulkeen jnr", "ct", "P Hewart", "F Daly", 5),
                    _bat(3, "D Mulkeen", "ct", "S Carr", "Warne", 11),
                    _bat(4, "J Rafique", "not out", None, None, 23),
                    _bat(5, "S Khan", "b", "S Dalton", None, 42),
                    _bat(6, "Z Shah", "not out", None, None, 0),
                    _bat(7, "M Tayab", "did not bat"),
                    _bat(8, "W Ali", "did not bat"),
                    _bat(9, "M Sohail", "did not bat"),
                    _bat(10, "J Iqbal", "did not bat"),
                    _bat(11, "B Anjum", "did not bat"),
                ],
                "bowl": [
                    _bowl("P Hewart", "4", 0, 19, 2),
                    _bowl("S Carr", "4", 0, 20, 1),
                    _bowl("A Berry", "3.5", 0, 17, 0),
                    _bowl("S Dalton", "2", 0, 30, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Elton Vale 1st XI|12/06/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Elton Vale", "away_club_name": "Elton Vale CC",
        "away_team_id": "Elton Vale 1st XI", "away_team_name": "1st XI",
        "match_date": "12/06/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Won by 4 wickets",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 4 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("J Wade", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("A McCheyne", 6),
                _player("P Partington", 7), _player("A Berry", 8), _player("S Dalton", 9),
                _player("P Hewart", 10), _player("S Carr", 11, wicket_keeper=True),
            ]},
            {"away_team": [
                _player("M Irfan", 1), _player("F Ahmed", 2), _player("Z Daddaboy", 3),
                _player("A Khan", 4), _player("T Ahmed", 5), _player("M Ikram", 6),
                _player("L Marsden", 7), _player("J Khan", 8), _player("C Keyworth", 9),
                _player("K Hothersall", 10), _player("B Baker", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Elton Vale 1st XI", "team_batting_name": "1st XI",
                "runs": 122, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 5, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 5,
                "bat": [
                    _bat(1, "M Irfan", "b", "S Carr", None, 7),
                    _bat(2, "F Ahmed", "ct", "P Hewart", "J Sheils", 2),
                    _bat(3, "Z Daddaboy", "ct", "A Berry", "I Wade", 23),
                    _bat(4, "A Khan", "ct", "S Carr", "P Partington", 2),
                    _bat(5, "T Ahmed", "ct", "S Dalton", "I Wade", 36),
                    _bat(6, "M Ikram", "b", "S Dalton", None, 10),
                    _bat(7, "L Marsden", "b", "S Dalton", None, 0),
                    _bat(8, "J Khan", "lbw", "S Dalton", None, 23),
                    _bat(9, "C Keyworth", "not out", None, None, 14),
                    _bat(10, "K Hothersall", "ct", "A Berry", "J Sheils", 0),
                    _bat(11, "B Baker", "st", "S Carr", "P Partington", 0),
                ],
                "bowl": [
                    _bowl("P Hewart", "11", 3, 24, 1),
                    _bowl("S Carr", "10.1", 4, 30, 3),
                    _bowl("A Berry", "6", 1, 33, 2),
                    _bowl("S Dalton", "7", 4, 15, 4),
                    _bowl("I Wade", "3", 0, 14, 0),
                    _bowl("J Sheils", "5", 2, 3, 0),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 123, "wickets": 6, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 10, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 10,
                "bat": [
                    _bat(1, "F Daly", "ct", "M Ikram", "L Marsden", 3),
                    _bat(2, "J Sheils", "b", "Z Daddaboy", None, 13),
                    _bat(3, "J Wade", "ct", "J Khan", "L Marsden", 73),
                    _bat(4, "I Wade", "ct", "M Ikram", "T Ahmed", 8),
                    _bat(5, "G Young", "ct", "M Irfan", "Z Daddaboy", 5),
                    _bat(6, "A McCheyne", "c&b", "M Irfan", None, 3),
                    _bat(7, "P Partington", "not out", None, None, 3),
                    _bat(8, "A Berry", "not out", None, None, 5),
                    _bat(9, "S Dalton", "did not bat"),
                    _bat(10, "P Hewart", "did not bat"),
                    _bat(11, "S Carr", "did not bat"),
                ],
                "bowl": [
                    _bowl("M Ikram", "8", 1, 30, 2),
                    _bowl("Z Daddaboy", "6", 0, 39, 1),
                    _bowl("C Keyworth", "3", 0, 18, 0),
                    _bowl("M Irfan", "5", 0, 19, 2),
                    _bowl("J Khan", "4.1", 1, 15, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Degham Hibbert 1st XI|13/06/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Degham Hibbert", "away_club_name": "Degham Hibbert CC",
        "away_team_id": "Degham Hibbert 1st XI", "away_team_name": "1st XI",
        "match_date": "13/06/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Lost by 3 wickets",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "Degham Hibbert CC won by 3 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("J Wade", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("S Keyworth", 6),
                _player("N Warne", 7), _player("A McCheyne", 8), _player("A Berry", 9),
                _player("O Hellyer", 10), _player("S Carr", 11),
            ]},
            {"away_team": [
                _player("P Iqbal", 1), _player("P Faruk", 3), _player("P Seed", 4),
                _player("P Muamaf", 5), _player("B Faruk", 6), _player("P Mustaq", 7),
                _player("P Mustaqa", 8), _player("P Younas", 9),
                # No. 2 in the order is unidentified -- see the module
                # docstring above.
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 254, "wickets": 7, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 18, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 18,
                "bat": [
                    _bat(1, "F Daly", "lbw", "E Ziz", None, 14),
                    _bat(2, "J Sheils", "ct", "M Bhana", "B Farouk", 63),
                    _bat(3, "J Wade", "run out", None, None, 36),
                    _bat(4, "I Wade", "ct", "Mustaq Patel", "A Ziz", 18),
                    _bat(5, "G Young", "c&b", "B Erfan", None, 57),
                    _bat(6, "S Keyworth", "b", "B Erfan", None, 1),
                    _bat(7, "N Warne", "ct", "P Younas", "Iqbal", 12),
                    _bat(8, "A McCheyne", "not out", None, None, 22),
                    _bat(9, "A Berry", "not out", None, None, 13),
                    _bat(10, "O Hellyer", "did not bat"),
                    _bat(11, "S Carr", "did not bat"),
                ],
                "bowl": [
                    _bowl("E Ziz", "6", 1, 15, 1),
                    _bowl("M Bhana", "9", 0, 42, 1),
                    _bowl("Mustaq Patel", "8", 0, 62, 1),
                    _bowl("B Erfan", "7", 0, 44, 2),
                    _bowl("P Younas", "9", 1, 30, 1),
                    _bowl("Mo Patel", "6", 0, 47, 0),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Degham Hibbert 1st XI", "team_batting_name": "1st XI",
                "runs": 256, "wickets": 7, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 23, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 23,
                "bat": [
                    _bat(1, "P Iqbal", "ct", "I Wade", "J Wade", 32),
                    # inferred, not transcribed -- see the module docstring
                    # above: the only way both the runs (233 batsmen's
                    # total) and the bowling analysis (7 wickets) reconcile.
                    _bat(2, "Unknown", "b", "P Hewart", None, 38),
                    _bat(3, "P Faruk", "ct", "I Wade", "J Sheils", 24),
                    _bat(4, "P Seed", "b", "I Wade", None, 13),
                    _bat(5, "P Muamaf", "b", "I Wade", None, 18),
                    _bat(6, "B Faruk", "ct", "A Berry", "N Warne", 10),
                    _bat(7, "P Mustaq", "b", "P Hewart", None, 2),
                    _bat(8, "P Mustaqa", "not out", None, None, 65),
                    _bat(9, "P Younas", "not out", None, None, 31),
                ],
                "bowl": [
                    _bowl("P Hewart", "9", 0, 44, 2),
                    _bowl("S Carr", "7.2", 0, 58, 0),
                    _bowl("I Wade", "9", 2, 49, 4),
                    _bowl("A Berry", "7", 0, 49, 1),
                    _bowl("S Keyworth", "3", 0, 16, 0),
                    _bowl("J Sheils", "3", 0, 14, 0),
                    _bowl("J Wade", "1", 0, 2, 0),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Ashton Ladysmith 1st XI|19/06/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Ashton Ladysmith", "away_club_name": "Ashton Ladysmith CC",
        "away_team_id": "Ashton Ladysmith 1st XI", "away_team_name": "1st XI",
        "match_date": "19/06/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Won by 9 wickets",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 9 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("I Wade", 3),
                _player("P Hewart", 4), _player("S Carr", 5), _player("A Berry", 6),
                _player("S Keyworth", 7), _player("S Dalton", 8),
            ]},
            {"away_team": [
                _player("S Shields", 1), _player("G Pinder", 2), _player("P Reynolds", 3),
                _player("M Shields", 4), _player("C Collings", 5), _player("C Bennett", 6),
                _player("D Shields", 7), _player("M Collings", 8), _player("B Collings", 9),
                _player("C Rose", 10), _player("S Telfer", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Ashton Ladysmith 1st XI", "team_batting_name": "1st XI",
                "runs": 140, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 21, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 21,
                "bat": [
                    _bat(1, "S Shields", "b", "S Carr", None, 3),
                    _bat(2, "G Pinder", "ct", "I Wade", "G Young", 55),
                    _bat(3, "P Reynolds", "ct", "P Hewart", "I Wade", 5),
                    _bat(4, "M Shields", "ct", "S Keyworth", "S Dalton", 18),
                    _bat(5, "C Collings", "ct", "S Keyworth", "S Carr", 8),
                    _bat(6, "C Bennett", "ct", "S Keyworth", "J Sheils", 5),
                    _bat(7, "D Shields", "b", "I Wade", None, 0),
                    _bat(8, "M Collings", "run out", None, None, 6),
                    _bat(9, "B Collings", "ct", "J Sheils", "S Dalton", 4),
                    _bat(10, "C Rose", "b", "J Sheils", None, 15),
                    _bat(11, "S Telfer", "not out", None, None, 0),
                ],
                "bowl": [
                    _bowl("P Hewart", "7", 2, 33, 1),
                    _bowl("S Carr", "7", 1, 20, 1),
                    _bowl("A Berry", "5", 0, 15, 0),
                    _bowl("S Keyworth", "10", 1, 29, 3),
                    _bowl("I Wade", "6", 1, 13, 2),
                    _bowl("J Sheils", "2.3", 1, 5, 2),
                    _bowl("S Dalton", "2", 0, 10, 0),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 144, "wickets": 1, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 13, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 13,
                "bat": [
                    _bat(1, "F Daly", "ct", "S Shields", "C Rose", 51),
                    _bat(2, "J Sheils", "not out", None, None, 66),
                    _bat(3, "I Wade", "not out", None, None, 14),
                    _bat(4, "P Hewart", "did not bat"),
                    _bat(5, "S Carr", "did not bat"),
                    _bat(6, "A Berry", "did not bat"),
                    _bat(7, "S Keyworth", "did not bat"),
                    _bat(8, "S Dalton", "did not bat"),
                ],
                "bowl": [
                    _bowl("P Reynolds", "11", 0, 42, 0),
                    _bowl("J Telfer", "5", 0, 30, 0),
                    _bowl("G Pinder", "6", 0, 30, 0),
                    _bowl("S Shields", "3", 0, 17, 1),
                    _bowl("M Collings", "2.4", 0, 17, 0),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "West Leigh 1st XI|ELPM 1st XI|20/06/2004",
        "home_club_id": "West Leigh", "home_club_name": "West Leigh CC",
        "home_team_id": "West Leigh 1st XI", "home_team_name": "1st XI",
        "away_club_id": "ELPM", "away_club_name": "East Lancs Paper Mill CC",
        "away_team_id": "ELPM 1st XI", "away_team_name": "1st XI",
        "match_date": "20/06/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "West Leigh",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Won by 5 wickets",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 5 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("KH Sadiq", 1), _player("D Jackson", 2), _player("J Taylor", 3),
                _player("C Ralph", 4), _player("K Lloyd", 5), _player("C Brett", 6),
                _player("A Lloyd", 7), _player("S Ralph", 8), _player("D Alridge", 9),
                _player("I Atkinson", 10), _player("L Brennan", 11),
            ]},
            {"away_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("I Wade", 3),
                _player("G Young", 4), _player("A McCheyne", 5), _player("S Keyworth", 6),
                _player("P Hewart", 7), _player("K Hocking", 8), _player("S Dalton", 9),
                _player("S Carr", 10), _player("A Berry", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "West Leigh 1st XI", "team_batting_name": "1st XI",
                "runs": 139, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 15, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 15,
                "bat": [
                    _bat(1, "KH Sadiq", "b", "P Hewart", None, 7),
                    _bat(2, "D Jackson", "b", "S Carr", None, 5),
                    _bat(3, "J Taylor", "ct", "P Hewart", "G Young", 0),
                    _bat(4, "C Ralph", "ct", "S Keyworth", "J Sheils", 61),
                    _bat(5, "K Lloyd", "b", "S Dalton", None, 5),
                    _bat(6, "C Brett", "ct", "S Keyworth", "G Young", 1),
                    _bat(7, "A Lloyd", "ct", "A Berry", "P Hewart", 17),
                    _bat(8, "S Ralph", "b", "A Berry", None, 13),
                    _bat(9, "D Alridge", "b", "S Dalton", None, 4),
                    _bat(10, "I Atkinson", "not out", None, None, 6),
                    _bat(11, "L Brennan", "ct", "A Berry", "J Sheils", 0),
                ],
                "bowl": [
                    _bowl("P Hewart", "10", 5, 26, 2),
                    _bowl("S Carr", "7", 0, 35, 1),
                    _bowl("S Dalton", "9", 0, 37, 2),
                    _bowl("S Keyworth", "4", 1, 20, 2),
                    _bowl("A Berry", "3", 0, 9, 3),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 141, "wickets": 5, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 8, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 8,
                "bat": [
                    _bat(1, "F Daly", "ct", "KH Sadiq", "A Lloyd", 24),
                    _bat(2, "J Sheils", "b", "A Lloyd", None, 17),
                    _bat(3, "I Wade", "ct", "I Atkinson", None, 14),
                    _bat(4, "G Young", "ct", "A Lloyd", "J Taylor", 13),
                    _bat(5, "A McCheyne", "lbw", "C Ralph", None, 11),
                    _bat(6, "S Keyworth", "not out", None, None, 34),
                    _bat(7, "P Hewart", "not out", None, None, 20),
                    _bat(8, "K Hocking", "did not bat"),
                    _bat(9, "S Dalton", "did not bat"),
                    _bat(10, "S Carr", "did not bat"),
                    _bat(11, "A Berry", "did not bat"),
                ],
                "bowl": [
                    _bowl("A Lloyd", "11.3", 1, 66, 2),
                    _bowl("I Atkinson", "8", 2, 23, 1),
                    _bowl("C Ralph", "8", 0, 24, 1),
                    _bowl("KH Sadiq", "5", 0, 23, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Springhead 1st XI|03/07/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Springhead", "away_club_name": "Springhead CC",
        "away_team_id": "Springhead 1st XI", "away_team_name": "1st XI",
        "match_date": "03/07/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Won by 130 runs",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 130 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("J Wade", 3),
                _player("G Young", 4), _player("A McCheyne", 5), _player("S Keyworth", 6),
                _player("K Hocking", 7), _player("P Partington", 8, wicket_keeper=True),
                _player("N Warne", 9), _player("P Hewart", 10), _player("S Carr", 11),
            ]},
            {"away_team": [
                _player("J Batey", 1), _player("K Fielding", 2), _player("D Percival", 3),
                _player("R Shaw", 4), _player("K DeHavilland", 5), _player("K Lees", 6),
                _player("A Milner", 7), _player("J Walmesly", 8), _player("J Cook", 9),
                _player("M Sweeting", 10),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 229, "wickets": 8, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 26, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 26,
                "bat": [
                    _bat(1, "F Daly", "ct", "DeHavilland", "D Percival", 50),
                    _bat(2, "J Sheils", "c&b", "DeHavilland", None, 16),
                    _bat(3, "J Wade", "ct", "J Cook", "Milner", 39),
                    _bat(4, "G Young", "b", "DeHavilland", None, 40),
                    # inferred score -- see the module docstring above; the
                    # dismissal (b DeHavilland) is directly from the user.
                    _bat(5, "A McCheyne", "b", "DeHavilland", None, 4),
                    _bat(6, "S Keyworth", "b", "M Sweeting", None, 7),
                    _bat(7, "K Hocking", "not out", None, None, 8),
                    _bat(8, "P Partington", "lbw", "M Sweeting", None, 18),
                    _bat(9, "N Warne", "b", "M Sweeting", None, 17),
                    _bat(10, "P Hewart", "not out", None, None, 4),
                    _bat(11, "S Carr", "did not bat"),
                ],
                "bowl": [
                    _bowl("K Lees", "14", 2, 46, 0),
                    _bowl("DeHavilland", "16", 2, 76, 4),
                    _bowl("J Cook", "6", 0, 54, 1),
                    _bowl("M Sweeting", "9", 1, 38, 3),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Springhead 1st XI", "team_batting_name": "1st XI",
                "runs": 99, "wickets": 9, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 5, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 5,
                "bat": [
                    _bat(1, "J Batey", "ct", "S Keyworth", "J Sheils", 17),
                    _bat(2, "K Fielding", "ct", "P Hewart", "J Wade", 0),
                    _bat(3, "D Percival", "b", "P Hewart", None, 8),
                    _bat(4, "R Shaw", "b", "P Hewart", None, 8),
                    _bat(5, "K DeHavilland", "c&b", "P Hewart", None, 0),
                    _bat(6, "K Lees", "b", "P Hewart", None, 0),
                    _bat(7, "A Milner", "run out", None, "J Wade", 21),
                    _bat(8, "J Walmesly", "st", "N Warne", "P Partington", 12),
                    _bat(9, "J Cook", "b", "S Carr", None, 14),
                    _bat(10, "M Sweeting", "not out", None, None, 6),
                ],
                "bowl": [
                    _bowl("P Hewart", "16", 7, 26, 5),
                    _bowl("S Carr", "11", 1, 25, 1),
                    _bowl("S Keyworth", "8", 3, 23, 1),
                    _bowl("J Wade", "4", 0, 10, 0),
                    _bowl("J Sheils", "3", 1, 13, 0),
                    _bowl("N Warne", "0.1", 0, 0, 1),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "Robinsons 1st XI|ELPM 1st XI|10/07/2004",
        "home_club_id": "Robinsons", "home_club_name": "Robinsons CC",
        "home_team_id": "Robinsons 1st XI", "home_team_name": "1st XI",
        "away_club_id": "ELPM", "away_club_name": "East Lancs Paper Mill CC",
        "away_team_id": "ELPM 1st XI", "away_team_name": "1st XI",
        "match_date": "10/07/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "Robinsons",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Won by 25 runs",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 25 runs",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("W Hughes", 1), _player("L Brook", 2), _player("M Massey", 3),
                _player("R Hild", 4), _player("R Congalhor", 5), _player("A Alletson", 6),
                _player("D Faulkner", 7), _player("C Betts", 8), _player("A Hodson", 9),
                _player("N Clarke", 10), _player("E Whitworth", 11),
            ]},
            {"away_team": [
                _player("F Daly", 1), _player("J Sheils", 2), _player("K Hocking", 3),
                _player("I Wade", 4), _player("G Young", 5), _player("P Smith", 6),
                _player("T Birtwistle", 7), _player("P Hewart", 8), _player("S Dalton", 9),
                _player("S Carr", 10), _player("M Robinson", 11, wicket_keeper=True),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 110, "wickets": 9, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 25, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 25,
                "bat": [
                    _bat(1, "F Daly", "b", "A Hodson", None, 3),
                    _bat(2, "J Sheils", "ct", "N Clarke", "A Hodson", 50),
                    _bat(3, "K Hocking", "lbw", "E Whitworth", None, 16),
                    _bat(4, "I Wade", "lbw", "N Clarke", None, 11),
                    _bat(5, "G Young", "b", "E Whitworth", None, 0),
                    _bat(6, "P Smith", "b", "E Whitworth", None, 1),
                    _bat(7, "T Birtwistle", "ct", "N Clarke", "Hughes", 3),
                    _bat(8, "P Hewart", "b", "E Whitworth", None, 1),
                    _bat(9, "S Dalton", "b", "N Clarke", None, 0),
                    _bat(10, "S Carr", "not out", None, None, 0),
                    _bat(11, "M Robinson", "not out", None, None, 0),
                ],
                "bowl": [
                    _bowl("A Hodson", "9", 1, 25, 1),
                    _bowl("D Faulkner", "4", 0, 22, 0),
                    _bowl("E Whitworth", "9", 3, 25, 4),
                    _bowl("N Clarke", "4.4", 0, 15, 4),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "Robinsons 1st XI", "team_batting_name": "1st XI",
                "runs": 85, "wickets": 10, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 4, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 4,
                "bat": [
                    _bat(1, "W Hughes", "b", "P Hewart", None, 8),
                    _bat(2, "L Brook", "lbw", "P Hewart", None, 17),
                    _bat(3, "M Massey", "ct", "S Carr", "I Wade", 8),
                    _bat(4, "R Hild", "ct", "J Sheils", "K Hocking", 20),
                    _bat(5, "R Congalhor", "lbw", "P Hewart", None, 10),
                    _bat(6, "A Alletson", "ct", "P Hewart", "S Dalton", 5),
                    _bat(7, "D Faulkner", "not out", None, None, 10),
                    _bat(8, "C Betts", "b", "P Hewart", None, 1),
                    _bat(9, "A Hodson", "lbw", "J Sheils", None, 0),
                    _bat(10, "N Clarke", "b", "J Sheils", None, 2),
                    _bat(11, "E Whitworth", "b", "P Hewart", None, 0),
                ],
                "bowl": [
                    _bowl("P Hewart", "13.3", 4, 37, 6),
                    _bowl("S Carr", "7", 2, 15, 1),
                    _bowl("I Wade", "3", 0, 14, 0),
                    _bowl("J Sheils", "3", 0, 16, 3),
                ],
                "fow": [],
            },
        ],
    },
    {
        "id": "ELPM 1st XI|Rochdalians 1st XI|24/07/2004",
        "home_club_id": "ELPM", "home_club_name": "East Lancs Paper Mill CC",
        "home_team_id": "ELPM 1st XI", "home_team_name": "1st XI",
        "away_club_id": "Rochdalians", "away_club_name": "Rochdalians CC",
        "away_team_id": "Rochdalians 1st XI", "away_team_name": "1st XI",
        "match_date": "24/07/2004",
        "match_time": None,
        "competition_id": None,
        "competition_name": "NMCL Division 1",
        "competition_type": None,
        "league_id": None, "league_name": None,
        "ground_id": None, "ground_name": "ELPM",
        "no_of_innings": 2,
        "no_of_overs": None,
        "no_of_days": 1,
        "toss": None,
        "toss_won_by_team_id": None,
        "result": "Won by 6 wickets",
        "result_applied_to": "ELPM 1st XI",
        "result_description": "East Lancs Paper Mill CC won by 6 wickets",
        "status": "Played",
        "last_updated": None,
        "players": [
            {"home_team": [
                _player("F Daly", 1), _player("P Partington", 2), _player("J Wade", 3),
                _player("I Wade", 4), _player("A McCheyne", 5), _player("S Keyworth", 6),
                _player("Unknown", 7), _player("Unknown", 8), _player("P Hewart", 9),
                _player("S Carr", 10), _player("M Robinson", 11, wicket_keeper=True),
            ]},
            {"away_team": [
                _player("M Shahid", 1), _player("N Hayee", 2), _player("M Tayyab", 3),
                _player("M Iqbal", 4), _player("S Rahman", 5), _player("A Dar", 6),
                _player("K Ali", 7), _player("G Khan", 8), _player("M Buxton", 9),
                _player("A Rauf", 10), _player("T Khan", 11),
            ]},
        ],
        "innings": [
            {
                "innings_number": 1,
                "team_batting_id": "Rochdalians 1st XI", "team_batting_name": "1st XI",
                "runs": 232, "wickets": 9, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 16, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 16,
                "bat": [
                    _bat(1, "M Shahid", "ct", "P Hewart", "M Robinson", 58),
                    _bat(2, "N Hayee", "ct", "P Hewart", "P Partington", 21),
                    _bat(3, "M Tayyab", "ct", "P Hewart", "A McCheyne", 1),
                    _bat(4, "M Iqbal", "c&b", "J Wade", None, 39),
                    _bat(5, "S Rahman", "lbw", "J Wade", None, 32),
                    _bat(6, "A Dar", "ct", "J Wade", "P Hewart", 4),
                    _bat(7, "K Ali", "ct", "S Keyworth", "I Wade", 16),
                    _bat(8, "G Khan", "not out", None, None, 35),
                    _bat(9, "M Buxton", "b", "S Keyworth", None, 8),
                    _bat(10, "A Rauf", "b", "S Keyworth", None, 2),
                    _bat(11, "T Khan", "not out", None, None, 0),
                ],
                "bowl": [
                    _bowl("I Wade", "3", 1, 15, 0),
                    _bowl("S Carr", "4", 1, 26, 0),
                    _bowl("P Hewart", "13", 2, 65, 3),
                    _bowl("S Keyworth", "15", 2, 64, 3),
                    _bowl("J Wade", "7", 0, 51, 3),
                ],
                "fow": [],
            },
            {
                "innings_number": 2,
                "team_batting_id": "ELPM 1st XI", "team_batting_name": "1st XI",
                "runs": 238, "wickets": 4, "overs": None,
                "declared": 0, "forfeited_innings": 0,
                "extra_byes": 0, "extra_leg_byes": 0, "extra_wides": 20, "extra_no_balls": 0,
                "extra_penalty_runs": 0, "total_extras": 20,
                "bat": [
                    _bat(1, "F Daly", "ct", "T Khan", "M Tayyab", 1),
                    _bat(2, "P Partington", "b", "A Dar", None, 15),
                    _bat(3, "J Wade", "b", "G Khan", None, 120),
                    _bat(4, "I Wade", "b", "N Hayee", None, 40),
                    _bat(5, "A McCheyne", "not out", None, None, 11),
                    _bat(6, "S Keyworth", "not out", None, None, 31),
                    _bat(9, "P Hewart", "did not bat"),
                    _bat(10, "S Carr", "did not bat"),
                    _bat(11, "M Robinson", "did not bat"),
                ],
                "bowl": [
                    _bowl("S Rahman", "0.1", 0, 0, 0),
                    _bowl("T Khan", "3", 0, 51, 1),
                    _bowl("A Dar", "4", 0, 40, 1),
                    _bowl("A Rauf", "3", 0, 24, 0),
                    _bowl("G Khan", "7", 0, 51, 1),
                    _bowl("N Hayee", "8", 0, 69, 1),
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
