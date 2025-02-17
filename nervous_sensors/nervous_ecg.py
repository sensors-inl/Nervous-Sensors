import numpy as np

from . import pb2
from .codec import Codec
from .data_manager import DataManager
from .nervous_sensor import NervousSensor

ECG_SAMPLING_RATE = 512


class NervousECG(NervousSensor):
    def __init__(self, name, start_time, timeout, connection_manager):
        super().__init__(name=name, start_time=start_time, timeout=timeout, connection_manager=connection_manager)
        # override
        self._data_manager = ECGDataManager(sensor_name=name, sampling_rate=ECG_SAMPLING_RATE, start_time=start_time)

    # override Nervous Sensor class properties

    def get_type(self) -> str:
        return "ECG"

    def get_sampling_rate(self) -> int:
        return ECG_SAMPLING_RATE


class ECGDataManager(DataManager):
    def __init__(self, sensor_name, sampling_rate, start_time):
        super().__init__(
            sensor_name=sensor_name,
            sampling_rate=sampling_rate,
            header=["Time (s)", "ECG (A.U.)"],
            start_time=start_time,
            codec=ECGCodec(),
        )

    # implements
    def _process_decoded_data(self, timestamp, data):
        data_to_add = []
        for i in range(len(data)):
            data_to_add.append([timestamp + i * (1 / self._sampling_rate), data[i]])
        self._add_data(data_to_add)


class ECGCodec(Codec):
    # override
    async def protobuf_decode(self, data):
        # parse the serialized message from a byte string
        pb_buffer_msg = pb2.EcgBuffer()
        pb_buffer_msg.ParseFromString(data)
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
