from .data_manager import DataManager
from .nervous_sensor import NervousSensor
from .nervous_ecg import NervousECG
import asyncio

class NervousVirtual(NervousSensor):
    def __init__(self, type, name, sensor:NervousSensor, start_time, update_time, timeout, connection_manager):
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
        return self._type

    def get_sampling_rate(self) -> int:
        return 0 # IRREGULAR_RATE in LSL for variable sampling rate
    
    # override Bleak helpers as Bluetooth is not used in virtual sensors

    def is_connected(self) -> bool:
        return self._is_connected

    async def connect(self):
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
        self._is_connected = False
        self._disconnect_event.set()

    async def start_notifications(self) -> bool:
        self._start_event.set()
        return True

    async def stop_notifications(self) -> bool:
        self._stop_event.set()
        return True
    
    # This must be overriden by the virtual sensor instance
    def _process_data(self):
        print("_process_data() method not implemented")
