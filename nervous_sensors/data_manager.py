import logging
import threading
import traceback
from abc import ABC, abstractmethod

import bleak
import pandas as pd

from .codec import Codec

logger = logging.getLogger("nervous")

# Maximum sizes from which the data are truncated and rested
# using hysteresis for CPU consumption avoidance
THRESH1 = 12000  # Lower threshold for truncation
THRESH2 = 20000  # Upper threshold that triggers truncation


class DataManager(ABC):
    """
    Abstract base class for managing sensor data.

    This class handles the collection, storage, and retrieval of sensor data.
    It provides methods for adding new data, retrieving subsets of data,
    and processing incoming data from BLE sensors.

    Attributes:
        _codec: Codec object used for encoding/decoding sensor data.
        _sensor_name: Name of the associated sensor.
        _sampling_rate: Sampling rate of the sensor in Hz.
        __header: List of column names for the data.
        __data: List of data rows.
        __start_time: Start time of data collection (used for timestamp calculation).
        __lock: Thread lock for ensuring thread-safe data operations.
    """

    def __init__(self, sensor_name, sampling_rate, header, start_time, codec: Codec):
        """
        Initialize the data manager.

        Args:
            sensor_name: Name of the associated sensor.
            sampling_rate: Sampling rate of the sensor in Hz.
            header: List of column names for the data.
            start_time: Start time of data collection (used for timestamp calculation).
            codec: Codec object used for encoding/decoding sensor data.
        """
        self._codec = codec
        self._sensor_name = sensor_name
        self._sampling_rate = sampling_rate
        self.__header = header
        self.__data = []
        self.__start_time = start_time
        self.__lock = threading.Lock()

    def get_header(self):
        """
        Get the header (column names) for the data.

        Returns:
            list: List of column names.
        """
        return self.__header

    def _add_data(self, data):
        """
        Add new data rows to the data store.

        Implements hysteresis-based truncation to manage memory usage:
        when data exceeds THRESH2 rows, it's truncated to keep only the
        last THRESH1 rows.

        Args:
            data: 2D list of data rows to add.
        """
        with self.__lock:
            self.__data.extend(data)
            if len(self.__data) >= THRESH2:
                self.__data = self.__data[-THRESH1:]
                logger.debug(f"Data for {self._sensor_name} truncated to {THRESH1} rows")

    def get_name(self):
        """
        Get the name of the associated sensor.

        Returns:
            str: Sensor name.
        """
        return self._sensor_name

    def get_latest_data(
        self,
        last_n=None,
        latest_data=None,
        latest_data_column=0,
        concerned_columns=None,
    ):
        """
        Retrieve a subset of the data.

        Provides two modes of data retrieval:
        1. The last N data rows
        2. All data newer than a specified timestamp

        Args:
            last_n: Number of last data rows to get, -1 to get all rows.
            latest_data: Latest data timestamp (not included) from which to get newer data.
            latest_data_column: Column of the timestamp. Can be a name or an index.
            concerned_columns: Columns to include in the result. Can be names or indices.
                               None to get all columns.

        Returns:
            pandas.DataFrame: The requested subset of data.

        Raises:
            ValueError: If both last_n and latest_data are specified.
        """
        if concerned_columns is None:
            concerned_columns = self.__header

        if all(isinstance(c, int) for c in concerned_columns):
            concerned_columns = [self.__header[c] for c in concerned_columns]

        with self.__lock:
            try:
                data = pd.DataFrame(self.__data, columns=self.__header)
                data = data[concerned_columns]

                if last_n is not None and latest_data is None:
                    if last_n == -1 or last_n >= data.shape[0]:
                        return data
                    else:
                        return data[-last_n:]

                elif latest_data is not None and last_n is None:
                    if isinstance(latest_data_column, int):
                        latest_data_column = self.__header[latest_data_column]

                    if latest_data_column in data.columns:
                        data = data[data[latest_data_column] > latest_data]
                        return data

                else:
                    raise ValueError("Only one of last_n or latest_data can be defined")
            except Exception as e:
                logger.error(f"{self._sensor_name} DataManager error: {str(e)}")
                logger.debug(traceback.format_exc())
                return pd.DataFrame(columns=concerned_columns)  # Return empty DataFrame on error

    @abstractmethod
    def _process_decoded_data(self, timestamp, data):
        """
        Process decoded data from the sensor.

        This abstract method must be implemented by subclasses to handle
        the specific data processing requirements of each sensor type.

        Args:
            timestamp: Timestamp of the first data point.
            data: Array of data to process.
        """
        pass

    def get_data_callback(self):
        """
        Create a callback function for receiving BLE characteristic notifications.

        Returns:
            function: Async callback function that processes received BLE data.
        """

        async def data_callback(sender: bleak.BleakGATTCharacteristic, data: bytearray):
            """
            Process BLE characteristic notifications.

            Decodes the received data using the codec and processes it.

            Args:
                sender: The BLE characteristic that sent the notification.
                data: The raw data received from the characteristic.
            """
            try:
                data = await self._codec.cobs_decode(data)
                data, timestamp = await self._codec.protobuf_decode(data)
                timestamp -= self.__start_time
                self._process_decoded_data(timestamp, data)
            except Exception as e:
                logger.error(f"{self._sensor_name} data callback error: {str(e)}")
                logger.debug(traceback.format_exc())

        return data_callback
