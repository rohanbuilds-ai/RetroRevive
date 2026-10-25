"""
game_registry.py - Central Game Registry for RetroRevive.

Provides a unified catalog of retro computer games supported by the platform,
including metadata, category filtering, search capabilities, and launcher entry points.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class GameStatus(str, Enum):
    PLAYABLE = "PLAYABLE"
    COMING_SOON = "COMING_SOON"


class GameCategory(str, Enum):
    ALL = "ALL"
    STRATEGY_SIMULATION = "STRATEGY_SIMULATION"
    PUZZLE_LOGIC = "PUZZLE_LOGIC"
    ADVENTURE_SPACE = "ADVENTURE_SPACE"


@dataclass
class GameMetadata:
    """Stores metadata and launch configuration for a retro game."""
    game_id: str
    title: str
    subtitle: str
    year: int
    author: str
    original_publisher: str
    category: GameCategory
    category_display: str
    status: GameStatus
    modes: List[str]
    description: str
    rules_summary: str
    historical_provenance: str
    book_source: str
    tags: List[str] = field(default_factory=list)
    launch_callable: Optional[Callable[..., Any]] = None

    @property
    def is_playable(self) -> bool:
        return self.status == GameStatus.PLAYABLE


# Master game definitions
CATALOG: Dict[str, GameMetadata] = {
    "hammurabi": GameMetadata(
        game_id="hammurabi",
        title="HAMMURABI",
        subtitle="The Ancient Sumerian Kingdom Simulation",
        year=1978,
        author="Doug Dyment (1968), David H. Ahl (1973/1978)",
        original_publisher="Creative Computing (Morristown, NJ)",
        category=GameCategory.STRATEGY_SIMULATION,
        category_display="Strategy & Simulation",
        status=GameStatus.PLAYABLE,
        modes=["Classic 1978 Mode", "Enhanced Mode (Advisors & Scenarios)"],
        description=(
            "Rule ancient Sumeria for a 10-year term of office. Allocate grain between "
            "feeding your citizens, planting seed for the next harvest, and trading land "
            "while managing rat plagues, droughts, and population growth."
        ),
        rules_summary=(
            "Each citizen needs 20 bushels to survive. 1 acre requires 1 bushel of seed "
            "and 1 citizen can tend up to 10 acres. Land trades between 17 and 26 bushels/acre. "
            "Starving over 45% in any year triggers immediate impeachment."
        ),
        historical_provenance=(
            "Derived from Doug Dyment's The Sumer Game (FOCAL, 1968). Ported to DEC BASIC "
            "by David H. Ahl in 101 BASIC Computer Games (1973) and published in BASIC Computer "
            "Games (1978). RetroRevive preserves the exact 1978 Microsoft BASIC mechanics."
        ),
        book_source="BASIC Computer Games: Microcomputer Edition (1978), pp. 78-79.",
        tags=["Simulation", "Resource Management", "Classic 1978", "Historical"],
    ),
    "23_matches": GameMetadata(
        game_id="23_matches",
        title="23 MATCHES",
        subtitle="The Classic Mathematical Nim Subtraction Game",
        year=1978,
        author="Bob Albrecht (1973), David H. Ahl (1978)",
        original_publisher="People's Computer Company / Creative Computing",
        category=GameCategory.PUZZLE_LOGIC,
        category_display="Puzzle & Logic",
        status=GameStatus.PLAYABLE,
        modes=["Classic 1978 Mode (Albrecht AI)", "Master Mode (Optimal Modular AI)"],
        description=(
            "The timeless strategy game of 23 matchsticks. You and the computer take turns "
            "removing 1, 2, or 3 matches from the table. The player forced to take the "
            "very last match loses! Can you discover the mathematical winning strategy?"
        ),
        rules_summary=(
            "23 matches start on the table. Each turn, take 1, 2, or 3 matches. "
            "You cannot take more matches than remain on the table. The player who takes "
            "the last match loses the game (Misère Nim rules)."
        ),
        historical_provenance=(
            "Authored by Bob Albrecht at the People's Computer Company to teach modular "
            "arithmetic and strategic thinking. Published in 101 BASIC Computer Games (1973) "
            "and republished in BASIC Computer Games (1978) as game #93."
        ),
        book_source="BASIC Computer Games: Microcomputer Edition (1978), pp. 177-178.",
        tags=["Puzzle", "Nim", "Mathematical", "Turn-Based", "Misère"],
    ),
    "lunar_lander": GameMetadata(
        game_id="lunar_lander",
        title="LUNAR LANDER",
        subtitle="Apollo 11 Lunar Module Descent Simulator",
        year=1978,
        author="Jim Storer (1969), David H. Ahl (1973/1978)",
        original_publisher="DEC / Creative Computing",
        category=GameCategory.ADVENTURE_SPACE,
        category_display="Adventure & Space",
        status=GameStatus.PLAYABLE,
        modes=["Classic 1978 Mode (Jim Storer Model)", "Enhanced Flight Telemetry HUD"],
        description=(
            "Pilot the Apollo lunar excursion module (LEM) safely down to the moon's surface. "
            "Manage your retro-rocket fuel burn rate (0-200 lbs/sec) against lunar gravity "
            "over 10-second cycles to touch down smoothly on Tranquility Base."
        ),
        rules_summary=(
            "Starts at 120 miles altitude falling at 3,600 MPH (1.0 mi/s) with 16,500 lbs of fuel. "
            "Set burn rate K (0-200 lbs/sec) every 10 seconds. Lunar gravity accelerates at 0.001 mi/s². "
            "Touchdown velocity <= 1.2 MPH: Perfect Landing. <= 10 MPH: Good Landing. 10-60 MPH: Craft Damaged. "
            "> 60 MPH: Fatal Crash, creates a crater."
        ),
        historical_provenance=(
            "Created in autumn 1969 by 17-year-old Lexington High School student Jim Storer in FOCAL. "
            "Ported to DEC BASIC by David H. Ahl and published in 101 BASIC Computer Games (1973) "
            "and BASIC Computer Games: Microcomputer Edition (1978, pp. 106-108). Features exact Taylor series "
            "numerical integration of Tsiolkovsky's rocket equation."
        ),
        book_source="BASIC Computer Games: Microcomputer Edition (1978), pp. 106-108.",
        tags=["Space", "Physics", "Apollo", "Simulation", "NASA", "Retro-Rocket"],
    ),
    "super_star_trek": GameMetadata(
        game_id="super_star_trek",
        title="SUPER STAR TREK",
        subtitle="Tactical Deep Space Command Simulation",
        year=1974,
        author="Mike Mayfield (1971), David H. Ahl & Bob Leedom (1974)",
        original_publisher="Creative Computing",
        category=GameCategory.ADVENTURE_SPACE,
        category_display="Adventure & Space",
        status=GameStatus.PLAYABLE,
        modes=["1978 Strategic Space Combat", "Tactical Sensor Array & Starbase Operations"],
        description=(
            "Command the USS Enterprise across an 8x8 quadrant galaxy. Hunt down Klingon battlecruisers, "
            "fire directional photon torpedoes and energy phasers, manage deflector shields, and dock "
            "at Federation Starbases before your mission stardates expire."
        ),
        rules_summary=(
            "Navigate through 64 quadrants (8x8 grid) and 64 sectors per quadrant. Balance energy between "
            "warp engines, phasers, and protective shields. Fire photon torpedoes along straight-line courses. "
            "Dock adjacent to Starbases to repair damaged subsystems and replenish energy and torpedoes."
        ),
        historical_provenance=(
            "Created on an SDS Sigma 7 by Mike Mayfield in 1971 in BASIC. David H. Ahl and Bob Leedom "
            "expanded it into Super Star Trek in 1974. Published in Creative Computing and BASIC Computer Games "
            "(1978, pp. 157-163). Preserves authentic quadrant/sector coordinates and device damage rules."
        ),
        book_source="BASIC Computer Games: Microcomputer Edition (1978), pp. 157-163.",
        tags=["Sci-Fi", "Tactical", "Grid Command", "Playable", "Classic 1978"],
    ),
    "oregon_trail": GameMetadata(
        game_id="oregon_trail",
        title="THE OREGON TRAIL",
        subtitle="The Great 1848 Pioneer Frontier Journey",
        year=1971,
        author="Don Rawitsch, Bill Heinemann, Paul Dillenberger (1971)",
        original_publisher="MECC (Minnesota Educational Computing Consortium)",
        category=GameCategory.STRATEGY_SIMULATION,
        category_display="Strategy & Simulation",
        status=GameStatus.PLAYABLE,
        modes=["1848 Pioneer Journey", "Survival Simulation & Trail Guide"],
        description=(
            "Lead a covered wagon party of pioneers from Independence, Missouri to Oregon's "
            "Willamette Valley across 2,040 miles of wilderness. Manage rations, oxen, and pace, "
            "ford dangerous rivers, hunt wild game, endure illnesses, and reach the fertile valley."
        ),
        rules_summary=(
            "Manage 5 pioneers across 17 historic trail landmarks. Balance daily pace and food rations "
            "to maintain party health. Hunt for game when ammo permits. Negotiate rivers with fords, "
            "caulk & float, or ferries. Score points based on surviving members, supplies, and profession multiplier."
        ),
        historical_provenance=(
            "Created in autumn 1971 by Carleton College student teachers Don Rawitsch, Bill Heinemann, "
            "and Paul Dillenberger for an 8th-grade history class in Minneapolis, running on a CDC Cyber "
            "timeshare mainframe via teletype. Rewritten and published in Creative Computing (May/June 1978, "
            "pp. 132-139). Preserved in authentic 1848 historical simulation rules."
        ),
        book_source="Creative Computing Magazine (May/June 1978), pp. 132-139.",
        tags=["History", "Survival", "Pioneers", "Simulation", "Classic 1978", "Playable"],
    ),
    "hunt_the_wumpus": GameMetadata(
        game_id="hunt_the_wumpus",
        title="HUNT THE WUMPUS",
        subtitle="The Cave of the Dodecahedron Strategy Adventure",
        year=1973,
        author="Gregory Yob (1973), David H. Ahl (1978)",
        original_publisher="People's Computer Company / Creative Computing",
        category=GameCategory.ADVENTURE_SPACE,
        category_display="Adventure & Space",
        status=GameStatus.PLAYABLE,
        modes=["Classic 1978 Dodecahedron Cavern", "Sensory Warnings & Crooked Arrow Planner"],
        description=(
            "Navigate 20 subterranean caverns connected as a regular dodecahedron. Heed sensory "
            "warnings ('I smell a Wumpus!', 'I feel a draft.', 'Bats nearby!'), avoid bottomless "
            "pits and giant snatch-bats, and loose crooked arrows to slay the fearsome Wumpus "
            "before your arrows or lives run out!"
        ),
        rules_summary=(
            "20 rooms with 3 tunnels each. Hazards: 1 Wumpus, 2 Bottomless Pits, 2 Super Bats. "
            "Smell Wumpus/feel draft/hear bats when 1 room away. Shoot crooked arrows through "
            "1-5 connected rooms. Ricochets occur on non-connected paths. 5 arrows total."
        ),
        historical_provenance=(
            "Authored by Gregory Yob in 1973 at Dartmouth College / People's Computer Company in BASIC. "
            "Yob designed it specifically to break away from traditional Euclidean grid coordinates by "
            "using a dodecahedral graph. Published in Creative Computing (1975) and BASIC Computer Games "
            "(1978, pp. 178-181)."
        ),
        book_source="BASIC Computer Games: Microcomputer Edition (1978), pp. 178-181.",
        tags=["Adventure", "Dodecahedron", "Wumpus", "Crooked Arrow", "Classic 1978", "Playable"],
    ),
}


class GameRegistry:
    """Manages the catalog of retro games and provides filtering and lookup methods."""

    def __init__(self, catalog: Optional[Dict[str, GameMetadata]] = None) -> None:
        self._catalog: Dict[str, GameMetadata] = dict(catalog if catalog is not None else CATALOG)

    def register(self, metadata: GameMetadata) -> None:
        """Registers or replaces a game in the catalog."""
        self._catalog[metadata.game_id] = metadata

    def get(self, game_id: str) -> Optional[GameMetadata]:
        """Returns game metadata for a given game ID, or None if not found."""
        return self._catalog.get(game_id)

    def list_all(self) -> List[GameMetadata]:
        """Returns all registered games in catalog order."""
        return list(self._catalog.values())

    def list_playable(self) -> List[GameMetadata]:
        """Returns only currently playable games."""
        return [g for g in self._catalog.values() if g.is_playable]

    def filter_by_category(self, category: GameCategory) -> List[GameMetadata]:
        """Filters games by category enum. Returns all if category is ALL."""
        if category == GameCategory.ALL:
            return self.list_all()
        return [g for g in self._catalog.values() if g.category == category]

    def search(self, query: str) -> List[GameMetadata]:
        """
        Searches game titles, subtitles, tags, and authors by substring (case-insensitive).
        Empty query returns all games.
        """
        q = query.strip().lower()
        if not q:
            return self.list_all()
        results: List[GameMetadata] = []
        for g in self._catalog.values():
            if (
                q in g.title.lower()
                or q in g.subtitle.lower()
                or q in g.author.lower()
                or q in g.category_display.lower()
                or any(q in tag.lower() for tag in g.tags)
            ):
                results.append(g)
        return results


# Global singleton instance for convenient import
REGISTRY = GameRegistry()
