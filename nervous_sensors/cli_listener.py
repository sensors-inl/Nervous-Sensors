import io

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
    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.content = io.StringIO()

    def write(self, message):
        if not any(word in message for word in blacklist):
            self.original_stream.write(message)
        self.content.write(message)

    def flush(self):
        self.original_stream.flush()
        self.content.flush()

    def get_content(self):
        return self.content.getvalue()
