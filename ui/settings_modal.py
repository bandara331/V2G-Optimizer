# pyrefly: ignore [missing-import]
import flet as ft

class SettingsModal(ft.UserControl):
    def __init__(self, on_settings_changed=None):
        super().__init__()
        self.on_settings_changed = on_settings_changed

        # Default values
        self._high_price = 0.25
        self._low_price = 0.15
        self._charge_rate = 5.0
        self._discharge_rate = 5.0
        self._min_reserve = 20.0
        self._sim_speed = 1.0

        # Sliders
        self.sl_high_price = ft.Slider(min=0.15, max=0.50, divisions=35, value=self._high_price,
                                       label="${value:.2f}/kWh", active_color="#E50000",
                                       on_change=self._on_change)
        self.sl_low_price = ft.Slider(min=0.05, max=0.25, divisions=20, value=self._low_price,
                                      label="${value:.2f}/kWh", active_color="#2563EB",
                                      on_change=self._on_change)
        self.sl_charge_rate = ft.Slider(min=1.0, max=20.0, divisions=19, value=self._charge_rate,
                                        label="{value:.0f}%/tick", active_color="#16A34A",
                                        on_change=self._on_change)
        self.sl_discharge_rate = ft.Slider(min=1.0, max=20.0, divisions=19, value=self._discharge_rate,
                                           label="{value:.0f}%/tick", active_color="#F59E0B",
                                           on_change=self._on_change)
        self.sl_min_reserve = ft.Slider(min=5.0, max=50.0, divisions=45, value=self._min_reserve,
                                        label="{value:.0f}%", active_color="#7C3AED",
                                        on_change=self._on_change)
        self.sl_sim_speed = ft.Slider(min=0.25, max=3.0, divisions=11, value=self._sim_speed,
                                      label="{value:.2f}s/tick", active_color="#0EA5E9",
                                      on_change=self._on_change)

        self.status_text = ft.Text("Settings applied.", size=12, color="#16A34A", opacity=0.0,
                                   animate_opacity=ft.animation.Animation(500, "easeOut"))

    def _label(self, text, color="#333333"):
        return ft.Text(text, size=13, weight="w600", color=color)

    def _sub(self, text):
        return ft.Text(text, size=11, color="#777777")

    def _on_change(self, e):
        self._high_price = self.sl_high_price.value
        self._low_price = self.sl_low_price.value
        self._charge_rate = self.sl_charge_rate.value
        self._discharge_rate = self.sl_discharge_rate.value
        self._min_reserve = self.sl_min_reserve.value
        self._sim_speed = self.sl_sim_speed.value

        if self.on_settings_changed:
            self.on_settings_changed(self.get_settings())

        self.status_text.opacity = 1.0
        if self.page:
            self.status_text.update()

        # Fade out after 2 seconds
        import threading
        def fade():
            import time
            time.sleep(2.0)
            self.status_text.opacity = 0.0
            if self.page:
                self.status_text.update()
        threading.Thread(target=fade, daemon=True).start()

    def get_settings(self):
        return {
            "high_price_threshold": self._high_price,
            "low_price_threshold": self._low_price,
            "charge_rate": self._charge_rate,
            "discharge_rate": self._discharge_rate,
            "min_battery_reserve": self._min_reserve,
            "sim_speed": self._sim_speed,
        }

    def _row(self, label_text, sub_text, slider):
        return ft.Column([
            ft.Row([
                self._label(label_text),
                ft.Container(expand=True),
                self._sub(sub_text),
            ]),
            slider,
            ft.Container(height=8)
        ], tight=True)

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
                    ft.Text("OPTIMIZER SETTINGS", size=18, weight="w600", color="#111111"),
                    ft.Container(expand=True),
                    self.status_text
                ]),
                ft.Text("Adjust parameters in real-time. Changes apply immediately.", size=12, color="#555555"),
                ft.Container(height=15),
                ft.Divider(color="#E0E0E0"),
                ft.Container(height=10),

                self._row("High Price Threshold", "Trigger V2G discharge above this", self.sl_high_price),
                self._row("Low Price Threshold", "Trigger charging below this", self.sl_low_price),
                self._row("Charge Rate", "% SoC gained per tick", self.sl_charge_rate),
                self._row("Discharge Rate", "% SoC discharged per tick", self.sl_discharge_rate),
                self._row("Min Battery Reserve", "Never discharge below this SoC", self.sl_min_reserve),
                self._row("Sim Speed", "Seconds per simulation tick", self.sl_sim_speed),
            ], tight=True, scroll=ft.ScrollMode.AUTO),
            width=520,
            height=560,
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
