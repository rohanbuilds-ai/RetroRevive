"""
games/lunar_lander/engine.py - Pure Python engine for Lunar Lander (1978 Edition).

Preserves the historical 1969/1978 Apollo Lunar Module descent simulation rules
originally authored by Jim Storer and published by David H. Ahl in:
101 BASIC Computer Games (1973) and BASIC Computer Games (1978, pp. 106-108).
Uses only the Python standard library.
"""

from dataclasses import dataclass, field
import math
import sys
from typing import Any, List, Optional, Tuple

# Physical & Engineering Constants from 1978 David Ahl / Jim Storer listing
GRAVITY_G = 0.001       # Lunar gravitational acceleration in miles/sec^2
THRUST_Z = 1.8          # Engine exhaust velocity coefficient in miles/sec
DEFAULT_MASS = 33000.0  # Initial wet capsule mass in lbs
DRY_MASS = 16500.0      # Empty capsule dry mass in lbs
INITIAL_ALTITUDE = 120.0# Initial altitude in miles
INITIAL_VELOCITY = 1.0  # Initial downward velocity in miles/sec (3600 MPH)
STANDARD_TIME_STEP = 10.0# Standard turn time interval in seconds
MAX_LEGAL_BURN = 200.0  # Maximum burn rate in lbs/sec


@dataclass
class TurnTelemetry:
    """Telemetry log entry for a flight cycle."""
    time: float
    altitude_miles: float
    altitude_feet: float
    velocity_mph: float
    fuel_lbs: float
    burn_rate: float


@dataclass
class LanderState:
    """State model for Lunar LEM descent simulation."""
    time_elapsed: float = 0.0
    altitude: float = INITIAL_ALTITUDE
    velocity: float = INITIAL_VELOCITY
    mass: float = DEFAULT_MASS
    empty_mass: float = DRY_MASS
    landed: bool = False
    touchdown_velocity_mph: Optional[float] = None
    outcome: Optional[str] = None          # "PERFECT", "GOOD", "DAMAGED", "CRASH"
    outcome_message: Optional[str] = None
    crater_depth: Optional[float] = None   # in feet, if crashed
    history: List[TurnTelemetry] = field(default_factory=list)

    @property
    def fuel_remaining(self) -> float:
        return max(0.0, self.mass - self.empty_mass)

    @property
    def velocity_mph(self) -> float:
        return self.velocity * 3600.0

    @property
    def altitude_feet(self) -> float:
        return self.altitude * 5280.0

    @property
    def is_terminal(self) -> bool:
        return self.landed


def init_game(
    initial_altitude: float = INITIAL_ALTITUDE,
    initial_velocity: float = INITIAL_VELOCITY,
    initial_mass: float = DEFAULT_MASS,
    empty_mass: float = DRY_MASS,
) -> LanderState:
    """Initializes a new Apollo Lunar Module descent simulation."""
    if initial_altitude <= 0:
        raise ValueError("Initial altitude must be greater than 0.")
    if initial_mass <= empty_mass:
        raise ValueError("Total initial mass must exceed dry empty mass.")

    return LanderState(
        time_elapsed=0.0,
        altitude=initial_altitude,
        velocity=initial_velocity,
        mass=initial_mass,
        empty_mass=empty_mass,
        landed=False,
        touchdown_velocity_mph=None,
        outcome=None,
        outcome_message=None,
        crater_depth=None,
        history=[],
    )


def validate_burn(state: LanderState, burn_rate: Any) -> Tuple[bool, Optional[str]]:
    """
    Validates proposed fuel burn rate K (in lbs/sec).
    Returns (True, None) if legal, or (False, error_reason) if illegal.
    Does NOT mutate game state.
    """
    if state.is_terminal:
        return False, "The landing mission has already concluded."

    if not isinstance(burn_rate, (int, float)) or isinstance(burn_rate, bool):
        return False, "Burn rate must be a valid numeric quantity (0 to 200 lbs/sec)."

    val = float(burn_rate)

    if val < 0.0:
        return False, "Negative burn rate is illegal (historical abort command)."

    if val > MAX_LEGAL_BURN:
        return False, f"Maximum allowable retro-rocket burn rate is {MAX_LEGAL_BURN:.0f} lbs/sec."

    return True, None


