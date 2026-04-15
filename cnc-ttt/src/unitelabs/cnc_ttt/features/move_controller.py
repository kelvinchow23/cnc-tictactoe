"""MoveController feature — execute moves on the physical board."""

import typing_extensions as typing

from unitelabs.cdk import sila

from ..io.enums import PLAYER_SYMBOLS
from ..io.errors import CncMotionFailed, GameNotInProgress, InvalidMove, NoPiecesRemaining
from ..io.game_engine import GameEngine


class MoveController(sila.Feature):
    """Execute tic-tac-toe moves on the physical CNC board.

    The MakeMove command is observable because it involves CNC gantry
    motion (picking a piece from storage and placing it on the board).
    In single-player mode, the AI response move is executed automatically.
    """

    def __init__(self, engine: GameEngine):
        super().__init__(
            originator="io.unitelabs",
            category="games",
            version="1.0",
            maturity_level="Draft",
        )
        self._engine = engine

    @sila.ObservableCommand()
    async def make_move(
        self,
        position: typing.Annotated[str, sila.constraints.Set(values=[
            "A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3",
        ])],
        *,
        status: sila.Status,
    ) -> str:
        """Place a piece at the specified board position via the CNC gantry.

        The CNC picks a piece from storage and places it on the board.
        In single-player mode, if the game is not over after the human
        move, the AI automatically makes its response move.

        Args:
          Position: The board position to place the piece (A1 through C3).
            Rows are A-C (top to bottom), columns are 1-3 (left to right).

        Returns:
          Result: A description of the move(s) made.

        Raises:
          GameNotInProgress: No game is currently in progress.
            Start a new game first using the StartGame command.
          InvalidMove: The requested board position is invalid
            or already occupied. Valid positions are A1 through C3.
          NoPiecesRemaining: No pieces of the required type remain
            in storage. Reset the board to return pieces.
          CncMotionFailed: The CNC gantry failed during a pick-and-place
            operation. Check for mechanical obstructions.
        """
        status.update(progress=0.0)

        human_result = self._engine.make_move(position)
        status.update(progress=0.5)

        result = human_result

        if self._engine.is_ai_turn():
            ai_result = self._engine.make_ai_move()
            result += f"\n{ai_result}"

        status.update(progress=1.0)
        return result
