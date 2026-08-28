"""
nmcl_stats.py

Ingests the North Manchester Cricket League "Final Averages" scanned
sheets (`nmcl stats/*.tif`) into the SQLite store's `nmcl_season_stats`
table -- see schema.sql for why these are a separate, explicitly
season-aggregate table rather than match-level data.

Unlike the other three sources (Play-Cricket API, CricHQ PDF,
CricketStatz .MXP), the 2000-2005 sheets are photocopies/scans with no
machine-readable text layer and no consistent enough layout for a
regex/OCR pipeline to be worth the risk of silently mis-reading a
qualification-threshold table (wrong average, wrong player) -- so those
years' rows in ELPM_ROWS are a direct, manually verified transcription
of every ELPM-relevant row on each sheet, not a parser output. From
2011 onwards the club has the same "Final Averages" report as a native
Excel workbook (`nmcl stats/NMCL <year> FINAL AVERAGES.xls`) instead of
a scan -- those years ARE machine-parsed (see the DIV1BAT/DIV1BOWL/
DIV2/DIV3/DIV4 sheet-reading logic in the git history of this file
around the 2011-2013 rows) and only re-typed into ELPM_ROWS as plain
dicts here to keep one format for every season regardless of how it
was sourced. New scanned seasons are added by transcription, matching
the schema below exactly (see each dict's keys); a new Excel workbook
would be parsed the same way the 2011-2013 ones were.

Only ELPM (East Lancs Paper Mill) rows are transcribed -- every other
club appearing on these league-wide sheets is out of scope for this
project, per the same "opposition players aren't tracked as our own
players" boundary the other sources draw (see sqlite_queries.py's
ELPMCC_NAME / elpmcc_only).

"Division One" is this club's 1st XI on every sheet transcribed so
far; "Division Two" would be the 2nd XI. Mapped to team_id via
DIVISION_TEAM_NAMES below, resolved against whatever team rows already
exist in the target store (so it works after the standard "1st XI"/
"2nd XI" club/team dedup key, not by a hardcoded id).

A second, different kind of row also lives in ELPM_ROWS from 2010
onwards: RESIDUAL figures, not a sheet transcription. The 2010 season
has real match-level data (cricketstatz_txt.py, `cricketstatz/2010
scorecards/`), but that folder is confirmed incomplete -- some
fixtures were saved under the wrong filename with another match's
content, and at least two 1st XI matches aren't present under any
filename at all (found by comparing ingested per-player totals against
the club's own official end-of-season summary sheets, which cover
every match played). For each player the DIFFERENCE between the
official summary's season total and this project's own ingested total
is the missing matches' combined contribution -- exactly the same
"season aggregate, no match/innings granularity" shape as a real NMCL
sheet, just derived by subtraction instead of read directly off a
sheet. Only added where the difference is non-zero on a real stat
(runs or wickets) -- a player who simply has 1-2 more Mts on the
official sheet with zero runs/wickets attached isn't given a batting
row for a blank innings. innings_played/highest_score/average are left
None throughout: the official summary's own total, and this project's
ingested total, are both real per-innings-detailed figures, but their
DIFFERENCE isn't a real innings-level record of anything -- it's a sum
across however many missing matches, mixed with whatever innings
detail did make it into the sheet-level average, so reporting an
"average" or "innings" for it would imply a precision the number
doesn't have.
"""

import re


SOURCE = "nmcl_stats"

ELPM_CLUB_CODE = "ELPM"

DIVISION_TEAM_NAMES = {
    1: "1st XI",
    2: "2nd XI",
}


# Every ELPM row transcribed from `nmcl stats/*.tif` so far. Each dict:
#   season, division, discipline ('batting' | 'bowling' | 'wicketkeeping'),
#   name (as printed), source_file, plus the discipline's own columns
#   (see schema.sql's nmcl_season_stats for what each means).
#
# highest_score_not_out is set when the sheet's HS carries a trailing
# "*" (retired/not out at the top score), matching batting_innings.not_out
# elsewhere in the schema.

