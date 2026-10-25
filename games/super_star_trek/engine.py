"""
games/super_star_trek/engine.py - Pure Python engine for Super Star Trek (1974/1978 Edition).

Authored by Mike Mayfield (1971), David H. Ahl & Bob Leedom (1974).
Published in Creative Computing and BASIC Computer Games (1978, pp. 157-163).
Uses 100% Python standard library with zero external dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
import random
import sys
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants & Enumerations
# ---------------------------------------------------------------------------

GALAXY_WIDTH = 8
GALAXY_HEIGHT = 8
SECTOR_WIDTH = 8
SECTOR_HEIGHT = 8

INITIAL_ENERGY = 3000.0
MAX_ENERGY = 3000.0
INITIAL_SHIELDS = 500.0
MAX_SHIELDS = 1500.0
INITIAL_TORPEDOES = 10
MAX_TORPEDOES = 10
INITIAL_STARDATE = 3000.0
MISSION_DAYS = 30.0

# 16 authentic star quadrant names (4 variants I-IV = 64 total quadrants)
QUADRANT_REGION_NAMES = [
    "Antares", "Rigel", "Procyon", "Vega",
    "Canopus", "Altair", "Sagittarius", "Pollux",
    "Sirius", "Deneb", "Capella", "Betelgeuse",
    "Aldebaran", "Regulus", "Arcturus", "Spica",
]


class ShipCondition(str, Enum):
    GREEN = "GREEN"        # No enemies in quadrant
    YELLOW = "YELLOW"      # Low energy (< 1000 units)
    RED = "RED"            # Klingons present in quadrant
    DOCKED = "DOCKED"      # Adjacent to or docked at Federation Starbase


class Device(str, Enum):
    WARP_ENGINES = "WARP_ENGINES"
    SHORT_RANGE_SENSORS = "SHORT_RANGE_SENSORS"
    LONG_RANGE_SENSORS = "LONG_RANGE_SENSORS"
    PHASER_CONTROL = "PHASER_CONTROL"
    PHOTON_TUBES = "PHOTON_TUBES"
    SHIELD_CONTROL = "SHIELD_CONTROL"
    COMPUTER = "COMPUTER"


class SectorEntity(str, Enum):
    EMPTY = "EMPTY"
    ENTERPRISE = "ENTERPRISE"
    KLINGON = "KLINGON"
    STARBASE = "STARBASE"
    STAR = "STAR"

    @property
    def symbol(self) -> str:
        if self == SectorEntity.ENTERPRISE:
            return "<*>"
        elif self == SectorEntity.KLINGON:
            return "+K+"
        elif self == SectorEntity.STARBASE:
            return ">!<"
        elif self == SectorEntity.STAR:
            return " * "
        return " . "


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class KlingonShip:
    """An enemy Klingon battlecruiser inside the current quadrant."""
    ship_id: int
    sector_x: int
    sector_y: int
    shields: float = 200.0
    max_shields: float = 200.0

    @property
    def is_alive(self) -> bool:
        return self.shields > 0.0


@dataclass
class QuadrantRecord:
    """Persistent galaxy-wide state for a single 8x8 quadrant."""
    klingons: int = 0
    starbases: int = 0
    stars: int = 0
    scanned: bool = False

    @property
    def summary_code(self) -> str:
        """Standard 3-digit sensor code: KBS (Klingons, Bases, Stars)."""
        return f"{self.klingons}{self.starbases}{self.stars}"


@dataclass
class TrekState:
    """Authoritative state for a Super Star Trek mission."""
    stardate: float = INITIAL_STARDATE
    stardate_start: float = INITIAL_STARDATE
    stardate_limit: float = INITIAL_STARDATE + MISSION_DAYS
    energy: float = INITIAL_ENERGY
    shields: float = INITIAL_SHIELDS
    torpedoes: int = INITIAL_TORPEDOES
    quadrant_x: int = 0
    quadrant_y: int = 0
    sector_x: int = 0
    sector_y: int = 0
    condition: ShipCondition = ShipCondition.GREEN
    is_game_over: bool = False
    victory: bool = False
    game_over_reason: Optional[str] = None

    # Galaxy and Quadrant state
    galaxy: List[List[QuadrantRecord]] = field(default_factory=list)
    klingons_in_quadrant: List[KlingonShip] = field(default_factory=list)
    starbase_in_quadrant: Optional[Tuple[int, int]] = None
    stars_in_quadrant: List[Tuple[int, int]] = field(default_factory=list)
    devices: Dict[Device, float] = field(default_factory=dict)
    history_log: List[str] = field(default_factory=list)
    total_klingons_start: int = 0
    total_starbases_start: int = 0
    rng_seed: Optional[int] = None

    @property
    def total_klingons_remaining(self) -> int:
        return sum(self.galaxy[y][x].klingons for y in range(GALAXY_HEIGHT) for x in range(GALAXY_WIDTH))

    @property
    def total_starbases_remaining(self) -> int:
        return sum(self.galaxy[y][x].starbases for y in range(GALAXY_HEIGHT) for x in range(GALAXY_WIDTH))

    @property
    def quadrant_name(self) -> str:
        reg_idx = (self.quadrant_y * 2 + (self.quadrant_x // 4)) % len(QUADRANT_REGION_NAMES)
        sub_num = (self.quadrant_x % 4) + 1
        return f"{QUADRANT_REGION_NAMES[reg_idx]} {['I', 'II', 'III', 'IV'][sub_num - 1]}"

    @property
    def days_remaining(self) -> float:
        return max(0.0, self.stardate_limit - self.stardate)

    def is_device_operational(self, dev: Device) -> bool:
        return self.devices.get(dev, 0.0) <= 0.0

    def get_sector_entity(self, sx: int, sy: int) -> SectorEntity:
        if sx == self.sector_x and sy == self.sector_y:
            return SectorEntity.ENTERPRISE
        if self.starbase_in_quadrant and (sx, sy) == self.starbase_in_quadrant:
            return SectorEntity.STARBASE
        for k in self.klingons_in_quadrant:
            if k.is_alive and k.sector_x == sx and k.sector_y == sy:
                return SectorEntity.KLINGON
        if (sx, sy) in self.stars_in_quadrant:
            return SectorEntity.STAR
        return SectorEntity.EMPTY


# ---------------------------------------------------------------------------
# Initializer & Setup
# ---------------------------------------------------------------------------

def init_game(seed: Optional[int] = None) -> TrekState:
    """Initializes a new Super Star Trek galaxy and Enterprise state."""
    r = random.Random(seed) if seed is not None else random.Random()

    state = TrekState(rng_seed=seed)

    # Initialize Subsystems (all 0.0 = operational)
    for dev in Device:
        state.devices[dev] = 0.0

    # 1. Generate Galaxy Map (8x8 Quadrants)
    state.galaxy = []
    total_klingons = 0
    total_starbases = 0

    for y in range(GALAXY_HEIGHT):
        row = []
        for x in range(GALAXY_WIDTH):
            # Klingon generation distribution (approx 15-22 across galaxy)
            k_roll = r.random()
            if k_roll < 0.65:
                k = 0
            elif k_roll < 0.88:
                k = 1
            elif k_roll < 0.97:
                k = 2
            else:
                k = 3
            total_klingons += k

            # Starbase distribution (approx 2 to 4 in galaxy)
            b_roll = r.random()
            b = 1 if b_roll < 0.055 else 0
            total_starbases += b

            # Stars (1 to 8 per quadrant)
            s = r.randint(1, 8)

            row.append(QuadrantRecord(klingons=k, starbases=b, stars=s, scanned=False))
        state.galaxy.append(row)

    # Ensure at least 15 Klingons and at least 2 Starbases
    while total_klingons < 15:
        rx, ry = r.randint(0, 7), r.randint(0, 7)
        if state.galaxy[ry][rx].klingons < 3:
            state.galaxy[ry][rx].klingons += 1
            total_klingons += 1

    while total_starbases < 2:
        rx, ry = r.randint(0, 7), r.randint(0, 7)
        if state.galaxy[ry][rx].starbases == 0:
            state.galaxy[ry][rx].starbases = 1
            total_starbases += 1

    state.total_klingons_start = total_klingons
    state.total_starbases_start = total_starbases

    # 2. Place Enterprise at random quadrant and sector
    state.quadrant_x = r.randint(0, GALAXY_WIDTH - 1)
    state.quadrant_y = r.randint(0, GALAXY_HEIGHT - 1)
    state.sector_x = r.randint(0, SECTOR_WIDTH - 1)
    state.sector_y = r.randint(0, SECTOR_HEIGHT - 1)

    # 3. Materialize initial quadrant contents
    _enter_quadrant(state, state.quadrant_x, state.quadrant_y, r=r)

    state.history_log.append(
        f"Stardate {state.stardate:.1f}: Mission commenced. Orders: Destroy {total_klingons} Klingon battlecruisers in {int(MISSION_DAYS)} stardates."
    )
    return state


def _enter_quadrant(state: TrekState, qx: int, qy: int, r: Optional[random.Random] = None) -> None:
    """Populates sector entities when the Enterprise enters a quadrant."""
    rng = r or random.Random()
    state.quadrant_x = qx
    state.quadrant_y = qy
    q_rec = state.galaxy[qy][qx]
    q_rec.scanned = True

    occupied_sectors = {(state.sector_x, state.sector_y)}

    def get_open_sector() -> Tuple[int, int]:
        while True:
            pos = (rng.randint(0, SECTOR_WIDTH - 1), rng.randint(0, SECTOR_HEIGHT - 1))
            if pos not in occupied_sectors:
                occupied_sectors.add(pos)
                return pos

    # Starbase
    state.starbase_in_quadrant = None
    if q_rec.starbases > 0:
        state.starbase_in_quadrant = get_open_sector()

    # Klingons
    state.klingons_in_quadrant = []
    for i in range(q_rec.klingons):
        sx, sy = get_open_sector()
        k_shields = rng.uniform(150.0, 300.0)
        state.klingons_in_quadrant.append(KlingonShip(ship_id=i + 1, sector_x=sx, sector_y=sy, shields=k_shields, max_shields=k_shields))

    # Stars
    state.stars_in_quadrant = []
    for _ in range(q_rec.stars):
        state.stars_in_quadrant.append(get_open_sector())

    _update_ship_condition(state)


def _update_ship_condition(state: TrekState) -> None:
    """Evaluates ship condition tag (GREEN, YELLOW, RED, DOCKED)."""
    # Check docking condition: adjacent to starbase (distance <= 1.5 sectors)
    if state.starbase_in_quadrant:
        bx, by = state.starbase_in_quadrant
        dist = math.hypot(state.sector_x - bx, state.sector_y - by)
        if dist <= 1.5:
            state.condition = ShipCondition.DOCKED
            return

    living_klingons = [k for k in state.klingons_in_quadrant if k.is_alive]
    if living_klingons:
        state.condition = ShipCondition.RED
    elif state.energy < 1000.0:
        state.condition = ShipCondition.YELLOW
    else:
        state.condition = ShipCondition.GREEN


# ---------------------------------------------------------------------------
# Ship Navigation & Movement
# ---------------------------------------------------------------------------

# Course direction angles in radians (1=East/0°, 2=NE/45°, 3=North/90°, 4=NW/135°, 5=West/180°, etc.)
def course_to_vector(course: float) -> Tuple[float, float]:
    """Converts classic Star Trek course direction (1 to 9) to (dx, dy) direction vector."""
    # 1.0 is East (+x, 0), 3.0 is North (0, -y), 5.0 is West (-x, 0), 7.0 is South (0, +y)
    angle = (course - 1.0) * (math.pi / 4.0)
    dx = math.cos(angle)
    dy = -math.sin(angle)  # In screen/grid coordinates, -y is North
    return dx, dy


def navigate(
    state: TrekState,
    course: float,
    warp: float,
    rng: Optional[random.Random] = None,
) -> Tuple[TrekState, bool, str]:
    """
    Executes warp or impulse navigation.
    Warp < 1.0 moves within the quadrant (impulse).
    Warp >= 1.0 traverses quadrants.
    """
    r = rng or random.Random()
    _check_game_over(state)
    if state.is_game_over:
        return state, False, state.game_over_reason or "Mission is over."

    # Clamp warp factor
    warp = max(0.1, min(8.0, warp))
    if warp > 0.2 and not state.is_device_operational(Device.WARP_ENGINES):
        return state, False, "Warp engines are damaged! Limited to impulse speed (warp <= 0.2)."

    # Energy requirement: 8 units per sector step or proportional to warp
    sectors_to_move = int(round(warp * 8.0))
    energy_cost = int(warp * 8.0 * (12.0 if warp >= 1.0 else 3.0))

    if state.energy < energy_cost:
        if state.energy <= 0:
            _check_game_over(state)
            return state, False, state.game_over_reason or "Enterprise ran out of energy."
        return state, False, f"Insufficient energy! Navigation requires {energy_cost} units, but only {int(state.energy)} available."

    state.energy -= energy_cost

    # Advance calendar: warp consumes stardates
    stardate_cost = max(0.1, round(warp * 0.4, 2))
    state.stardate += stardate_cost

    # Vector movement step-by-step
    dx, dy = course_to_vector(course)
    norm = math.hypot(dx, dy) or 1.0
    step_dx = dx / norm
    step_dy = dy / norm

    # Calculate global coordinates in sub-sector precision
    current_global_x = state.quadrant_x * 8.0 + state.sector_x
    current_global_y = state.quadrant_y * 8.0 + state.sector_y

    hit_obstacle = False
    obstacle_msg = ""

    for _ in range(sectors_to_move):
        next_gx = current_global_x + step_dx
        next_gy = current_global_y + step_dy

        # Check galaxy perimeter boundary
        if next_gx < 0 or next_gx >= 64 or next_gy < 0 or next_gy >= 64:
            hit_obstacle = True
            obstacle_msg = "Enterprise encountered the galactic energy barrier! Navigation halted."
            break

        # Check local sector obstacle collision if within the same quadrant
        next_qx = int(next_gx // 8)
        next_qy = int(next_gy // 8)
        next_sx = int(next_gx % 8)
        next_sy = int(next_gy % 8)

        if next_qx == state.quadrant_x and next_qy == state.quadrant_y:
            ent = state.get_sector_entity(next_sx, next_sy)
            if ent in (SectorEntity.STAR, SectorEntity.STARBASE, SectorEntity.KLINGON):
                hit_obstacle = True
                obstacle_msg = f"Navigation stopped to prevent collision with {ent.value.lower()} at sector {next_sx+1},{next_sy+1}."
                break

        current_global_x = next_gx
        current_global_y = next_gy

    new_qx = int(max(0, min(7, current_global_x // 8)))
    new_qy = int(max(0, min(7, current_global_y // 8)))
    new_sx = int(max(0, min(7, current_global_x % 8)))
    new_sy = int(max(0, min(7, current_global_y % 8)))

    state.sector_x = new_sx
    state.sector_y = new_sy

    # Entered a new quadrant?
    if new_qx != state.quadrant_x or new_qy != state.quadrant_y:
        _enter_quadrant(state, new_qx, new_qy, r=r)
        msg = f"Entered quadrant {state.quadrant_name} (Q: {new_qx+1},{new_qy+1}  S: {new_sx+1},{new_sy+1})."
    else:
        _update_ship_condition(state)
        msg = f"Moved to sector {new_sx+1},{new_sy+1} in {state.quadrant_name}."

    if hit_obstacle and obstacle_msg:
        msg += f" {obstacle_msg}"

    # Auto-repair devices slightly over elapsed time
    _repair_subsystems(state, stardate_cost)

    # Klingon counterattack if present in quadrant
    k_msg = _klingon_counterattack(state, r=r)
    if k_msg:
        msg += " " + k_msg

    # Check victory / defeat conditions
    _check_game_over(state)

    state.history_log.append(f"Stardate {state.stardate:.1f}: {msg}")
    return state, True, msg


# ---------------------------------------------------------------------------
# Weapons Systems: Phasers & Photon Torpedoes
# ---------------------------------------------------------------------------

def fire_phasers(
    state: TrekState,
    energy_to_fire: float,
    rng: Optional[random.Random] = None,
) -> Tuple[TrekState, bool, str]:
    """Fires ship's phasers, dividing energy among all Klingons in the quadrant."""
    r = rng or random.Random()
    if state.is_game_over:
        return state, False, "Mission is over."

    if not state.is_device_operational(Device.PHASER_CONTROL):
        return state, False, "Phaser control subsystem is damaged and offline!"

    living_klingons = [k for k in state.klingons_in_quadrant if k.is_alive]
    if not living_klingons:
        return state, False, "No Klingon targets detected in this quadrant."

    if energy_to_fire <= 0:
        return state, False, "Must specify a positive energy amount to fire."

    if state.energy < energy_to_fire:
        return state, False, f"Insufficient energy! Have {int(state.energy)} units, requested {int(energy_to_fire)}."

    state.energy -= energy_to_fire

    # Divide energy evenly among targets
    power_per_klingon = energy_to_fire / len(living_klingons)
    destroyed_count = 0
    hit_details = []

    for k in living_klingons:
        dist = max(1.0, math.hypot(state.sector_x - k.sector_x, state.sector_y - k.sector_y))
        # Distance attenuation formula from 1978 BASIC listing
        hit_energy = (power_per_klingon / dist) * r.uniform(0.7, 1.2)
        hit_energy = round(hit_energy, 1)

        k.shields -= hit_energy
        if k.shields <= 0:
            k.shields = 0.0
            destroyed_count += 1
            hit_details.append(f"Klingon at {k.sector_x+1},{k.sector_y+1} destroyed!")
        else:
            hit_details.append(f"Klingon at {k.sector_x+1},{k.sector_y+1} hit for {int(hit_energy)} units (shields: {int(k.shields)}).")

    # Update galaxy quadrant count
    state.galaxy[state.quadrant_y][state.quadrant_x].klingons = max(
        0, state.galaxy[state.quadrant_y][state.quadrant_x].klingons - destroyed_count
    )

    msg = f"Phasers fired ({int(energy_to_fire)} units). " + " ".join(hit_details)

    # Klingon counterattack if any survived
    k_msg = _klingon_counterattack(state, r=r)
    if k_msg:
        msg += " " + k_msg

    _update_ship_condition(state)
    _check_game_over(state)
    state.history_log.append(f"Stardate {state.stardate:.1f}: {msg}")
    return state, True, msg


