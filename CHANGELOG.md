## 0.4.0 - 2026-04-16
- Web client now connects to the SiLA 2 server via sila2 client library (gRPC)
- All game state lives on the server; web app is a thin proxy
- Supports SILA_HOST and SILA_PORT environment variables for server address
- Optimistic UI: piece appears immediately on click, polls server for live updates
- Polling during StartGame, MakeMove, and ResetBoard for real-time board sync
- Fixed CSS layout from 3-column to 2-column grid

## 0.3.0 - 2026-04-16
- Web client GUI for playing tic-tac-toe in the browser
- FastAPI REST backend wrapping GameEngine (simulation mode by default)
- YouTube / live stream embed panel for watching the CNC machine
- Endpoints: GET /api/state, POST /api/start, POST /api/move, POST /api/reset
- Dark theme responsive layout (game board + stream side by side)

## 0.2.0 - 2026-04-14
- SiLA 2 server integration via UniteLabs CDK (cnc-ttt/ subfolder)
- 3 SiLA features: GameController, BoardProvider, MoveController
- IO layer: GameEngine + SimulationEngine wrapping CNC_Machine and game_logic
- Defined execution errors with recovery suggestions

## 0.1.0 - 2026-04-14
- Initial implementation of CNC Tic-Tac-Toe game
- 1-player mode (vs AI) with Easy, Medium, and Hard difficulty
- 2-player mode (local, shared terminal)
- Terminal GUI board display with A1-C3 input
- CNC pick-and-place via vacuum gripper: storage (slot 1) to gameboard (slot 2)
- Board reset returns all pieces to original storage positions
- Virtual mode for testing without hardware
- Deck state tracking via DeckState preset (presets/ttt_preset.yaml)
