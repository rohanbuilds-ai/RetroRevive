"""
games/oregon_trail/test_engine.py - Automated unit tests for Oregon Trail pure simulation engine.
"""

import datetime
import random
import unittest

from games.oregon_trail.engine import (
    BASE_PRICES,
    LANDMARKS,
    Inventory,
    LandmarkType,
    Pace,
    PartyMember,
    Profession,
    Rations,
    TrailState,
    Weather,
    buy_supplies,
    calculate_final_score,
    cross_river,
    get_item_price,
    hunt_cycle,
    init_game,
    rest_cycle,
    step_turn,
    travel_cycle,
)


class TestOregonTrailInitialState(unittest.TestCase):
    """Verifies default journey parameters, professions, and party setup."""

    def test_default_initialization(self) -> None:
        state = init_game()
        self.assertEqual(state.miles_traveled, 0.0)
        self.assertEqual(state.total_trail_miles, 2040.0)
        self.assertEqual(len(state.party), 5)
        self.assertTrue(state.party[0].is_leader)
        self.assertEqual(state.party[0].name, "Captain Lewis")
        self.assertTrue(all(m.health == 100.0 for m in state.party))
        self.assertEqual(state.inventory.oxen, 4)
        self.assertEqual(state.inventory.food, 400.0)
        self.assertEqual(state.inventory.clothing, 5)
        self.assertEqual(state.inventory.ammunition, 150)
        self.assertEqual(state.profession, Profession.CARPENTER)
        self.assertEqual(state.inventory.cash, 800.0)
        self.assertFalse(state.is_game_over)
        self.assertFalse(state.victory)
        self.assertEqual(state.current_landmark_idx, 0)
        self.assertTrue(state.at_landmark)

    def test_profession_cash_and_multipliers(self) -> None:
        banker_state = init_game(profession="BANKER")
        self.assertEqual(banker_state.profession, Profession.BANKER)
        self.assertEqual(banker_state.inventory.cash, 1600.0)
        self.assertEqual(banker_state.profession.score_multiplier, 1.0)

        farmer_state = init_game(profession="FARMER")
        self.assertEqual(farmer_state.profession, Profession.FARMER)
        self.assertEqual(farmer_state.inventory.cash, 400.0)
        self.assertEqual(farmer_state.profession.score_multiplier, 3.0)

    def test_custom_party_names(self) -> None:
        comps = ["Abigail", "Benjamin", "Caleb", "Deborah"]
        state = init_game(leader_name="Josiah", companion_names=comps)
        self.assertEqual(state.party[0].name, "Josiah")
        self.assertEqual([m.name for m in state.party[1:]], comps)


class TestTravelProgressionAndConsumption(unittest.TestCase):
    """Verifies distance accumulation, calendar advance, and food consumption."""

    def test_travel_cycle_advances_distance_and_date(self) -> None:
        state = init_game(seed=42)
        start_date = state.current_date
        state = step_turn(state, "TRAVEL", days=4, enable_incidents=False)

        self.assertGreater(state.miles_traveled, 0.0)
        self.assertEqual(state.current_date, start_date + datetime.timedelta(days=4))
        # 5 people eating FILLING rations (3.0 lbs/day) for 4 days = 60 lbs consumed
        self.assertEqual(state.inventory.food, 400.0 - 60.0)

    def test_rations_consumption_rates(self) -> None:
        # Meager rations (2.0 lbs/day)
        state_m = init_game(seed=42)
        state_m.rations = Rations.MEAGER
        state_m = step_turn(state_m, "TRAVEL", days=5, enable_incidents=False)
        # 5 people * 2 lbs/day * 5 days = 50 lbs
        self.assertEqual(state_m.inventory.food, 400.0 - 50.0)

        # Bare bones rations (1.0 lb/day)
        state_b = init_game(seed=42)
        state_b.rations = Rations.BARE_BONES
        state_b = step_turn(state_b, "TRAVEL", days=5, enable_incidents=False)
        # 5 people * 1 lb/day * 5 days = 25 lbs
        self.assertEqual(state_b.inventory.food, 400.0 - 25.0)

    def test_food_depletion_causes_starvation_health_drain(self) -> None:
        state = init_game(seed=42)
        state.inventory.food = 10.0  # severely inadequate food
        initial_hp = state.party[0].health

        state = step_turn(state, "TRAVEL", days=4, enable_incidents=False)
        self.assertEqual(state.inventory.food, 0.0)
        # Health drops due to severe food deficit
        self.assertLess(state.party[0].health, initial_hp - 10.0)

    def test_oxen_loss_halts_travel(self) -> None:
        state = init_game(seed=42)
        state.inventory.oxen = 0
        state = step_turn(state, "TRAVEL", days=4)
        self.assertTrue(state.is_game_over)
        self.assertIn("no oxen", state.game_over_reason.lower())


class TestRestAndHealthRecovery(unittest.TestCase):
    """Verifies healing, illness recovery, and rest cycles."""

    def test_resting_heals_party(self) -> None:
        state = init_game(seed=42)
        state.party[0].health = 50.0
        state = rest_cycle(state, days=3)

        self.assertGreater(state.party[0].health, 50.0)
        self.assertIsNotNone(state.active_event)
        self.assertEqual(state.active_event.event_type, "REST")

    def test_resting_cures_illness_probabilistically(self) -> None:
        state = init_game(seed=10)
        state.party[1].diseases.append("Fever")
        rng = random.Random(1)
        state = rest_cycle(state, days=3, rng=rng)
        # Under seed 1, illness recovery chance succeeds
        self.assertEqual(state.party[1].diseases, [])


