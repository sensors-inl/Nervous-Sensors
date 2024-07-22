# Nervous Sensors

This project aims at implementing drivers in python to handle connection to
Bluetooth Low Energy sensors developed in the frame of ANR project RENFORCE.
It also implements an interface to PLUME Unity plugin to collect data within a
virtual environment for synchronous recording as well as real-time feedback to
the user.

## Installation

```bash
pip install nervous-sensors
```

## CLI

```text
Usage: nervous [OPTIONS]

Options:
  -g, --gui           Show real-time data graph
  -f, --folder PATH   Save CSV data files in folder
  -l, --lsl           Send sensor data on LSL outlets
  -s, --sensors TEXT  ECGxxx,EDAxxx... : Give the name of the sensors you want
                      to use. Make sure to put 'ecg' or 'eda' in their name so
                      the program will know which type of sensor you want to
                      use (not case sensitive).
  --help              Show this message and exit.
```

### Example

```bash
nervous -g -f data/csv/ -l -s ECG6543,EDA7201
```

## CPU consumption

- BLE : no significant CPU usage was noticed with Bleak
- Data storage : `TRESH1` & `TRESH2` values in `reforce_lsl.py` file may be
adjusted according to your system's performance
