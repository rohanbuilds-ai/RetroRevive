"""
games/lunar_lander/test_engine.py - Automated tests for Lunar Lander simulation rules and physics.
"""

import math
import unittest
from .engine import (
    GRAVITY_G,
    INITIAL_ALTITUDE,
    INITIAL_VELOCITY,
    MAX_LEGAL_BURN,
    LanderState,
    init_game,
    step_burn,
    validate_burn,
    _evaluate_landing,
)


class TestLanderInitialState(unittest.TestCase):
    """Verifies default and custom initial configuration of Lunar LEM."""

    def test_default_initial_conditions(self) -> None:
        state = init_game()
        self.assertEqual(state.altitude, 120.0)
        self.assertEqual(state.altitude_feet, 120.0 * 5280.0)
        self.assertEqual(state.velocity, 1.0)
        self.assertEqual(state.velocity_mph, 3600.0)
        self.assertEqual(state.mass, 33000.0)
        self.assertEqual(state.empty_mass, 16500.0)
        self.assertEqual(state.fuel_remaining, 16500.0)
        self.assertEqual(state.time_elapsed, 0.0)
        self.assertFalse(state.landed)
        self.assertIsNone(state.touchdown_velocity_mph)
        self.assertIsNone(state.outcome)
        self.assertEqual(len(state.history), 0)

    def test_custom_initial_state(self) -> None:
        state = init_game(initial_altitude=50.0, initial_velocity=0.5, initial_mass=25000.0, empty_mass=10000.0)
        self.assertEqual(state.altitude, 50.0)
        self.assertEqual(state.velocity, 0.5)
        self.assertEqual(state.fuel_remaining, 15000.0)

    def test_invalid_initial_parameters(self) -> None:
        with self.assertRaises(ValueError):
            init_game(initial_altitude=0.0)
        with self.assertRaises(ValueError):
            init_game(initial_altitude=-10.0)
        with self.assertRaises(ValueError):
            init_game(initial_mass=10000.0, empty_mass=15000.0)


class TestBurnValidation(unittest.TestCase):
    """Verifies burn rate input validation and state preservation."""

    def setUp(self) -> None:
        self.state = init_game()

    def test_valid_burn_rates(self) -> None:
        for val in (0, 10, 50, 100, 150, 200, 45.5):
            ok, err = validate_burn(self.state, val)
            self.assertTrue(ok)
            self.assertIsNone(err)

    def test_reject_negative_burns(self) -> None:
        for val in (-1, -50, -0.1):
            ok, err = validate_burn(self.state, val)
            self.assertFalse(ok)
            self.assertIn("negative", err.lower())

    def test_reject_burn_exceeding_max_thrust(self) -> None:
        for val in (201, 250, 500):
            ok, err = validate_burn(self.state, val)
            self.assertFalse(ok)
            self.assertIn("maximum", err.lower())

    def test_reject_non_numeric_burns(self) -> None:
        for val in ("fifty", None, True, False, [100], "200"):
            ok, err = validate_burn(self.state, val)
            self.assertFalse(ok)
            self.assertIn("numeric", err.lower())

    def test_reject_burn_when_already_landed(self) -> None:
        landed_st = LanderState(altitude=0.0, landed=True)
        ok, err = validate_burn(landed_st, 100)
        self.assertFalse(ok)
        self.assertIn("concluded", err.lower())


