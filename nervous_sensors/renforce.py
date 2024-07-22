import argparse
import asyncio
import datetime
import time

import renforce_file
import renforce_gui
import renforce_lsl
from renforce_lsl import send_callback
from renforce_sensor import RenforceSensor

# List of sensor objects
_sensors: RenforceSensor = []

# Flag to retain global data notification state (enabled / disabled)
_run_flag = False

# Interfaces which will be used
_lsl_is_enabled = False
_file_is_enabled = False
_gui_is_enabled = False

# Initial launch script timestamp (for later relative time calculations)
_start_time = int(time.time())


def sensor_battery_callback(sensor: RenforceSensor, data):
    """
    sensor_battery_callback is the recipient of battery level sent by sensors using BLE indications
    """
    battery_level = int.from_bytes(data, byteorder="little")
    print(sensor.name + f" Battery level: {battery_level}%")


async def sensor_connected_callback():
    """
    sensor_connected_callback is the recipient for connection events.
    Each time this function is called by a sensor, it counts how many
    sensors are connected to check if all sensors are connected.
    When this occurs, data notifications can be enabled.
    This is to secure connection process without having BLE saturated with data.
    """
    global _run_flag
    connected_sensors = 0
    # Check how many sensors are now connected
    for sensor in _sensors:
        if sensor.is_connected():
            connected_sensors += 1
        else:
            print("Waiting for " + sensor.name + " to be connected")
    total_sensors = len(_sensors)
    print(str(connected_sensors) + " of " + str(total_sensors) + " sensors connected")
    # Enable notifications if all sensors are connected
    if connected_sensors == len(_sensors):
        for sensor in _sensors:
            await sensor.start_notifications()
        # Using a flag to disable the stop notify if it's already disable##
        _run_flag = True
        print("")
        print("\033[92mNotifications are now enabled.\033[00m")


async def sensor_disconnected_callback(self: RenforceSensor):
    """
    sensor_disconnected_callback is the recipient for disconnection events.
    In that case, all notifications from other sensors must be disabled to let this sensor be properly reconnected.
    """
    global _run_flag
    for sensor in _sensors:
        if sensor.is_connected() and _run_flag:
            await sensor.stop_notifications()
            print(sensor.name + " stop notify !")
    _run_flag = False


async def main(file_path, enable_lsl, enable_gui, sensors_list):
    global _lsl_is_enabled, _file_is_enabled, _gui_is_enabled, _sensors
    _lsl_is_enabled = enable_lsl
    _gui_is_enabled = enable_gui

    if file_path:
        _file_is_enabled = True
        print("File recording enabled")
    start_time_str = f'{datetime.datetime.today().strftime("%Y_%m_%d")}_{datetime.datetime.now().strftime("%Hh%Mm")}'

    callbacks = []
    if _lsl_is_enabled:
        callbacks.append(send_callback)

    for sensor_name in sensors_list:
        _sensors.append(
            RenforceSensor(
                sensor_name,
                start_time=_start_time,
                callbacks=callbacks,
                battery_callback=sensor_battery_callback,
                connected_callback=sensor_connected_callback,
                disconnected_callback=sensor_disconnected_callback,
            )
        )
    if _file_is_enabled:
        renforce_file.start()

    if _gui_is_enabled:
        renforce_gui.start()

    # Create a task depending on the number of variables
    async with asyncio.TaskGroup() as tg:
        for sensor in _sensors:
            if _file_is_enabled:
                sensor.start_time_str = start_time_str
                renforce_file.add_sensor(sensor, file_path)

            if _gui_is_enabled:
                renforce_gui.add_sensor(sensor)

            if _lsl_is_enabled:
                renforce_lsl.init(sensor)

            tg.create_task(sensor.connect())
            await asyncio.sleep(20)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--gui", action="store_true", help="Show real-time data graph")
    parser.add_argument("-f", "--folder", help="Save CSV data files in folder")
    parser.add_argument(
        "-l",
        "--lsl",
        action="store_true",
        help="Send sensor data on LSL outlets",
    )
    parser.add_argument(
        "-s",
        "--sensors",
        help="ECGxxx,EDAxxx... : Give the name of the sensors you want"
        " to use. Make sure to put 'ecg' or 'eda' in their name so the program"
        " will know which type of sensor you want to use (not case sensitive)",
    )

    arg = parser.parse_args()
    # Default sensors list if none are provided
    if arg.sensors is None:
        arg.sensors = "ecg1,eda1"
    # Split the sensors_value into a list of sensor names
    sensors_list = [sensor.strip().upper() for sensor in arg.sensors.split(",")]
    # BUG WARN
    print("")
    print("")
    print("\033[93m ***************************************")
    print("\033[93m WARNING : Always list ECG devices first")
    print("\033[93m *************************************** \033[00m ")
    print("")

    # Call the main function with the parsed arguments
    try:
        asyncio.run(main(arg.folder, arg.lsl, arg.gui, sensors_list))
    except KeyboardInterrupt:
        if _file_is_enabled:
            renforce_file.stop()
        if _gui_is_enabled:
            renforce_gui.stop()
        time.sleep(1.0)
    print(" ")
    print("\033[93m ****** Exiting RENFORCE Application ****** \033[00m")
    print(" ")
