"""
games/oregon_trail/app.py - Graphical desktop application for The Oregon Trail (1848 Pioneer Simulation).

Features an animated prairie landscape with rolling covered wagon and draught oxen,
interactive trail progress map, health gauges, inventory provisions, river crossing decisions,
general store provisioning with distance inflation, hunting mechanics, random incident modals,
and seamless RetroRevive platform library integration.
"""

import datetime
import math
import random
import sys
import time
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from ui_theme import CRTEffect, FontManager, Palette, SoundSynthesizer, UIButton, UIModal
from .engine import (
    BASE_PRICES,
    LANDMARKS,
    Inventory,
    Landmark,
    LandmarkType,
    Pace,
    PartyMember,
    Profession,
    Rations,
    TrailEvent,
    TrailState,
    Weather,
    buy_supplies,
    calculate_score,
    cross_river,
    get_item_price,
    hunt_cycle,
    init_game,
    rest_cycle,
    step_turn,
)

BASE_WIDTH = 1280
BASE_HEIGHT = 720


class WeatherParticle:
    """Atmospheric particle: falling rain drop or drifting snowflake."""

    def __init__(self, bounds: pygame.Rect, p_type: str = "rain") -> None:
        self.bounds = bounds
        self.p_type = p_type
        self.x = random.uniform(bounds.left, bounds.right)
        self.y = random.uniform(bounds.top, bounds.bottom)
        if p_type == "rain":
            self.vx = -random.uniform(40, 70)
            self.vy = random.uniform(180, 260)
            self.length = random.uniform(6, 12)
        else:
            self.vx = -random.uniform(20, 50)
            self.vy = random.uniform(30, 60)
            self.radius = random.uniform(1.5, 3.0)

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y > self.bounds.bottom:
            self.y = self.bounds.top
            self.x = random.uniform(self.bounds.left, self.bounds.right)
        elif self.x < self.bounds.left:
            self.x = self.bounds.right
            self.y = random.uniform(self.bounds.top, self.bounds.bottom)

    def draw(self, surface: pygame.Surface) -> None:
        if self.p_type == "rain":
            ex = self.x + (self.vx / 30.0) * self.length
            ey = self.y + (self.vy / 30.0) * self.length
            pygame.draw.line(surface, (170, 200, 240), (int(self.x), int(self.y)), (int(ex), int(ey)), 1)
        else:
            pygame.draw.circle(surface, (240, 245, 255), (int(self.x), int(self.y)), int(self.radius))


class CloudParticle:
    """Drifting prairie cloud across the panoramic sky."""

    def __init__(self, x: float, y: float, speed: float, scale: float) -> None:
        self.x = x
        self.y = y
        self.speed = speed
        self.scale = scale

    def update(self, dt: float) -> None:
        self.x += self.speed * dt
        if self.x > BASE_WIDTH + 150:
            self.x = -150.0
            self.y = random.uniform(20.0, 110.0)

    def draw(self, surface: pygame.Surface) -> None:
        col = (245, 248, 252, 190)
        surf = pygame.Surface((int(140 * self.scale), int(50 * self.scale)), pygame.SRCALPHA)
        w, h = surf.get_size()
        pygame.draw.ellipse(surf, col, (0, int(h * 0.25), int(w * 0.6), int(h * 0.7)))
        pygame.draw.ellipse(surf, col, (int(w * 0.25), 0, int(w * 0.55), int(h * 0.95)))
        pygame.draw.ellipse(surf, col, (int(w * 0.45), int(h * 0.2), int(w * 0.55), int(h * 0.75)))
        surface.blit(surf, (int(self.x), int(self.y)))