def fire_torpedo(
    state: TrekState,
    course: float,
    rng: Optional[random.Random] = None,
) -> Tuple[TrekState, bool, str]:
    """Fires a high-yield photon torpedo along a direction vector (course 1-9)."""
    r = rng or random.Random()
    if state.is_game_over:
        return state, False, "Mission is over."

    if not state.is_device_operational(Device.PHOTON_TUBES):
        return state, False, "Photon torpedo tubes are damaged and offline!"

    if state.torpedoes < 1:
        return state, False, "All photon torpedoes expended! Dock at starbase to reload."

    state.torpedoes -= 1

    dx, dy = course_to_vector(course)
    norm = math.hypot(dx, dy) or 1.0
    step_dx = dx / norm
    step_dy = dy / norm

    cur_x = float(state.sector_x)
    cur_y = float(state.sector_y)
    hit_msg = ""
    hit_something = False

    for _ in range(12):
        cur_x += step_dx
        cur_y += step_dy

        sx = int(round(cur_x))
        sy = int(round(cur_y))

        # Flew out of quadrant
        if sx < 0 or sx >= SECTOR_WIDTH or sy < 0 or sy >= SECTOR_HEIGHT:
            hit_msg = "Torpedo flew out of quadrant into deep space (missed)."
            break

        # Check entity hit
        ent = state.get_sector_entity(sx, sy)
        if ent == SectorEntity.KLINGON:
            # Hit Klingon!
            for k in state.klingons_in_quadrant:
                if k.is_alive and k.sector_x == sx and k.sector_y == sy:
                    k.shields = 0.0
                    state.galaxy[state.quadrant_y][state.quadrant_x].klingons = max(
                        0, state.galaxy[state.quadrant_y][state.quadrant_x].klingons - 1
                    )
                    hit_msg = f"*** DIRECT HIT! *** Klingon battlecruiser at {sx+1},{sy+1} was annihilated!"
                    hit_something = True
                    break
            break
        elif ent == SectorEntity.STAR:
            hit_msg = f"Torpedo struck a star at {sx+1},{sy+1} and dissipated in solar flares."
            hit_something = True
            break
        elif ent == SectorEntity.STARBASE:
            state.starbase_in_quadrant = None
            state.galaxy[state.quadrant_y][state.quadrant_x].starbases = 0
            hit_msg = f"*** TRAGIC ERROR *** Starbase at {sx+1},{sy+1} was destroyed by your torpedo! Starfleet court martial warning!"
            hit_something = True
            break

    msg = f"Torpedo fired on course {course:.1f}. {hit_msg}"

    # Klingon counterattack if any survived
    k_msg = _klingon_counterattack(state, r=r)
    if k_msg:
        msg += " " + k_msg

    _update_ship_condition(state)
    _check_game_over(state)
    state.history_log.append(f"Stardate {state.stardate:.1f}: {msg}")
    return state, True, msg


