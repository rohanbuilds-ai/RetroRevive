# RetroRevive — The Oregon Trail (1848 Pioneer Simulation) Mechanics & Verification Specification

**Historical Origin:** Don Rawitsch, Bill Heinemann, and Paul Dillenberger (Jordan Junior High, Minneapolis / Carleton College, November–December 1971)  
**Published by:** MECC (*Minnesota Educational Computing Consortium*, 1974); *Creative Computing* Magazine (May/June 1978, pp. 132–139)  
**Engine Implementation:** `games/oregon_trail/engine.py` (100% Python Standard Library)  
**Graphical Desktop Interface:** `games/oregon_trail/app.py` (Pygame Desktop Experience)  
**Automated Tests:** `games/oregon_trail/test_engine.py` & `test_platform.py`  

---

## 1. Historical Provenance

In autumn 1971, student teacher **Don Rawitsch** created a board game to help teach an 8th-grade American history class at Jordan Junior High in Minneapolis about the historic 1848 pioneer migration across North America. Roommates **Bill Heinemann** and **Paul Dillenberger**, fellow student teachers and math/programming students at Carleton College, suggested programming the simulation on a minicomputer. Over an intense weekend in November 1971, Heinemann and Dillenberger coded the original program in BASIC on a CDC Cyber timesharing mainframe accessed via a 110-baud acoustic coupler teletype.

In 1974, Rawitsch was hired by the Minnesota Educational Computing Consortium (MECC) and re-entered the code into the statewide network. In 1978, David H. Ahl published the full BASIC source code in *Creative Computing* (May/June 1978, pp. 132–139).

RetroRevive's implementation faithfully reproduces the historical 1848 pioneer journey, authentic distance calculations across 17 historic trail milestones, health drain, rations, river crossings, hunting, dynamic fort inflation, and victory scoring.

---

## 2. Journey Specifications & Route Map

The Oregon Trail begins at the trailhead in Independence, Missouri, and finishes 2,040 miles westward in Oregon's fertile Willamette Valley.

### The 17 Historic Trail Milestones

| # | Milestone Name | Distance | Milestone Type | Crossing / Outpost Feature |
|:---:|:---|:---:|:---:|:---|
| 1 | **Independence, Missouri** | $0\text{ mi}$ | Town / Trailhead | Pioneer jumping-off point; base store prices |
| 2 | **Kansas River Crossing** | $102\text{ mi}$ | River Crossing | 200-yard wide prairie river; $4.5\text{ ft}$ depth; ferry service available |
| 3 | **Big Blue River Crossing** | $185\text{ mi}$ | River Crossing | Swift prairie river; $3.2\text{ ft}$ depth; flash flood risk |
| 4 | **Fort Kearney** | $319\text{ mi}$ | Military Fort | U.S. Army outpost on Platte River; general store |
| 5 | **Chimney Rock** | $554\text{ mi}$ | Scenic Landmark | Towering $300\text{ ft}$ spire signaling Rocky Mountain approach |
| 6 | **Fort Laramie** | $640\text{ mi}$ | Military Outpost | Junction of Laramie and North Platte rivers; general store |
| 7 | **Independence Rock** | $830\text{ mi}$ | Scenic Landmark | 'Great Register of the Desert' inscribed with pioneer names |
| 8 | **South Pass** | $932\text{ mi}$ | Mountain Pass | Gentle saddle crossing the Continental Divide |
| 9 | **Fort Bridger** | $989\text{ mi}$ | Trading Post | Jim Bridger's supply post on Black's Fork River; general store |
| 10 | **Green River Crossing** | $1,020\text{ mi}$ | River Crossing | Dangerous deep glacial river; $6.5\text{ ft}$ depth; ferry service |
| 11 | **Soda Springs** | $1,180\text{ mi}$ | Scenic Landmark | Steaming carbonated bubbling springs in Idaho hills |
| 12 | **Fort Hall** | $1,288\text{ mi}$ | Trading Post | Hudson's Bay Company outpost on Snake River; general store |
| 13 | **Snake River Crossing** | $1,534\text{ mi}$ | River Crossing | Treacherous wide river; $5.8\text{ ft}$ depth; island sandbars |
| 14 | **Fort Boise** | $1,642\text{ mi}$ | Trading Outpost | Adobe fur-trading station; general store |
| 15 | **Blue Mountains** | $1,818\text{ mi}$ | Mountain Pass | Steep granite passes; early autumn blizzard danger |
| 16 | **The Dalles** | $1,940\text{ mi}$ | Columbia River Port | Trail junction: Barlow Road toll or Columbia River raft; store |
| 17 | **Willamette Valley** | $2,040\text{ mi}$ | Destination | **Final Goal:** Fertile Oregon farmland reached! Victory! |

