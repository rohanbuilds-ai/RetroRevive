"""
test_platform.py - Automated tests for RetroRevive platform hub, game registry,
and cross-game navigation.
"""

import os
import unittest
import pygame

from game_registry import CATALOG, GameCategory, GameMetadata, GameRegistry, GameStatus
from games import (
    lander_app,
    lander_engine,
    matches_app,
    matches_engine,
    oregon_app,
    oregon_engine,
    trek_app,
    trek_engine,
    wumpus_app,
    wumpus_engine,
)
from retrorevive import CardArtRenderer, RetroReviveHub
from ui_pygame import GameApp
from ui_theme import SoundSynthesizer, UIButton


class TestGameRegistry(unittest.TestCase):
    """Verifies catalog queries, category filters, and metadata consistency."""

    def setUp(self) -> None:
        self.registry = GameRegistry()

    def test_catalog_contains_expected_games(self) -> None:
        games = self.registry.list_all()
        self.assertGreaterEqual(len(games), 6)
        ids = [g.game_id for g in games]
        self.assertIn("hammurabi", ids)
        self.assertIn("23_matches", ids)
        self.assertIn("lunar_lander", ids)
        self.assertIn("super_star_trek", ids)
        self.assertIn("oregon_trail", ids)
        self.assertIn("hunt_the_wumpus", ids)

    def test_playable_filter(self) -> None:
        playable = self.registry.list_playable()
        self.assertEqual(len(playable), 6)
        p_ids = [g.game_id for g in playable]
        self.assertIn("hammurabi", p_ids)
        self.assertIn("23_matches", p_ids)
        self.assertIn("lunar_lander", p_ids)
        self.assertIn("oregon_trail", p_ids)
        self.assertIn("super_star_trek", p_ids)
        self.assertIn("hunt_the_wumpus", p_ids)

    def test_category_filtering(self) -> None:
        strategy = self.registry.filter_by_category(GameCategory.STRATEGY_SIMULATION)
        self.assertTrue(all(g.category == GameCategory.STRATEGY_SIMULATION for g in strategy))
        self.assertIn("hammurabi", [g.game_id for g in strategy])

        space = self.registry.filter_by_category(GameCategory.ADVENTURE_SPACE)
        self.assertEqual(len(space), 3)
        self.assertIn("lunar_lander", [g.game_id for g in space])
        self.assertIn("super_star_trek", [g.game_id for g in space])
        self.assertIn("hunt_the_wumpus", [g.game_id for g in space])

        puzzle = self.registry.filter_by_category(GameCategory.PUZZLE_LOGIC)
        self.assertEqual(len(puzzle), 1)
        self.assertEqual(puzzle[0].game_id, "23_matches")

        all_games = self.registry.filter_by_category(GameCategory.ALL)
        self.assertEqual(len(all_games), len(self.registry.list_all()))

    def test_search_functionality(self) -> None:
        # Search by title
        ham_results = self.registry.search("hammurabi")
        self.assertEqual(len(ham_results), 1)
        self.assertEqual(ham_results[0].game_id, "hammurabi")

        lander_results = self.registry.search("lander")
        self.assertEqual(len(lander_results), 1)
        self.assertEqual(lander_results[0].game_id, "lunar_lander")

        # Search by tag
        apollo_results = self.registry.search("Apollo")
        self.assertEqual(len(apollo_results), 1)
        self.assertEqual(apollo_results[0].game_id, "lunar_lander")

        nim_results = self.registry.search("nim")
        self.assertEqual(len(nim_results), 1)
        self.assertEqual(nim_results[0].game_id, "23_matches")

        # Search by author
        storer_results = self.registry.search("Storer")
        self.assertEqual(len(storer_results), 1)
        self.assertEqual(storer_results[0].game_id, "lunar_lander")

        albrecht_results = self.registry.search("Albrecht")
        self.assertEqual(len(albrecht_results), 1)
        self.assertEqual(albrecht_results[0].game_id, "23_matches")

        # Empty search returns all
        self.assertEqual(len(self.registry.search("")), len(self.registry.list_all()))

    def test_register_custom_game_dynamically(self) -> None:
        custom_game = GameMetadata(
            game_id="spacewar",
            title="SPACEWAR!",
            subtitle="The Original PDP-1 Space Combat Game",
            year=1962,
            author="Steve Russell",
            original_publisher="MIT",
            category=GameCategory.ADVENTURE_SPACE,
            category_display="Adventure & Space",
            status=GameStatus.COMING_SOON,
            modes=["Classic 2-Player"],
            description="Gravity well dogfight.",
            rules_summary="Shoot torpedoes.",
            historical_provenance="PDP-1 Spacewar.",
            book_source="Origins of Computing.",
            tags=["Space", "Pioneer"],
        )
        self.registry.register(custom_game)
        self.assertIsNotNone(self.registry.get("spacewar"))
        self.assertEqual(self.registry.get("spacewar").year, 1962)


