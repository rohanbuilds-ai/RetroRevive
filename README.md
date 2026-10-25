# RetroRevive — Hammurabi Reimagined

**Confluence Buildathon 2026 — Track: Resurrections**

RetroRevive is a modernization of the classic 1978 computer game **HAMURABI**, originally edited and published by David H. Ahl in *BASIC Computer Games: Microcomputer Edition* (Creative Computing / Workman Publishing).

RetroRevive delivers a **dual-experience**:
1. **Desktop Graphical Edition (`ui_pygame.py`):** A fully animated, visual kingdom-management game powered by Pygame. Features an ancient Sumerian world with an animated Euphrates river, Ziggurat of Ur, mudbrick granary silos, citizens, celestial day-night cycles, procedural 8-bit sound synthesis, steppers, and two rich gameplay modes (Classic 1978 & Enhanced Modern).
2. **Terminal CLI Edition (`main.py`):** A faithful, standalone command-line modernization built strictly with the Python standard library, complete with optional 7-bit ASCII animations and ANSI color themes.

---

## 1. Quick Start Guide

### System Prerequisites
- **Python 3.10+** (verified on Python 3.13.7 64-bit on Windows)
- **Standard Library** for core simulation and CLI game (zero third-party dependencies required for CLI)
- **Pygame 2.6+** for the graphical desktop interface

### Environment Setup (Desktop Edition)
Create and activate a virtual environment, then install Pygame:
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Or on Linux / macOS:
# source .venv/bin/activate

# Install the pinned desktop dependency
pip install -r requirements-ui.txt
```

### Launch the Desktop Graphical Game
From the repository root:
```bash
python ui_pygame.py
# Or directly via the virtual environment:
.venv\Scripts\python.exe ui_pygame.py
```

### Launch the Terminal CLI Game (Zero Dependencies)
```bash
# Animated terminal mode with color and ASCII landscapes
python main.py

# Pure classic 1978 text terminal mode
python main.py --no-animate
```

### Run the Automated Test Suite
```bash
python -m unittest discover -v
# Runs all 50 tests across test_game.py, test_modern.py, and test_ui.py
```

### Run Automated Headless Visual UI Verification
```bash
python verify_ui.py
# Renders all screens and responsive window sizes, saving verification screenshots to docs/screenshots/
```

---

## 2. Dual Gameplay Modes

RetroRevive cleanly separates historical fidelity from modern convenience:

### Mode 1: Classic 1978 Mode
- **100% Faithful Simulation:** Strictly executes the verified 1978 Microsoft BASIC source code formulas.
- **Authoritative Engine (`game_logic.py`):** Exact mathematical starting state (100 population, 1,000 acres, 2,800 bushels), land pricing ($17$–$26$ bu/acre), immigration curve, 40% rat infestation odds, 20% plague chance, strict labor constraint ($D < 10P$), and Ahl's iconic 4-tier final evaluation (Fink, Nero, Assassination, Charlemagne).
- **Safe Input Protection:** Entering negative values safely triggers steward dismissal without crashing; malformed text triggers `?REDO FROM START`.

### Mode 2: Enhanced Modern Mode
- **Interactive 5-Step Tutorial:** Teaches the three pillars of ancient Sumerian economy (population workforce, land territory, and grain currency).
- **The Royal Council of Sumeria (Contextual Advisors):**
  - **The Vizier:** Evaluates macroeconomic stability, famine risk, and population growth.
  - **The Granary Master:** Analyzes food reserves, recommends minimum rations (20 bu/person), and highlights rat loss history.
  - **The Surveyor:** Evaluates current land trading prices (`VERY CHEAP`, `CHEAP`, `FAIR`, `EXPENSIVE`) and workforce planting capacity.
  - *One-click "APPLY ADVICE" autofills optimal, safe turn decisions into your decree inputs.*
- **4 Scenario Challenges:**
  1. *The Great Drought:* 5-year survival challenge with depleted starting grain stores ($\ge 2,500$ bu victory).
  2. *The Population Boom:* 7-year expansion challenge managing heavy immigration ($\ge 1,300$ ac, $\ge 120$ pop).
  3. *The Granary Defense:* 6-year stockpile challenge fighting aggressive desert rodents ($\ge 3,500$ bu).
  4. *Empire of Babylon:* 10-year master challenge to build a thriving ancient empire ($\ge 1,400$ ac, $\ge 130$ pop).
- **Chronicle Event Log:** Retains a historical record of all prior year decrees, harvest yields, rat attacks, and citizen counts.
- **Safe JSON Save & Resume:** Save your reign at any time and resume seamlessly.

---

## 3. Visual UI & Audio Showcase

RetroRevive's desktop interface is built with procedural pixel rendering and sound synthesis:
- **Procedural Sumerian World (`ui_world.py`):**
  - Atmospheric desert sky with moving clouds and a pulsing celestial sun.
  - Stepped Ziggurat of Ur with animated flame braziers.
  - Sine-wave flowing Euphrates river with shimmering water highlights.
  - Mudbrick granary silos with real-time grain fill level gauges.
  - Animated citizen villagers walking along the riverfront.
  - Dynamic particle emitters for harvest chaff, scampering granary rats, and victory fireworks.
- **Procedural 8-Bit Audio Synthesis (`ui_theme.py`):**
  - Generates authentic 16-bit mono PCM waveforms in memory via standard `math.sin` and `struct`.
  - Audio cues for button clicks, coin purchases, harvest chimes, famine warnings, and royal bells.
  - Requires zero external `.wav` or `.mp3` assets and includes a one-click mute toggle.
- **Fluid Layout & Resolution Independence:**
  - Designed on an internal $1280 \times 720$ logical canvas with aspect-ratio letterboxing.
  - Automatically scales cleanly to $1366 \times 768$, $1920 \times 1080$, $4\text{K}$, or arbitrary window sizes.
  - Intuitive input widgets provide direct typing, quick-adjust steppers (`-100`, `-10`, `+10`, `+100`), `MAX`, and `CLR` buttons.

### Verified Screenshot Gallery
Generated programmatically via [`verify_ui.py`](file:///e:/GitHub%20Projects/RetroRevive/verify_ui.py) in [`docs/screenshots/`](file:///e:/GitHub%20Projects/RetroRevive/docs/screenshots):
- `screenshot_main_menu.png`: Title screen with mode selection, scenario challenges, tutorial, and resume button.
- `screenshot_classic_gameplay.png`: Annual royal report, animated world, resource indicators, and allocation decree inputs.
- `screenshot_enhanced_advisors.png`: The Royal Council of Sumeria dialog with word-wrapped counsel and one-click decree autofill.
- `screenshot_scenarios.png`: 4 scenario challenge cards with objectives and difficulty tiers.
- `screenshot_tutorial.png`: 5-step interactive instructional walkthrough.
- `screenshot_game_over.png`: Historical 10-year governance evaluation with metric breakdowns and rating banner.
- `screenshot_scale_1366x768.png` & `screenshot_scale_1920x1080.png`: Responsive aspect-ratio scaling verification.

---

## 4. Architecture & Codebase Map

```
RetroRevive/
├── ui_pygame.py             # Desktop graphical application (Pygame loop, event routing, modals, scaling)
├── ui_theme.py              # Visual design system: Sumerian palette, fonts, PCM audio synthesizer, UI widgets
├── ui_world.py              # Living animated world: ziggurat, river, silos, villagers, clouds, particle emitters
├── modern_game_logic.py     # Modern engine: Scenarios, Royal Advisors, Chronicle log, JSON save/load
├── game_logic.py            # Authoritative 1978 domain engine: state transitions, exact formulas, validations
├── presentation.py          # Terminal presentation fallback: 7-bit ASCII landscapes, colors, and transitions
├── main.py                  # CLI application entry point: terminal user loop, safe prompt parsing
├── test_game.py             # Automated unit tests for classic engine and terminal presentation (26 tests)
├── test_modern.py           # Automated unit tests for modern scenarios, advisors, and save/resume (7 tests)
├── verify_ui.py             # Automated headless visual test script and screenshot generator
├── requirements-ui.txt      # Pygame dependency pin (pygame==2.6.1)
├── RULES.md                 # Canonical rules specification with line-by-line historical citations
├── INTERFACE.md             # Complete component interfaces, random provider design, and architecture
├── BUILD_PLAN.md            # Implementation roadmap, milestone checklists, and acceptance criteria
└── docs/
    ├── scenarios.md         # 6 documented, repeatable gameplay scenarios and strategies
    ├── compatibility.md     # Mathematical verification matrix, historical quirks, and primary citations
    └── screenshots/         # Automated visual verification capture repository
