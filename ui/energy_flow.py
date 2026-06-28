# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
import flet as ft
import math

class EnergyFlowDiagram(ft.UserControl):
    """
    Animated V2G Energy Flow Diagram.
    Shows power flowing between: EV Battery <-> Grid <-> Solar/Cloud
    Animated particles show direction based on current action.
    """

    def __init__(self):
        super().__init__()
        self._action = "IDLE"
        self._v2g_flow = 0.0
        self._cloud_cover = 0.0

        # Animated particle dots for EV <-> Grid flow
        # We'll simulate animation with opacity + position toggle
        self._dots_eg = []   # EV <-> Grid
        self._dots_sg = []   # Solar -> Grid

        # Status labels
        self.ev_soc_label = ft.Text("50.0%", size=14, weight="bold", color="#111111", text_align=ft.TextAlign.CENTER)
        self.grid_label = ft.Text("GRID", size=11, weight="w600", color="#555555", text_align=ft.TextAlign.CENTER)
        self.solar_label = ft.Text("SOLAR", size=11, weight="w600", color="#555555", text_align=ft.TextAlign.CENTER)

        self.action_badge = ft.Container(
            content=ft.Text("IDLE", size=11, weight="bold", color="#555555"),
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=20,
            border=ft.border.all(1, "#D0D0D0"),
            bgcolor=ft.colors.with_opacity(0.2, "#888888")
        )

        self.flow_label = ft.Text("No energy flow", size=11, color="#777777", text_align=ft.TextAlign.CENTER)

        # Node icons
        self.ev_icon = ft.Icon(ft.icons.ELECTRIC_CAR, size=36, color="#555555")
        self.grid_icon = ft.Icon(ft.icons.BOLT, size=36, color="#555555")
        self.solar_icon = ft.Icon(ft.icons.WB_CLOUDY, size=30, color="#555555")

        # Arrow containers (left=EV→Grid, right=Grid←EV)
        self.arrow_eg = ft.Text("→", size=28, color="#CCCCCC", animate_opacity=ft.animation.Animation(600, "easeInOut"))
        self.arrow_ge = ft.Text("←", size=28, color="#CCCCCC", animate_opacity=ft.animation.Animation(600, "easeInOut"))
        self.arrow_sg = ft.Text("↓", size=22, color="#CCCCCC", animate_opacity=ft.animation.Animation(600, "easeInOut"))

    def _make_node(self, icon, label, soc_label=None):
        items = [icon, ft.Text(label, size=11, weight="w600", color="#555555")]
        if soc_label:
            items.append(soc_label)
        return ft.Column(items, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, spacing=4)

    def build(self):
        ev_node = self._make_node(self.ev_icon, "EV BATTERY", self.ev_soc_label)
        grid_node = self._make_node(self.grid_icon, "GRID", None)
        solar_node = self._make_node(self.solar_icon, "SOLAR", None)

        # Main horizontal flow row: EV — arrows — GRID
        flow_row = ft.Row([
            ft.Container(content=ev_node, width=90, alignment=ft.alignment.center),
            ft.Column([
                self.arrow_eg,
                self.arrow_ge,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, spacing=2),
            ft.Container(content=grid_node, width=90, alignment=ft.alignment.center),
        ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        # Solar above grid
        solar_section = ft.Column([
            ft.Container(content=solar_node, alignment=ft.alignment.center),
            self.arrow_sg,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, spacing=4)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.DEVICE_HUB, size=16, color="#333333"),
                    ft.Text("ENERGY FLOW", size=14, weight="w600", color="#111111")
                ]),
                ft.Container(height=10),
                ft.Column([
                    solar_section,
                    ft.Container(height=10),
                    flow_row,
                    ft.Container(height=10),
                    ft.Row([self.action_badge], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=4),
                    ft.Row([self.flow_label], alignment=ft.MainAxisAlignment.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ], tight=True),
            padding=20,
            width=330,
            bgcolor=ft.colors.with_opacity(0.3, "white"),
            border_radius=15,
            border=ft.border.all(1, ft.colors.with_opacity(0.5, "white")),
            blur=ft.Blur(15, 15, ft.BlurTileMode.MIRROR)
        )

    def update_state(self, data):
        action = data.get("action", "IDLE")
        soc = data.get("soc", 50.0)
        v2g_flow = data.get("v2g_flow", 0.0)
        cloud_cover = data.get("cloud_cover", 0.0)

        self._action = action
        self.ev_soc_label.value = f"{soc:.1f}%"

        # Solar energy based on cloud cover (simulated)
        solar_output = max(0.0, (1.0 - cloud_cover / 100.0) * 8.0)
        solar_active = solar_output > 1.0

        if action == "DISCHARGE":
            # EV → Grid
            self.arrow_eg.opacity = 1.0
            self.arrow_ge.opacity = 0.15
            self.arrow_eg.color = "#16A34A"
            self.arrow_ge.color = "#CCCCCC"
            self.ev_icon.color = "#16A34A"
            self.grid_icon.color = "#16A34A"
            self.action_badge.bgcolor = ft.colors.with_opacity(0.15, "#16A34A")
            self.action_badge.border = ft.border.all(1, ft.colors.with_opacity(0.5, "#16A34A"))
            self.action_badge.content.value = "V2G DISCHARGING"
            self.action_badge.content.color = "#16A34A"
            self.flow_label.value = f"Sending {abs(v2g_flow):.1f} kW to Grid"
            self.flow_label.color = "#16A34A"
        elif action == "CHARGE":
            # Grid → EV
            self.arrow_eg.opacity = 0.15
            self.arrow_ge.opacity = 1.0
            self.arrow_eg.color = "#CCCCCC"
            self.arrow_ge.color = "#2563EB"
            self.ev_icon.color = "#2563EB"
            self.grid_icon.color = "#2563EB"
            self.action_badge.bgcolor = ft.colors.with_opacity(0.15, "#2563EB")
            self.action_badge.border = ft.border.all(1, ft.colors.with_opacity(0.5, "#2563EB"))
            self.action_badge.content.value = "CHARGING"
            self.action_badge.content.color = "#2563EB"
            self.flow_label.value = f"Drawing {abs(v2g_flow):.1f} kW from Grid"
            self.flow_label.color = "#2563EB"
        else:
            self.arrow_eg.opacity = 0.15
            self.arrow_ge.opacity = 0.15
            self.arrow_eg.color = "#CCCCCC"
            self.arrow_ge.color = "#CCCCCC"
            self.ev_icon.color = "#555555"
            self.grid_icon.color = "#555555"
            self.action_badge.bgcolor = ft.colors.with_opacity(0.1, "#888888")
            self.action_badge.border = ft.border.all(1, "#D0D0D0")
            self.action_badge.content.value = "IDLE"
            self.action_badge.content.color = "#555555"
            self.flow_label.value = "No energy flow"
            self.flow_label.color = "#777777"

        # Solar arrow
        if solar_active:
            self.arrow_sg.opacity = 0.85
            self.arrow_sg.color = "#F59E0B"
            self.solar_icon.color = "#F59E0B"
            self.solar_label.value = f"SOLAR ~{solar_output:.1f}kW"
        else:
            self.arrow_sg.opacity = 0.1
            self.arrow_sg.color = "#CCCCCC"
            self.solar_icon.color = "#AAAAAA"

        if self.page:
            self.update()