class TestRetroReviveHubNavigation(unittest.TestCase):
    """Verifies hub interface, card cycling, search, and detail modals."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        self.hub = RetroReviveHub()

    def test_hub_initial_state(self) -> None:
        self.assertEqual(len(self.hub.cards), 6)
        self.assertIsNone(self.hub.active_subapp)
        self.assertIsNone(self.hub.selected_game_for_modal)
        self.assertEqual(self.hub.selected_card_index, 0)
        self.assertTrue(self.hub.cards[0].is_selected)

    def test_category_tab_filtering(self) -> None:
        # Filter by Space
        self.hub._set_category(GameCategory.ADVENTURE_SPACE)
        self.assertEqual(len(self.hub.cards), 3)
        card_ids = [c.meta.game_id for c in self.hub.cards]
        self.assertIn("lunar_lander", card_ids)
        self.assertIn("super_star_trek", card_ids)
        self.assertIn("hunt_the_wumpus", card_ids)

        # Filter by Puzzle
        self.hub._set_category(GameCategory.PUZZLE_LOGIC)
        self.assertEqual(len(self.hub.cards), 1)
        self.assertEqual(self.hub.cards[0].meta.game_id, "23_matches")

        # Return to All
        self.hub._set_category(GameCategory.ALL)
        self.assertEqual(len(self.hub.cards), 6)

    def test_card_arrow_cycling(self) -> None:
        self.assertEqual(self.hub.selected_card_index, 0)

        # Press Right Arrow
        ev_right = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        self.hub.handle_event(ev_right)
        self.assertEqual(self.hub.selected_card_index, 1)
        self.assertTrue(self.hub.cards[1].is_selected)

        # Press Left Arrow
        ev_left = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT})
        self.hub.handle_event(ev_left)
        self.assertEqual(self.hub.selected_card_index, 0)

    def test_open_and_close_details_modal(self) -> None:
        meta = self.hub.cards[0].meta
        self.hub._open_details(meta)
        self.assertIsNotNone(self.hub.selected_game_for_modal)
        self.assertEqual(self.hub.selected_game_for_modal.game_id, "hammurabi")

        # Press Escape closes modal
        ev_esc = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        self.hub.handle_event(ev_esc)
        self.assertIsNone(self.hub.selected_game_for_modal)

    def test_search_synthetic_event_and_keypad_enter(self) -> None:
        # Activate search
        self.hub.is_search_active = True
        # Synthetic event without unicode must not crash
        ev_no_unicode = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UNKNOWN})
        self.hub.handle_event(ev_no_unicode)
        self.assertTrue(self.hub.is_search_active)

        # KP_ENTER closes search focus
        ev_kp_enter = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_KP_ENTER})
        self.hub.handle_event(ev_kp_enter)
        self.assertFalse(self.hub.is_search_active)


class TestGameLaunchAndReturn(unittest.TestCase):
    """Verifies clean launching of games and stateful return to library."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        self.hub = RetroReviveHub()

    def test_launch_hammurabi_and_return(self) -> None:
        self.hub.launch_game("hammurabi")
        self.assertIsNotNone(self.hub.active_subapp)
        self.assertIsInstance(self.hub.active_subapp, GameApp)

        # Subapp quit returns to hub
        self.hub.active_subapp.quit()
        self.assertIsNone(self.hub.active_subapp)

    def test_launch_23_matches_and_return(self) -> None:
        self.hub.launch_game("23_matches")
        self.assertIsNotNone(self.hub.active_subapp)
        self.assertIsInstance(self.hub.active_subapp, matches_app.MatchesApp)

        # Subapp back button returns to hub
        self.hub.active_subapp._on_back_clicked()
        self.assertIsNone(self.hub.active_subapp)

    def test_launch_lunar_lander_and_return(self) -> None:
        self.hub.launch_game("lunar_lander")
        self.assertIsNotNone(self.hub.active_subapp)
        self.assertIsInstance(self.hub.active_subapp, lander_app.LanderApp)

        # Subapp back button returns to hub
        self.hub.active_subapp._on_back_clicked()
        self.assertIsNone(self.hub.active_subapp)

    def test_launch_super_star_trek_and_return(self) -> None:
        self.hub.launch_game("super_star_trek")
        self.assertIsNotNone(self.hub.active_subapp)
        self.assertIsInstance(self.hub.active_subapp, trek_app.TrekApp)

        # Subapp back button returns to hub
        self.hub.active_subapp._on_back_clicked()
        self.assertIsNone(self.hub.active_subapp)

    def test_launch_hunt_the_wumpus_and_return(self) -> None:
        self.hub.launch_game("hunt_the_wumpus")
        self.assertIsNotNone(self.hub.active_subapp)
        self.assertIsInstance(self.hub.active_subapp, wumpus_app.WumpusApp)

        # Subapp back button returns to hub
        self.hub.active_subapp._on_back_clicked()
        self.assertIsNone(self.hub.active_subapp)

    def test_numeric_hotkeys_quick_launch(self) -> None:
        # Key '1' launches Hammurabi
        ev_1 = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1})
        self.hub.handle_event(ev_1)
        self.assertIsInstance(self.hub.active_subapp, GameApp)

        self.hub._return_to_hub()
        self.assertIsNone(self.hub.active_subapp)

        # Key '2' launches 23 Matches
        ev_2 = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_2})
        self.hub.handle_event(ev_2)
        self.assertIsInstance(self.hub.active_subapp, matches_app.MatchesApp)

        self.hub._return_to_hub()
        self.assertIsNone(self.hub.active_subapp)

        # Key '3' launches Lunar Lander
        ev_3 = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_3})
        self.hub.handle_event(ev_3)
        self.assertIsInstance(self.hub.active_subapp, lander_app.LanderApp)

        self.hub._return_to_hub()
        self.assertIsNone(self.hub.active_subapp)

        # Key '4' launches Oregon Trail
        ev_4 = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_4})
        self.hub.handle_event(ev_4)
        self.assertIsInstance(self.hub.active_subapp, oregon_app.OregonApp)

        self.hub._return_to_hub()
        self.assertIsNone(self.hub.active_subapp)

        # Key '5' launches Super Star Trek
        ev_5 = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_5})
        self.hub.handle_event(ev_5)
        self.assertIsInstance(self.hub.active_subapp, trek_app.TrekApp)

        self.hub._return_to_hub()
        self.assertIsNone(self.hub.active_subapp)

        # Key '6' launches Hunt the Wumpus
        ev_6 = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_6})
        self.hub.handle_event(ev_6)
        self.assertIsInstance(self.hub.active_subapp, wumpus_app.WumpusApp)

        self.hub._return_to_hub()
        self.assertIsNone(self.hub.active_subapp)