class OregonApp:
    """Pygame desktop application for The Oregon Trail (1848)."""

    def __init__(
        self,
        start_fullscreen: bool = False,
        on_exit_to_library: Optional[Callable[[], None]] = None,
        shared_window: Optional[pygame.Surface] = None,
    ) -> None:
        pygame.init()
        SoundSynthesizer.init()

        self.on_exit_to_library = on_exit_to_library
        self.screen_width = BASE_WIDTH
        self.screen_height = BASE_HEIGHT

        if shared_window is not None:
            self.window = shared_window
        else:
            flags = pygame.RESIZABLE
            if start_fullscreen:
                flags |= pygame.FULLSCREEN
            self.window = pygame.display.set_mode((self.screen_width, self.screen_height), flags)

        pygame.display.set_caption("RetroRevive: The Oregon Trail (1848)")
        self.canvas = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        self.clock = pygame.time.Clock()
        self.is_running = True

        # Trail Simulation State
        self.state: TrailState = init_game(profession="CARPENTER")

        # Visual & Animation variables
        self.wheel_angle: float = 0.0
        self.ox_step_phase: float = 0.0
        self.wagon_bob: float = 0.0
        self.travel_anim_timer: float = 0.0
        self.is_traveling_anim: bool = False

        self.clouds: List[CloudParticle] = []
        self._init_clouds()
        self.weather_particles: List[WeatherParticle] = []
        self.weather_type: str = ""

        # UI Modals & State
        self.show_rules_modal: bool = False
        self.show_log_modal: bool = False
        self.show_store_modal: bool = False
        self.show_river_modal: bool = False
        self.show_event_modal: bool = False
        self.show_hunt_modal: bool = False
        self.hunt_modal_text: str = ""

        # Store Cart amounts
        self.store_cart: Dict[str, int] = {
            "oxen": 0,
            "food": 0,
            "clothing": 0,
            "ammunition": 0,
            "wagon_wheel": 0,
            "wagon_axle": 0,
            "wagon_tongue": 0,
            "medical_kit": 0,
        }

        # Toast notification
        self.toast_message: Optional[str] = None
        self.toast_timer: float = 0.0

        # UI Controls Initialization
        self._init_buttons()

    def _init_clouds(self) -> None:
        self.clouds.clear()
        for i in range(5):
            x = (i * 280) + random.randint(0, 100)
            y = random.uniform(30.0, 120.0)
            spd = random.uniform(12.0, 22.0)
            scl = random.uniform(0.8, 1.25)
            self.clouds.append(CloudParticle(x, y, spd, scl))

    def _init_buttons(self) -> None:
        # Header navigation buttons
        self.btn_back = UIButton((25, 12, 140, 36), "← LIBRARY", self._on_back_clicked, color_scheme="sand", font_size=13)
        self.btn_rules = UIButton((175, 12, 135, 36), "TRAIL GUIDE", self._toggle_rules, color_scheme="lapis", font_size=13)
        self.btn_restart = UIButton((BASE_WIDTH - 170, 12, 145, 36), "RESTART TRAIL", self._restart_trail, color_scheme="crimson", font_size=13)

        # Primary Command Deck Buttons (Bottom Row, y=650)
        by = 650
        self.btn_continue = UIButton((25, by, 250, 48), "CONTINUE ON TRAIL [SPACE]", self._action_continue, primary=True, font_size=14)
        self.btn_rest = UIButton((285, by, 150, 48), "REST (3 DAYS) [T]", self._action_rest, color_scheme="sand", font_size=13)
        self.btn_hunt = UIButton((445, by, 140, 48), "HUNT GAME [H]", self._action_hunt, color_scheme="sand", font_size=13)
        self.btn_pace = UIButton((595, by, 175, 48), f"PACE: {self.state.pace.value}", self._cycle_pace, color_scheme="lapis", font_size=13)
        self.btn_rations = UIButton((780, by, 185, 48), f"RATIONS: {self.state.rations.value}", self._cycle_rations, color_scheme="lapis", font_size=13)
        self.btn_store = UIButton((975, by, 140, 48), "VISIT STORE [S]", self._open_store, color_scheme="gold", font_size=13)
        self.btn_log = UIButton((1125, by, 130, 48), "TRAIL LOG [L]", self._toggle_log, color_scheme="sand", font_size=13)

        # Rules Modal Close Button
        self.btn_rules_close = UIButton((BASE_WIDTH // 2 - 80, 600, 160, 40), "CLOSE GUIDE", self._toggle_rules, color_scheme="gold")

        # Log Modal Close Button
        self.btn_log_close = UIButton((BASE_WIDTH // 2 - 80, 600, 160, 40), "CLOSE LOG", self._toggle_log, color_scheme="sand")

        # River Crossing Action Buttons
        rw = 180
        ry = 450
        self.btn_river_ford = UIButton((BASE_WIDTH // 2 - 290, ry, rw, 44), "FORD RIVER (FREE)", lambda: self._resolve_river("FORD"), primary=True, font_size=13)
        self.btn_river_caulk = UIButton((BASE_WIDTH // 2 - 90, ry, rw, 44), "CAULK & FLOAT", lambda: self._resolve_river("CAULK"), color_scheme="lapis", font_size=13)
        self.btn_river_ferry = UIButton((BASE_WIDTH // 2 + 110, ry, rw, 44), "TAKE FERRY ($5.00)", lambda: self._resolve_river("FERRY"), color_scheme="gold", font_size=13)

        # Store Modal Buttons
        self.btn_store_buy = UIButton((BASE_WIDTH // 2 - 180, 560, 170, 42), "CONFIRM PURCHASE", self._execute_store_purchase, primary=True, font_size=13)
        self.btn_store_close = UIButton((BASE_WIDTH // 2 + 10, 560, 170, 42), "LEAVE STORE", self._close_store, color_scheme="sand", font_size=13)

        # Event & Hunt dismiss buttons
        self.btn_event_dismiss = UIButton((BASE_WIDTH // 2 - 80, 470, 160, 42), "CONTINUE", self._dismiss_event, primary=True, font_size=14)
        self.btn_hunt_dismiss = UIButton((BASE_WIDTH // 2 - 80, 470, 160, 42), "CONTINUE", self._dismiss_hunt, primary=True, font_size=14)

        # Outcome Modal Buttons (Game Over / Victory)
        self.btn_outcome_restart = UIButton((BASE_WIDTH // 2 - 190, 520, 180, 46), "PLAY AGAIN", self._restart_trail, primary=True)
        self.btn_outcome_library = UIButton((BASE_WIDTH // 2 + 10, 520, 180, 46), "BACK TO LIBRARY", self._on_back_clicked, color_scheme="sand")

    def _on_back_clicked(self) -> None:
        if self.on_exit_to_library:
            self.on_exit_to_library()
        else:
            self.is_running = False

    def _toggle_rules(self) -> None:
        self.show_rules_modal = not self.show_rules_modal
        SoundSynthesizer.play("click")

    def _toggle_log(self) -> None:
        self.show_log_modal = not self.show_log_modal
        SoundSynthesizer.play("click")

    def _restart_trail(self) -> None:
        self.state = init_game(profession="CARPENTER")
        self.wheel_angle = 0.0
        self.ox_step_phase = 0.0
        self.show_river_modal = False
        self.show_store_modal = False
        self.show_event_modal = False
        self.show_hunt_modal = False
        self._update_button_labels()
        SoundSynthesizer.play("fanfare")
        self.show_toast("New journey commenced at Independence, Missouri!")

    def show_toast(self, msg: str) -> None:
        self.toast_message = msg
        self.toast_timer = 2.8

    def _update_button_labels(self) -> None:
        self.btn_pace.text = f"PACE: {self.state.pace.value}"
        self.btn_rations.text = f"RATIONS: {self.state.rations.value}"

    def _cycle_pace(self) -> None:
        paces = [Pace.STEADY, Pace.STRENUOUS, Pace.GRUELING]
        idx = (paces.index(self.state.pace) + 1) % len(paces)
        self.state.pace = paces[idx]
        self._update_button_labels()
        SoundSynthesizer.play("click")
        self.show_toast(f"Pace adjusted to {self.state.pace.value} (~{int(self.state.pace.daily_miles)} mi/day)")

    def _cycle_rations(self) -> None:
        rations_list = [Rations.FILLING, Rations.MEAGER, Rations.BARE_BONES]
        idx = (rations_list.index(self.state.rations) + 1) % len(rations_list)
        self.state.rations = rations_list[idx]
        self._update_button_labels()
        SoundSynthesizer.play("click")
        self.show_toast(f"Food rations set to {self.state.rations.value} ({self.state.rations.daily_lbs} lbs/person/day)")

    def _action_continue(self) -> None:
        if self.state.is_game_over:
            return
        if self.state.pending_river:
            self.show_river_modal = True
            SoundSynthesizer.play("warning")
            return

        self.is_traveling_anim = True
        self.travel_anim_timer = 0.5
        SoundSynthesizer.play("harvest")

        # Step 4 days on trail
        self.state = step_turn(self.state, "TRAVEL", days=4)

        if self.state.pending_river:
            self.show_river_modal = True
            SoundSynthesizer.play("warning")
        elif self.state.active_event:
            self.show_event_modal = True
            SoundSynthesizer.play("pestilence")
        elif self.state.is_game_over:
            if self.state.victory:
                SoundSynthesizer.play("fanfare")
            else:
                SoundSynthesizer.play("warning")

    def _action_rest(self) -> None:
        if self.state.is_game_over:
            return
        SoundSynthesizer.play("click")
        self.state = rest_cycle(self.state, days=3)
        self.show_event_modal = True

    def _action_hunt(self) -> None:
        if self.state.is_game_over:
            return
        if self.state.inventory.ammunition < 10:
            SoundSynthesizer.play("warning")
            self.show_toast("Need at least 10 rounds of ammunition to hunt!")
            return

        SoundSynthesizer.play("harvest")
        self.state, gained, msg = hunt_cycle(self.state)
        self.hunt_modal_text = msg
        self.show_hunt_modal = True

    def _open_store(self) -> None:
        curr_lm = self.state.current_landmark
        is_store_avail = self.state.at_landmark and curr_lm.has_store
        if not is_store_avail:
            SoundSynthesizer.play("warning")
            self.show_toast("No trading post or fort store at this location!")
            return

        # Reset cart
        for k in self.store_cart:
            self.store_cart[k] = 0
        self.show_store_modal = True
        SoundSynthesizer.play("click")

    def _close_store(self) -> None:
        self.show_store_modal = False
        SoundSynthesizer.play("click")

    def _execute_store_purchase(self) -> None:
        # Calculate total
        total = 0.0
        for item, qty in self.store_cart.items():
            if qty > 0:
                price = get_item_price(item, self.state.miles_traveled)
                total += price * qty

        if total > self.state.inventory.cash:
            SoundSynthesizer.play("warning")
            self.show_toast(f"Insufficient cash! Total ${total:.2f} exceeds balance ${self.state.inventory.cash:.2f}")
            return

        # Execute purchase
        for item, qty in self.store_cart.items():
            if qty > 0:
                self.state, ok, _ = buy_supplies(self.state, item, qty)

        SoundSynthesizer.play("fanfare")
        self.show_toast(f"Purchased provisions for ${total:.2f}!")
        self.show_store_modal = False

    def _resolve_river(self, choice: str) -> None:
        self.state, ok, msg = cross_river(self.state, choice=choice)
        self.show_river_modal = False
        if ok:
            SoundSynthesizer.play("fanfare")
            self.show_toast(f"River crossed successfully! {msg}")
        else:
            SoundSynthesizer.play("warning")
            self.show_toast(f"River crossing mishap: {msg}")

    def _dismiss_event(self) -> None:
        self.show_event_modal = False
        SoundSynthesizer.play("click")

    def _dismiss_hunt(self) -> None:
        self.show_hunt_modal = False
        SoundSynthesizer.play("click")

    def handle_event(self, event: pygame.event.Event) -> None:
        canvas_mouse = self._screen_to_canvas(pygame.mouse.get_pos())

        if event.type == pygame.QUIT:
            self.is_running = False
            return

        if event.type == pygame.VIDEORESIZE:
            self.screen_width = event.w
            self.screen_height = event.h
            self.window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            return

        # Modal Priority Handling
        if self.show_rules_modal:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.show_rules_modal = False
                return
            self.btn_rules_close.handle_event(event, canvas_mouse)
            return

        if self.show_log_modal:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.show_log_modal = False
                return
            self.btn_log_close.handle_event(event, canvas_mouse)
            return

        if self.show_event_modal:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self._dismiss_event()
                return
            self.btn_event_dismiss.handle_event(event, canvas_mouse)
            return

        if self.show_hunt_modal:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self._dismiss_hunt()
                return
            self.btn_hunt_dismiss.handle_event(event, canvas_mouse)
            return

        if self.show_river_modal:
            if self.btn_river_ford.handle_event(event, canvas_mouse):
                return
            if self.btn_river_caulk.handle_event(event, canvas_mouse):
                return
            if self.btn_river_ferry.handle_event(event, canvas_mouse):
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self._resolve_river("FORD")
                elif event.key == pygame.K_2:
                    self._resolve_river("CAULK")
                elif event.key == pygame.K_3:
                    self._resolve_river("FERRY")
            return

        if self.show_store_modal:
            self._handle_store_events(event, canvas_mouse)
            return

        # Outcome Modal (Game Over / Victory)
        if self.state.is_game_over:
            if self.btn_outcome_restart.handle_event(event, canvas_mouse):
                return
            if self.btn_outcome_library.handle_event(event, canvas_mouse):
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                    self._restart_trail()
                elif event.key == pygame.K_ESCAPE:
                    self._on_back_clicked()
            return

        # Header Buttons
        if self.btn_back.handle_event(event, canvas_mouse):
            return
        if self.btn_rules.handle_event(event, canvas_mouse):
            return
        if self.btn_restart.handle_event(event, canvas_mouse):
            return

        # Bottom Command Buttons
        if self.btn_continue.handle_event(event, canvas_mouse):
            return
        if self.btn_rest.handle_event(event, canvas_mouse):
            return
        if self.btn_hunt.handle_event(event, canvas_mouse):
            return
        if self.btn_pace.handle_event(event, canvas_mouse):
            return
        if self.btn_rations.handle_event(event, canvas_mouse):
            return
        if self.btn_store.handle_event(event, canvas_mouse):
            return
        if self.btn_log.handle_event(event, canvas_mouse):
            return

        # Keyboard hotkeys
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2:
                CRTEffect.toggle()
                return
            elif event.key == pygame.K_F3:
                SoundSynthesizer.set_enabled(not SoundSynthesizer._enabled)
                return
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._action_continue()
            elif event.key == pygame.K_t:
                self._action_rest()
            elif event.key == pygame.K_h:
                self._action_hunt()
            elif event.key == pygame.K_p:
                self._cycle_pace()
            elif event.key == pygame.K_r:
                self._cycle_rations()
            elif event.key == pygame.K_s:
                self._open_store()
            elif event.key == pygame.K_l:
                self._toggle_log()
            elif event.key in (pygame.K_F1, pygame.K_m):
                self._toggle_rules()
            elif event.key == pygame.K_ESCAPE:
                self._on_back_clicked()

    def _handle_store_events(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]) -> None:
        if self.btn_store_buy.handle_event(event, mouse_pos):
            return
        if self.btn_store_close.handle_event(event, mouse_pos):
            return

        # Check clicks on + and - stepper buttons inside store
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            items = list(self.store_cart.keys())
            start_y = 195
            for i, item in enumerate(items):
                row_y = start_y + i * 42
                minus_rect = pygame.Rect(BASE_WIDTH // 2 + 100, row_y + 4, 30, 28)
                plus_rect = pygame.Rect(BASE_WIDTH // 2 + 200, row_y + 4, 30, 28)

                step = 10 if item in ("food", "ammunition") else 1
                if minus_rect.collidepoint(mouse_pos):
                    self.store_cart[item] = max(0, self.store_cart[item] - step)
                    SoundSynthesizer.play("click")
                    return
                elif plus_rect.collidepoint(mouse_pos):
                    self.store_cart[item] += step
                    SoundSynthesizer.play("click")
                    return

    def update(self, dt: float) -> None:
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast_message = None

        # Update clouds
        for c in self.clouds:
            c.update(dt)

        # Weather precipitation particles sync
        w = self.state.weather
        view_rect = pygame.Rect(25, 68, 830, 240)
        if w == Weather.RAINY:
            if self.weather_type != "rain":
                self.weather_type = "rain"
                self.weather_particles = [WeatherParticle(view_rect, "rain") for _ in range(45)]
        elif w in (Weather.BLIZZARD, Weather.COLD, Weather.VERY_COLD):
            if self.weather_type != "snow":
                self.weather_type = "snow"
                self.weather_particles = [WeatherParticle(view_rect, "snow") for _ in range(35)]
        else:
            if self.weather_type != "":
                self.weather_type = ""
                self.weather_particles.clear()

        for p in self.weather_particles:
            p.update(dt)

        # Wagon and oxen animation
        if self.is_traveling_anim:
            self.travel_anim_timer -= dt
            spd = 14.0
            self.wheel_angle += dt * spd * 180.0
            self.ox_step_phase += dt * spd * 3.0
            self.wagon_bob = math.sin(self.wheel_angle * 0.05) * 2.0
            if self.travel_anim_timer <= 0:
                self.is_traveling_anim = False
        else:
            # Idle breathing bob
            self.wagon_bob = math.sin(time.time() * 2.5) * 1.0

    def draw(self) -> None:
        # Background Canvas
        self.canvas.fill(Palette.BG_DARK)

        # 1. Header Bar
        self._draw_header()

        # 2. Panoramic Prairie Scene (Wagon, Oxen, Landscape, Landmarks Track)
        self._draw_prairie_viewport()

        # 3. Trail Status Card (Weather, Health, Distance, Pace)
        self._draw_status_card()

        # 4. Party Members Ledger
        self._draw_party_ledger()

        # 5. Inventory Provisions Grid
        self._draw_inventory_panel()

        # 6. Command Deck Buttons
        self._draw_command_deck()

        # 7. Modals (Overlays)
        if self.show_rules_modal:
            self._draw_rules_modal()
        elif self.show_log_modal:
            self._draw_log_modal()
        elif self.show_river_modal:
            self._draw_river_modal()
        elif self.show_store_modal:
            self._draw_store_modal()
        elif self.show_event_modal:
            self._draw_event_modal()
        elif self.show_hunt_modal:
            self._draw_hunt_modal()
        elif self.state.is_game_over:
            self._draw_outcome_modal()

        # 8. Toast notification
        self._draw_toast()

    def _draw_header(self) -> None:
        header_rect = pygame.Rect(0, 0, BASE_WIDTH, 56)
        pygame.draw.rect(self.canvas, Palette.PANEL_BG, header_rect)
        pygame.draw.line(self.canvas, Palette.PANEL_BORDER, (0, 56), (BASE_WIDTH, 56), 2)

        # Title
        title_font = FontManager.title(22)
        title_surf = title_font.render("THE OREGON TRAIL", True, Palette.GOLD_LIGHT)
        self.canvas.blit(title_surf, (BASE_WIDTH // 2 - title_surf.get_width() // 2, 8))

        # Date & Year
        date_str = self.state.current_date.strftime("%B %d, %Y")
        sub_font = FontManager.small(13)
        sub_surf = sub_font.render(f"PIONEER SIMULATION  •  {date_str.upper()}", True, Palette.SAND_LIGHT)
        self.canvas.blit(sub_surf, (BASE_WIDTH // 2 - sub_surf.get_width() // 2, 33))

        # Header buttons
        self.btn_back.draw(self.canvas)
        self.btn_rules.draw(self.canvas)
        self.btn_restart.draw(self.canvas)

    def _draw_prairie_viewport(self) -> None:
        view_rect = pygame.Rect(25, 68, 830, 240)
        self.canvas.set_clip(view_rect)

        # Prairie sky background
        pygame.draw.rect(self.canvas, (40, 60, 95), view_rect, border_radius=6)

        # Sky gradient
        sky_surf = pygame.Surface((view_rect.width, view_rect.height), pygame.SRCALPHA)
        for y in range(view_rect.height):
            ratio = y / view_rect.height
            r = int(50 + 60 * ratio)
            g = int(80 + 70 * ratio)
            b = int(120 + 40 * ratio)
            pygame.draw.line(sky_surf, (r, g, b, 255), (0, y), (view_rect.width, y))
        self.canvas.blit(sky_surf, (view_rect.x, view_rect.y))

        # Sun
        pygame.draw.circle(self.canvas, (255, 235, 160), (view_rect.right - 90, view_rect.y + 45), 26)
        pygame.draw.circle(self.canvas, (255, 245, 200), (view_rect.right - 90, view_rect.y + 45), 22)

        # Clouds
        for c in self.clouds:
            if view_rect.x <= c.x <= view_rect.right:
                c.draw(self.canvas)

        # Distant Mountain Range (Parallax Peaks)
        mountain_pts = [
            (view_rect.x, view_rect.y + 160),
            (view_rect.x + 90, view_rect.y + 105),
            (view_rect.x + 190, view_rect.y + 145),
            (view_rect.x + 310, view_rect.y + 85),
            (view_rect.x + 420, view_rect.y + 130),
            (view_rect.x + 540, view_rect.y + 90),
            (view_rect.x + 680, view_rect.y + 140),
            (view_rect.x + 770, view_rect.y + 100),
            (view_rect.right, view_rect.y + 155),
            (view_rect.right, view_rect.bottom),
            (view_rect.x, view_rect.bottom),
        ]
        pygame.draw.polygon(self.canvas, (65, 80, 85), mountain_pts)
        # Snowcaps
        pygame.draw.polygon(self.canvas, (230, 240, 250), [
            (view_rect.x + 310, view_rect.y + 85),
            (view_rect.x + 285, view_rect.y + 105),
            (view_rect.x + 335, view_rect.y + 105),
        ])
        pygame.draw.polygon(self.canvas, (230, 240, 250), [
            (view_rect.x + 540, view_rect.y + 90),
            (view_rect.x + 515, view_rect.y + 110),
            (view_rect.x + 565, view_rect.y + 110),
        ])

        # Rolling Green Prairie Foothills
        pygame.draw.ellipse(self.canvas, (80, 120, 60), (view_rect.x - 40, view_rect.y + 140, 500, 100))
        pygame.draw.ellipse(self.canvas, (95, 140, 70), (view_rect.x + 350, view_rect.y + 145, 550, 110))

        # Foreground Prairie Trail Ground
        ground_rect = pygame.Rect(view_rect.x, view_rect.y + 175, view_rect.width, view_rect.height - 175)
        pygame.draw.rect(self.canvas, (135, 110, 70), ground_rect)
        # Prairie grass border
        pygame.draw.rect(self.canvas, (105, 135, 60), (view_rect.x, view_rect.y + 175, view_rect.width, 10))

        # Trail Ruts
        pygame.draw.line(self.canvas, (110, 88, 55), (view_rect.x, view_rect.y + 198), (view_rect.right, view_rect.y + 198), 2)
        pygame.draw.line(self.canvas, (110, 88, 55), (view_rect.x, view_rect.y + 206), (view_rect.right, view_rect.y + 206), 2)

        # Covered Wagon & Oxen Rendering
        self._draw_wagon_and_oxen(view_rect.x + 170, view_rect.y + 140)

        # Trail Landmark Progress Bar (At bottom of prairie viewport)
        self._draw_trail_progress_bar(view_rect)

        # Atmospheric weather precipitation overlay
        for p in self.weather_particles:
            p.draw(self.canvas)

        # Heat shimmer for hot weather
        if self.state.weather in (Weather.HOT, Weather.WARM):
            heat_overlay = pygame.Surface((view_rect.width, 60), pygame.SRCALPHA)
            heat_overlay.fill((255, 200, 80, 25))
            self.canvas.blit(heat_overlay, (view_rect.x, view_rect.y + 120))

        # Reset clipping
        self.canvas.set_clip(None)

        # Border
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, view_rect, width=2, border_radius=6)

    def _draw_wagon_and_oxen(self, base_x: int, base_y: int) -> None:
        """Renders authentic covered prairie schooner with spoked wheels and draught oxen."""
        wy = base_y + int(self.wagon_bob)

        # 1. Draught Oxen (Walking ahead of wagon)
        ox_x = base_x + 155
        ox_y = wy + 26
        self._draw_ox(ox_x, ox_y, phase=self.ox_step_phase)
        self._draw_ox(ox_x + 75, ox_y, phase=self.ox_step_phase + math.pi)

        # Oxen Yoke Hitch Beam
        pygame.draw.line(self.canvas, (80, 50, 30), (base_x + 105, wy + 42), (ox_x + 105, ox_y + 15), 3)

        # 2. Covered Wagon Box
        body_rect = pygame.Rect(base_x + 10, wy + 26, 95, 20)
        pygame.draw.rect(self.canvas, (120, 80, 45), body_rect, border_radius=3)
        pygame.draw.rect(self.canvas, (85, 55, 30), body_rect, width=2, border_radius=3)

        # Tool chest / water barrel at side
        pygame.draw.rect(self.canvas, (90, 60, 35), (base_x + 35, wy + 29, 16, 14), border_radius=2)
        pygame.draw.line(self.canvas, (180, 160, 120), (base_x + 35, wy + 33), (base_x + 51, wy + 33), 1)

        # 3. Canvas Bonnet (White curved cover)
        bonnet_pts = [
            (base_x + 8, wy + 26),
            (base_x + 14, wy + 2),
            (base_x + 40, wy - 10),
            (base_x + 75, wy - 10),
            (base_x + 102, wy + 2),
            (base_x + 108, wy + 26),
        ]
        pygame.draw.polygon(self.canvas, (245, 240, 225), bonnet_pts)
        pygame.draw.lines(self.canvas, (190, 180, 160), False, bonnet_pts, 2)
        # Arch ribs on canvas
        pygame.draw.line(self.canvas, (200, 190, 170), (base_x + 40, wy - 10), (base_x + 38, wy + 26), 2)
        pygame.draw.line(self.canvas, (200, 190, 170), (base_x + 75, wy - 10), (base_x + 76, wy + 26), 2)

        # 4. Wooden Spoked Wheels (Front smaller, Rear larger)
        rear_hub = (base_x + 28, wy + 48)
        front_hub = (base_x + 90, wy + 50)
        self._draw_spoked_wheel(rear_hub[0], rear_hub[1], radius=18, angle=self.wheel_angle)
        self._draw_spoked_wheel(front_hub[0], front_hub[1], radius=15, angle=self.wheel_angle * 1.2)

    def _draw_spoked_wheel(self, cx: int, cy: int, radius: int, angle: float) -> None:
        # Wooden rim and iron tire
        pygame.draw.circle(self.canvas, (65, 55, 45), (cx, cy), radius, 3)
        pygame.draw.circle(self.canvas, (140, 95, 50), (cx, cy), radius - 2, 2)
        # Center hub
        pygame.draw.circle(self.canvas, (75, 50, 25), (cx, cy), 4)

        # 6 spokes
        for i in range(6):
            spoke_ang = math.radians(angle + i * 60)
            ex = cx + int(math.cos(spoke_ang) * (radius - 2))
            ey = cy + int(math.sin(spoke_ang) * (radius - 2))
            pygame.draw.line(self.canvas, (160, 115, 65), (cx, cy), (ex, ey), 2)

    def _draw_ox(self, ox: int, oy: int, phase: float) -> None:
        leg_swing = math.sin(phase) * 6.0

        # Body
        body_rect = pygame.Rect(ox + 8, oy + 5, 48, 22)
        pygame.draw.ellipse(self.canvas, (105, 70, 45), body_rect)

        # Head & Horns
        pygame.draw.circle(self.canvas, (95, 60, 35), (ox + 58, oy + 12), 11)
        pygame.draw.line(self.canvas, (240, 235, 215), (ox + 57, oy + 5), (ox + 63, oy - 3), 3)  # Right horn
        pygame.draw.line(self.canvas, (240, 235, 215), (ox + 53, oy + 5), (ox + 48, oy - 2), 2)  # Left horn

        # Muzzle
        pygame.draw.circle(self.canvas, (65, 40, 20), (ox + 66, oy + 15), 5)

        # 4 Legs with walk cycle
        pygame.draw.line(self.canvas, (80, 50, 30), (ox + 16, oy + 24), (ox + 16 + int(leg_swing), oy + 38), 3)
        pygame.draw.line(self.canvas, (80, 50, 30), (ox + 25, oy + 24), (ox + 25 - int(leg_swing), oy + 38), 3)
        pygame.draw.line(self.canvas, (80, 50, 30), (ox + 42, oy + 24), (ox + 42 - int(leg_swing), oy + 38), 3)
        pygame.draw.line(self.canvas, (80, 50, 30), (ox + 49, oy + 24), (ox + 49 + int(leg_swing), oy + 38), 3)

    def _draw_trail_progress_bar(self, view_rect: pygame.Rect) -> None:
        """Renders 2040-mile trail progression bar with landmark markers."""
        bar_y = view_rect.bottom - 24
        bar_x = view_rect.x + 20
        bar_w = view_rect.width - 40
        bar_h = 8

        # Track line
        track_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(self.canvas, (45, 35, 25), track_rect, border_radius=4)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, track_rect, width=1, border_radius=4)

        # Filled progress
        progress_ratio = max(0.0, min(1.0, self.state.miles_traveled / self.state.total_trail_miles))
        fill_w = int(bar_w * progress_ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
            pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT, fill_rect, border_radius=4)

        # Landmark tick marks
        for lm in LANDMARKS:
            lm_ratio = lm.distance_miles / self.state.total_trail_miles
            tick_x = bar_x + int(bar_w * lm_ratio)
            col = Palette.AMBER_WARN if lm.landmark_type == LandmarkType.RIVER else Palette.SAND_LIGHT
            pygame.draw.line(self.canvas, col, (tick_x, bar_y - 2), (tick_x, bar_y + bar_h + 2), 2)

        # Wagon Position Marker
        marker_x = bar_x + fill_w
        pygame.draw.polygon(self.canvas, Palette.GOLD_PALE, [
            (marker_x, bar_y - 6),
            (marker_x - 6, bar_y - 14),
            (marker_x + 6, bar_y - 14),
        ])

        # Current landmark indicator text with protective dark HUD plate
        curr_name = self.state.current_landmark.name
        nxt = self.state.next_landmark
        dist_str = f"Next: {nxt.name} ({int(self.state.distance_to_next_landmark)} mi)" if nxt else "Willamette Valley (Goal Reached!)"
        lbl_surf = FontManager.micro(11).render(f"LOCATION: {curr_name.upper()}  •  {dist_str}", True, Palette.GOLD_LIGHT)
        bg_pad = 6
        plate_rect = pygame.Rect(bar_x - bg_pad, bar_y - 20, lbl_surf.get_width() + bg_pad * 2, lbl_surf.get_height() + 2)
        plate_surf = pygame.Surface((plate_rect.width, plate_rect.height), pygame.SRCALPHA)
        plate_surf.fill((20, 16, 12, 215))
        self.canvas.blit(plate_surf, (plate_rect.x, plate_rect.y))
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, plate_rect, width=1, border_radius=4)
        self.canvas.blit(lbl_surf, (bar_x, bar_y - 19))

    def _draw_status_card(self) -> None:
        """Top right card displaying vital journey conditions."""
        card_rect = pygame.Rect(875, 68, 380, 240)
        pygame.draw.rect(self.canvas, Palette.PANEL_BG, card_rect, border_radius=6)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, card_rect, width=2, border_radius=6)

        # Card Header
        pygame.draw.rect(self.canvas, Palette.PANEL_BG_LIGHT, (card_rect.x, card_rect.y, card_rect.width, 36), border_top_left_radius=6, border_top_right_radius=6)
        hdr_txt = FontManager.header(14).render("JOURNEY TELEMETRY", True, Palette.GOLD_LIGHT)
        self.canvas.blit(hdr_txt, (card_rect.x + 14, card_rect.y + 9))

        # Status Rows
        rows = [
            ("Distance Traveled", f"{int(self.state.miles_traveled):,} / {int(self.state.total_trail_miles):,} miles", Palette.TEXT_TITLE),
            ("Wagon Pace", f"{self.state.pace.value} (~{int(self.state.pace.daily_miles)} mi/day)", Palette.SAND_LIGHT),
            ("Food Rations", f"{self.state.rations.value} ({self.state.rations.daily_lbs} lbs/day)", Palette.SAND_LIGHT),
            ("Weather Condition", self.state.weather.value, self._get_weather_color()),
            ("Party Overall Health", self.state.overall_health_status.upper(), self._get_health_color()),
            ("Profession & Bonus", f"{self.state.profession.value} ({self.state.profession.score_multiplier:.1f}x Score)", Palette.GOLD_PALE),
        ]

        curr_y = card_rect.y + 46
        for lbl, val, val_col in rows:
            lbl_surf = FontManager.small(13).render(lbl, True, Palette.TEXT_MUTED)
            val_surf = FontManager.body(13).render(val, True, val_col)
            self.canvas.blit(lbl_surf, (card_rect.x + 16, curr_y))
            self.canvas.blit(val_surf, (card_rect.right - val_surf.get_width() - 16, curr_y))
            curr_y += 31

    def _get_weather_color(self) -> Tuple[int, int, int]:
        w = self.state.weather
        if w in (Weather.FAIR, Weather.WARM):
            return Palette.SUCCESS_GREEN
        elif w in (Weather.RAINY, Weather.COOL, Weather.COLD):
            return Palette.AMBER_WARN
        return Palette.CRIMSON_LIGHT

    def _get_health_color(self) -> Tuple[int, int, int]:
        st = self.state.overall_health_status
        if st == "Good":
            return Palette.SUCCESS_GREEN
        elif st == "Fair":
            return Palette.GOLD_LIGHT
        elif st == "Poor":
            return Palette.AMBER_WARN
        return Palette.CRIMSON_LIGHT

    def _draw_party_ledger(self) -> None:
        """Renders status and health bars of wagon pioneer companions."""
        pnl_rect = pygame.Rect(25, 320, 595, 315)
        pygame.draw.rect(self.canvas, Palette.PANEL_BG, pnl_rect, border_radius=6)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, pnl_rect, width=2, border_radius=6)

        # Header
        pygame.draw.rect(self.canvas, Palette.PANEL_BG_LIGHT, (pnl_rect.x, pnl_rect.y, pnl_rect.width, 36), border_top_left_radius=6, border_top_right_radius=6)
        hdr_txt = FontManager.header(14).render("WAGON PARTY COMPANIONS", True, Palette.GOLD_LIGHT)
        self.canvas.blit(hdr_txt, (pnl_rect.x + 14, pnl_rect.y + 9))

        curr_y = pnl_rect.y + 48
        for member in self.state.party:
            # Name and role badge
            name_txt = f"{member.name} (LEADER)" if member.is_leader else member.name
            name_col = Palette.GOLD_PALE if member.is_leader else Palette.TEXT_TITLE
            if not member.is_alive:
                name_col = (110, 100, 90)

            n_surf = FontManager.body(14).render(name_txt, True, name_col)
            self.canvas.blit(n_surf, (pnl_rect.x + 16, curr_y))

            # Health Bar (0-100)
            bar_w = 170
            bar_h = 14
            bar_x = pnl_rect.x + 235
            bar_y = curr_y + 3

            bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
            pygame.draw.rect(self.canvas, (35, 28, 22), bg_rect, border_radius=3)

            if member.is_alive:
                fill_w = int(bar_w * (member.health / 100.0))
                hp_col = Palette.SUCCESS_GREEN if member.health >= 65 else (Palette.AMBER_WARN if member.health >= 35 else Palette.CRIMSON)
                if fill_w > 0:
                    pygame.draw.rect(self.canvas, hp_col, (bar_x, bar_y, fill_w, bar_h), border_radius=3)
            pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, bg_rect, width=1, border_radius=3)

            # Health Number
            hp_txt = f"{int(member.health)} HP" if member.is_alive else "DEAD"
            hp_surf = FontManager.small(11).render(hp_txt, True, Palette.TEXT_BODY if member.is_alive else Palette.CRIMSON_LIGHT)
            self.canvas.blit(hp_surf, (bar_x + bar_w + 10, curr_y + 2))

            # Disease / Condition Status Tag
            status_x = pnl_rect.x + 475
            if not member.is_alive:
                tag_surf = FontManager.small(11).render("PERISHED", True, Palette.CRIMSON_LIGHT)
            elif member.diseases:
                tag_surf = FontManager.small(11).render(member.diseases[0].upper(), True, Palette.CRIMSON_LIGHT)
            else:
                tag_surf = FontManager.small(11).render("HEALTHY", True, Palette.SUCCESS_GREEN)
            self.canvas.blit(tag_surf, (status_x, curr_y + 2))

            curr_y += 52

    def _draw_inventory_panel(self) -> None:
        """Renders supplies and provisions deck."""
        pnl_rect = pygame.Rect(635, 320, 620, 315)
        pygame.draw.rect(self.canvas, Palette.PANEL_BG, pnl_rect, border_radius=6)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, pnl_rect, width=2, border_radius=6)

        # Header
        pygame.draw.rect(self.canvas, Palette.PANEL_BG_LIGHT, (pnl_rect.x, pnl_rect.y, pnl_rect.width, 36), border_top_left_radius=6, border_top_right_radius=6)
        hdr_txt = FontManager.header(14).render("WAGON INVENTORY & PROVISIONS", True, Palette.GOLD_LIGHT)
        self.canvas.blit(hdr_txt, (pnl_rect.x + 14, pnl_rect.y + 9))

        inv = self.state.inventory
        supplies = [
            ("Cash Funds", f"${inv.cash:.2f}", Palette.GOLD_LIGHT),
            ("Draught Oxen", f"{inv.oxen} oxen ({inv.oxen // 2} yokes)", Palette.SUCCESS_GREEN if inv.oxen >= 2 else Palette.CRIMSON_LIGHT),
            ("Food Provisions", f"{int(inv.food)} lbs", Palette.SUCCESS_GREEN if inv.food > 100 else Palette.CRIMSON_LIGHT),
            ("Warm Clothing", f"{inv.clothing} sets", Palette.TEXT_TITLE if inv.clothing >= len(self.state.living_members) else Palette.AMBER_WARN),
            ("Ammunition", f"{inv.ammunition} rounds", Palette.TEXT_TITLE if inv.ammunition >= 20 else Palette.AMBER_WARN),
            ("Spare Wagon Wheels", f"{inv.wagon_wheels} wheels", Palette.TEXT_TITLE),
            ("Spare Wagon Axles", f"{inv.wagon_axles} axles", Palette.TEXT_TITLE),
            ("Spare Wagon Tongues", f"{inv.wagon_tongues} tongues", Palette.TEXT_TITLE),
            ("Medical Kits", f"{inv.medical_kits} kits", Palette.SUCCESS_GREEN if inv.medical_kits > 0 else Palette.TEXT_MUTED),
        ]

        curr_y = pnl_rect.y + 48
        # Split into two columns for high legibility
        col1 = supplies[:5]
        col2 = supplies[5:]

        for lbl, val, col in col1:
            lbl_surf = FontManager.small(13).render(lbl, True, Palette.TEXT_MUTED)
            val_surf = FontManager.body(13).render(val, True, col)
            self.canvas.blit(lbl_surf, (pnl_rect.x + 16, curr_y))
            self.canvas.blit(val_surf, (pnl_rect.x + 170, curr_y))
            curr_y += 50

        curr_y = pnl_rect.y + 48
        for lbl, val, col in col2:
            lbl_surf = FontManager.small(13).render(lbl, True, Palette.TEXT_MUTED)
            val_surf = FontManager.body(13).render(val, True, col)
            self.canvas.blit(lbl_surf, (pnl_rect.x + 320, curr_y))
            self.canvas.blit(val_surf, (pnl_rect.x + 490, curr_y))
            curr_y += 50

    def _draw_command_deck(self) -> None:
        """Renders interactive command buttons at bottom of screen."""
        self.btn_continue.draw(self.canvas)
        self.btn_rest.draw(self.canvas)
        self.btn_hunt.draw(self.canvas)
        self.btn_pace.draw(self.canvas)
        self.btn_rations.draw(self.canvas)

        # Highlight store button if at a town/fort
        curr_lm = self.state.current_landmark
        is_store_avail = self.state.at_landmark and curr_lm.has_store
        self.btn_store.is_enabled = is_store_avail
        self.btn_store.draw(self.canvas)

        self.btn_log.draw(self.canvas)

    def _draw_river_modal(self) -> None:
        """River crossing modal when arriving at river milestones."""
        river = self.state.pending_river or self.state.current_landmark
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 10, 8, 205))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 760, 420
        px, py = (BASE_WIDTH - pw) // 2, (BASE_HEIGHT - ph) // 2
        pnl = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, Palette.PANEL_BG, pnl, border_radius=8)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, pnl, width=2, border_radius=8)

        # Header
        title = FontManager.title(20).render(f"RIVER CROSSING: {river.name.upper()}", True, Palette.GOLD_LIGHT)
        self.canvas.blit(title, (pnl.centerx - title.get_width() // 2, py + 24))

        # River telemetry
        depth_val = river.river_depth_ft if river.river_depth_ft is not None else 4.0
        width_val = int(river.distance_miles % 300) + 120
        lines = [
            f"You have arrived at the {river.name}.",
            f"The river is approximately {width_val} feet wide and {depth_val:.1f} feet deep at this crossing.",
            "",
            "Choose your crossing strategy carefully:",
            "1. FORD: Free. Safe if depth is shallow (< 2.5 ft). Deep water risks swamping the wagon!",
            "2. CAULK & FLOAT: Seal wagon bed with tar and float across like a boat. Good for wide rivers.",
            "3. TAKE FERRY ($5.00): Safest option operated by local ferrymen. Guaranteed safe crossing.",
        ]

        curr_y = py + 75
        for line in lines:
            if line:
                s = FontManager.body(14).render(line, True, Palette.TEXT_BODY)
                self.canvas.blit(s, (px + 40, curr_y))
            curr_y += 28

        # Action Buttons
        self.btn_river_ford.draw(self.canvas)
        self.btn_river_caulk.draw(self.canvas)
        self.btn_river_ferry.is_enabled = self.state.inventory.cash >= 5.0
        self.btn_river_ferry.draw(self.canvas)

    def _draw_store_modal(self) -> None:
        """General store provisioning modal with distance-inflation adjusted prices."""
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 10, 8, 205))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 820, 520
        px, py = (BASE_WIDTH - pw) // 2, (BASE_HEIGHT - ph) // 2
        pnl = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, Palette.PANEL_BG, pnl, border_radius=8)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, pnl, width=2, border_radius=8)

        # Header
        curr_lm = self.state.current_landmark
        title = FontManager.title(20).render(f"{curr_lm.name.upper()} GENERAL STORE", True, Palette.GOLD_LIGHT)
        self.canvas.blit(title, (pnl.centerx - title.get_width() // 2, py + 20))

        cash_txt = FontManager.body(14).render(f"Available Cash: ${self.state.inventory.cash:.2f}", True, Palette.GOLD_PALE)
        self.canvas.blit(cash_txt, (px + 45, py + 55))

        # Table Column Headers
        hdr_item = FontManager.small(12).render("SUPPLY ITEM", True, Palette.TEXT_MUTED)
        hdr_price = FontManager.small(12).render("UNIT PRICE", True, Palette.TEXT_MUTED)
        hdr_cart = FontManager.small(12).render("QUANTITY TO BUY", True, Palette.TEXT_MUTED)
        hdr_subtotal = FontManager.small(12).render("SUBTOTAL", True, Palette.TEXT_MUTED)

        self.canvas.blit(hdr_item, (px + 45, py + 85))
        self.canvas.blit(hdr_price, (px + 230, py + 85))
        self.canvas.blit(hdr_cart, (px + 360, py + 85))
        self.canvas.blit(hdr_subtotal, (px + 570, py + 85))
        pygame.draw.line(self.canvas, Palette.PANEL_BORDER, (px + 35, py + 105), (pnl.right - 35, py + 105), 1)

        # Items
        items = [
            ("oxen", "Ox (Draught animal)", 1),
            ("food", "Food (Pound)", 10),
            ("clothing", "Warm Clothing (Set)", 1),
            ("ammunition", "Ammunition (Box of 50)", 10),
            ("wagon_wheel", "Spare Wagon Wheel", 1),
            ("wagon_axle", "Spare Wagon Axle", 1),
            ("wagon_tongue", "Spare Wagon Tongue", 1),
            ("medical_kit", "Medical / Medicine Kit", 1),
        ]

        curr_y = py + 115
        total_cost = 0.0

        for key, name, step in items:
            unit_price = get_item_price(key, self.state.miles_traveled)
            qty = self.store_cart[key]
            subtotal = unit_price * qty
            total_cost += subtotal

            # Item name
            i_surf = FontManager.body(13).render(name, True, Palette.TEXT_TITLE)
            self.canvas.blit(i_surf, (px + 45, curr_y))

            # Unit price
            p_surf = FontManager.body(13).render(f"${unit_price:.2f}", True, Palette.SAND_LIGHT)
            self.canvas.blit(p_surf, (px + 230, curr_y))

            # Stepper minus [-]
            minus_rect = pygame.Rect(px + 360, curr_y - 2, 28, 24)
            pygame.draw.rect(self.canvas, Palette.PANEL_BG_LIGHT, minus_rect, border_radius=3)
            pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, minus_rect, width=1, border_radius=3)
            m_txt = FontManager.body(14).render("-", True, Palette.TEXT_TITLE)
            self.canvas.blit(m_txt, (minus_rect.centerx - m_txt.get_width() // 2, minus_rect.centery - m_txt.get_height() // 2))

            # Quantity
            q_surf = FontManager.body(13).render(str(qty), True, Palette.GOLD_LIGHT)
            self.canvas.blit(q_surf, (px + 410, curr_y))

            # Stepper plus [+]
            plus_rect = pygame.Rect(px + 450, curr_y - 2, 28, 24)
            pygame.draw.rect(self.canvas, Palette.PANEL_BG_LIGHT, plus_rect, border_radius=3)
            pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, plus_rect, width=1, border_radius=3)
            p_txt = FontManager.body(14).render("+", True, Palette.TEXT_TITLE)
            self.canvas.blit(p_txt, (plus_rect.centerx - p_txt.get_width() // 2, plus_rect.centery - p_txt.get_height() // 2))

            # Subtotal
            sub_surf = FontManager.body(13).render(f"${subtotal:.2f}", True, Palette.GOLD_PALE)
            self.canvas.blit(sub_surf, (px + 570, curr_y))

            curr_y += 34

        # Total Cart Cost
        pygame.draw.line(self.canvas, Palette.PANEL_BORDER, (px + 35, curr_y + 5), (pnl.right - 35, curr_y + 5), 1)
        tot_str = f"Cart Total: ${total_cost:.2f}"
        tot_col = Palette.SUCCESS_GREEN if total_cost <= self.state.inventory.cash else Palette.CRIMSON_LIGHT
        tot_surf = FontManager.header(16).render(tot_str, True, tot_col)
        self.canvas.blit(tot_surf, (pnl.right - tot_surf.get_width() - 45, curr_y + 15))

        # Buttons
        self.btn_store_buy.is_enabled = (0 < total_cost <= self.state.inventory.cash)
        self.btn_store_buy.draw(self.canvas)
        self.btn_store_close.draw(self.canvas)

    def _draw_event_modal(self) -> None:
        """Announcement modal for random occurrences, illnesses, and rest recovery."""
        event = self.state.active_event
        if not event:
            return

        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 10, 8, 205))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 680, 360
        px, py = (BASE_WIDTH - pw) // 2, (BASE_HEIGHT - ph) // 2
        pnl = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, Palette.PANEL_BG, pnl, border_radius=8)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, pnl, width=2, border_radius=8)

        # Title
        title_surf = FontManager.title(18).render(event.title.upper(), True, Palette.GOLD_LIGHT)
        self.canvas.blit(title_surf, (pnl.centerx - title_surf.get_width() // 2, py + 30))

        # Description
        desc_surf = FontManager.body(15).render(event.description, True, Palette.TEXT_BODY)
        self.canvas.blit(desc_surf, (px + 45, py + 95))

        # Impact Summary
        imp_surf = FontManager.body(15).render(event.impact_summary, True, Palette.AMBER_WARN if "Lost" in event.impact_summary or "sick" in event.impact_summary else Palette.SUCCESS_GREEN)
        self.canvas.blit(imp_surf, (px + 45, py + 145))

        self.btn_event_dismiss.draw(self.canvas)

    def _draw_hunt_modal(self) -> None:
        """Hunting expedition outcome modal."""
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 10, 8, 205))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 640, 340
        px, py = (BASE_WIDTH - pw) // 2, (BASE_HEIGHT - ph) // 2
        pnl = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, Palette.PANEL_BG, pnl, border_radius=8)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, pnl, width=2, border_radius=8)

        title = FontManager.title(18).render("HUNTING EXPEDITION", True, Palette.GOLD_LIGHT)
        self.canvas.blit(title, (pnl.centerx - title.get_width() // 2, py + 30))

        msg_surf = FontManager.body(15).render(self.hunt_modal_text, True, Palette.TEXT_BODY)
        self.canvas.blit(msg_surf, (px + 45, py + 110))

        ammo_surf = FontManager.small(13).render(f"Remaining Ammunition: {self.state.inventory.ammunition} rounds", True, Palette.TEXT_MUTED)
        self.canvas.blit(ammo_surf, (px + 45, py + 160))

        self.btn_hunt_dismiss.draw(self.canvas)

    def _draw_log_modal(self) -> None:
        """Chronicle modal displaying trail expedition history entries."""
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 10, 8, 205))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 840, 560
        px, py = (BASE_WIDTH - pw) // 2, (BASE_HEIGHT - ph) // 2
        pnl = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, Palette.PANEL_BG, pnl, border_radius=8)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, pnl, width=2, border_radius=8)

        title = FontManager.title(18).render("TRAIL EXPEDITION JOURNAL & LOG", True, Palette.GOLD_LIGHT)
        self.canvas.blit(title, (pnl.centerx - title.get_width() // 2, py + 25))

        entries = self.state.history_log[-14:] if self.state.history_log else ["No entries recorded yet."]
        curr_y = py + 70
        for entry in entries:
            e_surf = FontManager.small(12).render(f"•  {entry}", True, Palette.TEXT_BODY)
            self.canvas.blit(e_surf, (px + 40, curr_y))
            curr_y += 28

        self.btn_log_close.draw(self.canvas)

    def _draw_rules_modal(self) -> None:
        """Trail guide manual overlay."""
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 10, 8, 215))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 880, 590
        px, py = (BASE_WIDTH - pw) // 2, (BASE_HEIGHT - ph) // 2
        pnl = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, Palette.PANEL_BG, pnl, border_radius=8)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, pnl, width=2, border_radius=8)

        title = FontManager.title(20).render("THE OREGON TRAIL: PIONEER SURVIVAL GUIDE", True, Palette.GOLD_LIGHT)
        self.canvas.blit(title, (pnl.centerx - title.get_width() // 2, py + 22))

        rules = [
            ("HISTORICAL BACKGROUND (1971 / 1978 MECC & CREATIVE COMPUTING):", Palette.GOLD_BASE, True),
            ("Designed by Don Rawitsch, Bill Heinemann, and Paul Dillenberger to simulate the historic 1848 journey.", Palette.SAND_LIGHT, False),
            ("Your pioneer party travels 2,040 miles across prairies, rivers, and Rocky Mountains to Oregon.", Palette.SAND_LIGHT, False),
            ("", Palette.TEXT_MUTED, False),
            ("VITAL TRAIL MECHANICS & SURVIVAL RULES:", Palette.GOLD_BASE, True),
            ("• RATIONS: Filling (3 lbs/day) restores health. Meager (2 lbs/day) maintains. Bare bones causes starvation.", Palette.SAND_LIGHT, False),
            ("• PACE: Steady (~14 mi/day) is sustainable. Strenuous (~18 mi/day) drains stamina. Grueling wears down party & oxen.", Palette.SAND_LIGHT, False),
            ("• REST: Resting heals sick pioneers and grants a 40% chance per day to cure fever and dysentery.", Palette.SAND_LIGHT, False),
            ("• HUNTING: Spend ammunition to harvest wild rabbits, antelope, and buffalo for fresh meat.", Palette.SAND_LIGHT, False),
            ("• RIVER CROSSINGS: Ford shallow rivers (<2.5 ft). Caulk and float wide rivers. Take ferry for guaranteed safety.", Palette.SAND_LIGHT, False),
            ("• FORTS & STORES: Stock up early. Prices inflate between 1.0x at Independence to 2.2x at Oregon outposts.", Palette.SAND_LIGHT, False),
            ("", Palette.TEXT_MUTED, False),
            ("FINAL SCORING & MULTIPLIERS:", Palette.GOLD_BASE, True),
            ("• Score = Remaining health + Surviving party members (500 pts each) + Remaining supplies & cash.", Palette.SAND_LIGHT, False),
            ("• Multipliers: Banker (1.0x), Carpenter (2.0x), Farmer (3.0x).", Palette.SUCCESS_GREEN, False),
        ]

        curr_y = py + 65
        for text, col, is_bold in rules:
            if text:
                f = FontManager.header(14) if is_bold else FontManager.small(12)
                s = f.render(text, True, col)
                self.canvas.blit(s, (px + 40, curr_y))
            curr_y += 22

        self.btn_rules_close.draw(self.canvas)

    def _draw_outcome_modal(self) -> None:
        """Victory or defeat end-of-journey tombstone and scorecard."""
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 10, 8, 225))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 780, 520
        px, py = (BASE_WIDTH - pw) // 2, (BASE_HEIGHT - ph) // 2
        pnl = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, Palette.PANEL_BG, pnl, border_radius=8)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, pnl, width=2, border_radius=8)

        if self.state.victory:
            title_text = "WILLAMETTE VALLEY REACHED! VICTORY!"
            title_col = Palette.SUCCESS_GREEN
            score = calculate_score(self.state)
            desc_lines = [
                "Congratulations! You have completed the grueling 2,040-mile trek across North America.",
                f"Surviving party members: {len(self.state.living_members)} / {len(self.state.party)} pioneers.",
                f"Remaining food: {int(self.state.inventory.food)} lbs  •  Remaining cash: ${self.state.inventory.cash:.2f}",
                f"Profession Multiplier: {self.state.profession.value} ({self.state.profession.score_multiplier:.1f}x)",
                f"TOTAL ADVENTURE SCORE: {score:,} POINTS",
            ]
        else:
            title_text = "THE JOURNEY HAS ENDED IN TRAGEDY"
            title_col = Palette.CRIMSON_LIGHT
            reason = self.state.game_over_reason or "Your party could not complete the trail."
            desc_lines = [
                reason,
                f"Final miles reached: {int(self.state.miles_traveled)} / {int(self.state.total_trail_miles)} miles.",
                f"Nearest milestone: {self.state.current_landmark.name}",
                "A weathered cedar tombstone now marks your resting place along the historic trail.",
            ]

        title_surf = FontManager.title(22).render(title_text, True, title_col)
        self.canvas.blit(title_surf, (pnl.centerx - title_surf.get_width() // 2, py + 35))

        curr_y = py + 110
        for line in desc_lines:
            f = FontManager.header(16) if "TOTAL ADVENTURE SCORE" in line else FontManager.body(15)
            col = Palette.GOLD_LIGHT if "TOTAL ADVENTURE SCORE" in line else Palette.TEXT_BODY
            s = f.render(line, True, col)
            self.canvas.blit(s, (pnl.centerx - s.get_width() // 2, curr_y))
            curr_y += 38

        # Tombstone icon if defeat
        if not self.state.victory:
            tomb_rect = pygame.Rect(pnl.centerx - 45, curr_y + 10, 90, 75)
            pygame.draw.rect(self.canvas, (90, 85, 80), tomb_rect, border_top_left_radius=25, border_top_right_radius=25)
            pygame.draw.rect(self.canvas, (130, 125, 120), tomb_rect, width=2, border_top_left_radius=25, border_top_right_radius=25)
            rip_surf = FontManager.header(14).render("R. I. P.", True, Palette.TEXT_MUTED)
            self.canvas.blit(rip_surf, (tomb_rect.centerx - rip_surf.get_width() // 2, tomb_rect.y + 24))

        self.btn_outcome_restart.draw(self.canvas)
        self.btn_outcome_library.draw(self.canvas)

    def _draw_toast(self) -> None:
        if not self.toast_message:
            return
        surf = FontManager.body(14).render(self.toast_message, True, Palette.TEXT_TITLE)
        tw = surf.get_width() + 40
        th = 38
        tx = (BASE_WIDTH - tw) // 2
        ty = BASE_HEIGHT - 60
        pygame.draw.rect(self.canvas, (40, 24, 18), (tx, ty, tw, th), border_radius=6)
        pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT, (tx, ty, tw, th), width=2, border_radius=6)
        self.canvas.blit(surf, (tx + 20, ty + 9))

    def _screen_to_canvas(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        win_w, win_h = self.screen_width, self.screen_height
        scale = min(win_w / BASE_WIDTH, win_h / BASE_HEIGHT)
        scaled_w = int(BASE_WIDTH * scale)
        scaled_h = int(BASE_HEIGHT * scale)
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2

        cx = int((pos[0] - offset_x) / scale)
        cy = int((pos[1] - offset_y) / scale)
        return max(0, min(BASE_WIDTH, cx)), max(0, min(BASE_HEIGHT, cy))

    def _present(self) -> None:
        CRTEffect.apply(self.canvas)
        win_w, win_h = self.screen_width, self.screen_height
        scale = min(win_w / BASE_WIDTH, win_h / BASE_HEIGHT)
        scaled_w = int(BASE_WIDTH * scale)
        scaled_h = int(BASE_HEIGHT * scale)
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2

        scaled_canvas = pygame.transform.smoothscale(self.canvas, (scaled_w, scaled_h))
        self.window.fill((0, 0, 0))
        self.window.blit(scaled_canvas, (offset_x, offset_y))
        pygame.display.flip()

    def run(self) -> None:
        """Main game loop for standalone execution."""
        last_time = time.time()
        while self.is_running:
            now = time.time()
            dt = min(now - last_time, 0.1)
            last_time = now

            for event in pygame.event.get():
                self.handle_event(event)

            self.update(dt)
            self.draw()
            self._present()
            self.clock.tick(60)


if __name__ == "__main__":
    app = OregonApp()
    app.run()
