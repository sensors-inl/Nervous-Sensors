import logging

import numpy as np

from . import pb2
from .codec import Codec
from .data_manager import DataManager
from .nervous_sensor import NervousSensor

EDA_SAMPLING_RATE = 8
logger = logging.getLogger("nervous")


class NervousEDA(NervousSensor):
    """
    A sensor class for managing EDA (Electrodermal Activity) data acquisition.

    This class extends the NervousSensor base class and provides specific
    implementations for EDA data collection and processing.

    Attributes:
        _data_manager (EDADataManager): Manager for EDA data processing and storage
        _labels (list): List of data labels (["GSR"])
        _units (list): List of measurement units (["uS"])
    """

    def __init__(self, name, start_time, timeout, connection_manager):
        """
        Initialize the EDA sensor.

        Args:
            name (str): Sensor name
            start_time (float): Timestamp marking the start of data collection
            timeout (float): Connection timeout in seconds
            connection_manager: Manager handling connection events
        """
        super().__init__(name=name, start_time=start_time, timeout=timeout, connection_manager=connection_manager)
        # override
        self._data_manager = EDADataManager(sensor_name=name, sampling_rate=EDA_SAMPLING_RATE, start_time=start_time)
        self._labels = ["GSR"]
        self._units = ["uS"]

    # override Nervous Sensor class properties

    def get_type(self) -> str:
        """
        Get the sensor type.

        Returns:
            str: Sensor type identifier ('GSR')
        """
        return "GSR"

    def get_sampling_rate(self) -> int:
        """
        Get the sampling rate of the sensor.

        Returns:
            int: Sampling rate in Hz
        """
        return EDA_SAMPLING_RATE


class EDADataManager(DataManager):
    """
    Data manager for EDA sensor data.

    This class processes and stores EDA data received from the sensor.

    Attributes:
        _sampling_rate (int): EDA sampling rate
        _codec (EDACodec): Codec for decoding EDA data
    """

    def __init__(self, sensor_name, sampling_rate, start_time):
        """
        Initialize the EDA data manager.

        Args:
            sensor_name (str): Name of the associated sensor
            sampling_rate (int): Sampling rate in Hz
            start_time (float): Timestamp marking the start of data collection
        """
        super().__init__(
            sensor_name=sensor_name,
            sampling_rate=sampling_rate,
            header=["Time (s)", "EDA (uS)"],
            start_time=start_time,
            codec=EDACodec(),
        )

    # implements
    def _process_decoded_data(self, timestamp, data):
        """
        Process decoded EDA data.

        Add a single data point with timestamp and EDA value to the data store.

        Args:
            timestamp (float): Timestamp of the sample
            data (float): EDA measurement value
        """
        data_to_add = [[timestamp, data]]
        self._add_data(data_to_add)


class EDACodec(Codec):
    """
    Codec for decoding EDA data from protobuf messages.

    This class handles the decoding of binary EDA data.
    """

    # override
    async def protobuf_decode(self, data):
        """
        Decode EDA data from a protobuf message.

        Args:
            data (bytes): Serialized protobuf message

        Returns:
            tuple: (buffer_data, timestamp) containing the decoded EDA value and timestamp
        """
        # parse the serialized message from a byte string
        pb_buffer_msg = pb2.EdaBuffer()
        pb_buffer_msg.ParseFromString(data)
        # return self._reshape_data(type, pb_buffer_msg.data, pb_buffer_msg.timestamp)
        # def _reshape_data(self, type, buffer_msg_data, buffer_msg_timestamp):
        timestamp = pb_buffer_msg.timestamp.time + pb_buffer_msg.timestamp.us * 0.000001
        real = pb_buffer_msg.data[0].real
        imag = pb_buffer_msg.data[0].imag
        buffer_data = np.sqrt(np.square(real) + np.square(imag))  # get impedance amgnitude of lowest frequency
        buffer_data = 1000000 * 1 / buffer_data
        return buffer_data, timestamp