ELPM_ROWS = [

    # ---- 2000 ----
    {"season": 2000, "division": 1, "discipline": "batting", "name": "N Warne",
     "innings_played": 19, "not_outs": 3, "highest_score": 119, "highest_score_not_out": 1,
     "runs": 553, "average": 34.56, "source_file": "nmcl stats/2000 1.tif"},
    {"season": 2000, "division": 1, "discipline": "batting", "name": "R Savage",
     "innings_played": 19, "not_outs": 3, "highest_score": 105, "highest_score_not_out": 0,
     "runs": 482, "average": 30.13, "source_file": "nmcl stats/2000 1.tif"},
    {"season": 2000, "division": 1, "discipline": "batting", "name": "F Daly",
     "innings_played": 18, "not_outs": 2, "highest_score": 136, "highest_score_not_out": 1,
     "runs": 476, "average": 29.75, "source_file": "nmcl stats/2000 1.tif"},

    {"season": 2000, "division": 1, "discipline": "bowling", "name": "T Birtwistle",
     "overs": "106.3", "maidens": 15, "runs_conceded": 406, "wickets": 30,
     "average": 13.53, "source_file": "nmcl stats/2000 2.tif"},
    {"season": 2000, "division": 1, "discipline": "bowling", "name": "A Openshaw",
     "overs": "202.1", "maidens": 59, "runs_conceded": 579, "wickets": 33,
     "average": 17.55, "source_file": "nmcl stats/2000 2.tif"},
    {"season": 2000, "division": 1, "discipline": "bowling", "name": "R Savage",
     "overs": "201.3", "maidens": 41, "runs_conceded": 642, "wickets": 32,
     "average": 20.06, "source_file": "nmcl stats/2000 2.tif"},

    # ---- 2001 ----
    {"season": 2001, "division": 1, "discipline": "batting", "name": "F Daly",
     "innings_played": 20, "not_outs": 1, "highest_score": 82, "highest_score_not_out": 0,
     "runs": 627, "average": 33.00, "source_file": "nmcl stats/2001 1.tif"},
    {"season": 2001, "division": 1, "discipline": "batting", "name": "R Savage",
     "innings_played": 20, "not_outs": 4, "highest_score": 76, "highest_score_not_out": 1,
     "runs": 470, "average": 29.38, "source_file": "nmcl stats/2001 1.tif"},
    {"season": 2001, "division": 1, "discipline": "batting", "name": "N Warne",
     "innings_played": 14, "not_outs": 1, "highest_score": 101, "highest_score_not_out": 0,
     "runs": 333, "average": 25.62, "source_file": "nmcl stats/2001 1.tif"},

    {"season": 2001, "division": 1, "discipline": "bowling", "name": "R Savage",
     "overs": "190", "maidens": 37, "runs_conceded": 597, "wickets": 34,
     "average": 17.56, "source_file": "nmcl stats/2001 2.tif"},

    # ---- 2002 ----
    {"season": 2002, "division": 1, "discipline": "batting", "name": "R Savage",
     "innings_played": 14, "not_outs": 3, "highest_score": 73, "highest_score_not_out": 1,
     "runs": 376, "average": 34.18, "source_file": "nmcl stats/2002 1.tif"},
    {"season": 2002, "division": 1, "discipline": "batting", "name": "F Daly",
     "innings_played": 19, "not_outs": 2, "highest_score": 69, "highest_score_not_out": 0,
     "runs": 539, "average": 31.71, "source_file": "nmcl stats/2002 1.tif"},
    {"season": 2002, "division": 1, "discipline": "batting", "name": "N Warne",
     "innings_played": 16, "not_outs": 3, "highest_score": 42, "highest_score_not_out": 1,
     "runs": 270, "average": 20.77, "source_file": "nmcl stats/2002 1.tif"},

    {"season": 2002, "division": 1, "discipline": "bowling", "name": "J Richardson",
     "overs": "115.4", "maidens": 17, "runs_conceded": 457, "wickets": 30,
     "average": 15.23, "source_file": "nmcl stats/2002 2.tif"},

    # ---- 2003 ----
    {"season": 2003, "division": 1, "discipline": "batting", "name": "J Wade",
     "innings_played": 11, "not_outs": 2, "highest_score": 183, "highest_score_not_out": 1,
     "runs": 574, "average": 63.78, "source_file": "nmcl stats/2003 1.tif"},
    {"season": 2003, "division": 1, "discipline": "batting", "name": "F Daly",
     "innings_played": 13, "not_outs": 2, "highest_score": 109, "highest_score_not_out": 1,
     "runs": 550, "average": 50.00, "source_file": "nmcl stats/2003 1.tif"},
    {"season": 2003, "division": 1, "discipline": "batting", "name": "I Wade",
     "innings_played": 14, "not_outs": 2, "highest_score": 152, "highest_score_not_out": 0,
     "runs": 400, "average": 33.33, "source_file": "nmcl stats/2003 1.tif"},
    {"season": 2003, "division": 1, "discipline": "batting", "name": "J Shiels",
     "innings_played": 15, "not_outs": 4, "highest_score": 84, "highest_score_not_out": 0,
     "runs": 344, "average": 31.27, "source_file": "nmcl stats/2003 1.tif"},
    {"season": 2003, "division": 1, "discipline": "batting", "name": "R Savage",
     "innings_played": 13, "not_outs": 4, "highest_score": 89, "highest_score_not_out": 1,
     "runs": 233, "average": 25.89, "source_file": "nmcl stats/2003 1.tif"},
    {"season": 2003, "division": 1, "discipline": "batting", "name": "G Young",
     "innings_played": 14, "not_outs": 4, "highest_score": 51, "highest_score_not_out": 0,
     "runs": 210, "average": 21.00, "source_file": "nmcl stats/2003 1.tif"},

    {"season": 2003, "division": 1, "discipline": "bowling", "name": "P Hewart",
     "overs": "134", "maidens": 32, "runs_conceded": 422, "wickets": 36,
     "average": 11.72, "source_file": "nmcl stats/2003 2.tif"},

    {"season": 2003, "division": 1, "discipline": "wicketkeeping", "name": "M Robinson",
     "catches": 21, "stumpings": 8, "average": None, "source_file": "nmcl stats/2003 2.tif"},

    # ---- 2004 ----
    {"season": 2004, "division": 1, "discipline": "batting", "name": "J Shiels",
     "innings_played": 16, "not_outs": 1, "highest_score": 104, "highest_score_not_out": 0,
     "runs": 429, "average": 28.60, "source_file": "nmcl stats/2004 1.tif"},
    {"season": 2004, "division": 1, "discipline": "batting", "name": "F Daly",
     "innings_played": 18, "not_outs": 2, "highest_score": 82, "highest_score_not_out": 1,
     "runs": 397, "average": 24.81, "source_file": "nmcl stats/2004 1.tif"},

    {"season": 2004, "division": 1, "discipline": "bowling", "name": "S Dalton",
     "overs": "114.4", "maidens": 22, "runs_conceded": 395, "wickets": 32,
     "average": 12.34, "source_file": "nmcl stats/2004 2.tif"},
    {"season": 2004, "division": 1, "discipline": "bowling", "name": "P Hewart",
     "overs": "176.3", "maidens": 44, "runs_conceded": 549, "wickets": 35,
     "average": 15.69, "source_file": "nmcl stats/2004 2.tif"},

    {"season": 2004, "division": 1, "discipline": "wicketkeeping", "name": "M Robinson",
     "catches": 12, "stumpings": 4, "average": None, "source_file": "nmcl stats/2004 2.tif"},

    # ---- 2005 ----
    {"season": 2005, "division": 1, "discipline": "batting", "name": "F Daly",
     "innings_played": 18, "not_outs": 3, "highest_score": 105, "highest_score_not_out": 1,
     "runs": 635, "average": 42.33, "source_file": "nmcl stats/2005 1.tif"},
    {"season": 2005, "division": 1, "discipline": "batting", "name": "G Greaves",
     "innings_played": 18, "not_outs": 5, "highest_score": 67, "highest_score_not_out": 1,
     "runs": 424, "average": 32.62, "source_file": "nmcl stats/2005 1.tif"},
    {"season": 2005, "division": 1, "discipline": "batting", "name": "J Shiels",
     "innings_played": 14, "not_outs": 0, "highest_score": 66, "highest_score_not_out": 0,
     "runs": 351, "average": 25.07, "source_file": "nmcl stats/2005 1.tif"},

    {"season": 2005, "division": 1, "discipline": "bowling", "name": "P Hewart",
     "overs": "131", "maidens": 40, "runs_conceded": 360, "wickets": 38,
     "average": 9.47, "source_file": "nmcl stats/2005 2.tif"},
    {"season": 2005, "division": 1, "discipline": "bowling", "name": "S Carr",
     "overs": "154.3", "maidens": 29, "runs_conceded": 513, "wickets": 36,
     "average": 14.25, "source_file": "nmcl stats/2005 2.tif"},

    {"season": 2005, "division": 1, "discipline": "wicketkeeping", "name": "M Robinson",
     "catches": 19, "stumpings": 6, "average": None, "source_file": "nmcl stats/2005 2.tif"},

    # ---- 2010 (RESIDUAL rows -- see module docstring) ----
    # Official season total (2010_1st_XI_Complete_Summary.txt) minus
    # this project's own cricketstatz_txt-ingested total, 1st XI only
    # (the 2nd XI's own gap turned out to be zero runs/wickets across
    # every player -- see the module docstring). Only players with a
    # non-zero runs and/or wickets difference are listed.
    {"season": 2010, "division": 1, "discipline": "batting", "name": "C Greaves",
     "runs": 137, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "C Holt",
     "runs": 24, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "D Pearson",
     "runs": 8, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "D Willett",
     "runs": 9, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "bowling", "name": "D Willett",
     "wickets": 2, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "G Greaves",
     "runs": 203, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "bowling", "name": "G Greaves",
     "wickets": 2, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "G Wade",
     "runs": 27, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "bowling", "name": "G Wade",
     "wickets": 1, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "I Wade",
     "runs": 168, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "bowling", "name": "I Wade",
     "wickets": 6, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "J Bailey",
     "runs": 91, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "bowling", "name": "J Bailey",
     "wickets": 3, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "J Shiels",
     "runs": 100, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "bowling", "name": "J Shiels",
     "wickets": 8, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "L Withington",
     "runs": 1, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "M Hay",
     "runs": 20, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "P Hewart",
     "runs": 10, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "P Partington",
     "runs": 24, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "S Keyworth",
     "runs": 1, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "bowling", "name": "S Keyworth",
     "wickets": 5, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "batting", "name": "W Street",
     "runs": 63, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},
    {"season": 2010, "division": 1, "discipline": "bowling", "name": "W Street",
     "wickets": 3, "source_file": "cricketstatz/2010_1st_XI_Complete_Summary.txt"},

    # ---- 2011-2013 (NMCL "Final Averages" Excel workbooks, not scans --
    # `nmcl stats/NMCL <year> FINAL AVERAGES.xls`) ----
    # Each workbook has separate DIV1BAT/DIV1BOWL sheets plus a combined
    # DIV2/DIV3/DIV4 sheet (batting+bowling+wicketkeeping together) per
    # division. Per the user: the NMCL renumbered which division the
    # 2nd XI played in as they were relegated across these seasons, so
    # every division other than One is this club's 2nd XI -- division
    # here is already normalised to 1 or 2, not the sheet's own division
    # number (kept in the reason/commit history, not per-row).
    {"season": 2011, "division": 1, "discipline": "batting", "name": "G Greaves",
     "innings_played": 15, "not_outs": 3, "highest_score": 64, "highest_score_not_out": 0,
     "runs": 361, "average": 30.08, "source_file": "nmcl stats/NMCL 2011 FINAL AVERAGES.xls"},
    {"season": 2011, "division": 1, "discipline": "batting", "name": "S Keyworth",
     "innings_played": 20, "not_outs": 8, "highest_score": 50, "highest_score_not_out": 0,
     "runs": 254, "average": 21.17, "source_file": "nmcl stats/NMCL 2011 FINAL AVERAGES.xls"},
    {"season": 2011, "division": 1, "discipline": "bowling", "name": "P Hewart",
     "overs": "133", "maidens": 30, "runs_conceded": 396, "wickets": 35,
     "average": 11.31, "source_file": "nmcl stats/NMCL 2011 FINAL AVERAGES.xls"},
    {"season": 2011, "division": 1, "discipline": "wicketkeeping", "name": "P Partington",
     "catches": 11, "stumpings": 7, "source_file": "nmcl stats/NMCL 2011 FINAL AVERAGES.xls"},

    {"season": 2012, "division": 1, "discipline": "batting", "name": "I Wade",
     "innings_played": 13, "not_outs": 3, "highest_score": 78, "highest_score_not_out": 0,
     "runs": 403, "average": 40.30, "source_file": "nmcl stats/NMCL 2012 FINAL AVERAGES.xls"},
    {"season": 2012, "division": 1, "discipline": "batting", "name": "G Greaves",
     "innings_played": 13, "not_outs": 3, "highest_score": 194, "highest_score_not_out": 0,
     "runs": 372, "average": 37.20, "source_file": "nmcl stats/NMCL 2012 FINAL AVERAGES.xls"},
    {"season": 2012, "division": 1, "discipline": "bowling", "name": "P Hewart",
     "overs": "140.3", "maidens": 31, "runs_conceded": 542, "wickets": 37,
     "average": 14.65, "source_file": "nmcl stats/NMCL 2012 FINAL AVERAGES.xls"},
    {"season": 2012, "division": 1, "discipline": "wicketkeeping", "name": "J Bond",
     "catches": 6, "stumpings": 3, "source_file": "nmcl stats/NMCL 2012 FINAL AVERAGES.xls"},
    {"season": 2012, "division": 2, "discipline": "bowling", "name": "M Young",
     "overs": "99", "maidens": 12, "runs_conceded": 514, "wickets": 24,
     "average": 21.42, "source_file": "nmcl stats/NMCL 2012 FINAL AVERAGES.xls"},
    {"season": 2012, "division": 2, "discipline": "wicketkeeping", "name": "N Warne",
     "catches": 5, "stumpings": 8, "source_file": "nmcl stats/NMCL 2012 FINAL AVERAGES.xls"},

    {"season": 2013, "division": 1, "discipline": "batting", "name": "I Wade",
     "innings_played": 18, "not_outs": 5, "highest_score": 83, "highest_score_not_out": 1,
     "runs": 518, "average": 39.85, "source_file": "nmcl stats/NMCL 2013 FINAL AVERAGES.xls"},
    {"season": 2013, "division": 1, "discipline": "batting", "name": "G Greaves",
     "innings_played": 13, "not_outs": 2, "highest_score": 91, "highest_score_not_out": 1,
     "runs": 370, "average": 33.64, "source_file": "nmcl stats/NMCL 2013 FINAL AVERAGES.xls"},
    {"season": 2013, "division": 1, "discipline": "batting", "name": "M Partington",
     "innings_played": 16, "not_outs": 2, "highest_score": 95, "highest_score_not_out": 1,
     "runs": 395, "average": 28.21, "source_file": "nmcl stats/NMCL 2013 FINAL AVERAGES.xls"},
    {"season": 2013, "division": 1, "discipline": "batting", "name": "K Dodson",
     "innings_played": 15, "not_outs": 1, "highest_score": 88, "highest_score_not_out": 1,
     "runs": 281, "average": 20.07, "source_file": "nmcl stats/NMCL 2013 FINAL AVERAGES.xls"},
    {"season": 2013, "division": 1, "discipline": "bowling", "name": "S Dalton",
     "overs": "111", "maidens": 20, "runs_conceded": 397, "wickets": 40,
     "average": 9.93, "source_file": "nmcl stats/NMCL 2013 FINAL AVERAGES.xls"},
    {"season": 2013, "division": 1, "discipline": "wicketkeeping", "name": "G Young",
     "catches": 27, "stumpings": 4, "source_file": "nmcl stats/NMCL 2013 FINAL AVERAGES.xls"},
    {"season": 2013, "division": 2, "discipline": "batting", "name": "S Dwyer",
     "innings_played": 10, "not_outs": 3, "highest_score": 33, "highest_score_not_out": 0,
     "runs": 213, "average": 30.43, "source_file": "nmcl stats/NMCL 2013 FINAL AVERAGES.xls"},
    {"season": 2013, "division": 2, "discipline": "batting", "name": "D Rushton",
     "innings_played": 11, "not_outs": 0, "highest_score": 67, "highest_score_not_out": 0,
     "runs": 276, "average": 25.09, "source_file": "nmcl stats/NMCL 2013 FINAL AVERAGES.xls"},
    {"season": 2013, "division": 2, "discipline": "batting", "name": "A Lomax",
     "innings_played": 13, "not_outs": 2, "highest_score": 70, "highest_score_not_out": 1,
     "runs": 267, "average": 24.27, "source_file": "nmcl stats/NMCL 2013 FINAL AVERAGES.xls"},
    {"season": 2013, "division": 2, "discipline": "bowling", "name": "D Rushton",
     "overs": "160", "maidens": 29, "runs_conceded": 536, "wickets": 37,
     "average": 14.49, "source_file": "nmcl stats/NMCL 2013 FINAL AVERAGES.xls"},
    {"season": 2013, "division": 2, "discipline": "wicketkeeping", "name": "P Partington",
     "catches": 9, "stumpings": 6, "source_file": "nmcl stats/NMCL 2013 FINAL AVERAGES.xls"},
]


