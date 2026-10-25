"""
games/oregon_trail/engine.py - Pure Python engine for The Oregon Trail (1848 Pioneer Simulation).

Based on the historical 1971 CDC Cyber edition by Don Rawitsch, Bill Heinemann,
and Paul Dillenberger, published in Creative Computing (1978).
Uses 100% Python standard library.
"""

from dataclasses import dataclass, field
import datetime
from enum import Enum
import math
import random
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enumerations & Domain Constants
# ---------------------------------------------------------------------------

class Pace(str, Enum):
    STEADY = "STEADY"        # ~14 miles/day, sustainable pace
    STRENUOUS = "STRENUOUS"  # ~18 miles/day, minor health strain
    GRUELING = "GRUELING"    # ~22 miles/day, heavy health and oxen strain

    @property
    def daily_miles(self) -> float:
        if self == Pace.STEADY:
            return 14.0
        elif self == Pace.STRENUOUS:
            return 18.0
        return 22.0

    @property
    def health_drain_per_day(self) -> float:
        if self == Pace.STEADY:
            return 0.2
        elif self == Pace.STRENUOUS:
            return 0.8
        return 2.0


class Rations(str, Enum):
    FILLING = "FILLING"      # 3.0 lbs/day per person (+health recovery)
    MEAGER = "MEAGER"        # 2.0 lbs/day per person (stable)
    BARE_BONES = "BARE_BONES"# 1.0 lb/day per person (health degradation)

    @property
    def daily_lbs(self) -> float:
        if self == Rations.FILLING:
            return 3.0
        elif self == Rations.MEAGER:
            return 2.0
        return 1.0

    @property
    def health_delta_per_day(self) -> float:
        if self == Rations.FILLING:
            return 1.2
        elif self == Rations.MEAGER:
            return 0.0
        return -1.5


class Weather(str, Enum):
    FAIR = "FAIR"
    WARM = "WARM"
    HOT = "HOT"
    COOL = "COOL"
    RAINY = "RAINY"
    COLD = "COLD"
    VERY_COLD = "VERY_COLD"
    BLIZZARD = "BLIZZARD"

    @property
    def speed_multiplier(self) -> float:
        if self in (Weather.FAIR, Weather.WARM):
            return 1.0
        elif self in (Weather.HOT, Weather.COOL):
            return 0.9
        elif self in (Weather.RAINY, Weather.COLD):
            return 0.75
        elif self == Weather.VERY_COLD:
            return 0.6
        return 0.35  # BLIZZARD

    @property
    def health_drain(self) -> float:
        if self in (Weather.FAIR, Weather.WARM):
            return 0.0
        elif self in (Weather.COOL, Weather.HOT):
            return 0.3
        elif self in (Weather.RAINY, Weather.COLD):
            return 0.8
        elif self == Weather.VERY_COLD:
            return 1.8
        return 3.5  # BLIZZARD


class Profession(str, Enum):
    BANKER = "BANKER"        # $1,600 starting cash, standard scoring
    CARPENTER = "CARPENTER"  # $800 starting cash, repair bonus, 2x score
    FARMER = "FARMER"        # $400 starting cash, oxen care bonus, 3x score

    @property
    def starting_cash(self) -> float:
        if self == Profession.BANKER:
            return 1600.0
        elif self == Profession.CARPENTER:
            return 800.0
        return 400.0

    @property
    def score_multiplier(self) -> float:
        if self == Profession.BANKER:
            return 1.0
        elif self == Profession.CARPENTER:
            return 2.0
        return 3.0


class LandmarkType(str, Enum):
    TOWN = "TOWN"
    FORT = "FORT"
    RIVER = "RIVER"
    SCENIC_LANDMARK = "SCENIC_LANDMARK"
    MOUNTAIN_PASS = "MOUNTAIN_PASS"
    DESTINATION = "DESTINATION"


@dataclass
class Landmark:
    """Historical milestone along the 2,040-mile Oregon Trail."""
    name: str
    distance_miles: float
    landmark_type: LandmarkType
    description: str
    river_depth_ft: Optional[float] = None
    has_store: bool = False


