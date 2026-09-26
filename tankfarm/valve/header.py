"""Discharge header setpoint device."""

from __future__ import annotations

from collections import deque

from tankfarm.clock import LogicalClock
from tankfarm.errors import NegativeSetpointError
from tankfarm.event import Event, EventBus
from tankfarm.event import topics
from tankfarm.journal.writer import JournalWriter

HISTORY_LIMIT = 8


class Header:
    """Single setpoint shared by every transfer pump."""

    def __init__(
        self,
        header_id: str,
        journal: JournalWriter,
        bus: EventBus,
        clock: LogicalClock,
        history_limit: int = HISTORY_LIMIT,
    ) -> None:
        self._header_id = header_id
        self._journal = journal
        self._bus = bus
        self._clock = clock
        self._setpoint = 0.0
        self._history: deque[tuple[int, float]] = deque(maxlen=history_limit)

    @property
    def header_id(self) -> str:
        return self._header_id

    def setpoint(self) -> float:
        return self._setpoint

    def history(self) -> tuple[tuple[int, float], ...]:
        return tuple(self._history)

    def write(self, value: float, pump_id: str = "") -> float:
        if value < 0:
            raise NegativeSetpointError(value)
        self._setpoint = float(value)
        now = self._clock.tick()
        self._record(now)
        payload = {"setpoint": self._setpoint}
        if pump_id:
            payload["pump_id"] = pump_id
        self._journal.append(topics.HEADER_SETPOINT, payload)
        self._bus.publish(
            Event(
                topic=topics.HEADER_SETPOINT,
                value=dict(payload),
                ts=now,
            )
        )
        return self._setpoint

    def replay_write(self, value: float, ts: int) -> None:
        """Re-enters a setpoint recovered from the journal without appending."""

        self._setpoint = float(value)
        self._record(ts)

    def restore(self, value: float) -> None:
        self._setpoint = float(value)
        self._history.clear()

    def _record(self, ts: int) -> None:
        self._history.append((int(ts), self._setpoint))