def _evaluate_landing(w_mph: float) -> Tuple[str, str, Optional[float]]:
    """
    Evaluates touchdown impact velocity according to historical thresholds:
    - W <= 1.2 MPH: PERFECT LANDING !-(LUCKY)
    - 1.2 < W <= 10 MPH: GOOD LANDING (COULD BE BETTER)
    - 10 < W <= 60 MPH: CRAFT DAMAGE... STRANDED UNTIL RESCUE
    - W > 60 MPH: NO SURVIVORS... BLASTED A NEW LUNAR CRATER
    """
    if w_mph <= 1.2:
        return (
            "PERFECT",
            "PERFECT LANDING !-(LUCKY)\nTouchdown was within nominal structural limits.",
            None,
        )
    elif w_mph <= 10.0:
        return (
            "GOOD",
            "GOOD LANDING (COULD BE BETTER)\nThe lunar module settled safely on the landing pad.",
            None,
        )
    elif w_mph <= 60.0:
        return (
            "DAMAGED",
            "CRAFT DAMAGE... YOU'RE STRANDED HERE UNTIL A RESCUE\nPARTY ARRIVES. HOPE YOU HAVE ENOUGH OXYGEN!",
            None,
        )
    else:
        crater = w_mph * 0.227
        return (
            "CRASH",
            f"SORRY THERE WERE NO SURVIVORS. YOU BLEW IT!\nIN FACT, YOU BLASTED A NEW LUNAR CRATER {crater:.2f} FEET DEEP!",
            crater,
        )


def _integrate_taylor_step(a: float, v: float, m: float, k: float, s: float) -> Tuple[float, float]:
    """
    Subroutine 420 from historical 1978 listing:
    Evaluates Jim Storer's 5th-order Taylor series approximation for rocket descent.
    Returns (new_altitude_i, new_velocity_j).
    """
    q = (s * k) / m
    # Velocity update with Taylor terms for ln(1 - q)
    vel_j = v + GRAVITY_G * s + THRUST_Z * (
        -q - (q ** 2) / 2.0 - (q ** 3) / 3.0 - (q ** 4) / 4.0 - (q ** 5) / 5.0
    )
    # Altitude update integrating velocity over time
    alt_i = a - (GRAVITY_G * (s ** 2)) / 2.0 - v * s + THRUST_Z * s * (
        q / 2.0 + (q ** 2) / 6.0 + (q ** 3) / 12.0 + (q ** 4) / 20.0 + (q ** 5) / 30.0
    )
    return alt_i, vel_j


def step_burn(state: LanderState, burn_rate: float, time_step: float = STANDARD_TIME_STEP) -> LanderState:
    """
    Executes a single time-step burn according to the verified 1978 physics model.
    Advances simulation by time_step seconds or to the exact moment of touchdown.
    Raises ValueError on invalid burn input.
    """
    ok, err = validate_burn(state, burn_rate)
    if not ok:
        raise ValueError(err)

    k = float(burn_rate)
    t = float(time_step)
    l_time = state.time_elapsed
    a = state.altitude
    v = state.velocity
    m = state.mass
    n = state.empty_mass

    # Log current cycle telemetry into history
    telem = TurnTelemetry(
        time=l_time,
        altitude_miles=a,
        altitude_feet=a * 5280.0,
        velocity_mph=v * 3600.0,
        fuel_lbs=max(0.0, m - n),
        burn_rate=k,
    )
    new_history = list(state.history) + [telem]

    # Line 160: Check if fuel is exhausted (free-fall descent)
    if (m - n) < 1e-3 or k <= 0.0 and (m - n) <= 0.0:
        # Free fall under pure gravity to surface (Line 240)
        # S = (-V + SQR(V^2 + 2*A*G)) / G
        discriminant = v * v + 2.0 * a * GRAVITY_G
        s = (-v + math.sqrt(max(0.0, discriminant))) / GRAVITY_G
        final_v = v + GRAVITY_G * s
        final_l = l_time + s
        final_w = 3600.0 * final_v
        outcome, msg, crater = _evaluate_landing(final_w)
        return LanderState(
            time_elapsed=final_l,
            altitude=0.0,
            velocity=final_v,
            mass=m,
            empty_mass=n,
            landed=True,
            touchdown_velocity_mph=final_w,
            outcome=outcome,
            outcome_message=msg,
            crater_depth=crater,
            history=new_history,
        )

    # Line 180: Check if burn time is restricted by remaining fuel
    if (m - n) < t * k:
        s = (m - n) / k
    else:
        s = t

    # Subroutine 420: Numerical integration step
    alt_i, vel_j = _integrate_taylor_step(a, v, m, k, s)

    # Line 200: Check if surface reached during interval (alt_i <= 0)
    if alt_i <= 0.0:
        # Loop 340-360: iteratively converge onto exact touchdown moment
        curr_a, curr_v, curr_m, curr_l = a, v, m, l_time
        step_s = s
        for _ in range(8):
            if step_s < 1e-3:
                break
            # D = V + SQR(V^2 + 2*A*(G - Z*K/M))
            disc = curr_v * curr_v + 2.0 * curr_a * (GRAVITY_G - THRUST_Z * k / curr_m)
            d = curr_v + math.sqrt(max(0.0, disc))
            if d > 1e-5:
                step_s = 2.0 * curr_a / d
            else:
                step_s = 0.0
            test_a, test_v = _integrate_taylor_step(curr_a, curr_v, curr_m, k, step_s)
            curr_a = test_a
            curr_v = test_v
            curr_m = max(n, curr_m - step_s * k)
            curr_l += step_s

        final_w = 3600.0 * curr_v
        outcome, msg, crater = _evaluate_landing(final_w)
        return LanderState(
            time_elapsed=curr_l,
            altitude=0.0,
            velocity=curr_v,
            mass=curr_m,
            empty_mass=n,
            landed=True,
            touchdown_velocity_mph=final_w,
            outcome=outcome,
            outcome_message=msg,
            crater_depth=crater,
            history=new_history,
        )

    # Normal in-flight update (Subroutine 330)
    new_m = max(n, m - s * k)
    new_l = l_time + s
    return LanderState(
        time_elapsed=new_l,
        altitude=alt_i,
        velocity=vel_j,
        mass=new_m,
        empty_mass=n,
        landed=False,
        touchdown_velocity_mph=None,
        outcome=None,
        outcome_message=None,
        crater_depth=None,
        history=new_history,
    )


