import asyncio
import logging
import time
import traceback

from .async_manager import AsyncManager
from .folder_manager import FolderManager
from .gui_manager import GUIManager
from .lsl_manager import LSLManager
from .nervous_ecg import NervousECG
from .nervous_eda import NervousEDA
from .nervous_hr import NervousHR
from .nervous_scr import NervousSCR
from .nervous_sensor import NervousSensor
from .utils import print_green, print_red

# Configure logging
logger = logging.getLogger("nervous")


class ConnectionManager(AsyncManager):
    """
    Manages connections to multiple physiological sensors and their data streams.

    This class handles the connection, disconnection, and notification management for
    physiological sensors like ECG (electrocardiogram) and EDA (electrodermal activity).
    It coordinates parallel connections, notifications, and ensures data is properly
    streamed to configured outputs (GUI, file storage, or LSL stream).

    Attributes:
        _sensors (list): List of sensor objects to manage
        _semaphore (asyncio.Semaphore): Controls the number of parallel connection attempts
        _all_connected (asyncio.Event): Event that is set when all sensors are connected
        _async_managers (list): List of output managers (GUI, folder, LSL)
    """

    def __init__(self, sensor_names, gui=False, folder=False, lsl=False, parallel_connection_authorized=1):
        """
        Initialize the connection manager with the specified sensors and output options.

        Args:
            sensor_names (list): List of sensor names to connect to
            gui (bool): Whether to enable GUI visualization of sensor data
            folder (bool/str): Whether/where to save sensor data to files
            lsl (bool): Whether to stream sensor data via Lab Streaming Layer
            parallel_connection_authorized (int): Maximum number of simultaneous connection attempts
        """
        super().__init__()
        self._sensors = []

        start_time = int(time.time())
        for name in sensor_names:
            try:
                if "ECG" in name:
                    ecg_sensor = NervousECG(name=name, start_time=start_time, timeout=10, connection_manager=self)
                    self._sensors.append(ecg_sensor)
                    self._sensors.append(
                        NervousHR(ecg_sensor=ecg_sensor, start_time=start_time, timeout=10, connection_manager=self)
                    )
                elif "EDA" in name:
                    eda_sensor = NervousEDA(name=name, start_time=start_time, timeout=10, connection_manager=self)
                    self._sensors.append(eda_sensor)
                    self._sensors.append(
                        NervousSCR(eda_sensor=eda_sensor, start_time=start_time, timeout=10, connection_manager=self)
                    )
            except Exception as e:
                logger.error(print_red(f"Error initializing sensor {name}: {e}"))
                logger.debug(traceback.format_exc())

        self._semaphore = asyncio.Semaphore(parallel_connection_authorized)
        self._all_connected = asyncio.Event()
        self._notifications_active = False
        self._async_managers = []

        if lsl:
            self._async_managers.append(LSLManager(self._sensors))
        if folder:
            self._async_managers.append(FolderManager(self._sensors, folder))
        if gui:
            self._async_managers.append(GUIManager(self._sensors))

    async def start(self):
        """
        Start the connection manager, output managers, and all sensor connections.

        This method starts all configured output managers and initiates the connection
        process for all sensors in parallel. It also starts the notification and battery
        level monitoring tasks.
        """
        logger.info("Starting connection manager")
        try:
            async with asyncio.TaskGroup() as tg:
                for async_manager in self._async_managers:
                    tg.create_task(async_manager.start())
                tg.create_task(self.manage_all_connections())
                tg.create_task(self.manage_all_notifications())
                tg.create_task(self.manage_battery_level())
        except Exception as e:
            logger.error(print_red(f"Error starting connection manager: {e}"))
            logger.debug(traceback.format_exc())

    async def stop(self):
        """
        Stop the connection manager, output managers, and disconnect all sensors.

        This method stops all notification streams, disconnects all sensors,
        and shuts down all output managers.
        """
        logger.info("Stopping connection manager")
        try:
            self._stop_event.set()
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.manage_all_disconnections())
                for async_manager in self._async_managers:
                    tg.create_task(async_manager.stop())
        except Exception as e:
            logger.error(print_red(f"Error stopping connection manager: {e}"))
            logger.debug(traceback.format_exc())

    # Event handlers

    def on_sensor_fail_to_connect(self, sensor: NervousSensor):
        """
        Handler for when a sensor fails to connect.

        Args:
            sensor (NervousSensor): The sensor that failed to connect
        """
        logger.warning(f"{sensor.get_colored_name()}" + print_red(" failed to connect"))
        self._semaphore.release()

    def on_sensor_connect(self, sensor: NervousSensor):
        """
        Handler for when a sensor successfully connects.

        Releases the connection semaphore and sets the all_connected event
        if all sensors are now connected.

        Args:
            sensor (NervousSensor): The sensor that connected
        """
        logger.info(f"{sensor.get_colored_name()}" + print_green(" connected"))
        self._semaphore.release()
        if all(sensor.is_connected() for sensor in self._sensors):
            self._all_connected.set()

    def on_sensor_disconnect(self, sensor: NervousSensor):
        """
        Handler for when a sensor disconnects.

        Clears the all_connected event since not all sensors are connected.

        Args:
            sensor (NervousSensor): The sensor that disconnected
        """
        logger.info(f"{sensor.get_colored_name()}" + print_red(" disconnected"))
        self._all_connected.clear()

    # Sensors management

    async def manage_all_disconnections(self):
        """
        Stop notifications on all sensors and disconnect them.
        """
        try:
            await self.stop_all_notifications()
            logger.info("All notifications stopped")
            await self.disconnect_all()
            logger.info("All sensors disconnected")
        except Exception as e:
            logger.error(f"Error in manage_all_disconnections: {e}")
            logger.debug(traceback.format_exc())

    async def manage_all_notifications(self):
        """
        Manage notification streams for all sensors.

        This method continuously monitors the connection status of sensors and
        starts/stops notifications accordingly. When all sensors are connected,
        it starts notifications; when any sensor disconnects, it stops notifications.
        """
        while not self._stop_event.is_set():
            try:
                logger.info("Waiting for all sensors to connect")
                await self._all_connected.wait()
                logger.info("All sensors connected")
                await self.start_all_notifications()
                logger.info("All notifications started")
                while self._all_connected.is_set():
                    await asyncio.sleep(0.1)
                logger.info("All sensors are not connected")
                await self.stop_all_notifications()
                logger.info("All notifications stopped")
            except Exception as e:
                logger.error(f"Error in manage_all_notifications: {e}")
                logger.debug(traceback.format_exc())
                await asyncio.sleep(1)  # Prevent tight loop in case of errors

    async def manage_connection(self, sensor):
        """
        Manage connection for a single sensor.

        Continuously attempts to connect the sensor if it's not already connected.
        Uses a semaphore to limit the number of simultaneous connection attempts.

        Args:
            sensor (NervousSensor): The sensor to manage connection for
        """
        while not self._stop_event.is_set():
            try:
                if not sensor.is_connected():
                    await self._semaphore.acquire()
                    logger.info(f"{sensor.get_colored_name()} tries to connect")
                    await sensor.connect()
                # Avoid one sensor monopolizing the semaphore
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error connecting {sensor.get_colored_name()}: {e}")
                logger.debug(traceback.format_exc())
                if self._semaphore.locked():
                    self._semaphore.release()
                await asyncio.sleep(1)  # Wait before retrying

    async def manage_battery_level(self):
        """
        Periodically check and log battery levels for all sensors.

        Battery levels are checked every 2 minutes unless the manager is stopping.
        """
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=120)
                self.log_battery_level()
            except TimeoutError:
                self.log_battery_level()
            except Exception as e:
                logger.error(f"Error checking battery levels: {e}")
                logger.debug(traceback.format_exc())
                await asyncio.sleep(60)  # Wait before retrying

    # Sensors parallel actions

    async def manage_all_connections(self):
        """
        Start connection management for all sensors in parallel.
        """
        await self._run_parallel(lambda sensor: self.manage_connection(sensor))

    async def start_all_notifications(self):
        """Start notifications for all sensors in parallel."""
        await self._run_parallel(lambda sensor: sensor.start_notifications())
        self._notifications_active = True

    async def stop_all_notifications(self):
        """Stop notifications for all sensors in parallel."""
        await self._run_parallel(lambda sensor: sensor.stop_notifications())
        self._notifications_active = False

    def are_notifications_active(self):
        """Check if notifications are currently active"""
        return self._notifications_active

    async def disconnect_all(self):
        """
        Disconnect all sensors in parallel.
        """
        await self._run_parallel(lambda sensor: sensor.disconnect())

    # Utils

    def log_battery_level(self):
        """
        Log the current battery level for all sensors.
        """
        for sensor in self._sensors:
            try:
                level = sensor.get_battery_level()
                message = f"{sensor.get_colored_name()} battery level: {level}"
                if isinstance(level, int):
                    message += " %"
                if not sensor.is_connected():
                    message += " (disconnected)"
                logger.info(message)
            except Exception as e:
                logger.error(f"Error getting battery level for {sensor.get_colored_name()}: {e}")
                logger.debug(traceback.format_exc())

    async def _run_parallel(self, action):
        """
        Run an action on all sensors in parallel.

        Args:
            action (callable): A function that takes a sensor as an argument
        """
        try:
            async with asyncio.TaskGroup() as tg:
                for sensor in self._sensors:
                    tg.create_task(action(sensor))
        except Exception as e:
            logger.error(f"Error running parallel action: {e}")
            logger.debug(traceback.format_exc())