# 17 Authentic Historical Trail Landmarks from Missouri to Oregon
LANDMARKS: List[Landmark] = [
    Landmark("Independence, Missouri", 0.0, LandmarkType.TOWN, "Trailhead jump-off point for western emigrants.", has_store=True),
    Landmark("Kansas River Crossing", 102.0, LandmarkType.RIVER, "A 200-yard wide prairie river. Ferry service available.", river_depth_ft=4.5),
    Landmark("Big Blue River Crossing", 185.0, LandmarkType.RIVER, "Swift tributary prone to spring flash floods.", river_depth_ft=3.2),
    Landmark("Fort Kearney", 319.0, LandmarkType.FORT, "U.S. Army outpost guarding the Platte River Valley.", has_store=True),
    Landmark("Chimney Rock", 554.0, LandmarkType.SCENIC_LANDMARK, "Towering 300-foot spire signaling the Rocky Mountain approach."),
    Landmark("Fort Laramie", 640.0, LandmarkType.FORT, "Former fur trading post at the junction of the Laramie and North Platte.", has_store=True),
    Landmark("Independence Rock", 830.0, LandmarkType.SCENIC_LANDMARK, "The 'Great Register of the Desert' carved with pioneer signatures."),
    Landmark("South Pass", 932.0, LandmarkType.MOUNTAIN_PASS, "Gentle saddle crossing the Continental Divide into Oregon Territory."),
    Landmark("Fort Bridger", 989.0, LandmarkType.FORT, "Jim Bridger's supply station along the Black's Fork River.", has_store=True),
    Landmark("Green River Crossing", 1020.0, LandmarkType.RIVER, "A deep, dangerous glacial river with fast currents.", river_depth_ft=6.5),
    Landmark("Soda Springs", 1180.0, LandmarkType.SCENIC_LANDMARK, "Carbonated mineral springs steaming in the Idaho hills."),
    Landmark("Fort Hall", 1288.0, LandmarkType.FORT, "Hudson's Bay Company post on the Snake River.", has_store=True),
    Landmark("Snake River Crossing", 1534.0, LandmarkType.RIVER, "Treacherous crossing requiring floating across islands.", river_depth_ft=5.8),
    Landmark("Fort Boise", 1642.0, LandmarkType.FORT, "Adobe trading outpost on the lower Snake River plains.", has_store=True),
    Landmark("Blue Mountains", 1818.0, LandmarkType.MOUNTAIN_PASS, "Steep, heavily forested granite peaks prone to early snows."),
    Landmark("The Dalles", 1940.0, LandmarkType.TOWN, "Columbia River port. Choose between Barlow Road toll or river rafting.", has_store=True),
    Landmark("Willamette Valley", 2040.0, LandmarkType.DESTINATION, "The promised fertile land of Oregon! The journey ends in triumph!"),
]


# ---------------------------------------------------------------------------
# Party Member & Inventory Models
# ---------------------------------------------------------------------------

@dataclass
class PartyMember:
    """Represents a pioneer traveler."""
    name: str
    is_leader: bool = False
    health: float = 100.0  # 0 to 100
    diseases: List[str] = field(default_factory=list)

    @property
    def is_alive(self) -> bool:
        return self.health > 0.0

    @property
    def health_status(self) -> str:
        if not self.is_alive:
            return "Dead"
        elif self.health >= 80.0:
            return "Good"
        elif self.health >= 55.0:
            return "Fair"
        elif self.health >= 30.0:
            return "Poor"
        return "Very Poor"


@dataclass
class Inventory:
    """Pioneer wagon supplies and funds."""
    cash: float = 800.0
    oxen: int = 4            # Need >= 2 to pull wagon; 4-8 recommended
    food: float = 400.0      # Pounds of food
    clothing: int = 5        # Sets of warm clothing
    ammunition: int = 150    # Bullets (boxes of 50)
    wagon_wheels: int = 2    # Spare parts
    wagon_axles: int = 2
    wagon_tongues: int = 2
    medical_kits: int = 2


@dataclass
class TrailEvent:
    """Random or situational incident occurring during travel."""
    event_type: str
    title: str
    description: str
    impact_summary: str


# Base Store Prices at Trailhead (Independence, MO)
BASE_PRICES: Dict[str, float] = {
    "oxen": 25.0,           # Per ox ($50 per yoke of two)
    "food": 0.20,           # Per pound
    "clothing": 10.0,       # Per warm set
    "ammunition": 2.0,      # Per box of 50 bullets ($0.04/round)
    "wagon_wheel": 10.0,    # Per spare wheel
    "wagon_axle": 10.0,     # Per spare axle
    "wagon_tongue": 10.0,   # Per spare tongue
    "medical_kit": 15.0,    # Per medicine kit
}