# ---------------------------------------------------------------------------
# Shield Management & Starbase Docking
# ---------------------------------------------------------------------------

def transfer_shields(state: TrekState, amount: float) -> Tuple[TrekState, bool, str]:
    """Transfers energy between main reserves and protective deflector shields."""
    if state.is_game_over:
        return state, False, "Mission is over."

    if not state.is_device_operational(Device.SHIELD_CONTROL):
        return state, False, "Shield control subsystem is damaged and offline!"

    if amount > 0:
        # Raising shields (transfer from energy to shields)
        max_possible = min(amount, state.energy, MAX_SHIELDS - state.shields)
        if max_possible <= 0:
            return state, False, "Cannot raise shields further (max shield capacity or no energy)."
        state.energy -= max_possible
        state.shields += max_possible
        msg = f"Transferred {int(max_possible)} units into shields (Shields: {int(state.shields)}, Energy: {int(state.energy)})."
    else:
        # Lowering shields (transfer from shields to energy)
        drop = min(abs(amount), state.shields, MAX_ENERGY - state.energy)
        if drop <= 0:
            return state, False, "Cannot lower shields further."
        state.shields -= drop
        state.energy += drop
        msg = f"Lowered shields by {int(drop)} units into energy reserves (Shields: {int(state.shields)}, Energy: {int(state.energy)})."

    _update_ship_condition(state)
    state.history_log.append(f"Stardate {state.stardate:.1f}: {msg}")
    return state, True, msg


