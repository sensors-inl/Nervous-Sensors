import asyncio
import bleak
from renforce_codec import (cobs_decode, protobuf_decode, time_encode)
from renforce_data import ECGData, EDAData, RenforceData


SENSOR_TYPE_LIST = ['ECG', 'EDA']
SENSOR_ADV_PREFIX = 'RENFORCE '


class RenforceSensor:
    def __init__(self, name, start_time, callbacks, battery_callback, connected_callback, disconnected_callback):
        self.name = name
        self.type = None
        self.data = None

        # Detect device type according to name
        for sensor_type in SENSOR_TYPE_LIST:
            if sensor_type in self.name:
                self.type = SENSOR_ADV_PREFIX + sensor_type
                self.data = RenforceData.get_instance(self.name, self.type, start_time, callbacks)
                break

        if self.type is None:
            self.type = SENSOR_ADV_PREFIX + SENSOR_TYPE_LIST[0]
            print("Error in detecting sensor type from its name", self.name, ", default to " + self.type)

        # Bind all callbacks
        self.battery_callback = battery_callback
        self.connected_callback = connected_callback
        self.disconnected_callback = disconnected_callback

        # Create disconnection event
        self.disconnected_event = asyncio.Event()
        self.stop_flag = False

        # Init empty bleak client
        self.client = None

    def __get_battery_callback(self):
        def battery_callback(sender: bleak.BleakGATTCharacteristic, data: bytearray):
            self.battery_callback(self, data)

        return battery_callback

    def __get_disconnected_callback(self):
        def disconnected_callback(client):
            print(" ")
            print("\033[91m" + self.name + " disconnected ! \033[00m")
            try:
                self.disconnected_event._loop.call_soon_threadsafe(self.disconnected_event.set)
            except:
                print("error while setting disconnect event")

        return disconnected_callback

    def is_connected(self):
        if self.client != None:
            return self.client.is_connected
        else:
            return False

    async def disconnect(self):
        print("Attempt to stop " + self.name)
        self.stop_flag = True
        if self.is_connected():
            await self.client.disconnect()

    async def start_notifications(self):
        await self.client.start_notify("00002a19-0000-1000-8000-00805f9b34fb", self.__get_battery_callback())
        await self.client.start_notify("6e400003-b5a3-f393-e0a9-e50e24dcca9e", self.data.get_data_callback())

    async def stop_notifications(self):
        await self.client.stop_notify("00002a19-0000-1000-8000-00805f9b34fb")
        await self.client.stop_notify("6e400003-b5a3-f393-e0a9-e50e24dcca9e")

    async def connect(self):
        while not self.stop_flag:
            print(" ")
            print("Scanning " + self.type + " devices for " + self.name + "...")
            device = None
            devices = await bleak.BleakScanner.discover()

            for d in devices:
                if d.name is not None and self.type in d.name:
                    device = d
                    break

            if device:
                print("Device", device.name, "found - attempting to connect...")
                self.disconnected_event.clear()

                try:
                    async with bleak.BleakClient(device.address,
                                                 disconnected_callback=self.__get_disconnected_callback()) as client:
                        self.client = client
                        print("\033[92m" + self.name + " is connected \033[00m")

                        # Update embedded RTC
                        await self.client.write_gatt_char(
                            "6e400002-b5a3-f393-e0a9-e50e24dcca9e",
                            await time_encode(),
                            response=False)

                        # Notify connection to main app
                        await self.connected_callback()

                        # Wait for disconnection using asyncio event
                        await self.disconnected_event.wait()
                        await self.disconnected_callback(self)
                    self.client = None

                except KeyboardInterrupt:
                    print("Exiting - waiting for sensor", self.name, "disconnection")
                    return

                except bleak.exc.BleakDeviceNotFoundError:
                    print("Error while connecting " + self.name)
                    pass
            else:
                print("No device found. New scan will start in 3 sec.")

            await asyncio.sleep(3)
