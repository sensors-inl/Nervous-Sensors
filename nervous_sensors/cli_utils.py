from datetime import datetime

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

SENSORS_HELP = (
    '"ECG XXXX","EDA XXXX",... : specify a list of'
    "sensors name to connect to. Replace XXXX with the"
    "serial number."
)
GUI_HELP = (
    "Show real-time data graph in web browser."
    "Get the URL of the webserver in the output console"
    "when the script is launched."
)
FOLDER_HELP = "Save CSV data files in folder." "WARNING: The folder must exist as it won't be created."
LSL_HELP = "Send sensor data on LSL outlets."
PARALLEL_HELP = "Number of parallel connection tentatives authorized." "This is optional and should not be set."


def printf(*arg, **kwarg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(timestamp, *arg, **kwarg)


def print_start_info(info):
    printf(f"{GREEN}{info}{RESET}")


def print_stop_info(info):
    printf(f"{RED}{info}{RESET}")


def print_bold_section(section):
    printf(f"\n\033[1m{section}\033[22m\n")


def print_general_info(info):
    printf(f"\033[38;5;245m{info}\033[0m")


def get_color(i):
    return [
        # "\033[34m",  # blue
        # "\033[35m",  # magenta skip magenta because of PS background color
        # "\033[36m",  # cyan
        # "\033[33m",  # yellow
        "\033[91m",  # light red
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
    ][i % 15]
