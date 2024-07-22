import asyncio
import threading

from renforce_viewer import RenforceViewer

sensors_list = []
update_interval = 0.5
quit_event = asyncio.Event()
viewer = None


def start():
    global viewer
    viewer = RenforceViewer()
    threading.Thread(target=viewer.run_server).start()
    print("Gui thread started")


def add_sensor(sensor):
    viewer.add_sensor(sensor)
