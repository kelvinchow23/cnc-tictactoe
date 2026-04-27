"""Web client for CNC Tic-Tac-Toe.

Connects to the SiLA 2 game server via the sila2 client library.
All game state lives on the server; this app is a thin proxy.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sila2.client import SilaClient

SILA_HOST = os.getenv("SILA_HOST", "sdl99-vial-capper.tail6a1dd7.ts.net")
SILA_PORT = int(os.getenv("SILA_PORT", "50052"))

_client: SilaClient | None = None

POS_MAP = {
    "A1": (0, 0), "A2": (0, 1), "A3": (0, 2),
    "B1": (1, 0), "B2": (1, 1), "B3": (1, 2),
    "C1": (2, 0), "C2": (2, 1), "C3": (2, 2),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    _client = SilaClient(SILA_HOST, SILA_PORT, insecure=True)
    yield
    _client.close()
    _client = None


app = FastAPI(title="CNC Tic-Tac-Toe", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


class StartGameRequest(BaseModel):
    mode: str = "SinglePlayer"
    difficulty: str = "Easy"
    human_symbol: str = "X"


class MoveRequest(BaseModel):
    position: str


def _board_from_cells(cells) -> list[list[str | None]]:
    board = [[None, None, None] for _ in range(3)]
    for cell in cells:
        r, c = POS_MAP[cell.Position]
        board[r][c] = None if cell.Value == "Empty" else cell.Value
    return board


def _state() -> dict:
    bp = _client.BoardProvider
    gc = _client.GameController

    game_status = gc.GameStatus.get()
    current_player = bp.CurrentPlayer.get()
    game_mode = bp.GameMode.get()
    difficulty = bp.Difficulty.get()

    try:
        human_symbol = bp.HumanSymbol.get()
    except AttributeError:
        human_symbol = "X"

    is_ai_turn = (
        game_status == "InProgress"
        and game_mode == "SinglePlayer"
        and current_player != human_symbol
    )

    return {
        "board": _board_from_cells(bp.BoardState.get()),
        "board_display": bp.BoardDisplay.get(),
        "current_player": current_player,
        "game_status": game_status,
        "game_mode": game_mode,
        "difficulty": difficulty,
        "move_history": list(bp.MoveHistory.get()),
        "is_ai_turn": is_ai_turn,
    }


# ── Endpoints ────────────────────────────────────────────────────

@app.get("/api/state")
def get_state():
    return _state()


@app.post("/api/start")
def start_game(req: StartGameRequest):
    if _client.GameController.GameStatus.get() == "InProgress":
        _client.GameController.ResetBoard()

    resp = _client.GameController.StartGame(
        Mode=req.mode,
        Difficulty=req.difficulty,
        HumanSymbol=req.human_symbol,
    )
    return {"message": resp.Confirmation, "state": _state()}


@app.post("/api/move")
def make_move(req: MoveRequest):
    resp = _client.MoveController.MakeMove(Position=req.position.upper())
    return {"message": resp.Result, "ai_message": None, "state": _state()}


@app.post("/api/reset")
def reset_board():
    resp = _client.GameController.ResetBoard()
    return {"message": resp.Confirmation, "state": _state()}
