import logging

logger = logging.getLogger("nervous")

# Terminal color codes
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

# Help text for CLI options
SENSORS_HELP = (
    '"ECG XXXX","EDA XXXX",... : specify a list of sensors name to connect to. Replace XXXX with the serial number.'
)
GUI_HELP = (
    "Show real-time data graph in web browser. "
    "Get the URL of the webserver in the output console "
    "when the script is launched."
)
FOLDER_HELP = "Save CSV data files in folder. WARNING: The folder must exist as it won't be created."
LSL_HELP = "Send sensor data on LSL outlets."
PARALLEL_HELP = "Number of parallel connection tentatives authorized. This is optional and should not be set."

# Available colors for different sensors or outputs
colors = [
    # "\033[34m",  # blue
    # "\033[35m",  # magenta
    # "\033[36m",  # cyan
    # "\033[33m",  # yellow
    # "\033[91m",  # light red
    "\033[92m",  # light green
    "\033[93m",  # light yellow
    "\033[94m",  # light blue
    "\033[95m",  # light magenta
    "\033[96m",  # light cyan
    "\033[38;5;208m",  # orange
    "\033[38;5;214m",  # gold
    "\033[38;5;172m",  # brown
    "\033[38;5;105m",  # purple
    "\033[38;5;130m",  # violet
]


def print_green(info) -> str:
    """
    Format an info message with green color to indicate starting an operation.

    Args:
        info (str): Information message to display.
    """
    message = f"{GREEN}{info}{RESET}"
    return message


def print_red(info) -> str:
    """
    Format an info message with red color to indicate stopping an operation.

    Args:
        info (str): Information message to display.
    """
    message = f"{RED}{info}{RESET}"
    return message


def print_bold(info):
    """
    Format a info message in bold formatting.

    Args:
        section (str): Section header text.
    """
    print("")
    message = f"\033[1m{info}\033[22m\n"
    return message


def print_grey(info):
    """
    Format general information in gray color.

    Args:
        info (str): Information message to display.
    """
    message = f"\033[38;5;245m{info}\033[0m"
    return message


def get_color(i):
    """
    Get a color from the color palette based on an index.

    Args:
        i (int): Index used to select a color from the palette.

    Returns:
        str: ANSI color code.
    """
    return colors[i % len(colors)]


def extract_sensors(sensors):
    """
    Extract sensor names from a list, handling different format variants.

    Handles formats: ECG/EDAxxx, ECG/EDA_xxx, and ECG/EDA-xxx

    Args:
        sensors (list): List of sensor strings.

    Returns:
        list: List of extracted sensor names in standard format ECG/EDAxxx.
    """
    logger.debug(f"Extracting sensors from: {sensors}")
    if not sensors:
        logger.warning("Empty sensors list provided")
        return []

    if "_" in sensors[0] or "-" in sensors[0]:
        result = [f"{s[:3]}{s[4:]}" for s in sensors if "ecg" in s.lower() or "eda" in s.lower()]
    else:
        result = [s for s in sensors if "ecg" in s.lower() or "eda" in s.lower()]

    logger.debug(f"Extracted sensors: {result}")
    return result
