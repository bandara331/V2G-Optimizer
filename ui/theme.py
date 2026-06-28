import flet as ft

# Cyberpunk / Tesla Energy Theme Colors
BG_COLOR = "#0F172A"       # Dark slate blue background
PANEL_BG = "#1E293B"       # Slightly lighter for panels
ACCENT_CYAN = "#00F0FF"    # Neon Cyan
ACCENT_MAGENTA = "#FF003C" # Neon Magenta
ACCENT_GREEN = "#39FF14"   # Neon Green
TEXT_MAIN = "#F8FAFC"      # White/off-white text
TEXT_MUTED = "#94A3B8"     # Muted gray text

def get_theme():
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            background=BG_COLOR,
            surface=PANEL_BG,
            primary=ACCENT_CYAN,
            secondary=ACCENT_GREEN,
            error=ACCENT_MAGENTA,
            on_background=TEXT_MAIN,
            on_surface=TEXT_MAIN,
        ),
        font_family="Inter, Roboto, sans-serif"
    )

def glass_container(content, padding=20, width=None, height=None, expand=False):
    """Returns a container with a glassmorphism effect."""
    return ft.Container(
        content=content,
        padding=padding,
        width=width,
        height=height,
        expand=expand,
        bgcolor=ft.colors.with_opacity(0.6, PANEL_BG),
        border_radius=15,
        border=ft.border.all(1, ft.colors.with_opacity(0.1, TEXT_MAIN)),
        blur=ft.Blur(10, 10, ft.BlurTileMode.MIRROR)
    )