def get_item_price(item: str, miles_traveled: float) -> float:
    """Calculates inflation-adjusted supply cost along the trail."""
    base = BASE_PRICES.get(item, 10.0)
    # Fort prices increase between 1.0x at Independence to 2.2x near Oregon
    inflation = 1.0 + (miles_traveled / 2040.0) * 1.2
    return round(base * inflation, 2)


# ---------------------------------------------------------------------------
# Trail State Model
# ---------------------------------------------------------------------------

@dataclass
class TrailState:
    """Complete authoritative state for an Oregon Trail journey."""
    start_date: datetime.date = field(default_factory=lambda: datetime.date(1848, 4, 15))
    current_date: datetime.date = field(default_factory=lambda: datetime.date(1848, 4, 15))
    miles_traveled: float = 0.0
    total_trail_miles: float = 2040.0
    current_landmark_idx: int = 0
    at_landmark: bool = True
    party: List[PartyMember] = field(default_factory=list)
    inventory: Inventory = field(default_factory=Inventory)
    pace: Pace = Pace.STEADY
    rations: Rations = Rations.FILLING
    weather: Weather = Weather.FAIR
    profession: Profession = Profession.CARPENTER
    is_game_over: bool = False
    victory: bool = False
    game_over_reason: Optional[str] = None
    active_event: Optional[TrailEvent] = None
    pending_river: Optional[Landmark] = None
    history_log: List[str] = field(default_factory=list)
    rng_seed: Optional[int] = None

    @property
    def living_members(self) -> List[PartyMember]:
        return [m for m in self.party if m.is_alive]

    @property
    def leader_alive(self) -> bool:
        leader = next((m for m in self.party if m.is_leader), None)
        return leader.is_alive if leader else False

    @property
    def current_landmark(self) -> Landmark:
        idx = min(self.current_landmark_idx, len(LANDMARKS) - 1)
        return LANDMARKS[idx]

    @property
    def next_landmark(self) -> Optional[Landmark]:
        if self.current_landmark_idx + 1 < len(LANDMARKS):
            return LANDMARKS[self.current_landmark_idx + 1]
        return None

    @property
    def distance_to_next_landmark(self) -> float:
        nxt = self.next_landmark
        if nxt:
            return max(0.0, nxt.distance_miles - self.miles_traveled)
        return max(0.0, self.total_trail_miles - self.miles_traveled)

    @property
    def overall_health_status(self) -> str:
        living = self.living_members
        if not living:
            return "Dead"
        avg = sum(m.health for m in living) / len(living)
        if avg >= 80.0:
            return "Good"
        elif avg >= 55.0:
            return "Fair"
        elif avg >= 30.0:
            return "Poor"
        return "Very Poor"


# ---------------------------------------------------------------------------
# Simulation Engine Initialization & Actions
# ---------------------------------------------------------------------------

def init_game(
    profession: str = "CARPENTER",
    leader_name: str = "Captain Lewis",
    companion_names: Optional[List[str]] = None,
    starting_cash: Optional[float] = None,
    seed: Optional[int] = None,
) -> TrailState:
    """Initializes a new Oregon Trail journey with historically authentic defaults."""
    try:
        prof = Profession(profession.upper())
    except (ValueError, KeyError):
        prof = Profession.CARPENTER

    cash = starting_cash if starting_cash is not None else prof.starting_cash

    # Default party members
    comps = companion_names or ["Martha", "Samuel", "Ezekiel", "Sarah"]
    party: List[PartyMember] = [PartyMember(name=leader_name, is_leader=True, health=100.0)]
    for c_name in comps[:4]:
        party.append(PartyMember(name=c_name, is_leader=False, health=100.0))

    # Initial supplies: standard starter kit suitable for immediate travel
    inv = Inventory(
        cash=cash,
        oxen=4,              # 2 yoke of oxen
        food=400.0,          # 400 lbs grain/meat
        clothing=5,          # 1 set per traveler
        ammunition=150,      # 3 boxes of 50 bullets
        wagon_wheels=2,
        wagon_axles=2,
        wagon_tongues=2,
        medical_kits=2,
    )

    state = TrailState(
        start_date=datetime.date(1848, 4, 15),
        current_date=datetime.date(1848, 4, 15),
        miles_traveled=0.0,
        current_landmark_idx=0,
        at_landmark=True,
        party=party,
        inventory=inv,
        pace=Pace.STEADY,
        rations=Rations.FILLING,
        weather=Weather.FAIR,
        profession=prof,
        is_game_over=False,
        victory=False,
        history_log=["April 15, 1848: Departed Independence, Missouri for Oregon Territory!"],
        rng_seed=seed,
    )
    return state


