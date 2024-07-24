RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

SENSORS_HELP = (
    "ECGxxx,EDAxxx... : Give the name of the sensors you want to use. "
    "Make sure to put 'ECG' or 'EDA' in their name so the program will know "
    "which type of sensor you want to use (not case sensitive)."
)
GUI_HELP = "Show real-time data graph."
FOLDER_HELP = "Save CSV data files in folder."
LSL_HELP = "Send sensor data on LSL outlets."
PARALLEL_HELP = "Number of parallel connection tentatives authorized."


def print_start_info(info):
    print(f"{GREEN}{info}{RESET}")


def print_stop_info(info):
    print(f"{RED}{info}{RESET}")


def print_bold_section(section):
    print(f"\n\033[1m{section}\033[22m\n")


def print_general_info(info):
    print(f"\033[38;5;245m{info}\033[0m")


def get_color(i):
    return [
        "\033[34m",  # blue
        "\033[35m",  # magenta
        "\033[36m",  # cyan
        "\033[33m",  # yellow
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
