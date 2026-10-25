# RetroRevive — Lunar Lander (1978 Edition) Mechanics & Verification Specification

**Historical Origin:** Jim Storer (Lexington High School, 1969)  
**Ported & Published by:** David H. Ahl, *101 BASIC Computer Games* (1973) and *BASIC Computer Games: Microcomputer Edition* (1978, pp. 106–108)  
**Engine Implementation:** `games/lunar_lander/engine.py` (100% Python Standard Library)  
**Graphical Interface:** `games/lunar_lander/app.py` (Pygame Desktop Experience)  
**Automated Tests:** `games/lunar_lander/test_engine.py` & `test_platform.py`  

---

## 1. Historical Provenance

In autumn 1969, shortly after Apollo 11 landed on the Sea of Tranquility, 17-year-old Lexington High School student **Jim Storer** wrote the original text-based Lunar Landing Game in DEC's FOCAL-69 language for the PDP-8 minicomputer. 

David H. Ahl ported Storer's code to DEC BASIC and published it in *101 BASIC Computer Games* (1973). In 1978, Ahl republished it with minor formatting refinements in *BASIC Computer Games* (pp. 106–108). 

Unlike later arcade vector adaptations (e.g., Atari 1979), Storer's original simulation is a rigorous numerical integration model based on **Tsiolkovsky's rocket equation** using a 5th-order Taylor series expansion.

---

## 2. Initial Mission Conditions

Every descent simulation commences with authentic Apollo LEM orbital insertion parameters:

| Parameter | BASIC Variable | Physical Value | Description |
|:---|:---:|:---:|:---|
| **Altitude** | `A` | $120.0\text{ miles}$ ($633,600\text{ feet}$) | Altitude above lunar surface |
| **Velocity** | `V` | $1.0\text{ mile/sec}$ ($3,600\text{ MPH}$) | Initial downward velocity |
| **Total Wet Mass** | `M` | $33,000\text{ lbs}$ | Total capsule mass with propellant |
| **Empty Dry Mass** | `N` | $16,500\text{ lbs}$ | Capsule mass without propellant |
| **Fuel Propellant** | `F = M - N` | $16,500\text{ lbs}$ | Usable descent stage propellant |
| **Cycle Duration** | `T` | $10.0\text{ seconds}$ | Duration of standard turn |
| **Lunar Gravity** | `G` | $0.001\text{ miles/sec}^2$ ($5.28\text{ ft/s}^2$) | Gravitational acceleration |
| **Thrust Velocity** | `Z` | $1.8\text{ miles/sec}$ | Exhaust velocity coefficient |
| **Maximum Burn** | `K` | $200.0\text{ lbs/sec}$ | Engine throttle ceiling |

---

## 3. Physics Simulation & Subroutine 420 Numerical Integration

### 3.1. Turn Input Validation
Each turn, the astronaut enters the retro-rocket fuel burn rate $K$ in pounds per second:
1. $K$ must be a non-negative real number ($K \ge 0$).
2. $K$ cannot exceed $200\text{ lbs/sec}$. If $K > 200$, it is clamped or rejected.
3. If $K \in (0, 0.001)$, it is treated as zero burn (coasting under gravity).
4. Available fuel limits the duration of the burn: if $F < K \cdot T$, the engine burns at rate $K$ for time $S = F / K$ before running dry.

### 3.2. Subroutine 420: 5th-Order Taylor Series Expansion
Under continuous mass exhaustion, the differential equation governing rocket motion is:
$$\frac{dv}{dt} = g - \frac{Z \cdot K}{M - K \cdot t}$$

To solve this on a 1969 minicomputer without floating-point calculus hardware, Jim Storer derived a 5th-order Taylor series expansion of $\ln(1 - x)$ where $Q = \frac{S \cdot K}{M}$:

$$J = V + G \cdot S + Z \cdot \left(-Q - \frac{Q^2}{2} - \frac{Q^3}{3} - \frac{Q^4}{4} - \frac{Q^5}{5}\right)$$

$$I = A - G \cdot \frac{S^2}{2} - V \cdot S + Z \cdot S \cdot \left(\frac{Q}{2} + \frac{Q^2}{6} + \frac{Q^3}{12} + \frac{Q^4}{20} + \frac{Q^5}{30}\right)$$

Where:
- $S$: elapsed time interval ($10.0\text{ s}$ standard, or partial step if fuel depleted or surface reached)
- $J$: updated downward velocity at step completion
- $I$: updated altitude above lunar surface

