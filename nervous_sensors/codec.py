import time

import numpy as np
from cobs import cobs

from . import pb2

ecg_buffer_msg = pb2.EcgBuffer()
eda_buffer_msg = pb2.EdaBuffer()
__all__ = ["cobs_decode", "protobuf_decode"]


async def time_encode():
    t = time.time()
    timestamp = pb2.Timestamp()
    timestamp.time = int(t)
    timestamp.us = int((t - int(t)) * 1_000_000)
    serialized_data = timestamp.SerializeToString()
    encoded_data = cobs.encode(serialized_data)
    encoded_data = encoded_data + b"\x00"
    return encoded_data


async def cobs_decode(data):
    global ecg_buffer_msg
    data_buffer = bytearray()
    data_buffer = data[:-1]
    decoded_data = cobs.decode(data_buffer)
    return decoded_data


async def protobuf_decode(type, data):
    # parse the serialized message from a byte string
    pb_buffer_msg = None
    if type == "RENFORCE ECG":
        pb_buffer_msg = pb2.EcgBuffer()
    elif type == "RENFORCE EDA":
        pb_buffer_msg = pb2.EdaBuffer()
    else:
        print("Unknown protobuf message type")
        return None
    pb_buffer_msg.ParseFromString(data)
    return _reshape_data(type, pb_buffer_msg.data, pb_buffer_msg.timestamp)


def _reshape_data(type, buffer_msg_data, buffer_msg_timestamp):
    timestamp = buffer_msg_timestamp.time + buffer_msg_timestamp.us * 0.000001
    if type == "RENFORCE ECG":
        buffer_data = np.frombuffer(buffer_msg_data, np.int8)
        buffer_data = buffer_data.view(np.int16)
    elif type == "RENFORCE EDA":
        real = buffer_msg_data[0].real
        imag = buffer_msg_data[0].imag
        buffer_data = np.sqrt(np.square(real) + np.square(imag))  # get impedance amgnitude of lowest frequency
        buffer_data = 1000000 * 1 / buffer_data
    return buffer_data, timestamp
