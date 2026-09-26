"""Pump setpoint and ramp handling."""

from __future__ import annotations

import math

from tankfarm.errors import NegativeSetpointError
from tankfarm.pump.arbiter import HeaderArbiter
from tankfarm.pump.model import Pump

RAMP_STEP = 5.0


class SetpointController:
    """Applies setpoints directly or ramps in fixed steps towards a target."""

    def __init__(self, arbiter: HeaderArbiter, step: float = RAMP_STEP) -> None:
        if step <= 0:
            raise ValueError("ramp step must be positive")
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
        target = float(target)
        current = float(pump.setpoint)
        if target == current:
            return ()
        applied: list[float] = []
        step = self._step if target > current else -self._step
        value = current
        remaining = abs(target - current)
        while remaining > self._step + 1e-9:
            value += step
            applied.append(self.apply(pump, value))
            remaining = abs(target - value)
        if not math.isclose(value, target, abs_tol=1e-9):
            applied.append(self.apply(pump, target))
        return tuple(applied)