class TestPhysicsAndTransitions(unittest.TestCase):
    """Verifies mathematical updates under gravity and retro-thrust."""

    def test_zero_burn_free_fall_step(self) -> None:
        """With zero burn rate, velocity increases by G*T = 0.001 * 10 = 0.01 mi/s."""
        state = init_game()
        next_st = step_burn(state, burn_rate=0.0, time_step=10.0)

        self.assertEqual(next_st.time_elapsed, 10.0)
        self.assertEqual(next_st.mass, 33000.0)
        self.assertEqual(next_st.fuel_remaining, 16500.0)
        # Expected downward velocity increases from 1.0 to 1.01
        self.assertAlmostEqual(next_st.velocity, 1.01, places=3)
        self.assertLess(next_st.altitude, 120.0)
        self.assertEqual(len(next_st.history), 1)

    def test_full_burn_deceleration_step(self) -> None:
        """With maximum burn (200 lbs/sec), downward velocity is significantly reduced."""
        state = init_game()
        next_st = step_burn(state, burn_rate=200.0, time_step=10.0)

        self.assertEqual(next_st.time_elapsed, 10.0)
        # Fuel consumed = 200 * 10 = 2000 lbs
        self.assertEqual(next_st.fuel_remaining, 14500.0)
        # Velocity must be less than previous 1.0 mi/s
        self.assertLess(next_st.velocity, 1.0)

    def test_fuel_exhaustion_initiates_free_fall_terminal(self) -> None:
        """When fuel is zero, the craft falls under gravity to the surface."""
        # Setup low altitude craft with zero fuel
        zero_fuel_st = LanderState(
            altitude=1.0,
            velocity=0.1,
            mass=16500.0,
            empty_mass=16500.0,
            landed=False,
        )
        end_st = step_burn(zero_fuel_st, burn_rate=0.0)
        self.assertTrue(end_st.landed)
        self.assertEqual(end_st.altitude, 0.0)
        self.assertIsNotNone(end_st.touchdown_velocity_mph)
        self.assertGreater(end_st.touchdown_velocity_mph, 0.0)


class TestLandingEvaluationTiers(unittest.TestCase):
    """Verifies historical outcome evaluation and crater calculations."""

    def test_perfect_landing_tier(self) -> None:
        tier, msg, crater = _evaluate_landing(0.8)
        self.assertEqual(tier, "PERFECT")
        self.assertIn("PERFECT LANDING", msg)
        self.assertIsNone(crater)

        tier_border, _, _ = _evaluate_landing(1.2)
        self.assertEqual(tier_border, "PERFECT")

    def test_good_landing_tier(self) -> None:
        tier, msg, crater = _evaluate_landing(5.5)
        self.assertEqual(tier, "GOOD")
        self.assertIn("GOOD LANDING", msg)
        self.assertIsNone(crater)

        tier_border, _, _ = _evaluate_landing(10.0)
        self.assertEqual(tier_border, "GOOD")

    def test_damaged_landing_tier(self) -> None:
        tier, msg, crater = _evaluate_landing(35.0)
        self.assertEqual(tier, "DAMAGED")
        self.assertIn("CRAFT DAMAGE", msg)
        self.assertIsNone(crater)

        tier_border, _, _ = _evaluate_landing(60.0)
        self.assertEqual(tier_border, "DAMAGED")

    def test_crash_and_crater_depth(self) -> None:
        impact_w = 100.0
        tier, msg, crater = _evaluate_landing(impact_w)
        self.assertEqual(tier, "CRASH")
        self.assertIn("NO SURVIVORS", msg)
        self.assertIsNotNone(crater)
        # Expected crater depth: W * 0.227 = 22.7 feet
        self.assertAlmostEqual(crater, 22.7, places=2)


class TestRepeatableScenarios(unittest.TestCase):
    """Verifies deterministic flight runs and clean restarts."""

    def test_uncontrolled_free_fall_crash(self) -> None:
        """Free-fall from 120 mi with zero burn rates hits at over 3600 MPH creating a deep crater."""
        st = init_game()
        while not st.landed:
            st = step_burn(st, 0.0)

        self.assertTrue(st.landed)
        self.assertEqual(st.altitude, 0.0)
        self.assertEqual(st.outcome, "CRASH")
        self.assertGreater(st.touchdown_velocity_mph, 3600.0)
        self.assertGreater(st.crater_depth, 800.0)

    def test_state_isolation_on_restart(self) -> None:
        st1 = init_game()
        st1 = step_burn(st1, 100.0)
        self.assertEqual(st1.time_elapsed, 10.0)
        self.assertEqual(st1.fuel_remaining, 15500.0)

        # Fresh restart produces pristine state
        st2 = init_game()
        self.assertEqual(st2.time_elapsed, 0.0)
        self.assertEqual(st2.altitude, 120.0)
        self.assertEqual(st2.fuel_remaining, 16500.0)
        self.assertEqual(st1.fuel_remaining, 15500.0)


if __name__ == "__main__":
    unittest.main()
