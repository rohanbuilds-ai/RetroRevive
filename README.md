# RetroRevive — Classic Computer Games Platform

**Confluence Buildathon 2026 — Track: Resurrections**  
**Repository:** [https://github.com/rohanbuilds-ai/RetroRevive.git](https://github.com/rohanbuilds-ai/RetroRevive.git)

RetroRevive brings classic computer games from the 1970s into the modern era through polished desktop graphics, animation, responsive controls, interactive tutorials, and optional modern enhancements—while strictly preserving original gameplay in verified Classic Modes.

Built as an extensible platform, RetroRevive currently features:
1. **Central Graphical Game Library (`retrorevive.py`):** An arcade/retro-styled desktop hub featuring authentic 2×3 game catalog cards with dedicated procedural pixel-art vignettes, live animated online LED status badge, dynamic category filters, real-time search with one-click clear, detail modals, CRT monitor phosphor scanlines, procedural 8-bit sound synthesis, and seamless launch/return routing.
2. **Hammurabi: Reimagined (`ui_pygame.py`):** The iconic 1978 Sumerian kingdom simulation featuring an animated Mesopotamian landscape, Euphrates river, Ziggurat of Ur, Decree Preview ledger, Royal Advisors, and Scenarios.
3. **23 Matches (`games/23_matches/`):** The timeless mathematical subtraction strategy game (Nim) by Bob Albrecht, featuring an animated wooden matchstick board, ember sparks, burning match effects, human-vs-computer play, and dual AI modes.
4. **Lunar Lander (`games/lunar_lander/`):** Jim Storer's 1969/1978 Apollo 11 lunar excursion module (LEM) descent simulation featuring 5th-order Taylor series rocket physics, animated LEM with gimbaling thrusters, particle exhaust flames, low-altitude regolith dust clouds, comprehensive telemetry dashboard, and auto-hover assist.
5. **The Oregon Trail (`games/oregon_trail/`):** Don Rawitsch, Bill Heinemann, and Paul Dillenberger's 1971/1978 historic 2,040-mile pioneer expedition featuring an animated covered wagon with rotating spoked wheels and walking oxen team, dynamic weather overlays (rainfall, blizzards, heat shimmer), interactive 17-landmark route map, river crossings, hunting expeditions, distance-inflation trading posts, and profession scoring multipliers.
6. **Super Star Trek (`games/super_star_trek/`):** Mike Mayfield, David H. Ahl, and Bob Leedom's 1971/1974/1978 galactic fleet command simulation featuring an 8×8 quadrant galaxy (4,096 sectors), directional vector navigation, twin directed phaser beams, ray-traced photon torpedoes, red alert tactical pulse, deflector shields, 3×3 Long-Range Sensor scans, Starbase docking, and subsystem damage modeling.
7. **Hunt the Wumpus (`games/hunt_the_wumpus/`):** Gregory Yob's 1973/1978 non-Euclidean cavern strategy adventure featuring a 20-vertex regular dodecahedral graph, dynamic flickering torchlight wall warmth, animated crooked arrow flight trajectories, sensory proximity cues ("I smell a Wumpus!", "I feel a draft.", "Bats nearby!"), lethal bottomless pits, snatch-bats, and crooked arrows with ricochet physics.
8. **Universal Retro Shader & Audio System:** Procedural CRT scanlines and phosphor bloom toggleable with `[F2]`, and real-time square/sine/triangle wave sound synthesizer toggleable with `[F3]`.
9. **Coming Soon Index:** Metadata, provenance, and rules for upcoming classics: *Colossal Cave Adventure* (1976).
10. **Standalone Terminal CLI Fallback (`main.py --cli`):** Zero-dependency pure standard library CLI for running all playable games in traditional text terminals.

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
- Launch The Oregon Trail directly: `.venv\Scripts\python.exe main.py --oregon`
- Launch Super Star Trek directly: `.venv\Scripts\python.exe main.py --trek`
- Launch Hunt the Wumpus directly: `.venv\Scripts\python.exe main.py --wumpus`

### Launch Standalone Terminal CLI (Zero Dependencies)
```powershell
# Hammurabi historical terminal mode:
.venv\Scripts\python.exe main.py --cli --no-animate --seed 42

# 23 Matches historical terminal mode:
.venv\Scripts\python.exe main.py --matches --cli

# Lunar Lander historical terminal mode:
.venv\Scripts\python.exe main.py --lander --cli

# The Oregon Trail historical terminal mode:
.venv\Scripts\python.exe main.py --oregon --cli

# Super Star Trek historical terminal mode:
.venv\Scripts\python.exe main.py --trek --cli

# Hunt the Wumpus historical terminal mode:
.venv\Scripts\python.exe main.py --wumpus --cli
```
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

### Game 4: The Oregon Trail (1848 Pioneer Simulation)
- **Historical Provenance:** Authored by Don Rawitsch, Bill Heinemann, and Paul Dillenberger (November 1971) on a CDC Cyber timeshare mainframe via teletype; published by MECC (1974) and in *Creative Computing* (May/June 1978, pp. 132–139).
- **Core Mechanics:** Lead a 5-member pioneer wagon party 2,040 miles from Independence, Missouri to Oregon's Willamette Valley across 17 historic landmarks. Balance travel pace (Steady, Strenuous, Grueling) and rations (Filling, Meager, Bare Bones) to preserve party health and prevent exhaustion.
- **Features & Decisions:**
  - **Animated Pioneer Scene:** Covered prairie schooner with spoked wheels, walk-cycle draught oxen, parallax mountain ranges, and landmark progress bar.
  - **River Crossing Mechanics:** Real decisions at Kansas River, Big Blue, Green River, and Snake River (Ford shallow waters, Caulk & Float deep rivers, or Pay $5.00 for guaranteed safe ferry passage).
  - **Hunting Expeditions:** Spend ammunition to hunt prairie rabbits, pronghorn antelope, and wild buffalo for fresh meat.
  - **Trading Economy & Inflation:** Outpost stores with distance-adjusted inflation formula: $\text{Price} = \text{Base} \times (1.0 + \frac{\text{miles}}{2040} \times 1.2)$.
  - **Health & Disaster System:** Manage illnesses (Cholera, Dysentery, Typhoid, Measles, Fever, Snakebite), wagon repairs with spare parts (wheels, axles, tongues), and rest recuperation.
  - **Historic Scoring:** Survivor bonuses, good health points, remaining asset value, and profession difficulty multipliers (Banker $1.0\times$, Carpenter $2.0\times$, Farmer $3.0\times$).

### Game 5: Super Star Trek (1978 Strategic Space Fleet Simulation)
- **Historical Provenance:** Authored by Mike Mayfield (1971, SDS Sigma 7); expanded by David H. Ahl & Mary Cole (DEC, 1973) and Bob Leedom (Westinghouse, 1974); published in *BASIC Computer Games* (1978, pp. 157–163).
- **Core Mechanics:** Command the U.S.S. Enterprise (NCC-1701) across an 8×8 quadrant galaxy ($4,096\text{ sectors}$) on a critical mission to neutralize Klingon battlecruisers before the stardate deadline expires.
- **Cockpit Systems & Controls:**
  - **Tactical SRS Grid (8×8):** Visual sector radar rendering Enterprise (`<*>`), Klingons (`+K+`), Starbases (`>!<`), and Stars (`*`).
  - **Navigational Propulsion:** 8-direction compass course vector calculations ($1.0$–$8.9$) with impulse and warp speeds.
  - **Tactical Combat:** Directed Phaser energy attenuation across hostiles, and ray-traced Photon Torpedo trajectories with obstacle collisions.
  - **Deflector Shields:** 2,500-unit protective energy envelope with live transfer between main reserves and shields.
  - **Reconnaissance & Sensors:** Long-Range Sensor (LRS) 3×3 scan returning authentic 3-digit $K S B$ telemetry code.
  - **Starbase Docking:** Full energy, torpedo, and shield replenishment plus instant repair of 7 ship subsystems.
  - **Starfleet Efficiency Scoring:** Dynamic evaluation of Klingons destroyed, energy conservation, stardate speed, and officer ranks (Fleet Admiral to Lieutenant).

### Game 6: Hunt the Wumpus (1973/1978 Non-Euclidean Cavern Hunt)
- **Historical Provenance:** Authored by Gregory Yob (1973, People's Computer Company / Dartmouth College) and published in *Creative Computing* (1975) and *BASIC Computer Games* (1978, pp. 178–181).
- **Core Mechanics:** Hunt the fearsome Wumpus across a 20-room subterranean cavern forming the vertices of a regular dodecahedron (each room connecting to 3 adjacent tunnels).
- **Cavern Systems & Hazards:**
  - **Sensory Proximity System:** First-person sensory warnings: "I smell a Wumpus!" (1 room away), "I feel a draft." (adjacent to bottomless pit), and "Bats nearby!" (super bat colony).
  - **Lethal Hazards:** Bottomless pits cause fatal falls; super bats snatch and relocate the hunter to a random room.
  - **Crooked Arrow Ballistics:** Chain flight paths of 1 to 5 rooms. Missing or disconnected room choices ricochet into random adjacent passages.
  - **Wumpus Reaction:** Slay the beast with an arrow to win! But missing may stir the Wumpus (75% probability of moving to an adjacent chamber).
  - **Dual Cavern Perspective:** Left stone archway chamber with dynamic tunnel portals + Right 2D planar Schlegel projection map with interactive arrow route planner.

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
│   ├── lunar_lander/
│   │   ├── engine.py           # Lunar Lander pure Python simulation & physics
│   │   ├── app.py              # Lunar Lander Pygame Apollo LEM & HUD
│   │   └── test_engine.py      # Automated tests for Lunar Lander (17 tests)
│   ├── oregon_trail/
│   │   ├── engine.py           # Oregon Trail pure Python 1848 pioneer simulation
│   │   ├── app.py              # Oregon Trail Pygame animated wagon & trail HUD
│   │   └── test_engine.py      # Automated tests for Oregon Trail (20 tests)
│   ├── super_star_trek/
│   │   ├── engine.py           # Super Star Trek pure Python 1978 galaxy engine
│   │   ├── app.py              # Super Star Trek Pygame tactical radar & bridge
│   │   └── test_engine.py      # Automated tests for Super Star Trek (19 tests)
│   └── hunt_the_wumpus/
│       ├── engine.py           # Hunt the Wumpus pure Python 1978 dodecahedron engine
│       ├── app.py              # Hunt the Wumpus Pygame cavern chamber & Schlegel chart
│       └── test_engine.py      # Automated tests for Hunt the Wumpus (20 tests)
├── test_game.py                # Hammurabi core unit tests (26 tests)
├── test_modern.py              # Hammurabi enhanced unit tests (7 tests)
├── test_ui.py                  # Hammurabi UI unit tests (31 tests)
├── test_platform.py            # Platform hub, registry, and UI integration tests (50 tests)
├── verify_ui.py                # Visual screenshot verification script
└── docs/
    ├── platform-architecture.md# Comprehensive architecture documentation
    ├── game-sources.md         # Historical provenance and licensing
    ├── lunar-lander-rules.md   # Mathematical derivation, physics & tiers
    ├── oregon-trail-rules.md   # 1848 route map, landmark guide, math, health equations
    ├── super-star-trek-rules.md# Galactic coordinate math, phaser formulas, torpedo ballistics
    ├── hunt-the-wumpus-rules.md# Dodecahedron topology, sensory warnings, crooked arrows
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

### Run All 211 Automated Unit Tests
```powershell
.venv\Scripts\python.exe -m unittest discover -v
```
**Test Suite Breakdown (211 Tests Total):**
- `test_game.py`: **26 tests** (Historical formulas, land prices, harvest, rat infestation, safe prompt recovery, evaluation tiers).
- `test_modern.py`: **7 tests** (Royal Advisors, Chronicle Log, Scenarios, JSON save/resume roundtrip).
- `test_ui.py`: **31 tests** (Letterbox scaling, Decree Preview math, numeric steppers, text entry, Enter/Keypad Enter submission, Shift+Tab cycling, synthetic event safety, modal focus).
- `games.23_matches.test_engine`: **16 tests** (Initial state, bounds checking, integer validation, Misère termination, Albrecht AI, Optimal AI, repeatable scenarios).
- `games.lunar_lander.test_engine`: **17 tests** (Initial LEM state, burn rate validation, 5th-order Taylor series deceleration, free-fall under gravity, touchdown interpolation, 4 landing outcome tiers, crater depth formula).
- `games.oregon_trail.test_engine`: **20 tests** (Pioneer party initialization, profession multipliers, travel consumption, starvation health drain, oxen loss halts, resting and illness cure, hunting minimum ammo, successful and skunked hunt meat yields, shallow ford vs deep river, ferry tolls, distance store inflation, victory score math).
- `games.super_star_trek.test_engine`: **19 tests** (Initial galaxy state, sector entities, compass heading math, impulse/warp traversal, phaser decay, torpedo ray-tracing collision, shield transfer, starbase docking, subsystem damage/repairs, LRS sensor scan, victory/defeat conditions).
- `games.hunt_the_wumpus.test_engine`: **20 tests** (20-vertex dodecahedron topology, bidirectional edges, graph connectivity, hazard placement, draft/wumpus/bat sensory warnings, movement, pit death, bat transport, crooked arrow flight, ricochets, wumpus slaying, self-hit defeat, arrow exhaustion).
- `test_platform.py`: **55 tests** (Game Registry catalog queries, 6 playable games filter, category filters, substring search, card cycling, details modal, launch/return lifecycle, hotkey quick launches [1]-[6], 23 Matches UI interaction and keypad shortcuts, Lunar Lander telemetry, M flight manual toggle, Oregon Trail journey travel, pace/rations cycling, store purchasing, Super Star Trek tactical cockpit, navigation, sensors, Hunt the Wumpus cavern chamber, Schlegel chart, crooked arrows, restart, procedural card art generation, delta-time transitions, search clearing, and hover interpolation).

### Run Automated Headless Visual UI Verification
```powershell
.venv\Scripts\python.exe verify_ui.py
```
Generates 26 verified screenshots in `docs/screenshots/` covering the platform library, game details modal, 23 Matches gameplay, 23 Matches victory, Lunar Lander flight, Lunar Lander touchdown modal, Lunar Lander crash crater, The Oregon Trail journey, river crossing, store trading post, trail victory, Super Star Trek tactical bridge, LRS reconnaissance scan, phaser combat, Starfleet victory scorecard, Hunt the Wumpus cavern chamber, crooked arrow path flight, Wumpus victory modal, Hammurabi screens, and multi-resolution scaling ($1366\times768$ and $1920\times1080$).

---

## 6. Controls & Accessibility

### Platform Hub Controls
- `[1]`: Quick-launch Hammurabi
- `[2]`: Quick-launch 23 Matches
- `[3]`: Quick-launch Lunar Lander
- `[4]`: Quick-launch The Oregon Trail
- `[5]`: Quick-launch Super Star Trek
- `[6]`: Quick-launch Hunt the Wumpus
- `[F2]`: Toggle CRT Monitor Scanlines & Phosphor Bloom filter (universal across all screens)
- `[F3]`: Toggle 8-bit Sound Synthesizer Audio (universal across all screens)
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

### The Oregon Trail Controls
- `[Space]` / `[Enter]` / Click `CONTINUE ON TRAIL`: Advance journey 4 days along the trail
- `[T]` / Click `REST (3 DAYS)`: Halt wagon to recuperate health and treat sickness
- `[H]` / Click `HUNT GAME`: Spend ammunition to hunt prairie wild game for fresh meat
- `[P]` / Click `PACE`: Cycle wagon pace (Steady, Strenuous, Grueling)
- `[R]` / Click `RATIONS`: Cycle food rations (Filling, Meager, Bare Bones)
- `[S]` / Click `VISIT STORE`: Access outpost trading post when at fort or town
- `[L]` / Click `TRAIL LOG`: Review pioneer expedition chronicle
- `[F1]` / `[M]` / Click `TRAIL GUIDE`: Open pioneer survival manual
- `[Esc]` / Click `← LIBRARY`: Return to RetroRevive Game Library

### Super Star Trek Controls
- `[1]`–`[8]` (Compass Buttons): Select course direction ($1=\text{East}, 3=\text{North}, 5=\text{West}, 7=\text{South}$)
- `[IMP]`, `[W1]`, `[W2]`, `[W4]`, `[W8]`: Select warp speed factor
- `[Space]` / `[Enter]` / Click `ENGAGE WARP`: Execute course navigation
- `[P]` / Click `PHASERS`: Discharge directed energy banks across Klingon targets
- `[T]` / Click `TORPEDO`: Launch ray-traced photon torpedo along active heading
- `[S]` / Click `SHIELDS`: Transfer energy between main reserves and deflector shields
- `[L]` / Click `LRS SCAN`: Probe adjacent 3×3 quadrants with Long-Range Sensors
- `[D]` / Click `DOCK BASE`: Dock at adjacent Federation Starbase for full resupply & repairs
- `[M]` / Click `ORDERS`: View Starfleet Command tactical briefing & rules
- `[C]` / Click `SHIP LOG`: Open Captain's mission log
- `[Esc]` / Click `← LIBRARY`: Return to RetroRevive Game Library

### Hunt the Wumpus Controls
- `[1]`, `[2]`, `[3]` / Click `TUNNEL 1-3`: Traverse connected tunnels into adjacent chambers
- Mouse Click on Dodecahedron Map Nodes: Chain rooms for crooked arrow trajectory (1 to 5 rooms)
- `[Space]` / `[Enter]` / Click `SHOOT ARROW`: Loose crooked arrow along planned trajectory
- `[C]` / Click `CLEAR PATH`: Reset planned crooked arrow flight path
- `[M]` / Click `CAVERN RULES`: Open authentic 1978 Gregory Yob survival guide
- `[L]` / Click `JOURNAL`: Review subterranean exploration chronicle
- `[R]` / Click `RESTART`: Re-generate cave topology and entities
- `[Esc]` / Click `← LIBRARY`: Return to RetroRevive Game Library

---

## 7. Historical Attribution & Licensing

- **RetroRevive Implementation:** Copyright © 2026 RetroRevive Contributors. Released under the open-source MIT License.
- **Game Concepts & Formulas:** Derived from educational public computer literature edited by David H. Ahl (*BASIC Computer Games*, 1978, Creative Computing Press) and Bob Albrecht (*People's Computer Company*, 1973).
- **Zero External Assets:** All fonts, graphics, world elements, and 8-bit sound effects are procedurally rendered in real time using the Python standard library and Pygame.
