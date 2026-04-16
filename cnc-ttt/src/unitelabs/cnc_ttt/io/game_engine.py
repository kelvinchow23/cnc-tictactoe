"""Game engine wrapping CNC hardware and game logic for SiLA integration."""

import time
from pathlib import Path

import yaml
from cnc_machine_core import CNC_Machine, Deck, DeckState

from .enums import GAME_STATUSES
from .errors import (
    CncConnectionFailed,
    CncMotionFailed,
    GameAlreadyInProgress,
    GameNotInProgress,
    InvalidMove,
    NoPiecesRemaining,
)

# Import game logic from the repo root
import sys

_REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_REPO_ROOT))

from game_logic import (
    AI_LEVELS,
    BOARD_WELL_MAP,
    STORAGE_WELLS,
    WELL_TO_BOARD,
    board_label,
    check_winner,
    get_empty_cells,
    is_draw,
    new_board,
    parse_input,
)

# Hardware defaults
Z_PICK = -21.2
Z_PLACE = -19
VACUUM_RPM = 2500
GRIPPER_OFFSET = {"x": 0.0, "y": 0.0, "z": 0.0}
MOVE_SPEED = 2500
LABWARE_DIR = _REPO_ROOT / "labware"
STORAGE_LABWARE = LABWARE_DIR / "storage_15_tuberack_100ul.json"
GAMEBOARD_LABWARE = LABWARE_DIR / "gameboard_15_tuberack_100ul.json"
PRESET_PATH = _REPO_ROOT / "presets" / "ttt_preset.yaml"
STORAGE_SLOT = "1"
BOARD_SLOT = "2"
GRIP_DELAY = 1.0
PLACE_DELAY = 3.0


