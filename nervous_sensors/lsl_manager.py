import asyncio

from pylsl import StreamInfo, StreamOutlet, local_clock

from .async_manager import AsyncManager
from .cli_utils import print_start_info, print_stop_info


class LSLManager(AsyncManager):
    _start_time_lsl = local_clock()

    def __init__(self, sensors, update_time=0.5):
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
        print("LSL offset clock:", self._start_time_lsl)
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._update_time)
                self.send_data()
            except TimeoutError:
                self.send_data()

    def send_data(self):
        for sensor_lsl in self._sensors_lsl:
            self.send_data_generic(sensor_lsl)

    async def stop(self):
        print_stop_info("Stopping LSL manager")
        self._stop_event.set()

    def send_data_generic(self, sensor_lsl):
        sensor = sensor_lsl["sensor"]
        outlet = sensor_lsl["outlet"]
        time = sensor_lsl["time"]
        data = sensor.data_manager.get_latest_data(latest_data=time)
        try:
            sensor_lsl["time"] = data.iloc[-1, 0]
            data.iloc[:, 0] = data.iloc[:, 0] + LSLManager._start_time_lsl
            timestamp_list = data.iloc[:, 0].tolist()
            data_list = data.iloc[:, 1].tolist()
            outlet.push_chunk(
                x=data_list,
                timestamp=timestamp_list,
                pushthrough=True,
            )
        except IndexError:
            pass  # No data to send