### 3.3. Mid-Turn Surface Touchdown Interpolation
If $I \le 0$ during a step, the craft has reached the surface during interval $S$. The engine interpolates the exact moment of touchdown:
1. When burn rate $K = 0$, exact quadratic solution:
   $$S_{\text{touch}} = \frac{\sqrt{V^2 + 2 \cdot G \cdot A} - V}{G}$$
   $$V_{\text{final}} = \sqrt{V^2 + 2 \cdot G \cdot A}$$
2. When $K > 0$, iterative root-finding (successive approximation matching lines 420–500 in BASIC) determines the fractional second $S$ such that $I(S) = 0$, yielding touchdown downward velocity $W = 3600 \cdot J\text{ MPH}$.

### 3.4. Fuel Exhaustion (Free-Fall to Surface)
When propellant runs out ($F \le 0$):
1. The engine reports: `FUEL OUT AT <T> SECONDS`.
2. The craft accelerates under pure gravity $G$:
   $$W = 3600 \cdot \sqrt{V^2 + 2 \cdot G \cdot A}$$
   $$T_{\text{final}} = T_{\text{exhaust}} + \frac{\sqrt{V^2 + 2 \cdot G \cdot A} - V}{G}$$

---

## 4. Touchdown Evaluation Tiers

Upon touchdown ($A \le 0$), the craft's impact velocity $W$ (in MPH) determines mission survival:

| Impact Velocity ($W$) | Rating Tier | Historical BASIC Outcome Message | Craft State |
|:---|:---:|:---|:---:|
| **$W \le 1.2\text{ MPH}$** | **Tier 1: Perfect** | `"PERFECT LANDING !-(LUCKY)"` | Intact |
| **$1.2 < W \le 10.0\text{ MPH}$** | **Tier 2: Good** | `"GOOD LANDING (COULD BE BETTER)"` | Intact |
| **$10.0 < W \le 60.0\text{ MPH}$** | **Tier 3: Damaged** | `"CRAFT DAMAGE. . . YOU MAY BE STRANDED UNTIL A RESCUE PARTY ARRIVES. HOPE YOU HAVE ENOUGH FOOD!"` | Damaged / Stranded |
| **$W > 60.0\text{ MPH}$** | **Tier 4: Crash** | `"SORRY THERE WERE NO SURVIVORS. YOU BLEW IT!"` | Fatal Impact |

### Crater Depth Formula
In a Tier 4 fatal crash ($W > 60\text{ MPH}$), the impact creates a lunar crater proportional to velocity:
$$\text{Crater Depth} = W \times 0.227\text{ feet}$$

For example, an uncontrolled free-fall crash at $3,612\text{ MPH}$ produces an $820\text{-foot}$ crater.

---

## 5. Optimal Flight Strategy & Auto-Hover

### Hover Equilibrium Burn Rate
To maintain zero vertical acceleration ($dv/dt = 0$), rocket thrust must precisely balance lunar gravity:
$$Z \cdot K = M \cdot G \implies K_{\text{hover}} = \frac{M \cdot G}{Z}$$

- At mission start ($M = 33,000\text{ lbs}$):
  $$K_{\text{hover}} = \frac{33000 \times 0.001}{1.8} \approx 18.33\text{ lbs/sec}$$
- At dry mass ($M = 16,500\text{ lbs}$):
  $$K_{\text{hover}} = \frac{16500 \times 0.001}{1.8} \approx 9.17\text{ lbs/sec}$$

Because $K_{\text{hover}}$ decreases as propellant burns off, holding a constant burn rate of $18.33\text{ lbs/sec}$ will gradually cause the lander to accelerate upwards!

---

## 6. Architecture & User Interfaces

RetroRevive delivers two complete interfaces for Lunar Lander:

1. **Desktop Graphical Experience (`games/lunar_lander/app.py`):**
   - Animated Apollo LEM with thruster gimbaling and dynamic exhaust particle physics.
   - Comprehensive telemetry dashboard displaying mission elapsed time, altitude (miles and feet), descent velocity (MPH), remaining fuel (lbs), and active thrust.
   - Interactive burn controls: Quick presets (`0`, `50`, `100`, `150`, `MAX 200`), adjustment steppers (`-25`, `-10`, `+10`, `+25`), and automated **AUTO-HOVER** computation.
   - Modal flight manual and historical landing evaluation screen.

2. **Terminal CLI Runner (`games/lunar_lander/engine.py`):**
   - Authentic 1978 text telemetry table.
   - Safe input prompt with `?REDO FROM START` on malformed entries.
   - Exact historical text messages for landing outcomes and crater reports.
