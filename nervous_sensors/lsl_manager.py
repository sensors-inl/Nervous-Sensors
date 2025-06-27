import asyncio
import logging
import traceback

from pylsl import StreamInfo, StreamOutlet, local_clock

from .async_manager import AsyncManager

logger = logging.getLogger("nervous")


class LSLManager(AsyncManager):
    """
    Manages the streaming of sensor data through Lab Streaming Layer (LSL).

    This class creates LSL outlets for each sensor and periodically pushes
    new data from the sensors to their respective outlets. This allows
    real-time streaming of sensor data for external applications.

    Attributes:
        _start_time_lsl: Class variable storing the LSL clock time at startup.
        _sensors_lsl: List of dictionaries containing sensor objects, their LSL outlets,
                      and their last sent timestamps.
        _update_time: Time interval in seconds between data sends.
    """

    _start_time_lsl = local_clock()

    def __init__(self, sensors, update_time=0.5):
        """
        Initialize the LSL manager.

        Creates LSL outlets for each sensor based on their characteristics.

        Args:
            sensors: List of sensor objects to stream.
            update_time: Time interval in seconds between data sends (default: 0.5).
        """
        super().__init__()
        self._sensors_lsl = [
            {
                "sensor": sensor,
                "outlet": None,
                "time": 0,
            }
            for sensor in sensors
        ]
        self._update_time = update_time

        try:
            for sensor_lsl in self._sensors_lsl:
                sensor = sensor_lsl["sensor"]
                name = sensor.get_name()
                type = sensor.get_type()
                labels = sensor.get_labels()
                units = sensor.get_units()
                sampling_rate = sensor.get_sampling_rate()
                channel_count = sensor.get_channel_count()

                stream_info = StreamInfo(name, type, channel_count, sampling_rate, "float32", name)
                stream_info.set_channel_labels(labels)
                stream_info.set_channel_units(units)
                sensor_lsl["outlet"] = StreamOutlet(stream_info)
                logger.debug(f"Created LSL outlet for sensor {name}")
        except Exception as e:
            logger.error(f"Error initializing LSL manager: {str(e)}")
            logger.debug(traceback.format_exc())
            raise

    async def start(self):
        """
        Start the LSL manager to periodically send sensor data.

        Runs a loop that periodically sends all sensor data to their respective LSL outlets
        until the stop event is set.
        """
        logger.info("Starting LSL manager")
        logger.info(f"LSL offset clock: {self._start_time_lsl}")

        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._update_time)
                self.send_data()
            except asyncio.TimeoutError:
                self.send_data()
            except Exception as e:
                logger.error(f"Error in LSL manager loop: {str(e)}")
                logger.debug(traceback.format_exc())

    def send_data(self):
        """
        Send data from all sensors to their respective LSL outlets.
        """
        for sensor_lsl in self._sensors_lsl:
            self.send_data_generic(sensor_lsl)

    async def stop(self):
        """
        Stop the LSL manager.

        Sets the stop event to terminate the running loop.
        """
        logger.info("Stopping LSL manager")
        self._stop_event.set()

    def send_data_generic(self, sensor_lsl):
        """
        Send data from a specific sensor to its LSL outlet.

        Only sends data that has been collected since the last send operation.

        Args:
            sensor_lsl: Dictionary containing the sensor object, its LSL outlet,
                        and its last send time.
        """
        sensor = sensor_lsl["sensor"]
        outlet = sensor_lsl["outlet"]
        time = sensor_lsl["time"]

        try:
            data = sensor.data_manager.get_latest_data(latest_data=time)
            if len(data) == 0:
                return

            sensor_lsl["time"] = data.iloc[-1, 0]
            data.iloc[:, 0] = data.iloc[:, 0] + LSLManager._start_time_lsl
            timestamp_list = data.iloc[:, 0].tolist()
            data_list = data.iloc[:, 1:].values.tolist()

            outlet.push_chunk(
                x=data_list,
                timestamp=timestamp_list,
                pushthrough=True,
            )
        except Exception as e:
            logger.error(f"{sensor.get_name()} LSL send error: {str(e)}")
            logger.debug(traceback.format_exc())
