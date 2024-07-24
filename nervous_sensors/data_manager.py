import threading
from abc import ABC, abstractmethod

import bleak
import pandas as pd

from .codec import cobs_decode, protobuf_decode

# Maximum sizes from which the data are truncated and rested
# using hysteresis for CPU consumption avoidance
THRESH1 = 12000
THRESH2 = 20000


class DataManager(ABC):
    def __init__(self, sensor_name, sampling_rate, header, start_time, protobuf_type):
        """
        @param header: header of the data
        @param start_time: start time of the data
        @param protobuf_type: type of the protobuf message
        """
        self._sensor_name = sensor_name
        self._sampling_rate = sampling_rate
        self.__header = header
        self.__data = []
        self.__start_time = start_time
        self._protobuf_type = protobuf_type
        self.__lock = threading.Lock()

    def get_header(self):
        return self.__header

    def _add_data(self, data):
        """
        @param data: 2D list of the data to add
        """
        with self.__lock:
            self.__data.extend(data)

            if len(self.__data) >= THRESH2:
                self.__data = self.__data[-THRESH1:]

    def get_name(self):
        return self._sensor_name

    def get_latest_data(
        self,
        last_n=None,
        latest_data=None,
        latest_data_column=0,
        concerned_columns=None,
    ):
        """
        Two modes available:
        - all last n
        - all from latest data

        @param last_n: number of last data to get, -1 to get all lines
        @param latest_data: latest data (not included) from which to get the new data
        @param latest_data_column: column of the latest data. Can be a name or an index.
        @param concerned_columns: columns of the header to get, None to get all columns.
        Can be a list of names or a list of index
        """
        if concerned_columns is None:
            concerned_columns = self.__header

        if all(isinstance(c, int) for c in concerned_columns):
            concerned_columns = [self.__header[c] for c in concerned_columns]

        with self.__lock:
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

    @abstractmethod
    def _process_decoded_data(self, timestamp, data):
        """
        @param timestamp: timestamp of the first data
        @param data: array of data to process
        """
        pass

    def get_data_callback(self):
        async def data_callback(sender: bleak.BleakGATTCharacteristic, data: bytearray):
            data = await cobs_decode(data)
            data, timestamp = await protobuf_decode(self._protobuf_type, data)
            timestamp -= self.__start_time
            self._process_decoded_data(timestamp, data)

        return data_callback

    @staticmethod
    def get_instance(sensor):
        name = sensor.get_name()
        start_time = sensor.get_start_time()
        sampling_rate = sensor.get_sampling_rate()
        protobuf_type = "RENFORCE ECG" if "ECG" in name else "RENFORCE EDA"
        if protobuf_type == "RENFORCE ECG":
            return ECGDataManager(name, sampling_rate, start_time, protobuf_type)
        else:
            return EDADataManager(name, sampling_rate, start_time, protobuf_type)


# ---------------------------
# ECG and EDA data classes
# ---------------------------


class ECGDataManager(DataManager):
    def __init__(self, sensor_name, sampling_rate, start_time, protobuf_type):
        super().__init__(
            sensor_name=sensor_name,
            sampling_rate=sampling_rate,
            header=["time_ecg (s)", "ecg (mV)"],
            start_time=start_time,
            protobuf_type=protobuf_type,
        )

    def _process_decoded_data(self, timestamp, data):
        data_to_add = []
        for i in range(len(data)):
            data_to_add.append([timestamp + i * (1 / self._sampling_rate), data[i]])
        self._add_data(data_to_add)


class EDADataManager(DataManager):
    def __init__(self, sensor_name, sampling_rate, start_time, protobuf_type):
        super().__init__(
            sensor_name=sensor_name,
            sampling_rate=sampling_rate,
            header=["time_eda (s)", "12Hz"],
            start_time=start_time,
            protobuf_type=protobuf_type,
        )

    def _process_decoded_data(self, timestamp, data):
        data_to_add = [[timestamp, data]]
        self._add_data(data_to_add)
