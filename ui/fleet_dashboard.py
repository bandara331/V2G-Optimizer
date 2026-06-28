# pyrefly: ignore [missing-import]
import flet as ft


class EVStatusCard(ft.UserControl):
    def __init__(self, ev_id):
        super().__init__()
        self.ev_id = ev_id

        self.icon = ft.Icon(ft.icons.ELECTRIC_CAR, size=30, color="#555555")
        self.status_text = ft.Text("IDLE", size=11, weight="bold", color="#555555")
        self.battery_bar = ft.ProgressBar(
            value=0.5, color="#555555",
            bgcolor=ft.colors.with_opacity(0.2, "#111111"), height=6
        )
        self.soc_text = ft.Text("50%", size=14, weight="bold", color="#111111")
        self.soh_text = ft.Text("SOH: 100.00%", size=10, color="#555555")

        # NEW: Temperature display
        self.temp_text = ft.Text(
            "25.0°C", size=12, weight="bold", color="#0EA5E9"
        )
        self.temp_bar = ft.ProgressBar(
            value=0.0, color="#0EA5E9",
            bgcolor=ft.colors.with_opacity(0.15, "#111111"), height=4
        )

        # NEW: Dispatch score badge
        self.score_badge = ft.Container(
            content=ft.Text("0.0", size=9, weight="bold", color="white"),
            padding=ft.padding.symmetric(horizontal=5, vertical=1),
            border_radius=8,
            bgcolor=ft.colors.with_opacity(0.6, "#2563EB"),
        )

        # NEW: Leader crown indicator
        self.leader_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.STAR, size=12, color="#00F0FF"),
                ft.Text("LEADER", size=8, weight="bold", color="#00F0FF"),
            ], tight=True, spacing=2),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=10,
            bgcolor=ft.colors.with_opacity(0.15, "#00F0FF"),
            visible=False,
        )

        # NEW: Throttled / Disconnected badge
        self.warn_badge = ft.Container(
            content=ft.Text("", size=8, weight="bold", color="white"),
            padding=ft.padding.symmetric(horizontal=5, vertical=1),
            border_radius=6,
            bgcolor="#F59E0B",
            visible=False,
        )

        self.card_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.icon,
                    ft.Column([
                        ft.Text(f"Unit-{self.ev_id}", size=14, weight="w600", color="#333333"),
                        self.leader_badge,
                    ], tight=True, spacing=2),
                    ft.Container(expand=True),
                    self.score_badge,
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Container(height=4),
                self.status_text,
                self.battery_bar,
                ft.Row([self.soc_text, self.soh_text],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=4),
                # Temperature row
                ft.Row([
                    ft.Icon(ft.icons.THERMOSTAT, size=14, color="#888888"),
                    self.temp_text,
                    ft.Container(expand=True),
                    self.warn_badge,
                ], alignment=ft.MainAxisAlignment.START, spacing=4),
                self.temp_bar,
            ], tight=True, spacing=3),
            width=160,
            padding=15,
            border_radius=10,
            border=ft.border.all(1, ft.colors.with_opacity(0.2, "#111111")),
            bgcolor=ft.colors.with_opacity(0.4, "white"),
        )

    def build(self):
        return self.card_container

    def update_state(self, unit_data: dict):
        """
        Accept a per-unit dict from FleetManager:
        {soc, soh, temp, action, dispatch_score, is_leader, is_connected, throttled, flow}
        """
        soc = unit_data.get("soc", 50.0)
        soh = unit_data.get("soh", 100.0)
        temp = unit_data.get("temp", 25.0)
        action = unit_data.get("action", "IDLE")
        score = unit_data.get("dispatch_score", 0.0)
        is_leader = unit_data.get("is_leader", False)
        is_connected = unit_data.get("is_connected", True)
        throttled = unit_data.get("throttled", False)

        # Battery bar
        self.battery_bar.value = soc / 100.0
        self.soc_text.value = f"{soc:.1f}%"
        self.soh_text.value = f"SOH: {soh:.2f}%"

        # Temperature display with color coding
        self.temp_text.value = f"{temp:.1f}°C"
        temp_norm = min(1.0, max(0.0, (temp - 20.0) / 40.0))  # 20-60°C range
        self.temp_bar.value = temp_norm

        if not is_connected:
            self.temp_text.color = "#991B1B"
            self.temp_bar.color = "#991B1B"
        elif temp > 45.0:
            self.temp_text.color = "#E50000"
            self.temp_bar.color = "#E50000"
        elif temp > 35.0:
            self.temp_text.color = "#F59E0B"
            self.temp_bar.color = "#F59E0B"
        else:
            self.temp_text.color = "#0EA5E9"
            self.temp_bar.color = "#0EA5E9"

        # Dispatch score
        self.score_badge.content.value = f"{score:.0f}"

        # Leader badge
        self.leader_badge.visible = is_leader

        # Throttle / disconnect warning
        if not is_connected:
            self.warn_badge.visible = True
            self.warn_badge.content.value = "⚠ DISCONNECTED"
            self.warn_badge.bgcolor = "#991B1B"
        elif throttled:
            self.warn_badge.visible = True
            self.warn_badge.content.value = "⚡ THROTTLED"
            self.warn_badge.bgcolor = "#F59E0B"
        else:
            self.warn_badge.visible = False

        # Action-based styling
        if not is_connected:
            self.status_text.value = "DISCONNECTED"
            self.status_text.color = "#991B1B"
            self.battery_bar.color = "#991B1B"
            self.icon.color = "#991B1B"
            self.card_container.border = ft.border.all(2, ft.colors.with_opacity(0.6, "#991B1B"))
            self.card_container.shadow = ft.BoxShadow(
                spread_radius=1, blur_radius=10,
                color=ft.colors.with_opacity(0.3, "#991B1B")
            )
        elif action == "CHARGING":
            self.status_text.value = "CHARGING"
            self.status_text.color = "#2563EB"
            self.battery_bar.color = "#3B82F6"
            self.icon.color = "#2563EB"
            self.card_container.border = ft.border.all(2, ft.colors.with_opacity(0.5, "#3B82F6"))
            self.card_container.shadow = ft.BoxShadow(
                spread_radius=1, blur_radius=10,
                color=ft.colors.with_opacity(0.3, "#3B82F6")
            )
        elif action == "DISCHARGING":
            self.status_text.value = "V2G DISCHARGING"
            self.status_text.color = "#16A34A"
            self.battery_bar.color = "#22C55E"
            self.icon.color = "#16A34A"
            self.card_container.border = ft.border.all(2, ft.colors.with_opacity(0.5, "#22C55E"))
            self.card_container.shadow = ft.BoxShadow(
                spread_radius=1, blur_radius=10,
                color=ft.colors.with_opacity(0.3, "#22C55E")
            )
            # Leader glow
            if is_leader:
                self.card_container.border = ft.border.all(2, "#00F0FF")
                self.card_container.shadow = ft.BoxShadow(
                    spread_radius=2, blur_radius=18,
                    color=ft.colors.with_opacity(0.5, "#00F0FF")
                )
        else:
            self.status_text.value = "IDLE"
            self.status_text.color = "#555555"
            self.battery_bar.color = "#555555"
            self.icon.color = "#555555"
            self.card_container.border = ft.border.all(1, ft.colors.with_opacity(0.2, "#111111"))
            self.card_container.shadow = None

        if self.page:
            self.update()


