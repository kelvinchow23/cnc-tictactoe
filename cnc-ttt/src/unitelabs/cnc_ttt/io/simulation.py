"""Simulation backend for CNC Tic-Tac-Toe (virtual mode)."""

from .game_engine import GameEngine


class SimulationEngine(GameEngine):
    """GameEngine running in virtual mode (no real CNC hardware)."""

    def __init__(self, com_port: str = "/dev/ttyUSB0", baud_rate: int = 115200):
        super().__init__(com_port=com_port, baud_rate=baud_rate, virtual=True)