def dock_at_starbase(state: TrekState) -> Tuple[TrekState, bool, str]:
    """Replenishes energy, torpedoes, and fully repairs all damaged systems at Starbase."""
    if state.is_game_over:
        return state, False, "Mission is over."

    if not state.starbase_in_quadrant:
        return state, False, "No Federation Starbase present in this quadrant."

    bx, by = state.starbase_in_quadrant
    dist = math.hypot(state.sector_x - bx, state.sector_y - by)
    if dist > 1.5:
        return state, False, f"Not adjacent to Starbase! Current distance is {dist:.1f} sectors. Must be within 1.5 sectors."

    # Execute full resupply
    state.energy = MAX_ENERGY
    state.torpedoes = MAX_TORPEDOES
    state.shields = max(state.shields, INITIAL_SHIELDS)
    for dev in state.devices:
        state.devices[dev] = 0.0

    state.condition = ShipCondition.DOCKED
    msg = "Docked at Federation Starbase. Systems repaired, energy replenished to 3000, torpedoes reloaded to 10."
    state.history_log.append(f"Stardate {state.stardate:.1f}: {msg}")
    return state, True, msg


# ---------------------------------------------------------------------------
# Enemy Attacks, Subsystem Damage, & Repairs
# ---------------------------------------------------------------------------

