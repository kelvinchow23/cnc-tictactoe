"""Defined execution errors for CNC Tic-Tac-Toe."""


class GameNotInProgress(Exception):
    """No game is currently in progress. Start a new game first using the StartGame command."""


class GameAlreadyInProgress(Exception):
    """A game is already in progress. Reset the board first before starting a new game."""


class InvalidMove(Exception):
    """The requested board position is invalid or already occupied. Valid positions are A1 through C3."""


class NoPiecesRemaining(Exception):
    """No pieces of the required type remain in storage. Reset the board to return pieces."""


class CncConnectionFailed(Exception):
    """Failed to connect to the CNC machine. Check that the serial port is correct and the machine is powered on."""


class CncMotionFailed(Exception):
    """The CNC gantry failed during a pick-and-place operation. Check for mechanical obstructions."""