def step_turn(
    state: TrailState,
    action: str = "TRAVEL",
    days: int = 4,
    rng: Optional[random.Random] = None,
    enable_incidents: bool = True,
) -> TrailState:
    """Dispatches turn actions cleanly according to engine rules."""
    r = rng or (random.Random(state.rng_seed) if state.rng_seed is not None else random.Random())
    act = action.upper()

    if state.is_game_over:
        return state

    if act == "TRAVEL":
        return travel_cycle(state, days=days, rng=r, enable_incidents=enable_incidents)
    elif act == "REST":
        return rest_cycle(state, days=days, rng=r)
    return state


def travel_cycle(
    state: TrailState,
    days: int = 4,
    rng: Optional[random.Random] = None,
    enable_incidents: bool = True,
) -> TrailState:
    """Simulates a multi-day journey stretch along the trail."""
    r = rng or random.Random()
    if state.is_game_over:
        return state

    # 1. Check Oxen readiness
    if state.inventory.oxen < 1:
        state.is_game_over = True
        state.game_over_reason = "You have no oxen to pull the wagon! Your party is stranded in the wilderness."
        state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: All oxen lost. Journey ended.")
        return state

    # 2. Compute Travel Distance
    # Base daily miles from pace
    daily = state.pace.daily_miles
    # Oxen speed factor: 4+ oxen = 100%, 2 oxen = 75%, 1 ox = 40%
    if state.inventory.oxen >= 4:
        ox_factor = 1.0
    elif state.inventory.oxen >= 2:
        ox_factor = 0.75
    else:
        ox_factor = 0.40

    weather_factor = state.weather.speed_multiplier
    cycle_distance = daily * ox_factor * weather_factor * days

    # Add slight terrain variance
    cycle_distance *= r.uniform(0.9, 1.1)
    cycle_distance = round(cycle_distance, 1)

    # 3. Check for Intercepting Next Landmark
    nxt_landmark = state.next_landmark
    traveled = cycle_distance
    reached_landmark = False

    if nxt_landmark:
        dist_to_lm = nxt_landmark.distance_miles - state.miles_traveled
        if cycle_distance >= dist_to_lm:
            traveled = dist_to_lm
            reached_landmark = True

    state.miles_traveled += traveled

    # 4. Advance Calendar
    state.current_date += datetime.timedelta(days=days)

    # 5. Consume Food Rations
    living_count = len(state.living_members)
    daily_food_rate = state.rations.daily_lbs
    food_needed = daily_food_rate * living_count * days

    if state.inventory.food >= food_needed:
        state.inventory.food -= food_needed
        food_starvation_ratio = 0.0
    else:
        # Ran out of food!
        deficit = food_needed - state.inventory.food
        food_starvation_ratio = deficit / max(1.0, food_needed)
        state.inventory.food = 0.0

    # 6. Update Health for Living Members
    ration_health_delta = state.rations.health_delta_per_day * days
    pace_drain = state.pace.health_drain_per_day * days
    weather_drain = state.weather.health_drain * days
    starvation_drain = food_starvation_ratio * 25.0

    # Clothing protection against cold
    clothing_penalty = 0.0
    if state.weather in (Weather.COLD, Weather.VERY_COLD, Weather.BLIZZARD):
        needed_clothes = living_count
        if state.inventory.clothing < needed_clothes:
            clothing_penalty = (needed_clothes - state.inventory.clothing) * 3.0

    for m in state.party:
        if not m.is_alive:
            continue

        # Net health change
        net_delta = ration_health_delta - (pace_drain + weather_drain + starvation_drain + clothing_penalty)
        # Illness drain
        if m.diseases:
            net_delta -= len(m.diseases) * 2.5 * days

        m.health = max(0.0, min(100.0, m.health + net_delta))

        # Check death
        if m.health <= 0.0:
            m.health = 0.0
            death_msg = f"{m.name} has died of exhaustion and hardship on the trail."
            state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: {death_msg}")

    # 7. Check Victory or Fatal Impeachment/Loss
    if not state.living_members:
        state.is_game_over = True
        state.game_over_reason = "Everyone in your party has perished. The journey has ended in tragedy."
        return state

    if not state.leader_alive:
        state.is_game_over = True
        state.game_over_reason = "Your wagon party leader has died. The remaining pioneers could not continue."
        return state

    # 8. Check Destination Victory
    if state.miles_traveled >= state.total_trail_miles:
        state.miles_traveled = state.total_trail_miles
        state.is_game_over = True
        state.victory = True
        state.game_over_reason = "Congratulations! You have safely completed the Oregon Trail and reached Willamette Valley!"
        state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: Reached Oregon! Victory!")
        return state

    # 9. Landmark Arrival
    state.active_event = None
    if reached_landmark and nxt_landmark:
        state.current_landmark_idx += 1
        state.at_landmark = True
        state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: Reached {nxt_landmark.name} ({int(nxt_landmark.distance_miles)} miles).")

        if nxt_landmark.landmark_type == LandmarkType.RIVER:
            state.pending_river = nxt_landmark
            return state
    else:
        state.at_landmark = False

    # 10. Random Weather and Travel Incidents
    if enable_incidents:
        _evaluate_weather(state, r)
        _evaluate_random_incidents(state, r)

    return state


