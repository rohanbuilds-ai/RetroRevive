"""
games/super_star_trek/test_engine.py - Automated tests for Super Star Trek (1974/1978 Edition) Engine.
"""

import math
import random
import unittest

from games.super_star_trek.engine import (
    GALAXY_HEIGHT,
    GALAXY_WIDTH,
    INITIAL_ENERGY,
    INITIAL_SHIELDS,
    INITIAL_TORPEDOES,
    MAX_SHIELDS,
    SECTOR_HEIGHT,
    SECTOR_WIDTH,
    Device,
    KlingonShip,
    QuadrantRecord,
    SectorEntity,
    ShipCondition,
    TrekState,
    calculate_score,
    dock_at_starbase,
    fire_phasers,
    fire_torpedo,
    init_game,
    long_range_scan,
    navigate,
    transfer_shields,
)


class TestStarTrekInitialState(unittest.TestCase):
    """Verifies starting conditions, galaxy generation, and resource baselines."""

    def test_default_initial_state(self) -> None:
        state = init_game(seed=42)

        self.assertEqual(state.energy, INITIAL_ENERGY)
        self.assertEqual(state.shields, INITIAL_SHIELDS)
        self.assertEqual(state.torpedoes, INITIAL_TORPEDOES)
        self.assertEqual(state.stardate, 3000.0)
        self.assertEqual(state.days_remaining, 30.0)
        self.assertFalse(state.is_game_over)
        self.assertFalse(state.victory)

        # 8x8 Galaxy
        self.assertEqual(len(state.galaxy), GALAXY_HEIGHT)
        self.assertEqual(len(state.galaxy[0]), GALAXY_WIDTH)

        # Enterprise placed inside valid coordinates
        self.assertTrue(0 <= state.quadrant_x < GALAXY_WIDTH)
        self.assertTrue(0 <= state.quadrant_y < GALAXY_HEIGHT)
        self.assertTrue(0 <= state.sector_x < SECTOR_WIDTH)
        self.assertTrue(0 <= state.sector_y < SECTOR_HEIGHT)

        # Minimum required Klingons and Starbases across galaxy
        self.assertGreaterEqual(state.total_klingons_remaining, 15)
        self.assertGreaterEqual(state.total_starbases_remaining, 2)

        # Subsystems all operational
        for dev in Device:
            self.assertTrue(state.is_device_operational(dev))

    def test_quadrant_name_formatting(self) -> None:
        state = init_game(seed=1)
        name = state.quadrant_name
        self.assertTrue(any(roman in name for roman in ["I", "II", "III", "IV"]))


class TestNavigation(unittest.TestCase):
    """Verifies impulse navigation, warp travel, and collision prevention."""

    def test_impulse_navigation_within_quadrant(self) -> None:
        state = init_game(seed=42)
        state.quadrant_x = 3
        state.quadrant_y = 3
        state.sector_x = 2
        state.sector_y = 2
        # Clear obstacles in path
        state.stars_in_quadrant = []
        state.klingons_in_quadrant = []
        state.starbase_in_quadrant = None

        initial_energy = state.energy
        initial_stardate = state.stardate

        # Course 1 (East, dx=+1, dy=0) at warp 0.2 (impulse = ~2 sectors)
        state, ok, msg = navigate(state, course=1.0, warp=0.2)
        self.assertTrue(ok)
        self.assertGreater(state.sector_x, 2)
        self.assertEqual(state.sector_y, 2)
        self.assertEqual(state.quadrant_x, 3)
        self.assertEqual(state.quadrant_y, 3)
        self.assertLess(state.energy, initial_energy)
        self.assertGreater(state.stardate, initial_stardate)

    def test_warp_navigation_across_quadrants(self) -> None:
        state = init_game(seed=42)
        state.quadrant_x = 2
        state.quadrant_y = 2
        state.sector_x = 2
        state.sector_y = 2

        # Course 1 (East) at Warp 2.0 (traverses across into neighboring quadrant)
        state, ok, msg = navigate(state, course=1.0, warp=2.0)
        self.assertTrue(ok)
        self.assertGreater(state.quadrant_x, 2)

    def test_insufficient_energy_rejects_navigation(self) -> None:
        state = init_game(seed=42)
        state.energy = 10.0
        state, ok, msg = navigate(state, course=1.0, warp=4.0)
        self.assertFalse(ok)
        self.assertIn("Insufficient energy", msg)

    def test_damaged_warp_engines_limits_warp_factor(self) -> None:
        state = init_game(seed=42)
        state.devices[Device.WARP_ENGINES] = 3.5  # Damaged!
        state, ok, msg = navigate(state, course=1.0, warp=1.0)
        self.assertFalse(ok)
        self.assertIn("Warp engines are damaged", msg)

        # But impulse speed (<= 0.2) is still permitted
        state, ok, msg = navigate(state, course=1.0, warp=0.2)
        self.assertTrue(ok)