class GameEngine:
    """Manages game state and CNC hardware for tic-tac-toe."""

    def __init__(
        self,
        com_port: str = "/dev/ttyUSB0",
        baud_rate: int = 115200,
        virtual: bool = False,
    ):
        self._com_port = com_port
        self._baud_rate = baud_rate
        self._virtual = virtual
        self._cnc: CNC_Machine | None = None
        self._deck: Deck | None = None
        self._state: DeckState | None = None
        self._board: list[list[str | None]] = new_board()
        self._move_history: list[tuple[str, str, str]] = []
        self._current_player: str = "O"
        self._game_status: str = "Idle"
        self._game_mode: str = "SinglePlayer"
        self._difficulty: str = "Easy"
        self._human_symbol: str = "X"
        self._ai_symbol: str = "O"

    async def open(self) -> None:
        """Connect to CNC hardware and load deck."""
        try:
            self._cnc = CNC_Machine(
                self._com_port, baud_rate=self._baud_rate, virtual=self._virtual
            )
            self._cnc.connect()
            self._cnc.wake_up()
            if not self._virtual:
                self._cnc.home()
        except Exception as exc:
            msg = f"Failed to connect to CNC at {self._com_port}: {exc}"
            raise CncConnectionFailed(msg) from exc

        self._deck = Deck()
        self._deck.load_labware(STORAGE_SLOT, str(STORAGE_LABWARE))
        self._deck.load_labware(BOARD_SLOT, str(GAMEBOARD_LABWARE))
        self._state = self._load_preset()

    def close(self) -> None:
        """Disconnect CNC hardware."""
        if self._cnc is not None:
            if not self._virtual:
                self._cnc.move_to_point_safe(0, 0, 0, speed=MOVE_SPEED)
            self._cnc.close()
            self._cnc = None

    def _load_preset(self) -> DeckState:
        with open(PRESET_PATH) as f:
            preset = yaml.safe_load(f)
        state = DeckState()
        state.init_from_preset(preset)
        return state

    def _get_well_xy(self, slot: str, well_name: str) -> tuple[float, float]:
        labware = self._deck.get_labware(slot)
        x, y, _ = labware[well_name].position(offset=GRIPPER_OFFSET)
        return x, y

    def _pick_and_place(self, storage_well: str, board_well: str) -> None:
        sx, sy = self._get_well_xy(STORAGE_SLOT, storage_well)
        bx, by = self._get_well_xy(BOARD_SLOT, board_well)
        try:
            self._cnc.move_to_point_safe(sx, sy, Z_PICK, speed=MOVE_SPEED)
            self._cnc.spindle_on(speed=VACUUM_RPM)
            time.sleep(GRIP_DELAY)
            self._cnc.move_to_point_safe(bx, by, Z_PLACE, speed=MOVE_SPEED)
            self._cnc.spindle_off()
            time.sleep(PLACE_DELAY)
        except Exception as exc:
            msg = f"CNC motion failed during pick-and-place: {exc}"
            raise CncMotionFailed(msg) from exc

    def _return_piece(self, board_well: str, storage_well: str) -> None:
        bx, by = self._get_well_xy(BOARD_SLOT, board_well)
        sx, sy = self._get_well_xy(STORAGE_SLOT, storage_well)
        try:
            self._cnc.move_to_point_safe(bx, by, Z_PICK, speed=MOVE_SPEED)
            self._cnc.spindle_on(speed=VACUUM_RPM)
            time.sleep(GRIP_DELAY)
            self._cnc.move_to_point_safe(sx, sy, Z_PLACE, speed=MOVE_SPEED)
            self._cnc.spindle_off()
            time.sleep(PLACE_DELAY)
        except Exception as exc:
            msg = f"CNC motion failed during return: {exc}"
            raise CncMotionFailed(msg) from exc

    def _get_next_storage_well(self, piece: str) -> str | None:
        for well in STORAGE_WELLS[piece]:
            if self._state.get_status(STORAGE_SLOT, well) == f"{piece}_piece":
                return well
        return None

    # ── Public API ───────────────────────────────────────────────────────

    @property
    def game_status(self) -> str:
        return self._game_status

    @property
    def current_player(self) -> str:
        return self._current_player

    @property
    def game_mode(self) -> str:
        return self._game_mode

    @property
    def difficulty(self) -> str:
        return self._difficulty

    @property
    def board_state(self) -> list[list[str | None]]:
        return [row[:] for row in self._board]

    @property
    def move_history(self) -> list[str]:
        """Return move history as list of strings like 'O: A1 -> B2'."""
        return [f"{piece}: {sw} -> {bw}" for piece, sw, bw in self._move_history]

    def board_as_string(self) -> str:
        """Return the board as a displayable string."""
        sym = {None: "·", "X": "X", "O": "O"}
        lines = []
        lines.append("    1   2   3")
        lines.append("")
        for r, letter in enumerate("ABC"):
            row = "   ".join(sym[self._board[r][c]] for c in range(3))
            lines.append(f"{letter}   {row}")
            if r < 2:
                lines.append("")
        return "\n".join(lines)

    def start_game(
        self, mode: str, difficulty: str = "Easy", human_symbol: str = "X"
    ) -> None:
        """Start a new game."""
        if self._game_status == "InProgress":
            raise GameAlreadyInProgress

        self._board = new_board()
        self._move_history = []
        self._current_player = "O"
        self._game_status = "InProgress"
        self._game_mode = mode
        self._difficulty = difficulty
        self._state = self._load_preset()

        if mode == "SinglePlayer":
            self._human_symbol = human_symbol
            self._ai_symbol = "O" if human_symbol == "X" else "X"
        else:
            self._human_symbol = "X"
            self._ai_symbol = None

    def make_move(self, position: str) -> str:
        """Place a piece at the given position (e.g., 'A1').

        Returns a description of the move made.
        """
        if self._game_status != "InProgress":
            raise GameNotInProgress

        pos = parse_input(position)
        if pos is None:
            msg = f"Invalid position '{position}'. Use A1 through C3."
            raise InvalidMove(msg)

        row, col = pos
        if self._board[row][col] is not None:
            msg = f"Position {position.upper()} is already occupied."
            raise InvalidMove(msg)

        return self._execute_move(row, col)

    def make_ai_move(self) -> str:
        """Let the AI make a move. Returns a description of the move made."""
        if self._game_status != "InProgress":
            raise GameNotInProgress
        if self._game_mode != "SinglePlayer":
            msg = "AI moves are only available in single-player mode."
            raise InvalidMove(msg)
        if self._current_player != self._ai_symbol:
            msg = "It is not the AI's turn."
            raise InvalidMove(msg)

        ai_fn = AI_LEVELS[self._difficulty.lower()]
        row, col = ai_fn(self._board, self._current_player)
        return self._execute_move(row, col)

    def _execute_move(self, row: int, col: int) -> str:
        """Execute a move at grid position (row, col). Returns description."""
        piece = self._current_player
        storage_well = self._get_next_storage_well(piece)
        if storage_well is None:
            raise NoPiecesRemaining

        board_well = BOARD_WELL_MAP[(row, col)]

        if not self._virtual:
            self._pick_and_place(storage_well, board_well)

        self._board[row][col] = piece
        self._state.set_status(STORAGE_SLOT, storage_well, "empty")
        self._state.set_status(BOARD_SLOT, board_well, piece)
        self._move_history.append((piece, storage_well, board_well))

        label = board_label(row, col)
        description = f"{piece} placed at {label}"

        winner = check_winner(self._board)
        if winner:
            self._game_status = f"{winner}Wins"
            description += f" — {winner} wins!"
        elif is_draw(self._board):
            self._game_status = "Draw"
            description += " — Draw!"
        else:
            self._current_player = "O" if piece == "X" else "X"

        return description

    def reset_board(self) -> None:
        """Return all pieces to storage and reset the game."""
        if self._move_history:
            for piece, storage_well, board_well in reversed(self._move_history):
                if not self._virtual:
                    self._return_piece(board_well, storage_well)
                self._state.set_status(BOARD_SLOT, board_well, "empty")
                self._state.set_status(STORAGE_SLOT, storage_well, f"{piece}_piece")

        self._board = new_board()
        self._move_history = []
        self._current_player = "O"
        self._game_status = "Idle"

    def is_ai_turn(self) -> bool:
        """Check if it's the AI's turn in single-player mode."""
        return (
            self._game_status == "InProgress"
            and self._game_mode == "SinglePlayer"
            and self._current_player == self._ai_symbol
        )