def play_cli() -> None:
    """Interactive terminal command-line runner for Lunar Lander (1978 Edition)."""
    print("=" * 65)
    print("             LUNAR LEM ROCKET SIMULATION (1978)")
    print("          Original by Jim Storer (1969) & David H. Ahl")
    print("=" * 65)
    print("CONTROL CALLING LUNAR MODULE...")
    print("MANUAL CONTROL NECESSARY.")
    print("YOU MAY SET THE FUEL RATE <K> TO ZERO OR ANY VALUE")
    print("BETWEEN 0 AND 200 LBS PER SECOND.\n")
    print("INITIAL ALTITUDE: 120 MILES  |  INITIAL FUEL: 16,500 LBS")
    print("CAPSULE WEIGHT: 33,000 LBS   |  FIRST RADAR CHECK COMING UP...\n")
    print(f"{'SEC':<6} {'ALTITUDE':<18} {'VELOCITY':<14} {'FUEL (LBS)':<12} {'BURN RATE'}")
    print("-" * 65)

    state = init_game()

    while not state.is_terminal:
        alt_str = f"{int(state.altitude)} MI {int(state.altitude_feet % 5280)} FT"
        vel_str = f"{state.velocity_mph:.1f} MPH"
        fuel_str = f"{state.fuel_remaining:.0f}"
        print(f"{int(state.time_elapsed):<6} {alt_str:<18} {vel_str:<14} {fuel_str:<12} ", end="")

        if state.fuel_remaining <= 0:
            print("[FUEL EXHAUSTED - FREE FALL]")
            state = step_burn(state, 0.0)
            break

        while True:
            try:
                raw = input("? K = ").strip()
                if not raw:
                    continue
                burn = float(raw)
                ok, err = validate_burn(state, burn)
                if not ok:
                    print(f"? {err}")
                    continue
                state = step_burn(state, burn)
                break
            except ValueError:
                print("? INVALID NUMBER. ENTER FUEL BURN RATE (0 - 200 LBS/SEC).")
            except (EOFError, KeyboardInterrupt):
                print("\nMISSION ABORTED. SO LONG FOR NOW.")
                return

    print("\n" + "=" * 65)
    print(f"TOUCHDOWN AT {state.time_elapsed:.1f} SECONDS — IMPACT VELOCITY {state.touchdown_velocity_mph:.2f} MPH")
    print("-" * 65)
    print(state.outcome_message)
    print("=" * 65)
