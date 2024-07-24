import asyncio
from datetime import datetime

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakDeviceNotFoundError, BleakError

from .cli_utils import RESET, get_color
from .codec import time_encode
from .data_manager import DataManager

# Sampling rates
ECG_SAMPLING_RATE = 512
EDA_SAMPLING_RATE = 8


class NervousSensor:
    n = 0

    def __init__(self, name, start_time, timeout, connection_manager):
        self._name = name
        self._start_time = start_time
        self._start_time_str = f'{datetime.today().strftime("%Y_%m_%d")}_{datetime.now().strftime("%Hh%Mm")}'
        self._color = get_color(NervousSensor.n)
        self._timeout = timeout
        self._connection_manager = connection_manager
        self._client = None
        self._battery_level = "unknown"
        self._data_manager = DataManager.get_instance(self)
        NervousSensor.n += 1

    # Getters

    def get_start_time(self):
        return self._start_time

    @property
    def data_manager(self):
        return self._data_manager

    def get_start_time_str(self) -> str:
        return self._start_time_str

    def get_type(self) -> str:
        return "ECG" if "ecg" in self._name.lower() else "EDA"

    def get_sampling_rate(self) -> int:
        return ECG_SAMPLING_RATE if "ecg" in self._name.lower() else EDA_SAMPLING_RATE

    def get_name(self) -> str:
        return self._name

    def get_colored_name(self) -> str:
        return f"[{self._color}{self._name[:3]} {self._name[3:]}{RESET}]"

    def get_ble_name(self) -> str:
        return f"RENFORCE {self._name[:3]} {self._name[3:]}"

    def get_battery_level(self) -> str | int:
        return self._battery_level

    # Bleak methods

    def is_connected(self) -> bool:
        if self._client is not None:
            return self._client.is_connected
        return False

    async def disconnect(self):
        """
        Blocking until the code complete (short period)
        """
        if self.is_connected():
            await self._client.disconnect()

    async def start_notifications(self) -> bool:
        """
        Blocking until the code complete (short period)
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
        except (BleakError, AttributeError):
            return False

    async def stop_notifications(self) -> bool:
        """
        Blocking until the code complete (short period)
        """
        try:
            await self._client.stop_notify("00002a19-0000-1000-8000-00805f9b34fb")
            await self._client.stop_notify("6e400003-b5a3-f393-e0a9-e50e24dcca9e")
            return True
        except (BleakError, KeyError, AttributeError, ValueError):
            return False

    async def connect(self):
        """
        ! Blocking as long as connection is maintained (theoretically indefinitely)
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
                    await time_encode(),
                    response=False,
                )

                self._connection_manager.on_sensor_connect(self)
                connection_was_established = True
                await disconnection_event.wait()
                self._connection_manager.on_sensor_disconnect(self)

            self._client = None

        except BleakDeviceNotFoundError:
            if connection_was_established:
                self._connection_manager.on_sensor_disconnect(self)
            else:
                self._connection_manager.on_sensor_fail_to_connect(self)
