# RetroRevive — Super Star Trek (1978 Edition) Mechanics & Verification Specification

**Historical Origin:** Mike Mayfield (1971, SDS Sigma 7)  
**Refined & Expanded by:** David H. Ahl & Mary Cole (DEC, 1973), Bob Leedom (Westinghouse, 1974)  
**Published by:** David H. Ahl, *BASIC Computer Games: Microcomputer Edition* (1978, pp. 157–163)  
**Engine Implementation:** `games/super_star_trek/engine.py` (100% Python Standard Library)  
**Graphical Interface:** `games/super_star_trek/app.py` (Pygame Desktop Experience)  
**Automated Tests:** `games/super_star_trek/test_engine.py` & `test_platform.py`  

---

## 1. Historical Provenance

In 1971, high school student **Mike Mayfield** wrote the original *Star Trek* game in HP BASIC on a Scientific Data Systems Sigma 7 minicomputer. In 1973, **David H. Ahl** and **Mary Cole** adapted the game for Digital Equipment Corporation's DEC BASIC-PLUS and published it in *101 BASIC Computer Games*.

In 1974, **Bob Leedom** of Westinghouse substantially rewrote and enriched the simulation, introducing the quadrant/sector coordinate scheme, the three-digit Long Range Sensor readout ($K S B$), subsystem damage modeling, starbase docking, and randomized tactical encounters. David H. Ahl published this expanded version as **Super Star Trek** in *Creative Computing* and later in *BASIC Computer Games: Microcomputer Edition* (1978, pp. 157–163), cementing it as one of the most influential computer strategy simulations in computing history.

RetroRevive preserves the full authentic 1978 rule set, coordinate geometry, phaser attenuation formulas, and torpedo ballistics, paired with a modern tactical Pygame command deck.

---

## 2. Galactic Coordinate Geometry

The galaxy is modeled as an 8×8 grid of **Quadrants** ($64\text{ quadrants}$), each containing an 8×8 grid of **Sectors** ($64\text{ sectors}$ per quadrant, total $4,096\text{ sectors}$):

```
       1       2       3       4       5       6       7       8   (Quadrant X)
   +-------+-------+-------+-------+-------+-------+-------+-------+
 1 |       |       |       |       |       |       |       |       |
 2 |       |       |       |       |       |       |       |       |
 3 |       |       |       |       |       |       |       |       |
 4 |       |       |       |Enterprise     |       |       |       |
 5 |       |       |       | [4, 4]|       |       |       |       |
 6 |       |       |       |       |       |       |       |       |
 7 |       |       |       |       |       |       |       |       |
 8 |       |       |       |       |       |       |       |       |
   +-------+-------+-------+-------+-------+-------+-------+-------+
(Quadrant Y)
```

### 2.1. Quadrant Nomenclature
Quadrants are assigned historical Federation sector names based on primary star names, grouped into quadrants I through IV across the 8×8 galactic map:

| Row Index | Primary Quadrant Names |
|:---:|:---|
| 0–1 | Antares, Rigel, Procyon, Vega |
| 2–3 | Canopus, Altair, Sagittarius, Pollux |
| 4–5 | Sirius, Deneb, Capella, Betelgeuse |
| 6–7 | Aldebaran, Regulus, Arcturus, Spica |

Each region is subdivided into quadrants `I`, `II`, `III`, and `IV` across the X axis.

---

## 3. Navigation & Movement Physics

### 3.1. Directional Vectors
Course directions follow the standard 1978 8-point compass navigation system where $C \in [1.0, 9.0)$:

```
           3.0 (North)
       4.0 \     / 2.0 (North-East)
 (North-West)\   /
               o --- 1.0 (East)
 (South-West)/   \
       6.0 /     \ 8.0 (South-East)
           7.0 (South)
  (Course 5.0 is West)
```

The mathematical unit displacement per step is given by:
$$\theta = (C - 1.0) \times \frac{\pi}{4}$$
$$\Delta X = \cos(\theta), \quad \Delta Y = -\sin(\theta)$$

### 3.2. Warp & Impulse Engines
- **Distance:** For warp factor $W$, distance traveled equals $D = 8 \cdot W$ sectors.
- **Energy Cost:** Warp traversal consumes $E = \text{round}(8 \cdot W)$ energy units.
- **Stardate Consumption:** Stardate advances by $W$ stardates (or $0.1$ for sub-warp impulse maneuvers within a quadrant).
- **Subsystem Constraint:** If the Warp Engines are damaged, speed is restricted to sub-warp impulse ($W \le 0.2$).

---

## 4. Tactical Combat Systems

