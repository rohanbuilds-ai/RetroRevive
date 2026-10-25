"""
games/lunar_lander/app.py - Graphical desktop application for Lunar Lander (1978 Edition).

Features an animated lunar descent, Apollo LEM sprite with thruster exhaust particles,
real-time flight telemetry cockpit, fuel burn presets, landing evaluation tiers,
and seamless RetroRevive platform library integration.
"""

import math
import random
import sys
import time
from typing import Callable, List, Optional, Tuple

import pygame

from ui_theme import FontManager, Palette, SoundSynthesizer, UIButton, UIModal
from .engine import (
    DEFAULT_MASS,
    DRY_MASS,
    GRAVITY_G,
    INITIAL_ALTITUDE,
    MAX_LEGAL_BURN,
    THRUST_Z,
    LanderState,
    init_game,
    step_burn,
    validate_burn,
)

BASE_WIDTH = 1280
BASE_HEIGHT = 720


class StarParticle:
    """Twinkling background star in deep space."""

    def __init__(self, x: int, y: int, size: int, brightness: float) -> None:
        self.x = x
        self.y = y
        self.size = size
        self.brightness = brightness
        self.twinkle_speed = random.uniform(1.5, 4.0)

    def update(self, dt: float) -> None:
        self.brightness += math.sin(time.time() * self.twinkle_speed) * 0.05
        self.brightness = max(0.2, min(1.0, self.brightness))

    def draw(self, surface: pygame.Surface) -> None:
        val = int(255 * self.brightness)
        col = (val, val, min(255, val + 20))
        if self.size == 1:
            surface.set_at((self.x, self.y), col)
        else:
            pygame.draw.circle(surface, col, (self.x, self.y), self.size)


class ExhaustFlame:
    """Animated flame particle emitted from LEM descent engine."""

    def __init__(self, x: float, y: float, intensity: float) -> None:
        self.x = x + random.uniform(-4, 4)
        self.y = y
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(3.0, 8.0) * (intensity / 100.0)
        self.life = random.uniform(0.15, 0.4)
        self.max_life = self.life
        self.size = random.uniform(3.0, 7.0)

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.x += self.vx
        self.y += self.vy
        self.size = max(0.5, self.size - dt * 4.0)
        return self.life > 0

    def draw(self, surface: pygame.Surface) -> None:
        alpha = int(255 * (self.life / self.max_life))
        # Orange/yellow core transitioning to red smoke
        if self.life > self.max_life * 0.5:
            color = (255, random.randint(180, 240), 40, alpha)
        else:
            color = (240, random.randint(60, 100), 20, alpha)

        surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (int(self.size), int(self.size)), int(self.size))
        surface.blit(surf, (int(self.x - self.size), int(self.y - self.size)))