```

---

## 5. Automated Verification & Quality Assurance

The automated test suite contains **50 tests** passing with 0 errors and 0 failures:

| Test Module | Test Count | Scope Verified |
|---|---|---|
| `test_game.py` | 26 tests | Initial state, land pricing, buy/sell/feed/plant validations, harvest yield, rat parity math, immigration formula, plague 50% halving, underfeeding, 45% annual impeachment, overfeeding statistical quirk, all 4 evaluation tiers, full 10-year deterministic simulation, safe input recovery, and terminal presentation routines. |
| `test_modern.py` | 7 tests | Contextual advisor calculations, market price ratings, chronicle log persistence across years, scenario definitions, scenario victory/defeat conditions, JSON save and load roundtrip, corrupt save recovery, and nonexistent file handling. |
| `test_ui.py` | 17 tests | UI widgets, steppers, buttons, modal dialogs, audio synthesizer waveform generation, world renderer tick updates, particle emitters, screen state routing, input re-entrancy, and letterbox coordinate transformations. |

Run tests:
```bash
python -m unittest discover -v
```

---

## 6. Terminal CLI Options (`main.py`)

For headless servers or environments without a graphical display, the terminal version provides comprehensive command-line controls:

| Flag | Description |
|---|---|
| *(default)* | Auto-detects terminal capabilities, displaying ASCII scenes and ANSI colors |
| `--animate` | Forces ASCII city scene rendering and harvest/rat transitions |
| `--no-animate` | Disables ASCII graphics (pure classic 1978 terminal output) |
| `--color {auto,always,never}` | Controls ANSI terminal color sequences (default: auto) |
| `--speed {fast,normal,slow}` | Animation playback speed |
| `--seed <N>` | Runs with a fixed random seed for 100% reproducible outcomes |
| `--relaxed` | Permits modern boundary tolerances ($D \le 10P$ and $Q \le A$) |
| `--no-sound` | Suppresses terminal bell characters (`\a`) |

Example:
```bash
python main.py --animate --speed fast --seed 42 --no-sound
```

---

## 7. Historical Provenance & Citations

- **Doug Dyment:** Original author of *The Sumer Game* (FOCAL, 1968) on the DEC PDP-8 at Digital Equipment Corporation.
- **David H. Ahl:** Author of *101 BASIC Computer Games* (1973) and *BASIC Computer Games: Microcomputer Edition* (1978), who adapted the game to Microsoft BASIC and created the celebrated 10-year performance evaluation system.
- **Digital Preservation Archives:** Special recognition to Tristano Ajmone (*The Hamurabi Collection*) and AtariArchives.org for maintaining verified historical source listings.