def _klingon_counterattack(state: TrekState, r: Optional[random.Random] = None) -> str:
    """Surviving Klingons fire disruptors back at Enterprise."""
    rng = r or random.Random()
    living = [k for k in state.klingons_in_quadrant if k.is_alive]
    if not living or state.is_game_over:
        return ""

    if state.condition == ShipCondition.DOCKED:
        return "Starbase deflector screens shielded the Enterprise from Klingon fire."

    total_damage = 0.0
    for k in living:
        dist = max(1.0, math.hypot(state.sector_x - k.sector_x, state.sector_y - k.sector_y))
        # Klingon disruptor fire formula
        shot_power = (k.shields / dist) * rng.uniform(1.0, 2.5)
        total_damage += shot_power

    total_damage = round(total_damage, 1)

    # Shields absorb damage first
    if state.shields >= total_damage:
        state.shields -= total_damage
        return f"Klingons attacked! Shields absorbed {int(total_damage)} units of damage (Shields remaining: {int(state.shields)})."
    else:
        absorbed = state.shields
        excess = total_damage - absorbed
        state.shields = 0.0
        state.energy -= excess

        # Subsystem damage from hull breach
        damaged_dev = rng.choice(list(Device))
        state.devices[damaged_dev] += rng.uniform(1.0, 4.0)

        return f"*** SHIELDS COLLAPSED! *** Sustained {int(total_damage)} units of damage! Hull breach damaged {damaged_dev.value}."


