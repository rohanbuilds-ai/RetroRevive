"""
games/hunt_the_wumpus/engine.py - Pure Python simulation engine for Hunt the Wumpus (1973/1978).

Historical Provenance:
- Original Game: Gregory Yob (1973, Dartmouth College / People's Computer Company)
- Published in: Creative Computing (1975) & BASIC Computer Games (1978, Ahl, pp. 178-181)

Mechanics:
- 20 rooms arranged on the vertices of a regular dodecahedron (each room connects to 3 others)
- 1 Hunter with 5 crooked arrows
- 1 Wumpus (lethal, stirs on arrow fire)
- 2 Bottomless Pits (instant fatal fall)
- 2 Super Bats (transport hunter to random room)
- Sensory warnings: "I smell a Wumpus!", "I feel a draft.", "Bats nearby!"
- Crooked arrows: paths of 1-5 rooms with ricochet on non-connected paths
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


# Standard 1978 Gregory Yob regular dodecahedron adjacency table
DODECAHEDRON_ROOMS: Dict[int, Tuple[int, int, int]] = {
    1: (2, 5, 8),
    2: (1, 3, 10),
    3: (2, 4, 12),
    4: (3, 5, 14),
    5: (1, 4, 6),
    6: (5, 7, 15),
    7: (6, 8, 17),
    8: (1, 7, 9),
    9: (8, 10, 18),
    10: (2, 9, 11),
    11: (10, 12, 19),
    12: (3, 11, 13),
    13: (12, 14, 20),
    14: (4, 13, 15),
    15: (6, 14, 16),
    16: (15, 17, 20),
    17: (7, 16, 18),
    18: (9, 17, 19),
    19: (11, 18, 20),
    20: (13, 16, 19),
}

# 2D Planar Schlegel Projection layout normalized to (0.0 .. 1.0) for map rendering
DODECAHEDRON_COORDS: Dict[int, Tuple[float, float]] = {
    # Outer circle (radius 0.44)
    1: (0.50, 0.06),
    2: (0.92, 0.36),
    3: (0.76, 0.88),
    4: (0.24, 0.88),
    5: (0.08, 0.36),
    # Intermediate outer ring
    6: (0.20, 0.42),
    7: (0.32, 0.22),
    8: (0.50, 0.22),
    9: (0.68, 0.22),
    10: (0.80, 0.42),
    # Intermediate inner ring
    11: (0.74, 0.62),
    12: (0.66, 0.76),
    13: (0.50, 0.82),
    14: (0.34, 0.76),
    15: (0.26, 0.62),
    # Innermost pentagon (radius 0.14)
    16: (0.38, 0.58),
    17: (0.42, 0.42),
    18: (0.58, 0.42),
    19: (0.62, 0.58),
    20: (0.50, 0.68),
}


class HazardType(Enum):
    WUMPUS = "WUMPUS"
    PIT = "PIT"
    BATS = "BATS"


@dataclass
class SensoryWarnings:
    smell_wumpus: bool = False
    feel_draft: bool = False
    hear_bats: bool = False


@dataclass
class WumpusState:
    hunter_room: int
    wumpus_room: int
    pit_rooms: Set[int]
    bat_rooms: Set[int]
    arrows: int = 5
    is_game_over: bool = False
    victory: bool = False
    game_over_reason: Optional[str] = None
    visited_rooms: Set[int] = field(default_factory=set)
    history_log: List[str] = field(default_factory=list)
    rng_seed: Optional[int] = None


@dataclass
class TurnResult:
    success: bool
    message: str
    warnings: SensoryWarnings
    bat_transported: bool = False
    arrow_path_taken: Optional[List[int]] = None


def init_game(seed: Optional[int] = None) -> WumpusState:
    """Initialize a brand-new authentic Hunt the Wumpus game state."""
    rng = random.Random(seed)
    # Pick 6 distinct rooms: 1 hunter, 1 wumpus, 2 pits, 2 bats
    all_rooms = list(range(1, 21))
    rng.shuffle(all_rooms)

    hunter_room = all_rooms[0]
    wumpus_room = all_rooms[1]
    pit_rooms = {all_rooms[2], all_rooms[3]}
    bat_rooms = {all_rooms[4], all_rooms[5]}

    state = WumpusState(
        hunter_room=hunter_room,
        wumpus_room=wumpus_room,
        pit_rooms=pit_rooms,
        bat_rooms=bat_rooms,
        arrows=5,
        is_game_over=False,
        victory=False,
        game_over_reason=None,
        visited_rooms={hunter_room},
        history_log=[f"Entered the caverns of the Wumpus at Room {hunter_room}. Equipped with 5 crooked arrows."],
        rng_seed=seed,
    )
    return state


def get_sensory_warnings(state: WumpusState) -> SensoryWarnings:
    """Return sensations detected from adjacent rooms."""
    adjacent = DODECAHEDRON_ROOMS[state.hunter_room]
    smell = state.wumpus_room in adjacent
    draft = any(p in adjacent for p in state.pit_rooms)
    bats = any(b in adjacent for b in state.bat_rooms)
    return SensoryWarnings(smell_wumpus=smell, feel_draft=draft, hear_bats=bats)


def move_hunter(state: WumpusState, target_room: int, rng: Optional[random.Random] = None) -> TurnResult:
    """
    Move the hunter to an adjacent room. Resolves hazards (Wumpus, Pit, Super Bats).
    """
    if state.is_game_over:
        return TurnResult(
            success=False,
            message="Game is already over.",
            warnings=get_sensory_warnings(state),
        )

    adjacent = DODECAHEDRON_ROOMS[state.hunter_room]
    if target_room not in adjacent:
        return TurnResult(
            success=False,
            message=f"Room {target_room} is not connected to Room {state.hunter_room}! Tunnels lead to: {adjacent}",
            warnings=get_sensory_warnings(state),
        )

    if rng is None:
        rng = random.Random()

    state.hunter_room = target_room
    state.visited_rooms.add(target_room)
    bat_transported = False

    # Check Super Bats first (bats pick you up and fly to random room)
    if state.hunter_room in state.bat_rooms:
        bat_transported = True
        # Super bat drops you into an arbitrary room
        new_room = rng.randint(1, 20)
        state.hunter_room = new_room
        state.visited_rooms.add(new_room)
        state.history_log.append(f"ZAP--SUPER BAT SNATCH! Carried away and dropped in Room {new_room}!")

    # Check lethal hazards in arrival room
    if state.hunter_room == state.wumpus_room:
        state.is_game_over = True
        state.victory = False
        state.game_over_reason = "TSK TSK TSK - WUMPUS GOT YOU!"
        state.history_log.append(f"Room {state.hunter_room}: Stumbled directly upon the sleeping beast! WUMPUS GOT YOU!")
        return TurnResult(
            success=True,
            message="TSK TSK TSK - WUMPUS GOT YOU!",
            warnings=get_sensory_warnings(state),
            bat_transported=bat_transported,
        )

    if state.hunter_room in state.pit_rooms:
        state.is_game_over = True
        state.victory = False
        state.game_over_reason = "YYYIIIIEEEE . . . FELL IN PIT"
        state.history_log.append(f"Room {state.hunter_room}: Stepped into the bottomless abyss! YYYIIIIEEEE . . . FELL IN PIT")
        return TurnResult(
            success=True,
            message="YYYIIIIEEEE . . . FELL IN PIT",
            warnings=get_sensory_warnings(state),
            bat_transported=bat_transported,
        )

    # Safe room reached
    warnings = get_sensory_warnings(state)
    msg = f"Entered Room {state.hunter_room}."
    if bat_transported:
        msg = f"Super Bat snatched you and deposited you in Room {state.hunter_room}."
    state.history_log.append(f"Moved to Room {state.hunter_room}.")
    return TurnResult(success=True, message=msg, warnings=warnings, bat_transported=bat_transported)


def shoot_arrow(state: WumpusState, path: List[int], rng: Optional[random.Random] = None) -> TurnResult:
    """
    Shoot a crooked arrow along a proposed room path (1 to 5 rooms).
    If a room is not adjacent to the prior room, the arrow ricochets into a random connected room.
    """
    if state.is_game_over:
        return TurnResult(
            success=False,
            message="Game is already over.",
            warnings=get_sensory_warnings(state),
        )

    if state.arrows <= 0:
        state.is_game_over = True
        state.victory = False
        state.game_over_reason = "YOU ARE OUT OF CROOKED ARROWS!"
        return TurnResult(
            success=False,
            message="YOU ARE OUT OF CROOKED ARROWS!",
            warnings=get_sensory_warnings(state),
        )

    if not path or len(path) > 5:
        return TurnResult(
            success=False,
            message="Arrow path must contain between 1 and 5 rooms.",
            warnings=get_sensory_warnings(state),
        )

    if rng is None:
        rng = random.Random()

    state.arrows -= 1
    arrow_pos = state.hunter_room
    actual_path_taken: List[int] = []

    for target in path:
        adjacent = DODECAHEDRON_ROOMS[arrow_pos]
        if target in adjacent:
            arrow_pos = target
        else:
            # Ricochet into random adjacent room
            arrow_pos = rng.choice(adjacent)
        actual_path_taken.append(arrow_pos)

        # Check arrow strikes Wumpus
        if arrow_pos == state.wumpus_room:
            state.is_game_over = True
            state.victory = True
            state.game_over_reason = "AHA! YOU GOT THE WUMPUS!"
            state.history_log.append(
                f"Shot arrow through path {actual_path_taken}. DIRECT HIT on the Wumpus in Room {arrow_pos}! VICTORY!"
            )
            return TurnResult(
                success=True,
                message="AHA! YOU GOT THE WUMPUS!",
                warnings=get_sensory_warnings(state),
                arrow_path_taken=actual_path_taken,
            )

        # Check arrow strikes Hunter
        if arrow_pos == state.hunter_room:
            state.is_game_over = True
            state.victory = False
            state.game_over_reason = "OUCH! ARROW STRUCK YOU!"
            state.history_log.append(
                f"Shot arrow through path {actual_path_taken}. The arrow ricocheted back into Room {arrow_pos} and struck you!"
            )
            return TurnResult(
                success=True,
                message="OUCH! ARROW STRUCK YOU!",
                warnings=get_sensory_warnings(state),
                arrow_path_taken=actual_path_taken,
            )

    # Arrow missed! The noise may wake the Wumpus.
    # Authentic 1978 rule: 75% chance Wumpus moves to an adjacent room
    wumpus_stirred = rng.random() < 0.75
    if wumpus_stirred:
        wumpus_adjacent = DODECAHEDRON_ROOMS[state.wumpus_room]
        new_wumpus_room = rng.choice(wumpus_adjacent)
        state.wumpus_room = new_wumpus_room
        state.history_log.append(f"The arrow whizzed harmlessly into the dark. The Wumpus awoke and crept into Room {new_wumpus_room}!")

        # If Wumpus moves into Hunter's room, it devours the hunter
        if state.wumpus_room == state.hunter_room:
            state.is_game_over = True
            state.victory = False
            state.game_over_reason = "TSK TSK TSK - WUMPUS GOT YOU!"
            state.history_log.append(f"The awakened Wumpus lumbered into Room {state.hunter_room} and ate you!")
            return TurnResult(
                success=True,
                message="TSK TSK TSK - WUMPUS GOT YOU!",
                warnings=get_sensory_warnings(state),
                arrow_path_taken=actual_path_taken,
            )
    else:
        state.history_log.append("The arrow clattered against stone. The Wumpus remains asleep.")

    # Check arrows exhausted
    if state.arrows <= 0 and not state.is_game_over:
        state.is_game_over = True
        state.victory = False
        state.game_over_reason = "YOU RAN OUT OF ARROWS!"
        state.history_log.append("You have exhausted all 5 crooked arrows without slaying the beast. DEFEAT.")
        return TurnResult(
            success=True,
            message="YOU RAN OUT OF ARROWS!",
            warnings=get_sensory_warnings(state),
            arrow_path_taken=actual_path_taken,
        )

    return TurnResult(
        success=True,
        message=f"Arrow missed. Remaining arrows: {state.arrows}.",
        warnings=get_sensory_warnings(state),
        arrow_path_taken=actual_path_taken,
    )


def play_cli() -> None:
    """Terminal CLI runner for Hunt the Wumpus (zero dependencies)."""
    print("=" * 60)
    print("           HUNT THE WUMPUS (1973/1978)")
    print("       Original Author: Gregory Yob")
    print("=" * 60)
    print("INSTRUCTIONS:")
    print("- You are in a cave of 20 rooms connected by tunnels.")
    print("- Each room connects to exactly 3 other rooms (dodecahedron).")
    print("- Hazards: Bottomless Pits, Super Bats, and the dreaded WUMPUS.")
    print("- Sensations: Smell Wumpus (1 room away), Draft (pit nearby), Bats.")
    print("- Commands: 'M <room>' to move, 'S <r1> <r2>...' to shoot crooked arrow.")
    print("=" * 60)

    state = init_game()

    while not state.is_game_over:
        warnings = get_sensory_warnings(state)
        print(f"\nYou are in Room {state.hunter_room}.")
        tunnels = DODECAHEDRON_ROOMS[state.hunter_room]
        print(f"Tunnels lead to: {tunnels[0]}, {tunnels[1]}, {tunnels[2]}")
        print(f"Crooked arrows remaining: {state.arrows}")

        if warnings.smell_wumpus:
            print(">> I smell a Wumpus!")
        if warnings.feel_draft:
            print(">> I feel a draft.")
        if warnings.hear_bats:
            print(">> Bats nearby!")

        try:
            line = input("\nAction (M <room> / S <r1> <r2>... / Q to quit): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting cavern.")
            break

        if not line:
            continue
        parts = line.split()
        cmd = parts[0].upper()

        if cmd == "Q":
            print("Leaving the caverns.")
            break
        elif cmd == "M":
            if len(parts) < 2:
                print("Specify which room to enter.")
                continue
            try:
                target = int(parts[1])
            except ValueError:
                print("Enter a numeric room number.")
                continue
            res = move_hunter(state, target)
            print(res.message)
        elif cmd == "S":
            if len(parts) < 2:
                print("Specify 1 to 5 rooms along the arrow path.")
                continue
            try:
                path = [int(p) for p in parts[1:]]
            except ValueError:
                print("Enter numeric room numbers.")
                continue
            res = shoot_arrow(state, path)
            print(res.message)
        else:
            print("Unknown command. Use 'M <room>' to move or 'S <r1> <r2>...' to shoot.")

    print("\n" + "=" * 60)
    if state.victory:
        print("CONGRATULATIONS! YOU HAVE SLAIN THE WUMPUS!")
    else:
        print(f"GAME OVER: {state.game_over_reason or 'Defeat'}")
    print("=" * 60)
