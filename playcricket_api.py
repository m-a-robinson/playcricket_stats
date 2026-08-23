"""
Direct Play-Cricket API access.

This module provides a lightweight interface to the Play-Cricket API
without using the playcric package.

Design principle:
    - Minimise API requests
    - Retrieve the season match list once
    - Retrieve each match detail once
    - Allow the Scorecard class to extract all match information
      from that single match-detail response
"""

import requests
import pandas as pd
import numpy as np


class PlayCricketAPI:

    # --------------------------------------------------
    # API ENDPOINTS
    # --------------------------------------------------

    MATCHES_URL = (
        "http://play-cricket.com/api/v2/"
        "matches.json"
        "?&site_id={site_id}"
        "&season={season}"
        "&api_token={api_key}"
    )

    MATCH_DETAIL_URL = (
        "http://play-cricket.com/api/v2/"
        "match_detail.json"
        "?&match_id={match_id}"
        "&api_token={api_key}"
    )

    # --------------------------------------------------
    # INITIALISE
    # --------------------------------------------------

    def __init__(
        self,
        api_key,
        site_id,
        team_names=None,
        team_name_to_ids_lookup=None
    ):

        self.api_key = api_key
        self.site_id = site_id

        self.team_names = (
            team_names
            if team_names is not None
            else []
        )

        self.team_name_to_ids_lookup = (
            team_name_to_ids_lookup
            if team_name_to_ids_lookup is not None
            else {}
        )

        # Re-use the same HTTP session
        # rather than creating a new connection
        # for every request.
        self.session = requests.Session()

    # ==================================================
    # INTERNAL API REQUEST
    # ==================================================

    def _make_api_request(self, url):
        """
        Make one request to the Play-Cricket API.

        Returns
        -------
        dict
            JSON response from the API.
        """

        response = self.session.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    # ==================================================
    # MATCHES
    # ==================================================

    def get_all_matches(
        self,
        season,
        team_ids=None,
        competition_ids=None,
        competition_types=None,
        site_id=None
    ):
        """
        Retrieve all matches for a season.

        The Play-Cricket matches endpoint is called once.

        Optional filtering is performed locally so that filtering
        does not require additional API requests.
        """

        if team_ids is None:
            team_ids = []

        if competition_ids is None:
            competition_ids = []

        if competition_types is None:
            competition_types = []

        if site_id is None:
            site_id = self.site_id

        # --------------------------------------------------
        # ONE API REQUEST
        # --------------------------------------------------

        url = self.MATCHES_URL.format(
            site_id=site_id,
            season=season,
            api_key=self.api_key
        )

        data = self._make_api_request(url)

        # --------------------------------------------------
        # CONVERT TO DATAFRAME
        # --------------------------------------------------

        df = pd.json_normalize(
            data["matches"]
        )

        if df.empty:
            return pd.DataFrame()

        # --------------------------------------------------
        # MATCH DATE
        # --------------------------------------------------

        for col in [
            "last_updated",
            "match_date"
        ]:

            if col in df.columns:

                df[col] = pd.to_datetime(
                    df[col],
                    format="%d/%m/%Y"
                )

        # --------------------------------------------------
        # COMPETITION ID
        # --------------------------------------------------

        if "competition_id" in df.columns:

            df["competition_id"] = (
                df["competition_id"]
                .replace("", np.nan)
                .astype(float)
            )

        # --------------------------------------------------
        # TEAM IDS
        # --------------------------------------------------

        for col in [
            "home_team_id",
            "away_team_id"
        ]:

            if col in df.columns:

                df[col] = (
                    df[col]
                    .astype(int)
                )

        # --------------------------------------------------
        # TEAM FILTER
        # --------------------------------------------------

        if team_ids:

            df = df.loc[
                (df["home_team_id"].isin(team_ids))
                |
                (df["away_team_id"].isin(team_ids))
            ]

        # --------------------------------------------------
        # COMPETITION FILTER
        # --------------------------------------------------

        if competition_ids:

            df = df.loc[
                df["competition_id"]
                .isin(competition_ids)
            ]

        # --------------------------------------------------
        # COMPETITION TYPE FILTER
        # --------------------------------------------------

        if competition_types:

            df = df.loc[
                df["competition_type"]
                .isin(competition_types)
            ]

        return df

    # ==================================================
    # MATCH DETAIL
    # ==================================================

    def get_match_detail(
        self,
        match_id
    ):
        """
        Retrieve the complete match-detail response.

        IMPORTANT:
            This is the single API request from which the
            Scorecard will derive:

                - match information
                - players
                - batting
                - bowling
                - innings totals
                - partnerships
                - fall of wickets

        Returns
        -------
        dict
            The raw ``match_details[0]`` dictionary.
        """

        url = self.MATCH_DETAIL_URL.format(
            match_id=match_id,
            api_key=self.api_key
        )

        data = self._make_api_request(url)

        return data["match_details"][0]