def _repair_subsystems(state: TrekState, elapsed_stardates: float) -> None:
    """Gradually repairs damaged subsystems over elapsed mission stardates."""
    for dev in state.devices:
        if state.devices[dev] > 0.0:
            state.devices[dev] = max(0.0, state.devices[dev] - elapsed_stardates * 2.0)


# ---------------------------------------------------------------------------
# Scanners: Long-Range Scan & Galactic Chart
# ---------------------------------------------------------------------------

def long_range_scan(state: TrekState) -> List[List[Tuple[int, int, int]]]:
    """
    Returns a 3x3 array of (klingons, starbases, stars) for quadrants
    adjacent to and including the current quadrant.
    """
    scan_grid = []
    qx = state.quadrant_x
    qy = state.quadrant_y

    for dy in [-1, 0, 1]:
        row = []
        for dx in [-1, 0, 1]:
            tx = qx + dx
            ty = qy + dy
            if 0 <= tx < GALAXY_WIDTH and 0 <= ty < GALAXY_HEIGHT:
                q = state.galaxy[ty][tx]
                q.scanned = True
                row.append((q.klingons, q.starbases, q.stars))
            else:
                row.append((-1, -1, -1))  # Edge of galaxy
        scan_grid.append(row)

    return scan_grid


# ---------------------------------------------------------------------------
# Victory, Defeat, and Evaluation
# ---------------------------------------------------------------------------

