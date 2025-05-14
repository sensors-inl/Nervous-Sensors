import io
import logging

logger = logging.getLogger("nervous")

# List of strings to filter from output
blacklist = [
    "Flask",
    "Dash is running",
    "* Debug mode",
    "Address already",
    "Port",
    "is in use by another program",
    "netinterfaces",
    "udp_server",
    "netif",
    "multicast",
]


class CLIListener:
    """
    A custom stream listener that filters certain messages from the output stream.

    This class is used to intercept stdout/stderr and filter out unwanted messages
    while still capturing all output content.
    """

    def __init__(self, original_stream):
        """
        Initialize the CLI listener with an original stream to wrap.

        Args:
            original_stream: The original output stream (e.g. sys.stdout).
        """
        self.original_stream = original_stream
        self.content = io.StringIO()
        logger.debug(f"Initialized CLIListener for stream: {original_stream}")

    def write(self, message):
        """
        Write a message to the stream, filtering out blacklisted content.

        Args:
            message (str): The message to write.
        """
        # Check if message contains any blacklisted terms
        if not any(word in message for word in blacklist):
            self.original_stream.write(message)
        else:
            logger.debug(f"Filtered message containing blacklisted content: {message[:50]}...")

        # Always write to internal content buffer
        self.content.write(message)

    def flush(self):
        """
        Flush both the original stream and the internal content buffer.
        """
        self.original_stream.flush()
        self.content.flush()

    def get_content(self):
        """
        Get the complete content captured by this listener.

        Returns:
            str: The full content written to this stream.
        """
        return self.content.getvalue()