def rest_cycle(
    state: TrailState,
    days: int = 3,
    rng: Optional[random.Random] = None,
) -> TrailState:
    """Halts wagon to rest, heal sick companions, and recover stamina."""
    if state.is_game_over:
        return state

    # Advance calendar
    state.current_date += datetime.timedelta(days=days)

    # Consume rations while resting
    living_count = len(state.living_members)
    food_needed = state.rations.daily_lbs * living_count * days
    if state.inventory.food >= food_needed:
        state.inventory.food -= food_needed
    else:
        state.inventory.food = 0.0

    # Healing bonus from rest
    heal_amount = 12.0 * (days / 3.0)
    for m in state.party:
        if m.is_alive:
            m.health = min(100.0, m.health + heal_amount)
            # Chance to recover from mild illness
            if m.diseases and (rng or random.Random()).random() < 0.40:
                cured = m.diseases.pop(0)
                state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: {m.name} recovered from {cured}.")

    state.active_event = TrailEvent(
        event_type="REST",
        title="RESTING ON THE TRAIL",
        description=f"Your party rested for {days} days. The oxen grazed and companions regained strength.",
        impact_summary=f"Party health restored (+{int(heal_amount)} HP).",
    )
    return state


def hunt_cycle(
    state: TrailState,
    rng: Optional[random.Random] = None,
) -> Tuple[TrailState, int, str]:
    """Spends ammunition to hunt game for fresh meat."""
    r = rng or random.Random()
    if state.inventory.ammunition < 10:
        return state, 0, "You need at least 10 bullets to organize a hunt."

    bullets_spent = min(state.inventory.ammunition, r.randint(10, 25))
    state.inventory.ammunition -= bullets_spent

    # Hunt yield table based on terrain and random luck
    roll = r.random()
    if roll < 0.15:
        # Skunked
        food_yield = 0
        msg = f"Hunt yielded no game after spending {bullets_spent} bullets."
    elif roll < 0.45:
        # Small game (rabbits, fowl)
        food_yield = r.randint(25, 60)
        msg = f"Shot wild rabbits and prairie grouse! Gained {food_yield} lbs of meat (-{bullets_spent} bullets)."
    elif roll < 0.80:
        # Medium game (deer, antelope)
        food_yield = r.randint(80, 160)
        msg = f"Downed a fine pronghorn antelope! Gained {food_yield} lbs of meat (-{bullets_spent} bullets)."
    else:
        # Large game (bison / bear)
        food_yield = r.randint(180, 250)
        msg = f"A great buffalo was brought down! Packed {food_yield} lbs of fresh meat into the wagon (-{bullets_spent} bullets)."

    state.inventory.food += food_yield
    state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: {msg}")
    return state, food_yield, msg


