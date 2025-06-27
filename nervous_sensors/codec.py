import logging
import time
import traceback

from cobs import cobs

from . import pb2

logger = logging.getLogger("nervous")


class Codec:
    """
    A codec class that handles encoding and decoding of data using COBS protocol and protobuf.

    This class provides methods for time encoding, COBS decoding, and an abstract method
    for protocol buffer decoding that should be implemented by each sensor type.
    """

    @staticmethod
    async def time_encode():
        """
        Encode the current time into a protocol buffer Timestamp message.

        Returns:
            bytes: COBS encoded timestamp data with a trailing zero byte.
        """
        try:
            t = time.time()
            timestamp = pb2.Timestamp()
            timestamp.time = int(t)
            timestamp.us = int((t - int(t)) * 1_000_000)
            serialized_data = timestamp.SerializeToString()
            encoded_data = cobs.encode(serialized_data)
            encoded_data = encoded_data + b"\x00"
            logger.debug("Time encoded successfully")
            return encoded_data
        except Exception as e:
            logger.error(f"Error encoding time: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise

    async def cobs_decode(self, data):
        """
        Decode data using the COBS protocol.

        Args:
            data (bytes): COBS encoded data with a trailing zero byte.

        Returns:
            bytes: Decoded data.
        """
        try:
            data_buffer = bytearray()
            data_buffer = data[:-1]
            decoded_data = cobs.decode(data_buffer)
            logger.debug(f"COBS decoded {len(data)} bytes to {len(decoded_data)} bytes")
            return decoded_data
        except Exception as e:
            logger.error(f"Error decoding data with COBS: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise

    # Abstract method to be overridden by each sensor type
    async def protobuf_decode(self, data):
        """
        Abstract method to decode protocol buffer data.
        This method should be implemented by each sensor type.

        Args:
            data (bytes): Protocol buffer encoded data.

        Returns:
            tuple: A tuple containing (buffer_data, timestamp).
        """
        logger.warning("Using base protobuf_decode method which returns None values")
        buffer_data = None
        timestamp = None
        return buffer_data, timestamp