def parse_nmcl_stats():
    """Return the transcribed ELPM row list. See ELPM_ROWS' docstring above."""

    return ELPM_ROWS


def _resolve_elpm_team_id(store, division):
    """
    Look up the ELPM team_id a division maps to, by name -- NOT via
    the usual source_team_id path (this source has no numeric team ids
    of its own, and it's naming an existing team another source
    already created, not creating a new one). Team/club names are
    stable across a rebuild even though their autoincrement ids
    aren't, so this is safe to call at ingest time against whatever
    store already has ELPM's teams loaded from another source.

    Returns None (rather than guessing) if the division has no mapping
    or the target team doesn't exist yet in this store -- callers
    leave nmcl_season_stats.team_id NULL in that case; every row still
    gets inserted regardless, this only affects the optional team_id
    convenience link.
    """

    team_name = DIVISION_TEAM_NAMES.get(division)

    if team_name is None:
        return None

    row = store.conn.execute(
        """
        SELECT t.team_id
        FROM teams t
        JOIN clubs c ON c.club_id = t.club_id
        WHERE c.club_name LIKE 'East Lancs Paper Mill%'
          AND t.team_name LIKE '%' || ?
        """,
        (team_name,)
    ).fetchone()

    return row[0] if row else None


def _source_player_id(name):
    """
    A stable per-name key within this source, the same role a CricHQ
    name plays in crichq_pdf.py: no numeric id exists on these sheets,
    so the (normalised) printed name IS the source's own identifier.
    Reconciliation (reconcile/decisions.yaml) links it to an existing
    canonical player the same way it links any other source's name.
    """

    return re.sub(r"\s+", " ", name.strip()).upper()


