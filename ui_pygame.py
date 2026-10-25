"""
ui_pygame.py - Graphical desktop application for RetroRevive: Hammurabi Reimagined.

Features:
- Full 1280x720 responsive desktop interface with aspect-ratio letterboxing
- CLASSIC MODE: 100% faithful to 1978 Microsoft BASIC Hammurabi rules
- ENHANCED MODE: Interactive Tutorial, Royal Advisors, Chronicle, and Scenarios
- Animated ancient Sumerian kingdom landscape, flowing river, and particles
- Complete interactive controls: Number entry, steppers, Min/Max buttons, Modals
- Save & Resume game persistence via standard-library JSON
"""

import math
import os
import sys
from typing import Dict, List, Optional, Tuple
import pygame

from game_logic import (
    DefaultRNG,
    GameState,
    RandomProvider,
    TurnDecisions,
    evaluate_term,
    init_game,
    step_year,
    validate_buy_land,
    validate_feed_people,
    validate_plant_seed,
    validate_sell_land,
)
from modern_game_logic import (
    SCENARIOS,
    AdvisorAdvice,
    EnhancedGameState,
    delete_save_game,
    get_advisor_advice,
    init_enhanced_game,
    load_game_state,
    save_game_state,
    step_enhanced_year,
)
from ui_theme import (
    FontManager,
    Palette,
    SoundSynthesizer,
    UIButton,
    UIModal,
    UINumberInput,
    UIToast,
)
from ui_world import WorldRenderer


BASE_WIDTH = 1280
BASE_HEIGHT = 720