---

## 3. Pioneer Party & Occupations

Each wagon consists of a party of **5 pioneers** (the Wagon Leader and 4 companions).

### Starting Occupations & Score Multipliers

| Occupation | Starting Cash | Special Capability | Final Score Multiplier |
|:---|:---:|:---|:---:|
| **Banker** | $\$1,600.00$ | Ample funding for excessive supplies and ferry tolls | $1.0\times$ |
| **Carpenter** | $\$800.00$ | Skilled woodworker; repairs broken wagon parts | $2.0\times$ |
| **Farmer** | $\$400.00$ | Hardscrabble pioneer; excellent oxen care | $3.0\times$ |

---

## 4. Trail Dynamics & Health Simulation

### 4.1. Travel Cycles
Each standard travel turn simulates a **4-day march** along the trail:
- Base daily travel speed is governed by wagon pace.
- Oxen factor: $4+$ oxen $= 100\%$ speed; $2-3$ oxen $= 75\%$ speed; $1$ ox $= 40\%$ speed.
- If oxen count drops to $0$, the wagon is immobilized and the journey fails.
- Weather conditions apply multiplier penalties to daily distance (e.g. Mud $= 0.6\times$, Blizzard $= 0.35\times$).

### 4.2. Paces & Stamina
| Pace | Daily Distance | Daily Health Drain | Description |
|:---|:---:|:---:|:---|
| **Steady** | $14\text{ miles/day}$ | $-0.2\text{ HP/day}$ | Sustainable cadence; preserves party endurance |
| **Strenuous** | $18\text{ miles/day}$ | $-0.8\text{ HP/day}$ | Fast progress; minor stamina depletion |
| **Grueling** | $22\text{ miles/day}$ | $-2.0\text{ HP/day}$ | Maximum speed; severe exhaustion risk for oxen and pioneers |

### 4.3. Rations & Nutrition
Food consumption is computed per living party member per day:
| Rations | Consumption | Health Effect |
|:---|:---:|:---|
| **Filling** | $3.0\text{ lbs/person/day}$ | $+0.5\text{ HP/day}$ health recovery |
| **Meager** | $2.0\text{ lbs/person/day}$ | $+0.0\text{ HP/day}$ baseline maintenance |
| **Bare Bones** | $1.0\text{ lb/person/day}$ | $-1.5\text{ HP/day}$ malnutrition drain |
| **Depleted (0 lbs)** | $0.0\text{ lbs/person/day}$ | $-25.0\text{ HP/cycle}$ acute starvation drain |

### 4.4. Resting & Recuperation
- Resting halts the wagon for **3 days**.
- Pioneers consume rations normally.
- Living companions recover $+12.0\text{ HP}$.
- Each sick companion has a **40% daily chance** to recover from active illness (Fever, Dysentery, Measles).

---

## 5. River Crossing Decisions

At each river landmark (Kansas, Big Blue, Green, Snake), the player must choose a crossing technique:

1. **Ford River (Free):**
   - Ideal when water is shallow ($< 2.5\text{ ft}$).
   - If water is deeper than $3.0\text{ ft}$, high probability of swamping wagon bed, losing $20-60\text{ lbs}$ of food, or drowning an ox.
2. **Caulk and Float (Free):**
   - Pioneers seal wagon box with pine pitch and float across as an impromptu boat.
   - Effective on wide, deep, calm waters; small chance ($15\%$) of tipping in turbulent rapids.
3. **Take Ferry ($\$5.00$):**
   - Guaranteed $100\%$ safe passage with local ferry operators.
   - Requires sufficient cash funds.

---

## 6. General Store Provisions & Distance Inflation

Supplies can be purchased at Independence, MO ($0\text{ mi}$) and forts along the route (Fort Kearney, Fort Laramie, Fort Bridger, Fort Hall, Fort Boise, The Dalles).

### Supply Price Table & Inflation Formula
Fort prices increase with distance along the trail according to:
$$\text{Price}(\text{miles}) = \text{Base Price} \times \left(1.0 + \frac{\text{miles}}{2040} \times 1.2\right)$$

