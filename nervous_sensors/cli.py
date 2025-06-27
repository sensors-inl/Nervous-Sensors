import asyncio
import logging
import os
import sys
import traceback

import click

from . import utils
from .cli_listener import CLIListener
from .connection_manager import ConnectionManager
from .utils import extract_sensors, print_bold, print_green, print_grey, print_red

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("nervous")


@click.command()
@click.option("-s", "--sensors", help=utils.SENSORS_HELP)
@click.option("-g", "--gui", is_flag=True, help=utils.GUI_HELP)
@click.option("-f", "--folder", type=click.Path(), help=utils.FOLDER_HELP)
@click.option("-l", "--lsl", is_flag=True, help=utils.LSL_HELP)
@click.option("-p", "--parallel", default=1, help=utils.PARALLEL_HELP)
def cli(sensors, gui, folder, lsl, parallel):
    """
    Command-line interface for the Nervous framework.

    This function processes command-line arguments, initializes the connection manager,
    and runs the application.
    """
    # Redirect stdout/stderr to our custom listener to filter certain messages
    sys.stdout = CLIListener(sys.stdout)
    sys.stderr = CLIListener(sys.stderr)

    logger.info(print_bold("Starting Nervous CLI"))

    if sensors:
        sensors = sensors.split(",")
        true_sensors = extract_sensors(sensors)

        if not true_sensors:
            logger.error(print_red("No sensors follows -s/--sensors option, use syntax ECGxxx,EDAxxx..."))
            sys.exit(0)
        else:
            logger.info(print_grey(f"Sensors used: {true_sensors}"))
    else:
        logger.error(print_red("Option -s/--sensors is required."))
        sys.exit(0)

    # Initialize the connection manager
    manager = ConnectionManager(true_sensors, gui, folder, lsl, parallel)

    try:
        logger.info(print_green("Starting application event loop"))
        asyncio.run(run_app(manager))
    except (KeyboardInterrupt, OSError) as e:
        logger.info(print_red(f"Application terminated: {str(e)}"))
        logger.info(print_red("Shutting down Nervous framework"))
        os._exit(os.EX_OK)


async def run_app(manager: ConnectionManager):
    """
    Run the application using the provided connection manager.

    Args:
        manager (ConnectionManager): The connection manager instance.
    """
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(manager.start())
    except Exception as e:
        logger.error(print_red(f"Error in connection manager: {str(e)}"))
        logger.debug(f"Traceback: {traceback.format_exc()}")
        await manager.stop()
