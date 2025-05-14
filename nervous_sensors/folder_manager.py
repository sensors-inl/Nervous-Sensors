import asyncio
import csv
import logging
import os
import traceback

from .async_manager import AsyncManager

logger = logging.getLogger("nervous")


class FolderManager(AsyncManager):
    """
    Manages the storage of sensor data to CSV files in a specified folder.

    This class periodically writes sensor data to CSV files, creating a separate file
    for each sensor. It handles file creation, appending new data, and manages
    file paths.

    Attributes:
        _sensor_times: List of dictionaries containing sensor objects and their last write time.
        _folder_path: Path to the folder where CSV files will be saved.
        _update_time: Time interval in seconds between data writes.
    """

    def __init__(self, sensors, folder_path, update_time=5.0):
        """
        Initialize the folder manager.

        Args:
            sensors: List of sensor objects to monitor.
            folder_path: Directory path where CSV files will be stored.
            update_time: Time interval in seconds between data writes (default: 5.0).
        """
        super().__init__()
        self._sensor_times = [
            {
                "sensor": sensor,
                "time": 0,
            }
            for sensor in sensors
        ]
        self._folder_path = folder_path
        self._update_time = update_time

        try:
            # Create the folder if it does not exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)

            # Create the csv files with header
            for sensor_time in self._sensor_times:
                sensor = sensor_time["sensor"]
                path = self.get_path(sensor)
                header = sensor.data_manager.get_header()
                with open(path, "w", newline="") as f_object:
                    writer = csv.DictWriter(f_object, fieldnames=header, delimiter=";")
                    writer.writeheader()
        except Exception as e:
            logger.error(f"Error initializing folder manager: {str(e)}")
            logger.debug(traceback.format_exc())
            raise

    def get_path(self, sensor):
        """
        Generate the file path for a specific sensor.

        Args:
            sensor: The sensor object for which to generate a file path.

        Returns:
            str: The complete file path for the sensor's CSV file.
        """
        name = sensor.get_name()
        return f"{self._folder_path}/{sensor.get_start_time_str()}_{name}.csv"

    async def start(self):
        """
        Start the folder manager to periodically write sensor data to CSV files.

        Runs a loop that periodically writes all sensor data to their respective CSV files
        until the stop event is set.
        """
        logger.info("Starting Folder manager")
        logger.info(f"Data files will be created in folder {self._folder_path}")

        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._update_time)
                await self.write_all_csv()
            except asyncio.TimeoutError:
                await self.write_all_csv()
            except Exception as e:
                logger.error(f"Error in folder manager loop: {str(e)}")
                logger.debug(traceback.format_exc())

    async def stop(self):
        """
        Stop the folder manager.

        Sets the stop event to terminate the running loop.
        """
        logger.info("Stopping Folder manager")
        self._stop_event.set()

    async def write_all_csv(self):
        """
        Write data from all sensors to their respective CSV files.

        Creates a task for each sensor to write its data concurrently.
        """
        try:
            async with asyncio.TaskGroup() as tg:
                for sensor_time in self._sensor_times:
                    tg.create_task(self.write_csv(sensor_time))
        except Exception as e:
            logger.error(f"Error writing all CSV files: {str(e)}")
            logger.debug(traceback.format_exc())

    async def write_csv(self, sensor_time):
        """
        Write data from a specific sensor to its CSV file.

        Only writes data that has been collected since the last write operation.

        Args:
            sensor_time: Dictionary containing the sensor object and its last write time.
        """
        sensor = sensor_time["sensor"]
        time = sensor_time["time"]
        file_path = self.get_path(sensor)

        try:
            with open(file_path, "a", newline="") as f_object:
                writer_object = csv.writer(f_object, delimiter=";")
                new_data = sensor.data_manager.get_latest_data(latest_data=time)
                rows = new_data.values.tolist()
                writer_object.writerows(rows)
                if not new_data.empty:
                    sensor_time["time"] = new_data.iloc[-1, 0]
        except Exception as e:
            logger.error(f"Error writing CSV for sensor {sensor.get_name()}: {str(e)}")
            logger.debug(traceback.format_exc())
