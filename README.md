# Nervous Sensors

This project aims at implementing drivers in python to handle connection to
physiological sensors ECG and EDA developed at the Lyon Institute of
Nanotechnology (INL).
Those Bluetooth Low Energy sensors developed in the frame of ANR project
RENFORCE (grant ANR-22-CE38-0008).
Sensors data can be plotted in real-time on a local webserver or saved in a
.csv file.
It also implements an LSL interface to PLUME Unity plugin to collect data within
a virtual environment for synchronous recording as well as real-time feedback to
the user.

## Installation

> [!NOTE]
> Requires python version 3.11 or 3.12
>
> ```bash
> pip install nervous-sensors
> ```

## CLI

```text
Usage: nervous [OPTIONS]

Options:
  -s, --sensors TEXT      "ECG XXXX","EDA XXXX",... : specify a list of
                          sensors name to connect to. Replace XXXX with the
                          serial number.
  -g, --gui               Show real-time data graph in web browser.
                          Get the URL of the webserver in the output console
                          when the script is launched.
  -f, --folder PATH       Save CSV data files in folder.
                          WARNING: The folder must exist as it won't be created.
  -l, --lsl               Send sensor data on LSL outlets.
  -p, --parallel INTEGER  Number of parallel connection tentatives authorized.
                          This is optional and should not be set.
  --help                  Show this message and exit.
```

### Example

```bash
nervous -g -f ./data/csv/ -l -s "ECG 6543","EDA 7201"
```
