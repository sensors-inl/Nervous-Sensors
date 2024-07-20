# Python backend for physiological sensors in RENFORCE ANR project

This project aims at implementing drivers in python to handle connection to 
Bluetooth Low Energy sensors developed in the frame of ANR project RENFORCE.
It also implements an interface to PLUME Unity plugin to collect data within a 
virtual environment for synchronous recording as well as real-time feedback to 
the user.

# CPU consumption

- BLE : no significant CPU usage was noticed with Bleak
- Data storage : `TRESH1` & `TRESH2` values in `reforce_lsl.py` file may be 
adjusted according to your system's performance

# CLI

```shell
Usage: nervous [OPTIONS] [ARGS]

Options:
  -g, --gui           Show real-time data graph
  -f, --folder PATH   Save CSV data files in folder
  -l, --lsl           Send sensor data on LSL outlets
  -s, --sensors TEXT  ECGxxx,EDAxxx... : Give the name of the sensors you want to use. 
                      Make sure to put 'ecg' or 'eda' in their name so the program will 
                      know which type of sensor you want to use (not case sensitive).
  --help              Show this message and exit.

Commands:
  export-csv               Export samples from the record to CSV files.
  export-world-transforms  Export world transforms of a GameObject with the given GUID to a CSV file.
  export-xdf               Export a XDF file including LSL samples and markers.
  find-guid                Find the GUID(s) of a GameObject by the given name.
  find-name                Find the name(s) of a GameObject with the given GUID in the record.
```

### Example

```shell
nervous -g -l -s ECG6543,EDA7201
```