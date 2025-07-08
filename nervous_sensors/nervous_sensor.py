"""
Nervous Sensor Module.

This module provides the NervousSensor class for connecting to and managing
Bluetooth Low Energy (BLE) sensors. It handles connection management, data
reception, and battery level monitoring.

The module includes:
- NervousSensor: Main class for managing BLE sensor connections
- DummyDataManager: A placeholder implementation of DataManager
"""

import asyncio
import logging
import traceback
from datetime import datetime

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

from .codec import Codec
from .data_manager import DataManager
from .utils import RESET, get_color

logger = logging.getLogger("nervous")


class NervousSensor:
    """
    A class for managing connections to Bluetooth Low Energy (BLE) sensors.

    This class handles the connection lifecycle, data notifications, and
    battery level monitoring for BLE sensors.

    Attributes:
        n (int): Class-level counter for sensor instances created.
    """

    n = 0

    def __init__(self, name, start_time, timeout, connection_manager):
        """
        Initialize a new NervousSensor instance.

        Args:
            name (str): Name of the sensor.
            start_time (float): Timestamp when the sensor started.
            timeout (float): Connection timeout in seconds.
            connection_manager: Manager that handles connection events.
        """
        self._name = name
        self._channel_count = 1
        self._units = ["a.u."]
        self._labels = ["signal"]
        self._start_time = start_time
        self._start_time_str = f"{datetime.today().strftime('%Y_%m_%d')}_{datetime.now().strftime('%Hh%Mm')}"
        self._color = get_color(NervousSensor.n)
        self._timeout = timeout
        self._connection_manager = connection_manager
        self._client = None
        self._battery_level = "unknown"
        self._data_manager = DummyDataManager(sensor_name=name, sampling_rate=1, start_time=start_time, codec=Codec())
        self._plot_type = "scatter"
        NervousSensor.n += 1

    # Getters

    def get_start_time(self):
        """
        Get the sensor's start time.

        Returns:
            float: The timestamp when the sensor started.
        """
        return self._start_time

    @property
    def data_manager(self):
        """
        Get the data manager associated with this sensor.

        Returns:
            DataManager: The data manager instance.
        """
        return self._data_manager

    def get_start_time_str(self) -> str:
        """
        Get the formatted start time string.

        Returns:
            str: Formatted timestamp string.
        """
        return self._start_time_str

    def get_type(self) -> str:
        """
        Get the sensor type.

        Returns:
            str: The sensor type.
        """
        return self._type

    def get_sampling_rate(self) -> int:
        """
        Get the sampling rate of the sensor.

        Returns:
            int: 0 indicating variable sampling rate (IRREGULAR_RATE in LSL).
        """
        return 0  # IRREGULAR_RATE in LSL for variable sampling rate

    def get_name(self) -> str:
        """
        Get the sensor name.

        Returns:
            str: The name of the sensor.
        """
        return self._name

    def get_units(self):
        """
        Get the measurement units for each channel.

        Returns:
            list: List of unit strings.
        """
        return self._units

    def get_labels(self):
        """
        Get the labels for each channel.

        Returns:
            list: List of label strings.
        """
        return self._labels

    def get_channel_count(self) -> int:
        """
        Get the number of data channels.

        Returns:
            int: Number of channels.
        """
        return self._channel_count

    def get_plot_type(self) -> str:
        """
        Get the recommended plot type for visualizing the sensor data.

        Returns:
            str: Plot type string.
        """
        return self._plot_type

    def get_colored_name(self) -> str:
        """
        Get the sensor name with terminal color coding.

        Returns:
            str: Color-coded sensor name.
        """
        return f"[{self._color}{self._name}{RESET}]"

    def get_ble_name(self) -> str:
        """
        Get the official BLE name of the sensor.

        Returns:
            str: BLE device name.
        """
        return f"{self._name}"

    def get_battery_level(self) -> str | int:
        """
        Get the current battery level.

        Returns:
            str|int: Battery level as an integer percentage or 'unknown'.
        """
        return self._battery_level

    # Bleak methods

    def is_connected(self) -> bool:
        """
        Check if the sensor is currently connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        if self._client is not None:
            return self._client.is_connected
        return False

    async def disconnect(self):
        """
        Disconnect from the sensor.

        This method blocks until the disconnection is complete.
        """
        if self.is_connected():
            await self._client.disconnect()

    async def start_notifications(self) -> bool:
        """
        Start notifications for battery level and sensor data.

        This method blocks until the operation completes.

        Returns:
            bool: True if successful, False otherwise.
        """

        def battery_callback(_, data):
            self._battery_level = int.from_bytes(data, byteorder="little")

        try:
            await self._client.start_notify(
                "00002a19-0000-1000-8000-00805f9b34fb",
                battery_callback,
            )
            await self._client.start_notify(
                "6e400003-b5a3-f393-e0a9-e50e24dcca9e", self._data_manager.get_data_callback()
            )
            return True
        except (BleakError, KeyError, AttributeError, ValueError):
            logger.error(f"{self.get_colored_name()} Failed to start notifications")
            return False

    async def stop_notifications(self) -> bool:
        """
        Stop notifications for battery level and sensor data.

        This method blocks until the operation completes.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            await self._client.stop_notify("00002a19-0000-1000-8000-00805f9b34fb")
            await self._client.stop_notify("6e400003-b5a3-f393-e0a9-e50e24dcca9e")
            return True
        except (BleakError, KeyError, AttributeError, ValueError):
            logger.error(f"{self.get_colored_name()} Failed to stop notifications")
            return False

    async def connect(self):
        """
        Connect to the sensor and maintain the connection.

        This method blocks as long as the connection is maintained,
        theoretically indefinitely. It handles connection events and
        disconnection notifications.
        """
        scanner = BleakScanner()
        disconnection_event = asyncio.Event()
        device = await scanner.find_device_by_name(self.get_ble_name(), self._timeout)
        connection_was_established = False

        if device is None:
            self._connection_manager.on_sensor_fail_to_connect(self)
            return

        try:
            async with BleakClient(device, lambda _: disconnection_event.set()) as self._client:
                # Update embedded RTC
                await self._client.write_gatt_char(
                    "6e400002-b5a3-f393-e0a9-e50e24dcca9e",
                    await Codec.time_encode(),
                    response=False,
                )
                self._connection_manager.on_sensor_connect(self)
                connection_was_established = True
                await disconnection_event.wait()
                self._connection_manager.on_sensor_disconnect(self)

            self._client = None

        except Exception as ex:
            logger.error(f"{self.get_colored_name()} Error: {str(ex)}")
            logger.debug(traceback.format_exc())
            if connection_was_established:
                self._connection_manager.on_sensor_disconnect(self)
            else:
                self._connection_manager.on_sensor_fail_to_connect(self)


class DummyDataManager(DataManager):
    """
    A placeholder implementation of DataManager that does nothing.

    This class is used as a fallback or for testing when a real data manager
    is not available or necessary.
    """

    def __init__(self, sensor_name, sampling_rate, start_time, codec):
        """
        Initialize a new DummyDataManager instance.

        Args:
            sensor_name (str): Name of the sensor.
            sampling_rate (int): Sampling rate in Hz.
            start_time (float): Timestamp when the sensor started.
            codec (Codec): Codec for encoding/decoding data.
        """
        # this one do nothing
        pass

    def _process_decoded_data(self, timestamp, data):
        """
        Process decoded data from the sensor.

        This implementation does nothing.

        Args:
            timestamp (float): Timestamp of the data.
            data (any): Decoded sensor data.
        """
        # this does not add any data
        pass
