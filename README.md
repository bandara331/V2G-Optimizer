# ⚡ V2G Fleet Optimizer — Desktop Simulator

A real-time **Vehicle-to-Grid (V2G)** fleet optimization simulator built with Python and [Flet](https://flet.dev/). Simulates a fleet of 4 electric vehicles intelligently charging and discharging to support the power grid, with live telemetry, thermal physics, LLM-generated executive reports, and a full-featured HUD dashboard.

---

## 🚀 Features

- **Smart Optimizer** — Rule-based V2G decision engine that triggers `CHARGE`, `DISCHARGE`, or `IDLE` actions based on real-time electricity price and grid demand thresholds.
- **Fleet Manager** — Independent per-unit EV state with priority-based dispatch scoring (SoC, SoH, temperature), thermal physics simulation (throttling & emergency disconnect), and micro-degradation modelling.
- **Live 10Hz Telemetry Stream** — Per-unit JSON telemetry packets (voltage, current, temperature, SoC, SoH, status) emitted at 10 Hz in a parallel async task.
- **Real-time HUD Dashboard** — Custom-built frameless desktop UI with:
  - Live grid demand & electricity price gauges
  - Fleet SoC / SoH indicators
  - V2G energy flow diagram
  - Per-unit fleet dashboard with thermal status
  - EV spec cards
  - Configurable simulation settings modal
  - Scrollable system event log
- **Weather Integration** — Fetches live cloud cover data from [Open-Meteo](https://open-meteo.com/) to influence grid demand simulation.
- **AI Executive Report** — Uses **Groq (Llama 3.1-8B)** to generate a professional energy-systems analyst report from session logs.
- **CSV Export** — Export full telemetry history to `v2g_telemetry.csv` with a single click.

---

## 🏗️ Architecture

```
V2G Fleet Optimizer
│
├── main.py              # Flet app entry point — wires UI, simulator & callbacks
├── simulator.py         # Async simulation engine — environment, timing, logging
├── optimizer.py         # V2GOptimizer — smart charge/discharge decision logic
├── fleet_model.py       # FleetManager + EVUnit — per-unit state, thermal physics, telemetry
├── llm_reporter.py      # Groq LLM integration — AI executive report generation
│
├── ui/
│   ├── hud.py           # Main HUD layout (frameless window)
│   ├── dashboard.py     # Chart modal (historical trends)
│   ├── fleet_dashboard.py  # Per-unit fleet status cards
│   ├── energy_flow.py   # Animated V2G energy flow diagram
│   ├── ev_specs.py      # EV specification cards
│   ├── settings_modal.py   # Runtime settings (thresholds, speed)
│   ├── sidebar.py       # Sidebar navigation
│   └── theme.py         # App-wide Flet theme
│
└── assets/              # UI assets (background, car images, animations)
```

---

## ⚙️ How the Optimizer Works

The `V2GOptimizer` makes per-tick decisions based on two configurable price thresholds:

| Condition | Action |
|-----------|--------|
| Price ≥ `high_price_threshold` ($0.25/kWh) **and** demand > 50 kW | `DISCHARGE` — Feed energy to the grid |
| Price ≤ `low_price_threshold` ($0.15/kWh) | `CHARGE` — Cheap off-peak charging |
| Otherwise | `IDLE` — Hold current state |

Each decision is delegated to the **FleetManager** which distributes energy across individual EV units using a **priority dispatch score**:

```
Score = (SoC × 0.6) + (SoH × 0.3) − (Temperature × 0.1)
```

Units with the highest score are dispatched first. Thermal limits are enforced automatically:
- **> 45°C** → Throttle to 50% discharge rate
- **> 55°C** → Emergency disconnect; auto-reconnect once cooled

---

## 🛠️ Installation

### Prerequisites
- Python 3.10+

### 1. Clone the repository
```bash
git clone https://github.com/bandara331/V2G-Optimizer.git
cd V2G-Optimizer
```

### 2. Create a virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
Create a `.env` file in the project root:
```
GROQ_API_KEY="your_groq_api_key_here"
```
> Get a free API key at [console.groq.com](https://console.groq.com)

---

## ▶️ Running the Simulator

```bash
python main.py
```

The desktop window will launch automatically. The simulation starts immediately — use the HUD controls to pause, adjust settings, generate reports, or export telemetry.

---

## 🖥️ UI Controls

| Control | Description |
|---------|-------------|
| **Start / Stop** | Toggle the V2G simulation |
| **View Charts** | Open historical trend charts |
| **Fleet Dashboard** | Per-unit EV status with thermal indicators |
| **EV Specs** | Battery & hardware specifications per unit |
| **Settings** | Adjust price thresholds, charge/discharge rates, simulation speed |
| **Generate Report** | AI-powered executive summary via Groq LLM |
| **Export CSV** | Save full telemetry history to `v2g_telemetry.csv` |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `flet==0.23.2` | Desktop UI framework |
| `groq` | Groq API client for LLM report generation |
| `python-dotenv==1.0.1` | `.env` file support for API key management |
| `httpx` | Async HTTP client for weather API calls |

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes (for AI report) | Groq API key for Llama 3.1 report generation |

> **Note:** The `.env` file is listed in `.gitignore` and will never be committed to the repository.

---

## 📄 License

This project is open source. Feel free to fork, modify, and build upon it.

---

## 🙏 Acknowledgements

- [Flet](https://flet.dev/) — Flutter-powered Python desktop UI framework
- [Groq](https://groq.com/) — Ultra-fast LLM inference (Llama 3.1-8B)
- [Open-Meteo](https://open-meteo.com/) — Free weather forecast API
