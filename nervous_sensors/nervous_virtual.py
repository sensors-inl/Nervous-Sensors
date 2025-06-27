"""
Nervous Virtual Sensor Module.

This module provides the NervousVirtual class which extends NervousSensor
to implement virtual sensors. Virtual sensors can be used for testing,
simulation, or processing data from other sensors without requiring a
physical Bluetooth connection.
"""

import asyncio
import logging

from .nervous_sensor import NervousSensor

logger = logging.getLogger("nervous")


class NervousVirtual(NervousSensor):
    """
    A class for implementing virtual sensors extending the NervousSensor functionality.

    This class provides a framework for creating virtual sensors that don't
    rely on actual Bluetooth connections but still implement the same interface
    as physical sensors. Virtual sensors can be used for testing, simulation,
    or derived metrics from real sensors.
    """

    def __init__(self, type, name, sensor: NervousSensor, start_time, update_time, timeout, connection_manager):
        """
        Initialize a new NervousVirtual instance.

        Args:
            type (str): The type identifier for this virtual sensor.
            name (str): Name of the virtual sensor.
            sensor (NervousSensor): Parent sensor that this virtual sensor derives from.
            start_time (float): Timestamp when the sensor started.
            update_time (float): Time interval between data updates in seconds.
            timeout (float): Connection timeout in seconds.
            connection_manager: Manager that handles connection events.
        """
        super().__init__(name=name, start_time=start_time, timeout=timeout, connection_manager=connection_manager)
        self._type = type
        self._sensor = sensor
        self._is_connected = False
        self._start_event = asyncio.Event()
        self._stop_event = asyncio.Event()
        self._disconnect_event = asyncio.Event()
        self._update_time = update_time

    # override Nervous Sensor class properties

    def get_type(self) -> str:
        """
        Get the sensor type.

        Returns:
            str: The sensor type.
        """
        return self._type

    def get_sampling_rate(self) -> int:
        """
        Get the sampling rate of the virtual sensor.

        Returns:
            int: 0 indicating variable sampling rate (IRREGULAR_RATE in LSL).
        """
        return 0  # IRREGULAR_RATE in LSL for variable sampling rate

    # override Bleak helpers as Bluetooth is not used in virtual sensors

    def is_connected(self) -> bool:
        """
        Check if the virtual sensor is currently connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._is_connected

    async def connect(self):
        """
        Establish a virtual connection and begin the data processing loop.

        This method blocks as long as the virtual connection is maintained.
        It handles the main event loop for data processing based on the
        start and stop notification events.
        """
        self._is_connected = True
        # dummy wait
        await asyncio.sleep(0.1)
        self._connection_manager.on_sensor_connect(self)
        while not self._disconnect_event.is_set():
            await self._start_event.wait()
            self._start_event.clear()
            while not self._stop_event.is_set():
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self._update_time)
                    self._process_data()
                except TimeoutError:
                    self._process_data()
            self._stop_event.clear()
        self._disconnect_event.clear()
        self._connection_manager.on_sensor_disconnect(self)

    async def disconnect(self):
        """
        Disconnect the virtual sensor.

        This method signals the connection loop to terminate.
        """
        self._is_connected = False
        self._disconnect_event.set()

    async def start_notifications(self) -> bool:
        """
        Start the data notification process for the virtual sensor.

        Returns:
            bool: True indicating success.
        """
        self._start_event.set()
        return True

    async def stop_notifications(self) -> bool:
        """
        Stop the data notification process for the virtual sensor.

        Returns:
            bool: True indicating success.
        """
        self._stop_event.set()
        return True

    def _process_data(self):
        """
        Process data for this virtual sensor.

        This method must be overridden by subclasses to implement
        actual data processing logic. The default implementation
        simply logs a warning.
        """
        logger.warning(f"{self.get_colored_name()} _process_data() method not implemented")
