import dataclasses
import collections.abc
from importlib.metadata import version

from unitelabs.cdk import Connector, ConnectorBaseConfig, SiLAServerConfig

from .io.cnc_ttt_protocol import CncTttProtocol

__version__ = version("unitelabs-cnc-ttt")


@dataclasses.dataclass
class CncTttConfig(ConnectorBaseConfig):
    """Configuration for the tic-tac-toe."""

    sila_server: SiLAServerConfig = dataclasses.field(
        default_factory=lambda: SiLAServerConfig(
            name="tic-tac-toe",
            type="Example",
            description=(
                """
                A connector for the tic-tac-toe built with the UniteLabs CDK.
                """
            ),
            version=str(__version__),
            vendor_url="https://unitelabs.io/",
        )
    )


async def create_app(config: CncTttConfig) -> collections.abc.AsyncGenerator[Connector, None]:
    """Create the connector application."""
    app = Connector(config)

    protocol = CncTttProtocol()
    await protocol.open()

    yield app

    protocol.close()
