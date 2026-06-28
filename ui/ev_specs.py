# pyrefly: ignore [missing-import]
import flet as ft
from ui.theme import ACCENT_CYAN, TEXT_MUTED

class EVSpecsModal(ft.UserControl):
    def __init__(self):
        super().__init__()
        # Dynamic text fields for real-time monitoring
        self.soc_text = ft.Text("N/A", size=24, weight="bold", color=ACCENT_CYAN)
        self.soh_text = ft.Text("N/A", size=24, weight="bold", color=ACCENT_CYAN)
        self.action_text = ft.Text("IDLE", size=24, weight="bold", color=ACCENT_CYAN)
        self.v2g_power_text = ft.Text("0.0 kW", size=24, weight="bold", color=ACCENT_CYAN)
        
    def update_data(self, data):
        if hasattr(self, 'soc_text'):
            self.soc_text.value = f"{data.get('soc', 0):.1f}%"
            self.soh_text.value = f"{data.get('soh', 0):.1f}%"
            self.action_text.value = data.get('action', 'IDLE')
            self.v2g_power_text.value = f"{data.get('v2g_flow', 0.0):.2f} kW"
            if self.page:
                self.update()

    def did_mount(self):
        self.main_container.scale = 0.8
        self.main_container.opacity = 0.0
        self.update()
        
        import threading, time
        def anim():
            time.sleep(0.05)
            self.main_container.scale = 1.0
            self.main_container.opacity = 1.0
            if self.page:
                self.update()
        threading.Thread(target=anim, daemon=True).start()

    def build(self):
        columns = [
            ft.DataColumn(ft.Text("Tesla Model", weight="bold", color="#111111")),
            ft.DataColumn(ft.Text("Battery Capacity", weight="bold", color="#111111")),
            ft.DataColumn(ft.Text("Max AC Charge", weight="bold", color="#111111")),
            ft.DataColumn(ft.Text("V2G / Powershare", weight="bold", color="#111111")),
        ]
        
        # Data sourced from public Tesla specifications
        rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("Model 3 (RWD)", color="#333333")), 
                ft.DataCell(ft.Text("~57.5 kWh", color="#333333")), 
                ft.DataCell(ft.Text("11 kW", color="#333333")), 
                ft.DataCell(ft.Text("No", color="#555555"))
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("Model 3 / Y (LR)", color="#333333")), 
                ft.DataCell(ft.Text("~82.0 kWh", color="#333333")), 
                ft.DataCell(ft.Text("11 kW", color="#333333")), 
                ft.DataCell(ft.Text("No", color="#555555"))
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("Model S / X", color="#333333")), 
                ft.DataCell(ft.Text("~100.0 kWh", color="#333333")), 
                ft.DataCell(ft.Text("11.5 kW", color="#333333")), 
                ft.DataCell(ft.Text("No", color="#555555"))
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("Cybertruck", color="#333333")), 
                ft.DataCell(ft.Text("~123.0 kWh", color="#333333")), 
                ft.DataCell(ft.Text("11.5 kW", color="#333333")), 
                ft.DataCell(ft.Text("Yes (up to 9.6kW)", color="#15803d", weight="bold"))
            ]),
        ]
        
        table = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.all(1, ft.colors.with_opacity(0.3, "#111111")),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "#111111")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "#111111")),
            heading_row_color=ft.colors.with_opacity(0.1, "white"),
        )
        
        real_time_dashboard = ft.Row([
            ft.Container(
                content=ft.Column([ft.Text("Current SoC", color="#333333"), self.soc_text], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=ft.colors.with_opacity(0.1, "white"), padding=15, border_radius=10, expand=True
            ),
            ft.Container(
                content=ft.Column([ft.Text("Battery Health", color="#333333"), self.soh_text], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=ft.colors.with_opacity(0.1, "white"), padding=15, border_radius=10, expand=True
            ),
            ft.Container(
                content=ft.Column([ft.Text("Active Mode", color="#333333"), self.action_text], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=ft.colors.with_opacity(0.1, "white"), padding=15, border_radius=10, expand=True
            ),
            ft.Container(
                content=ft.Column([ft.Text("V2G Power Flow", color="#333333"), self.v2g_power_text], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=ft.colors.with_opacity(0.1, "white"), padding=15, border_radius=10, expand=True
            ),
        ], spacing=15)
        
        self.main_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Image(src="tesla_logo.png", height=60, fit=ft.ImageFit.CONTAIN),
                    ft.Text("REAL-TIME EV MONITORING", size=18, weight="w600", color="#111111"),
                ], spacing=10),
                ft.Text("Live telemetry from simulated Cybertruck V2G session.", size=12, color="#333333"),
                ft.Container(height=5),
                real_time_dashboard,
                ft.Container(height=15),
                ft.Text("TESLA EV SPECIFICATIONS", size=16, weight="w600", color="#111111"),
                ft.Text("Reference parameters for Vehicle-to-Grid simulation.", size=12, color="#333333"),
                ft.Container(height=5),
                table
            ], tight=True),
            padding=30,
            bgcolor=ft.colors.with_opacity(0.3, "white"),
            border_radius=15,
            border=ft.border.all(1, ft.colors.with_opacity(0.5, "white")),
            blur=ft.Blur(15, 15, ft.BlurTileMode.MIRROR),
            width=800,
            scale=0.9,
            opacity=0.0,
            animate_scale=ft.animation.Animation(300, ft.AnimationCurve.DECELERATE),
            animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.DECELERATE)
        )
        return self.main_container