class TestHuntingMechanics(unittest.TestCase):
    """Verifies bullet expenditure and meat yields from wild game."""

    def test_hunting_requires_minimum_ammunition(self) -> None:
        state = init_game()
        state.inventory.ammunition = 5
        _, food_yield, msg = hunt_cycle(state)
        self.assertEqual(food_yield, 0)
        self.assertIn("at least 10 bullets", msg)
        self.assertEqual(state.inventory.ammunition, 5)

    def test_successful_hunt_yields_food_and_deducts_ammo(self) -> None:
        state = init_game()
        state.inventory.ammunition = 100
        initial_food = state.inventory.food
        rng = random.Random(1)

        _, food_yield, msg = hunt_cycle(state, rng=rng)
        self.assertGreater(food_yield, 0)
        self.assertEqual(state.inventory.food, initial_food + food_yield)
        self.assertLess(state.inventory.ammunition, 100)
        self.assertIn("Gained", msg)

    def test_skunked_hunt_yields_no_meat(self) -> None:
        state = init_game()
        state.inventory.ammunition = 100
        initial_food = state.inventory.food
        rng = random.Random(42)

        _, food_yield, msg = hunt_cycle(state, rng=rng)
        self.assertEqual(food_yield, 0)
        self.assertEqual(state.inventory.food, initial_food)
        self.assertLess(state.inventory.ammunition, 100)
        self.assertIn("yielded no game", msg)


class TestRiverCrossingMechanics(unittest.TestCase):
    """Verifies ford, caulk, and ferry decisions at river milestones."""

    def test_ferry_safe_with_sufficient_funds(self) -> None:
        state = init_game()
        state.inventory.cash = 50.0
        state.current_landmark_idx = 1  # Kansas River Crossing
        state.pending_river = LANDMARKS[1]

        state, success, msg = cross_river(state, choice="FERRY")
        self.assertTrue(success)
        self.assertEqual(state.inventory.cash, 45.0)
        self.assertIsNone(state.pending_river)

    def test_ferry_rejects_insufficient_funds(self) -> None:
        state = init_game()
        state.inventory.cash = 2.0
        state.pending_river = LANDMARKS[1]

        state, success, msg = cross_river(state, choice="FERRY")
        self.assertFalse(success)
        self.assertEqual(state.inventory.cash, 2.0)
        self.assertIn("Not enough money", msg)

    def test_shallow_ford_success(self) -> None:
        state = init_game()
        shallow_river = LANDMARKS[1]
        shallow_river.river_depth_ft = 2.0
        state.pending_river = shallow_river

        state, success, msg = cross_river(state, choice="FORD")
        self.assertTrue(success)
        self.assertIn("successful", msg.lower())


class TestStoreAndEconomy(unittest.TestCase):
    """Verifies supply purchasing and distance-based price inflation."""

    def test_distance_inflation_increases_prices(self) -> None:
        trailhead_food = get_item_price("food", 0.0)
        middle_food = get_item_price("food", 1020.0)
        oregon_food = get_item_price("food", 2040.0)

        self.assertEqual(trailhead_food, 0.20)
        self.assertGreater(middle_food, trailhead_food)
        self.assertGreater(oregon_food, middle_food)

    def test_buy_supplies_success(self) -> None:
        state = init_game()
        initial_cash = state.inventory.cash
        initial_oxen = state.inventory.oxen

        state, ok, msg = buy_supplies(state, "oxen", 2)
        self.assertTrue(ok)
        self.assertEqual(state.inventory.oxen, initial_oxen + 2)
        self.assertEqual(state.inventory.cash, initial_cash - 50.0)

    def test_buy_supplies_insufficient_cash_rejected(self) -> None:
        state = init_game()
        state.inventory.cash = 10.0

        state, ok, msg = buy_supplies(state, "oxen", 2)
        self.assertFalse(ok)
        self.assertEqual(state.inventory.cash, 10.0)
        self.assertIn("Not enough cash", msg)


class TestJourneyVictoryAndScoring(unittest.TestCase):
    """Verifies reaching Willamette Valley and score calculations."""

    def test_destination_victory(self) -> None:
        state = init_game()
        state.miles_traveled = 2035.0
        state.current_landmark_idx = 15  # The Dalles

        state = travel_cycle(state, days=2)
        self.assertTrue(state.is_game_over)
        self.assertTrue(state.victory)
        self.assertEqual(state.miles_traveled, 2040.0)
        self.assertIn("safely completed", state.game_over_reason.lower())

    def test_score_calculation_with_multipliers(self) -> None:
        state = init_game(profession="FARMER")
        state.victory = True
        state.miles_traveled = 2040.0

        score = calculate_final_score(state)
        self.assertGreater(score, 5000)
        # Farmer gets 3x multiplier
        self.assertEqual(score % 3, 0)


if __name__ == "__main__":
    unittest.main()