class TestMatchesAppUI(unittest.TestCase):
    """Verifies 23 Matches graphical UI interaction and moves."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        self.app = matches_app.MatchesApp()

    def test_initial_app_state(self) -> None:
        self.assertEqual(len(self.app.matches), 23)
        self.assertEqual(self.app.state.matches_remaining, 23)
        self.assertEqual(self.app.state.current_player, "HUMAN")
        self.assertFalse(self.app.state.game_over)
        self.assertFalse(self.app.show_rules_modal)

    def test_human_move_and_computer_turn_progression(self) -> None:
        # Take 2 matches
        self.app._on_human_move(2)
        self.assertEqual(self.app.state.matches_remaining, 21)
        self.assertTrue(self.app.ai_pending)

        # Advance timer to trigger computer move
        self.app.update(1.0)
        self.assertFalse(self.app.ai_pending)
        self.assertEqual(self.app.state.matches_remaining, 19)
        self.assertEqual(self.app.state.current_player, "HUMAN")

    def test_rules_modal_toggle(self) -> None:
        self.assertFalse(self.app.show_rules_modal)
        self.app._toggle_rules()
        self.assertTrue(self.app.show_rules_modal)
        self.app._toggle_rules()
        self.assertFalse(self.app.show_rules_modal)

    def test_game_restart(self) -> None:
        self.app._on_human_move(3)
        self.assertEqual(self.app.state.matches_remaining, 20)
        self.app._restart_game()
        self.assertEqual(self.app.state.matches_remaining, 23)
        self.assertFalse(self.app.state.game_over)

    def test_23matches_keypad_enter_and_game_over_status(self) -> None:
        # Toggle rules with button then dismiss with KP_ENTER
        self.app._toggle_rules()
        self.assertTrue(self.app.show_rules_modal)
        ev_kp_enter = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_KP_ENTER})
        self.app.handle_event(ev_kp_enter)
        self.assertFalse(self.app.show_rules_modal)

        # Force game over by taking remaining matches
        self.app.state.matches_remaining = 1
        self.app._on_human_move(1)
        self.assertTrue(self.app.state.game_over)
        self.assertEqual(self.app.state.winner, "COMPUTER")
        self.assertIn("Game Over", self.app.status_message)

        # KP_ENTER restarts game from game over
        self.app.handle_event(ev_kp_enter)
        self.assertFalse(self.app.state.game_over)
        self.assertEqual(self.app.state.matches_remaining, 23)


class TestLanderAppUI(unittest.TestCase):
    """Verifies Lunar Lander graphical UI interactions, telemetry, presets, and modals."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        self.app = lander_app.LanderApp()

    def test_initial_app_state(self) -> None:
        self.assertEqual(self.app.state.time_elapsed, 0.0)
        self.assertEqual(self.app.state.altitude, 120.0)
        self.assertEqual(self.app.state.velocity, 1.0)
        self.assertEqual(self.app.state.fuel_remaining, 16500.0)
        self.assertIsNone(self.app.state.outcome)
        self.assertFalse(self.app.state.is_terminal)
        self.assertFalse(self.app.show_rules_modal)
        self.assertEqual(self.app.current_burn_input, 0.0)

    def test_preset_burn_buttons(self) -> None:
        self.app._set_burn(50.0)
        self.assertEqual(self.app.current_burn_input, 50.0)

        self.app._set_burn(200.0)
        self.assertEqual(self.app.current_burn_input, 200.0)

        # Clamping
        self.app._set_burn(350.0)
        self.assertEqual(self.app.current_burn_input, 200.0)

        self.app._set_burn(-10.0)
        self.assertEqual(self.app.current_burn_input, 0.0)

    def test_burn_adjustments(self) -> None:
        self.app._set_burn(100.0)
        self.app._adjust_burn(25.0)
        self.assertEqual(self.app.current_burn_input, 125.0)

        self.app._adjust_burn(-10.0)
        self.assertEqual(self.app.current_burn_input, 115.0)

    def test_auto_hover_calculation(self) -> None:
        self.app._set_hover_burn()
        # Hover burn = (33000 * 0.001) / 1.8 = 18.333 lbs/sec
        self.assertAlmostEqual(self.app.current_burn_input, 18.3, places=1)

    def test_burn_execution_and_telemetry_advance(self) -> None:
        self.app._set_burn(100.0)
        self.app._execute_burn()

        # After 10s burn of 100 lbs/sec, fuel is 15,500 lbs
        self.assertEqual(self.app.state.time_elapsed, 10.0)
        self.assertEqual(self.app.state.fuel_remaining, 15500.0)
        self.assertLess(self.app.state.altitude, 120.0)
        self.assertTrue(self.app.is_thrusting)

    def test_rules_modal_toggle(self) -> None:
        self.assertFalse(self.app.show_rules_modal)
        self.app._toggle_rules()
        self.assertTrue(self.app.show_rules_modal)
        self.app._toggle_rules()
        self.assertFalse(self.app.show_rules_modal)

    def test_restart_flight(self) -> None:
        self.app._set_burn(100.0)
        self.app._execute_burn()
        self.assertEqual(self.app.state.time_elapsed, 10.0)

        self.app._restart_flight()
        self.assertEqual(self.app.state.time_elapsed, 0.0)
        self.assertEqual(self.app.state.altitude, 120.0)
        self.assertEqual(self.app.state.fuel_remaining, 16500.0)
        self.assertEqual(self.app.current_burn_input, 0.0)

    def test_lunar_lander_m_key_toggles_rules_modal(self) -> None:
        self.assertFalse(self.app.show_rules_modal)
        # Press key 'M' toggles flight manual
        ev_m = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_m})
        self.app.handle_event(ev_m)
        self.assertTrue(self.app.show_rules_modal)

        # Press key 'M' again toggles it off
        self.app.handle_event(ev_m)
        self.assertFalse(self.app.show_rules_modal)

    def test_lunar_lander_keypad_enter_executes_burn(self) -> None:
        self.app._set_burn(50.0)
        ev_kp_enter = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_KP_ENTER})
        self.app.handle_event(ev_kp_enter)
        self.assertEqual(self.app.state.time_elapsed, 10.0)
        self.assertEqual(self.app.state.fuel_remaining, 16000.0)