class FleetDashboardModal(ft.UserControl):
    def __init__(self):
        super().__init__()

        # Create a fleet of 4 EVs
        self.evs = [
            EVStatusCard(ev_id="T01"),
            EVStatusCard(ev_id="T02"),
            EVStatusCard(ev_id="T03"),
            EVStatusCard(ev_id="T04"),
        ]

    def did_mount(self):
        self.main_container.scale = 0.8
        self.main_container.opacity = 0.0
        self.update()

        import threading
        import time

        def anim():
            time.sleep(0.05)
            self.main_container.scale = 1.0
            self.main_container.opacity = 1.0
            if self.page:
                self.update()

        threading.Thread(target=anim, daemon=True).start()

    def build(self):
        grid = ft.Row(
            controls=self.evs,
            wrap=True,
            spacing=15,
            run_spacing=15,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.main_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Image(src="tesla_logo.png", height=60, fit=ft.ImageFit.CONTAIN),
                    ft.Text("REAL-TIME FLEET STATUS", size=18, weight="w600", color="#111111"),
                ], spacing=10),
                ft.Text(
                    "Live telemetry of V2G units responding to grid demand. "
                    "Temperature, dispatch priority, and leader shown per unit.",
                    size=12, color="#333333"
                ),
                ft.Container(height=15),
                ft.Container(
                    content=grid,
                    width=355,  # 160+15+160=335, extra padding
                ),
            ], tight=True),
            padding=30,
            bgcolor=ft.colors.with_opacity(0.3, "white"),
            border_radius=15,
            border=ft.border.all(1, ft.colors.with_opacity(0.5, "white")),
            blur=ft.Blur(15, 15, ft.BlurTileMode.MIRROR),
            scale=0.9,
            opacity=0.0,
            animate_scale=ft.animation.Animation(300, ft.AnimationCurve.DECELERATE),
            animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.DECELERATE),
        )
        return self.main_container

    def update_data(self, data):
        fleet = data.get("fleet", None)

        if fleet:
            # Use real fleet data from FleetManager
            for ev_card, unit_data in zip(self.evs, fleet):
                ev_card.update_state(unit_data)
        else:
            # Fallback: legacy single-unit data
            soc = data.get("soc", 50.0)
            soh = data.get("soh", 100.0)
            action = data.get("action", "IDLE")
            for ev_card in self.evs:
                ev_card.update_state({
                    "soc": soc, "soh": soh, "temp": 25.0,
                    "action": action, "dispatch_score": 0.0,
                    "is_leader": False, "is_connected": True, "throttled": False,
                })
