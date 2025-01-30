import asyncio
from unittest.mock import Mock

from nervous_sensors.nervous_sensor import NervousSensor


def get_correct_sensor(manager):
    """
    :return: A mock sensor that will connect and stay connected.
    """
    mock_sensor = Mock(spec=NervousSensor)

    async def connect_side_effect():
        mock_sensor.is_connected.return_value = True
        manager.on_sensor_connect(mock_sensor)
        await asyncio.sleep(100)

    mock_sensor.connect.side_effect = connect_side_effect
    mock_sensor.is_connected.return_value = False
    return mock_sensor


def get_failed_sensor(manager):
    """
    :return: A mock sensor that will fail to connect.
    """
    mock_sensor = Mock(spec=NervousSensor)

    async def connect_side_effect():
        manager.on_sensor_fail_to_connect(mock_sensor)

    mock_sensor.connect.side_effect = connect_side_effect
    mock_sensor.is_connected.return_value = False
    return mock_sensor


def get_sensor_with_disconnection(manager):
    """
    :return: A mock sensor that will connect and has disconnections occurring.
    """
    mock_sensor = Mock(spec=NervousSensor)

    async def connect_side_effect():
        mock_sensor.is_connected.return_value = True
        manager.on_sensor_connect(mock_sensor)
        await asyncio.sleep(0.1)
        mock_sensor.is_connected.return_value = False
        manager.on_sensor_disconnect(mock_sensor)

    mock_sensor.connect.side_effect = connect_side_effect
    mock_sensor.is_connected.return_value = False
    return mock_sensor
