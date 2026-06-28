# pyrefly: ignore [missing-import]
import flet as ft
import asyncio
from simulator import Simulator
from llm_reporter import LLMReporter
from ui.theme import get_theme
from ui.hud import HUD
from ui.dashboard import ChartModal
from ui.fleet_dashboard import FleetDashboardModal
from ui.ev_specs import EVSpecsModal
from ui.settings_modal import SettingsModal
from ui.energy_flow import EnergyFlowDiagram
import os

def main(page: ft.Page):
    page.title = "V2G Grid Optimizer Desktop Simulator"
    page.theme = get_theme()
    page.bgcolor = "#000000"
    page.padding = 0
    page.window.width = 1400
    page.window.height = 850
    page.window.title_bar_hidden = True
    page.window.title_bar_buttons_hidden = True
    
    reporter = LLMReporter()
    chart_modal = ChartModal()
    fleet_dashboard_modal = FleetDashboardModal()
    ev_specs_modal = EVSpecsModal()
    settings_modal = SettingsModal()
    energy_flow = EnergyFlowDiagram()
    
    chart_dlg = ft.AlertDialog(content=chart_modal, bgcolor=ft.colors.TRANSPARENT, content_padding=0)
    fleet_dlg = ft.AlertDialog(content=fleet_dashboard_modal, bgcolor=ft.colors.TRANSPARENT, content_padding=0)
    ev_specs_dlg = ft.AlertDialog(content=ev_specs_modal, bgcolor=ft.colors.TRANSPARENT, content_padding=0)
    settings_dlg = ft.AlertDialog(content=settings_modal, bgcolor=ft.colors.TRANSPARENT, content_padding=0)

    # Callbacks for HUD
    def handle_generate_report(callback):
        reporter.generate_report(simulator.get_logs(), callback)
        
    def handle_toggle_sim(is_running):
        if is_running and not simulator.is_running:
            page.run_task(run_simulation)
        elif not is_running and simulator.is_running:
            simulator.stop()
            
    def handle_view_charts():
        page.open(chart_dlg)

    def handle_view_dashboard():
        page.open(fleet_dlg)

    def handle_view_ev_specs():
        page.open(ev_specs_dlg)

    def handle_open_settings():
        def on_settings_changed(cfg):
            # Apply new settings to optimizer and simulator
            simulator.optimizer.high_price_threshold = cfg["high_price_threshold"]
            simulator.optimizer.low_price_threshold = cfg["low_price_threshold"]
            simulator.optimizer.charge_rate = cfg["charge_rate"]
            simulator.optimizer.discharge_rate = cfg["discharge_rate"]
            simulator.optimizer.min_battery_reserve = cfg["min_battery_reserve"]
            simulator.sim_speed = cfg["sim_speed"]

        settings_modal.on_settings_changed = on_settings_changed
        page.open(settings_dlg)

    def handle_export_csv():
        success = simulator.export_to_csv("v2g_telemetry.csv")
        if success:
            page.snack_bar = ft.SnackBar(ft.Text("Successfully exported to v2g_telemetry.csv"))
            page.snack_bar.open = True
            page.update()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Failed to export telemetry data.", color="red"))
            page.snack_bar.open = True
            page.update()

    hud = HUD(
        on_toggle_sim=handle_toggle_sim,
        on_view_charts=handle_view_charts,
        on_generate_report=handle_generate_report,
        on_view_dashboard=handle_view_dashboard,
        on_export_csv=handle_export_csv,
        on_open_settings=handle_open_settings,
        on_view_ev_specs=handle_view_ev_specs,
    )
    
    page.add(hud)
    
    last_action = {"action": "IDLE"}
    last_soh_warn = {"level": 0}  # 0=none, 1=warning, 2=critical
    
    def update_ui(data):
        hud.update_data(data)
        chart_modal.update_data(data)
        fleet_dashboard_modal.update_data(data)
        energy_flow.update_state(data)
        ev_specs_modal.update_data(data)
        
        # System Logs Generation
        time_str = f"[{int(data['time']):02d}:{int((data['time']%1)*60):02d}]"
        
        if data['demand'] > 85:
            hud.log_message(f"{time_str} [WARN] Grid overload imminent. Grid Load: {data['demand']:.1f}kW")
            
        if data['action'] != last_action["action"]:
            if data['action'] == "DISCHARGE":
                hud.log_message(f"{time_str} [INFO] Fleet initiated V2G support. Fleet discharging.")
            elif data['action'] == "CHARGE":
                hud.log_message(f"{time_str} [INFO] Fleet drawing power (Charging).")
            else:
                hud.log_message(f"{time_str} [INFO] Fleet is IDLE.")
            last_action["action"] = data['action']

        # SoH degradation warnings
        soh = data.get("soh", 100.0)
        if soh < 90.0 and last_soh_warn["level"] < 2:
            hud.log_message(f"{time_str} [CRIT] Battery health at {soh:.1f}%. Reduce V2G activity.")
            last_soh_warn["level"] = 2
        elif soh < 95.0 and last_soh_warn["level"] < 1:
            hud.log_message(f"{time_str} [WARN] Battery health declining -- SoH at {soh:.1f}%.")
            last_soh_warn["level"] = 1

        # NEW: Thermal event logging
        thermal_events = data.get("thermal_events", [])
        for event in thermal_events:
            if event["type"] == "DISCONNECT":
                hud.log_message(
                    f"{time_str} [CRIT] Unit {event['unit']} EMERGENCY DISCONNECT at {event['temp']:.1f}°C!"
                )
            elif event["type"] == "THROTTLE":
                hud.log_message(
                    f"{time_str} [WARN] Unit {event['unit']} thermal throttled at {event['temp']:.1f}°C — rate halved."
                )
            elif event["type"] == "RECONNECT":
                hud.log_message(
                    f"{time_str} [INFO] Unit {event['unit']} cooled to {event['temp']:.1f}°C — reconnected."
                )

    # Telemetry callback — routes 10Hz packets to HUD
    def handle_telemetry(packet_str):
        hud.log_telemetry(packet_str)

    simulator = Simulator(update_callback=update_ui, telemetry_callback=handle_telemetry)
    
    async def run_simulation():
        await simulator.run()
        
    page.run_task(run_simulation)

if __name__ == "__main__":
    # Ensure assets_dir is used to load background.png
    assets_path = os.path.join(os.path.dirname(__file__), "assets")
    ft.app(target=main, assets_dir=assets_path)
