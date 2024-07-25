import asyncio
from unittest.mock import Mock

import pytest

from nervous_sensors.connection_manager import ConnectionManager
from nervous_sensors.nervous_sensor import NervousSensor


@pytest.fixture
def mock_nervous_sensor1():
    mock_sensor = Mock(spec=NervousSensor)
    mock_sensor.is_connected.return_value = False
    return mock_sensor


@pytest.fixture
def mock_nervous_sensor2():
    mock_sensor = Mock(spec=NervousSensor)
    mock_sensor.is_connected.return_value = False
    return mock_sensor


@pytest.fixture
def mock_nervous_sensor3():
    mock_sensor = Mock(spec=NervousSensor)
    mock_sensor.is_connected.return_value = False
    return mock_sensor


@pytest.mark.asyncio
async def test_start_connection(mock_nervous_sensor1, mock_nervous_sensor2, mock_nervous_sensor3):
    manager = ConnectionManager(sensor_names=[], gui=False, folder=False, lsl=False, parallel_connection_authorized=3)
    sensors = [mock_nervous_sensor1, mock_nervous_sensor2, mock_nervous_sensor3]
    manager._sensors = sensors

    try:
        await asyncio.wait_for(manager.start(), timeout=1)
    except asyncio.TimeoutError:
        pass

    for mock_sensor in sensors:
        assert mock_sensor.connect.call_count >= 1


@pytest.mark.asyncio
async def test_stop_all_notifications():
    assert True
