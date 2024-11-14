import time

from cobs import cobs

from . import pb2


class Codec:
    async def time_encode():
        t = time.time()
        timestamp = pb2.Timestamp()
        timestamp.time = int(t)
        timestamp.us = int((t - int(t)) * 1_000_000)
        serialized_data = timestamp.SerializeToString()
        encoded_data = cobs.encode(serialized_data)
        encoded_data = encoded_data + b"\x00"
        return encoded_data

    async def cobs_decode(self, data):
        data_buffer = bytearray()
        data_buffer = data[:-1]
        decoded_data = cobs.decode(data_buffer)
        return decoded_data

    # Abstract method to be override by each sensor type
    async def protobuf_decode(self, data):
        buffer_data = None
        timestamp = None
        return buffer_data, timestamp
