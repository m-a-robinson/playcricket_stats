#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
playcricket_api.py

Pure Play-Cricket API client.

Responsibilities
----------------
This class is responsible ONLY for communicating with the
Play-Cricket API and returning API data in useful Python forms.

It does NOT:
    - store JSON data
    - load or save the local database
    - decide whether a match is already stored
    - update the local database
    - calculate player statistics
    - create Scorecard objects

Those responsibilities belong to PlayCricketDatabase and the
analysis classes.

Main API methods
----------------
get_all_matches()
    Retrieve the Play-Cricket match list for a season.

get_match_detail()
    Retrieve the complete raw scorecard/detail for one match.

The API match list includes a `last_updated` field. This is
important because Play-Cricket scorecards can be edited after
the original result has been entered. PlayCricketDatabase can
use this value to determine whether its local copy is current.
"""

import os
import json
from datetime import datetime

import numpy as np
import pandas as pd
import requests


class PlayCricketAPI:

    # ==========================================================
    # INITIALISATION
    # ==========================================================

    def __init__(
        self,
        api_key=None,
        site_id=None,
        base_url="https://play-cricket.com/api/v2",
        timeout=60
    ):
        """
        Initialise the Play-Cricket API client.

        Parameters
        ----------
        api_key : str
            Play-Cricket API key.

        site_id : int
            Play-Cricket site ID.

            For East Lancs Paper Mill CC this is:

                9653

        base_url : str
            Base URL for the Play-Cricket API.

        timeout : int
            HTTP request timeout in seconds.
        """

        if api_key is None:
            api_key = os.environ.get("PLAY_CRICKET_API_KEY")

        if not api_key:
            raise ValueError(
                "No Play-Cricket API key supplied. "
                "Pass api_key=... or set PLAY_CRICKET_API_KEY."
            )

        if site_id is None:
            raise ValueError(
                "site_id is required when creating PlayCricketAPI."
            )

        self.api_key = api_key
        self.site_id = int(site_id)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Reusable HTTP session
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "East-Lancs-Paper-Mill-Cricket-Stats/1.0"
        })

    # ==========================================================
    # HTTP REQUEST
    # ==========================================================

    def _make_api_request(
        self,
        endpoint,
        params=None
    ):
        """
        Make a GET request to the Play-Cricket API.

        Parameters
        ----------
        endpoint : str
            API endpoint, e.g. "matches.json".

        params : dict, optional
            Query parameters.

        Returns
        -------
        dict
            Decoded JSON response.
        """

        if params is None:
            params = {}

        params = params.copy()

        # API key is always supplied by the client
        params["api_token"] = self.api_key

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout
        )

        # Raise an informative HTTP error if the API rejects
        # the request.
        response.raise_for_status()

        try:
            return response.json()

        except ValueError as exc:

            raise ValueError(
                "Play-Cricket API returned a response that "
                "could not be decoded as JSON.\n\n"
                f"URL: {response.url}\n"
                f"Status: {response.status_code}\n"
                f"Response: {response.text[:500]}"
            ) from exc

    # ==========================================================
    # ID NORMALISATION
    # ==========================================================

    @staticmethod
    def _normalise_id(value):
        """
        Normalise a Play-Cricket ID.

        Play-Cricket sometimes returns IDs as strings,
        integers or floats.

        Examples
        --------
        "9653"      -> 9653
        9653        -> 9653
        9653.0      -> 9653
        np.nan      -> None
        """

        if pd.isna(value):
            return None

        try:
            return int(float(value))

        except (TypeError, ValueError):
            return None

    # ==========================================================
    # MATCH DATAFRAME NORMALISATION
    # ==========================================================

    def _normalise_matches(
        self,
        matches
    ):
        """
        Convert the raw match list into a pandas DataFrame.

        This method only shapes API data.

        It does NOT save anything to the database.
        """

        if matches is None:
            return pd.DataFrame()

        if not isinstance(matches, list):
            raise TypeError(
                "Expected match data to be a list."
            )

        if len(matches) == 0:
            return pd.DataFrame()

        data = pd.DataFrame(matches).copy()

        # ------------------------------------------------------
        # Standardise commonly used ID columns
        # ------------------------------------------------------

        id_columns = [
            "id",
            "home_club_id",
            "home_team_id",
            "away_club_id",
            "away_team_id",
            "division_id",
            "cup_id",
            "competition_id",
            "league_id"
        ]

        for column in id_columns:

            if column in data.columns:

                data[column] = data[column].apply(
                    self._normalise_id
                )

        # ------------------------------------------------------
        # Standardise match ID
        # ------------------------------------------------------

        if "id" in data.columns:

            data["id"] = data["id"].astype("Int64")

        # ------------------------------------------------------
        # Standardise season
        # ------------------------------------------------------

        if "season" in data.columns:

            data["season"] = pd.to_numeric(
                data["season"],
                errors="coerce"
            ).astype("Int64")

        # ------------------------------------------------------
        # Parse match date
        # ------------------------------------------------------

        if "match_date" in data.columns:

            data["match_date"] = pd.to_datetime(
                data["match_date"],
                dayfirst=True,
                errors="coerce"
            )

        # ------------------------------------------------------
        # Parse last_updated
        # ------------------------------------------------------

        if "last_updated" in data.columns:

            data["last_updated"] = self._parse_last_updated(
                data["last_updated"]
            )

        return data

    # ==========================================================
    # LAST UPDATED
    # ==========================================================

    @staticmethod
    def _parse_last_updated(series):
        """
        Parse Play-Cricket last_updated values.

        Play-Cricket has returned slightly different date
        formats over time, so parsing is deliberately tolerant.

        Invalid values become NaT rather than causing an API
        request to fail.
        """

        if not isinstance(series, pd.Series):
            series = pd.Series(series)

        # First attempt: normal pandas parsing
        parsed = pd.to_datetime(
            series,
            errors="coerce",
            dayfirst=True
        )

        # Some Play-Cricket responses contain ISO timestamps.
        # Re-attempt values which were not parsed.
        missing = parsed.isna()

        if missing.any():

            parsed_iso = pd.to_datetime(
                series[missing],
                errors="coerce",
                format="mixed"
            )

            parsed.loc[missing] = parsed_iso

        return parsed

    # ==========================================================
    # GET ALL MATCHES
    # ==========================================================

    def get_all_matches(
        self,
        season,
        team_ids=None,
        competition_ids=None,
        competition_types=None,
        division_id=None,
        cup_id=None,
        from_entry_date=None,
        end_entry_date=None,
        include_unpublished=False,
        site_id=None
    ):
        """
        Retrieve matches from Play-Cricket.

        Parameters
        ----------
        season : int
            Season to retrieve.

        team_ids : list, optional
            Restrict matches to specific team IDs.

        competition_ids : list, optional
            Restrict matches to specific competition IDs.

        competition_types : list, optional
            Restrict by competition type.

            Examples:
                ["League"]
                ["Cup"]
                ["Friendly"]

        division_id : int, optional
            Restrict to a division.

        cup_id : int, optional
            Restrict to a cup.

        from_entry_date : str, optional
            Return records updated from this date/time.

            Example:
                "23/08/2026T00:00:00"

        end_entry_date : str, optional
            Return records updated before this date/time.

        include_unpublished : bool
            Whether unpublished fixtures should be included.

        site_id : int, optional
            Alternative site ID.

        Returns
        -------
        pandas.DataFrame
            One row per Play-Cricket match.
        """

        if site_id is None:
            site_id = self.site_id

        site_id = self._normalise_id(site_id)

        season = self._normalise_id(season)

        if season is None:
            raise ValueError(
                "A valid season is required."
            )

        params = {
            "site_id": site_id,
            "season": season
        }

        # ------------------------------------------------------
        # Optional filters
        # ------------------------------------------------------

        if division_id is not None:

            params["division_id"] = self._normalise_id(
                division_id
            )

        if cup_id is not None:

            params["cup_id"] = self._normalise_id(
                cup_id
            )

        if from_entry_date is not None:

            params["from_entry_date"] = from_entry_date

        if end_entry_date is not None:

            params["end_entry_date"] = end_entry_date

        if include_unpublished:

            params["include_unpublished"] = "yes"

        # ------------------------------------------------------
        # Retrieve matches
        # ------------------------------------------------------

        response = self._make_api_request(
            "matches.json",
            params=params
        )

        matches = response.get(
            "matches",
            []
        )

        data = self._normalise_matches(
            matches
        )

        if data.empty:
            return data

        # ------------------------------------------------------
        # Local team filtering
        #
        # These filters are applied after retrieval because
        # team_ids and competition_ids may be supplied as
        # lists.
        # ------------------------------------------------------

        if team_ids is not None:

            team_ids = {
                self._normalise_id(x)
                for x in team_ids
            }

            home = (
                data["home_team_id"]
                if "home_team_id" in data.columns
                else pd.Series(
                    [None] * len(data),
                    index=data.index
                )
            )

            away = (
                data["away_team_id"]
                if "away_team_id" in data.columns
                else pd.Series(
                    [None] * len(data),
                    index=data.index
                )
            )

            mask = (
                home.isin(team_ids)
                | away.isin(team_ids)
            )

            data = data.loc[mask].copy()

        if competition_ids is not None:

            competition_ids = {
                self._normalise_id(x)
                for x in competition_ids
            }

            if "competition_id" in data.columns:

                data = data[
                    data["competition_id"].isin(
                        competition_ids
                    )
                ].copy()

        if competition_types is not None:

            competition_types = {
                str(x).lower()
                for x in competition_types
            }

            if "competition_type" in data.columns:

                data = data[
                    data["competition_type"]
                    .astype(str)
                    .str.lower()
                    .isin(competition_types)
                ].copy()

        return data.reset_index(drop=True)

    # ==========================================================
    # GET MATCH DETAIL
    # ==========================================================

    def get_match_detail(
        self,
        match_id
    ):
        """
        Retrieve raw match-detail data from Play-Cricket.

        No database access takes place here.

        Parameters
        ----------
        match_id : int

        Returns
        -------
        dict
            Raw Play-Cricket match-detail response.

        Notes
        -----
        The returned object is deliberately left as raw JSON.

        Scorecard is responsible for interpreting this data.
        """

        match_id = self._normalise_id(
            match_id
        )

        if match_id is None:
            raise ValueError(
                "A valid match_id is required."
            )

        response = self._make_api_request(
            "match_detail.json",
            params={
                "match_id": match_id
            }
        )

        return response

    # ==========================================================
    # OPTIONAL RESULT SUMMARY
    # ==========================================================

    def get_result_summary(
        self,
        season,
        team_id=None,
        competition_type=None,
        from_match_date=None,
        end_match_date=None,
        from_entry_date=None,
        end_entry_date=None,
        site_id=None
    ):
        """
        Retrieve Play-Cricket result-summary data.

        This is useful when a lightweight list of completed
        results is required without downloading full scorecards.

        It is also potentially useful for future database
        synchronisation because Play-Cricket supports filtering
        result records using last-updated entry dates.

        Returns
        -------
        pandas.DataFrame
        """

        if site_id is None:
            site_id = self.site_id

        params = {
            "site_id": self._normalise_id(site_id),
            "season": self._normalise_id(season)
        }

        if team_id is not None:

            params["team_id"] = self._normalise_id(
                team_id
            )

        if competition_type is not None:

            params["competition_type"] = (
                competition_type
            )

        if from_match_date is not None:

            params["from_match_date"] = (
                from_match_date
            )

        if end_match_date is not None:

            params["end_match_date"] = (
                end_match_date
            )

        if from_entry_date is not None:

            params["from_entry_date"] = (
                from_entry_date
            )

        if end_entry_date is not None:

            params["end_entry_date"] = (
                end_entry_date
            )

        response = self._make_api_request(
            "result_summary.json",
            params=params
        )

        results = response.get(
            "result_summary",
            []
        )

        if not results:
            return pd.DataFrame()

        return self._normalise_matches(
            results
        )

    # ==========================================================
    # SIMPLE API INFORMATION
    # ==========================================================

    def __repr__(self):
        return (
            f"PlayCricketAPI("
            f"site_id={self.site_id}, "
            f"base_url='{self.base_url}')"
        )
