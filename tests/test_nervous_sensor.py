import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bleak import BleakClient, BleakError, BleakScanner, BLEDevice

from nervous_sensors.connection_manager import ConnectionManager
from nervous_sensors.nervous_sensor import NervousSensor

timeout = 3


def get_mock_scanner_device_found():
    scanner = Mock(spec=BleakScanner)
    device = Mock(spec=BLEDevice)
    scanner.find_device_by_name.return_value = device
    return scanner


def get_mock_scanner_device_not_found():
    scanner = Mock(spec=BleakScanner)
    scanner.find_device_by_name.return_value = None
    return scanner


def get_mock_client_connection():
    mock_client = AsyncMock(spec=BleakClient)
    mock_client.write_gatt_char = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


def get_mock_client_fail_connection():
    mock_client = AsyncMock(spec=BleakClient)
    mock_client.__aenter__ = AsyncMock(side_effect=BleakError)
    return mock_client


def get_mock_client_disconnection():
    mock_client = AsyncMock(spec=BleakClient)
    mock_client.write_gatt_char = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aenter__.side_effect = get_bleak_error(0.1)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


def get_mock_connection_manager():
    return Mock(spec=ConnectionManager)


def get_bleak_error(wait_time=None):
    async def _bleak_error():
        if wait_time is not None:
            await asyncio.sleep(wait_time)
        raise BleakError()

    return _bleak_error


@pytest.mark.asyncio
async def test_sensor_connection():
    manager = get_mock_connection_manager()
    scanner = get_mock_scanner_device_found()
    client = get_mock_client_connection()
    sensor = NervousSensor("ECG73BA", 0, 10, manager)

    with patch("nervous_sensors.nervous_sensor.BleakScanner", return_value=scanner):
        with patch("nervous_sensors.nervous_sensor.BleakClient", return_value=client):
            try:
                await asyncio.wait_for(sensor.connect(), timeout=timeout)
            except asyncio.TimeoutError:
                pass

    manager.on_sensor_connect.assert_called_once_with(sensor)
    manager.on_sensor_fail_to_connect.assert_not_called()
    # manager.on_sensor_disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_sensor_not_found():
    manager = get_mock_connection_manager()
    scanner = get_mock_scanner_device_not_found()
    sensor = NervousSensor("ECG73BA", 0, 10, manager)

    with patch("nervous_sensors.nervous_sensor.BleakScanner", return_value=scanner):
        try:
            await asyncio.wait_for(sensor.connect(), timeout=timeout)
        except asyncio.TimeoutError:
            pass

        manager.on_sensor_connect.assert_not_called()
        manager.on_sensor_fail_to_connect.assert_called_once_with(sensor)
        manager.on_sensor_disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_sensor_client_fail_connection():
    manager = get_mock_connection_manager()
    scanner = get_mock_scanner_device_found()
    client = get_mock_client_fail_connection()
    sensor = NervousSensor("ECG73BA", 0, 10, manager)

    with patch("nervous_sensors.nervous_sensor.BleakScanner", return_value=scanner):
        with patch("nervous_sensors.nervous_sensor.BleakClient", return_value=client):
            try:
                await asyncio.wait_for(sensor.connect(), timeout=timeout)
            except asyncio.TimeoutError:
                pass

            manager.on_sensor_connect.assert_not_called()
            manager.on_sensor_fail_to_connect.assert_called_once_with(sensor)
            manager.on_sensor_disconnect.assert_not_called()
