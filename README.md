<p align="center">
    <img src="https://raw.githubusercontent.com/sensors-inl/Nervous-Sensors/refs/heads/main/assets/nervous-logo.png" align="center" width="50%">
</p>
<p align="center">
    <h1 align="center">Nervous Sensors</h1>
</p>

<p align="center">
  <a href="https://badge.fury.io/py/nervous-sensors"><img src="https://badge.fury.io/py/nervous-sensors.svg" alt="PyPI version" height="18"></a>
  <a href="https://pypi.org/project/nervous-sensors/"><img src="https://img.shields.io/pypi/pyversions/nervous-sensors.svg" alt="Python Versions" height="18"></a>
  <a href="https://github.com/sensors-inl/Nervous-Sensors/actions"><img src="https://github.com/sensors-inl/Nervous-Sensors/workflows/CI/badge.svg" alt="Build Status" height="18"></a>
  <!-- a href="https://nervous-sensors.readthedocs.io/en/latest/?badge=latest"><img src="https://readthedocs.org/projects/nervous-sensors/badge/?version=latest" alt="Documentation Status" height="18"></a -->
  <!-- a href="https://pypi.org/project/nervous-sensors/"><img src="https://img.shields.io/pypi/dm/nervous-sensors.svg" alt="Downloads" height="18"></a -->
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" height="18"></a>
</p>

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Project Overview](#project-overview)
  - [Key Features](#key-features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Command-Line Interface (CLI)](#command-line-interface-cli)
  - [Usage](#usage)
    - [Options](#options)
  - [Example Command](#example-command)
- [Sensor Compatibility](#sensor-compatibility)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Contact](#contact)

---

## Project Overview

Nervous Sensors is a Python-based driver and data acquisition toolset for physiological sensors, specifically designed for [Nervous ECG](https://github.com/sensors-inl/Nervous-ECG) (Electrocardiography) and [Nervous EDA](https://github.com/sensors-inl/Nervous-EDA) (Electrodermal Activity) sensors developed in the frame of the [Nervous Toolkit](https://github.com/sensors-inl/Nervous-Toolkit).

### Key Features

- 📱 Bluetooth Low Energy (BLE) sensor support
- 📈 Real-time data visualization via local webserver
- 💾 Flexible data storage (CSV export)
- 📣 LSL (Lab Streaming Layer) integration for [PLUME](https://github.com/liris-xr/PLUME) Unity plugin
- 🔗 Multi-sensor connection capabilities

---

## Prerequisites

- Python 3.11, 3.12 or 3.13
- Compatible Bluetooth Low Energy Nervous sensors

---

## Installation

```bash
pip install nervous-sensors
```

---

## Command-Line Interface (CLI)

### Usage

```bash
nervous [OPTIONS]
```

#### Options

| Option | Description | Example |
|--------|-------------|---------|
| `-s, --sensors` | Specify sensors to connect (by serial number) | `"ECG 6543","EDA 7201"` |
| `-g, --gui` | Enable real-time data graph in web browser | |
| `-f, --folder` | Save CSV data files to specified folder | `./data/csv/` |
| `-l, --lsl` | Send sensor data to LSL outlets | |
| `-p, --parallel` | Set number of parallel connection attempts | |

### Example Command

```bash
# Connect to multiple sensors, enable GUI, save to CSV, and activate LSL
nervous -g -f ./data/csv/ -l -s "ECG 6543","EDA 7201"
```

---

## Sensor Compatibility

- Nervous ECG Sensors
- Nervous EDA Sensors

---

## Contributing

Contributions are what make the open-source community such a great place to learn, inspire, and create. Any contributions you make are greatly appreciated. You can open an issue to report a bug, request a feature, or submit a pull request.

---

## License

This project, along with the entire Nervous initiative, is licensed under the [MIT License](https://opensource.org/licenses/MIT). For more details, see the [License](LICENSE.md) file.

---

## Acknowledgments

The main contributors to this project are Bertrand Massot, Tristan Habémont and Hugo Buy from INSA Lyon, CNRS, INL UMR 5270, Villeurbanne, France.

This work was supported by the **French National Research Agency (ANR)** under grant **ANR-22-CE31-0023-03 RENFORCE**.

---

## Contact

[bertrand.massot@insa-lyon.fr](mailto:bertrand.massot@insa-lyon.fr)

---
