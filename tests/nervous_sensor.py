import asyncio
from asyncio import TaskGroup
from unittest.mock import Mock

import pytest
from bleak import BleakClient, BleakScanner, BLEDevice

from nervous_sensors.connection_manager import ConnectionManager
from nervous_sensors.nervous_sensor import NervousSensor


@pytest.fixture
def mock_bleak_client():
    return Mock(spec=BleakClient)


@pytest.fixture
def mock_bleak_scanner():
    return Mock(spec=BleakScanner)


@pytest.fixture
def mock_bleak_device():
    return Mock(spec=BLEDevice)


@pytest.fixture
def mock_connection_manager():
    return Mock(spec=ConnectionManager)


@pytest.mark.asyncio
async def tes_connect(mock_connection_manager, mock_bleak_client, mock_bleak_scanner, mock_bleak_device):
    sensor = NervousSensor("ECG73BA", "2023-03-01 12:00:00", 10, mock_connection_manager)
    sensor._client = mock_bleak_client
    sensor._scanner = mock_bleak_scanner

    mock_bleak_scanner.find_device_by_name.return_value = mock_bleak_device
    mock_bleak_client.connect.return_value = True

    async def disconnection_event():
        await asyncio.sleep(1)
        await sensor.disconnect()

    async with TaskGroup() as tg:
        tg.create_task(sensor.connect())
        tg.create_task(disconnection_event())

    mock_connection_manager.on_sensor_connect.assert_called_once_with(sensor)
    mock_connection_manager.on_sensor_fail_to_connect.assert_not_called()
    mock_connection_manager.on_sensor_disconnect.assert_called_once_with(sensor)


@pytest.mark.asyncio
async def tes_connect_fail(mock_connection_manager, mock_bleak_client, mock_bleak_scanner):
    sensor = NervousSensor("ECG73BA", "2023-03-01 12:00:00", 10, mock_connection_manager)
    sensor._client = mock_bleak_client
    sensor._scanner = mock_bleak_scanner

    mock_bleak_scanner.find_device_by_name.return_value = None
    mock_bleak_client.connect.return_value = False
    await sensor.connect()

    mock_connection_manager.on_sensor_connect.assert_not_called()
    mock_connection_manager.on_sensor_fail_to_connect.assert_called_once_with(sensor)
    mock_connection_manager.on_sensor_disconnect.assert_not_called()
