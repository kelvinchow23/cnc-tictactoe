"""CNC Tic-Tac-Toe — physical tic-tac-toe using a CNC gantry.

Deck layout:
    Slot 1 (front-left):  Storage rack — O pieces (cols 1-2), X pieces (cols 4-5)
    Slot 2 (front-right): Game board — 3x3 grid (cols 2-4, rows A-C)
    Slot 3 (back-left):   Empty
    Slot 4 (back-right):  Empty

Pieces are picked from storage via vacuum gripper and placed on the board.
Supports 1-player (Easy / Medium / Hard AI) and 2-player modes.
"""

import sys
import time
from pathlib import Path

import yaml
from cnc_machine_core import CNC_Machine, Deck, DeckState

sys.path.insert(0, str(Path(__file__).resolve().parent))

from game_logic import (
    BOARD_WELL_MAP,
    STORAGE_WELLS,
    AI_LEVELS,
    new_board,
    get_empty_cells,
    check_winner,
    is_draw,
    display_board,
    parse_input,
    board_label,
)

# ── Hardware ────────────────────────────────────────────────────────────
COM_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
VIRTUAL = True  # Set False for real hardware

# ── Z Heights (calibrate for your hardware) ─────────────────────────────
Z_PICK_STORAGE = -20.0   # Z to descend when picking from storage
Z_PLACE_BOARD = -18.0    # Z to descend when placing on board

# ── Vacuum Gripper ──────────────────────────────────────────────────────
VACUUM_RPM = 1000
GRIPPER_OFFSET = {"x": 7.846, "y": 0.0, "z": 0.0}

# ── Labware ─────────────────────────────────────────────────────────────
LABWARE_DIR = Path(__file__).resolve().parent / "labware"
STORAGE_LABWARE = LABWARE_DIR / "storage_15_tuberack_100ul.json"
GAMEBOARD_LABWARE = LABWARE_DIR / "gameboard_15_tuberack_100ul.json"

# ── Slots ───────────────────────────────────────────────────────────────
STORAGE_SLOT = "1"
BOARD_SLOT = "2"

# ── Preset ──────────────────────────────────────────────────────────────
PRESET_PATH = Path(__file__).resolve().parent / "presets" / "ttt_preset.yaml"

# ── Motion ──────────────────────────────────────────────────────────────
MOVE_SPEED = 2500


# ── CNC Helpers ─────────────────────────────────────────────────────────

def vacuum_on(cnc, rpm=None):
    cnc.follow_gcode_path(f"M3 S{rpm or VACUUM_RPM}\n")


def vacuum_off(cnc):
    cnc.follow_gcode_path("M5\n")


def get_well_xy(deck, slot, well_name):
    """Absolute XY with gripper offset for a well. Z from labware is ignored."""
    labware = deck.get_labware(slot)
    x, y, _ = labware[well_name].position(offset=GRIPPER_OFFSET)
    return x, y


def pick_and_place(cnc, deck, storage_well, board_well):
    """Pick a piece from storage and place on the game board."""
    sx, sy = get_well_xy(deck, STORAGE_SLOT, storage_well)
    bx, by = get_well_xy(deck, BOARD_SLOT, board_well)

    cnc.move_to_point_safe(sx, sy, Z_PICK_STORAGE, speed=MOVE_SPEED)
    vacuum_on(cnc)
    time.sleep(0.3)

    cnc.move_to_point_safe(bx, by, Z_PLACE_BOARD, speed=MOVE_SPEED)
    vacuum_off(cnc)
    time.sleep(0.3)


def return_piece(cnc, deck, board_well, storage_well):
    """Pick a piece from the board and return it to storage."""
    bx, by = get_well_xy(deck, BOARD_SLOT, board_well)
    sx, sy = get_well_xy(deck, STORAGE_SLOT, storage_well)

    cnc.move_to_point_safe(bx, by, Z_PLACE_BOARD, speed=MOVE_SPEED)
    vacuum_on(cnc)
    time.sleep(0.3)

    cnc.move_to_point_safe(sx, sy, Z_PICK_STORAGE, speed=MOVE_SPEED)
    vacuum_off(cnc)
    time.sleep(0.3)


# ── Game Helpers ────────────────────────────────────────────────────────

def load_preset():
    with open(PRESET_PATH) as f:
        preset = yaml.safe_load(f)
    state = DeckState()
    state.init_from_preset(preset)
    return state


def get_next_storage_well(state, piece):
    for well in STORAGE_WELLS[piece]:
        if state.get_status(STORAGE_SLOT, well) == f"{piece}_piece":
            return well
    return None


def reset_board(cnc, deck, state, board, move_history):
    if not move_history:
        return
    print("\nResetting board...")
    for piece, storage_well, board_well in reversed(move_history):
        print(f"  {piece}: board {board_well} -> storage {storage_well}")
        if not VIRTUAL:
            return_piece(cnc, deck, board_well, storage_well)
        state.set_status(BOARD_SLOT, board_well, "empty")
        state.set_status(STORAGE_SLOT, storage_well, f"{piece}_piece")
    for r in range(3):
        for c in range(3):
            board[r][c] = None
    move_history.clear()
    print("Done.\n")


