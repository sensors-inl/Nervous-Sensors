import asyncio
from asyncio import TaskGroup
from unittest.mock import patch

import pytest

from .mock_bleak import (
    get_disconnection_event_raise_error,
    get_mock_client_connection,
    get_mock_client_fail_connection,
    get_mock_client_with_disconnection_event,
    get_mock_scanner_device_found,
    get_mock_scanner_device_not_found,
    get_mock_sensor_and_connection_manager,
)

timeout = 2


def assert_called_event(manager, sensor, events):
    events = events.split("+")
    manager.on_sensor_connect.assert_called_once_with(
        sensor
    ) if "connect" in events else manager.on_sensor_connect.assert_not_called()

    manager.on_sensor_fail_to_connect.assert_called_once_with(
        sensor
    ) if "fail" in events else manager.on_sensor_fail_to_connect.assert_not_called()

    manager.on_sensor_disconnect.assert_called_once_with(
        sensor
    ) if "disconnect" in events else manager.on_sensor_disconnect.assert_not_called()


async def run_test(task, scanner, client, event=asyncio.Event()):
    with patch("nervous_sensors.nervous_sensor.BleakScanner", return_value=scanner):
        with patch("nervous_sensors.nervous_sensor.BleakClient", return_value=client):
            with patch("nervous_sensors.nervous_sensor.asyncio.Event", return_value=event):
                try:
                    await asyncio.wait_for(task, timeout=timeout)
                except asyncio.TimeoutError:
                    pass


# Operating connection tests


@pytest.mark.asyncio
async def test_sensor_connection():
    """
    Test if the sensor is connected by checking
    if the correct events are called on the manager.
    """
    sensor, manager = get_mock_sensor_and_connection_manager()
    await run_test(
        task=sensor.connect(),
        scanner=get_mock_scanner_device_found(),
        client=get_mock_client_connection(),
    )
    assert_called_event(manager, sensor, "connect")


@pytest.mark.asyncio
async def test_sensor_disconnection():
    """
    Test if the sensor is disconnected by checking
    if the correct events are called on the manager.
    """
    sensor, manager = get_mock_sensor_and_connection_manager()
    client, event = get_mock_client_with_disconnection_event()

    async def disconnection_task():
        async with TaskGroup() as tg:
            tg.create_task(sensor.connect())
            await asyncio.sleep(0.1)
            tg.create_task(sensor.disconnect())

    await run_test(
        task=disconnection_task(),
        scanner=get_mock_scanner_device_found(),
        client=client,
        event=event,
    )
    assert_called_event(manager, sensor, "connect+disconnect")


# Device didn't find test


@pytest.mark.asyncio
async def test_sensor_not_found():
    """
    Test if the sensor is not found by checking
    if the correct events are called on the manager.
    """
    sensor, manager = get_mock_sensor_and_connection_manager()
    await run_test(
        task=sensor.connect(),
        scanner=get_mock_scanner_device_not_found(),
        client=get_mock_client_connection(),
    )
    assert_called_event(manager, sensor, "fail")


# Client tests


@pytest.mark.asyncio
async def test_sensor_client_fail_connection():
    """
    Test if the sensor fails to connect by checking
    if the correct events are called on the manager.
    """
    sensor, manager = get_mock_sensor_and_connection_manager()
    await run_test(
        task=sensor.connect(),
        scanner=get_mock_scanner_device_found(),
        client=get_mock_client_fail_connection(),
    )
    assert_called_event(manager, sensor, "fail")


@pytest.mark.asyncio
async def test_sensor_client_disconnection():
    """
    Test if the sensor has disconnection problems by checking
    if the correct events are called on the manager.
    """
    sensor, manager = get_mock_sensor_and_connection_manager()
    await run_test(
        task=sensor.connect(),
        scanner=get_mock_scanner_device_found(),
        client=get_mock_client_connection(),
        event=get_disconnection_event_raise_error(),
    )
    assert_called_event(manager, sensor, "connect+disconnect")
