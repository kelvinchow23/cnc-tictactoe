import dataclasses
import collections.abc
from importlib.metadata import version

from unitelabs.cdk import Connector, ConnectorBaseConfig, SiLAServerConfig

from .features import BoardProvider, GameController, HardwareSettings, MoveController
from .io import GameEngine, SimulationEngine

__version__ = version("unitelabs-cnc-ttt")


@dataclasses.dataclass
class CncTttConfig(ConnectorBaseConfig):
    """Configuration for the tic-tac-toe."""

    sila_server: SiLAServerConfig = dataclasses.field(
        default_factory=lambda: SiLAServerConfig(
            name="tic-tac-toe",
            type="CNC Games",
            description=(
                """
                A CNC-powered tic-tac-toe game server. Plays tic-tac-toe
                on a physical board using a CNC gantry with vacuum gripper
                to pick and place pieces. Supports single-player (vs AI)
                and two-player modes.
                """
            ),
            version=str(__version__),
            vendor_url="https://github.com/kelvinchow23/cnc-tictactoe",
        )
    )

    com_port: str = "/dev/ttyUSB0"
    baud_rate: int = 115200
    virtual: bool = False


async def create_app(
    config: CncTttConfig,
) -> collections.abc.AsyncGenerator[Connector, None]:
    """Create the connector application."""
    app = Connector(config)

    if config.virtual:
        engine = SimulationEngine(com_port=config.com_port, baud_rate=config.baud_rate)
    else:
        engine = GameEngine(com_port=config.com_port, baud_rate=config.baud_rate)

    await engine.open()

    app.register(GameController(engine))
    app.register(BoardProvider(engine))
    app.register(MoveController(engine))
    app.register(HardwareSettings(engine))

    yield app

    engine.close()