class TestCombatPhasersAndTorpedoes(unittest.TestCase):
    """Verifies phaser energy division, distance degradation, and torpedo trajectories."""

    def test_phaser_fire_damages_klingons(self) -> None:
        state = init_game(seed=42)
        state.sector_x = 0
        state.sector_y = 0
        # Place 1 Klingon at 2,0 (distance 2)
        target = KlingonShip(ship_id=1, sector_x=2, sector_y=0, shields=100.0, max_shields=100.0)
        state.klingons_in_quadrant = [target]
        state.galaxy[state.quadrant_y][state.quadrant_x].klingons = 1

        initial_energy = state.energy
        # Fire 400 energy units
        state, ok, msg = fire_phasers(state, energy_to_fire=400.0)
        self.assertTrue(ok)
        self.assertEqual(state.energy, initial_energy - 400.0)
        # Target took heavy damage
        self.assertLess(target.shields, 100.0)

    def test_phasers_reject_damaged_subsystem(self) -> None:
        state = init_game(seed=42)
        state.devices[Device.PHASER_CONTROL] = 2.0
        state.klingons_in_quadrant = [KlingonShip(1, 2, 2, 100.0, 100.0)]
        state, ok, msg = fire_phasers(state, 200.0)
        self.assertFalse(ok)
        self.assertIn("damaged and offline", msg)

    def test_torpedo_direct_hit_destroys_klingon(self) -> None:
        state = init_game(seed=42)
        state.sector_x = 0
        state.sector_y = 3
        # Put Klingon directly East at 4, 3
        k = KlingonShip(ship_id=1, sector_x=4, sector_y=3, shields=200.0, max_shields=200.0)
        state.klingons_in_quadrant = [k]
        state.galaxy[state.quadrant_y][state.quadrant_x].klingons = 1
        # Clear obstacles between
        state.stars_in_quadrant = []

        initial_torpedoes = state.torpedoes
        # Course 1 is East
        state, ok, msg = fire_torpedo(state, course=1.0)
        self.assertTrue(ok)
        self.assertEqual(state.torpedoes, initial_torpedoes - 1)
        self.assertFalse(k.is_alive)
        self.assertEqual(state.galaxy[state.quadrant_y][state.quadrant_x].klingons, 0)
        self.assertIn("DIRECT HIT", msg)

    def test_torpedo_striking_star_dissipates(self) -> None:
        state = init_game(seed=42)
        state.sector_x = 0
        state.sector_y = 3
        state.klingons_in_quadrant = []
        state.stars_in_quadrant = [(3, 3)]

        state, ok, msg = fire_torpedo(state, course=1.0)
        self.assertTrue(ok)
        self.assertIn("struck a star", msg)

    def test_torpedo_rejection_when_exhausted(self) -> None:
        state = init_game(seed=42)
        state.torpedoes = 0
        state, ok, msg = fire_torpedo(state, course=1.0)
        self.assertFalse(ok)
        self.assertIn("expended", msg)


