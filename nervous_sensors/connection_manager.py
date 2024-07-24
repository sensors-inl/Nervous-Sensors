import asyncio
import time

from .async_manager import AsyncManager
from .cli_utils import print_bold_section, print_general_info
from .folder_manager import FolderManager
from .gui_manager import GUIManager
from .lsl_manager import LSLManager
from .nervous_sensor import NervousSensor


class ConnectionManager(AsyncManager):
    def __init__(self, sensor_names, gui, folder, lsl, parallel_connection_authorized):
        super().__init__()
        self._sensors = [
            NervousSensor(name=name, start_time=int(time.time()), timeout=10, connection_manager=self)
            for name in sensor_names
        ]
        self._semaphore = asyncio.Semaphore(parallel_connection_authorized)
        self._all_connected = asyncio.Event()
        self._async_managers = []

        if gui:
            self._async_managers.append(GUIManager(self._sensors))
        if folder:
            self._async_managers.append(FolderManager(self._sensors, folder))
        if lsl:
            self._async_managers.append(LSLManager(self._sensors))

    async def start(self):
        print_bold_section("Starting connection manager")
        async with asyncio.TaskGroup() as tg:
            for async_manager in self._async_managers:
                tg.create_task(async_manager.start())
            tg.create_task(self.manage_all_connections())
            tg.create_task(self.manage_all_notifications())
            tg.create_task(self.manage_battery_level())

    async def stop(self):
        print_bold_section("Stopping connection manager")
        self._stop_event.set()
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.manage_all_disconnections())
            for async_manager in self._async_managers:
                tg.create_task(async_manager.stop())

    # Event handlers

    def on_sensor_fail_to_connect(self, sensor: NervousSensor):
        print(f"{sensor.get_colored_name()} failed to connect")
        self._semaphore.release()

    def on_sensor_connect(self, sensor: NervousSensor):
        print(f"{sensor.get_colored_name()} connected")
        self._semaphore.release()
        if all(sensor.is_connected() for sensor in self._sensors):
            self._all_connected.set()

    def on_sensor_disconnect(self, sensor: NervousSensor):
        print(f"{sensor.get_colored_name()} disconnected")
        self._all_connected.clear()

    # Sensors management

    async def manage_all_disconnections(self):
        await self.stop_all_notifications()
        print_general_info("All notifications stopped")
        await self.disconnect_all()
        print_general_info("All sensors disconnected")

    async def manage_all_notifications(self):
        while not self._stop_event.is_set():
            print_general_info("Waiting for all sensors to connect")
            await self._all_connected.wait()
            print_general_info("All sensors connected")
            await self.start_all_notifications()
            print_general_info("All notifications started")
            while self._all_connected.is_set():
                await asyncio.sleep(1)
            print_general_info("All sensors are not connected")
            await self.stop_all_notifications()
            print_general_info("All notifications stopped")

    async def manage_connection(self, sensor):
        while not self._stop_event.is_set():
            if not sensor.is_connected():
                await self._semaphore.acquire()
                print(f"{sensor.get_colored_name()} tries to connect")
                await sensor.connect()
            # Avoid one sensor to monopolize the semaphore
            await asyncio.sleep(1)

    async def manage_battery_level(self):
        while not self._stop_event.is_set():
            await asyncio.sleep(120)
            self.print_battery_level()

    # Sensors parallel actions

    async def manage_all_connections(self):
        await self._run_parallel(lambda sensor: self.manage_connection(sensor))

    async def stop_all_notifications(self):
        await self._run_parallel(lambda sensor: sensor.stop_notifications())

    async def start_all_notifications(self):
        await self._run_parallel(lambda sensor: sensor.start_notifications())

    async def disconnect_all(self):
        await self._run_parallel(lambda sensor: sensor.disconnect())

    # Utils

    def print_battery_level(self):
        for sensor in self._sensors:
            level = sensor.get_battery_level()
            text = f"{sensor.get_colored_name()} battery level: {level}"
            if isinstance(level, int):
                text += " %"
            if not sensor.is_connected():
                text += " (disconnected)"
            print(text)

    async def _run_parallel(self, action):
        async with asyncio.TaskGroup() as tg:
            for sensor in self._sensors:
                tg.create_task(action(sensor))