# ── UI ──────────────────────────────────────────────────────────────────

def select_mode():
    print("\n==============================")
    print("      CNC  TIC-TAC-TOE       ")
    print("==============================")
    print("\nGame Mode:")
    print("  1) 1 Player (vs AI)")
    print("  2) 2 Players")
    while True:
        choice = input("\nSelect (1/2): ").strip()
        if choice in ("1", "2"):
            break
        print("Invalid.")

    num_players = int(choice)
    human_symbol = None
    ai_difficulty = None

    if num_players == 1:
        print("\nYour symbol:")
        print("  X (goes first)")
        print("  O (goes second)")
        while True:
            sym = input("Choose (X/O): ").strip().upper()
            if sym in ("X", "O"):
                human_symbol = sym
                break
            print("Invalid.")

        print("\nDifficulty:")
        print("  1) Easy   - random moves")
        print("  2) Medium - blocks + random")
        print("  3) Hard   - unbeatable")
        while True:
            d = input("Choose (1/2/3): ").strip()
            if d in ("1", "2", "3"):
                ai_difficulty = ["easy", "medium", "hard"][int(d) - 1]
                break
            print("Invalid.")

    return num_players, human_symbol, ai_difficulty


def play_game(cnc, deck):
    """Run one game. Returns True to play again, False to quit."""
    num_players, human_symbol, ai_difficulty = select_mode()

    state = load_preset()
    board = new_board()
    move_history = []
    current = "X"

    if num_players == 1:
        ai_symbol = "O" if human_symbol == "X" else "X"
        ai_fn = AI_LEVELS[ai_difficulty]
        print(f"\nYou: {human_symbol}  |  AI: {ai_symbol} ({ai_difficulty})")
    else:
        ai_symbol = None
        ai_fn = None
        print("\nPlayer 1: X  |  Player 2: O")

    print("Moves: A1-C3 | 'reset' | 'quit'\n")

    while True:
        display_board(board)

        winner = check_winner(board)
        if winner:
            if num_players == 1:
                msg = "You win!" if winner == human_symbol else "AI wins!"
            else:
                msg = f"Player {'1' if winner == 'X' else '2'} ({winner}) wins!"
            print(msg)
            break

        if is_draw(board):
            print("Draw!")
            break

        is_ai_turn = num_players == 1 and current == ai_symbol

        if is_ai_turn:
            print(f"AI ({current}) thinking...")
            row, col = ai_fn(board, current)
            print(f"AI plays: {board_label(row, col)}")
        else:
            if num_players == 1:
                prompt = f"Your move ({current}): "
            else:
                prompt = f"Player {'1' if current == 'X' else '2'} ({current}): "

            while True:
                text = input(prompt).strip()
                if text.lower() == "quit":
                    reset_board(cnc, deck, state, board, move_history)
                    return False
                if text.lower() == "reset":
                    reset_board(cnc, deck, state, board, move_history)
                    return True
                pos = parse_input(text)
                if pos is None:
                    print("Invalid. Use A1-C3.")
                    continue
                row, col = pos
                if board[row][col] is not None:
                    print("Occupied. Try again.")
                    continue
                break

        storage_well = get_next_storage_well(state, current)
        if storage_well is None:
            print(f"No {current} pieces left in storage!")
            break

        board_well = BOARD_WELL_MAP[(row, col)]

        if not VIRTUAL:
            pick_and_place(cnc, deck, storage_well, board_well)
        else:
            print(f"  [VIRTUAL] {current}: storage {storage_well} -> board {board_well}")

        board[row][col] = current
        state.set_status(STORAGE_SLOT, storage_well, "empty")
        state.set_status(BOARD_SLOT, board_well, current)
        move_history.append((current, storage_well, board_well))

        current = "O" if current == "X" else "X"

    # Post-game
    while True:
        choice = input("\n(p)lay again / (q)uit: ").strip().lower()
        if choice in ("p", "play"):
            reset_board(cnc, deck, state, board, move_history)
            return True
        if choice in ("q", "quit"):
            reset_board(cnc, deck, state, board, move_history)
            return False
        print("Invalid.")


# ── Main ────────────────────────────────────────────────────────────────

def main():
    cnc = CNC_Machine(COM_PORT, baud_rate=BAUD_RATE, virtual=VIRTUAL)
    cnc.connect()
    cnc.wake_up()
    if not VIRTUAL:
        cnc.home()

    deck = Deck()
    deck.load_labware(STORAGE_SLOT, str(STORAGE_LABWARE))
    deck.load_labware(BOARD_SLOT, str(GAMEBOARD_LABWARE))

    try:
        playing = True
        while playing:
            playing = play_game(cnc, deck)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if not VIRTUAL:
            cnc.move_to_point_safe(0, 0, 0, speed=MOVE_SPEED)
        cnc.close()


main()
