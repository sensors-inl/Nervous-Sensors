import logging
import traceback

from nervous_analytics.analyzers import ECGAnalyzer

from .data_manager import DataManager
from .nervous_ecg import NervousECG
from .nervous_virtual import NervousVirtual

HR_UPDATE_INTERVAL = 1  # seconds
logger = logging.getLogger("nervous")


class NervousHR(NervousVirtual):
    """
    A virtual sensor for calculating heart rate from ECG data.

    This class extends NervousVirtual to create a derived measure (heart rate)
    from a physical sensor (ECG). It uses a signal processing algorithm to
    detect heart beats and calculate heart rate.

    Attributes:
        _data_manager (HRDataManager): Manager for HR data
        _latest_data (float): Timestamp of the last processed ECG data
        _labels (list): List of data labels (["HR"])
        _units (list): List of measurement units (["BPM"])
        _analyzer (ECGAnalyzer): Analyzer for computing HR from ECG
        _plot_type (str): Type of plot to use for visualizing data
    """

    def __init__(self, ecg_sensor: NervousECG, start_time, timeout, connection_manager):
        """
        Initialize the heart rate virtual sensor.

        Args:
            ecg_sensor (NervousECG): ECG sensor to derive HR from
            start_time (float): Timestamp marking the start of data collection
            timeout (float): Connection timeout in seconds
            connection_manager: Manager handling connection events
        """
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
        self._labels = ["HR"]
        self._units = ["BPM"]
        self._analyzer = ECGAnalyzer(fs=ecg_sensor.get_sampling_rate(), window_duration=5, history_size=5)
        self._plot_type = "bar"
        self._electrode_status = "both on"

    # override enabling notifications to reinit HR detection
    async def start_notifications(self) -> bool:
        """
        Start notifications and reinitialize HR detection algorithm.

        Returns:
            bool: Success status
        """
        self._analyzer._reinit_history()
        return await super().start_notifications()

    # This overrides the empty method of NervousVirtual and is called every HR_UPDATE_INTERVAL
    def _process_data(self):
        """
        Process new ECG data to extract heart rate.

        Fetches new ECG data since last processing, checks electrode status,
        and calculates heart rate using the ECG analyzer.
        """
        # Check for new samples since last processed
        data = self._sensor.data_manager.get_latest_data(latest_data=self._latest_data)
        if len(data.index) == 0:
            return
        # Every samples are processed by the analyzer so we save the latest sample timestamp
        self._latest_data = data.iloc[-1, 0]
        # Check if electrodes are connected
        electrode_status = self._sensor.get_electrode_status()
        if electrode_status != self._electrode_status:
            self._electrode_status = electrode_status
            if electrode_status != "both on":
                logger.warning("%s Electrode disconnection detected", self.get_colored_name())
            else:
                logger.info("%s Electrodes connected", self.get_colored_name())
        # Skip processing if electrodes are disconnected
        if electrode_status != "both on":
            return

        # Process samples
        try:
            heart_rate, heart_rate_timestamp, _ = self._analyzer.update_hr(
                data["ECG (A.U.)"].tolist(), data["Time (s)"].tolist()
            )
            # Add data to the data manager, with a list of timestamps and a list of HR values
            if heart_rate is not None:
                self._data_manager._process_decoded_data(timestamp=heart_rate_timestamp, data=heart_rate)
        except Exception as e:
            logger.error("%s Processing error: %s", self.get_colored_name(), str(e))
            logger.debug(traceback.format_exc())


class HRDataManager(DataManager):
    """
    Data manager for heart rate (HR) data derived from ECG.

    This class processes and stores heart rate data calculated from ECG.

    Attributes:
        _sampling_rate (int): Always 0 as HR is irregularly sampled
    """

    def __init__(self, sensor_name, sampling_rate, start_time):
        """
        Initialize the HR data manager.

        Args:
            sensor_name (str): Name of the associated sensor
            sampling_rate (int): Usually 0 as HR is irregularly sampled
            start_time (float): Timestamp marking the start of data collection
        """
        super().__init__(
            sensor_name=sensor_name,
            sampling_rate=sampling_rate,
            header=["Time (s)", "HR (BPM)"],
            start_time=start_time,
            codec=None,
        )

    # implements
    def _process_decoded_data(self, timestamp, data):
        """
        Process heart rate data.

        Add heart rate values with their respective timestamps to the data store.

        Args:
            timestamp (list): List of timestamps for each HR value
            data (list): List of HR values in BPM
        """
        try:
            data_to_add = []
            for i in range(len(data)):
                data_to_add.append([timestamp[i], data[i]])
            self._add_data(data_to_add)
        except Exception as e:
            logger.error("HR processing error: %s", str(e), exc_info=True)
