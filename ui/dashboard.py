# pyrefly: ignore [missing-import]
import flet as ft
from ui.theme import TEXT_MUTED
import math

class ChartModal(ft.UserControl):
    def __init__(self):
        super().__init__()
        
        self.chart_data_demand = []
        self.chart_data_v2g = []
        
        # LineChart Data Series
        self.demand_series = ft.LineChartData(
            data_points=[],
            stroke_width=4,
            color="#E50000", # Tesla Red
            curved=True,
            stroke_cap_round=True,
            below_line_gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.colors.with_opacity(0.4, "#E50000"), ft.colors.TRANSPARENT]
            )
        )
        
        self.v2g_series = ft.LineChartData(
            data_points=[],
            stroke_width=4,
            color="#16A34A", # V2G Green
            curved=True,
            stroke_cap_round=True,
            below_line_gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.colors.with_opacity(0.3, "#16A34A"), ft.colors.TRANSPARENT]
            )
        )
        
        self.chart = ft.LineChart(
            data_series=[self.demand_series, self.v2g_series],
            border=ft.border.all(1, ft.colors.with_opacity(0.2, "#111111")),
            horizontal_grid_lines=ft.ChartGridLines(
                interval=20, color=ft.colors.with_opacity(0.1, "#111111"), width=1
            ),
            vertical_grid_lines=ft.ChartGridLines(
                interval=4, color=ft.colors.with_opacity(0.1, "#111111"), width=1
            ),
            left_axis=ft.ChartAxis(labels=[
                ft.ChartAxisLabel(value=20, label=ft.Text("20kW", size=10, color="#333333")),
                ft.ChartAxisLabel(value=60, label=ft.Text("60kW", size=10, color="#333333")),
                ft.ChartAxisLabel(value=100, label=ft.Text("100kW", size=10, color="#333333")),
            ]),
            bottom_axis=ft.ChartAxis(labels=[
                ft.ChartAxisLabel(value=0, label=ft.Text("0h", size=10, color="#333333")),
                ft.ChartAxisLabel(value=6, label=ft.Text("6h", size=10, color="#333333")),
                ft.ChartAxisLabel(value=12, label=ft.Text("12h", size=10, color="#333333")),
                ft.ChartAxisLabel(value=18, label=ft.Text("18h", size=10, color="#333333")),
                ft.ChartAxisLabel(value=24, label=ft.Text("24h", size=10, color="#333333")),
            ]),
            tooltip_bgcolor=ft.colors.with_opacity(0.8, "black"),
            min_y=0,
            max_y=120,
            min_x=0,
            max_x=24,
            expand=True,
            animate=ft.animation.Animation(500, "easeOut"),
        )

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
        self.main_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Image(src="tesla_logo.png", height=60, fit=ft.ImageFit.CONTAIN),
                    ft.Container(width=10),
                    ft.Text("GRID DEMAND vs V2G SUPPORT", size=18, weight="w600", color="#111111"),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Container(width=12, height=12, bgcolor="#E50000", border_radius=6),
                        ft.Text("Grid Demand", size=13, weight="w500", color="#333333"),
                        ft.Container(width=15),
                        ft.Container(width=12, height=12, bgcolor="#16A34A", border_radius=6),
                        ft.Text("V2G Support", size=13, weight="w500", color="#333333"),
                    ])
                ]),
                ft.Container(height=15),
                ft.Container(content=self.chart, height=350, width=650)
            ], tight=True),
            padding=30,
            bgcolor=ft.colors.with_opacity(0.3, "white"),
            border_radius=15,
            border=ft.border.all(1, ft.colors.with_opacity(0.5, "white")),
            blur=ft.Blur(15, 15, ft.BlurTileMode.MIRROR),
            scale=0.9,
            opacity=0.0,
            animate_scale=ft.animation.Animation(300, ft.AnimationCurve.DECELERATE),
            animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.DECELERATE)
        )
        return self.main_container

    def update_data(self, data):
        time = data['time']
        demand = data['demand']
        v2g = max(0, data['v2g_flow'])
        
        # Reset chart at midnight to loop
        if time < 0.25 and len(self.chart_data_demand) > 10:
            self.chart_data_demand.clear()
            self.chart_data_v2g.clear()

        self.chart_data_demand.append(ft.LineChartDataPoint(time, demand))
        self.chart_data_v2g.append(ft.LineChartDataPoint(time, v2g))
        
        self.demand_series.data_points = self.chart_data_demand
        self.v2g_series.data_points = self.chart_data_v2g
        
        if self.page:
            self.update()
