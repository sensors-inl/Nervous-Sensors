import logging
import traceback

import numpy as np
from nervous_analytics.analyzers import EDAAnalyzer

from .data_manager import DataManager
from .nervous_eda import NervousEDA
from .nervous_virtual import NervousVirtual

SCR_UPDATE_INTERVAL = 5  # seconds
logger = logging.getLogger("nervous")


class NervousSCR(NervousVirtual):
    """
    A virtual sensor for calculating Skin Conductance Response (SCR) from EDA data.

    This class extends NervousVirtual to create derived measures (SCR parameters)
    from a physical sensor (EDA). It uses a signal processing algorithm to
    detect and characterize skin conductance responses.

    Attributes:
        _data_manager (SCRDataManager): Manager for SCR data
        _latest_data (float): Timestamp of the last processed EDA data
        _labels (list): List of data labels (["SCR amp.", "SCR ris.t.", "SCL"])
        _units (list): List of measurement units (["uS", "s", "uS"])
        _analyzer (EDAAnalyzer): Analyzer for computing SCR from EDA
        _channel_count (int): Number of measurement channels (3)
        _plot_type (str): Type of plot to use for visualizing data
    """

    def __init__(self, eda_sensor: NervousEDA, start_time, timeout, connection_manager):
        """
        Initialize the SCR virtual sensor.

        Args:
            eda_sensor (NervousEDA): EDA sensor to derive SCR from
            start_time (float): Timestamp marking the start of data collection
            timeout (float): Connection timeout in seconds
            connection_manager: Manager handling connection events
        """
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
        self._electrode_status = "connected"

    # override enabling notifications to reinit SCR detection
    async def start_notifications(self) -> bool:
        """
        Start notifications.
        SCR detection reinitialization is commented out but preserved for future use.

        Returns:
            bool: Success status
        """
        # self._analyzer._reinit_history()
        return await super().start_notifications()

    # This overrides the empty method of NervousVirtual and is called every SCR_UPDATE_INTERVAL
    def _process_data(self):
        """
        Process new EDA data to extract SCR parameters.

        Fetches new EDA data since last processing, checks electrode connection,
        and calculates SCR parameters using the EDA analyzer.
        """
        # Check for new samples since last processed
        data = self._sensor.data_manager.get_latest_data(latest_data=self._latest_data)
        if len(data.index) == 0:
            return
        # Every samples are processed by the analyzer so we save the latest sample timestamp
        self._latest_data = data.iloc[-1, 0]
        # Check if electrodes are connected
        electrode_status = "connected"
        min_value = np.min(data["EDA (uS)"])
        if min_value < 0.2:
            electrode_status = "disconnected"
        if electrode_status != self._electrode_status:
            self._electrode_status = electrode_status
            if electrode_status != "connected":
                logger.warning("%s Electrode disconnection detected", self.get_colored_name())
            else:
                logger.info("%s Electrodes connected", self.get_colored_name())
        # Skip processing if electrodes are disconnected
        if electrode_status != "connected":
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
        except Exception as e:
            logger.error("%s Processing error: %s", self.get_colored_name(), str(e))
            logger.debug(traceback.format_exc())


class SCRDataManager(DataManager):
    """
    Data manager for Skin Conductance Response (SCR) data derived from EDA.

    This class processes and stores SCR data calculated from EDA measurements.

    Attributes:
        _sampling_rate (int): Always 0 as SCR is irregularly sampled
    """

    def __init__(self, sensor_name, sampling_rate, start_time):
        """
        Initialize the SCR data manager.

        Args:
            sensor_name (str): Name of the associated sensor
            sampling_rate (int): Usually 0 as SCR is irregularly sampled
            start_time (float): Timestamp marking the start of data collection
        """
        super().__init__(
            sensor_name=sensor_name,
            sampling_rate=sampling_rate,
            header=["Time (s)", "SCR amp. (uS)", "SCR ris.t. (s)", "SCL (uS)"],
            start_time=start_time,
            codec=None,
        )

    # implements
    def _process_decoded_data(self, timestamp, data):
        """
        Process SCR data.

        Add SCR data points with their respective timestamps to the data store.
        Each data point contains SCR amplitude, rise time, and skin conductance level.

        Args:
            timestamp (list): List of timestamps for each SCR event
            data (ndarray): Array containing SCR parameters for each event
                            (amplitude, rise time, skin conductance level)
        """
        try:
            data_to_add = []
            for i in range(len(timestamp)):
                data_to_add.append(np.hstack((timestamp[i], data[i])).tolist())
                # data_to_add.append([[timestamp[i]] + data[i]])
            self._add_data(data_to_add)
        except Exception as e:
            logger.error("SCR data processing error: %s", str(e), exc_info=True)
