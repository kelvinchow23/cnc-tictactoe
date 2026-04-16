"""HardwareSettings feature — read and adjust CNC motion parameters."""

import dataclasses

from unitelabs.cdk import sila

from ..io.game_engine import GameEngine


@dataclasses.dataclass
class GripperOffset(sila.CustomDataType):
    """XYZ offset applied to the vacuum gripper."""

    x: float
    y: float
    z: float


class HardwareSettings(sila.Feature):
    """Read and adjust CNC hardware parameters at runtime."""

    def __init__(self, engine: GameEngine):
        super().__init__(
            originator="io.unitelabs",
            category="games",
            version="1.0",
            maturity_level="Draft",
        )
        self._engine = engine

    # ── Properties ───────────────────────────────────────────────────────

    @sila.UnobservableProperty()
    async def z_pick_height(self) -> float:
        return self._engine.z_pick

    @sila.UnobservableProperty()
    async def z_place_height(self) -> float:
        return self._engine.z_place

    @sila.UnobservableProperty()
    async def vacuum_rpm(self) -> int:
        return self._engine.vacuum_rpm

    @sila.UnobservableProperty()
    async def move_speed(self) -> int:
        return self._engine.move_speed

    @sila.UnobservableProperty()
    async def grip_delay(self) -> float:
        return self._engine.grip_delay

    @sila.UnobservableProperty()
    async def place_delay(self) -> float:
        return self._engine.place_delay

    @sila.UnobservableProperty()
    async def gripper_offset(self) -> GripperOffset:
        o = self._engine.gripper_offset
        return GripperOffset(x=o["x"], y=o["y"], z=o["z"])

    # ── Commands ─────────────────────────────────────────────────────────

    @sila.UnobservableCommand()
    async def set_z_pick_height(self, value: float) -> str:
        self._engine.z_pick = value
        return f"Z pick height set to {value}"

    @sila.UnobservableCommand()
    async def set_z_place_height(self, value: float) -> str:
        self._engine.z_place = value
        return f"Z place height set to {value}"

    @sila.UnobservableCommand()
    async def set_vacuum_rpm(self, value: int) -> str:
        self._engine.vacuum_rpm = value
        return f"Vacuum RPM set to {value}"

    @sila.UnobservableCommand()
    async def set_move_speed(self, value: int) -> str:
        self._engine.move_speed = value
        return f"Move speed set to {value}"

    @sila.UnobservableCommand()
    async def set_grip_delay(self, value: float) -> str:
        self._engine.grip_delay = value
        return f"Grip delay set to {value}s"

    @sila.UnobservableCommand()
    async def set_place_delay(self, value: float) -> str:
        self._engine.place_delay = value
        return f"Place delay set to {value}s"

    @sila.UnobservableCommand()
    async def set_gripper_offset(self, x: float, y: float, z: float) -> str:
        self._engine.gripper_offset = {"x": x, "y": y, "z": z}
        return f"Gripper offset set to x={x}, y={y}, z={z}"
