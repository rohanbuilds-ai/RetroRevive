# RetroRevive — Classic Computer Games Platform

**Confluence Buildathon 2026 — Track: Resurrections**  
**Repository:** [https://github.com/rohanbuilds-ai/RetroRevive.git](https://github.com/rohanbuilds-ai/RetroRevive.git)

RetroRevive brings classic computer games from the 1970s into the modern era through polished desktop graphics, animation, responsive controls, interactive tutorials, and optional modern enhancements—while strictly preserving original gameplay in verified Classic Modes.

Built as an extensible platform, RetroRevive currently features:
1. **Central Graphical Game Library (`retrorevive.py`):** An arcade/retro-styled desktop hub featuring game catalog cards, category filters, real-time search, detail modals, and seamless launch/return routing.
2. **Hammurabi: Reimagined (`ui_pygame.py`):** The iconic 1978 Sumerian kingdom simulation featuring an animated Mesopotamian landscape, Euphrates river, Ziggurat of Ur, Decree Preview ledger, Royal Advisors, and Scenarios.
3. **23 Matches (`games/23_matches/`):** The timeless mathematical subtraction strategy game (Nim) by Bob Albrecht, featuring an animated wooden matchstick board, burning match effects, human-vs-computer play, and dual AI modes.
4. **Lunar Lander (`games/lunar_lander/`):** Jim Storer's 1969/1978 Apollo 11 lunar excursion module (LEM) descent simulation featuring 5th-order Taylor series rocket physics, animated LEM with gimbaling thrusters, particle exhaust flames, comprehensive telemetry dashboard, and auto-hover assist.
5. **Coming Soon Index:** Metadata, provenance, and rules for upcoming classics: *Super Star Trek* (1974) and *The Oregon Trail* (1971).
6. **Standalone Terminal CLI Fallback (`main.py --cli`):** Zero-dependency pure standard library CLI for running all three games in traditional text terminals.

---

## 1. Quick Start Guide

### System Prerequisites
- **Python 3.10+** (tested and verified on Python 3.13.7 64-bit on Windows)
- **Standard Library** for core simulation rules and CLI gameplay (zero external dependencies required)
- **Pygame 2.6+** for the graphical desktop interface

### Installation
Clone the repository and set up the virtual environment:
```powershell
# Clone repository
git clone https://github.com/rohanbuilds-ai/RetroRevive.git
cd RetroRevive

# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Or on Linux / macOS:
# source .venv/bin/activate

# Install Pygame for the desktop interface
pip install -r requirements-ui.txt
```

---

## 2. Launch Commands

### Launch the RetroRevive Game Library (Recommended)
```powershell
.venv\Scripts\python.exe main.py
# Or directly:
.venv\Scripts\python.exe retrorevive.py
```
*Optional launcher flags:*
- Start in fullscreen: `.venv\Scripts\python.exe main.py --fullscreen`
- Launch Hammurabi directly: `.venv\Scripts\python.exe main.py --hammurabi`
- Launch 23 Matches directly: `.venv\Scripts\python.exe main.py --matches`
- Launch Lunar Lander directly: `.venv\Scripts\python.exe main.py --lander`

### Launch Standalone Terminal CLI (Zero Dependencies)
```powershell
# Hammurabi historical terminal mode:
.venv\Scripts\python.exe main.py --cli --no-animate --seed 42

# 23 Matches historical terminal mode:
.venv\Scripts\python.exe main.py --matches --cli

# Lunar Lander historical terminal mode:
.venv\Scripts\python.exe main.py --lander --cli
```

---

## 3. The Playable Games

### Game 1: Hammurabi: Reimagined (1978)
- **Historical Provenance:** Authored by Doug Dyment (1968, PDP-8 FOCAL) and ported to BASIC by David H. Ahl (*101 BASIC Computer Games*, 1973; *BASIC Computer Games*, 1978).
- **Core Mechanics:** Manage ancient Sumeria over a 10-year term. Allocate grain between feeding citizens (20 bu/person), planting seed (1 bu/acre, 1 person tends 10 acres), and trading land ($17$–$26$ bu/acre). Starving over 45% in any year triggers immediate impeachment.
- **Available Modes:**
  - **Classic 1978 Mode:** 100% faithful to the original Creative Computing BASIC rules, rat infestation timing, immigration curve, and 4-tier final evaluation (Nero, Fink, Assassination, Charlemagne).
  - **Enhanced Mode:** Adds the Royal Council of Advisors (Grand Vizier, Royal Agronomist, High Treasurer) with one-click "APPLY ADVICE", 4 historical Scenario Challenges (The Great Drought, The Golden Era, Barbarian Incursion, Plague & Pestilence), Chronicle Log, and save/resume.

### Game 2: 23 Matches (1978)
- **Historical Provenance:** Authored by Bob Albrecht (*People's Computer Company*, 1973) and published in *BASIC Computer Games* (1978, Ahl, pp. 177–178, game #93).
- **Core Mechanics:** 23 matchsticks start on the table. The human player and computer alternate turns removing 1, 2, or 3 matches. You cannot remove more matches than remain. Whichever player is forced to take the very last match loses (Misère Nim rules).
- **Available AI Modes:**
  - **1978 Albrecht AI:** Replicates the historical rule where the computer takes $4 - Z$ matches (where $Z$ is your move). If the player knows the trick and takes 2 matches on the opening turn ($23 - 2 = 21$), the player can force a win!
  - **Master Mind AI (Optimal Modular Nim):** Mathematically optimal AI that calculates modular remainder $r = (N - 1) \bmod 4$ and leaves you in a losing position at every turn.

### Game 3: Lunar Lander (1978)
- **Historical Provenance:** Authored by Jim Storer (Lexington High School, Autumn 1969 in FOCAL-69) and published in *101 BASIC Computer Games* (DEC, 1973) and *BASIC Computer Games* (1978, pp. 106–108).
- **Core Mechanics:** Pilot the Apollo 11 lunar module (LEM) down to Tranquility Base from 120 miles altitude falling at 3,600 MPH (1.0 mi/s) with 16,500 lbs of fuel. Set engine burn rates ($0$–$200$ lbs/sec) over 10-second cycles. Governed by 5th-order Taylor series numerical integration of Tsiolkovsky's rocket equation.
- **Landing Evaluation Tiers:**
  - $\le 1.2\text{ MPH}$: Perfect Landing! (Lucky)
  - $1.2 - 10.0\text{ MPH}$: Good Landing (Could be better)
  - $10.0 - 60.0\text{ MPH}$: Craft Damage... Stranded until rescue
  - $> 60.0\text{ MPH}$: Fatal Crash... Leaves a crater $W \times 0.227\text{ feet}$ deep.
- **Flight Features:** Interactive burn rate presets (`0`, `50`, `100`, `150`, `MAX 200`), adjustment steppers (`-25`, `-10`, `+10`, `+25`), one-click **AUTO-HOVER** equilibrium calculation, and flight telemetry dashboard.

---

## 4. Platform Architecture & Extensibility

RetroRevive is architected to allow adding new retro games cleanly without modifying existing game logic or rewriting the display system:

```
RetroRevive/
├── main.py                     # Universal launcher & CLI dispatcher
├── retrorevive.py              # Graphical Game Library Hub
├── game_registry.py            # Central catalog metadata & search
├── ui_theme.py                 # Shared typography, palettes, widgets, audio
├── ui_pygame.py                # Hammurabi desktop game
├── game_logic.py               # Hammurabi 1978 pure Python engine
├── modern_game_logic.py        # Hammurabi enhanced logic & persistence
├── games/
│   ├── 23_matches/
│   │   ├── engine.py           # 23 Matches pure Python rule engine & AI
│   │   ├── app.py              # 23 Matches Pygame matchstick board
│   │   └── test_engine.py      # Automated tests for 23 Matches (16 tests)
│   └── lunar_lander/
│       ├── engine.py           # Lunar Lander pure Python simulation & physics
│       ├── app.py              # Lunar Lander Pygame Apollo LEM & HUD
│       └── test_engine.py      # Automated tests for Lunar Lander (17 tests)
├── test_game.py                # Hammurabi core unit tests (26 tests)
├── test_modern.py              # Hammurabi enhanced unit tests (7 tests)
├── test_ui.py                  # Hammurabi UI unit tests (27 tests)
├── test_platform.py            # Platform hub, registry, and UI integration tests (24 tests)
├── verify_ui.py                # Visual screenshot verification script
└── docs/
    ├── platform-architecture.md# Comprehensive architecture documentation
    ├── game-sources.md         # Historical provenance and licensing
    ├── lunar-lander-rules.md   # Mathematical derivation, physics & tiers
    └── screenshots/            # Verified screenshots across resolutions
```

### Adding a New Game in 3 Steps
1. Create `games/<game_id>/engine.py` using only the Python standard library, with automated tests in `test_engine.py`.
2. Create `games/<game_id>/app.py` taking `shared_window` and `on_exit_to_library` callback.
3. Register the game metadata in `game_registry.py`.

See [`docs/platform-architecture.md`](file:///e:/GitHub%20Projects/RetroRevive/docs/platform-architecture.md) for complete technical documentation.

---

## 5. Automated Testing & Verification

RetroRevive enforces rigorous test isolation across core domain engines, modern additions, UI state transitions, and platform navigation.

### Run All 117 Automated Unit Tests
```powershell
.venv\Scripts\python.exe -m unittest discover -v
```
**Test Suite Breakdown (117 Tests Total):**
- `test_game.py`: **26 tests** (Historical formulas, land prices, harvest, rat infestation, safe prompt recovery, evaluation tiers).
- `test_modern.py`: **7 tests** (Royal Advisors, Chronicle Log, Scenarios, JSON save/resume roundtrip).
- `test_ui.py`: **27 tests** (Letterbox scaling, Decree Preview math, numeric steppers, text entry, keyboard navigation, modal focus).
- `games.23_matches.test_engine`: **16 tests** (Initial state, bounds checking, integer validation, Misère termination, Albrecht AI, Optimal AI, repeatable scenarios).
- `games.lunar_lander.test_engine`: **17 tests** (Initial LEM state, burn rate validation, 5th-order Taylor series deceleration, free-fall under gravity, touchdown interpolation, 4 landing outcome tiers, crater depth formula).
- `test_platform.py`: **24 tests** (Game Registry catalog queries, category filters, substring search, card cycling, details modal, launch/return lifecycle, 23 Matches UI interaction, Lunar Lander telemetry and controls).

### Run Automated Headless Visual UI Verification
```powershell
.venv\Scripts\python.exe verify_ui.py
```
Generates 15 verified screenshots in `docs/screenshots/` covering the platform library, game details modal, 23 Matches gameplay, 23 Matches victory, Lunar Lander flight, Lunar Lander touchdown modal, Lunar Lander crash crater, Hammurabi screens, and multi-resolution scaling ($1366\times768$ and $1920\times1080$).

---

## 6. Controls & Accessibility

### Platform Hub Controls
- `[1]`: Quick-launch Hammurabi
- `[2]`: Quick-launch 23 Matches
- `[3]`: Quick-launch Lunar Lander
- `[←] / [→]`: Cycle selected game card
- `[Enter] / [Space]`: Launch selected game (or open details if coming soon)
- `[D]`: Open Game Details modal
- `[S]`: Focus search bar (type query to filter games in real time)
- `[Esc]`: Clear search / close modal / quit application

### Hammurabi Controls
- `[Tab] / [Shift+Tab]`: Cycle decree input fields
- `[0-9]`: Direct typing of bushels and acres
- `[+] / [-]`: Interactive stepper buttons ($+1$, $+10$, $+100$, Clear)
- `[R]`: Reset rations to sustainable baseline ($20 \times \text{population}$)
- `[Enter]`: Enact annual decree

### 23 Matches Controls
- `[1]`, `[2]`, `[3]`: Take 1, 2, or 3 matches
- Clickable action buttons with dynamic disabling when remaining matches $< 3$
- Hoverable visual matchsticks with ember glow
- `[Esc]`: Return to RetroRevive Game Library

### Lunar Lander Controls
- `[0]`, `[50]`, `[100]`, `[150]`, `[200]`: Direct burn presets
- `[-25]`, `[-10]`, `[+10]`, `[+25]`: Quick throttle adjustment steppers
- `[AUTO-HOVER]`: Automatically calculate fuel burn rate needed to balance lunar gravity
- `[Space]` / Click `EXECUTE 10S BURN`: Ignite thruster for 10 seconds of descent
- `[M]`: Open Apollo 11 Flight Manual modal
- `[Esc]` / Click `← LIBRARY`: Return to RetroRevive Game Library

---

## 7. Historical Attribution & Licensing

- **RetroRevive Implementation:** Copyright © 2026 RetroRevive Contributors. Released under the open-source MIT License.
- **Game Concepts & Formulas:** Derived from educational public computer literature edited by David H. Ahl (*BASIC Computer Games*, 1978, Creative Computing Press) and Bob Albrecht (*People's Computer Company*, 1973).
- **Zero External Assets:** All fonts, graphics, world elements, and 8-bit sound effects are procedurally rendered in real time using the Python standard library and Pygame.