class TestOregonAppUI(unittest.TestCase):
    """Verifies The Oregon Trail graphical UI interactions, modals, and store."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        self.app = oregon_app.OregonApp()

    def test_initial_app_state(self) -> None:
        self.assertEqual(self.app.state.miles_traveled, 0.0)
        self.assertEqual(self.app.state.total_trail_miles, 2040.0)
        self.assertEqual(len(self.app.state.living_members), 5)
        self.assertEqual(self.app.state.pace.value, "STEADY")
        self.assertEqual(self.app.state.rations.value, "FILLING")
        self.assertFalse(self.app.state.is_game_over)
        self.assertFalse(self.app.show_rules_modal)
        self.assertFalse(self.app.show_store_modal)

    def test_travel_advances_miles_and_date(self) -> None:
        initial_date = self.app.state.current_date
        self.app._action_continue()
        self.assertGreater(self.app.state.miles_traveled, 0.0)
        self.assertGreater(self.app.state.current_date, initial_date)

    def test_pace_and_rations_cycle(self) -> None:
        self.assertEqual(self.app.state.pace.value, "STEADY")
        self.app._cycle_pace()
        self.assertEqual(self.app.state.pace.value, "STRENUOUS")
        self.assertIn("STRENUOUS", self.app.btn_pace.text)

        self.assertEqual(self.app.state.rations.value, "FILLING")
        self.app._cycle_rations()
        self.assertEqual(self.app.state.rations.value, "MEAGER")
        self.assertIn("MEAGER", self.app.btn_rations.text)

    def test_rest_action(self) -> None:
        self.app.state.party[0].health = 60.0
        self.app._action_rest()
        self.assertGreater(self.app.state.party[0].health, 60.0)
        self.assertTrue(self.app.show_event_modal)

    def test_modals_toggle(self) -> None:
        # Rules modal
        self.assertFalse(self.app.show_rules_modal)
        self.app._toggle_rules()
        self.assertTrue(self.app.show_rules_modal)
        self.app._toggle_rules()
        self.assertFalse(self.app.show_rules_modal)

        # Log modal
        self.assertFalse(self.app.show_log_modal)
        self.app._toggle_log()
        self.assertTrue(self.app.show_log_modal)
        self.app._toggle_log()
        self.assertFalse(self.app.show_log_modal)

    def test_store_open_and_purchase_at_independence(self) -> None:
        # At start (Independence), store is available
        self.app._open_store()
        self.assertTrue(self.app.show_store_modal)

        initial_cash = self.app.state.inventory.cash
        initial_food = self.app.state.inventory.food

        # Add 20 lbs of food to cart
        self.app.store_cart["food"] = 20
        self.app._execute_store_purchase()

        self.assertFalse(self.app.show_store_modal)
        self.assertEqual(self.app.state.inventory.food, initial_food + 20)
        self.assertLess(self.app.state.inventory.cash, initial_cash)

    def test_restart_trail(self) -> None:
        self.app._action_continue()
        self.assertGreater(self.app.state.miles_traveled, 0.0)

        self.app._restart_trail()
        self.assertEqual(self.app.state.miles_traveled, 0.0)
        self.assertEqual(self.app.state.current_date.month, 4)
        self.assertEqual(self.app.state.current_date.day, 15)
        self.assertFalse(self.app.state.is_game_over)


class TestTrekAppUI(unittest.TestCase):
    """Verifies Super Star Trek graphical UI cockpit, navigation, sensors, and modals."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        self.app = trek_app.TrekApp()

    def test_initial_app_state(self) -> None:
        self.assertEqual(self.app.state.energy, 3000.0)
        self.assertEqual(self.app.state.torpedoes, 10)
        self.assertEqual(self.app.state.shields, 500.0)
        self.assertFalse(self.app.show_rules_modal)
        self.assertFalse(self.app.show_log_modal)
        self.assertFalse(self.app.state.is_game_over)

    def test_course_and_warp_selection(self) -> None:
        self.app._set_course(3.0)
        self.assertEqual(self.app.current_course, 3.0)
        self.assertEqual(self.app._heading_name(3.0), "North")

        self.app._set_warp(2.0)
        self.assertEqual(self.app.current_warp, 2.0)

    def test_fast_nav_execution(self) -> None:
        initial_energy = self.app.state.energy
        self.app._set_course(1.0)
        self.app._set_warp(0.5)
        self.app._execute_fast_nav()
        self.assertLess(self.app.state.energy, initial_energy)

    def test_modals_toggle(self) -> None:
        # Rules modal
        self.assertFalse(self.app.show_rules_modal)
        self.app._toggle_rules()
        self.assertTrue(self.app.show_rules_modal)
        self.app._toggle_rules()
        self.assertFalse(self.app.show_rules_modal)

        # Log modal
        self.assertFalse(self.app.show_log_modal)
        self.app._toggle_log()
        self.assertTrue(self.app.show_log_modal)
        self.app._toggle_log()
        self.assertFalse(self.app.show_log_modal)

    def test_long_range_sensor_scan(self) -> None:
        qx = self.app.state.quadrant_x
        qy = self.app.state.quadrant_y
        self.app._trigger_lrs()
        self.assertTrue(self.app.state.galaxy[qy][qx].scanned)

    def test_dock_button_handling(self) -> None:
        # If not adjacent, dock action notifies toast without crashing
        self.app._action_dock()
        self.assertIsNotNone(self.app.toast_message)
        self.assertTrue(len(self.app.toast_message) > 0)

    def test_restart_mission(self) -> None:
        self.app._set_course(5.0)
        self.app._set_warp(1.0)
        self.app._execute_fast_nav()

        self.app._restart_mission()
        self.assertEqual(self.app.state.energy, 3000.0)
        self.assertEqual(self.app.state.torpedoes, 10)
        self.assertEqual(self.app.state.shields, 500.0)
        self.assertEqual(self.app.state.stardate, 3000.0)
        self.assertFalse(self.app.state.is_game_over)