class GameApp:
    """Main Pygame application controller managing state, screens, and window scaling."""

    def __init__(self, start_fullscreen: bool = False) -> None:
        pygame.init()
        SoundSynthesizer.init()

        self.screen_width = BASE_WIDTH
        self.screen_height = BASE_HEIGHT
        flags = pygame.RESIZABLE
        if start_fullscreen:
            flags |= pygame.FULLSCREEN

        self.window = pygame.display.set_mode((self.screen_width, self.screen_height), flags)
        pygame.display.set_caption("RetroRevive: Hammurabi Reimagined")

        self.canvas = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        self.clock = pygame.time.Clock()
        self.is_running = True

        # Global Settings
        self.animations_enabled = True
        self.sound_enabled = True
        self.animation_speed = 1.0

        # World Scene Renderer
        self.world = WorldRenderer()

        # Navigation State
        self.current_screen = "MAIN_MENU"  # MAIN_MENU, CLASSIC, ENHANCED, SCENARIOS, INSTRUCTIONS, GAME_OVER
        self.active_modal: Optional[UIModal] = None
        self.active_toast: Optional[UIToast] = None

        # Game Instances
        self.classic_state: Optional[GameState] = None
        self.enhanced_state: Optional[EnhancedGameState] = None
        self.active_mode = "CLASSIC"  # "CLASSIC" or "ENHANCED"
        self.game_over_result: Optional[dict] = None

        self._is_updating_inputs = False

        # Turn Control Inputs
        self._init_turn_inputs()

        # Build Screen UI Buttons
        self._init_menu_buttons()
        self._init_scenario_buttons()
        self._init_instruction_buttons()
        self._init_game_over_buttons()

        # Tutorial step
        self.tutorial_step = 0

    def _init_scenario_buttons(self) -> None:
        """Creates persistent buttons for scenario challenges screen."""
        self.btn_scenarios_back = UIButton((50, 30, 120, 38), "← BACK", self._return_to_main_menu)
        self.scenario_play_buttons: Dict[str, UIButton] = {}
        card_w, card_h = 270, 520
        start_x = 55
        card_y = 110
        for i, key in enumerate(SCENARIOS.keys()):
            cx = start_x + i * (card_w + 25)
            self.scenario_play_buttons[key] = UIButton(
                (cx + 25, card_y + card_h - 60, 220, 44),
                "PLAY SCENARIO",
                lambda k=key: self._start_scenario(k),
                primary=True
            )

    def _init_instruction_buttons(self) -> None:
        """Creates persistent buttons for tutorial instructions screen."""
        panel_w, panel_h = 920, 580
        px, py = (BASE_WIDTH - panel_w) // 2, 70
        self.btn_instructions_back = UIButton((px + 30, py + 20, 100, 36), "← MENU", self._return_to_main_menu)
        self.btn_tutorial_prev = UIButton((px + 280, py + panel_h - 65, 140, 42), "← PREV", self._prev_tutorial_step)
        self.btn_tutorial_next = UIButton((px + 500, py + panel_h - 65, 140, 42), "NEXT →", self._next_tutorial_step, primary=True)

    def _init_game_over_buttons(self) -> None:
        """Creates persistent buttons for game over screen."""
        panel_w, panel_h = 760, 520
        px, py = (BASE_WIDTH - panel_w) // 2, 70
        self.btn_game_over_replay = UIButton((px + 140, py + panel_h - 70, 220, 48), "PLAY AGAIN", self._start_classic_game, primary=True)
        self.btn_game_over_menu = UIButton((px + 400, py + panel_h - 70, 220, 48), "MAIN MENU", self._return_to_main_menu, color_scheme="lapis")

    def _init_turn_inputs(self) -> None:
        """Initializes numeric input widgets for land, feeding, and planting."""
        panel_y = 470
        input_w = 360
        input_h = 105

        # Buy Land (x = 30)
        self.input_buy = UINumberInput((30, panel_y, input_w, input_h), label="BUY LAND (Acres)", on_change=self._on_input_changed)
        # Sell Land (x = 30, below buy)
        self.input_sell = UINumberInput((30, panel_y + 115, input_w, input_h), label="SELL LAND (Acres)", on_change=self._on_input_changed)
        # Feed Citizens (x = 410)
        self.input_feed = UINumberInput((410, panel_y, input_w, input_h), label="FEED CITIZENS (Bushels)", on_change=self._on_input_changed)
        # Plant Crops (x = 410, below feed)
        self.input_plant = UINumberInput((410, panel_y + 115, input_w, input_h), label="PLANT SEED (Acres)", on_change=self._on_input_changed)

        # Action Buttons (Right side: x = 800)
        self.btn_execute_turn = UIButton((800, panel_y + 115, 230, 56), "ENACT DECREE", self._on_execute_turn, font_size=20, primary=True)
        self.btn_advisors = UIButton((800, panel_y, 230, 48), "ROYAL ADVISORS", self._open_advisors_modal, font_size=16, color_scheme="lapis")
        self.btn_chronicle = UIButton((800, panel_y + 56, 230, 48), "CHRONICLE LOG", self._open_chronicle_modal, font_size=16)

        # In-Game Header Buttons (Top-Right)
        self.btn_pause = UIButton((1140, 14, 110, 36), "MENU", self._open_pause_modal, font_size=15)
        self.btn_save = UIButton((1020, 14, 110, 36), "SAVE", self._save_game_action, font_size=15, color_scheme="lapis")

    def _init_menu_buttons(self) -> None:
        """Creates main menu buttons."""
        bx = (BASE_WIDTH - 380) // 2
        start_y = 250
        spacing = 58

        self.menu_buttons = [
            UIButton((bx, start_y, 380, 48), "PLAY CLASSIC MODE (1978)", self._start_classic_game, primary=True),
            UIButton((bx, start_y + spacing, 380, 48), "PLAY ENHANCED MODE", self._start_enhanced_game, color_scheme="lapis"),
            UIButton((bx, start_y + spacing * 2, 380, 48), "SCENARIO CHALLENGES", self._open_scenarios_screen, color_scheme="sand"),
            UIButton((bx, start_y + spacing * 3, 380, 48), "HOW TO PLAY & TUTORIAL", self._open_instructions_screen, color_scheme="sand"),
            UIButton((bx, start_y + spacing * 4, 380, 48), "SETTINGS & AUDIO", self._open_settings_modal, color_scheme="sand"),
            UIButton((bx, start_y + spacing * 5, 380, 48), "QUIT GAME", self.quit, color_scheme="crimson"),
        ]

        # Resume button if save exists
        if os.path.exists("retrorevive_save.json"):
            resume_btn = UIButton((bx, start_y - 54, 380, 44), "RESUME SAVED GAME", self._resume_game_action, color_scheme="gold")
            self.menu_buttons.insert(0, resume_btn)

    def _on_input_changed(self, _: int) -> None:
        """Updates UI limits dynamically when inputs change without infinite recursion."""
        if self._is_updating_inputs:
            return
        self._is_updating_inputs = True
        try:
            st = self._get_current_game_state()
            if not st:
                return

            buy = self.input_buy.value
            sell = self.input_sell.value

            # In classic mode, selling is only permitted if buying is 0
            if self.active_mode == "CLASSIC":
                if buy > 0:
                    self.input_sell.is_enabled = False
                    self.input_sell.label = "SELL LAND (Buying Land)"
                    available_grain = max(0, st.bushels - buy * st.land_price)
                else:
                    self.input_sell.is_enabled = True
                    self.input_sell.label = "SELL LAND (Acres)"
                    self.input_sell.max_value = max(0, st.acres - 1)
                    available_grain = max(0, st.bushels + sell * st.land_price)
            else:
                self.input_sell.is_enabled = True
                self.input_sell.label = "SELL LAND (Acres)"
                self.input_sell.max_value = max(0, st.acres)
                available_grain = max(0, st.bushels - buy * st.land_price + sell * st.land_price)

            self.input_buy.max_value = max(0, st.bushels // max(1, st.land_price))
            self.input_feed.max_value = available_grain

            grain_after_feed = max(0, available_grain - self.input_feed.value)
            max_plant_by_seed = grain_after_feed * 2
            max_plant_by_labor = st.population * 10 - 1
            max_plant_by_land = st.acres + buy - sell
            self.input_plant.max_value = max(0, min(max_plant_by_land, max_plant_by_labor, max_plant_by_seed))
        finally:
            self._is_updating_inputs = False

    def _get_current_game_state(self) -> Optional[GameState]:
        if self.active_mode == "ENHANCED" and self.enhanced_state:
            return self.enhanced_state.classic_state
        return self.classic_state

    # -----------------------------------------------------------------------
    # Game Launch & Actions
    # -----------------------------------------------------------------------

    def _start_classic_game(self) -> None:
        SoundSynthesizer.play("harvest")
        self.active_mode = "CLASSIC"
        self.classic_state = init_game()
        self.current_screen = "GAMEPLAY"
        self._reset_turn_inputs_for_new_turn()
        self.show_toast("Welcome, Hammurabi. Govern Sumeria for a 10-year term!")

    def _start_enhanced_game(self) -> None:
        SoundSynthesizer.play("harvest")
        self.active_mode = "ENHANCED"
        self.enhanced_state = init_enhanced_game(mode="ENHANCED")
        self.current_screen = "GAMEPLAY"
        self._reset_turn_inputs_for_new_turn()
        self.show_toast("Enhanced Mode: Royal Advisors and Chronicle active.")

    def _start_scenario(self, scen_id: str) -> None:
        SoundSynthesizer.play("harvest")
        self.active_mode = "ENHANCED"
        self.enhanced_state = init_enhanced_game(mode="SCENARIO", scenario_id=scen_id)
        self.current_screen = "GAMEPLAY"
        self._reset_turn_inputs_for_new_turn()
        scen_title = SCENARIOS[scen_id].title
        self.show_toast(f"Scenario Started: {scen_title}")

    def _reset_turn_inputs_for_new_turn(self) -> None:
        st = self._get_current_game_state()
        if not st:
            return

        self.input_buy.set_value(0)
        self.input_sell.set_value(0)

        # Default feeding to exact requirement (20 per person)
        exact_feed = st.population * 20
        self.input_feed.set_value(min(st.bushels, exact_feed))

        # Default planting to sustainable safe amount
        grain_left = max(0, st.bushels - self.input_feed.value)
        safe_plant = min(st.acres, st.population * 8, grain_left * 2)
        self.input_plant.set_value(safe_plant)

        # Reset active status and error messages
        for inp in [self.input_buy, self.input_sell, self.input_feed, self.input_plant]:
            inp.is_active = False
            inp.error_message = None

        self._on_input_changed(0)

    def _on_execute_turn(self) -> None:
        st = self._get_current_game_state()
        if not st:
            return

        # 1. Parse all 4 inputs (validating integers, empty strings, letters, decimals)
        ok_buy, buy, err_buy = self.input_buy.parse_integer()
        ok_sell, sell, err_sell = self.input_sell.parse_integer()
        ok_feed, feed, err_feed = self.input_feed.parse_integer()
        ok_plant, plant, err_plant = self.input_plant.parse_integer()

        # Reject malformed inputs safely without modifying game state
        if not ok_buy:
            self.input_buy.error_message = err_buy
            self.show_toast(err_buy)
            SoundSynthesizer.play("warning")
            return
        if not ok_sell:
            self.input_sell.error_message = err_sell
            self.show_toast(err_sell)
            SoundSynthesizer.play("warning")
            return
        if not ok_feed:
            self.input_feed.error_message = err_feed
            self.show_toast(err_feed)
            SoundSynthesizer.play("warning")
            return
        if not ok_plant:
            self.input_plant.error_message = err_plant
            self.show_toast(err_plant)
            SoundSynthesizer.play("warning")
            return

        # Clear error tags if syntax was valid
        self.input_buy.error_message = None
        self.input_sell.error_message = None
        self.input_feed.error_message = None
        self.input_plant.error_message = None

        # 2. Check for negative numbers (Historical Classic Rule: lines 321, 341, 412, 442)
        if buy < 0 or sell < 0 or feed < 0 or plant < 0:
            SoundSynthesizer.play("warning")
            fired_state = GameState(
                year=st.year, population=st.population, bushels=st.bushels, acres=st.acres,
                land_price=st.land_price, starved_this_year=0, starved_total=st.starved_total,
                starved_pct_avg=st.starved_pct_avg, immigrants_this_year=0, harvest_yield=0,
                rats_ate=0, plague_struck=False, plague_next_year=False, is_over=True,
                game_over_reason="STEWARD_FIRED"
            )
            self._handle_game_over(fired_state)
            return

        # 3. In Classic Mode, buying land forbids selling land in the same year
        if self.active_mode == "CLASSIC" and buy > 0 and sell > 0:
            msg = "HAMURABI: You cannot both buy and sell land in the same year!"
            self.input_buy.error_message = msg
            self.input_sell.error_message = msg
            self.show_toast(msg)
            SoundSynthesizer.play("warning")
            return

        # 4. Validate Buy Land
        if buy > 0:
            res_buy = validate_buy_land(st, buy)
            if not res_buy.is_valid:
                self.input_buy.error_message = res_buy.message
                self.show_toast(res_buy.message.replace("\n", " "))
                SoundSynthesizer.play("warning")
                return

        # 5. Validate Sell Land
        if sell > 0:
            res_sell = validate_sell_land(st, sell, strict_historical=True)
            if not res_sell.is_valid:
                self.input_sell.error_message = res_sell.message
                self.show_toast(res_sell.message.replace("\n", " "))
                SoundSynthesizer.play("warning")
                return

        # 6. Validate Feed People
        grain_after_land = st.bushels - buy * st.land_price if buy > 0 else st.bushels + sell * st.land_price
        acres_after_land = st.acres + buy - sell
        temp_state = GameState(
            year=st.year, population=st.population, bushels=grain_after_land,
            acres=acres_after_land, land_price=st.land_price, starved_this_year=0,
            starved_total=st.starved_total, starved_pct_avg=st.starved_pct_avg,
            immigrants_this_year=0, harvest_yield=0, rats_ate=0, plague_struck=False,
            plague_next_year=False, is_over=False
        )
        res_feed = validate_feed_people(temp_state, feed)
        if not res_feed.is_valid:
            self.input_feed.error_message = res_feed.message
            self.show_toast(res_feed.message.replace("\n", " "))
            SoundSynthesizer.play("warning")
            return

        # 7. Validate Plant Seed
        grain_after_feed = grain_after_land - feed
        res_plant = validate_plant_seed(temp_state, plant, available_grain=grain_after_feed, strict_historical=True)
        if not res_plant.is_valid:
            self.input_plant.error_message = res_plant.message
            self.show_toast(res_plant.message.replace("\n", " "))
            SoundSynthesizer.play("warning")
            return

        # 8. All orders verified valid -> Advance simulation!
        decisions = TurnDecisions(buy_acres=buy, sell_acres=sell, feed_bushels=feed, plant_acres=plant)

        # Advance Simulation
        if self.active_mode == "ENHANCED" and self.enhanced_state:
            self.enhanced_state = step_enhanced_year(self.enhanced_state, decisions)
            new_st = self.enhanced_state.classic_state
        else:
            self.classic_state = step_year(self.classic_state, decisions)
            new_st = self.classic_state

        # Play sound and particle triggers
        if plant > 0:
            SoundSynthesizer.play("harvest")
            self.world.trigger_harvest_particles(30)
        if new_st.rats_ate > 0:
            self.world.trigger_rat_particles(25)

        # Check Game Over
        if new_st.is_over:
            self._handle_game_over(new_st)
            return

        self._reset_turn_inputs_for_new_turn()
        self.show_toast(f"Year {new_st.year} has arrived in Sumeria.")

    def _handle_game_over(self, state: GameState) -> None:
        if state.game_over_reason == "STEWARD_FIRED":
            self.game_over_result = {
                "tier": 1,
                "acres_per_person": state.acres / state.population if state.population > 0 else 0.0,
                "avg_starved_pct": state.starved_pct_avg,
                "total_starved": state.starved_total,
                "message": "HAMURABI:  I CANNOT DO WHAT YOU WISH.\nGET YOURSELF ANOTHER STEWARD!!!!!",
                "state": state,
            }
            SoundSynthesizer.play("warning")
        elif state.game_over_reason == "IMPEACHED":
            self.game_over_result = {
                "tier": 1,
                "acres_per_person": state.acres / state.population if state.population > 0 else 0.0,
                "avg_starved_pct": state.starved_pct_avg,
                "total_starved": state.starved_total,
                "message": f"YOU STARVED {state.starved_this_year} PEOPLE IN ONE YEAR!!!\nDUE TO THIS EXTREME MISMANAGEMENT YOU HAVE NOT ONLY\nBEEN IMPEACHED AND THROWN OUT OF OFFICE BUT YOU HAVE\nALSO BEEN DECLARED NATIONAL FINK!!!!",
                "state": state,
            }
            SoundSynthesizer.play("warning")
        else:
            eval_res = evaluate_term(state)
            self.game_over_result = {
                "tier": eval_res.tier,
                "acres_per_person": eval_res.acres_per_person,
                "avg_starved_pct": eval_res.avg_starved_pct,
                "total_starved": eval_res.total_starved,
                "message": eval_res.message,
                "state": state,
            }
            if eval_res.tier == 4:
                SoundSynthesizer.play("bell")
                self.world.trigger_victory_fireworks(50)
            else:
                SoundSynthesizer.play("warning")
        self.current_screen = "GAME_OVER"

    def _save_game_action(self) -> None:
        if self.active_mode == "ENHANCED" and self.enhanced_state:
            if save_game_state(self.enhanced_state):
                self.show_toast("Game successfully saved to retrorevive_save.json!")
                SoundSynthesizer.play("coin")
            else:
                self.show_toast("Failed to save game.")
        else:
            # Wrap classic state to save
            wrap = EnhancedGameState(classic_state=self.classic_state, mode="CLASSIC")
            if save_game_state(wrap):
                self.show_toast("Classic game progress saved!")
                SoundSynthesizer.play("coin")

    def _resume_game_action(self) -> None:
        loaded = load_game_state()
        if loaded:
            if loaded.mode == "CLASSIC":
                self.active_mode = "CLASSIC"
                self.classic_state = loaded.classic_state
            else:
                self.active_mode = "ENHANCED"
                self.enhanced_state = loaded
            self.current_screen = "GAMEPLAY"
            self._reset_turn_inputs_for_new_turn()
            self.show_toast(f"Game resumed from Year {self._get_current_game_state().year}!")
            SoundSynthesizer.play("harvest")
        else:
            self.show_toast("No valid save file found.")

    def show_toast(self, message: str) -> None:
        self.active_toast = UIToast(message)

    # -----------------------------------------------------------------------
    # Modals & Dialogs
    # -----------------------------------------------------------------------

    def _open_advisors_modal(self) -> None:
        st = self._get_current_game_state()
        if not st:
            return
        advice = get_advisor_advice(st)
        lines = [
            f"VIZIER: \"{advice.vizier}\"",
            "",
            f"GRANARY MASTER: \"{advice.granary_master}\"",
            "",
            f"SURVEYOR: \"{advice.surveyor}\"",
            "",
            f"Market Land Rating: {advice.land_price_rating}",
        ]

        def apply_advice():
            self.input_feed.set_value(advice.recommended_feed)
            self.input_plant.set_value(advice.recommended_plant)
            self.active_modal = None
            self.show_toast("Royal council recommendations applied to decree.")

        buttons = [
            ("APPLY ADVICE", apply_advice),
            ("CLOSE", lambda: setattr(self, "active_modal", None)),
        ]
        self.active_modal = UIModal("THE ROYAL COUNCIL OF SUMERIA", lines, buttons, width=820, height=480)

    def _open_chronicle_modal(self) -> None:
        if not (self.active_mode == "ENHANCED" and self.enhanced_state):
            self.show_toast("Chronicle Log is available in Enhanced Mode.")
            return

        entries = self.enhanced_state.chronicle
        if not entries:
            lines = ["No historical records yet. Enact decrees to record kingdom history."]
        else:
            lines = [f"{'YR':<4} {'POP':<7} {'GRAIN':<8} {'LAND':<7} {'HARVEST':<9} {'RATS':<7} {'STARVED':<8}"]
            lines.append("-" * 64)
            for e in entries[-8:]:
                lines.append(
                    f"{e.year:<4} {e.population_end:<7} {e.bushels:<8} {e.acres:<7} "
                    f"+{e.harvested_total:<8} -{e.rats_ate:<6} {e.starved:<8}"
                )

        buttons = [("CLOSE", lambda: setattr(self, "active_modal", None))]
        self.active_modal = UIModal("SUMERIAN ROYAL CHRONICLE", lines, buttons, width=760, height=450, monospace=True)

    def _open_pause_modal(self) -> None:
        lines = [
            "Game is paused. What is your decree, Sire?",
            "",
            f"Current Mode: {self.active_mode}",
            f"Audio Effects: {'ENABLED' if SoundSynthesizer.is_enabled() else 'MUTED'}",
            f"Animations: {'ENABLED' if self.animations_enabled else 'REDUCED'}",
        ]

        def toggle_sound():
            SoundSynthesizer.set_enabled(not SoundSynthesizer.is_enabled())
            self._open_pause_modal()

        def toggle_anim():
            self.animations_enabled = not self.animations_enabled
            self._open_pause_modal()

        buttons = [
            ("RESUME", lambda: setattr(self, "active_modal", None)),
            ("SOUND", toggle_sound),
            ("ANIM", toggle_anim),
            ("MAIN MENU", self._return_to_main_menu),
        ]
        self.active_modal = UIModal("PAUSE & GOVERNANCE", lines, buttons, width=680, height=380)

    def _open_settings_modal(self) -> None:
        lines = [
            "RetroRevive Configuration:",
            "",
            f"1. Audio Sound Effects: {'[ENABLED]' if SoundSynthesizer.is_enabled() else '[MUTED]'}",
            f"2. Visual Animations: {'[ACTIVE]' if self.animations_enabled else '[REDUCED]'}",
            "3. Canvas Layout: 1280x720 (Logical HD Scaling)",
            "4. Game Engine: Python Standard Library + Pygame",
        ]

        def toggle_sound():
            SoundSynthesizer.set_enabled(not SoundSynthesizer.is_enabled())
            self._open_settings_modal()

        def toggle_anim():
            self.animations_enabled = not self.animations_enabled
            self._open_settings_modal()

        buttons = [
            ("TOGGLE SOUND", toggle_sound),
            ("TOGGLE ANIM", toggle_anim),
            ("CLOSE", lambda: setattr(self, "active_modal", None)),
        ]
        self.active_modal = UIModal("SETTINGS & DISPLAY", lines, buttons, width=680, height=380)

    def _return_to_main_menu(self) -> None:
        self.active_modal = None
        self.active_toast = None
        for inp in [self.input_buy, self.input_sell, self.input_feed, self.input_plant]:
            inp.is_active = False
            inp.error_message = None
        self.current_screen = "MAIN_MENU"
        self._init_menu_buttons()

    def _open_scenarios_screen(self) -> None:
        self.active_modal = None
        self.active_toast = None
        self.current_screen = "SCENARIOS"

    def _open_instructions_screen(self) -> None:
        self.active_modal = None
        self.active_toast = None
        self.tutorial_step = 0
        self.current_screen = "INSTRUCTIONS"

    def quit(self) -> None:
        self.is_running = False

    # -----------------------------------------------------------------------
    # Main Loop, Event Handling & Canvas Scaling
    # -----------------------------------------------------------------------

    def _compute_viewport(self) -> Tuple[int, int, int, int]:
        """Calculates letterbox viewport offset and dimensions for current window size."""
        win_w = max(1, self.screen_width)
        win_h = max(1, self.screen_height)
        target_aspect = BASE_WIDTH / BASE_HEIGHT

        win_aspect = win_w / win_h
        if win_aspect >= target_aspect:
            vp_h = win_h
            vp_w = int(win_h * target_aspect)
            vp_x = (win_w - vp_w) // 2
            vp_y = 0
        else:
            vp_w = win_w
            vp_h = int(win_w / target_aspect)
            vp_x = 0
            vp_y = (win_h - vp_h) // 2
        return vp_x, vp_y, max(1, vp_w), max(1, vp_h)

    def _screen_to_canvas(self, screen_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Transforms window/screen coordinates to logical 1280x720 canvas coordinates."""
        vp_x, vp_y, vp_w, vp_h = self._compute_viewport()
        sx, sy = screen_pos
        cx = int((sx - vp_x) * (BASE_WIDTH / vp_w))
        cy = int((sy - vp_y) * (BASE_HEIGHT / vp_h))
        return cx, cy

    def handle_event(self, event: pygame.event.Event) -> None:
        # Window resize event
        if event.type == pygame.VIDEORESIZE:
            self.screen_width = event.w
            self.screen_height = event.h
            self.window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

        # Map screen mouse position to logical canvas coordinates
        raw_pos = getattr(event, "pos", pygame.mouse.get_pos())
        canvas_mouse = self._screen_to_canvas(raw_pos)

        # Modal event consumption
        if self.active_modal:
            self.active_modal.handle_event(event, canvas_mouse)
            return

        # Screen-specific routing
        if self.current_screen == "MAIN_MENU":
            for btn in self.menu_buttons:
                btn.handle_event(event, canvas_mouse)
        elif self.current_screen == "GAMEPLAY":
            self._handle_gameplay_events(event, canvas_mouse)
        elif self.current_screen == "GAME_OVER":
            self._handle_game_over_events(event, canvas_mouse)
        elif self.current_screen == "SCENARIOS":
            self._handle_scenarios_events(event, canvas_mouse)
        elif self.current_screen == "INSTRUCTIONS":
            self._handle_instructions_events(event, canvas_mouse)

    def _handle_gameplay_events(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]) -> None:
        # In-Game Header Buttons
        if self.btn_pause.handle_event(event, mouse_pos):
            return
        if self.btn_save.handle_event(event, mouse_pos):
            return

        # Execute Turn Button
        if self.btn_execute_turn.handle_event(event, mouse_pos):
            return

        # Advisors and Chronicle (Enhanced Mode only)
        if self.active_mode == "ENHANCED":
            if self.btn_advisors.handle_event(event, mouse_pos):
                return
            if self.btn_chronicle.handle_event(event, mouse_pos):
                return

        inputs = [self.input_buy, self.input_sell, self.input_feed, self.input_plant]

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                active_idx = -1
                for i, inp in enumerate(inputs):
                    if inp.is_active:
                        active_idx = i
                        inp.is_active = False
                for offset in range(1, len(inputs) + 1):
                    cand_idx = (active_idx + offset) % len(inputs)
                    if inputs[cand_idx].is_enabled:
                        inputs[cand_idx].is_active = True
                        break
                return
            elif event.key == pygame.K_RETURN:
                any_was_active = False
                for inp in inputs:
                    if inp.is_active:
                        inp.is_active = False
                        any_was_active = True
                if not any_was_active:
                    self._on_execute_turn()
                return

        # Forward event to inputs (steppers and typing)
        clicked_any_input = False
        for inp in inputs:
            if inp.handle_event(event, mouse_pos):
                clicked_any_input = True

        # Click outside blur
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not clicked_any_input:
            for inp in inputs:
                inp.is_active = False

    def _handle_game_over_events(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]) -> None:
        if self.btn_game_over_replay.handle_event(event, mouse_pos):
            return
        if self.btn_game_over_menu.handle_event(event, mouse_pos):
            return

    def _handle_scenarios_events(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]) -> None:
        if self.btn_scenarios_back.handle_event(event, mouse_pos):
            return
        for btn in self.scenario_play_buttons.values():
            if btn.handle_event(event, mouse_pos):
                return

    def _handle_instructions_events(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]) -> None:
        if self.btn_instructions_back.handle_event(event, mouse_pos):
            return
        if self.btn_tutorial_prev.handle_event(event, mouse_pos):
            return
        if self.btn_tutorial_next.handle_event(event, mouse_pos):
            return

    def _next_tutorial_step(self) -> None:
        self.tutorial_step = min(4, self.tutorial_step + 1)
        SoundSynthesizer.play("click")

    def _prev_tutorial_step(self) -> None:
        self.tutorial_step = max(0, self.tutorial_step - 1)
        SoundSynthesizer.play("click")

    # -----------------------------------------------------------------------
    # Rendering Screens onto Canvas
    # -----------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.animations_enabled:
            self.world.update(dt)

    def draw(self) -> None:
        # Render active screen onto logical 1280x720 canvas
        if self.current_screen == "MAIN_MENU":
            self._draw_main_menu()
        elif self.current_screen == "GAMEPLAY":
            self._draw_gameplay()
        elif self.current_screen == "GAME_OVER":
            self._draw_game_over()
        elif self.current_screen == "SCENARIOS":
            self._draw_scenarios()
        elif self.current_screen == "INSTRUCTIONS":
            self._draw_instructions()

        # Modal dialogs
        if self.active_modal:
            self.active_modal.draw(self.canvas)

        # Active toast notifications
        if self.active_toast:
            if self.active_toast.is_alive():
                self.active_toast.draw(self.canvas)
            else:
                self.active_toast = None

        # Scale virtual canvas to letterboxed viewport
        vp_x, vp_y, vp_w, vp_h = self._compute_viewport()
        scaled_surf = pygame.transform.smoothscale(self.canvas, (vp_w, vp_h))
        self.window.fill((0, 0, 0))
        self.window.blit(scaled_surf, (vp_x, vp_y))
        pygame.display.flip()

    def _draw_main_menu(self) -> None:
        # Background world scene
        self.world.render(self.canvas)

        # Dark overlay on center for menu readability
        overlay = pygame.Surface((540, 560), pygame.SRCALPHA)
        overlay.fill((20, 16, 12, 215))
        ox = (BASE_WIDTH - 540) // 2
        oy = 110
        self.canvas.blit(overlay, (ox, oy))
        pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT, (ox, oy, 540, 560), width=2, border_radius=12)

        # Game Title
        title_surf = FontManager.title(44).render("RETROREVIVE", True, Palette.GOLD_PALE)
        sub_surf = FontManager.header(24).render("HAMMURABI REIMAGINED", True, Palette.SAND_LIGHT)
        track_surf = FontManager.small(14).render("Confluence Buildathon 2026 — Track: Resurrections", True, Palette.TEXT_MUTED)

        self.canvas.blit(title_surf, title_surf.get_rect(center=(BASE_WIDTH // 2, 145)))
        self.canvas.blit(sub_surf, sub_surf.get_rect(center=(BASE_WIDTH // 2, 185)))
        self.canvas.blit(track_surf, track_surf.get_rect(center=(BASE_WIDTH // 2, 215)))

        # Menu buttons
        for btn in self.menu_buttons:
            btn.draw(self.canvas)

    def _draw_gameplay(self) -> None:
        st = self._get_current_game_state()
        if not st:
            return

        # 1. Background living world
        self.world.render(self.canvas, state=st)

        # 2. Top HUD Bar
        hud_rect = pygame.Rect(0, 0, BASE_WIDTH, 64)
        pygame.draw.rect(self.canvas, Palette.PANEL_BG, hud_rect)
        pygame.draw.line(self.canvas, Palette.GOLD_BASE, (0, 64), (BASE_WIDTH, 64), 2)

        # Mode Badge
        mode_label = f"[{self.active_mode} MODE]" if self.active_mode == "CLASSIC" else "[ENHANCED MODE]"
        badge_col = Palette.SAND_LIGHT if self.active_mode == "CLASSIC" else Palette.LAPIS_LIGHT
        b_surf = FontManager.header(18).render(mode_label, True, badge_col)
        self.canvas.blit(b_surf, (20, 20))

        # Year Indicator
        yr_surf = FontManager.header(22).render(f"YEAR {st.year} OF 10", True, Palette.GOLD_PALE)
        self.canvas.blit(yr_surf, (200, 18))

        # Quick Stats in HUD
        hud_stat = (
            f"Citizens: {st.population}  |  Land: {st.acres} ac  |  "
            f"Grain: {st.bushels} bu  |  Price: {st.land_price} bu/ac"
        )
        stat_surf = FontManager.body(18).render(hud_stat, True, Palette.TEXT_BODY)
        self.canvas.blit(stat_surf, (360, 21))

        # Pause and Save buttons
        self.btn_pause.draw(self.canvas)
        self.btn_save.draw(self.canvas)

        # 3. Annual Report Briefing Card (Upper Floating Card)
        card_w, card_h = 560, 175
        card_x, card_y = 30, 80
        pygame.draw.rect(self.canvas, (28, 22, 18, 220), (card_x, card_y, card_w, card_h), border_radius=8)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, (card_x, card_y, card_w, card_h), width=2, border_radius=8)

        # Header in briefing
        rep_hdr = FontManager.header(18).render(f"HAMURABI: REPORT FOR YEAR {st.year}", True, Palette.GOLD_PALE)
        self.canvas.blit(rep_hdr, (card_x + 16, card_y + 12))

        # Report lines
        lines = [
            f"- Starved this year: {st.starved_this_year} citizens | Newcomers: {st.immigrants_this_year} arrived",
            f"- Harvest yield: {st.harvest_yield} bushels/acre across cultivated land",
            f"- Rat infestation: {st.rats_ate} bushels destroyed in silos",
            f"- Current grain in store: {st.bushels} bushels",
            f"- Land is trading at {st.land_price} bushels per acre",
        ]
        if st.plague_struck:
            lines.insert(1, "WARNING: A HORRIBLE PLAGUE STRUCK! Half the people died.")

        curr_y = card_y + 38
        for line in lines:
            col = Palette.CRIMSON_LIGHT if "PLAGUE" in line or "Starved" in line and st.starved_this_year > 0 else Palette.TEXT_BODY
            l_surf = FontManager.small(14).render(line, True, col)
            self.canvas.blit(l_surf, (card_x + 16, curr_y))
            curr_y += 24

        # 4. Interactive Turn Decision Panel (Bottom half: y = 428 to 710)
        panel_rect = pygame.Rect(16, 428, 1248, 282)
        pygame.draw.rect(self.canvas, (32, 26, 20, 235), panel_rect, border_radius=10)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER_LIGHT, panel_rect, width=2, border_radius=10)

        # Title of Decision Panel
        dec_title = FontManager.header(18).render("ROYAL DECREES & RESOURCE ALLOCATION", True, Palette.GOLD_PALE)
        self.canvas.blit(dec_title, (30, 438))

        # Render Number Inputs
        self.input_buy.draw(self.canvas)
        self.input_sell.draw(self.canvas)
        self.input_feed.draw(self.canvas)
        self.input_plant.draw(self.canvas)

        # Action Buttons
        self.btn_execute_turn.draw(self.canvas)
        if self.active_mode == "ENHANCED":
            self.btn_advisors.draw(self.canvas)
            self.btn_chronicle.draw(self.canvas)

    def _draw_game_over(self) -> None:
        self.world.render(self.canvas)

        panel_w, panel_h = 760, 520
        px, py = (BASE_WIDTH - panel_w) // 2, 70
        pygame.draw.rect(self.canvas, (24, 18, 14, 235), (px, py, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT, (px, py, panel_w, panel_h), width=3, border_radius=12)

        if not self.game_over_result:
            return

        res = self.game_over_result
        tier = res["tier"]

        # Banner Title
        if res["state"].game_over_reason == "STEWARD_FIRED":
            title_text = "RULE TERMINATED: STEWARD DISMISSED"
        elif res["state"].year == 11 and not res["state"].game_over_reason:
            title_text = "TEN-YEAR GOVERNANCE EVALUATION"
        else:
            title_text = "RULE TERMINATED: IMPEACHMENT"
        t_surf = FontManager.title(32).render(title_text, True, Palette.GOLD_PALE)
        self.canvas.blit(t_surf, t_surf.get_rect(center=(BASE_WIDTH // 2, py + 45)))

        # Summary Metrics
        st = res["state"]
        if st.game_over_reason == "STEWARD_FIRED":
            m_lines = [
                "Your steward refused your order and abandoned your court.",
                f"Year of abdication: Year {st.year} of 10.",
                f"Final Population: {st.population} citizens  |  Final Land: {st.acres} acres",
                f"Grain remaining in store: {st.bushels} bushels",
            ]
        else:
            m_lines = [
                f"Total Citizens Starved: {res['total_starved']} people died across your reign.",
                f"Average Annual Starvation: {res['avg_starved_pct']:.1f}% per year.",
                f"Final Land Distribution: {res['acres_per_person']:.2f} acres per citizen (Started with 10.00).",
                f"Surviving Population: {st.population} citizens  |  Final Land: {st.acres} acres",
            ]

        curr_y = py + 105
        for line in m_lines:
            lsurf = FontManager.body(18).render(line, True, Palette.TEXT_BODY)
            self.canvas.blit(lsurf, (px + 40, curr_y))
            curr_y += 30

        # Historical Outcome Box
        box_rect = pygame.Rect(px + 40, curr_y + 10, panel_w - 80, 160)
        pygame.draw.rect(self.canvas, (42, 32, 24), box_rect, border_radius=8)
        border_col = Palette.GOLD_BASE if tier == 4 else Palette.CRIMSON_LIGHT if tier == 1 else Palette.PANEL_BORDER
        pygame.draw.rect(self.canvas, border_col, box_rect, width=2, border_radius=8)

        # Historic Text
        h_lines = res["message"].split("\n")
        hy = box_rect.y + 20
        for hl in h_lines:
            h_surf = FontManager.header(18).render(hl, True, Palette.GOLD_PALE if tier == 4 else Palette.TEXT_TITLE)
            self.canvas.blit(h_surf, (box_rect.x + 20, hy))
            hy += 28

        # Persistent Buttons
        self.btn_game_over_replay.draw(self.canvas)
        self.btn_game_over_menu.draw(self.canvas)

    def _draw_scenarios(self) -> None:
        self.world.render(self.canvas)

        header_surf = FontManager.title(36).render("SCENARIO CHALLENGES", True, Palette.GOLD_PALE)
        self.canvas.blit(header_surf, header_surf.get_rect(center=(BASE_WIDTH // 2, 50)))

        self.btn_scenarios_back.draw(self.canvas)

        # 4 Scenario Cards
        card_w, card_h = 270, 520
        start_x = 55
        card_y = 110
        scen_keys = list(SCENARIOS.keys())

        for i, key in enumerate(scen_keys):
            scen = SCENARIOS[key]
            cx = start_x + i * (card_w + 25)
            c_rect = pygame.Rect(cx, card_y, card_w, card_h)

            pygame.draw.rect(self.canvas, (32, 24, 18, 235), c_rect, border_radius=10)
            pygame.draw.rect(self.canvas, Palette.PANEL_BORDER_LIGHT, c_rect, width=2, border_radius=10)

            # Card Header
            title_s = FontManager.header(19).render(scen.title, True, Palette.GOLD_PALE)
            sub_s = FontManager.small(13).render(scen.subtitle, True, Palette.SAND_LIGHT)
            self.canvas.blit(title_s, (cx + 14, card_y + 16))
            self.canvas.blit(sub_s, (cx + 14, card_y + 42))
            pygame.draw.line(self.canvas, Palette.GOLD_BASE, (cx + 14, card_y + 64), (cx + card_w - 14, card_y + 64), 1)

            # Description (word wrapped manually)
            words = scen.description.split()
            desc_lines = []
            cur_line = []
            for w in words:
                cur_line.append(w)
                if len(" ".join(cur_line)) > 26:
                    desc_lines.append(" ".join(cur_line[:-1]))
                    cur_line = [w]
            if cur_line:
                desc_lines.append(" ".join(cur_line))

            dy = card_y + 76
            for dl in desc_lines[:6]:
                d_surf = FontManager.small(13).render(dl, True, Palette.TEXT_BODY)
                self.canvas.blit(d_surf, (cx + 14, dy))
                dy += 20

            # Objectives list
            obj_y = card_y + 220
            pygame.draw.rect(self.canvas, (24, 18, 14), (cx + 12, obj_y, card_w - 24, 180), border_radius=6)
            self.canvas.blit(FontManager.header(15).render("VICTORY GOALS:", True, Palette.GOLD_LIGHT), (cx + 20, obj_y + 10))

            goals = [
                f"- Term: Survive {scen.target_year} Years",
                f"- Start Grain: {scen.starting_bushels} bu",
                f"- Starvation Limit: <{scen.max_avg_starvation_pct:.0f}%",
            ]
            if scen.min_final_bushels > 0:
                goals.append(f"- Final Grain: >={scen.min_final_bushels} bu")
            if scen.min_final_acres > 0:
                goals.append(f"- Final Land: >={scen.min_final_acres} ac")
            if scen.min_final_population > 0:
                goals.append(f"- Final Pop: >={scen.min_final_population}")

            gy = obj_y + 36
            for g in goals:
                self.canvas.blit(FontManager.small(13).render(g, True, Palette.TEXT_MUTED), (cx + 20, gy))
                gy += 22

            # Start Scenario Button (persistent instance)
            if key in self.scenario_play_buttons:
                self.scenario_play_buttons[key].draw(self.canvas)

    def _draw_instructions(self) -> None:
        self.world.render(self.canvas)

        panel_w, panel_h = 920, 580
        px, py = (BASE_WIDTH - panel_w) // 2, 70
        pygame.draw.rect(self.canvas, (26, 20, 16, 240), (px, py, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT, (px, py, panel_w, panel_h), width=3, border_radius=12)

        self.btn_instructions_back.draw(self.canvas)

        tutorial_cards = [
            (
                "TUTORIAL: THE THREE PILLARS OF SUMERIA",
                [
                    "Welcome, ruler. Hammurabi is an ancient resource-management simulation.",
                    "To govern successfully for a 10-year term, you must balance three interconnected resources:",
                    "",
                    "1. CITIZENS (POPULATION): Your workforce. Citizens tend your crops and bring wealth.",
                    "2. ACRES (LAND): Your territorial foundation. Land trades between 17 and 26 bushels/acre.",
                    "3. GRAIN (BUSHELS): Your currency and lifeblood. Used to feed citizens, plant seeds, and trade land.",
                    "",
                    "Every decision you make this year directly impacts your kingdom next year!",
                ]
            ),
            (
                "FEEDING YOUR CITIZENS & FAMINE PREVENTION",
                [
                    "Each living citizen strictly requires 20 BUSHELS OF GRAIN per year to survive.",
                    "",
                    "- If you feed 20 bushels per person: Zero starvation occurs.",
                    "- If you feed LESS than 20 bushels: Citizens will starve to death (Deaths = Pop - Fed).",
                    "- CATASTROPHIC FAMINE: If more than 45% of your population starves in a SINGLE year,",
                    "  the people will violently revolt. You will be impeached and declared NATIONAL FINK!",
                    "",
                    "RULE OF THUMB: Always allocate 20 * Population to food before planting or buying land.",
                ]
            ),
            (
                "SOWING SEED & CROP HARVESTS",
                [
                    "Farming is how you replenish your grain silos every year:",
                    "",
                    "- SEED COST: Sowing 2 acres requires exactly 1 BUSHEL OF GRAIN (Acres // 2).",
                    "- WORKFORCE LIMIT: One citizen can cultivate up to 10 ACRES of land.",
                    "  (Historical quirk: 100 citizens can tend up to 999 acres).",
                    "- HARVEST YIELDS: Mother Nature provides a random yield from 1 to 5 bushels per acre.",
                    "",
                    "A yield of 5 is a bumper harvest! A yield of 1 is a harsh drought.",
                ]
            ),
            (
                "HAZARDS OF ANCIENT MESOPOTAMIA",
                [
                    "Beware the perils that strike ancient rulers without warning:",
                    "",
                    "- RAT INFESTATIONS: Rats have a 40% chance of invading your silos every year.",
                    "  When they strike, they devour between 25% and 50% of your stored grain!",
                    "  Crucial Timing: Rats eat your existing store BEFORE new harvest grain is added.",
                    "",
                    "- THE PLAGUE: A deadly epidemic carries a 20% random probability.",
                    "  When plague strikes, half of your living citizens instantly perish.",
                ]
            ),
            (
                "ACHIEVING THE GOLDEN AGE (EVALUATION TIERS)",
                [
                    "At the end of your 10-year term, your full record is judged by Hammurabi:",
                    "",
                    "- TIER 4 (FANTASTIC): Starvation <= 3% AND Land >= 10 acres per citizen.",
                    "  \"Charlemagne, Disraeli, and Jefferson combined could not have done better!\"",
                    "- TIER 3 (MEDIOCRE): Starvation <= 10% AND Land >= 9 acres per citizen.",
                    "- TIER 2 (TYRANT): Smacks of Nero and Ivan IV. The people frankly hate your guts!",
                    "- TIER 1 (FINK): Starvation > 33% OR Land < 7 acres/person. Impeached and thrown out!",
                ]
            ),
        ]

        card_title, card_lines = tutorial_cards[self.tutorial_step]

        # Step indicator
        step_str = f"STEP {self.tutorial_step + 1} OF 5"
        self.canvas.blit(FontManager.header(16).render(step_str, True, Palette.GOLD_LIGHT), (px + panel_w - 160, py + 26))

        # Card Title
        self.canvas.blit(FontManager.header(24).render(card_title, True, Palette.GOLD_PALE), (px + 60, py + 80))
        pygame.draw.line(self.canvas, Palette.GOLD_BASE, (px + 60, py + 115), (px + panel_w - 60, py + 115), 2)

        # Card Text
        cy = py + 140
        for cl in card_lines:
            col = Palette.GOLD_LIGHT if "TIER 4" in cl or "RULE OF THUMB" in cl else Palette.CRIMSON_LIGHT if "CATASTROPHIC" in cl or "PLAGUE" in cl else Palette.TEXT_BODY
            self.canvas.blit(FontManager.body(18).render(cl, True, col), (px + 60, cy))
            cy += 32

        # Step navigation buttons with visual disabled state
        self.btn_tutorial_prev.is_enabled = (self.tutorial_step > 0)
        self.btn_tutorial_next.is_enabled = (self.tutorial_step < 4)
        self.btn_tutorial_prev.draw(self.canvas)
        self.btn_tutorial_next.draw(self.canvas)

    # -----------------------------------------------------------------------
    # Main Game Loop
    # -----------------------------------------------------------------------

    def run(self) -> None:
        """Runs the 60 FPS event and rendering loop."""
        while self.is_running:
            dt = self.clock.tick(60) / 1000.0
            # Cap delta time to prevent physics jump on window drag
            dt = min(dt, 0.1) * self.animation_speed

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.active_modal:
                        self.active_modal = None
                    elif self.current_screen == "GAMEPLAY":
                        self._open_pause_modal()
                    elif self.current_screen != "MAIN_MENU":
                        self._return_to_main_menu()
                else:
                    self.handle_event(event)

            self.update(dt)
            self.draw()

        pygame.quit()


def main() -> None:
    """CLI launcher for the graphical desktop application."""
    start_fullscreen = "--fullscreen" in sys.argv
    app = GameApp(start_fullscreen=start_fullscreen)
    app.run()


if __name__ == "__main__":
    main()
