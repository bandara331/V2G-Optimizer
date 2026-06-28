# pyrefly: ignore [missing-import]
import flet as ft


# ---------------------------------------------------------------------------
# AnimatedBar  (self-contained, no UserControl nesting issues)
# ---------------------------------------------------------------------------
class AnimatedBar:
    def __init__(self, label, color="#E50000", unit=""):
        self.unit = unit
        self.bar_fill = ft.Container(
            bgcolor=color, height=10, width=0, border_radius=5,
            animate=ft.animation.Animation(500, "easeOut")
        )
        self.value_text = ft.Text("0" + unit, size=12, width=55, color="#555555",
                                   weight="bold", text_align=ft.TextAlign.RIGHT)
        self.control = ft.Row([
            ft.Text(label, size=13, width=95, color="#333333", weight="w500"),
            ft.Stack([
                ft.Container(bgcolor="#D3D3D3", height=10, width=140, border_radius=5),
                self.bar_fill
            ], height=10, width=140),
            self.value_text
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def set_progress(self, percentage, raw_value_str):
        percentage = max(0.0, min(1.0, percentage))
        self.bar_fill.width = 140 * percentage
        self.value_text.value = raw_value_str + self.unit
        self.bar_fill.update()
        self.value_text.update()


# ---------------------------------------------------------------------------
# HUD  — monolithic build, all panels as plain ft.Container
# ---------------------------------------------------------------------------
class HUD(ft.UserControl):
    def __init__(self, on_toggle_sim, on_view_charts, on_generate_report,
                 on_view_dashboard=None, on_export_csv=None,
                 on_open_settings=None, on_view_ev_specs=None):
        super().__init__()
        self.on_toggle_sim      = on_toggle_sim
        self.on_view_charts     = on_view_charts
        self.on_generate_report = on_generate_report
        self.on_view_dashboard  = on_view_dashboard
        self.on_export_csv      = on_export_csv
        self.on_open_settings   = on_open_settings
        self.on_view_ev_specs   = on_view_ev_specs

        self.expand         = True
        self.is_sim_running = True

        # ── Bars ──────────────────────────────────────────────────────
        self.bar_demand = AnimatedBar("Grid Load",      "#E50000",  "kW")
        self.bar_price  = AnimatedBar("Elec Price",     "#E50000",  "")
        self.bar_soc    = AnimatedBar("Charge Level",   "#E50000",  "%")
        self.bar_v2g    = AnimatedBar("V2G Output",     "#E50000",  "kW")
        self.bar_soh    = AnimatedBar("Battery Health", "#7C3AED",  "%")

        # ── Weather ───────────────────────────────────────────────────
        self.weather_icon = ft.Icon(ft.icons.CLOUD, size=16, color="#555555")
        self.weather_text = ft.Text("Weather: Loading...", size=13,
                                     color="#333333", weight="w500")

        # ── Sim clock ─────────────────────────────────────────────────
        self.sim_clock       = ft.Text("00:00", size=20, weight="bold",
                                        color="#111111", font_family="Courier New")
        self.sim_clock_label = ft.Text("SIM TIME", size=10, color="#888888", weight="w600")

        # ── SoH badge ─────────────────────────────────────────────────
        self.soh_badge = ft.Container(
            content=ft.Text("", size=10, weight="bold", color="white"),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=10, bgcolor="#E50000", visible=False
        )

        # ── Logs list ─────────────────────────────────────────────────
        self.log_list = ft.ListView(spacing=4, auto_scroll=True, height=200)

        # ── Financials ────────────────────────────────────────────────
        self.revenue_text = ft.Text("$0.00", size=22, weight="bold", color="#16A34A")
        self.cost_text    = ft.Text("$0.00", size=22, weight="bold", color="#E50000")
        self.net_text     = ft.Text("$0.00", size=22, weight="bold", color="#16A34A")
        self.events_text  = ft.Text("0",     size=22, weight="bold", color="#2563EB")

        # ── Telemetry stream panel ────────────────────────────────────
        self.telemetry_list = ft.ListView(spacing=2, auto_scroll=True, height=180)
        self.telemetry_blink = ft.Container(
            width=8, height=8, border_radius=4,
            bgcolor="#22C55E",
            animate=ft.animation.Animation(800, "easeInOut"),
        )

        # ── Specs container ref (for border glow) ─────────────────────
        self.specs_container = None

        # ── Nav toggle text ───────────────────────────────────────────
        self.sim_toggle_text = ft.Text("Pause Sim", size=14, color="#333333")

    # ── helpers ────────────────────────────────────────────────────────
    def _nav(self, text, on_click=None, active=False):
        return ft.TextButton(
            content=ft.Text(text, weight="bold" if active else "w400"),
            style=ft.ButtonStyle(
                color={"": "#E50000" if active else "#333333",
                        ft.MaterialState.HOVERED: "#E50000"},
                overlay_color=ft.colors.TRANSPARENT,
            ),
            on_click=on_click
        )

    def _metric(self, label, value_ctrl, icon, color):
        return ft.Column([
            ft.Row([ft.Icon(icon, size=13, color=color),
                    ft.Text(label, size=11, color="#666666", weight="w500")],
                   tight=True, spacing=4),
            value_ctrl
        ], tight=True, spacing=2)

    def _glass(self, content, width=None, padding=20, extra_animate=False):
        kwargs = dict(
            content=content, padding=padding,
            bgcolor=ft.colors.with_opacity(0.3, "white"),
            border_radius=15,
            border=ft.border.all(1, ft.colors.with_opacity(0.5, "white")),
            blur=ft.Blur(15, 15, ft.BlurTileMode.MIRROR),
        )
        if width:
            kwargs["width"] = width
        if extra_animate:
            kwargs["animate"] = ft.animation.Animation(500, "easeOut")
        return ft.Container(**kwargs)

    def _draggable(self, panel_container, left, top):
        """Wrap a plain ft.Container in a draggable GestureDetector."""
        handle = ft.Container(
            content=ft.Row([
                ft.Container(width=36, height=4,
                              bgcolor=ft.colors.with_opacity(0.3, "#888"),
                              border_radius=2)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.only(top=6, bottom=4),
        )
        inner = ft.Column([handle, panel_container], tight=True, spacing=0)

        def on_pan(e: ft.DragUpdateEvent):
            e.control.left = max(0, (e.control.left or 0) + e.delta_x)
            e.control.top  = max(70, (e.control.top  or 0) + e.delta_y)
            e.control.update()

        return ft.GestureDetector(
            content=inner,
            left=left, top=top,
            on_pan_update=on_pan,
            mouse_cursor=ft.MouseCursor.MOVE,
            drag_interval=10,
        )

    # ── window ─────────────────────────────────────────────────────────
    def close_app(self, e):    self.page.window.close()
    def minimize_app(self, e): self.page.window.minimized = True;  self.page.update()
    def maximize_app(self, e):
        self.page.window.maximized = not self.page.window.maximized; self.page.update()
    def toggle_sim(self, e):
        self.is_sim_running = not self.is_sim_running
        self.sim_toggle_text.value = "Resume Sim" if not self.is_sim_running else "Pause Sim"
        self.sim_toggle_text.update()
        self.on_toggle_sim(self.is_sim_running)

    # ── build ──────────────────────────────────────────────────────────
    def build(self):
        # Background image
        bg = ft.Container(
            image_src="light_bg.png", image_fit=ft.ImageFit.COVER,
            left=0, top=0, right=0, bottom=0
        )
        bg_overlay = ft.Container(
            bgcolor=ft.colors.with_opacity(0.15, "black"),
            left=0, top=0, right=0, bottom=0
        )

        # ── Title bar ────────────────────────────────────────────────
        clock_block = ft.Column([
            ft.Row([ft.Icon(ft.icons.ACCESS_TIME, size=14, color="#888888"),
                    self.sim_clock], tight=True, spacing=4),
            self.sim_clock_label,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, spacing=0)

        title_bar_content = ft.Row([
            ft.WindowDragArea(
                content=ft.Container(
                    content=ft.Row([
                        ft.Container(width=20),
                        ft.Image(src="tesla_logo.png", height=100, fit=ft.ImageFit.CONTAIN),
                        ft.Container(width=20),
                        ft.Container(content=clock_block,
                                      padding=ft.padding.symmetric(horizontal=12, vertical=4),
                                      bgcolor=ft.colors.with_opacity(0.15, "#111111"),
                                      border_radius=8),
                    ]),
                    padding=ft.padding.only(top=10, bottom=10),
                ),
                expand=True
            ),
            ft.Container(
                content=ft.Row([
                    self._nav("Dashboard",
                              lambda e: self.on_view_dashboard() if self.on_view_dashboard else None,
                              active=True),
                    self._nav("Charts",    lambda e: self.on_view_charts()),
                    self._nav("Fleet",     lambda e: self.on_view_dashboard() if self.on_view_dashboard else None),
                    self._nav("EV Specs",  lambda e: self.on_view_ev_specs()  if self.on_view_ev_specs  else None),
                    self._nav("AI Report", lambda e: self.on_generate_report(self.report_done)),
                    self._nav("Settings",  lambda e: self.on_open_settings()  if self.on_open_settings  else None),
                    self._nav("Export CSV",lambda e: self.on_export_csv()     if self.on_export_csv     else None),
                    ft.TextButton(
                        content=self.sim_toggle_text,
                        style=ft.ButtonStyle(
                            color={"": "#333333", ft.MaterialState.HOVERED: "#E50000"},
                            overlay_color=ft.colors.TRANSPARENT),
                        on_click=self.toggle_sim
                    ),
                    ft.Container(width=30),
                    ft.IconButton(ft.icons.MINIMIZE,    icon_size=18, icon_color="#333333", on_click=self.minimize_app),
                    ft.IconButton(ft.icons.CROP_SQUARE, icon_size=18, icon_color="#333333", on_click=self.maximize_app),
                    ft.IconButton(ft.icons.CLOSE,       icon_size=18, icon_color="#333333", on_click=self.close_app),
                    ft.Container(width=10),
                ]),
                padding=ft.padding.only(top=10, bottom=10),
            )
        ])

        glass_title_bar = self._glass(title_bar_content, padding=0)
        glass_title_bar.margin = 10

        # ── SPECS panel ──────────────────────────────────────────────
        self.specs_container = self._glass(
            ft.Column([
                ft.Text("Specifications", size=20, weight="w500", color="#111111"),
                ft.Container(height=6),
                ft.Row([self.weather_icon, self.weather_text,
                        ft.Container(expand=True), self.soh_badge]),
                ft.Container(height=12),
                self.bar_demand.control, ft.Container(height=10),
                self.bar_price.control,  ft.Container(height=10),
                self.bar_soc.control,    ft.Container(height=10),
                self.bar_v2g.control,    ft.Container(height=10),
                self.bar_soh.control,
            ], tight=True),
            width=360, padding=25, extra_animate=True
        )

        # ── LOGS panel ───────────────────────────────────────────────
        logs_panel = self._glass(
            ft.Column([
                ft.Row([ft.Icon(ft.icons.TERMINAL, size=18, color="#111111"),
                        ft.Text("SYSTEM LOGS", size=14, weight="w600", color="#111111")]),
                ft.Container(height=10),
                self.log_list,
            ], tight=True),
            width=400, padding=20
        )

        # ── FINANCIALS panel ─────────────────────────────────────────
        fin_panel = self._glass(
            ft.Column([
                ft.Row([ft.Icon(ft.icons.ATTACH_MONEY, size=18, color="#111111"),
                        ft.Text("LIVE FINANCIALS", size=14, weight="w600", color="#111111")]),
                ft.Container(height=12),
                ft.Row([
                    self._metric("V2G Revenue", self.revenue_text, ft.icons.TRENDING_UP,   "#16A34A"),
                    ft.Container(width=20),
                    self._metric("Charge Cost",  self.cost_text,   ft.icons.TRENDING_DOWN, "#E50000"),
                ]),
                ft.Container(height=12),
                ft.Row([
                    self._metric("Net Profit",  self.net_text,    ft.icons.ACCOUNT_BALANCE_WALLET, "#2563EB"),
                    ft.Container(width=20),
                    self._metric("Grid Events", self.events_text, ft.icons.FLASH_ON,               "#F59E0B"),
                ]),
            ], tight=True),
            width=310, padding=20
        )

        # ── TELEMETRY STREAM panel ──────────────────────────────────
        telemetry_panel = self._glass(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.CELL_TOWER, size=18, color="#111111"),
                    ft.Text("TELEMETRY STREAM", size=14, weight="w600", color="#111111"),
                    ft.Container(expand=True),
                    self.telemetry_blink,
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=10),
                self.telemetry_list,
            ], tight=True),
            width=380, padding=20
        )

        # Footer
        footer = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.VERIFIED, size=14,
                         color=ft.colors.with_opacity(0.8, "#111111")),
                ft.Text("Developed by Sasmitha Thejan", size=13,
                         color=ft.colors.with_opacity(0.9, "#111111"),
                         weight="w600"),
            ]),
            bottom=20, right=20
        )

        return ft.Stack(
            controls=[
                bg,
                bg_overlay,
                ft.Column([glass_title_bar]),        # title bar pinned top
                self._draggable(self.specs_container, left=50,  top=110),
                self._draggable(logs_panel,            left=440, top=110),
                self._draggable(fin_panel,             left=440, top=390),
                self._draggable(telemetry_panel,       left=850, top=110),
                footer,
            ],
            expand=True
        )

    # ── AI report ──────────────────────────────────────────────────────
    def report_done(self, result):
        # Parse **bold** markdown syntax into Flet TextSpans
        parts = result.split("**")
        text_spans = []
        for i, part in enumerate(parts):
            if i % 2 == 1:
                text_spans.append(ft.TextSpan(part, ft.TextStyle(weight="bold", color="#111111")))
            else:
                text_spans.append(ft.TextSpan(part, ft.TextStyle(weight="w500", color="#333333")))

        self.page.open(ft.AlertDialog(
            content=self._glass(
                ft.Column([
                    ft.Row([ft.Image(src="tesla_logo.png", height=40, fit=ft.ImageFit.CONTAIN, color="#E50000"),
                            ft.Text("AI DIAGNOSTIC REPORT", size=18,
                                     weight="w600", color="#111111")]),
                    ft.Container(height=15),
                    ft.ListView(controls=[
                        ft.Text(spans=text_spans, size=14, selectable=True)
                    ], expand=True, auto_scroll=False)
                ], tight=False),
                width=700, padding=30
            ),
            bgcolor=ft.colors.TRANSPARENT, content_padding=0
        ))

    # ── update_data ────────────────────────────────────────────────────
    def update_data(self, data):
        t = data.get("time", 0.0)
        self.sim_clock.value = f"{int(t):02d}:{int((t % 1) * 60):02d}"
        self.sim_clock.update()

        self.bar_demand.set_progress(data['demand'] / 120.0, f"{data['demand']:.1f}")
        p = data['price']
        self.bar_price.set_progress((p - 0.10) / 0.30, f"${p:.2f}")
        self.bar_soc.set_progress(data['soc'] / 100.0, f"{data['soc']:.1f}")
        v2g = max(0, data['v2g_flow'])
        self.bar_v2g.set_progress(v2g / 10.0, f"{v2g:.1f}")
        soh = data.get('soh', 100.0)
        self.bar_soh.set_progress(soh / 100.0, f"{soh:.1f}")

        # SoH glow
        if soh < 90.0:
            self.soh_badge.visible = True
            self.soh_badge.content.value = "! BATTERY DEGRADED"
            self.soh_badge.bgcolor = "#E50000"
            self.specs_container.border = ft.border.all(2, ft.colors.with_opacity(0.7, "#E50000"))
            self.specs_container.shadow = ft.BoxShadow(spread_radius=2, blur_radius=15,
                                                        color=ft.colors.with_opacity(0.3, "#E50000"))
        elif soh < 95.0:
            self.soh_badge.visible = True
            self.soh_badge.content.value = "! SoH WARNING"
            self.soh_badge.bgcolor = "#F59E0B"
            self.specs_container.border = ft.border.all(2, ft.colors.with_opacity(0.6, "#F59E0B"))
            self.specs_container.shadow = ft.BoxShadow(spread_radius=1, blur_radius=12,
                                                        color=ft.colors.with_opacity(0.25, "#F59E0B"))
        else:
            self.soh_badge.visible = False
            self.specs_container.border = ft.border.all(1, ft.colors.with_opacity(0.5, "white"))
            self.specs_container.shadow = None
        self.specs_container.update()
        self.soh_badge.update()

        self.weather_text.value = f"Weather: {data.get('cloud_cover', 0.0):.0f}% Cloud Cover"
        self.weather_text.update()

        # Financials
        earn = data.get("earnings", 0.0)
        cost = data.get("cost",     0.0)
        net  = data.get("net",      0.0)
        self.revenue_text.value = f"${earn:.2f}"
        self.cost_text.value    = f"${cost:.2f}"
        if net >= 0:
            self.net_text.value = f"+${net:.2f}"; self.net_text.color = "#16A34A"
        else:
            self.net_text.value = f"-${abs(net):.2f}"; self.net_text.color = "#E50000"
        self.events_text.value = str(data.get("grid_support_events", 0))
        self.revenue_text.update()
        self.cost_text.update()
        self.net_text.update()
        self.events_text.update()

    def log_message(self, message):
        self.log_list.controls.append(
            ft.Text(message, size=12, color="#333333",
                    font_family="Courier New", weight="w500")
        )
        if len(self.log_list.controls) > 100:
            self.log_list.controls.pop(0)
        if self.page:
            self.log_list.update()

    def log_telemetry(self, packet_str: str):
        """Append a raw JSON telemetry string to the telemetry stream panel."""
        self.telemetry_list.controls.append(
            ft.Text(
                packet_str, size=10, color="#333333",
                font_family="Courier New", weight="w500",
                no_wrap=True,
            )
        )
        # Cap at 50 visible entries
        if len(self.telemetry_list.controls) > 50:
            self.telemetry_list.controls.pop(0)
        # Blink indicator
        if self.telemetry_blink.bgcolor == "#22C55E":
            self.telemetry_blink.bgcolor = ft.colors.with_opacity(0.3, "#22C55E")
        else:
            self.telemetry_blink.bgcolor = "#22C55E"
        if self.page:
            try:
                self.telemetry_list.update()
                self.telemetry_blink.update()
            except Exception:
                pass  # Swallow race conditions during rapid updates
