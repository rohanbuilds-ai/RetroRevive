"""
test_platform.py - Automated tests for RetroRevive platform hub, game registry,
and cross-game navigation.
"""

import os
import unittest
import pygame

from game_registry import CATALOG, GameCategory, GameMetadata, GameRegistry, GameStatus
from games import lander_app, lander_engine, matches_app, matches_engine
from retrorevive import RetroReviveHub
from ui_pygame import GameApp
from ui_theme import SoundSynthesizer


class TestGameRegistry(unittest.TestCase):
    """Verifies catalog queries, category filters, and metadata consistency."""

    def setUp(self) -> None:
        self.registry = GameRegistry()

    def test_catalog_contains_expected_games(self) -> None:
        games = self.registry.list_all()
        self.assertGreaterEqual(len(games), 5)
        ids = [g.game_id for g in games]
        self.assertIn("hammurabi", ids)
        self.assertIn("23_matches", ids)
        self.assertIn("lunar_lander", ids)
        self.assertIn("super_star_trek", ids)
        self.assertIn("oregon_trail", ids)

    def test_playable_filter(self) -> None:
        playable = self.registry.list_playable()
        self.assertEqual(len(playable), 3)
        p_ids = [g.game_id for g in playable]
        self.assertIn("hammurabi", p_ids)
        self.assertIn("23_matches", p_ids)
        self.assertIn("lunar_lander", p_ids)

    def test_category_filtering(self) -> None:
        strategy = self.registry.filter_by_category(GameCategory.STRATEGY_SIMULATION)
        self.assertTrue(all(g.category == GameCategory.STRATEGY_SIMULATION for g in strategy))
        self.assertIn("hammurabi", [g.game_id for g in strategy])

        space = self.registry.filter_by_category(GameCategory.ADVENTURE_SPACE)
        self.assertEqual(len(space), 2)
        self.assertIn("lunar_lander", [g.game_id for g in space])

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
        self.assertEqual(len(self.hub.cards), 5)
        self.assertIsNone(self.hub.active_subapp)
        self.assertIsNone(self.hub.selected_game_for_modal)
        self.assertEqual(self.hub.selected_card_index, 0)
        self.assertTrue(self.hub.cards[0].is_selected)

    def test_category_tab_filtering(self) -> None:
        # Filter by Space
        self.hub._set_category(GameCategory.ADVENTURE_SPACE)
        self.assertEqual(len(self.hub.cards), 2)
        card_ids = [c.meta.game_id for c in self.hub.cards]
        self.assertIn("lunar_lander", card_ids)
        self.assertIn("super_star_trek", card_ids)

        # Filter by Puzzle
        self.hub._set_category(GameCategory.PUZZLE_LOGIC)
        self.assertEqual(len(self.hub.cards), 1)
        self.assertEqual(self.hub.cards[0].meta.game_id, "23_matches")

        # Return to All
        self.hub._set_category(GameCategory.ALL)
        self.assertEqual(len(self.hub.cards), 5)

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


if __name__ == "__main__":
    unittest.main()
