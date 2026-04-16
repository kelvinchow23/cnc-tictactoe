"""GameController feature — start games and reset the board."""

import typing_extensions as typing

from unitelabs.cdk import sila

from ..io.enums import DIFFICULTIES, GAME_MODES, GAME_STATUSES, PLAYER_SYMBOLS
from ..io.errors import GameAlreadyInProgress, GameNotInProgress
from ..io.game_engine import GameEngine


class GameController(sila.Feature):
    """Manage tic-tac-toe game lifecycle.

    Provides commands to start a new game with configurable mode
    and difficulty, and to reset the board by returning all pieces
    to storage via the CNC gantry.
    """

    def __init__(self, engine: GameEngine):
        super().__init__(
            originator="io.unitelabs",
            category="games",
            version="1.0",
            maturity_level="Draft",
        )
        self._engine = engine

    @sila.UnobservableCommand()
    async def start_game(
        self,
        mode: typing.Annotated[str, sila.constraints.Set(values=GAME_MODES)],
        difficulty: typing.Annotated[
            str, sila.constraints.Set(values=DIFFICULTIES)
        ] = "Easy",
        human_symbol: typing.Annotated[
            str, sila.constraints.Set(values=PLAYER_SYMBOLS)
        ] = "X",
    ) -> str:
        """Start a new tic-tac-toe game.

        Initializes the board and sets up game parameters. O always goes first.

        Args:
          Mode: The game mode. SinglePlayer plays against the AI,
            TwoPlayer is for two human players.
          Difficulty: The AI difficulty level, only used in SinglePlayer
            mode. Easy picks random moves, Medium blocks and plays
            randomly, Hard uses minimax (unbeatable).
          HumanSymbol: The symbol for the human player in SinglePlayer
            mode. The AI gets the other symbol.

        Returns:
          Confirmation: A confirmation message describing the game setup.

        Raises:
          GameAlreadyInProgress: A game is already in progress.
            Reset the board first before starting a new game.
        """
        self._engine.start_game(
            mode=mode, difficulty=difficulty, human_symbol=human_symbol
        )
        if mode == "SinglePlayer":
            msg = f"Game started: You are {human_symbol}, AI is {difficulty}. O goes first."
            if self._engine.is_ai_turn():
                ai_result = self._engine.make_ai_move()
                msg += f"\n{ai_result}"
            return msg
        return "Game started: Two player mode. O goes first."

    @sila.UnobservableCommand()
    async def reset_board(self) -> str:
        """Reset the board by returning all pieces to storage via the CNC gantry.

        Returns:
          Confirmation: A confirmation message after the board is reset.

        Raises:
          CncMotionFailed: The CNC gantry failed during piece return.
            Check for mechanical obstructions.
        """
        self._engine.reset_board()
        return "Board reset. All pieces returned to storage."

    @sila.UnobservableProperty()
    async def game_status(
        self,
    ) -> typing.Annotated[str, sila.constraints.Set(values=GAME_STATUSES)]:
        """Get the current game status."""
        return self._engine.game_status
