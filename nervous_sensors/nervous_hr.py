from nervous_analytics.analyzers import ECGAnalyzer

from .data_manager import DataManager
from .nervous_ecg import NervousECG
from .nervous_virtual import NervousVirtual

HR_UPDATE_INTERVAL = 1  # seconds


class HRDataManager(DataManager):
    def __init__(self, sensor_name, sampling_rate, start_time):
        super().__init__(
            sensor_name=sensor_name,
            sampling_rate=sampling_rate,
            header=["Time (s)", "HR (BPM)"],
            start_time=start_time,
            codec=None,
        )

    # implements
    def _process_decoded_data(self, timestamp, data):
        try:
            data_to_add = []
            for i in range(len(data)):
                data_to_add.append([timestamp[i], data[i]])
            self._add_data(data_to_add)
        except Exception as Argument:
            print("HR ERROR: ", str(Argument))


class NervousHR(NervousVirtual):
    def __init__(self, ecg_sensor: NervousECG, start_time, timeout, connection_manager):
        name = ecg_sensor.get_name().replace("ECG", "HR")
        super().__init__(
            "HR",
            name=name,
            sensor=ecg_sensor,
            start_time=start_time,
            update_time=HR_UPDATE_INTERVAL,
            timeout=timeout,
            connection_manager=connection_manager,
        )
        # This overrides the empty DataManager of NervousSensor
        self._data_manager = HRDataManager(sensor_name=name, sampling_rate=0, start_time=start_time)
        self._latest_data = 0
        self._unit = "BPM"
        self._analyzer = ECGAnalyzer(fs=ecg_sensor.get_sampling_rate(), window_duration=5, history_size=5)

    # override enabling notifications to reinit HR detection
    async def start_notifications(self) -> bool:
        self._analyzer._reinit_history()
        return await super().start_notifications()

    # This overrides the empty method of NervousVirtual and is called every HR_UPDATE_INTERVAL
    def _process_data(self):
        # Check for new samples since last processed
        data = self._sensor.data_manager.get_latest_data(latest_data=self._latest_data)
        # Process the new samples
        if len(data.index) == 0:
            return
        try:
            heart_rate, heart_rate_timestamp, _ = self._analyzer.update_hr(
                data["ECG (A.U.)"].tolist(), data["Time (s)"].tolist()
            )
            # Debug heart rate values
            print(heart_rate)
            # Add data to the data manager, with a list of timestamps and a list of HR values
            if heart_rate is not None:
                self._data_manager._process_decoded_data(timestamp=heart_rate_timestamp, data=heart_rate)
        except Exception as Argument:
            print("HR ERROR: ", str(Argument))
        # Every samples are processed by the analyzer so we save the latest sample timestamp
        self._latest_data = data.iloc[-1, 0]