def ingest_nmcl_stats(store, rows=None):
    """
    Upsert each row's player (source='nmcl_stats') and insert its
    season-aggregate stat row into nmcl_season_stats.

    Idempotent per (player_id, season, division, discipline) via that
    table's UNIQUE constraint -- re-running against a store that
    already has these rows raises IntegrityError rather than silently
    duplicating, the same "don't guess, fail loud" posture as the rest
    of this project.
    """

    if rows is None:
        rows = parse_nmcl_stats()

    inserted = 0

    for row in rows:

        source_player_id = _source_player_id(row["name"])
        player_id = store._upsert_player(SOURCE, source_player_id, row["name"])

        team_id = _resolve_elpm_team_id(store, row["division"])

        store.conn.execute(
            """
            INSERT INTO nmcl_season_stats (
                player_id, team_id, season, division, discipline,
                innings_played, not_outs, highest_score, highest_score_not_out, runs,
                overs, maidens, runs_conceded, wickets,
                catches, stumpings,
                average, source_club_code, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                player_id, team_id, row["season"], row["division"], row["discipline"],
                row.get("innings_played"), row.get("not_outs"), row.get("highest_score"),
                row.get("highest_score_not_out"), row.get("runs"),
                row.get("overs"), row.get("maidens"), row.get("runs_conceded"), row.get("wickets"),
                row.get("catches"), row.get("stumpings"),
                row.get("average"), ELPM_CLUB_CODE, row["source_file"],
            )
        )

        inserted += 1

    return inserted


if __name__ == "__main__":

    import argparse

    from sqlite_store import SQLiteStore

    parser = argparse.ArgumentParser(
        description="Ingest the transcribed NMCL 'Final Averages' ELPM rows into the SQLite store."
    )
    parser.add_argument("--sqlite-db", default="playcricket_stats.sqlite")

    args = parser.parse_args()

    store = SQLiteStore(args.sqlite_db)

    rows = parse_nmcl_stats()
    count = ingest_nmcl_stats(store, rows)

    store.conn.commit()
    store.close()

    seasons = sorted(set(r["season"] for r in rows))
    print(f"Inserted {count} nmcl_season_stats rows for seasons {seasons}.")
