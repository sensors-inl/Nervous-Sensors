import asyncio
from asyncio import TaskGroup

import pytest

from nervous_sensors.connection_manager import ConnectionManager
from tests.mock_sensors import get_correct_sensor, get_failed_sensor, get_sensor_with_disconnection

timeout = 3


@pytest.mark.asyncio
async def test_connection():
    manager = ConnectionManager(sensor_names=[])
    sensors = [get_correct_sensor(manager), get_correct_sensor(manager), get_correct_sensor(manager)]
    manager._sensors = sensors

    try:
        await asyncio.wait_for(manager.start(), timeout=timeout)
    except asyncio.TimeoutError:
        pass

    for mock_sensor in sensors:
        mock_sensor.connect.assert_called_once()
        mock_sensor.start_notifications.assert_called_once()
        mock_sensor.stop_notifications.assert_not_called()
        mock_sensor.disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_failed_connection():
    manager = ConnectionManager(sensor_names=[])
    sensors = [get_correct_sensor(manager), get_correct_sensor(manager), get_failed_sensor(manager)]
    manager._sensors = sensors

    try:
        await asyncio.wait_for(manager.start(), timeout=timeout)
    except asyncio.TimeoutError:
        pass

    for mock_sensor in sensors:
        mock_sensor.start_notifications.assert_not_called()
        mock_sensor.stop_notifications.assert_not_called()
        mock_sensor.disconnect.assert_not_called()

    assert sensors[0].connect.call_count == 1
    assert sensors[1].connect.call_count == 1
    assert sensors[2].connect.call_count >= 1


@pytest.mark.asyncio
async def test_connection_with_disconnection():
    manager = ConnectionManager(sensor_names=[])
    sensors = [
        get_correct_sensor(manager),
        get_correct_sensor(manager),
        get_sensor_with_disconnection(manager),
    ]
    manager._sensors = sensors

    try:
        await asyncio.wait_for(manager.start(), timeout=timeout)
    except asyncio.TimeoutError:
        pass

    for mock_sensor in sensors:
        start_call_count = mock_sensor.start_notifications.call_count
        assert start_call_count >= 2
        assert mock_sensor.stop_notifications.call_count == (start_call_count - 1) or start_call_count
        mock_sensor.disconnect.assert_not_called()

    assert sensors[0].connect.call_count == 1
    assert sensors[1].connect.call_count == 1
    assert sensors[2].connect.call_count >= 2


@pytest.mark.asyncio
async def test_disconnection():
    manager = ConnectionManager(sensor_names=[])
    sensors = [get_correct_sensor(manager), get_correct_sensor(manager), get_correct_sensor(manager)]
    manager._sensors = sensors

    async def task():
        async with TaskGroup() as tg:
            tg.create_task(manager.start())
            await asyncio.sleep(0.1)
            await manager.stop()

    try:
        await asyncio.wait_for(task(), timeout=timeout)
    except asyncio.TimeoutError:
        pass

    for mock_sensor in sensors:
        mock_sensor.connect.assert_called_once()
        mock_sensor.start_notifications.assert_called_once()
        mock_sensor.stop_notifications.assert_called_once()
        mock_sensor.disconnect.assert_called_once()
