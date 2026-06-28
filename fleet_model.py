"""
Fleet Model — Per-unit EV state management with thermal physics,
priority dispatch, and telemetry packet generation.
"""
import random
import json
from dataclasses import dataclass, field


AMBIENT_TEMP = 25.0           # °C — baseline ambient temperature
PASSIVE_COOL_RATE = 0.3       # °C per tick toward ambient
HEAT_COEFFICIENT = 0.05       # Heat generated per (discharge_amount²)
THROTTLE_TEMP = 45.0          # °C — half discharge rate
DISCONNECT_TEMP = 55.0        # °C — emergency disconnect

# Dispatch scoring weights
SCORE_SOC_WEIGHT = 0.6
SCORE_SOH_WEIGHT = 0.3
SCORE_TEMP_WEIGHT = 0.1


@dataclass
class EVUnit:
    """Represents a single EV in the fleet."""
    id: str
    soc: float = 50.0
    soh: float = 100.0
    temperature: float = 25.0
    is_connected: bool = True
    discharge_rate_multiplier: float = 1.0
    # Internal tracking
    _current_flow: float = field(default=0.0, repr=False)
    _status: str = field(default="idle", repr=False)

    @property
    def dispatch_score(self) -> float:
        """Priority dispatch score — higher is better for discharge."""
        if not self.is_connected:
            return -999.0
        return (self.soc * SCORE_SOC_WEIGHT
                + self.soh * SCORE_SOH_WEIGHT
                - self.temperature * SCORE_TEMP_WEIGHT)

    @property
    def voltage(self) -> float:
        """Simulated pack voltage (350-420V range based on SoC)."""
        return 350.0 + (self.soc / 100.0) * 70.0 + random.uniform(-0.5, 0.5)

    @property
    def current(self) -> float:
        """Simulated current — negative for discharge, positive for charge."""
        if self._status == "discharging":
            return -(10.0 + self._current_flow * 2.0) + random.uniform(-0.3, 0.3)
        elif self._status == "charging":
            return (8.0 + self._current_flow * 1.5) + random.uniform(-0.3, 0.3)
        return random.uniform(-0.1, 0.1)

    def telemetry_packet(self) -> dict:
        """Generate a single telemetry JSON packet for this unit."""
        return {
            "unit": self.id,
            "voltage": round(self.voltage, 1),
            "current": round(self.current, 1),
            "temp": round(self.temperature, 1),
            "soc": round(self.soc, 1),
            "soh": round(self.soh, 1),
            "status": self._status if self.is_connected else "disconnected",
        }

    def telemetry_json(self) -> str:
        """Telemetry packet as a compact JSON string."""
        return json.dumps(self.telemetry_packet(), separators=(",", ":"))


