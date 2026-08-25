#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Local JSON database for Play-Cricket data.

Architecture
------------

    PlayCricketAPI
          |
          | API requests
          v
    PlayCricketDatabase
          |
          | local cache
          v
    JSON database
          |
          v
    Scorecard / analysis classes


Responsibilities
----------------
PlayCricketDatabase is responsible for:

    - storing Play-Cricket data locally
    - loading and saving the local database
    - synchronising local data with Play-Cricket
    - detecting new and changed matches
    - providing local query methods

It does NOT:

    - make HTTP requests directly
    - calculate player statistics
    - create Scorecard objects
    - depend on playcric / pyplaycricket


Synchronisation principle
-------------------------

The Play-Cricket match list contains a `last_updated` value.

For each locally stored match:

    remote last_updated == local last_updated
        -> no detail API call

    remote last_updated != local last_updated
        -> download match detail

    match not in local database
        -> download match detail

Therefore a normal synchronisation requires:

    1 API call for the season match list
    +
    1 detail API call for each new/changed match.


Database structure
-----------------

{
    "database_version": 2,
    "last_updated": "...",

    "seasons": {

        "2026": {

            "match_list": [...],

            "matches": {
                "7240402": {
                    ...raw match detail...
                }
            },

            "match_metadata": {
                "7240402": {
                    "last_updated": "...",
                    "downloaded_at": "..."
                }
            }
        }
    }
}
"""

import json
import os

from datetime import datetime

import pandas as pd


class PlayCricketDatabase:

    # ==========================================================
    # INITIALISATION
    # ==========================================================

    def __init__(
        self,
        api,
        filename="playcricket_database.json"
    ):
        """
        Initialise the local Play-Cricket database.

        Parameters
        ----------
        api : PlayCricketAPI
            Configured Play-Cricket API client.

        filename : str
            Local JSON database filename.
        """

        self.api = api
        self.filename = filename

        self.data = {
            "database_version": 2,
            "last_updated": None,
            "seasons": {}
        }

        # Statistics for the most recent synchronisation.
        self.last_sync = None

        self.load()

    # ==========================================================
    # LOAD
    # ==========================================================

    def load(self):
        """
        Load the database from disk if it exists.

        Existing version-1 databases are supported.
        """

        if not os.path.exists(self.filename):
            return

        with open(
            self.filename,
            "r",
            encoding="utf-8"
        ) as f:

            loaded = json.load(f)

        self.data = loaded

        # ------------------------------------------------------
        # Ensure expected top-level structure exists
        # ------------------------------------------------------

        self.data.setdefault(
            "database_version",
            1
        )

        self.data.setdefault(
            "last_updated",
            None
        )

        self.data.setdefault(
            "seasons",
            {}
        )

        # ------------------------------------------------------
        # Prepare metadata for existing databases
        # ------------------------------------------------------

        for season_data in self.data["seasons"].values():

            season_data.setdefault(
                "matches",
                {}
            )

            season_data.setdefault(
                "match_list",
                []
            )

            season_data.setdefault(
                "match_metadata",
                {}
            )

        # Current database schema
        self.data["database_version"] = 2

    # ==========================================================
    # SAVE
    # ==========================================================

    def save(self):
        """
        Save the database to disk.
        """

        self.data["database_version"] = 2

        self.data["last_updated"] = (
            datetime.now().isoformat()
        )

        with open(
            self.filename,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.data,
                f,
                indent=2,
                ensure_ascii=False,
                default=str
            )

    # ==========================================================
    # SEASON KEY
    # ==========================================================

    @staticmethod
    def _season_key(season):
        """
        Return the standard string representation of a season.
        """

        return str(int(season))

    # ==========================================================
    # TIMESTAMP NORMALISATION
    # ==========================================================

    @staticmethod
    def _normalise_timestamp(value):
        """
        Convert a timestamp into a consistent ISO string.

        Returns
        -------
        str or None
        """

        if value is None:
            return None

        # pandas NaT
        if pd.isna(value):
            return None

        if isinstance(value, pd.Timestamp):

            return value.isoformat()

        if isinstance(value, datetime):

            return value.isoformat()

        # Strings are parsed where possible so that equivalent
        # timestamps have the same representation.

        try:

            parsed = pd.to_datetime(
                value,
                errors="coerce"
            )

            if not pd.isna(parsed):

                return parsed.isoformat()

        except Exception:
            pass

        return str(value)

    # ==========================================================
    # SEASON INITIALISATION
    # ==========================================================

    def _get_or_create_season(
        self,
        season
    ):
        """
        Return a season entry, creating it if necessary.
        """

        season_key = self._season_key(season)

        if season_key not in self.data["seasons"]:

            self.data["seasons"][season_key] = {
                "match_list": [],
                "matches": {},
                "match_metadata": {}
            }

        season_data = self.data["seasons"][season_key]

        season_data.setdefault(
            "match_list",
            []
        )

        season_data.setdefault(
            "matches",
            {}
        )

        season_data.setdefault(
            "match_metadata",
            {}
        )

        return season_data

    # ==========================================================
    # SYNCHRONISE SEASON
    # ==========================================================

    def sync_season(
        self,
        season,
        force=False
    ):
        """
        Synchronise one season with Play-Cricket.

        Parameters
        ----------
        season : int
            Play-Cricket season.

        force : bool
            If True, re-download every match detail.

        Returns
        -------
        dict
            Synchronisation summary.

        Notes
        -----
        The match list is always requested.

        Match details are only requested for:

            - new matches
            - changed matches
            - matches with insufficient metadata
            - all matches when force=True
        """

        season = int(season)

        season_data = self._get_or_create_season(
            season
        )

        print(
            f"Synchronising Play-Cricket season {season}..."
        )

        # ------------------------------------------------------
        # STEP 1
        # Get current match list
        # ------------------------------------------------------

        print(
            "Checking current match list..."
        )

        matches = self.api.get_all_matches(
            season=season
        )

        if matches.empty:

            print(
                f"No matches found for season {season}."
            )

            result = {
                "season": season,
                "matches_found": 0,
                "matches_new": 0,
                "matches_updated": 0,
                "matches_unchanged": 0,
                "matches_downloaded": 0,
                "matches_failed": 0,
                "api_calls": {
                    "match_list": 1,
                    "match_details": 0,
                    "total": 1
                }
            }

            self.last_sync = result

            return result

        # ------------------------------------------------------
        # STEP 2
        # Preserve complete current match list
        # ------------------------------------------------------

        season_data["match_list"] = (
            matches
            .copy()
            .to_dict(orient="records")
        )

        # ------------------------------------------------------
        # STEP 3
        # Create efficient remote match index
        # ------------------------------------------------------

        remote_matches = {}

        for _, match in matches.iterrows():

            match_id = match.get("id")

            if pd.isna(match_id):
                continue

            match_id = str(int(match_id))

            remote_matches[match_id] = match

        # ------------------------------------------------------
        # Counters
        # ------------------------------------------------------

        new_matches = 0
        updated_matches = 0
        unchanged_matches = 0
        downloaded = 0
        failed = 0

        # ------------------------------------------------------
        # STEP 4
        # Compare every remote match with local data
        # ------------------------------------------------------

        for match_id, remote_match in remote_matches.items():

            remote_last_updated = (
                self._normalise_timestamp(
                    remote_match.get(
                        "last_updated"
                    )
                )
            )

            local_detail = (
                season_data["matches"]
                .get(match_id)
            )

            local_metadata = (
                season_data["match_metadata"]
                .get(match_id)
            )

            # --------------------------------------------------
            # Determine whether download is required
            # --------------------------------------------------

            if force:

                needs_download = True
                match_type = "forced"

            elif local_detail is None:

                needs_download = True
                match_type = "new"

            elif local_metadata is None:

                # We have the detail but don't know when it was
                # downloaded relative to the remote version.
                #
                # Safest option is to refresh it once.

                needs_download = True
                match_type = "metadata_missing"

            else:

                local_last_updated = (
                    self._normalise_timestamp(
                        local_metadata.get(
                            "last_updated"
                        )
                    )
                )

                # If Play-Cricket gives us no timestamp we cannot
                # prove that the local record is current.
                #
                # Therefore refresh it.

                if remote_last_updated is None:

                    needs_download = True
                    match_type = "timestamp_missing"

                elif (
                    local_last_updated
                    != remote_last_updated
                ):

                    needs_download = True
                    match_type = "updated"

                else:

                    needs_download = False
                    match_type = "unchanged"

            # --------------------------------------------------
            # Existing and unchanged
            # --------------------------------------------------

            if not needs_download:

                unchanged_matches += 1

                continue

            # --------------------------------------------------
            # Count new / updated
            # --------------------------------------------------

            if match_type == "new":

                new_matches += 1

            elif match_type in (
                "updated",
                "metadata_missing",
                "timestamp_missing",
                "forced"
            ):

                updated_matches += 1

            # --------------------------------------------------
            # Download detail
            # --------------------------------------------------

            print(
                f"Downloading match {match_id} "
                f"({match_type})..."
            )

            try:

                detail = (
                    self.api
                    .get_match_detail(
                        int(match_id)
                    )
                )

                # ------------------------------------------------
                # Store raw API response unchanged
                # ------------------------------------------------

                season_data["matches"][match_id] = (
                    detail
                )

                # ------------------------------------------------
                # Store database metadata separately
                # ------------------------------------------------

                season_data[
                    "match_metadata"
                ][match_id] = {

                    "last_updated":
                        remote_last_updated,

                    "downloaded_at":
                        datetime.now().isoformat()
                }

                downloaded += 1

            except Exception as e:

                failed += 1

                print(
                    f"ERROR downloading "
                    f"{match_id}: {e}"
                )

        # ------------------------------------------------------
        # STEP 5
        # Save
        # ------------------------------------------------------

        self.save()

        # ------------------------------------------------------
        # STEP 6
        # API call accounting
        # ------------------------------------------------------

        api_calls = {
            "match_list": 1,
            "match_details": downloaded,
            "total": 1 + downloaded
        }

        result = {

            "season": season,

            "matches_found":
                len(remote_matches),

            "matches_new":
                new_matches,

            "matches_updated":
                updated_matches,

            "matches_unchanged":
                unchanged_matches,

            "matches_downloaded":
                downloaded,

            "matches_failed":
                failed,

            "api_calls":
                api_calls
        }

        self.last_sync = result

        # ------------------------------------------------------
        # REPORT
        # ------------------------------------------------------

        print()
        print("Synchronisation complete")
        print("--------------------------------")
        print(
            f"Matches found:       "
            f"{len(remote_matches)}"
        )
        print(
            f"New matches:         "
            f"{new_matches}"
        )
        print(
            f"Updated matches:     "
            f"{updated_matches}"
        )
        print(
            f"Unchanged matches:   "
            f"{unchanged_matches}"
        )
        print(
            f"Details downloaded:  "
            f"{downloaded}"
        )
        print(
            f"Failed:              "
            f"{failed}"
        )
        print()
        print("API calls")
        print("--------------------------------")
        print(
            f"Match list:          "
            f"{api_calls['match_list']}"
        )
        print(
            f"Match details:       "
            f"{api_calls['match_details']}"
        )
        print(
            f"Total:               "
            f"{api_calls['total']}"
        )

        return result

    # ==========================================================
    # BACKWARDS COMPATIBILITY
    # ==========================================================

    def download_season(
        self,
        season,
        force=False
    ):
        """
        Backwards-compatible alias for sync_season().

        New code should use sync_season().
        """

        return self.sync_season(
            season=season,
            force=force
        )

    # ==========================================================
    # SEASONS
    # ==========================================================

    def seasons(self):
        """
        Return seasons stored in the database.
        """

        return list(
            self.data["seasons"].keys()
        )

    # ==========================================================
    # MATCH LIST
    # ==========================================================

    def matches(
        self,
        season=None
    ):
        """
        Return the locally stored match list.

        This method NEVER calls the API.
        """

        if season is None:

            records = []

            for season_data in (
                self.data["seasons"].values()
            ):

                records.extend(
                    season_data.get(
                        "match_list",
                        []
                    )
                )

        else:

            season_key = self._season_key(
                season
            )

            season_data = (
                self.data["seasons"]
                .get(
                    season_key,
                    {}
                )
            )

            records = season_data.get(
                "match_list",
                []
            )

        return records

    # ==========================================================
    # MATCH
    # ==========================================================

    def match(
        self,
        match_id
    ):
        """
        Return locally stored raw match detail.

        This method NEVER calls the API.
        """

        match_id = str(int(match_id))

        for season_data in (
            self.data["seasons"].values()
        ):

            matches = season_data.get(
                "matches",
                {}
            )

            if match_id in matches:

                return matches[match_id]

        return None

    # ==========================================================
    # MATCH EXISTS
    # ==========================================================

    def has_match(
        self,
        match_id
    ):
        """
        Determine whether match detail exists locally.
        """

        return self.match(
            match_id
        ) is not None

    # ==========================================================
    # MATCH COUNT
    # ==========================================================

    def match_count(
        self,
        season=None
    ):
        """
        Return number of locally stored match details.
        """

        if season is None:

            return sum(
                len(
                    season_data.get(
                        "matches",
                        {}
                    )
                )
                for season_data
                in self.data["seasons"].values()
            )

        season_key = self._season_key(
            season
        )

        return len(
            self.data["seasons"]
            .get(
                season_key,
                {}
            )
            .get(
                "matches",
                {}
            )
        )

    # ==========================================================
    # MATCHES AS DATAFRAME
    # ==========================================================

    def matches_dataframe(
        self,
        season=None
    ):
        """
        Return the local match list as a pandas DataFrame.

        This method NEVER calls the API.
        """

        records = self.matches(
            season=season
        )

        if not records:
            return pd.DataFrame()

        return pd.json_normalize(
            records
        )

    # ==========================================================
    # MATCH DETAILS
    # ==========================================================

    def match_details(
        self,
        season=None
    ):
        """
        Return locally stored raw match details.

        This method NEVER calls the API.
        """

        if season is None:

            details = []

            for season_data in (
                self.data["seasons"].values()
            ):

                details.extend(
                    season_data
                    .get(
                        "matches",
                        {}
                    )
                    .values()
                )

            return details

        season_key = self._season_key(
            season
        )

        return list(
            self.data["seasons"]
            .get(
                season_key,
                {}
            )
            .get(
                "matches",
                {}
            )
            .values()
        )

    # ==========================================================
    # MATCH METADATA
    # ==========================================================

    def match_metadata(
        self,
        match_id
    ):
        """
        Return synchronisation metadata for a match.
        """

        match_id = str(int(match_id))

        for season_data in (
            self.data["seasons"].values()
        ):

            metadata = season_data.get(
                "match_metadata",
                {}
            )

            if match_id in metadata:

                return metadata[match_id]

        return None

    # ==========================================================
    # LAST SYNC
    # ==========================================================

    def last_sync_summary(self):
        """
        Return the result of the most recent synchronisation.
        """

        return self.last_sync

    # ==========================================================
    # PLAYERS
    # ==========================================================

    def players(
        self,
        season=None,
        club_id=None,
        team_id=None
    ):
        """
        Return players recorded in locally stored matches.

        One row is returned per:

            season / match / player / team

        This method NEVER calls the API.
        """

        records = []

        # ------------------------------------------------------
        # Select seasons
        # ------------------------------------------------------

        seasons = self.data.get(
            "seasons",
            {}
        )

        if season is not None:

            season_key = self._season_key(
                season
            )

            if season_key not in seasons:

                return pd.DataFrame()

            seasons = {
                season_key:
                    seasons[season_key]
            }

        # ------------------------------------------------------
        # Loop through seasons
        # ------------------------------------------------------

        for season_key, season_data in (
            seasons.items()
        ):

            matches = season_data.get(
                "matches",
                {}
            )

            # --------------------------------------------------
            # Loop through matches
            # --------------------------------------------------

            for match_id, match in (
                matches.items()
            ):

                player_groups = match.get(
                    "players",
                    []
                )

                if not player_groups:
                    continue

                # ------------------------------------------------
                # Extract player groups.
                #
                # Current API data has historically appeared in
                # more than one form, so support both:
                #
                #   {"home_team": [...]}
                #   {"away_team": [...]}
                #
                # and direct player dictionaries.
                # ------------------------------------------------

                home_players = []
                away_players = []
                direct_players = []

                for group in player_groups:

                    if not isinstance(
                        group,
                        dict
                    ):
                        continue

                    if "home_team" in group:

                        home_players.extend(
                            group.get(
                                "home_team"
                            ) or []
                        )

                    elif "away_team" in group:

                        away_players.extend(
                            group.get(
                                "away_team"
                            ) or []
                        )

                    elif (
                        "player_id" in group
                    ):

                        direct_players.append(
                            group
                        )

                # ------------------------------------------------
                # Helper
                # ------------------------------------------------

                def add_player(
                    player,
                    team_id_value,
                    team_name,
                    club_id_value,
                    club_name,
                    opposition_id,
                    opposition_name,
                    opposition_club_id,
                    opposition_club_name
                ):

                    record = player.copy()

                    record.update({

                        "season":
                            int(season_key),

                        "match_id":
                            int(
                                match.get(
                                    "id",
                                    match_id
                                )
                            ),

                        "team_id":
                            team_id_value,

                        "team_name":
                            team_name,

                        "club_id":
                            club_id_value,

                        "club_name":
                            club_name,

                        "opposition_id":
                            opposition_id,

                        "opposition_name":
                            opposition_name,

                        "opposition_club_id":
                            opposition_club_id,

                        "opposition_club_name":
                            opposition_club_name,

                        "venue":
                            match.get(
                                "ground_name"
                            ),

                        "match_date":
                            match.get(
                                "match_date"
                            )
                    })

                    records.append(record)

                # ------------------------------------------------
                # Home players
                # ------------------------------------------------

                for player in home_players:

                    add_player(
                        player,

                        match.get(
                            "home_team_id"
                        ),

                        match.get(
                            "home_team_name"
                        ),

                        match.get(
                            "home_club_id"
                        ),

                        match.get(
                            "home_club_name"
                        ),

                        match.get(
                            "away_team_id"
                        ),

                        match.get(
                            "away_team_name"
                        ),

                        match.get(
                            "away_club_id"
                        ),

                        match.get(
                            "away_club_name"
                        )
                    )

                # ------------------------------------------------
                # Away players
                # ------------------------------------------------

                for player in away_players:

                    add_player(
                        player,

                        match.get(
                            "away_team_id"
                        ),

                        match.get(
                            "away_team_name"
                        ),

                        match.get(
                            "away_club_id"
                        ),

                        match.get(
                            "away_club_name"
                        ),

                        match.get(
                            "home_team_id"
                        ),

                        match.get(
                            "home_team_name"
                        ),

                        match.get(
                            "home_club_id"
                        ),

                        match.get(
                            "home_club_name"
                        )
                    )

                # ------------------------------------------------
                # Direct player structure
                #
                # Use match-level information where the player
                # record itself contains team information.
                # ------------------------------------------------

                for player in direct_players:

                    player_team_id = player.get(
                        "team_id"
                    )

                    if (
                        player_team_id
                        == match.get(
                            "home_team_id"
                        )
                    ):

                        add_player(
                            player,

                            match.get(
                                "home_team_id"
                            ),

                            match.get(
                                "home_team_name"
                            ),

                            match.get(
                                "home_club_id"
                            ),

                            match.get(
                                "home_club_name"
                            ),

                            match.get(
                                "away_team_id"
                            ),

                            match.get(
                                "away_team_name"
                            ),

                            match.get(
                                "away_club_id"
                            ),

                            match.get(
                                "away_club_name"
                            )
                        )

                    elif (
                        player_team_id
                        == match.get(
                            "away_team_id"
                        )
                    ):

                        add_player(
                            player,

                            match.get(
                                "away_team_id"
                            ),

                            match.get(
                                "away_team_name"
                            ),

                            match.get(
                                "away_club_id"
                            ),

                            match.get(
                                "away_club_name"
                            ),

                            match.get(
                                "home_team_id"
                            ),

                            match.get(
                                "home_team_name"
                            ),

                            match.get(
                                "home_club_id"
                            ),

                            match.get(
                                "home_club_name"
                            )
                        )

        # ------------------------------------------------------
        # No data
        # ------------------------------------------------------

        if not records:

            return pd.DataFrame()

        df = pd.DataFrame(
            records
        )

        # ------------------------------------------------------
        # Normalise IDs
        # ------------------------------------------------------

        for column in [
            "season",
            "match_id",
            "player_id",
            "team_id",
            "club_id",
            "opposition_id",
            "opposition_club_id"
        ]:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        # ------------------------------------------------------
        # Filters
        # ------------------------------------------------------

        if club_id is not None:

            df = df[
                df["club_id"]
                == int(club_id)
            ]

        if team_id is not None:

            df = df[
                df["team_id"]
                == int(team_id)
            ]

        # ------------------------------------------------------
        # Remove duplicates
        # ------------------------------------------------------

        subset = [
            "season",
            "match_id",
            "player_id",
            "team_id"
        ]

        subset = [
            column
            for column in subset
            if column in df.columns
        ]

        if subset:

            df = df.drop_duplicates(
                subset=subset
            )

        # ------------------------------------------------------
        # Sort
        # ------------------------------------------------------

        sort_columns = [
            column
            for column in [
                "season",
                "match_date",
                "team_id",
                "position"
            ]
            if column in df.columns
        ]

        if sort_columns:

            df = df.sort_values(
                sort_columns,
                na_position="last"
            )

        return df.reset_index(
            drop=True
        )

    # ==========================================================
    # PLAYER APPEARANCES
    # ==========================================================

    def player_appearances(
        self,
        season=None,
        club_id=None,
        team_id=None,
        player_id=None
    ):
        """
        Return one row per player/match appearance.

        This is derived entirely from the local database.

        It does NOT call the API.
        """

        df = self.players(
            season=season,
            club_id=club_id,
            team_id=team_id
        )

        if df.empty:

            return df

        if player_id is not None:

            df = df[
                df["player_id"]
                == int(player_id)
            ]

        return (
            df
            .drop_duplicates(
                subset=[
                    "match_id",
                    "player_id"
                ]
            )
            .reset_index(
                drop=True
            )
        )

    # ==========================================================
    # CLUBS
    # ==========================================================

    def clubs(
        self,
        season=None
    ):
        """
        Return all clubs represented locally.
        """

        records = []

        for match in self.match_details(
            season=season
        ):

            records.append({

                "club_id":
                    match.get(
                        "home_club_id"
                    ),

                "club_name":
                    match.get(
                        "home_club_name"
                    )
            })

            records.append({

                "club_id":
                    match.get(
                        "away_club_id"
                    ),

                "club_name":
                    match.get(
                        "away_club_name"
                    )
            })

        if not records:

            return pd.DataFrame()

        return (
            pd.DataFrame(records)
            .drop_duplicates()
            .sort_values(
                "club_name"
            )
            .reset_index(
                drop=True
            )
        )

    # ==========================================================
    # TEAMS
    # ==========================================================

    def teams(
        self,
        season=None,
        club_id=None
    ):
        """
        Return all teams represented locally.
        """

        records = []

        for match in self.match_details(
            season=season
        ):

            records.append({

                "team_id":
                    match.get(
                        "home_team_id"
                    ),

                "team_name":
                    match.get(
                        "home_team_name"
                    ),

                "club_id":
                    match.get(
                        "home_club_id"
                    ),

                "club_name":
                    match.get(
                        "home_club_name"
                    )
            })

            records.append({

                "team_id":
                    match.get(
                        "away_team_id"
                    ),

                "team_name":
                    match.get(
                        "away_team_name"
                    ),

                "club_id":
                    match.get(
                        "away_club_id"
                    ),

                "club_name":
                    match.get(
                        "away_club_name"
                    )
            })

        if not records:

            return pd.DataFrame()

        df = (
            pd.DataFrame(records)
            .drop_duplicates()
        )

        if club_id is not None:

            df = df[
                pd.to_numeric(
                    df["club_id"],
                    errors="coerce"
                )
                == int(club_id)
            ]

        return (
            df
            .sort_values(
                [
                    "club_name",
                    "team_name"
                ]
            )
            .reset_index(
                drop=True
            )
        )

    # ==========================================================
    # REPRESENTATION
    # ==========================================================

    def __repr__(self):

        return (
            f"PlayCricketDatabase("
            f"filename='{self.filename}', "
            f"seasons={self.seasons()})"
        )