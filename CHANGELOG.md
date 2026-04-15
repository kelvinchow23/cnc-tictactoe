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
