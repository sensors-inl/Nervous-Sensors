import asyncio
import csv
import os

from .async_manager import AsyncManager
from .cli_utils import print_start_info, print_stop_info


class FolderManager(AsyncManager):
    def __init__(self, sensors, folder_path, update_time=5.0):
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

    def get_path(self, sensor):
        name = sensor.get_name()
        return f"{self._folder_path}/{sensor.get_start_time_str()}_{name[3:]}_{name[3:]}.csv"

    async def start(self):
        print_start_info("Starting folder manager")
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._update_time)
                await self.write_all_csv()
            except TimeoutError:
                await self.write_all_csv()

    async def stop(self):
        print_stop_info("Stopping folder manager")
        self._stop_event.set()

    async def write_all_csv(self):
        async with asyncio.TaskGroup() as tg:
            for sensor_time in self._sensor_times:
                tg.create_task(self.write_csv(sensor_time))

    async def write_csv(self, sensor_time):
        sensor = sensor_time["sensor"]
        time = sensor_time["time"]
        file_path = self.get_path(sensor)

        with open(file_path, "a", newline="") as f_object:
            writer_object = csv.writer(f_object, delimiter=";")
            new_data = sensor.data_manager.get_latest_data(latest_data=time)
            rows = new_data.values.tolist()
            writer_object.writerows(rows)
            if not new_data.empty:
                sensor_time["time"] = new_data.iloc[-1, 0]