class LanderApp:
    """Pygame application for Lunar Lander."""

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

        pygame.display.set_caption("RetroRevive: Lunar Lander (1978)")
        self.canvas = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        self.clock = pygame.time.Clock()
        self.is_running = True

        # Simulation State
        self.state: LanderState = init_game()
        self.current_burn_input: float = 0.0
        self.display_altitude: float = self.state.altitude
        self.display_velocity: float = self.state.velocity
        self.display_fuel: float = self.state.fuel_remaining

        # Visual Effects
        self.stars: List[StarParticle] = []
        self._init_stars()
        self.exhaust_particles: List[ExhaustFlame] = []
        self.is_thrusting: bool = False
        self.thrust_anim_timer: float = 0.0

        # UI Controls
        self._init_buttons()
        self.show_rules_modal: bool = False
        self.toast_message: Optional[str] = None
        self.toast_timer: float = 0.0

    def _init_stars(self) -> None:
        self.stars.clear()
        for _ in range(120):
            x = random.randint(0, BASE_WIDTH)
            y = random.randint(0, BASE_HEIGHT - 120)
            sz = 1 if random.random() > 0.2 else 2
            bright = random.uniform(0.3, 1.0)
            self.stars.append(StarParticle(x, y, sz, bright))

    def _init_buttons(self) -> None:
        # Header navigation buttons
        self.btn_back = UIButton((30, 18, 160, 38), "← LIBRARY", self._on_back_clicked, color_scheme="sand", font_size=14)
        self.btn_rules = UIButton((205, 18, 140, 38), "FLIGHT MANUAL", self._toggle_rules, color_scheme="lapis", font_size=14)
        self.btn_restart = UIButton((BASE_WIDTH - 180, 18, 150, 38), "RESTART FLIGHT", self._restart_flight, color_scheme="crimson", font_size=14)

        # Control Panel Buttons (Right Sidebar)
        cx = 940
        cy = 100

        # Burn Rate Presets
        self.btn_burn_0 = UIButton((cx, cy + 260, 70, 36), "0 (FREE)", lambda: self._set_burn(0.0), font_size=12)
        self.btn_burn_50 = UIButton((cx + 76, cy + 260, 68, 36), "50", lambda: self._set_burn(50.0), font_size=13)
        self.btn_burn_100 = UIButton((cx + 150, cy + 260, 68, 36), "100", lambda: self._set_burn(100.0), font_size=13)
        self.btn_burn_150 = UIButton((cx + 224, cy + 260, 72, 36), "150", lambda: self._set_burn(150.0), font_size=13)

        # Quick action buttons
        self.btn_burn_max = UIButton((cx, cy + 306, 144, 38), "MAX BURN [200]", lambda: self._set_burn(200.0), primary=True, font_size=13)
        self.btn_burn_hover = UIButton((cx + 152, cy + 306, 144, 38), "AUTO-HOVER", self._set_hover_burn, color_scheme="lapis", font_size=13)

        # Steppers (+10, -10, +25, -25)
        self.btn_step_m25 = UIButton((cx, cy + 354, 70, 34), "-25", lambda: self._adjust_burn(-25.0), color_scheme="sand", font_size=12)
        self.btn_step_m10 = UIButton((cx + 76, cy + 354, 68, 34), "-10", lambda: self._adjust_burn(-10.0), color_scheme="sand", font_size=12)
        self.btn_step_p10 = UIButton((cx + 150, cy + 354, 68, 34), "+10", lambda: self._adjust_burn(10.0), color_scheme="sand", font_size=12)
        self.btn_step_p25 = UIButton((cx + 224, cy + 354, 72, 34), "+25", lambda: self._adjust_burn(25.0), color_scheme="sand", font_size=12)

        # Main Execute Cycle Button
        self.btn_burn_ignite = UIButton((cx, cy + 404, 296, 52), "EXECUTE 10S BURN [SPACE]", self._execute_burn, primary=True, font_size=16)

        # Outcome Modal Buttons
        self.btn_modal_again = UIButton((BASE_WIDTH // 2 - 210, 480, 200, 48), "PLAY AGAIN", self._restart_flight, primary=True)
        self.btn_modal_library = UIButton((BASE_WIDTH // 2 + 10, 480, 200, 48), "BACK TO LIBRARY", self._on_back_clicked, color_scheme="sand")

        # Rules Modal Close Button
        self.btn_rules_close = UIButton((BASE_WIDTH // 2 - 80, 560, 160, 42), "CLOSE", self._toggle_rules, color_scheme="gold")

    def _set_burn(self, val: float) -> None:
        self.current_burn_input = max(0.0, min(MAX_LEGAL_BURN, val))
        SoundSynthesizer.play("click")

    def _adjust_burn(self, delta: float) -> None:
        self.current_burn_input = max(0.0, min(MAX_LEGAL_BURN, self.current_burn_input + delta))
        SoundSynthesizer.play("click")

    def _set_hover_burn(self) -> None:
        # Hover rate in lbs/sec is the burn rate that counteracts gravity: K = (M * G) / Z
        m = self.state.mass
        hover_k = (m * GRAVITY_G) / THRUST_Z
        self.current_burn_input = round(min(MAX_LEGAL_BURN, hover_k), 1)
        SoundSynthesizer.play("click")
        self.show_toast(f"Auto-Hover computed: {self.current_burn_input} lbs/sec")

    def _toggle_rules(self) -> None:
        self.show_rules_modal = not self.show_rules_modal
        SoundSynthesizer.play("click")

    def _restart_flight(self) -> None:
        self.state = init_game()
        self.current_burn_input = 0.0
        self.display_altitude = self.state.altitude
        self.display_velocity = self.state.velocity
        self.display_fuel = self.state.fuel_remaining
        self.exhaust_particles.clear()
        SoundSynthesizer.play("fanfare")

    def _on_back_clicked(self) -> None:
        if self.on_exit_to_library:
            self.on_exit_to_library()
        else:
            self.is_running = False

    def show_toast(self, msg: str) -> None:
        self.toast_message = msg
        self.toast_timer = 2.5

    def _execute_burn(self) -> None:
        if self.state.is_terminal:
            return

        ok, err = validate_burn(self.state, self.current_burn_input)
        if not ok:
            SoundSynthesizer.play("warning")
            self.show_toast(err or "Invalid burn rate")
            return

        # Trigger visual thruster animation
        if self.current_burn_input > 0:
            self.is_thrusting = True
            self.thrust_anim_timer = 0.6
            SoundSynthesizer.play("harvest")  # engine roar tone
        else:
            SoundSynthesizer.play("click")

        # Execute authoritative simulation step
        self.state = step_burn(self.state, self.current_burn_input)

        if self.state.is_terminal:
            if self.state.outcome in ("PERFECT", "GOOD"):
                SoundSynthesizer.play("fanfare")
            else:
                SoundSynthesizer.play("warning")

    def handle_event(self, event: pygame.event.Event) -> None:
        raw_pos = getattr(event, "pos", pygame.mouse.get_pos())
        canvas_mouse = self._screen_to_canvas(raw_pos)

        if event.type == pygame.QUIT:
            self.is_running = False
            return

        if event.type == pygame.VIDEORESIZE:
            self.screen_width = event.w
            self.screen_height = event.h
            self.window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            return

        # Rules Modal Event Handling
        if self.show_rules_modal:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_m, pygame.K_f
            ):
                self.show_rules_modal = False
                return
            self.btn_rules_close.handle_event(event, canvas_mouse)
            return

        # Header buttons
        if self.btn_back.handle_event(event, canvas_mouse):
            return
        if self.btn_rules.handle_event(event, canvas_mouse):
            return
        if self.btn_restart.handle_event(event, canvas_mouse):
            return

        # Outcome Modal Clicks
        if self.state.is_terminal:
            if self.btn_modal_again.handle_event(event, canvas_mouse):
                return
            if self.btn_modal_library.handle_event(event, canvas_mouse):
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_r):
                    self._restart_flight()
                elif event.key == pygame.K_ESCAPE:
                    self._on_back_clicked()
            return

        # Control Panel Buttons
        for btn in [
            self.btn_burn_0, self.btn_burn_50, self.btn_burn_100, self.btn_burn_150,
            self.btn_burn_max, self.btn_burn_hover,
            self.btn_step_m25, self.btn_step_m10, self.btn_step_p10, self.btn_step_p25,
            self.btn_burn_ignite,
        ]:
            if btn.handle_event(event, canvas_mouse):
                return

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._execute_burn()
            elif event.key in (pygame.K_0, pygame.K_KP0):
                self._set_burn(0.0)
            elif event.key in (pygame.K_1, pygame.K_KP1):
                self._set_burn(50.0)
            elif event.key in (pygame.K_2, pygame.K_KP2):
                self._set_burn(100.0)
            elif event.key in (pygame.K_3, pygame.K_KP3):
                self._set_burn(150.0)
            elif event.key in (pygame.K_4, pygame.K_KP4, pygame.K_x):
                self._set_burn(200.0)
            elif event.key in (pygame.K_m, pygame.K_f):
                self._toggle_rules()
            elif event.key == pygame.K_h:
                self._set_hover_burn()
            elif event.key == pygame.K_UP:
                self._adjust_burn(10.0)
            elif event.key == pygame.K_DOWN:
                self._adjust_burn(-10.0)
            elif event.key == pygame.K_ESCAPE:
                self._on_back_clicked()

    def update(self, dt: float) -> None:
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast_message = None

        # Update stars
        for star in self.stars:
            star.update(dt)

        # Smooth visual interpolation toward target simulation numbers
        self.display_altitude += (self.state.altitude - self.display_altitude) * min(1.0, dt * 5.0)
        self.display_velocity += (self.state.velocity - self.display_velocity) * min(1.0, dt * 5.0)
        self.display_fuel += (self.state.fuel_remaining - self.display_fuel) * min(1.0, dt * 5.0)

        # Handle thruster flame particles
        if self.thrust_anim_timer > 0:
            self.thrust_anim_timer -= dt
            if self.thrust_anim_timer <= 0:
                self.is_thrusting = False

        if self.is_thrusting and self.current_burn_input > 0:
            lem_x, lem_y = self._get_lem_pixel_pos()
            for _ in range(3):
                self.exhaust_particles.append(
                    ExhaustFlame(lem_x, lem_y + 32, intensity=self.current_burn_input)
                )

        # Update particles
        self.exhaust_particles = [p for p in self.exhaust_particles if p.update(dt)]

    def _get_lem_pixel_pos(self) -> Tuple[float, float]:
        """Maps simulation altitude (0 to 120 miles) to canvas viewport (x=460, y=140 to 520)."""
        top_y = 140.0
        ground_y = 515.0
        # Non-linear log scale for altitude so final 10 miles have high visual fidelity
        norm_alt = max(0.0, min(1.0, self.display_altitude / INITIAL_ALTITUDE))
        pixel_y = ground_y - (norm_alt ** 0.65) * (ground_y - top_y)
        return 460.0, pixel_y

    def draw(self) -> None:
        # 1. Deep space background
        self.canvas.fill((10, 10, 16))

        # Stars
        for star in self.stars:
            star.draw(self.canvas)

        # Distant Blue Earth hanging in lunar sky
        earth_center = (180, 180)
        pygame.draw.circle(self.canvas, (25, 75, 160), earth_center, 34)
        pygame.draw.circle(self.canvas, (65, 140, 210), earth_center, 32)
        # Cloud swirl
        pygame.draw.ellipse(self.canvas, (240, 245, 255, 180), (160, 168, 28, 14))
        pygame.draw.ellipse(self.canvas, (240, 245, 255, 160), (175, 182, 32, 12))

        # 2. Lunar Surface (Rugged terrain and landing pad)
        surface_rect = pygame.Rect(0, 560, BASE_WIDTH, BASE_HEIGHT - 560)
        pygame.draw.rect(self.canvas, (60, 58, 62), surface_rect)
        # Rocky crater lines
        pygame.draw.ellipse(self.canvas, (45, 43, 48), (120, 580, 160, 35))
        pygame.draw.ellipse(self.canvas, (45, 43, 48), (620, 610, 220, 45))
        pygame.draw.line(self.canvas, (110, 108, 115), (0, 560), (BASE_WIDTH, 560), 2)

        # Landing Target Pad (x: 400 to 520)
        pad_rect = pygame.Rect(400, 556, 120, 8)
        pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT, pad_rect, border_radius=3)
        pad_txt = FontManager.small(11).render("TRANQUILITY BASE", True, Palette.GOLD_PALE)
        self.canvas.blit(pad_txt, (pad_rect.centerx - pad_txt.get_width() // 2, 568))

        # 3. Exhaust Flame Particles
        for p in self.exhaust_particles:
            p.draw(self.canvas)

        # 4. Apollo Lunar Module (LEM) Sprite
        self._draw_lem()

        # 5. Top Header
        self._draw_header()

        # 6. Left Telemetry Dashboard Panel
        self._draw_telemetry_panel()

        # 7. Right Controls Panel
        self._draw_controls_panel()

        # 8. Terminal Outcome Modal
        if self.state.is_terminal:
            self._draw_outcome_modal()

        # 9. Rules Modal
        if self.show_rules_modal:
            self._draw_rules_modal()

        # 10. Toast Alert
        if self.toast_message:
            self._draw_toast()

        # 11. Scale canvas to window
        self._present()

    def _draw_lem(self) -> None:
        lem_x, lem_y = self._get_lem_pixel_pos()
        ix, iy = int(lem_x), int(lem_y)

        # Descent Stage (Mylar gold foil octagonal base)
        base_rect = pygame.Rect(ix - 24, iy + 6, 48, 22)
        pygame.draw.rect(self.canvas, (180, 140, 35), base_rect, border_radius=4)
        pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT, base_rect, width=2, border_radius=4)

        # Ascent Stage (Gray cabin with triangular cockpit windows)
        cabin_rect = pygame.Rect(ix - 18, iy - 16, 36, 24)
        pygame.draw.rect(self.canvas, (190, 195, 205), cabin_rect, border_radius=6)
        pygame.draw.rect(self.canvas, (120, 125, 135), cabin_rect, width=2, border_radius=6)

        # Cockpit windows (reflective black/cyan)
        pygame.draw.polygon(self.canvas, (20, 30, 45), [(ix - 12, iy - 6), (ix - 4, iy - 6), (ix - 7, iy - 12)])
        pygame.draw.polygon(self.canvas, (20, 30, 45), [(ix + 4, iy - 6), (ix + 12, iy - 6), (ix + 7, iy - 12)])

        # Reaction Control System (RCS) thruster quads
        pygame.draw.line(self.canvas, (160, 165, 175), (ix - 24, iy - 4), (ix - 28, iy - 4), 2)
        pygame.draw.line(self.canvas, (160, 165, 175), (ix + 24, iy - 4), (ix + 28, iy - 4), 2)

        # Landing Gear Legs & Footpads
        pygame.draw.line(self.canvas, (150, 150, 150), (ix - 22, iy + 26), (ix - 36, iy + 44), 3)
        pygame.draw.line(self.canvas, (150, 150, 150), (ix + 22, iy + 26), (ix + 36, iy + 44), 3)
        # Footpads
        pygame.draw.ellipse(self.canvas, Palette.GOLD_LIGHT, (ix - 42, iy + 42, 12, 5))
        pygame.draw.ellipse(self.canvas, Palette.GOLD_LIGHT, (ix + 30, iy + 42, 12, 5))

        # Main Engine Bell Nozzle
        nozzle_pts = [(ix - 8, iy + 28), (ix + 8, iy + 28), (ix + 12, iy + 36), (ix - 12, iy + 36)]
        pygame.draw.polygon(self.canvas, (70, 70, 75), nozzle_pts)

    def _draw_header(self) -> None:
        header_rect = pygame.Rect(0, 0, BASE_WIDTH, 68)
        pygame.draw.rect(self.canvas, Palette.PANEL_BG, header_rect)
        pygame.draw.line(self.canvas, Palette.GOLD_BASE, (0, 68), (BASE_WIDTH, 68), 2)

        # Title
        title = FontManager.header(22).render("LUNAR LANDER", True, Palette.GOLD_PALE)
        sub = FontManager.small(12).render("Jim Storer (1969) / David H. Ahl (1978) — Apollo LEM Descent", True, Palette.TEXT_MUTED)
        self.canvas.blit(title, (BASE_WIDTH // 2 - title.get_width() // 2, 12))
        self.canvas.blit(sub, (BASE_WIDTH // 2 - sub.get_width() // 2, 40))

        self.btn_back.draw(self.canvas)
        self.btn_rules.draw(self.canvas)
        self.btn_restart.draw(self.canvas)

    def _draw_telemetry_panel(self) -> None:
        px, py, pw, ph = 30, 90, 270, 450
        panel_rect = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(self.canvas, Palette.PANEL_BG, panel_rect, border_radius=12)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, panel_rect, width=1, border_radius=12)

        p_title = FontManager.header(16).render("MISSION TELEMETRY", True, Palette.GOLD_PALE)
        self.canvas.blit(p_title, (px + 18, py + 16))
        pygame.draw.line(self.canvas, Palette.PANEL_BORDER, (px + 18, py + 42), (px + pw - 18, py + 42), 1)

        # Velocity color coding
        w_mph = self.display_velocity * 3600.0
        if w_mph <= 10.0:
            v_col = Palette.SUCCESS_GREEN
            v_badge = "SAFE"
        elif w_mph <= 60.0:
            v_col = Palette.AMBER_WARN
            v_badge = "CAUTION"
        else:
            v_col = Palette.CRIMSON_LIGHT
            v_badge = "DANGER"

        items = [
            ("MISSION TIME:", f"{self.state.time_elapsed:.0f} SEC", Palette.TEXT_BODY),
            ("RADAR ALTITUDE:", f"{self.display_altitude:.1f} MI", Palette.GOLD_PALE),
            ("SURFACE DISTANCE:", f"{int(self.display_altitude * 5280):,} FT", Palette.SAND_LIGHT),
            ("VERTICAL SPEED:", f"{w_mph:.1f} MPH", v_col),
            ("DESCENT STATUS:", v_badge, v_col),
            ("REMAINING FUEL:", f"{self.display_fuel:.0f} LBS", Palette.GOLD_LIGHT),
            ("CAPSULE MASS:", f"{self.state.mass:.0f} LBS", Palette.TEXT_MUTED),
        ]

        curr_y = py + 56
        for lbl, val, col in items:
            self.canvas.blit(FontManager.small(12).render(lbl, True, Palette.TEXT_MUTED), (px + 18, curr_y))
            v_surf = FontManager.body(15).render(val, True, col)
            self.canvas.blit(v_surf, (px + 18, curr_y + 16))
            curr_y += 44

        # Fuel Tank Level Bar
        curr_y += 6
        self.canvas.blit(FontManager.small(11).render("PROPELLANT RESERVE:", True, Palette.TEXT_MUTED), (px + 18, curr_y))
        bar_rect = pygame.Rect(px + 18, curr_y + 16, pw - 36, 16)
        pygame.draw.rect(self.canvas, (25, 20, 16), bar_rect, border_radius=4)
        pct = max(0.0, min(1.0, self.display_fuel / (DEFAULT_MASS - DRY_MASS)))
        fill_w = int((pw - 36) * pct)
        if fill_w > 0:
            fill_col = Palette.GOLD_BASE if pct > 0.25 else Palette.CRIMSON_LIGHT
            pygame.draw.rect(self.canvas, fill_col, (px + 18, curr_y + 16, fill_w, 16), border_radius=4)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, bar_rect, width=1, border_radius=4)

    def _draw_controls_panel(self) -> None:
        px, py, pw, ph = 920, 90, 330, 470
        panel_rect = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(self.canvas, Palette.PANEL_BG, panel_rect, border_radius=12)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, panel_rect, width=1, border_radius=12)

        c_title = FontManager.header(16).render("RETRO-ROCKET CONTROLS", True, Palette.GOLD_PALE)
        self.canvas.blit(c_title, (px + 18, py + 16))
        pygame.draw.line(self.canvas, Palette.PANEL_BORDER, (px + 18, py + 42), (px + pw - 18, py + 42), 1)

        # Current Burn Rate Display Box
        box_rect = pygame.Rect(px + 18, py + 56, pw - 36, 68)
        pygame.draw.rect(self.canvas, (24, 18, 14), box_rect, border_radius=8)
        pygame.draw.rect(self.canvas, Palette.GOLD_BASE, box_rect, width=2, border_radius=8)

        lbl = FontManager.small(12).render("SET FUEL BURN RATE <K>:", True, Palette.TEXT_MUTED)
        self.canvas.blit(lbl, (box_rect.x + 14, box_rect.y + 10))

        val_str = f"{self.current_burn_input:.0f} LBS/SEC"
        val_surf = FontManager.title(26).render(val_str, True, Palette.GOLD_LIGHT)
        self.canvas.blit(val_surf, (box_rect.x + 14, box_rect.y + 30))

        # Preset Buttons
        self.btn_burn_0.draw(self.canvas)
        self.btn_burn_50.draw(self.canvas)
        self.btn_burn_100.draw(self.canvas)
        self.btn_burn_150.draw(self.canvas)

        self.btn_burn_max.draw(self.canvas)
        self.btn_burn_hover.draw(self.canvas)

        self.btn_step_m25.draw(self.canvas)
        self.btn_step_m10.draw(self.canvas)
        self.btn_step_p10.draw(self.canvas)
        self.btn_step_p25.draw(self.canvas)

        self.btn_burn_ignite.draw(self.canvas)

    def _draw_outcome_modal(self) -> None:
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 8, 6, 215))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 680, 420
        px = (BASE_WIDTH - pw) // 2
        py = (BASE_HEIGHT - ph) // 2
        p_rect = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, Palette.PANEL_BG, p_rect, border_radius=14)
        border_col = (
            Palette.GOLD_LIGHT
            if self.state.outcome in ("PERFECT", "GOOD")
            else (Palette.AMBER_WARN if self.state.outcome == "DAMAGED" else Palette.CRIMSON)
        )
        pygame.draw.rect(self.canvas, border_col, p_rect, width=2, border_radius=14)

        # Title
        t_str = f"TOUCHDOWN: {self.state.outcome} LANDING"
        title_surf = FontManager.title(32).render(t_str, True, border_col)
        self.canvas.blit(title_surf, title_surf.get_rect(center=(BASE_WIDTH // 2, py + 50)))

        # Velocity stats
        w_str = f"Impact Velocity: {self.state.touchdown_velocity_mph:.2f} MPH  |  Flight Time: {self.state.time_elapsed:.1f} Sec"
        w_surf = FontManager.header(17).render(w_str, True, Palette.SAND_LIGHT)
        self.canvas.blit(w_surf, w_surf.get_rect(center=(BASE_WIDTH // 2, py + 100)))

        # Historical message (multi-line)
        msg_lines = (self.state.outcome_message or "").split("\n")
        my = py + 145
        for line in msg_lines:
            s = FontManager.body(16).render(line, True, Palette.TEXT_TITLE)
            self.canvas.blit(s, s.get_rect(center=(BASE_WIDTH // 2, my)))
            my += 26

        self.btn_modal_again.draw(self.canvas)
        self.btn_modal_library.draw(self.canvas)

    def _draw_rules_modal(self) -> None:
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 8, 6, 225))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 780, 520
        px = (BASE_WIDTH - pw) // 2
        py = (BASE_HEIGHT - ph) // 2
        p_rect = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, Palette.PANEL_BG, p_rect, border_radius=14)
        pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT, p_rect, width=2, border_radius=14)

        title = FontManager.header(24).render("APOLLO LUNAR MODULE FLIGHT MANUAL (1978)", True, Palette.GOLD_PALE)
        self.canvas.blit(title, title.get_rect(center=(BASE_WIDTH // 2, py + 38)))

        rules = [
            ("MISSION OBJECTIVE:", Palette.GOLD_BASE, True),
            ("Safely pilot the Apollo Lunar Excursion Module (LEM) down onto the lunar surface.", Palette.SAND_LIGHT, False),
            ("", Palette.TEXT_MUTED, False),
            ("FLIGHT DYNAMICS (JIM STORER / DAVID AHL 1978 MODEL):", Palette.GOLD_BASE, True),
            ("• Mission starts at 120 miles altitude, falling at 3,600 MPH (1.0 mi/s).", Palette.SAND_LIGHT, False),
            ("• Spacecraft mass is 33,000 lbs, carrying exactly 16,500 lbs of propellant.", Palette.SAND_LIGHT, False),
            ("• Each 10-second cycle, set your fuel burn rate (K) between 0 and 200 lbs/sec.", Palette.SAND_LIGHT, False),
            ("• Lunar gravity accelerates you at 0.001 mi/s² (~5.28 ft/s²).", Palette.SAND_LIGHT, False),
            ("• The engine expels thrust at exhaust coefficient Z = 1.8 mi/s.", Palette.SAND_LIGHT, False),
            ("", Palette.TEXT_MUTED, False),
            ("TOUCHDOWN VELOCITY CRITERIA:", Palette.GOLD_BASE, True),
            ("• <= 1.2 MPH: PERFECT LANDING! -(LUCKY)", Palette.SUCCESS_GREEN, False),
            ("• 1.2 to 10 MPH: GOOD LANDING (COULD BE BETTER)", Palette.GOLD_LIGHT, False),
            ("• 10 to 60 MPH: CRAFT DAMAGE... Stranded until rescue arrives.", Palette.AMBER_WARN, False),
            ("• > 60 MPH: FATAL CRASH... Blasts a new lunar crater (depth = W * 0.227 ft)!", Palette.CRIMSON_LIGHT, False),
        ]

        curr_y = py + 80
        for text, col, is_bold in rules:
            if text:
                f = FontManager.header(15) if is_bold else FontManager.small(13)
                s = f.render(text, True, col)
                self.canvas.blit(s, (px + 40, curr_y))
            curr_y += 23

        self.btn_rules_close.draw(self.canvas)

    def _draw_toast(self) -> None:
        if not self.toast_message:
            return
        surf = FontManager.body(15).render(self.toast_message, True, Palette.TEXT_TITLE)
        tw = surf.get_width() + 40
        th = 40
        tx = (BASE_WIDTH - tw) // 2
        ty = BASE_HEIGHT - 65
        pygame.draw.rect(self.canvas, (40, 20, 20), (tx, ty, tw, th), border_radius=8)
        pygame.draw.rect(self.canvas, Palette.CRIMSON_LIGHT, (tx, ty, tw, th), width=2, border_radius=8)
        self.canvas.blit(surf, (tx + 20, ty + 10))

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
        while self.is_running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()


def main() -> None:
    start_fullscreen = "--fullscreen" in sys.argv
    app = LanderApp(start_fullscreen=start_fullscreen)
    app.run()
    pygame.quit()


if __name__ == "__main__":
    main()
