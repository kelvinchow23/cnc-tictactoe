from unitelabs.bus import Protocol, create_serial_connection


class CncTttProtocol(Protocol):
    """Underlying communication protocol for tic-tac-toe."""

    def __init__(self, **kwargs):
        kwargs["port"] = "/dev/ttyUSB0"  # FIXME: set device port
        super().__init__(create_serial_connection, **kwargs)