def cross_river(
    state: TrailState,
    choice: str = "FORD",
    rng: Optional[random.Random] = None,
) -> Tuple[TrailState, bool, str]:
    """Executes a river crossing with realistic risk assessment."""
    r = rng or random.Random()
    lm = state.pending_river or state.current_landmark
    depth = lm.river_depth_ft or 3.5
    ch = choice.upper()

    success = False
    details = ""

    if ch == "FERRY":
        ferry_cost = 5.0
        if state.inventory.cash >= ferry_cost:
            state.inventory.cash -= ferry_cost
            success = True
            details = f"Paid ${ferry_cost:.2f} for ferry transport. Crossed {lm.name} safely without incident."
        else:
            return state, False, "Not enough money to pay the ferryman ($5.00 required)!"
    elif ch == "FORD":
        # Safe if shallow (< 2.5 ft), risky if deeper
        if depth <= 2.8:
            success = True
            details = f"Fording the shallow waters was successful! Crossed {lm.name} cleanly."
        else:
            risk = min(0.85, (depth - 2.5) * 0.25)
            if r.random() > risk:
                success = True
                details = f"Wagon made it across the deep waters of {lm.name} with careful handling."
            else:
                success = False
                # Damage or food loss
                lost_food = min(state.inventory.food, round(r.uniform(40.0, 120.0), 1))
                state.inventory.food -= lost_food
                details = f"Disaster while fording! The wagon swamped in {depth:.1f} ft water. Lost {lost_food} lbs of food."
                if r.random() < 0.35 and state.inventory.clothing > 1:
                    state.inventory.clothing -= 1
                    details += " 1 set of clothing washed away."
    elif ch == "CAULK":
        # Float wagon across
        if r.random() < 0.85:
            success = True
            details = f"Wagon was successfully caulked and floated across {lm.name}!"
        else:
            success = False
            lost_ammo = min(state.inventory.ammunition, r.randint(20, 50))
            state.inventory.ammunition -= lost_ammo
            details = f"Wagon drifted into rocks while floating {lm.name}. Lost {lost_ammo} bullets and supplies soaked."

    # Clear pending river lock
    state.pending_river = None
    state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: {details}")
    return state, success, details


def buy_supplies(
    state: TrailState,
    item: str,
    quantity: int,
) -> Tuple[TrailState, bool, str]:
    """Purchases provisions at outpost general stores with distance inflation."""
    if quantity <= 0:
        return state, False, "Quantity must be positive."

    price_each = get_item_price(item, state.miles_traveled)
    total_cost = round(price_each * quantity, 2)

    if state.inventory.cash < total_cost:
        return state, False, f"Not enough cash! Need ${total_cost:.2f}, but only have ${state.inventory.cash:.2f}."

    state.inventory.cash = round(state.inventory.cash - total_cost, 2)

    if item == "oxen":
        state.inventory.oxen += quantity
    elif item == "food":
        state.inventory.food += quantity
    elif item == "clothing":
        state.inventory.clothing += quantity
    elif item == "ammunition":
        state.inventory.ammunition += quantity * 50  # bought in boxes of 50
    elif item == "wagon_wheel":
        state.inventory.wagon_wheels += quantity
    elif item == "wagon_axle":
        state.inventory.wagon_axles += quantity
    elif item == "wagon_tongue":
        state.inventory.wagon_tongues += quantity
    elif item == "medical_kit":
        state.inventory.medical_kits += quantity
    else:
        return state, False, f"Unknown item '{item}'."

    msg = f"Purchased {quantity} {item} for ${total_cost:.2f}."
    state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: {msg}")
    return state, True, msg


# ---------------------------------------------------------------------------
# Weather & Incident Generators
# ---------------------------------------------------------------------------

def _evaluate_weather(state: TrailState, r: random.Random) -> None:
    """Updates weather based on altitude, season, and geography."""
    miles = state.miles_traveled
    month = state.current_date.month

    if miles > 1750 or (miles > 800 and month in (10, 11, 12, 1, 2)):
        # Mountain snow & blizzard country
        weights = [0.10, 0.10, 0.05, 0.15, 0.15, 0.20, 0.15, 0.10]
    elif miles > 600:
        # High plains / Rocky foothills
        weights = [0.25, 0.25, 0.10, 0.15, 0.15, 0.05, 0.03, 0.02]
    else:
        # Missouri / Kansas prairies
        weights = [0.35, 0.30, 0.10, 0.10, 0.15, 0.00, 0.00, 0.00]

    weathers = [
        Weather.FAIR, Weather.WARM, Weather.HOT, Weather.COOL,
        Weather.RAINY, Weather.COLD, Weather.VERY_COLD, Weather.BLIZZARD,
    ]
    state.weather = r.choices(weathers, weights=weights, k=1)[0]