def _check_game_over(state: TrekState) -> None:
    """Authoritative game termination evaluation."""
    if state.is_game_over:
        return

    # Victory check: all Klingons eliminated
    if state.total_klingons_remaining <= 0:
        state.is_game_over = True
        state.victory = True
        state.game_over_reason = "Mission accomplished! All Klingon warships in the galaxy have been destroyed!"
        state.history_log.append(f"Stardate {state.stardate:.1f}: {state.game_over_reason}")
        return

    # Defeat check 1: Out of energy
    if state.energy <= 0:
        state.is_game_over = True
        state.victory = False
        state.game_over_reason = "Life support systems failed! The Enterprise ran completely out of energy."
        state.history_log.append(f"Stardate {state.stardate:.1f}: {state.game_over_reason}")
        return

    # Defeat check 2: Time expired
    if state.stardate >= state.stardate_limit:
        state.is_game_over = True
        state.victory = False
        state.game_over_reason = f"Stardate deadline exceeded! Klingons conquered Federation territory ({state.total_klingons_remaining} warships remain)."
        state.history_log.append(f"Stardate {state.stardate:.1f}: {state.game_over_reason}")
        return


def calculate_score(state: TrekState) -> int:
    """Calculates final Starfleet command efficiency rating score."""
    if not state.victory:
        k_killed = state.total_klingons_start - state.total_klingons_remaining
        return max(0, k_killed * 100 - int(state.stardate - state.stardate_start) * 10)

    # Victory calculation
    klingon_pts = state.total_klingons_start * 250
    time_pts = int(state.days_remaining * 100)
    energy_pts = int(state.energy * 0.2)
    bases_pts = state.total_starbases_remaining * 200

    return klingon_pts + time_pts + energy_pts + bases_pts


