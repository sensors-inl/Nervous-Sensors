import threading

from .async_manager import AsyncManager
from .viewer import RenforceViewer
from .cli_utils import print_start_info, print_stop_info

class GUIManager(AsyncManager):

    def __init__(self, sensors):
        super().__init__()
        self._sensors = sensors
        self._viewer = None
        self._server_thread = None


    async def start(self):
        print_start_info('Starting GUI manager')
        self._viewer = RenforceViewer(self._sensors)
        self._server_thread = threading.Thread(target=self._viewer.run_server)
        self._server_thread.start()


    async def stop(self):
        print_stop_info('Stopping GUI manager')
        self._viewer.stop_server()
        self._server_thread.join()