### 4.1. Directed Phaser Banks
Phasers distribute focused energy among all Klingon warships currently detected in the sector:
$$P_{per\_target} = \frac{P_{total}}{N_{klingons}}$$

Energy dissipates over distance according to the inverse distance attenuation law:
$$H_i = \text{round}\left(\frac{P_{per\_target}}{D_i} \cdot \left(2.0 + R\right)\right)$$
where $D_i = \sqrt{(\Delta X)^2 + (\Delta Y)^2}$ and $R \in [0.0, 0.5]$ represents targeting fluctuations.

If Phaser Controls are damaged, phaser banks cannot be fired until repaired.

### 4.2. Ballistic Photon Torpedoes
The Enterprise carries an initial complement of 10 Photon Torpedoes.
- Torpedoes travel in a straight line along the chosen course vector step by step across the 8×8 sector grid.
- **Collisions:**
  - **Klingon:** Direct hit destroys the Klingon battlecruiser immediately.
  - **Star:** Torpedo is absorbed/dissipated by stellar gravitational forces; star remains unharmed.
  - **Starbase:** Direct hit destroys the Starbase (incurs heavy Starfleet court-martial penalties).
  - **Boundary:** Torpedo exits the quadrant into deep space.

### 4.3. Deflector Shields & Combat Retaliation
- Shields form an protective energy envelope with up to $2,500\text{ units}$ capacity.
- Energy can be transferred freely between main reserves and shields ($1:1$ ratio).
- Surviving Klingons in the quadrant retaliate after every Enterprise offensive action or navigational maneuver:
$$H_{klingon} = \text{round}\left(\frac{E_{klingon}}{D_i} \cdot \left(2.0 + R\right)\right)$$
- If shields are raised, incoming damage diminishes shield energy. If shields drop to zero, damage penetrates the hull, directly reducing main energy reserves and causing critical subsystem casualties.

---

## 5. Long-Range Sensors (LRS) & Reconnaissance

The Long-Range Sensor array probes the 9 quadrants immediately adjacent to the Enterprise (a 3×3 matrix centered on current position).
Each scanned quadrant displays a 3-digit reconnaissance integer $K S B$:

$$\text{Code} = K \cdot 100 + B \cdot 10 + S$$

Where:
- $K$: Number of Klingon battlecruisers in quadrant ($0$ to $3$)
- $B$: Number of Federation Starbases in quadrant ($0$ or $1$)
- $S$: Number of Stars in quadrant ($1$ to $8$)

*Example:* Code `205` designates 2 Klingons, 0 Starbases, and 5 Stars.

---

## 6. Starbase Docking & Subsystem Repairs

When the Enterprise maneuvers to a sector directly adjacent to a Federation Starbase ($|\Delta X| \le 1 \land |\Delta Y| \le 1$):
- Condition shifts to **DOCKED**.
- Deflector shields drop to 0 (power redirected to docking clamps).
- Main energy reserves are replenished to maximum ($3,000\text{ units}$).
- Photon torpedo bays are fully restocked to 10 torpedoes.
- All damaged subsystems undergo immediate complete repair.

---

## 7. Subsystem Damage Modeling

The Library Computer tracks operational status across 7 critical ship devices:
1. `WARP_ENGINES` — Navigational propulsion across quadrants
2. `SHORT_RANGE_SENSORS` — Sector tactical view
3. `LONG_RANGE_SENSORS` — 3×3 galactic quadrant reconnaissance
4. `PHASER_CONTROL` — Energy weapon discharge & targeting
5. `PHOTON_TUBES` — Torpedo launching racks
6. `SHIELD_CONTROL` — Shield deflection & energy transfer
7. `COMPUTER` — Galactic chart & tactical telemetry

Damage occurs when unshielded enemy fire strikes the hull. Subsystems gradually self-repair over time during warp travel, or instantly when docked at a Starbase.

---

## 8. Victory, Defeat & Scoring

### Victory Conditions
- All Klingon battlecruisers in the galaxy destroyed before the mission deadline stardate expires.

### Defeat Conditions
- Enterprise main energy reaches zero ($E \le 0$).
- Mission stardate deadline expires before all Klingons are neutralized.
- Enterprise destroyed in combat.

### Starfleet Rating
$$\text{Score} = 1000 \cdot \left(\frac{K_{destroyed}}{K_{total}}\right) + \text{round}\left(\frac{E_{remaining}}{10}\right) - 50 \cdot (\text{Stardates Elapsed}) + 500 \cdot (\text{Victory Bonus})$$

Rank evaluation tiers:
- $\ge 1200$: Fleet Admiral
- $\ge 900$: Admiral
- $\ge 600$: Starship Captain
- $\ge 300$: Commander
- $< 300$: Lieutenant
