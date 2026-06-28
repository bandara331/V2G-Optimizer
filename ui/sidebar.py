# pyrefly: ignore [missing-import]
import flet as ft
from ui.theme import glass_container, TEXT_MUTED, ACCENT_CYAN, ACCENT_GREEN, ACCENT_MAGENTA

class Sidebar(ft.UserControl):
    def __init__(self):
        super().__init__()
        
        # UI Elements
        self.time_text = ft.Text("00:00", size=24, weight="bold", color=ACCENT_CYAN)
        self.demand_text = ft.Text("0.0 kW", size=20, weight="w600")
        self.price_text = ft.Text("$0.00/kWh", size=20, weight="w600")
        
        self.soc_bar = ft.ProgressBar(value=0.5, color=ACCENT_GREEN, bgcolor=ft.colors.with_opacity(0.2, ACCENT_GREEN), height=10)
        self.soc_text = ft.Text("50.0%", size=20, weight="w600", color=ACCENT_GREEN)
        
        self.action_text = ft.Text("IDLE", size=18, weight="bold", color=TEXT_MUTED)
        
    def build(self):
        return glass_container(
            width=250,
            expand=True,
            content=ft.Column(
                controls=[
                    ft.Text("SYSTEM MONITOR", size=14, weight="bold", color=TEXT_MUTED),
                    ft.Divider(color=ft.colors.with_opacity(0.2, "white")),
                    
                    ft.Container(height=10),
                    ft.Text("Simulation Time", size=12, color=TEXT_MUTED),
                    self.time_text,
                    
                    ft.Container(height=20),
                    ft.Text("Grid Load", size=12, color=TEXT_MUTED),
                    self.demand_text,
                    
                    ft.Container(height=20),
                    ft.Text("Electricity Price", size=12, color=TEXT_MUTED),
                    self.price_text,
                    
                    ft.Container(height=20),
                    ft.Text("EV State of Charge", size=12, color=TEXT_MUTED),
                    self.soc_text,
                    self.soc_bar,
                    
                    ft.Container(height=20),
                    ft.Text("Current Action", size=12, color=TEXT_MUTED),
                    self.action_text,
                ]
            )
        )

    def format_time(self, time_hour):
        h = int(time_hour)
        m = int((time_hour - h) * 60)
        return f"{h:02d}:{m:02d}"

    def update_data(self, data):
        self.time_text.value = self.format_time(data['time'])
        
        demand = data['demand']
        self.demand_text.value = f"{demand:.1f} kW"
        
        price = data['price']
        self.price_text.value = f"${price:.3f}/kWh"
        if price > 0.25:
            self.price_text.color = ACCENT_MAGENTA
        elif price < 0.15:
            self.price_text.color = ACCENT_GREEN
        else:
            self.price_text.color = "white"
            
        soc = data['soc']
        self.soc_text.value = f"{soc:.1f}%"
        self.soc_bar.value = soc / 100.0
        if soc < 25:
            self.soc_bar.color = ACCENT_MAGENTA
            self.soc_text.color = ACCENT_MAGENTA
        else:
            self.soc_bar.color = ACCENT_GREEN
            self.soc_text.color = ACCENT_GREEN
            
        action = data['action']
        self.action_text.value = action
        if action == "CHARGE":
            self.action_text.color = ACCENT_GREEN
        elif action == "DISCHARGE":
            self.action_text.color = ACCENT_MAGENTA
        else:
            self.action_text.color = TEXT_MUTED
            
        self.update()
