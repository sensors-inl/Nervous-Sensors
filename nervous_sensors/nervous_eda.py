import numpy as np

from . import pb2
from .codec import Codec
from .data_manager import DataManager
from .nervous_sensor import NervousSensor

EDA_SAMPLING_RATE = 8


class NervousEDA(NervousSensor):
    def __init__(self, name, start_time, timeout, connection_manager):
        super().__init__(name=name, start_time=start_time, timeout=timeout, connection_manager=connection_manager)
        # override
        self._data_manager = EDADataManager(sensor_name=name, sampling_rate=EDA_SAMPLING_RATE, start_time=start_time)

    # override Nervous Sensor class properties

    def get_type(self) -> str:
        return "EDA"

    def get_sampling_rate(self) -> int:
        return EDA_SAMPLING_RATE


class EDADataManager(DataManager):
    def __init__(self, sensor_name, sampling_rate, start_time):
        super().__init__(
            sensor_name=sensor_name,
            sampling_rate=sampling_rate,
            header=["time_ecg (s)", "eda (uS)"],
            start_time=start_time,
            codec=EDACodec(),
        )

    # implements
    def _process_decoded_data(self, timestamp, data):
        data_to_add = [[timestamp, data]]
        self._add_data(data_to_add)


class EDACodec(Codec):
    # override
    async def protobuf_decode(self, data):
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
