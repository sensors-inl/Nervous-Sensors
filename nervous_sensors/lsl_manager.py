import asyncio

from pylsl import StreamInfo, StreamOutlet, local_clock

from .async_manager import AsyncManager
from .cli_utils import print_start_info, print_stop_info


class LSLManager(AsyncManager):
    _start_time_lsl = local_clock()

    def __init__(self, sensors, update_time=0.01):
        super().__init__()
        self._sensors_lsl = [
            {
                "sensor": sensor,
                "outlet": None,
                "time": 0,
            }
            for sensor in sensors
        ]
        self._update_time = update_time

        for sensor_lsl in self._sensors_lsl:
            sensor = sensor_lsl["sensor"]
            name = sensor.get_name()
            type = sensor.get_type()
            sampling_rate = sensor.get_sampling_rate()
            stream_info = StreamInfo(name, type, 1, sampling_rate, "float32", name)
            sensor_lsl["outlet"] = StreamOutlet(stream_info)

    async def start(self):
        print_start_info("Starting LSL manager")
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._update_time)
                self.send_data()
            except TimeoutError:
                self.send_data()

    def send_data(self):
        for sensor_lsl in self._sensors_lsl:
            sensor = sensor_lsl["sensor"]
            if sensor.get_type() == "ECG":
                self.send_ecg_data(sensor_lsl)
            else:
                self.send_eda_data(sensor_lsl)

    async def stop(self):
        print_stop_info("Stopping LSL manager")
        self._stop_event.set()

    def send_ecg_data(self, sensor_lsl):
        sensor = sensor_lsl["sensor"]
        outlet = sensor_lsl["outlet"]
        time = sensor_lsl["time"]

        # Offset to use timestamp of the first sample
        # https://github.com/labstreaminglayer/pylsl/blob/master/pylsl/pylsl.py#L463C2-L467C47
        data = sensor.data_manager.get_latest_data(latest_data=time)

        try:
            first_timestamp = data.iloc[0, 0]
            last_timestamp = data.iloc[-1, 0]
            data_list = data.iloc[:, 1].tolist()
            timestamp_offset = (len(data_list) - 1) * 1 / sensor.get_sampling_rate()
            sensor_lsl["time"] = last_timestamp

            if len(data_list) != 100:
                return

            outlet.push_chunk(
                data_list,
                timestamp=first_timestamp + LSLManager._start_time_lsl + timestamp_offset,
                pushthrough=True,
            )
        except IndexError:
            pass  # No data to send

    def send_eda_data(self, sensor_lsl):
        sensor = sensor_lsl["sensor"]
        outlet = sensor_lsl["outlet"]
        time = sensor_lsl["time"]

        data = sensor.data_manager.get_latest_data(latest_data=time)

        try:
            timestamp = data.iloc[-1, 0]
            data_list = data.iloc[:, 1].tolist()
            data = data_list[0]
            sensor_lsl["time"] = timestamp

            if len(data_list) > 1:
                return

            outlet.push_sample(
                [data],
                timestamp=timestamp + LSLManager._start_time_lsl,
                pushthrough=True,
            )
        except IndexError:
            pass  # No data to send
