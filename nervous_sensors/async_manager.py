import asyncio
import logging
import traceback
from abc import ABC, abstractmethod

logger = logging.getLogger("nervous")


class AsyncManager(ABC):
    """
    Abstract base class for asynchronous managers.

    This class provides a foundation for implementing asynchronous operations with
    start and stop capabilities, including a stop event for signaling termination.
    """

    def __init__(self):
        """
        Initialize the AsyncManager with a stop event.
        """
        self._stop_event = asyncio.Event()
        logger.debug(f"Initialized AsyncManager: {self.__class__.__name__}")

    @abstractmethod
    async def start(self):
        """
        Start the asynchronous operations.

        This method should be implemented by subclasses to initialize and start
        their specific asynchronous operations.
        """
        logger.warning(f"Using base start method in {self.__class__.__name__}")
        pass

    @abstractmethod
    async def stop(self):
        """
        Stop the asynchronous operations.

        This method should be implemented by subclasses to properly terminate
        their specific asynchronous operations.
        """
        try:
            logger.info(f"Stopping {self.__class__.__name__}")
            self._stop_event.set()
        except Exception as e:
            logger.error(f"Error stopping {self.__class__.__name__}: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise
