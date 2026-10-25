"""
test_ui.py - Automated UI Regression & Interaction Tests for RetroRevive.

Tests synthetic Pygame mouse and keyboard events, button activation, input editing,
screen transitions, invalid numeric submissions, coordinate conversion, and end-to-end paths.
"""

import os
import unittest
import pygame

# Ensure headless video driver is set for test environment if running without display
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from game_logic import GameState
from modern_game_logic import SCENARIOS
from ui_pygame import BASE_HEIGHT, BASE_WIDTH, GameApp
from ui_theme import (
    DecreePreviewData,
    SoundSynthesizer,
    UIButton,
    UIDecreePreview,
    UIModal,
    UINumberInput,
    UIToast,
)


class TestUIButtonClicks(unittest.TestCase):
    """Verifies that buttons trigger callbacks reliably with synthetic mouse events."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        self.clicked_count = 0

    def _dummy_callback(self) -> None:
        self.clicked_count += 1

    def test_button_single_click_activation(self) -> None:
        btn = UIButton((100, 100, 150, 40), "TEST", self._dummy_callback)
        mouse_pos = (120, 120)

        # Mouse Down
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": mouse_pos})
        consumed = btn.handle_event(ev_down, mouse_pos)
        self.assertTrue(consumed)
        self.assertTrue(btn.is_pressed)
        self.assertEqual(self.clicked_count, 0)

        # Mouse Up inside button
        ev_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": mouse_pos})
        consumed = btn.handle_event(ev_up, mouse_pos)
        self.assertTrue(consumed)
        self.assertFalse(btn.is_pressed)
        self.assertEqual(self.clicked_count, 1)

    def test_button_drag_outside_cancels_click(self) -> None:
        btn = UIButton((100, 100, 150, 40), "TEST", self._dummy_callback)

        # Mouse Down inside
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (120, 120)})
        btn.handle_event(ev_down, (120, 120))
        self.assertTrue(btn.is_pressed)

        # Mouse Up outside
        ev_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (300, 300)})
        btn.handle_event(ev_up, (300, 300))
        self.assertFalse(btn.is_pressed)
        self.assertEqual(self.clicked_count, 0, "Callback should not fire when released outside")

    def test_disabled_button_blocks_click(self) -> None:
        btn = UIButton((100, 100, 150, 40), "DISABLED", self._dummy_callback)
        btn.is_enabled = False

        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (120, 120)})
        consumed = btn.handle_event(ev_down, (120, 120))
        self.assertFalse(consumed)
        self.assertFalse(btn.is_pressed)
        self.assertEqual(self.clicked_count, 0)


class TestUINumberInputEditingAndValidation(unittest.TestCase):
    """Tests keyboard typing, backspace, malformed input parsing, and recursion safety."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        self.changed_val = None

    def _on_change(self, val: int) -> None:
        self.changed_val = val

    def test_direct_typing_and_backspace(self) -> None:
        inp = UINumberInput((50, 50, 300, 100), initial_value=0, on_change=self._on_change)
        inp.is_active = True
        inp.text_buffer = ""

        # Type '500'
        for ch in "500":
            ev = pygame.event.Event(pygame.KEYDOWN, {"key": ord(ch), "unicode": ch})
            inp.handle_event(ev, (0, 0))

        self.assertEqual(inp.text_buffer, "500")
        self.assertEqual(inp.value, 500)
        self.assertEqual(self.changed_val, 500)

        # Backspace
        ev_bs = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_BACKSPACE, "unicode": ""})
        inp.handle_event(ev_bs, (0, 0))
        self.assertEqual(inp.text_buffer, "50")
        self.assertEqual(inp.value, 50)

    def test_malformed_string_parsing(self) -> None:
        inp = UINumberInput((50, 50, 300, 100), initial_value=100)

        # Empty string
        inp.text_buffer = "   "
        ok, val, err = inp.parse_integer()
        self.assertFalse(ok)
        self.assertIsNone(val)
        self.assertIn("empty", err.lower())

        # Non-numeric text
        inp.text_buffer = "abc123"
        ok, val, err = inp.parse_integer()
        self.assertFalse(ok)
        self.assertIsNone(val)
        self.assertIn("not an integer", err.lower())

        # Decimal string
        inp.text_buffer = "12.5"
        ok, val, err = inp.parse_integer()
        self.assertFalse(ok)
        self.assertIsNone(val)

        # Valid negative integer
        inp.text_buffer = "-50"
        ok, val, err = inp.parse_integer()
        self.assertTrue(ok)
        self.assertEqual(val, -50)
        self.assertIsNone(err)

    def test_stepper_buttons_adjust_and_clear(self) -> None:
        inp = UINumberInput((50, 50, 300, 100), initial_value=200, step=10, max_value=1000)

        inp.adjust(10)
        self.assertEqual(inp.value, 210)
        self.assertEqual(inp.text_buffer, "210")

        inp.adjust(-100)
        self.assertEqual(inp.value, 110)

        inp.set_max()
        self.assertEqual(inp.value, 1000)

        inp.clear()
        self.assertEqual(inp.value, 0)
        self.assertEqual(inp.text_buffer, "0")

    def test_no_infinite_recursion_on_set_value(self) -> None:
        """Verifies the fix for the critical recursion crash when input_buy triggers input_sell updates."""
        app = GameApp()
        app._start_classic_game()
        # Entering any positive buy amount previously triggered maximum recursion depth exceeded
        app.input_buy.set_value(5)
        self.assertEqual(app.input_buy.value, 5)
        self.assertFalse(app.input_sell.is_enabled, "Selling should be disabled when buying in Classic mode")


class TestScreenNavigationAndModals(unittest.TestCase):
    """Tests screen transitions, modal dialogs, and scenario/tutorial controls."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        if os.path.exists("retrorevive_save.json"):
            os.remove("retrorevive_save.json")
        self.app = GameApp()

    def tearDown(self) -> None:
        if os.path.exists("retrorevive_save.json"):
            os.remove("retrorevive_save.json")

    def test_main_menu_to_screens(self) -> None:
        # Start Classic
        self.app.menu_buttons[0].callback()
        self.assertEqual(self.app.current_screen, "GAMEPLAY")
        self.assertEqual(self.app.active_mode, "CLASSIC")

        # Return to Menu
        self.app._return_to_main_menu()
        self.assertEqual(self.app.current_screen, "MAIN_MENU")

        # Open Scenarios
        self.app._open_scenarios_screen()
        self.assertEqual(self.app.current_screen, "SCENARIOS")

        # Click Back in Scenarios
        btn_back = self.app.btn_scenarios_back
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (btn_back.rect.centerx, btn_back.rect.centery)})
        ev_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (btn_back.rect.centerx, btn_back.rect.centery)})
        self.app.handle_event(ev_down)
        self.app.handle_event(ev_up)
        self.assertEqual(self.app.current_screen, "MAIN_MENU")

    def test_scenario_launch_buttons(self) -> None:
        self.app._open_scenarios_screen()
        self.assertIn("drought", self.app.scenario_play_buttons)

        btn_drought = self.app.scenario_play_buttons["drought"]
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (btn_drought.rect.centerx, btn_drought.rect.centery)})
        ev_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (btn_drought.rect.centerx, btn_drought.rect.centery)})
        self.app.handle_event(ev_down)
        self.app.handle_event(ev_up)

        self.assertEqual(self.app.current_screen, "GAMEPLAY")
        self.assertEqual(self.app.active_mode, "ENHANCED")
        self.assertIsNotNone(self.app.enhanced_state)
        self.assertEqual(self.app.enhanced_state.scenario_id, "drought")

    def test_tutorial_prev_next_buttons_and_disabled_state(self) -> None:
        self.app._open_instructions_screen()
        self.assertEqual(self.app.tutorial_step, 0)

        # On Step 0, Prev is disabled
        self.app.draw()
        self.assertFalse(self.app.btn_tutorial_prev.is_enabled)
        self.assertTrue(self.app.btn_tutorial_next.is_enabled)

        # Click Next
        btn_next = self.app.btn_tutorial_next
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (btn_next.rect.centerx, btn_next.rect.centery)})
        ev_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (btn_next.rect.centerx, btn_next.rect.centery)})
        self.app.handle_event(ev_down)
        self.app.handle_event(ev_up)
        self.assertEqual(self.app.tutorial_step, 1)

        # Advance to step 4 (last step)
        for _ in range(3):
            self.app._next_tutorial_step()
        self.assertEqual(self.app.tutorial_step, 4)
        self.app.draw()
        self.assertTrue(self.app.btn_tutorial_prev.is_enabled)
        self.assertFalse(self.app.btn_tutorial_next.is_enabled, "Next button must be disabled on step 4")

    def test_advisors_modal_apply_advice(self) -> None:
        self.app._start_enhanced_game()
        self.app._open_advisors_modal()
        self.assertIsNotNone(self.app.active_modal)

        # Click 'APPLY ADVICE' (first action button in modal)
        apply_btn = self.app.active_modal.action_buttons[0]
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (apply_btn.rect.centerx, apply_btn.rect.centery)})
        ev_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (apply_btn.rect.centerx, apply_btn.rect.centery)})
        self.app.handle_event(ev_down)
        self.app.handle_event(ev_up)

        self.assertIsNone(self.app.active_modal, "Modal should close on apply")
        self.assertEqual(self.app.input_feed.value, 2000)
        self.assertEqual(self.app.input_plant.value, 999)


class TestCoordinateScalingAndLetterboxing(unittest.TestCase):
    """Tests resolution scaling, pillarboxing, and mouse coordinate mapping."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        if os.path.exists("retrorevive_save.json"):
            os.remove("retrorevive_save.json")
        self.app = GameApp()

    def tearDown(self) -> None:
        if os.path.exists("retrorevive_save.json"):
            os.remove("retrorevive_save.json")

    def test_1280x720_native_coordinate_mapping(self) -> None:
        self.app.screen_width = 1280
        self.app.screen_height = 720
        cx, cy = self.app._screen_to_canvas((640, 360))
        self.assertEqual((cx, cy), (640, 360))

    def test_1920x1080_proportional_mapping(self) -> None:
        self.app.screen_width = 1920
        self.app.screen_height = 1080
        cx, cy = self.app._screen_to_canvas((960, 540))
        self.assertEqual((cx, cy), (640, 360))

    def test_pillarbox_ultrawide_mapping(self) -> None:
        # 2560x1080 (21:9 ultrawide) -> Black bars on sides
        self.app.screen_width = 2560
        self.app.screen_height = 1080
        vp_x, vp_y, vp_w, vp_h = self.app._compute_viewport()
        self.assertEqual(vp_h, 1080)
        self.assertEqual(vp_w, 1920)
        self.assertEqual(vp_x, (2560 - 1920) // 2)

        # Center of viewport maps to center of canvas
        cx, cy = self.app._screen_to_canvas((1280, 540))
        self.assertEqual((cx, cy), (640, 360))


class TestEndToEndGameplay(unittest.TestCase):
    """Verifies complete interactive paths through the game."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        if os.path.exists("retrorevive_save.json"):
            os.remove("retrorevive_save.json")
        self.app = GameApp()

    def tearDown(self) -> None:
        if os.path.exists("retrorevive_save.json"):
            os.remove("retrorevive_save.json")

    def test_classic_mode_turn_advancement(self) -> None:
        self.app._start_classic_game()
        self.assertEqual(self.app._get_current_game_state().year, 1)

        # Set valid decrees
        self.app.input_buy.set_value(0)
        self.app.input_sell.set_value(0)
        self.app.input_feed.set_value(2000)
        self.app.input_plant.set_value(800)

        # Enact decree
        self.app._on_execute_turn()
        self.assertEqual(self.app.current_screen, "GAMEPLAY")
        self.assertEqual(self.app._get_current_game_state().year, 2)

    def test_negative_input_dismisses_steward(self) -> None:
        self.app._start_classic_game()
        self.app.input_feed.text_buffer = "-50"
        self.app._on_execute_turn()

        self.assertEqual(self.app.current_screen, "GAME_OVER")
        res = self.app.game_over_result
        self.assertIsNotNone(res)
        self.assertEqual(res["state"].game_over_reason, "STEWARD_FIRED")
        self.assertIn("GET YOURSELF ANOTHER STEWARD", res["message"])

    def test_malformed_input_rejection_leaves_state_intact(self) -> None:
        self.app._start_classic_game()
        st_before = self.app._get_current_game_state()

        self.app.input_buy.text_buffer = "invalid_text"
        self.app._on_execute_turn()

        st_after = self.app._get_current_game_state()
        self.assertEqual(st_before.year, st_after.year)
        self.assertEqual(st_before.bushels, st_after.bushels)
        self.assertIsNotNone(self.app.input_buy.error_message)


class TestDecreePreviewCalculations(unittest.TestCase):
    """Verifies deterministic, RNG-free decree calculations and validation warnings."""

    def setUp(self) -> None:
        self.base_state = GameState(
            year=1, population=100, bushels=2800, acres=1000, land_price=20,
            starved_this_year=0, starved_total=0, starved_pct_avg=0.0,
            immigrants_this_year=5, harvest_yield=3, rats_ate=200,
            plague_struck=False, plague_next_year=False, is_over=False
        )

    def test_preview_full_feeding_sustainable(self) -> None:
        # Feed 2000 (100 * 20), plant 800 (requires 400 bushels) -> 400 remaining
        p = DecreePreviewData(self.base_state, buy=0, sell=0, feed=2000, plant=800)
        self.assertTrue(p.is_valid)
        self.assertIsNone(p.critical_error)
        self.assertEqual(p.citizens_fed, 100)
        self.assertEqual(p.starving_citizens, 0)
        self.assertEqual(p.seed_bushels, 400)
        self.assertEqual(p.grain_balance, 400)
        self.assertIn("fully rationed", p.warning_msg.lower())

    def test_preview_starvation_warning_and_impeachment_threat(self) -> None:
        # Severe underfeeding: only feed 800 (40 fed, 60 starved = 60%)
        p = DecreePreviewData(self.base_state, buy=0, sell=0, feed=800, plant=500)
        self.assertTrue(p.is_valid)  # Mechanically valid input, but catastrophic consequence
        self.assertEqual(p.citizens_fed, 40)
        self.assertEqual(p.starving_citizens, 60)
        self.assertEqual(p.starvation_pct, 60.0)
        self.assertIn("impeachment", p.warning_msg.lower())

    def test_preview_grain_deficit_detection(self) -> None:
        # Over-allocating grain: 2000 feed + 2000 plant (needs 1000 bu seed) = 3000 bu > 2800 bu
        p = DecreePreviewData(self.base_state, buy=0, sell=0, feed=2000, plant=2000)
        self.assertFalse(p.is_valid)
        self.assertEqual(p.grain_balance, -200)
        self.assertIn("deficit", p.critical_error.lower())

    def test_preview_workforce_capacity_limit(self) -> None:
        # 100 people can cultivate at most 999 acres (D < 10*P)
        p = DecreePreviewData(self.base_state, buy=0, sell=0, feed=2000, plant=1000)
        self.assertFalse(p.is_valid)
        self.assertIn("workforce limit", p.critical_error.lower())

    def test_preview_buy_and_sell_conflict(self) -> None:
        p = DecreePreviewData(self.base_state, buy=50, sell=50, feed=2000, plant=500)
        self.assertFalse(p.is_valid)
        self.assertIn("cannot buy and sell", p.critical_error.lower())


class TestKeyboardShortcutsAndAccessibility(unittest.TestCase):
    """Verifies full keyboard navigability across screens and modal dialogs."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        if os.path.exists("retrorevive_save.json"):
            os.remove("retrorevive_save.json")
        self.app = GameApp()

    def tearDown(self) -> None:
        if os.path.exists("retrorevive_save.json"):
            os.remove("retrorevive_save.json")

    def test_menu_numeric_hotkeys(self) -> None:
        # Press '1' to start Classic Mode
        ev_1 = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1})
        self.app.handle_event(ev_1)
        self.assertEqual(self.app.current_screen, "GAMEPLAY")
        self.assertEqual(self.app.active_mode, "CLASSIC")

        # Return and press '3' to open Scenarios
        self.app._return_to_main_menu()
        ev_3 = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_3})
        self.app.handle_event(ev_3)
        self.assertEqual(self.app.current_screen, "SCENARIOS")

    def test_gameplay_tab_focus_cycle(self) -> None:
        self.app._start_classic_game()
        inputs = [self.app.input_buy, self.app.input_sell, self.app.input_feed, self.app.input_plant]
        self.assertFalse(any(inp.is_active for inp in inputs))

        # First Tab activates input_buy
        ev_tab = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB})
        self.app.handle_event(ev_tab)
        self.assertTrue(self.app.input_buy.is_active)

        # Tab again activates input_feed (input_sell disabled when buy=0 in classic mode or vice versa)
        self.app.handle_event(ev_tab)
        self.assertFalse(self.app.input_buy.is_active)

    def test_shift_tab_backwards_focus_cycle(self) -> None:
        self.app._start_classic_game()
        inputs = [self.app.input_buy, self.app.input_sell, self.app.input_feed, self.app.input_plant]
        # Activate input_feed
        self.app.input_feed.is_active = True

        # Shift+Tab cycles backwards
        pygame.key.get_mods = lambda: pygame.KMOD_LSHIFT
        try:
            ev_shift_tab = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB})
            self.app.handle_event(ev_shift_tab)
            # Should cycle backwards to enabled predecessor (input_sell or input_buy)
            self.assertFalse(self.app.input_feed.is_active)
        finally:
            pygame.key.get_mods = lambda: 0

    def test_enter_submits_decree_directly_when_input_active(self) -> None:
        self.app._start_classic_game()
        self.app.input_buy.text_buffer = ""
        self.app.input_buy.is_active = True

        # Pressing Enter while editing must directly validate and set error without requiring a second Enter
        ev_enter = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
        self.app.handle_event(ev_enter)
        self.assertFalse(self.app.input_buy.is_active)
        self.assertEqual(self.app.input_buy.error_message, "?REDO FROM START: Input cannot be empty.")

    def test_keypad_enter_submits_decree(self) -> None:
        self.app._start_classic_game()
        self.app.input_buy.text_buffer = "abc"
        self.app.input_buy.is_active = True

        # Pressing Keypad Enter must trigger execution and validation directly
        ev_kp_enter = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_KP_ENTER})
        self.app.handle_event(ev_kp_enter)
        self.assertFalse(self.app.input_buy.is_active)
        self.assertEqual(self.app.input_buy.error_message, "?REDO FROM START: 'abc' is not an integer.")

    def test_synthetic_event_without_unicode_does_not_crash(self) -> None:
        self.app._start_classic_game()
        self.app.input_buy.is_active = True

        # Event dictionary without 'unicode' key must not raise AttributeError
        ev_no_unicode = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UNKNOWN})
        self.app.handle_event(ev_no_unicode)
        self.assertTrue(self.app.input_buy.is_active)

    def test_gameplay_reset_hotkey(self) -> None:
        self.app._start_classic_game()
        self.app.input_feed.set_value(500)
        self.assertEqual(self.app.input_feed.value, 500)

        # Press 'R' when no input active resets to default rations
        ev_r = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_r})
        self.app.handle_event(ev_r)
        self.assertEqual(self.app.input_feed.value, 2000)

    def test_modal_escape_and_enter_keys(self) -> None:
        self.app._open_settings_modal()
        self.assertIsNotNone(self.app.active_modal)

        # Press Escape closes modal
        ev_esc = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        self.app.handle_event(ev_esc)
        self.assertIsNone(self.app.active_modal)


class TestAnnualSummaryAndDeltas(unittest.TestCase):
    """Verifies that annual transition summaries record deltas accurately."""

    def setUp(self) -> None:
        pygame.init()
        SoundSynthesizer.set_enabled(False)
        if os.path.exists("retrorevive_save.json"):
            os.remove("retrorevive_save.json")
        self.app = GameApp()

    def tearDown(self) -> None:
        if os.path.exists("retrorevive_save.json"):
            os.remove("retrorevive_save.json")

    def test_annual_summary_metrics_recorded_on_turn_advance(self) -> None:
        self.app._start_classic_game()
        self.assertIsNone(self.app.last_turn_summary)

        # Enact standard decree
        self.app.input_buy.set_value(0)
        self.app.input_sell.set_value(0)
        self.app.input_feed.set_value(2000)
        self.app.input_plant.set_value(800)
        self.app._on_execute_turn()

        self.assertIsNotNone(self.app.last_turn_summary)
        summary = self.app.last_turn_summary
        self.assertEqual(summary["year"], 1)
        self.assertIn("pop_delta", summary)
        self.assertIn("grain_delta", summary)
        self.assertIn("acres_delta", summary)
        self.assertEqual(summary["acres_delta"], 0)


if __name__ == "__main__":
    unittest.main()