def _evaluate_random_incidents(state: TrailState, r: random.Random) -> None:
    """Generates authentic pioneer encounters and travel mishaps."""
    chance = r.random()

    # 1. Illness Incident (12% chance)
    if chance < 0.12:
        living = state.living_members
        if living:
            victim = r.choice(living)
            diseases = ["Cholera", "Dysentery", "Typhoid", "Measles", "Exhaustion", "Fever", "Snakebite"]
            disease = r.choice(diseases)
            if disease not in victim.diseases:
                victim.diseases.append(disease)
                victim.health = max(10.0, victim.health - 20.0)

                # Use medical kit if available
                med_used = False
                if state.inventory.medical_kits > 0:
                    state.inventory.medical_kits -= 1
                    victim.health = min(100.0, victim.health + 15.0)
                    med_used = True

                summary = f"{victim.name} contracted {disease}!"
                if med_used:
                    summary += " Medical kit administered to aid recovery."

                state.active_event = TrailEvent(
                    event_type="ILLNESS",
                    title="ILLNESS STRIKES THE PARTY",
                    description=f"{victim.name} has fallen severely ill with {disease}.",
                    impact_summary=summary,
                )
                state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: {summary}")
                return

    # 2. Broken Wagon Part (7% chance)
    elif chance < 0.19:
        part_name = r.choice(["wheel", "axle", "tongue"])
        repaired = False

        if part_name == "wheel" and state.inventory.wagon_wheels > 0:
            state.inventory.wagon_wheels -= 1
            repaired = True
        elif part_name == "axle" and state.inventory.wagon_axles > 0:
            state.inventory.wagon_axles -= 1
            repaired = True
        elif part_name == "tongue" and state.inventory.wagon_tongues > 0:
            state.inventory.wagon_tongues -= 1
            repaired = True
        elif state.profession == Profession.CARPENTER and r.random() < 0.75:
            repaired = True  # Carpenter repair perk!

        if repaired:
            summary = f"Broken wagon {part_name} replaced using spare part."
        else:
            summary = f"Broken wagon {part_name}! No spare part; delayed 3 days repairing it."
            state.current_date += datetime.timedelta(days=3)

        state.active_event = TrailEvent(
            event_type="BREAKDOWN",
            title=f"BROKEN WAGON {part_name.upper()}",
            description=f"A sudden jolt snapped a wagon {part_name}!",
            impact_summary=summary,
        )
        state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: {summary}")
        return

    # 3. Theft / Wild Animals (5% chance)
    elif chance < 0.24:
        lost_food = min(state.inventory.food, round(r.uniform(20.0, 60.0), 1))
        state.inventory.food -= lost_food
        summary = f"Night raiders prowled the camp! Lost {lost_food} lbs of food."
        state.active_event = TrailEvent(
            event_type="THEFT",
            title="CAMP RAIDED IN THE NIGHT",
            description="Wild prairie predators and scavengers raided your food crates while the sentry was asleep.",
            impact_summary=summary,
        )
        state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: {summary}")
        return

    # 4. Beneficial Encounter: Abandoned Wagon or Helpful Emigrants (6% chance)
    elif chance < 0.30:
        found_food = r.randint(30, 80)
        found_ammo = r.randint(20, 50)
        state.inventory.food += found_food
        state.inventory.ammunition += found_ammo
        summary = f"Discovered an abandoned wagon! Salvaged {found_food} lbs food and {found_ammo} bullets."
        state.active_event = TrailEvent(
            event_type="SALVAGE",
            title="ABANDONED WAGON FOUND",
            description="You came across a supply cache abandoned by earlier travelers.",
            impact_summary=summary,
        )
        state.history_log.append(f"{state.current_date.strftime('%B %d, %Y')}: {summary}")
        return


# ---------------------------------------------------------------------------
# Scoring System
# ---------------------------------------------------------------------------

