import logging
import threading
import traceback

from .async_manager import AsyncManager
from .viewer import RenforceViewer

logger = logging.getLogger("nervous")


class GUIManager(AsyncManager):
    """
    Manages the graphical user interface for visualizing sensor data.

    This class handles the creation and management of a viewer that displays
    real-time sensor data. The viewer runs in a separate thread.

    Attributes:
        _sensors: List of sensor objects to be visualized.
        _viewer: The RenforceViewer instance for displaying sensor data.
        _server_thread: Thread that runs the viewer server.
    """

    def __init__(self, sensors):
        """
        Initialize the GUI manager.

        Args:
            sensors: List of sensor objects to be visualized.
        """
        super().__init__()
        self._sensors = sensors
        self._viewer = None
        self._server_thread = None

    async def start(self):
        """
        Start the GUI manager and viewer in a separate thread.

        Creates the viewer and starts its server in a background thread.
        """
        logger.info("Starting GUI manager")
        try:
            self._viewer = RenforceViewer(self._sensors, 6378)
            self._server_thread = threading.Thread(target=self._viewer.run_server)
            self._server_thread.start()
        except Exception as e:
            logger.error(f"Error starting GUI manager: {str(e)}")
            logger.debug(traceback.format_exc())
            raise

    async def stop(self):
        """
        Stop the GUI manager and viewer.

        Stops the viewer server and waits for the thread to complete.
        """
        logger.info("Stopping GUI manager")
        try:
            if self._viewer:
                self._viewer.stop_server()
            if self._server_thread:
                self._server_thread.join()
        except Exception as e:
            logger.error(f"Error stopping GUI manager: {str(e)}")
            logger.debug(traceback.format_exc())