class TestShieldsAndStarbaseDocking(unittest.TestCase):
    """Verifies deflector shield energy transfer and Starbase full resupply."""

    def test_transfer_energy_to_shields(self) -> None:
        state = init_game(seed=42)
        initial_energy = state.energy
        initial_shields = state.shields

        state, ok, msg = transfer_shields(state, 300.0)
        self.assertTrue(ok)
        self.assertEqual(state.shields, initial_shields + 300.0)
        self.assertEqual(state.energy, initial_energy - 300.0)

    def test_transfer_energy_from_shields_to_reserves(self) -> None:
        state = init_game(seed=42)
        state.shields = 800.0
        state.energy = 2000.0

        state, ok, msg = transfer_shields(state, -200.0)
        self.assertTrue(ok)
        self.assertEqual(state.shields, 600.0)
        self.assertEqual(state.energy, 2200.0)

    def test_starbase_docking_full_resupply(self) -> None:
        state = init_game(seed=42)
        state.energy = 500.0
        state.torpedoes = 2
        state.shields = 100.0
        state.devices[Device.WARP_ENGINES] = 4.0
        state.devices[Device.PHOTON_TUBES] = 2.5

        # Place Starbase adjacent to Enterprise (within 1.5 sectors)
        state.sector_x = 3
        state.sector_y = 3
        state.starbase_in_quadrant = (4, 3)

        state, ok, msg = dock_at_starbase(state)
        self.assertTrue(ok)
        self.assertEqual(state.energy, 3000.0)
        self.assertEqual(state.torpedoes, 10)
        self.assertGreaterEqual(state.shields, 500.0)
        # All devices repaired
        for dev in state.devices:
            self.assertEqual(state.devices[dev], 0.0)
        self.assertEqual(state.condition, ShipCondition.DOCKED)

    def test_docking_rejected_when_not_adjacent(self) -> None:
        state = init_game(seed=42)
        state.sector_x = 0
        state.sector_y = 0
        state.starbase_in_quadrant = (7, 7)  # Far away!

        state, ok, msg = dock_at_starbase(state)
        self.assertFalse(ok)
        self.assertIn("Not adjacent", msg)


class TestLongRangeSensorScan(unittest.TestCase):
    """Verifies 3x3 quadrant radar reconnaissance grid."""

    def test_long_range_scan_returns_3x3_grid(self) -> None:
        state = init_game(seed=42)
        state.quadrant_x = 3
        state.quadrant_y = 3

        scan = long_range_scan(state)
        self.assertEqual(len(scan), 3)
        self.assertEqual(len(scan[0]), 3)

        # Center of scan must match current quadrant
        center_k, center_b, center_s = scan[1][1]
        cur_q = state.galaxy[3][3]
        self.assertEqual(center_k, cur_q.klingons)
        self.assertEqual(center_b, cur_q.starbases)
        self.assertEqual(center_s, cur_q.stars)
        self.assertTrue(cur_q.scanned)


class TestVictoryAndDefeatScenarios(unittest.TestCase):
    """Verifies mission completion, failure criteria, and efficiency scoring."""

    def test_victory_when_all_klingons_eliminated(self) -> None:
        state = init_game(seed=42)
        # Wipe all Klingons in galaxy
        for row in state.galaxy:
            for q in row:
                q.klingons = 0
        state.klingons_in_quadrant = []

        # Navigation or combat triggers game over check
        state, _, _ = navigate(state, 1.0, 0.2)
        self.assertTrue(state.is_game_over)
        self.assertTrue(state.victory)
        self.assertIn("accomplished", state.game_over_reason.lower())

        score = calculate_score(state)
        self.assertGreater(score, 1000)

    def test_defeat_when_energy_exhausted(self) -> None:
        state = init_game(seed=42)
        state.energy = 5.0
        # Burning remaining energy in navigation
        state.energy = 0.0
        state, _, _ = navigate(state, 1.0, 0.1)
        self.assertTrue(state.is_game_over)
        self.assertFalse(state.victory)
        self.assertIn("out of energy", state.game_over_reason.lower())

    def test_defeat_when_stardate_deadline_exceeded(self) -> None:
        state = init_game(seed=42)
        state.stardate = state.stardate_limit + 1.0
        state, _, _ = navigate(state, 1.0, 0.1)
        self.assertTrue(state.is_game_over)
        self.assertFalse(state.victory)
        self.assertIn("deadline exceeded", state.game_over_reason.lower())


if __name__ == "__main__":
    unittest.main()