def calculate_final_score(state: TrailState) -> int:
    """Calculates final pioneer expedition score matching historical conventions."""
    if not state.victory:
        # Partial score for distance reached
        return int(state.miles_traveled * 0.5)

    base = 0
    # Surviving party members
    for m in state.living_members:
        base += 500
        if m.health >= 80.0:
            base += 300  # Bonus for excellent health

    # Remaining assets
    base += int(state.inventory.food * 0.5)
    base += state.inventory.oxen * 50
    base += state.inventory.clothing * 25
    base += int(state.inventory.ammunition * 0.1)
    base += (state.inventory.wagon_wheels + state.inventory.wagon_axles + state.inventory.wagon_tongues) * 40
    base += int(state.inventory.cash * 1.0)

    # Multiplier by occupation difficulty
    mult = state.profession.score_multiplier
    return int(base * mult)


calculate_score = calculate_final_score


# ---------------------------------------------------------------------------
# Terminal CLI Runner (Zero external dependencies)
# ---------------------------------------------------------------------------

def play_cli(seed: Optional[int] = None) -> int:
    """Runs an interactive text-mode Oregon Trail session."""
    print("=" * 64)
    print("               THE OREGON TRAIL (1848)")
    print("    Creative Computing / MECC Historical Pioneer Simulation")
    print("=" * 64)

    state = init_game(seed=seed)
    print(f"\nWelcome, {state.party[0].name}! You are journeying to Oregon's Willamette Valley.")
    print("Your wagon is loaded with 4 oxen, 400 lbs of food, and provisions.\n")

    while not state.is_game_over:
        print("-" * 64)
        print(f"Date: {state.current_date.strftime('%B %d, %Y')}  |  Miles Traveled: {int(state.miles_traveled)} / 2040")
        print(f"Weather: {state.weather.value}  |  Health: {state.overall_health_status}  |  Pace: {state.pace.value}")
        print(f"Food: {int(state.inventory.food)} lbs  |  Oxen: {state.inventory.oxen}  |  Cash: ${state.inventory.cash:.2f}")

        nxt = state.next_landmark
        if nxt:
            print(f"Next Landmark: {nxt.name} ({int(state.distance_to_next_landmark)} miles away)")

        if state.pending_river:
            print(f"\n>>> YOU HAVE ARRIVED AT {state.pending_river.name.upper()}! <<<")
            print("1. Ford river  2. Caulk wagon and float  3. Take ferry ($5)")
            choice = input("Your choice (1-3): ").strip()
            if choice == "3":
                _, ok, msg = cross_river(state, "FERRY")
            elif choice == "2":
                _, ok, msg = cross_river(state, "CAULK")
            else:
                _, ok, msg = cross_river(state, "FORD")
            print(f">> {msg}\n")
            continue

        print("\nChoose Action:")
        print("1. Continue Trail (Travel 4 days)")
        print("2. Rest (3 days)")
        print("3. Hunt for Food")
        print("4. Change Pace (Steady / Strenuous / Grueling)")
        print("5. Change Rations (Filling / Meager / Bare Bones)")
        print("6. Quit to Library")

        cmd = input("Command (1-6): ").strip()
        if cmd == "1":
            state = step_turn(state, "TRAVEL", days=4)
        elif cmd == "2":
            state = step_turn(state, "REST", days=3)
        elif cmd == "3":
            _, yield_amt, msg = hunt_cycle(state)
            print(f">> {msg}")
        elif cmd == "4":
            paces = [Pace.STEADY, Pace.STRENUOUS, Pace.GRUELING]
            curr_idx = paces.index(state.pace)
            state.pace = paces[(curr_idx + 1) % len(paces)]
            print(f">> Pace changed to {state.pace.value}")
        elif cmd == "5":
            rats = [Rations.FILLING, Rations.MEAGER, Rations.BARE_BONES]
            curr_idx = rats.index(state.rations)
            state.rations = rats[(curr_idx + 1) % len(rats)]
            print(f">> Rations changed to {state.rations.value}")
        elif cmd in ("6", "q", "quit"):
            print("Quitting journey. So long for now!")
            return 0

        if state.active_event:
            print(f"\n[! EVENT !] {state.active_event.title}")
            print(f">> {state.active_event.impact_summary}\n")

    print("\n" + "=" * 64)
    if state.victory:
        print("                     VICTORY!")
        print(f"You made it to the Willamette Valley on {state.current_date.strftime('%B %d, %Y')}!")
        print(f"Final Expedition Score: {calculate_final_score(state)} points.")
    else:
        print("                   JOURNEY FAILED")
        print(f"Reason: {state.game_over_reason}")
    print("=" * 64 + "\n")
    return 0