class FleetManager:
    """
    Manages a fleet of 4 EVs with independent state.
    Handles thermal physics, throttling, priority dispatch, and telemetry.
    """
    def __init__(self):
        self.units: list[EVUnit] = [
            EVUnit(id="T01", soc=50.0, temperature=24.8),
            EVUnit(id="T02", soc=45.8, temperature=25.2),
            EVUnit(id="T03", soc=53.1, temperature=24.5),
            EVUnit(id="T04", soc=48.5, temperature=25.5),
        ]
        self._leader_id: str | None = None
        self._thermal_events: list[dict] = []  # Consumed by main.py each tick

    # ── Thermal Physics ──────────────────────────────────────────────
    def _apply_thermal(self, unit: EVUnit, energy_amount: float):
        """Update temperature based on energy flow and passive cooling."""
        # Heat from energy flow (squared relationship)
        heat = (energy_amount ** 2) * HEAT_COEFFICIENT
        unit.temperature += heat

        # Passive cooling toward ambient
        if unit.temperature > AMBIENT_TEMP:
            unit.temperature -= PASSIVE_COOL_RATE
            unit.temperature = max(unit.temperature, AMBIENT_TEMP)
        elif unit.temperature < AMBIENT_TEMP:
            unit.temperature += PASSIVE_COOL_RATE * 0.5
            unit.temperature = min(unit.temperature, AMBIENT_TEMP)

        # Thermal throttling
        if unit.temperature > DISCONNECT_TEMP:
            if unit.is_connected:
                unit.is_connected = False
                unit.discharge_rate_multiplier = 0.0
                unit._status = "disconnected"
                self._thermal_events.append({
                    "type": "DISCONNECT",
                    "unit": unit.id,
                    "temp": unit.temperature,
                })
        elif unit.temperature > THROTTLE_TEMP:
            if unit.discharge_rate_multiplier != 0.5:
                unit.discharge_rate_multiplier = 0.5
                self._thermal_events.append({
                    "type": "THROTTLE",
                    "unit": unit.id,
                    "temp": unit.temperature,
                })
        else:
            unit.discharge_rate_multiplier = 1.0
            # Auto-reconnect if cooled below disconnect threshold
            if not unit.is_connected and unit.temperature < THROTTLE_TEMP:
                unit.is_connected = True
                self._thermal_events.append({
                    "type": "RECONNECT",
                    "unit": unit.id,
                    "temp": unit.temperature,
                })

    # ── Priority Dispatch ────────────────────────────────────────────
    def dispatch(self, action: str, total_amount: float, price: float):
        """
        Distribute energy across the fleet using priority scoring.
        Returns the actual total amount processed.
        """
        self._thermal_events.clear()
        self._leader_id = None

        if action == "IDLE":
            for u in self.units:
                u._current_flow = 0.0
                u._status = "idle"
                self._apply_thermal(u, 0.0)
            return 0.0

        # Sort by dispatch score (best candidate first)
        active_units = [u for u in self.units if u.is_connected]
        active_units.sort(key=lambda u: u.dispatch_score, reverse=True)

        if not active_units:
            return 0.0

        remaining = total_amount
        total_processed = 0.0

        for i, unit in enumerate(active_units):
            if remaining <= 0:
                unit._current_flow = 0.0
                unit._status = "idle"
                self._apply_thermal(unit, 0.0)
                continue

            # How much can this unit handle?
            if action == "DISCHARGE":
                effective_rate = total_amount / len(active_units) * unit.discharge_rate_multiplier
                can_discharge = max(0, unit.soc - 20.0)  # Reserve 20%
                amount = min(remaining, effective_rate, can_discharge)

                unit.soc -= amount
                unit.soh -= amount * 0.005  # Micro-degradation
                unit._current_flow = amount
                unit._status = "discharging"

                if i == 0 and amount > 0:
                    self._leader_id = unit.id

            elif action == "CHARGE":
                effective_rate = total_amount / len(active_units)
                can_charge = max(0, 100.0 - unit.soc)
                amount = min(remaining, effective_rate, can_charge)

                unit.soc += amount
                unit._current_flow = amount
                unit._status = "charging"

            remaining -= amount
            total_processed += amount
            self._apply_thermal(unit, amount)

        # Handle disconnected units (passive cooling only)
        for u in self.units:
            if not u.is_connected:
                u._current_flow = 0.0
                u._status = "disconnected"
                self._apply_thermal(u, 0.0)

        return total_processed

    # ── Aggregation ──────────────────────────────────────────────────
    def aggregate_soc(self) -> float:
        """Weighted average SOC of connected units."""
        connected = [u for u in self.units if u.is_connected]
        if not connected:
            return 0.0
        return sum(u.soc for u in connected) / len(connected)

    def aggregate_soh(self) -> float:
        """Weighted average SOH of all units."""
        return sum(u.soh for u in self.units) / len(self.units)

    # ── State Export ─────────────────────────────────────────────────
    def get_fleet_state(self) -> list[dict]:
        """Return list of dicts for each unit, used by UI."""
        result = []
        for u in self.units:
            result.append({
                "id": u.id,
                "soc": round(u.soc, 1),
                "soh": round(u.soh, 2),
                "temp": round(u.temperature, 1),
                "action": u._status.upper() if u._status != "idle" else "IDLE",
                "dispatch_score": round(u.dispatch_score, 1),
                "is_leader": u.id == self._leader_id,
                "is_connected": u.is_connected,
                "throttled": u.discharge_rate_multiplier < 1.0 and u.is_connected,
                "flow": round(u._current_flow, 2),
            })
        return result

    def get_thermal_events(self) -> list[dict]:
        """Return thermal events from the last tick, then clear."""
        events = list(self._thermal_events)
        self._thermal_events.clear()
        return events

    def generate_telemetry(self) -> list[str]:
        """Generate JSON telemetry strings for all units."""
        return [u.telemetry_json() for u in self.units]
