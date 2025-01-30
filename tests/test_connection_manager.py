import asyncio
from asyncio import TaskGroup

import pytest

from nervous_sensors.connection_manager import ConnectionManager

from .mock_sensors import get_correct_sensor, get_failed_sensor, get_sensor_with_disconnection

timeout = 2


async def run_timeout_task(task):
    try:
        await asyncio.wait_for(task, timeout=timeout)
    except asyncio.TimeoutError:
        pass


@pytest.mark.asyncio
async def test_connection():
    """
    Test if the manager connection works by checking
    if the correct methods are called on the sensors.
    """
    manager = ConnectionManager(sensor_names=[])
    sensors = [
        get_correct_sensor(manager),
        get_correct_sensor(manager),
        get_correct_sensor(manager),
    ]

    manager._sensors = sensors
    await run_timeout_task(manager.start())

    for mock_sensor in sensors:
        mock_sensor.connect.assert_called_once()
        mock_sensor.start_notifications.assert_called_once()
        mock_sensor.stop_notifications.assert_not_called()
        mock_sensor.disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_disconnection():
    """
    Test if the manager disconnection works by checking
    if the correct methods are called on the sensors.
    """
    manager = ConnectionManager(sensor_names=[])
    sensors = [
        get_correct_sensor(manager),
        get_correct_sensor(manager),
        get_correct_sensor(manager),
    ]

    async def task():
        async with TaskGroup() as tg:
            tg.create_task(manager.start())
            await asyncio.sleep(0.1)
            await manager.stop()

    manager._sensors = sensors
    await run_timeout_task(task())

    for mock_sensor in sensors:
        mock_sensor.connect.assert_called_once()
        mock_sensor.start_notifications.assert_called_once()
        mock_sensor.stop_notifications.assert_called_once()
        mock_sensor.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_failed_connection():
    """
    Test if the manager succeeds in handling when a sensor fails to connect
    by checking if the correct methods are called on the sensors.
    """
    manager = ConnectionManager(sensor_names=[])
    sensors = [
        get_correct_sensor(manager),
        get_correct_sensor(manager),
        get_failed_sensor(manager),
    ]

    manager._sensors = sensors
    await run_timeout_task(manager.start())

    for mock_sensor in sensors:
        mock_sensor.start_notifications.assert_not_called()
        mock_sensor.stop_notifications.assert_not_called()
        mock_sensor.disconnect.assert_not_called()

    assert sensors[0].connect.call_count == 1
    assert sensors[1].connect.call_count == 1
    assert sensors[2].connect.call_count >= 1


@pytest.mark.asyncio
async def test_connection_with_disconnection():
    """
    Test if the manager succeeds in handling when a sensor has disconnection problems
    by checking if the correct methods are called on the sensors.
    """
    manager = ConnectionManager(sensor_names=[])
    sensors = [
        get_correct_sensor(manager),
        get_correct_sensor(manager),
        get_sensor_with_disconnection(manager),
    ]

    manager._sensors = sensors
    await run_timeout_task(manager.start())

    for mock_sensor in sensors:
        call_count = mock_sensor.start_notifications.call_count
        assert call_count >= 2
        assert mock_sensor.stop_notifications.call_count == (call_count - 1) or call_count
        mock_sensor.disconnect.assert_not_called()

    assert sensors[0].connect.call_count == 1
    assert sensors[1].connect.call_count == 1
    assert sensors[2].connect.call_count >= 2
