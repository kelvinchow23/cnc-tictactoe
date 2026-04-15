# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.0 - 2026-04-14

### Added
- SiLA 2 server integration via UniteLabs CDK v0.9.0
- GameController feature: StartGame (configurable mode/difficulty), ResetBoard (observable), GameStatus
- BoardProvider feature: BoardState, BoardDisplay, CurrentPlayer, MoveHistory, GameMode, Difficulty
- MoveController feature: MakeMove (observable, auto-triggers AI response in single-player)
- IO layer: GameEngine (wraps CNC_Machine + game_logic), SimulationEngine (virtual mode)
- Defined execution errors with recovery suggestions: GameNotInProgress, GameAlreadyInProgress, InvalidMove, NoPiecesRemaining, CncConnectionFailed, CncMotionFailed
- Set constraints on enum-like parameters (game mode, difficulty, player symbol, board positions)
- CncTttConfig with com_port, baud_rate, and virtual fields
