"""
Play-Cricket analysis setup

Creates the Play-Cricket connection, loads match and player data,
builds Scorecard objects for the selected season, and prepares the
PlayerPerformances and MultiPlayerStats objects for analysis.
"""


# ==========================================================
# PLAY-CRICKET CONNECTION
# ==========================================================

from playcric.playcricket import pc


playc = pc(
    api_key,
    site_id=9653,
    team_names=['ELPMCC'],
    team_name_to_ids_lookup={
        '1s': 87898,
        '2s': 119947,
        'u11s': 362584,
    },
)


# ==========================================================
# IMPORT OUR CLASSES
# ==========================================================

from playcricket_scorecard import Scorecard
from player_performances import PlayerPerformances
from multi_player_stats import MultiPlayerStats


# ==========================================================
# SETTINGS
# ==========================================================

SEASON = 2026
CLUB_ID = 9653


# ==========================================================
# MATCH DATA
# ==========================================================

matches = playc.get_all_matches(
    season=SEASON
)


# ==========================================================
# PLAYER DATA
# ==========================================================

players = playc.get_all_players_involved(
    match_ids=matches["id"].tolist()
)


# ==========================================================
# SCORECARD LOADER
# ==========================================================

def load_scorecards(
    playc,
    matches,
    season
):
    """
    Create a Scorecard object for every match in the
    supplied matches DataFrame.

    Returns
    -------
    scorecards : list
        Successfully loaded Scorecard objects.

    failed_matches : list
        Match IDs for which a Scorecard could not be created.
    """

    if matches.empty:
        return [], []

    scorecards = []
    failed_matches = []

    for match_id in matches["id"]:

        try:

            scorecard = Scorecard(
                playc,
                match_id=match_id,
                season=season
            )

            scorecards.append(scorecard)

            print(f"Loaded scorecard: {match_id}")

        except Exception as error:

            failed_matches.append({
                "match_id": match_id,
                "error": str(error)
            })

            print(
                f"Could not load scorecard "
                f"{match_id}: {error}"
            )

    return scorecards, failed_matches

# NEED TO INVESTIGATE FAILED MATCHES IN MORE DETAIL AT SOME POINT


# ==========================================================
# LOAD SCORECARDS
# ==========================================================

scorecards, failed_matches = load_scorecards(
    playc=playc,
    matches=matches,
    season=SEASON
)


# ==========================================================
# PLAYER PERFORMANCES
# ==========================================================

performances = PlayerPerformances(
    scorecards,
    club_id=CLUB_ID
)


# ==========================================================
# MULTI-PLAYER STATISTICS
# ==========================================================

stats = MultiPlayerStats(
    performances
)