| Supply Item | Trailhead Base Price | Fort Laramie ($640\text{ mi}$) | Fort Boise ($1,642\text{ mi}$) | Purpose |
|:---|:---:|:---:|:---:|:---|
| **Ox** | $\$25.00$ | $\$34.40$ | $\$49.15$ | Pulls covered wagon; minimum 1 needed, 4 recommended |
| **Food (lb)** | $\$0.20$ | $\$0.28$ | $\$0.39$ | Daily nutrition for living companions |
| **Warm Clothing (set)** | $\$10.00$ | $\$13.76$ | $\$19.66$ | Protects against cold weather and blizzards |
| **Ammunition (box of 50)**| $\$2.00$ | $\$2.75$ | $\$3.93$ | Used for hunting wild prairie game |
| **Spare Wheel** | $\$10.00$ | $\$13.76$ | $\$19.66$ | Instantly repairs broken wagon wheel |
| **Spare Axle** | $\$10.00$ | $\$13.76$ | $\$19.66$ | Instantly repairs broken wagon axle |
| **Spare Tongue** | $\$10.00$ | $\$13.76$ | $\$19.66$ | Instantly repairs broken wagon tongue |
| **Medical Kit** | $\$15.00$ | $\$20.65$ | $\$29.49$ | Treats sudden illnesses and snakebites |

---

## 7. Hunting Wild Game

- Organizing a hunting expedition requires at least **10 rounds of ammunition**.
- Pioneers spend between $10$ and $25$ bullets.
- Wild game yield categories:
  - **Skunked (15%):** No game sighted; bullets expended.
  - **Small Game (30%):** Wild rabbits, grouse ($25 - 60\text{ lbs}$ meat).
  - **Medium Game (35%):** Pronghorn antelope, deer ($80 - 160\text{ lbs}$ meat).
  - **Large Game (20%):** Great American bison / buffalo ($180 - 250\text{ lbs}$ meat).

---

## 8. Final Expedition Scoring

Upon reaching Willamette Valley ($2,040\text{ miles}$), the expedition score is computed:

$$\text{Base Score} = \sum (\text{Surviving Pioneers} \times 500) + \sum (\text{Good Health Pioneers} \times 300) + \text{Asset Value}$$

Where Asset Value is:
$$\text{Asset Value} = 0.5 \times \text{Food} + 50 \times \text{Oxen} + 25 \times \text{Clothes} + 0.1 \times \text{Ammo} + 40 \times \text{Spare Parts} + 1.0 \times \text{Cash}$$

$$\text{Final Score} = \text{Base Score} \times \text{Profession Multiplier}$$

If the expedition terminates prematurely before reaching Oregon, partial points are awarded equal to $0.5 \times \text{Miles Traveled}$.

---

## 9. Automated Test Verification Matrix

All mechanics are verified by deterministic automated tests in `games/oregon_trail/test_engine.py` and `test_platform.py`:

| Test Case | Module | Verification Objective |
|:---|:---|:---|
| `test_default_initialization` | `test_engine.py` | Initial date, $0$ miles, $5$ companions, 4 oxen, $400\text{ lbs}$ food |
| `test_profession_cash_and_multipliers` | `test_engine.py` | Banker $(\$1600, 1.0\times)$, Carpenter $(\$800, 2.0\times)$, Farmer $(\$400, 3.0\times)$ |
| `test_travel_cycle_advances_distance_and_date` | `test_engine.py` | Distance increases, calendar advances 4 days, rations consumed |
| `test_rations_consumption_rates` | `test_engine.py` | Filling ($3\text{ lbs}$), Meager ($2\text{ lbs}$), Bare Bones ($1\text{ lb}$) |
| `test_food_depletion_causes_starvation_health_drain` | `test_engine.py` | Acute health drain when rations run dry |
| `test_oxen_loss_halts_travel` | `test_engine.py` | Immediate game over if oxen count reaches zero |
| `test_resting_heals_party` | `test_engine.py` | Rest cycle advances 3 days, heals $+12\text{ HP}$ |
| `test_resting_cures_illness_probabilistically` | `test_engine.py` | 40% daily chance to cure active disease |
| `test_hunting_requires_minimum_ammunition` | `test_engine.py` | Rejects hunt if ammunition $< 10$ rounds |
| `test_successful_hunt_yields_food_and_deducts_ammo` | `test_engine.py` | Fresh meat added to inventory, bullets decremented |
| `test_ferry_safe_with_sufficient_funds` | `test_engine.py` | Ferry crossing safely clears river for $\$5.00$ |
| `test_ferry_rejects_insufficient_funds` | `test_engine.py` | Rejects ferry if cash balance $< \$5.00$ |
| `test_distance_inflation_increases_prices` | `test_engine.py` | Fort prices scale up to $2.2\times$ along the trail |
| `test_buy_supplies_success` | `test_engine.py` | Cash deducted, inventory incremented at outposts |
| `test_destination_victory` | `test_engine.py` | Reaching $2,040\text{ miles}$ triggers victory |
| `test_score_calculation_with_multipliers` | `test_engine.py` | Scoring math with profession multipliers |
| `test_numeric_hotkeys_quick_launch` | `test_platform.py` | Key `'4'` launches Oregon Trail from library hub |
| `test_store_open_and_purchase_at_independence` | `test_platform.py` | General store modal UI cart interaction |
