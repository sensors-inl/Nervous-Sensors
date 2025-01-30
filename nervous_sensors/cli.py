import asyncio
import sys

import click

from . import cli_utils
from .cli_listener import CLIListener
from .cli_utils import extract_sensors, print_bold_section, print_general_info, print_stop_info
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
            print_stop_info("No sensors follows -s/--sensors option, use synthax ECGxxx,EDAxxx...")
            sys.exit(0)
        else:
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
    if parallel:
        print_general_info(f"- Parallel connection authorized: {parallel}")

    manager = ConnectionManager(true_sensors, gui, folder, lsl, parallel)

    try:
        asyncio.run(run_app(manager))
    except (KeyboardInterrupt, OSError):
        print_stop_info("Shutting down Nervous framework")
        sys.exit(0)

async def run_app(manager:ConnectionManager):
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(manager.start())
    except Exception:
        await manager.stop()
