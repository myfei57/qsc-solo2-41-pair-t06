"""Pump setpoint and ramp handling."""

from __future__ import annotations

from tankfarm.errors import NegativeSetpointError
from tankfarm.pump.arbiter import HeaderArbiter
from tankfarm.pump.model import Pump

RAMP_STEP = 5.0


class SetpointController:
    """Applies setpoints directly or walks to the target in fixed steps."""

    def __init__(self, arbiter: HeaderArbiter, step: float = RAMP_STEP) -> None:
        self._arbiter = arbiter
        self._step = float(step)

    def apply(self, pump: Pump, value: float) -> float:
        if value < 0:
            raise NegativeSetpointError(value)
        pump.setpoint = float(value)
        return self._arbiter.write(pump.pump_id, value)

    def ramp(self, pump: Pump, target: float) -> tuple[float, ...]:
        if target < 0:
            raise NegativeSetpointError(target)
        if target == pump.setpoint:
            return ()
        direction = 1.0 if target > pump.setpoint else -1.0
        steps: list[float] = []
        current = pump.setpoint
        while current != target:
            nxt = current + direction * self._step
            nxt = min(nxt, target) if direction > 0 else max(nxt, target)
            steps.append(self.apply(pump, nxt))
            current = nxt
        return tuple(steps)
