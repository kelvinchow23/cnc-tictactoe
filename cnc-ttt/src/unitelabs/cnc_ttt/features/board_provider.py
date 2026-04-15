"""BoardProvider feature — read-only board state and game information."""

import dataclasses

import typing_extensions as typing

from unitelabs.cdk import sila

from ..io.enums import DIFFICULTIES, GAME_MODES, GAME_STATUSES, PLAYER_SYMBOLS
from ..io.game_engine import GameEngine


@dataclasses.dataclass
class BoardCell(sila.CustomDataType):
    """A single cell on the tic-tac-toe board.

    Attributes:
      Position: The cell label (e.g. A1, B2, C3).
      Value: The piece occupying the cell, or Empty if unoccupied.
    """

    position: str
    value: typing.Annotated[str, sila.constraints.Set(values=["X", "O", "Empty"])]


class BoardProvider(sila.Feature):
    """Provide read-only access to tic-tac-toe game state.

    Exposes the current board layout, player turn, move history,
    and game configuration as SiLA properties.
    """

    def __init__(self, engine: GameEngine):
        super().__init__(
            originator="io.unitelabs",
            category="games",
            version="1.0",
            maturity_level="Draft",
        )
        self._engine = engine

    @sila.UnobservableProperty()
    async def board_state(self) -> list[BoardCell]:
        """Get the current state of all nine board cells.

        Returns cells in row-major order (A1, A2, A3, B1, ..., C3).
        """
        board = self._engine.board_state
        cells = []
        for r, letter in enumerate("ABC"):
            for c in range(3):
                label = f"{letter}{c + 1}"
                value = board[r][c] if board[r][c] is not None else "Empty"
                cells.append(BoardCell(position=label, value=value))
        return cells

    @sila.UnobservableProperty()
    async def board_display(self) -> str:
        """Get the board as a formatted text display."""
        return self._engine.board_as_string()

    @sila.UnobservableProperty()
    async def current_player(self) -> typing.Annotated[str, sila.constraints.Set(values=PLAYER_SYMBOLS)]:
        """Get the symbol of the player whose turn it is."""
        return self._engine.current_player

    @sila.UnobservableProperty()
    async def move_history(self) -> list[str]:
        """Get the list of moves made so far, in chronological order.

        Each entry describes a piece placement, e.g. 'O: A1 -> B2'.
        """
        return self._engine.move_history

    @sila.UnobservableProperty()
    async def game_mode(self) -> typing.Annotated[str, sila.constraints.Set(values=GAME_MODES)]:
        """Get the current game mode."""
        return self._engine.game_mode

    @sila.UnobservableProperty()
    async def difficulty(self) -> typing.Annotated[str, sila.constraints.Set(values=DIFFICULTIES)]:
        """Get the current AI difficulty level."""
        return self._engine.difficulty
