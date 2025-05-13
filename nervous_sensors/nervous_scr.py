import traceback

import numpy as np
from nervous_analytics.analyzers import EDAAnalyzer

from .data_manager import DataManager
from .nervous_eda import NervousEDA
from .nervous_virtual import NervousVirtual

SCR_UPDATE_INTERVAL = 5  # seconds


class SCRDataManager(DataManager):
    def __init__(self, sensor_name, sampling_rate, start_time):
        super().__init__(
            sensor_name=sensor_name,
            sampling_rate=sampling_rate,
            header=["Time (s)", "SCR amp. (uS)", "SCR ris.t. (s)", "SCL (uS)"],
            start_time=start_time,
            codec=None,
        )

    # implements
    def _process_decoded_data(self, timestamp, data):
        try:
            data_to_add = []
            for i in range(len(timestamp)):
                data_to_add.append(np.hstack((timestamp[i], data[i])).tolist())
                # data_to_add.append([[timestamp[i]] + data[i]])
            self._add_data(data_to_add)
        except Exception as Argument:
            print("SCR DEC: ", str(Argument))


class NervousSCR(NervousVirtual):
    def __init__(self, eda_sensor: NervousEDA, start_time, timeout, connection_manager):
        name = eda_sensor.get_name().replace("EDA", "SCR")
        super().__init__(
            "SCR",
            name=name,
            sensor=eda_sensor,
            start_time=start_time,
            update_time=SCR_UPDATE_INTERVAL,
            timeout=timeout,
            connection_manager=connection_manager,
        )
        # This overrides the empty DataManager of NervousSensor
        self._data_manager = SCRDataManager(sensor_name=name, sampling_rate=0, start_time=start_time)
        self._latest_data = 0
        self._labels = ["SCR amp.", "SCR ris.t.", "SCL"]
        self._units = ["uS", "s", "uS"]
        self._analyzer = EDAAnalyzer(fs=eda_sensor.get_sampling_rate(), window_duration=20, history_size=20)
        self._channel_count = 3
        self._plot_type = "bar"

    # override enabling notifications to reinit SCR detection
    async def start_notifications(self) -> bool:
        # self._analyzer._reinit_history()
        return await super().start_notifications()

    # This overrides the empty method of NervousVirtual and is called every SCR_UPDATE_INTERVAL
    def _process_data(self):
        # Check for new samples since last processed
        data = self._sensor.data_manager.get_latest_data(latest_data=self._latest_data)
        if len(data.index) == 0:
            return
        # Every samples are processed by the analyzer so we save the latest sample timestamp
        self._latest_data = data.iloc[-1, 0]
        # Check if electrodes are connected
        min_value = np.min(data["EDA (uS)"])
        if min_value < 0.2:
            print(self.get_name(), "Electrode disconnection detected")
            return
        # Process samples
        try:
            amplitude, duration, level, timestamp = self._analyzer.update_eda_peak(
                data["EDA (uS)"].tolist(), data["Time (s)"].tolist()
            )
            if not timestamp:
                return
            timestamp = np.array(timestamp)
            amplitude = np.array(amplitude)
            duration = np.array(duration)
            level = np.array(level)
            data_tosend = np.column_stack((amplitude, duration, level))
            # Add data to the data manager, with a list of timestamps and a list of SCR tuples
            self._data_manager._process_decoded_data(timestamp=timestamp, data=data_tosend)
        except Exception as Argument:
            print("SCR PROC: ", str(Argument))
            tb = traceback.format_exc()
            print(tb)