# ---------------------------------------------------------------------------
# Terminal CLI Runner (Zero external dependencies)
# ---------------------------------------------------------------------------

def play_cli(seed: Optional[int] = None) -> int:
    """Interactive text-mode Super Star Trek session."""
    print("=" * 64)
    print("                   SUPER STAR TREK (1978)")
    print("      Starfleet Command Strategic Galactic Simulation")
    print("=" * 64)

    state = init_game(seed=seed)
    print(f"\nWelcome, Commander. Enterprise is stationed in {state.quadrant_name}.")
    print(f"Mission: Neutralize {state.total_klingons_remaining} Klingon battlecruisers before Stardate {state.stardate_limit:.1f}.\n")

    while not state.is_game_over:
        print("-" * 64)
        print(f"Stardate: {state.stardate:.1f}  |  Condition: {state.condition.value}  |  Days Left: {state.days_remaining:.1f}")
        print(f"Energy: {int(state.energy)}  |  Shields: {int(state.shields)}  |  Torpedoes: {state.torpedoes}")
        print(f"Quadrant: {state.quadrant_name} ({state.quadrant_x+1},{state.quadrant_y+1})  |  Sector: {state.sector_x+1},{state.sector_y+1}")
        print(f"Klingons Left in Galaxy: {state.total_klingons_remaining}  |  Bases: {state.total_starbases_remaining}")

        print("\n--- SHORT RANGE SENSOR SCAN ---")
        for y in range(SECTOR_HEIGHT):
            row_str = " ".join(state.get_sector_entity(x, y).symbol for x in range(SECTOR_WIDTH))
            print(f"  {row_str}")

        print("\nCommands: 1. NAV (Warp/Move)  2. PHA (Phasers)  3. TOR (Torpedoes)")
        print("          4. SHE (Shields)    5. LRS (Scan)     6. DOC (Dock)  7. Quit")

        cmd = input("\nEnter Command (1-7): ").strip()
        if cmd == "1":
            try:
                crs = float(input("Course direction (1-9, e.g. 1=East, 3=North, 5=West, 7=South): ").strip())
                wrp = float(input("Warp factor (0.1 to 8.0, e.g. 0.2=sector impulse, 1.0=quadrant warp): ").strip())
                _, _, msg = navigate(state, crs, wrp)
                print(f">> {msg}\n")
            except ValueError:
                print(">> Invalid navigation values.")
        elif cmd == "2":
            try:
                nrg = float(input(f"Energy to fire into phasers (max {int(state.energy)}): ").strip())
                _, _, msg = fire_phasers(state, nrg)
                print(f">> {msg}\n")
            except ValueError:
                print(">> Invalid energy value.")
        elif cmd == "3":
            try:
                crs = float(input("Torpedo course direction (1-9): ").strip())
                _, _, msg = fire_torpedo(state, crs)
                print(f">> {msg}\n")
            except ValueError:
                print(">> Invalid course.")
        elif cmd == "4":
            try:
                amt = float(input(f"Energy transfer to shields (+ to raise, - to lower, max {MAX_SHIELDS}): ").strip())
                _, _, msg = transfer_shields(state, amt)
                print(f">> {msg}\n")
            except ValueError:
                print(">> Invalid amount.")
        elif cmd == "5":
            scan = long_range_scan(state)
            print("\n--- LONG RANGE SENSOR SCAN (KBS: Klingons Bases Stars) ---")
            for r in scan:
                row_str = " | ".join(f"{k}{b}{s}" if k >= 0 else "***" for k, b, s in r)
                print(f"   {row_str}")
            print("")
        elif cmd == "6":
            _, _, msg = dock_at_starbase(state)
            print(f">> {msg}\n")
        elif cmd in ("7", "q", "quit"):
            print("Commander resigned commission. Mission aborted.")
            return 0

    print("\n" + "=" * 64)
    if state.victory:
        print("                   STARFLEET VICTORY!")
        print(state.game_over_reason)
        print(f"Final Starfleet Command Rating: {calculate_score(state)} points.")
    else:
        print("                  MISSION FAILED")
        print(state.game_over_reason)
    print("=" * 64 + "\n")
    return 0
