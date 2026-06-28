import asyncio
import math
import random
import httpx
import csv
from datetime import datetime
from collections import deque
from optimizer import V2GOptimizer
from fleet_model import FleetManager


class Simulator:
    def __init__(self, update_callback, telemetry_callback=None):
        self.update_callback = update_callback
        self.telemetry_callback = telemetry_callback  # Called at ~10Hz with JSON strings
        self.optimizer = V2GOptimizer()
        self.fleet_manager = FleetManager()

        # State variables
        self.time_hour = 0.0  # 0.0 to 24.0
        self.demand = 40.0    # Base demand in kW
        self.price = 0.15     # Base price $/kWh
        self.cloud_cover = 0.0  # From Weather API

        self.is_running = False
        self.sim_speed = 1.0  # seconds per tick, configurable at runtime
        self.telemetry_history = []

        # Logging for AI report
        self.logs = {
            "total_energy_discharged": 0.0,
            "total_energy_charged": 0.0,
            "grid_support_events": 0,
            "earnings": 0.0,
            "cost": 0.0
        }

    # ── Property shims for aggregate SoC / SoH ──────────────────────
    @property
    def soc(self):
        return self.fleet_manager.aggregate_soc()

    @property
    def soh(self):
        return self.fleet_manager.aggregate_soh()

    async def _fetch_weather(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.open-meteo.com/v1/forecast?latitude=37.77&longitude=-122.41&current=cloud_cover",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    self.cloud_cover = float(data.get("current", {}).get("cloud_cover", 0.0))
        except Exception as e:
            print(f"Error fetching weather: {e}")

    def _simulate_environment(self):
        # Create a daily curve using a sine wave
        # Peak demand around 18:00 (6 PM)
        # Low demand around 04:00 (4 AM)
        phase_shift = (self.time_hour - 6) / 24.0 * 2 * math.pi
        curve = math.sin(phase_shift - math.pi / 2)

        # Demand fluctuates between 20kW and 100kW
        weather_impact = (self.cloud_cover / 100.0) * 15.0
        base_demand = 60 + curve * 40 + weather_impact
        self.demand = base_demand + random.uniform(-5, 5)

        # Price correlates with demand. Range $0.10 to $0.40
        base_price = 0.25 + curve * 0.15
        self.price = max(0.10, base_price + random.uniform(-0.02, 0.02))

    # ── 10Hz Telemetry Stream (runs independently) ──────────────────
    async def _telemetry_stream(self):
        """Emit per-unit telemetry packets at ~10Hz."""
        while self.is_running:
            if self.telemetry_callback:
                packets = self.fleet_manager.generate_telemetry()
                for pkt in packets:
                    self.telemetry_callback(pkt)
            await asyncio.sleep(0.1)  # 10Hz

    async def run(self):
        self.is_running = True
        await self._fetch_weather()

        # Launch the telemetry stream as a parallel task
        telemetry_task = asyncio.create_task(self._telemetry_stream())

        try:
            while self.is_running:
                # Advance time by 15 minutes per tick (0.25 hours)
                self.time_hour = (self.time_hour + 0.25) % 24.0

                self._simulate_environment()

                # Run optimizer (still decides aggregate action/amount)
                agg_soc = self.soc
                action, amount = self.optimizer.decide_action(agg_soc, self.price, self.demand)

                # Delegate to fleet manager for per-unit distribution
                actual_amount = self.fleet_manager.dispatch(action, amount, self.price)

                v2g_flow = 0.0
                if action == "CHARGE":
                    self.logs["total_energy_charged"] += actual_amount
                    self.logs["cost"] += actual_amount * self.price
                    v2g_flow = -actual_amount
                elif action == "DISCHARGE":
                    self.logs["total_energy_discharged"] += actual_amount
                    self.logs["earnings"] += actual_amount * self.price
                    self.logs["grid_support_events"] += 1
                    v2g_flow = actual_amount

                # Get aggregated values from fleet
                current_soc = self.soc
                current_soh = self.soh

                self.telemetry_history.append({
                    "time": self.time_hour,
                    "demand": self.demand,
                    "price": self.price,
                    "soc": current_soc,
                    "soh": current_soh,
                    "v2g_flow": v2g_flow
                })

                # Trigger UI update
                if self.update_callback:
                    net = self.logs["earnings"] - self.logs["cost"]
                    self.update_callback({
                        "time": self.time_hour,
                        "demand": self.demand,
                        "price": self.price,
                        "soc": current_soc,
                        "soh": current_soh,
                        "action": action,
                        "v2g_flow": v2g_flow,
                        "cloud_cover": self.cloud_cover,
                        "earnings": self.logs["earnings"],
                        "cost": self.logs["cost"],
                        "net": net,
                        "grid_support_events": self.logs["grid_support_events"],
                        # NEW: fleet-level data for dashboard
                        "fleet": self.fleet_manager.get_fleet_state(),
                        "thermal_events": self.fleet_manager.get_thermal_events(),
                    })

                # Wait a short real-time duration before next tick
                await asyncio.sleep(self.sim_speed)
        finally:
            telemetry_task.cancel()
            try:
                await telemetry_task
            except asyncio.CancelledError:
                pass

    def stop(self):
        self.is_running = False

    def get_logs(self):
        return self.logs

    def export_to_csv(self, filepath):
        if not self.telemetry_history:
            return False

        keys = self.telemetry_history[0].keys()
        try:
            with open(filepath, 'w', newline='') as output_file:
                dict_writer = csv.DictWriter(output_file, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(self.telemetry_history)
            return True
        except Exception as e:
            print(f"Failed to export CSV: {e}")
            return False
