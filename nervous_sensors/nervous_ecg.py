import logging

import numpy as np

from . import pb2
from .codec import Codec
from .data_manager import DataManager
from .nervous_sensor import NervousSensor

ECG_SAMPLING_RATE = 512
logger = logging.getLogger("nervous")


class NervousECG(NervousSensor):
    """
    A sensor class for managing ECG (electrocardiogram) data acquisition.

    This class extends the NervousSensor base class and provides specific
    implementations for ECG data collection and processing.

    Attributes:
        _data_manager (ECGDataManager): Manager for ECG data processing and storage
        _labels (list): List of data labels (["ECG"])
        _units (list): List of measurement units (["a.u."])
    """

    def __init__(self, name, start_time, timeout, connection_manager):
        """
        Initialize the ECG sensor.

        Args:
            name (str): Sensor name
            start_time (float): Timestamp marking the start of data collection
            timeout (float): Connection timeout in seconds
            connection_manager: Manager handling connection events
        """
        super().__init__(name=name, start_time=start_time, timeout=timeout, connection_manager=connection_manager)
        # override
        self._data_manager = ECGDataManager(sensor_name=name, sampling_rate=ECG_SAMPLING_RATE, start_time=start_time)
        self._labels = ["ECG"]
        self._units = ["a.u."]

    def get_electrode_status(self) -> str:
        """
        Get the current status of ECG electrodes.

        Returns:
            str: Status of the electrodes (e.g., 'both on', 'left off', etc.)
        """
        return self._data_manager._codec.get_lod()

    # override Nervous Sensor class properties

    def get_type(self) -> str:
        """
        Get the sensor type.

        Returns:
            str: Sensor type identifier ('ECG')
        """
        return "ECG"

    def get_sampling_rate(self) -> int:
        """
        Get the sampling rate of the sensor.

        Returns:
            int: Sampling rate in Hz
        """
        return ECG_SAMPLING_RATE


class ECGDataManager(DataManager):
    """
    Data manager for ECG sensor data.

    This class processes and stores ECG data received from the sensor.

    Attributes:
        _sampling_rate (int): ECG sampling rate
        _codec (ECGCodec): Codec for decoding ECG data
    """

    def __init__(self, sensor_name, sampling_rate, start_time):
        """
        Initialize the ECG data manager.

        Args:
            sensor_name (str): Name of the associated sensor
            sampling_rate (int): Sampling rate in Hz
            start_time (float): Timestamp marking the start of data collection
        """
        super().__init__(
            sensor_name=sensor_name,
            sampling_rate=sampling_rate,
            header=["Time (s)", "ECG (A.U.)"],
            start_time=start_time,
            codec=ECGCodec(),
        )

    # implements
    def _process_decoded_data(self, timestamp, data):
        """
        Process decoded ECG data.

        Convert samples and timestamps into time-series data points and
        add them to the data store.

        Args:
            timestamp (float): Timestamp of the first sample
            data (list): List of ECG samples
        """
        data_to_add = []
        for i in range(len(data)):
            data_to_add.append([timestamp + i * (1 / self._sampling_rate), data[i]])
        self._add_data(data_to_add)


class ECGCodec(Codec):
    """
    Codec for decoding ECG data from protobuf messages.

    This class handles the decoding of binary ECG data and tracking of
    electrode connection status.

    Attributes:
        _lodpn (str): Status of electrodes ('both on', 'left off', etc.)
    """

    def __init__(self):
        """Initialize the ECG codec with default electrode status."""
        self._lodpn = "both off"

    # override
    async def protobuf_decode(self, data):
        """
        Decode ECG data from a protobuf message.

        Args:
            data (bytes): Serialized protobuf message

        Returns:
            tuple: (buffer_data, timestamp) containing the decoded samples and timestamp
        """
        # parse the serialized message from a byte string
        pb_buffer_msg = pb2.EcgBuffer()
        pb_buffer_msg.ParseFromString(data)
        if pb_buffer_msg.lodpn == 0:
            self._lodpn = "both on"
        if pb_buffer_msg.lodpn == 1:
            self._lodpn = "left off"
        if pb_buffer_msg.lodpn == 2:
            self._lodpn = "right off"
        if pb_buffer_msg.lodpn == 3:
            self._lodpn = "both off"
        # return self._reshape_data(type, pb_buffer_msg.data, pb_buffer_msg.timestamp)
        # def _reshape_data(self, type, buffer_msg_data, buffer_msg_timestamp):
        timestamp = pb_buffer_msg.timestamp.time + pb_buffer_msg.timestamp.us * 0.000001
        buffer_data = np.frombuffer(pb_buffer_msg.data, np.int8)
        buffer_data = buffer_data.view(np.int16)
        # elif type == "RENFORCE EDA":
        #    real = buffer_msg_data[0].real
        #    imag = buffer_msg_data[0].imag
        #    buffer_data = np.sqrt(np.square(real) + np.square(imag))  # get impedance amgnitude of lowest frequency
        #    buffer_data = 1000000 * 1 / buffer_data
        return buffer_data, timestamp

    # specific to ECG
    def get_lod(self):
        """
        Get the electrode status.

        Returns:
            str: Status of the electrodes ('both on', 'left off', etc.)
        """
        return self._lodpn
