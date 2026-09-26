"""Header setpoint arbitration between pumps."""

from __future__ import annotations

from typing import Any

from tankfarm.errors import NegativeSetpointError
from tankfarm.valve.header import Header


class HeaderArbiter:
    """Keeps the latest demand of every pump and writes through to the header."""

    def __init__(self, header: Header) -> None:
        self._header = header
        self._last_writer = ""
        self._demands: dict[str, float] = {}

    def write(self, pump_id: str, value: float) -> float:
        if value < 0:
            raise NegativeSetpointError(value)
        self._last_writer = pump_id
        self._demands[pump_id] = float(value)
        return self._header.write(value, pump_id)

    def value(self) -> float:
        return self._header.setpoint()

    def last_writer(self) -> str:
        return self._last_writer

    def demands(self) -> dict[str, float]:
        return dict(self._demands)

    def demand_of(self, pump_id: str) -> float:
        return self._demands.get(pump_id, 0.0)

    def restore_demand(self, pump_id: str, value: float) -> None:
        """Re-enters a demand recovered from the journal without writing."""

        self._demands[str(pump_id)] = float(value)
        self._last_writer = str(pump_id)

    def reset(self) -> None:
        self._last_writer = ""
        self._demands.clear()

    def as_payload(self) -> dict[str, Any]:
        return {
            "setpoint": self.value(),
            "last_writer": self.last_writer(),
            "demands": self.demands(),
        }
