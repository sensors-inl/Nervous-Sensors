import asyncio
from unittest.mock import AsyncMock, Mock

from bleak import BleakClient, BleakError, BleakScanner, BLEDevice

from nervous_sensors.connection_manager import ConnectionManager
from nervous_sensors.nervous_sensor import NervousSensor

# Scanners


def get_mock_scanner_device_found():
    """
    :return: A mock scanner that will return a mock device when find_device_by_name is called.
    """
    scanner = Mock(spec=BleakScanner)
    device = Mock(spec=BLEDevice)
    scanner.find_device_by_name.return_value = device
    return scanner


def get_mock_scanner_device_not_found():
    """
    :return: A mock scanner that will return None when find_device_by_name is called.
    """
    scanner = Mock(spec=BleakScanner)
    scanner.find_device_by_name.return_value = None
    return scanner


# Clients


def get_mock_client_connection():
    """
    :return: A mock client that will return itself when __aenter__ (async with) is called.
    """
    mock_client = AsyncMock(spec=BleakClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    return mock_client


def get_mock_client_fail_connection():
    """
    :return: A mock client that will raise a BleakError when __aenter__ (async with) is called.
    """
    mock_client = AsyncMock(spec=BleakClient)
    mock_client.__aenter__ = AsyncMock(side_effect=BleakError)
    return mock_client


# Disconnection events


def get_mock_client_with_disconnection_event():
    """
    :return: A mock client that will return itself when __aenter__ (async with) is called
    and an event that will be set when disconnect is called.
    """
    mock_client = AsyncMock(spec=BleakClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    disconnection_event = asyncio.Event()
    mock_client.disconnect.side_effect = lambda: disconnection_event.set()
    return mock_client, disconnection_event


def get_disconnection_event_raise_error():
    """
    :return: An event that will raise a BleakError when wait is called.
    """
    mock_event = Mock(spec=asyncio.Event)
    mock_event.wait = AsyncMock(side_effect=BleakError)
    return mock_event


# Connection manager


def get_mock_sensor_and_connection_manager():
    """
    :return: A mock sensor and a mock connection manager.
    """
    manager = Mock(spec=ConnectionManager)
    sensor = NervousSensor("ECG73BA", 0, 10, manager)
    return sensor, manager
