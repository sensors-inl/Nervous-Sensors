import asyncio
import sys
import os
from asyncio import TaskGroup

import click

from . import cli_utils
from .cli_listener import CLIListener
from .cli_utils import print_bold_section, print_general_info, print_stop_info
from .connection_manager import ConnectionManager


@click.command()
@click.option("-s", "--sensors", help=cli_utils.SENSORS_HELP)
@click.option("-g", "--gui", is_flag=True, help=cli_utils.GUI_HELP)
@click.option("-f", "--folder", type=click.Path(), help=cli_utils.FOLDER_HELP)
@click.option("-l", "--lsl", is_flag=True, help=cli_utils.LSL_HELP)
@click.option("-p", "--parallel", default=1, help=cli_utils.PARALLEL_HELP)
def cli(sensors, gui, folder, lsl, parallel):
    sys.stdout = CLIListener(sys.stdout)
    sys.stderr = CLIListener(sys.stderr)

    print_bold_section("Nervous CLI")

    if sensors:
        sensors = sensors.split(",")
        true_sensors = extract_sensors(sensors)

        if not true_sensors:
            print_stop_info("No sensors follows -s/--sensors option, please use \"ECG XXXX\",\"EDA XXXX\" format")
            sys.exit(0)
        else:
            print_general_info("Press 'enter' to stop the program properly")
            print_general_info(f"- Sensors used: {true_sensors}")
    else:
        print_stop_info("Option -s/--sensors is required.")
        sys.exit(0)

    if gui:
        print_general_info("- GUI enabled")
    if folder:
        print_general_info(f"- Folder saving enabled in: '{folder}'")
    if lsl:
        print_general_info("- LSL enabled")
    #if parallel:
    #    print_general_info(f"- Parallel connection authorized: {parallel}")

    try:
        asyncio.run(run_app(true_sensors, gui, folder, lsl, parallel))
    except KeyboardInterrupt:
        print_stop_info("Shutting down Nervous framework")
        os._exit(0)


def extract_sensors(sensors):
    """
    :return: all ECG/EDAxxx for formats : ECG/EDAxxx, ECG/EDA_xxx and ECG/EDA-xxx
    """
    for i, sensor in enumerate(sensors):
        sensor = sensor.replace(' ','')
        sensor = sensor.replace('_','')
        sensor = sensor.replace('-','')
        sensor = sensor[:3] + ' ' + sensor[3:]
        sensors[i] = sensor.upper()
    return [s for s in sensors if "ECG" in s or "EDA" in s]

async def run_app(sensor_names, gui, folder, lsl, parallel_connection_authorized):
    manager = ConnectionManager(sensor_names, gui, folder, lsl, parallel_connection_authorized)

    # async def listen_enter():
    #    await aioconsole.ainput()
    #    raise KeyboardInterrupt

    try:
        async with TaskGroup() as tg:
            # tg.create_task(listen_enter()) # TODO remove or not ?
            tg.create_task(manager.start())
    except Exception:
        await manager.stop()