class TestWumpusAppUI(unittest.TestCase):
    """Verifies Hunt the Wumpus graphical UI chamber, Schlegel chart, and arrow actions."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        self.app = wumpus_app.WumpusApp()

    def test_initial_app_state(self) -> None:
        self.assertEqual(self.app.state.arrows, 5)
        self.assertFalse(self.app.state.is_game_over)
        self.assertFalse(self.app.show_rules_modal)
        self.assertFalse(self.app.show_log_modal)
        self.assertEqual(len(self.app.selected_arrow_path), 0)

    def test_tunnel_traversal(self) -> None:
        initial_room = self.app.state.hunter_room
        self.app._traverse_tunnel(0)
        self.assertNotEqual(self.app.state.hunter_room, initial_room)
        self.assertIn(self.app.state.hunter_room, self.app.state.visited_rooms)

    def test_arrow_path_selection_and_clear(self) -> None:
        self.assertEqual(len(self.app.selected_arrow_path), 0)
        self.app._add_room_to_arrow_path(2)
        self.app._add_room_to_arrow_path(3)
        self.assertEqual(self.app.selected_arrow_path, [2, 3])

        self.app._clear_arrow_path()
        self.assertEqual(len(self.app.selected_arrow_path), 0)

    def test_shoot_arrow_action(self) -> None:
        tunnels = wumpus_engine.DODECAHEDRON_ROOMS[self.app.state.hunter_room]
        target = tunnels[0]
        self.app._add_room_to_arrow_path(target)
        self.app._execute_shoot_arrow()
        self.assertEqual(len(self.app.selected_arrow_path), 0)
        # Either hit wumpus or missed and decremented arrows
        self.assertTrue(self.app.state.arrows == 4 or self.app.state.is_game_over)

    def test_modals_toggle(self) -> None:
        # Rules modal
        self.assertFalse(self.app.show_rules_modal)
        self.app._toggle_rules()
        self.assertTrue(self.app.show_rules_modal)
        self.app._toggle_rules()
        self.assertFalse(self.app.show_rules_modal)

        # Log modal
        self.assertFalse(self.app.show_log_modal)
        self.app._toggle_log()
        self.assertTrue(self.app.show_log_modal)
        self.app._toggle_log()
        self.assertFalse(self.app.show_log_modal)

    def test_restart_game(self) -> None:
        self.app._traverse_tunnel(0)
        self.app._restart_game()
        self.assertEqual(self.app.state.arrows, 5)
        self.assertFalse(self.app.state.is_game_over)
        self.assertEqual(len(self.app.selected_arrow_path), 0)


class TestUIAndArtworkEnhancements(unittest.TestCase):
    """Verifies procedural card artwork generation, delta-time transitions, and search clearing."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        self.hub = RetroReviveHub()

    def test_card_art_renderer_all_games(self) -> None:
        expected_games = ["hammurabi", "23_matches", "lunar_lander", "oregon_trail", "super_star_trek", "hunt_the_wumpus"]
        for gid in expected_games:
            surf = CardArtRenderer.get_art(gid, 94, 132)
            self.assertIsInstance(surf, pygame.Surface)
            self.assertEqual(surf.get_size(), (94, 132))

            # Test caching
            surf_cached = CardArtRenderer.get_art(gid, 94, 132)
            self.assertIs(surf, surf_cached)

    def test_library_card_update_hover_interpolation(self) -> None:
        card = self.hub.cards[0]
        card.is_selected = False
        card.hover_progress = 0.0
        self.assertEqual(card.hover_progress, 0.0)

        # Mark hovered and update with small delta time
        card.is_hovered = True
        card.update(0.05)
        self.assertGreater(card.hover_progress, 0.0)
        self.assertLess(card.hover_progress, 1.0)

        # Unmark hovered and update
        card.is_hovered = False
        card.update(0.1)
        self.assertLess(card.hover_progress, 0.5)

    def test_hub_search_clear_button(self) -> None:
        self.hub.search_query = "nim"
        self.hub._refresh_game_cards()
        self.assertEqual(len(self.hub.cards), 1)

        # Click clear [X] button on search bar: (BASE_WIDTH - 360 + 320 - 15, 106 + 15)
        clear_x = 1280 - 360 + 320 - 15
        clear_y = 106 + 15
        click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (clear_x, clear_y)})
        self.hub.handle_event(click_ev)

        self.assertEqual(self.hub.search_query, "")
        self.assertEqual(len(self.hub.cards), 6)

    def test_hub_status_pulse_timer_advances(self) -> None:
        initial = self.hub.status_pulse_timer
        self.hub.update(0.25)
        self.assertAlmostEqual(self.hub.status_pulse_timer, initial + 0.25, delta=0.01)

    def test_ui_button_hover_progress(self) -> None:
        btn = UIButton((0, 0, 100, 40), "TEST")
        self.assertEqual(btn.hover_progress, 0.0)
        btn.is_hovered = True
        btn.update(0.1)
        self.assertGreater(btn.hover_progress, 0.0)
        btn.is_hovered = False
        btn.update(0.2)
        self.assertLess(btn.hover_progress, 0.5)


if __name__ == "__main__":
    unittest.main()
