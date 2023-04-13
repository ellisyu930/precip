import os
from typing import Annotated
import netCDF4 as nc
import xarray as xr
import numpy as np
import pandas as pd

from fastapi import Depends
from settings import get_settings, DevSettings, ProdSettings

# Import the logging configuration module
from logging_config import get_logger

logger = get_logger(__name__)


class PrecipitationData:
    def __init__(self, url, settings: (DevSettings | ProdSettings | None)):
        self.settings = settings
        self.url = url
        self.data = None
        self.target_coords = None

    def get_curr_time_value(self):
        logger.info(self.url)

        with xr.open_dataset(self.url) as ds:
            # Select the last specified days of data
            time_values = ds["time"].values
            curr_time_value: np.datetime64 = time_values[-1]
        return curr_time_value

    def get_previous_time_value(self):
        file_path = os.path.join("data", self.settings.PREV_TIME_FILENAME)

        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                prev_time_value = np.datetime64(file.read().strip())
        else:
            prev_time_value = np.datetime64("1970-01-01T00:00:00")

        return prev_time_value

    def update_previous_time_value(self, curr_time_value):
        file_path = os.path.join("data", self.settings.PREV_TIME_FILENAME)

        with open(file_path, "w") as file:
            file.write(str(curr_time_value))

    def read_data(self):
        nearest_precip_data = None

        logger.info(self.url)

        with xr.open_dataset(self.url) as ds:
            # Select the last specified days of data
            last_specified_days = ds.isel(
                time=slice(-1 * self.settings.EXTRACTED_DAYS, None)
            )

            # Read the target coordinates from a CSV file
            self._read_target_coords()

            for index, target in self.target_coords.iterrows():
                # Extract the precipitation data at the nearest locations to the target coordinates
                nearest_point_i = last_specified_days.sel(
                    lat=target["Lat"],
                    lon=target["Lon"],
                    method="nearest",
                ).load()

                # Add the location name as a new coordinate to the nearest_point_i dataset
                nearest_point_i = nearest_point_i.assign_coords(
                    location=target["Location"]
                )

                # concatenate the nearest_point_i dataset with the nearest_point dataset
                if nearest_precip_data is None:
                    nearest_precip_data = nearest_point_i
                else:
                    nearest_precip_data = xr.concat(
                        [nearest_precip_data, nearest_point_i], dim="time"
                    )

            # Convert the precipitation data to a Numpy array and store it in the data attribute
            self.data = nearest_precip_data

    def compute_statistics(self):
        if self.data is None:
            self.read_data()
        mean = np.mean(self.data)
        median = np.median(self.data)
        std_dev = np.std(self.data)
        return mean, median, std_dev

    def extract_subset(self, start_date, end_date):
        if self.data is None:
            self.read_data()
        mask = (self.data["time"] >= start_date) & (self.data["time"] <= end_date)
        subset = self.data.loc[mask]
        return subset

    def save_to_csv(self, output_file):
        df_all = None

        if self.data is None:
            self.read_data()
        df = self.data.to_dataframe()

        # Create a new DataFrame with columns "Time" and location names from the target coordinates file
        # time_col = df["time"]
        # loc_cols = [row["Location"] for i, row in self.target_coords.iterrows()]
        # data_cols = [time_col] + [df[loc] for loc in loc_cols]
        # new_df = pd.concat(data_cols, axis=1)

        # create a list of unique locations in the original dataframe in the order they appear
        location_order = df["location"].unique().tolist()

        # create the pivot table with the specified column order
        df_all = df.pivot_table(
            index="time",
            columns="location",
            values="precip",
            aggfunc="mean",
        )

        # reindex the columns in the pivot table to match the original order
        df_all = df_all.reindex(columns=location_order)

        # df_loc = self.data.to_dataframe()
        # del df_loc["lat"]
        # del df_loc["lon"]
        # df_loc.shape
        # new_col = loc.Location
        # df_loc.rename(columns={"precip": new_col}, inplace=True)
        # if df_all is None:
        #     df_all = df_loc
        # else:
        #     df_all = pd.merge(df_all, df_loc, on=["time"])

        # Write the new DataFrame to a CSV file
        df_all.to_csv(output_file, index=True)

    def _find_nearest_locations(self, precip_data):
        if self.target_coords is None:
            self._read_target_coords()

        # Find the indices of the nearest locations to the target coordinates
        lat_diff = precip_data["lat"] - self.target_coords["Lat"]
        lon_diff = precip_data["lon"] - self.target_coords["Lon"]
        distance = np.sqrt(lat_diff**2 + lon_diff**2)
        nearest_indices = np.unravel_index(np.argmin(distance), distance.shape)

        # Extract the latitudes and longitudes of the nearest locations
        nearest_lat = precip_data["lat"].isel(lat=nearest_indices[0]).values
        nearest_lon = precip_data["lon"].isel(lon=nearest_indices[1]).values

        # Return the nearest locations as a dictionary
        return {"lat": nearest_lat, "lon": nearest_lon}

    def _read_target_coords(self):
        try:
            target_coord_file = os.path.join(
                "data", self.settings.TARGET_COORD_FILENAME
            )
            df = pd.read_csv(target_coord_file)
            logger.info(df)

        except:
            logger.critical("File <target_coord.csv> doesn't exist")
            raise
        else:
            df["Lon"] = self._convert_longitude(df["Lon"], from_360_to_180=False)
            self.target_coords = df

    def _convert_longitude(
        self,
        lon_values,
        from_360_to_180: Annotated[
            bool, "Whether to convert from 360 to 180 or vice versa"
        ] = True,
    ):
        """
        Converts longitude values from 360 to 180 or vice versa.

        Parameters:
            lon_values (array-like): The longitude values to be converted.
            from_360_to_180 (bool): Whether to convert from 360 to 180 or vice versa. Defaults to True.

        Returns:
            The converted longitude values.
        """

        if from_360_to_180:
            # convert from 360 to 180
            lon_values = (lon_values + 180) % 360 - 180
            # lon_values[lon_values > 180] -= 360
        else:
            # convert from 180 to 360
            lon_values = (lon_values) % 360
            # lon_values[lon_values < 0] += 360

        return lon_values
