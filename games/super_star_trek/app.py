"""
games/super_star_trek/app.py - Graphical desktop application for Super Star Trek (1974/1978 Edition).

Features an authentic tactical short-range sector grid, long-range radar scanner,
interactive phaser banks, directional photon torpedoes, deflector shield management,
starbase docking, subsystem damage telemetry, and seamless RetroRevive platform library integration.
"""

import math
import random
import sys
import time
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from ui_theme import FontManager, Palette, SoundSynthesizer, UIButton, UIModal
from .engine import (
    GALAXY_HEIGHT,
    GALAXY_WIDTH,
    INITIAL_ENERGY,
    INITIAL_SHIELDS,
    INITIAL_TORPEDOES,
    MAX_ENERGY,
    MAX_SHIELDS,
    MAX_TORPEDOES,
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

BASE_WIDTH = 1280
BASE_HEIGHT = 720


class StarParticle:
    """Twinkling deep space star in tactical background."""

    def __init__(self, x: int, y: int, brightness: float) -> None:
        self.x = x
        self.y = y
        self.brightness = brightness
        self.twinkle_speed = random.uniform(1.0, 3.5)

    def update(self, dt: float) -> None:
        self.brightness += math.sin(time.time() * self.twinkle_speed) * 0.04
        self.brightness = max(0.2, min(1.0, self.brightness))

    def draw(self, surface: pygame.Surface) -> None:
        v = int(255 * self.brightness)
        surface.set_at((self.x, self.y), (v, v, min(255, v + 25)))


class TrekApp:
    """Pygame desktop application for Super Star Trek."""

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

        pygame.display.set_caption("RetroRevive: Super Star Trek (1978)")
        self.canvas = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        self.clock = pygame.time.Clock()
        self.is_running = True

        # Tactical Simulation State
        self.state: TrekState = init_game()

        # Background stars
        self.stars: List[StarParticle] = []
        self._init_stars()

        # Input & Control values
        self.current_course: float = 1.0
        self.current_warp: float = 1.0
        self.current_phaser_energy: float = 400.0

        # UI Modals & Views
        self.show_rules_modal: bool = False
        self.show_log_modal: bool = False
        self.show_nav_modal: bool = False
        self.show_phaser_modal: bool = False
        self.show_torpedo_modal: bool = False
        self.show_shield_modal: bool = False
        self.active_lrs_scan: Optional[List[List[Tuple[int, int, int]]]] = None

        # Toast notification
        self.toast_message: Optional[str] = None
        self.toast_timer: float = 0.0

        # Weapons visual feedback timer
        self.weapon_anim_timer: float = 0.0
        self.weapon_anim_type: Optional[str] = None
        self.weapon_anim_target: Optional[Tuple[int, int]] = None

        self._init_buttons()

    def _init_stars(self) -> None:
        self.stars.clear()
        for _ in range(90):
            x = random.randint(0, BASE_WIDTH)
            y = random.randint(0, BASE_HEIGHT)
            self.stars.append(StarParticle(x, y, random.uniform(0.3, 0.9)))

    def _init_buttons(self) -> None:
        # Header navigation buttons
        self.btn_back = UIButton((25, 10, 140, 36), "← LIBRARY", self._on_back_clicked, color_scheme="sand", font_size=13)
        self.btn_rules = UIButton((175, 10, 160, 36), "STARFLEET MANUAL", self._toggle_rules, color_scheme="lapis", font_size=13)
        self.btn_restart = UIButton((BASE_WIDTH - 170, 10, 145, 36), "RESTART MISSION", self._restart_mission, color_scheme="crimson", font_size=13)

        # Primary Command Console Deck (y=555 to 695)
        by = 555
        bw = 160
        bh = 44
        sp = 14
        start_x = 25

        self.btn_cmd_nav = UIButton((start_x, by, bw, bh), "WARP NAV [N]", self._open_nav, primary=True, font_size=14)
        self.btn_cmd_pha = UIButton((start_x + (bw + sp), by, bw, bh), "PHASERS [P]", self._open_phaser, color_scheme="gold", font_size=14)
        self.btn_cmd_tor = UIButton((start_x + (bw + sp) * 2, by, bw, bh), "TORPEDO [T]", self._open_torpedo, color_scheme="crimson", font_size=14)
        self.btn_cmd_she = UIButton((start_x + (bw + sp) * 3, by, bw, bh), "SHIELDS [S]", self._open_shields, color_scheme="lapis", font_size=14)
        self.btn_cmd_lrs = UIButton((start_x + (bw + sp) * 4, by, bw, bh), "LRS RADAR [R]", self._trigger_lrs, color_scheme="lapis", font_size=14)
        self.btn_cmd_doc = UIButton((start_x + (bw + sp) * 5, by, bw, bh), "DOCK STARBASE [D]", self._action_dock, color_scheme="gold", font_size=13)
        self.btn_cmd_log = UIButton((start_x + (bw + sp) * 6, by, bw, bh), "SHIP'S LOG [L]", self._toggle_log, color_scheme="sand", font_size=14)

        # Quick Course Stepper Bar (y=610)
        cy = 615
        self.btn_course_e = UIButton((start_x, cy, 68, 36), "1: EAST", lambda: self._set_course(1.0), font_size=11)
        self.btn_course_ne = UIButton((start_x + 74, cy, 68, 36), "2: NE", lambda: self._set_course(2.0), font_size=11)
        self.btn_course_n = UIButton((start_x + 148, cy, 68, 36), "3: NORTH", lambda: self._set_course(3.0), font_size=11)
        self.btn_course_nw = UIButton((start_x + 222, cy, 68, 36), "4: NW", lambda: self._set_course(4.0), font_size=11)
        self.btn_course_w = UIButton((start_x + 296, cy, 68, 36), "5: WEST", lambda: self._set_course(5.0), font_size=11)
        self.btn_course_sw = UIButton((start_x + 370, cy, 68, 36), "6: SW", lambda: self._set_course(6.0), font_size=11)
        self.btn_course_s = UIButton((start_x + 444, cy, 68, 36), "7: SOUTH", lambda: self._set_course(7.0), font_size=11)
        self.btn_course_se = UIButton((start_x + 518, cy, 68, 36), "8: SE", lambda: self._set_course(8.0), font_size=11)

        # Quick Warp Presets (Right side of quick bar)
        wx = start_x + 605
        self.btn_warp_imp = UIButton((wx, cy, 95, 36), "WARP 0.2", lambda: self._set_warp(0.2), color_scheme="lapis", font_size=12)
        self.btn_warp_1 = UIButton((wx + 102, cy, 95, 36), "WARP 1.0", lambda: self._set_warp(1.0), color_scheme="lapis", font_size=12)
        self.btn_warp_2 = UIButton((wx + 204, cy, 95, 36), "WARP 2.0", lambda: self._set_warp(2.0), color_scheme="lapis", font_size=12)
        self.btn_warp_4 = UIButton((wx + 306, cy, 95, 36), "WARP 4.0", lambda: self._set_warp(4.0), color_scheme="lapis", font_size=12)
        self.btn_warp_8 = UIButton((wx + 408, cy, 95, 36), "WARP 8.0", lambda: self._set_warp(8.0), color_scheme="crimson", font_size=12)

        # Execute Fast Navigation Button
        self.btn_exec_nav = UIButton((wx + 512, cy, 110, 36), "ENGAGE [SPACE]", self._execute_fast_nav, primary=True, font_size=12)

        # Modal Dismiss Buttons
        self.btn_rules_close = UIButton((BASE_WIDTH // 2 - 80, 600, 160, 40), "CLOSE MANUAL", self._toggle_rules, color_scheme="gold")
        self.btn_log_close = UIButton((BASE_WIDTH // 2 - 80, 600, 160, 40), "CLOSE LOG", self._toggle_log, color_scheme="sand")

        # Outcome Modal Buttons
        self.btn_outcome_restart = UIButton((BASE_WIDTH // 2 - 190, 520, 180, 46), "NEW MISSION", self._restart_mission, primary=True)
        self.btn_outcome_library = UIButton((BASE_WIDTH // 2 + 10, 520, 180, 46), "BACK TO LIBRARY", self._on_back_clicked, color_scheme="sand")

    def _set_course(self, crs: float) -> None:
        self.current_course = crs
        SoundSynthesizer.play("click")
        self.show_toast(f"Course locked: {crs:.0f} (Heading: {self._heading_name(crs)})")

    def _set_warp(self, wrp: float) -> None:
        self.current_warp = wrp
        SoundSynthesizer.play("click")
        self.show_toast(f"Warp Factor set to {wrp:.1f}")

    def _heading_name(self, crs: float) -> str:
        names = {1.0: "East", 2.0: "Northeast", 3.0: "North", 4.0: "Northwest", 5.0: "West", 6.0: "Southwest", 7.0: "South", 8.0: "Southeast"}
        return names.get(crs, "Bearing")

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

    def _restart_mission(self) -> None:
        self.state = init_game()
        self.active_lrs_scan = None
        self.current_course = 1.0
        self.current_warp = 1.0
        SoundSynthesizer.play("fanfare")
        self.show_toast("New Starfleet mission commenced!")

    def show_toast(self, msg: str) -> None:
        self.toast_message = msg
        self.toast_timer = 2.8

    def _open_nav(self) -> None:
        self._execute_fast_nav()

    def _execute_fast_nav(self) -> None:
        if self.state.is_game_over:
            return
        SoundSynthesizer.play("harvest")
        self.state, ok, msg = navigate(self.state, self.current_course, self.current_warp)
        if ok:
            self.show_toast(msg)
            if self.state.is_game_over:
                SoundSynthesizer.play("fanfare" if self.state.victory else "warning")
        else:
            SoundSynthesizer.play("warning")
            self.show_toast(msg)

    def _open_phaser(self) -> None:
        if self.state.is_game_over:
            return
        if not self.state.klingons_in_quadrant:
            SoundSynthesizer.play("warning")
            self.show_toast("No Klingon targets detected in this quadrant!")
            return

        # Fire 400 energy units
        SoundSynthesizer.play("plague")
        self.weapon_anim_timer = 0.5
        self.weapon_anim_type = "PHASER"

        self.state, ok, msg = fire_phasers(self.state, energy_to_fire=self.current_phaser_energy)
        if ok:
            self.show_toast(msg)
            if self.state.is_game_over:
                SoundSynthesizer.play("fanfare" if self.state.victory else "warning")
        else:
            SoundSynthesizer.play("warning")
            self.show_toast(msg)

    def _open_torpedo(self) -> None:
        if self.state.is_game_over:
            return
        if self.state.torpedoes < 1:
            SoundSynthesizer.play("warning")
            self.show_toast("All photon torpedoes expended! Dock at starbase to reload.")
            return

        SoundSynthesizer.play("fanfare")
        self.weapon_anim_timer = 0.5
        self.weapon_anim_type = "TORPEDO"

        self.state, ok, msg = fire_torpedo(self.state, course=self.current_course)
        if ok:
            self.show_toast(msg)
            if self.state.is_game_over:
                SoundSynthesizer.play("fanfare" if self.state.victory else "warning")
        else:
            SoundSynthesizer.play("warning")
            self.show_toast(msg)

    def _open_shields(self) -> None:
        if self.state.is_game_over:
            return
        # Toggle: transfer 200 units into shields, or lower if shields high
        amt = 250.0 if self.state.shields < 1000.0 else -250.0
        SoundSynthesizer.play("click")
        self.state, ok, msg = transfer_shields(self.state, amt)
        if ok:
            self.show_toast(msg)
        else:
            SoundSynthesizer.play("warning")
            self.show_toast(msg)

    def _trigger_lrs(self) -> None:
        if not self.state.is_device_operational(Device.LONG_RANGE_SENSORS):
            SoundSynthesizer.play("warning")
            self.show_toast("Long-range sensors are damaged and offline!")
            return

        SoundSynthesizer.play("click")
        self.active_lrs_scan = long_range_scan(self.state)
        self.show_toast("Long-range sensor scan refreshed (KBS coordinates).")

    def _action_dock(self) -> None:
        self.state, ok, msg = dock_at_starbase(self.state)
        if ok:
            SoundSynthesizer.play("fanfare")
            self.show_toast(msg)
        else:
            SoundSynthesizer.play("warning")
            self.show_toast(msg)

    def handle_event(self, event: pygame.event.Event) -> None:
        canvas_mouse = self._screen_to_canvas(getattr(event, "pos", pygame.mouse.get_pos()))

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
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.show_rules_modal = False
                return
            self.btn_rules_close.handle_event(event, canvas_mouse)
            return

        if self.show_log_modal:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.show_log_modal = False
                return
            self.btn_log_close.handle_event(event, canvas_mouse)
            return

        # Outcome Modal Handling
        if self.state.is_game_over:
            if self.btn_outcome_restart.handle_event(event, canvas_mouse):
                return
            if self.btn_outcome_library.handle_event(event, canvas_mouse):
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r, pygame.K_KP_ENTER):
                    self._restart_mission()
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

        # Command Buttons
        if self.btn_cmd_nav.handle_event(event, canvas_mouse):
            return
        if self.btn_cmd_pha.handle_event(event, canvas_mouse):
            return
        if self.btn_cmd_tor.handle_event(event, canvas_mouse):
            return
        if self.btn_cmd_she.handle_event(event, canvas_mouse):
            return
        if self.btn_cmd_lrs.handle_event(event, canvas_mouse):
            return
        if self.btn_cmd_doc.handle_event(event, canvas_mouse):
            return
        if self.btn_cmd_log.handle_event(event, canvas_mouse):
            return

        # Quick Course Stepper Buttons
        for btn in [
            self.btn_course_e, self.btn_course_ne, self.btn_course_n, self.btn_course_nw,
            self.btn_course_w, self.btn_course_sw, self.btn_course_s, self.btn_course_se,
        ]:
            if btn.handle_event(event, canvas_mouse):
                return

        # Quick Warp Presets
        for btn in [self.btn_warp_imp, self.btn_warp_1, self.btn_warp_2, self.btn_warp_4, self.btn_warp_8, self.btn_exec_nav]:
            if btn.handle_event(event, canvas_mouse):
                return

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._execute_fast_nav()
            elif event.key == pygame.K_n:
                self._open_nav()
            elif event.key == pygame.K_p:
                self._open_phaser()
            elif event.key == pygame.K_t:
                self._open_torpedo()
            elif event.key == pygame.K_s:
                self._open_shields()
            elif event.key == pygame.K_r:
                self._trigger_lrs()
            elif event.key == pygame.K_d:
                self._action_dock()
            elif event.key == pygame.K_l:
                self._toggle_log()
            elif event.key in (pygame.K_F1, pygame.K_m):
                self._toggle_rules()
            elif event.key in (pygame.K_1, pygame.K_KP1):
                self._set_course(1.0)
            elif event.key in (pygame.K_2, pygame.K_KP2):
                self._set_course(2.0)
            elif event.key in (pygame.K_3, pygame.K_KP3):
                self._set_course(3.0)
            elif event.key in (pygame.K_4, pygame.K_KP4):
                self._set_course(4.0)
            elif event.key in (pygame.K_5, pygame.K_KP5):
                self._set_course(5.0)
            elif event.key in (pygame.K_6, pygame.K_KP6):
                self._set_course(6.0)
            elif event.key in (pygame.K_7, pygame.K_KP7):
                self._set_course(7.0)
            elif event.key in (pygame.K_8, pygame.K_KP8):
                self._set_course(8.0)
            elif event.key == pygame.K_ESCAPE:
                self._on_back_clicked()

    def update(self, dt: float) -> None:
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast_message = None

        if self.weapon_anim_timer > 0:
            self.weapon_anim_timer -= dt

        # Update stars
        for s in self.stars:
            s.update(dt)

    def draw(self) -> None:
        # Deep space canvas
        self.canvas.fill((12, 14, 22))

        # Background stars
        for s in self.stars:
            s.draw(self.canvas)

        # 1. Header Bar
        self._draw_header()

        # 2. Left Main Screen: Tactical Short Range Sensor Display
        self._draw_srs_grid()

        # 3. Right Top Screen: Telemetry & Condition Cockpit
        self._draw_telemetry_cockpit()

        # 4. Right Middle Screen: LRS 3x3 Radar & Subsystem Damage Report
        self._draw_lrs_and_subsystems()

        # 5. Bottom Console: Command Buttons & Course Steppers
        self._draw_command_deck()

        # 6. Modals & Overlays
        if self.show_rules_modal:
            self._draw_rules_modal()
        elif self.show_log_modal:
            self._draw_log_modal()
        elif self.state.is_game_over:
            self._draw_outcome_modal()

        # 7. Toast Notification
        self._draw_toast()

    def _draw_header(self) -> None:
        hdr_rect = pygame.Rect(0, 0, BASE_WIDTH, 54)
        pygame.draw.rect(self.canvas, (20, 24, 36), hdr_rect)
        pygame.draw.line(self.canvas, (65, 115, 210), (0, 54), (BASE_WIDTH, 54), 2)

        # Title
        t_surf = FontManager.title(22).render("SUPER STAR TREK", True, Palette.GOLD_LIGHT)
        self.canvas.blit(t_surf, (BASE_WIDTH // 2 - t_surf.get_width() // 2, 7))

        sub_surf = FontManager.small(12).render("STARFLEET COMMAND  •  USS ENTERPRISE NCC-1701", True, (130, 180, 240))
        self.canvas.blit(sub_surf, (BASE_WIDTH // 2 - sub_surf.get_width() // 2, 32))

        self.btn_back.draw(self.canvas)
        self.btn_rules.draw(self.canvas)
        self.btn_restart.draw(self.canvas)

    def _draw_srs_grid(self) -> None:
        """Draws the tactical 8x8 sector radar display."""
        grid_rect = pygame.Rect(25, 68, 615, 470)
        pygame.draw.rect(self.canvas, (16, 20, 32), grid_rect, border_radius=6)
        pygame.draw.rect(self.canvas, (45, 80, 150), grid_rect, width=2, border_radius=6)

        # Title bar of grid
        pygame.draw.rect(self.canvas, (25, 34, 55), (grid_rect.x, grid_rect.y, grid_rect.width, 32), border_top_left_radius=6, border_top_right_radius=6)
        title_txt = f"SHORT-RANGE TACTICAL SCAN  •  {self.state.quadrant_name.upper()} (Q: {self.state.quadrant_x+1},{self.state.quadrant_y+1})"
        t_surf = FontManager.header(13).render(title_txt, True, Palette.GOLD_LIGHT)
        self.canvas.blit(t_surf, (grid_rect.x + 14, grid_rect.y + 8))

        # Draw 8x8 Sector Cells
        cell_size = 50
        origin_x = grid_rect.x + 40
        origin_y = grid_rect.y + 55

        # Sector coordinate numbers (1-8)
        for col in range(SECTOR_WIDTH):
            cx_lbl = FontManager.small(12).render(str(col + 1), True, (110, 150, 200))
            self.canvas.blit(cx_lbl, (origin_x + col * cell_size + 20, origin_y - 18))

        for row in range(SECTOR_HEIGHT):
            cy_lbl = FontManager.small(12).render(str(row + 1), True, (110, 150, 200))
            self.canvas.blit(cy_lbl, (origin_x - 22, origin_y + row * cell_size + 16))

        # Cells
        for sy in range(SECTOR_HEIGHT):
            for sx in range(SECTOR_WIDTH):
                cx = origin_x + sx * cell_size
                cy = origin_y + sy * cell_size
                c_rect = pygame.Rect(cx, cy, cell_size, cell_size)

                # Sector grid line
                pygame.draw.rect(self.canvas, (28, 38, 62), c_rect, width=1)

                # Entity in sector
                ent = self.state.get_sector_entity(sx, sy)
                if ent == SectorEntity.ENTERPRISE:
                    self._draw_enterprise_sprite(c_rect.centerx, c_rect.centery)
                elif ent == SectorEntity.KLINGON:
                    self._draw_klingon_sprite(c_rect.centerx, c_rect.centery, sx, sy)
                elif ent == SectorEntity.STARBASE:
                    self._draw_starbase_sprite(c_rect.centerx, c_rect.centery)
                elif ent == SectorEntity.STAR:
                    self._draw_star_sprite(c_rect.centerx, c_rect.centery)

        # Weapon fire animation overlay
        if self.weapon_anim_timer > 0:
            ex = origin_x + self.state.sector_x * cell_size + cell_size // 2
            ey = origin_y + self.state.sector_y * cell_size + cell_size // 2

            if self.weapon_anim_type == "PHASER":
                for k in self.state.klingons_in_quadrant:
                    kx = origin_x + k.sector_x * cell_size + cell_size // 2
                    ky = origin_y + k.sector_y * cell_size + cell_size // 2
                    pygame.draw.line(self.canvas, (255, 230, 80), (ex, ey), (kx, ky), 3)
            elif self.weapon_anim_type == "TORPEDO":
                dx, dy = (math.cos((self.current_course - 1.0) * math.pi / 4.0), -math.sin((self.current_course - 1.0) * math.pi / 4.0))
                tx = ex + int(dx * 180)
                ty = ey + int(dy * 180)
                pygame.draw.line(self.canvas, (240, 60, 60), (ex, ey), (tx, ty), 4)
                pygame.draw.circle(self.canvas, (255, 200, 200), (tx, ty), 6)

    def _draw_enterprise_sprite(self, cx: int, cy: int) -> None:
        # Primary Saucer
        pygame.draw.circle(self.canvas, (180, 215, 255), (cx, cy - 2), 11)
        pygame.draw.circle(self.canvas, (90, 140, 220), (cx, cy - 2), 11, 2)
        # Bridge dome
        pygame.draw.circle(self.canvas, Palette.GOLD_LIGHT, (cx, cy - 2), 3)
        # Engineering Hull
        pygame.draw.rect(self.canvas, (140, 175, 225), (cx - 3, cy + 3, 6, 11), border_radius=2)
        # Warp Nacelles (Left and Right)
        pygame.draw.rect(self.canvas, (65, 115, 210), (cx - 13, cy + 2, 4, 14), border_radius=2)
        pygame.draw.rect(self.canvas, (65, 115, 210), (cx + 9, cy + 2, 4, 14), border_radius=2)
        # Bussard Collectors (Red tips)
        pygame.draw.circle(self.canvas, Palette.CRIMSON_LIGHT, (cx - 11, cy + 2), 2)
        pygame.draw.circle(self.canvas, Palette.CRIMSON_LIGHT, (cx + 11, cy + 2), 2)

    def _draw_klingon_sprite(self, cx: int, cy: int, sx: int, sy: int) -> None:
        # Menacing D7 Battlecruiser
        # Forward command pod
        pygame.draw.circle(self.canvas, (200, 50, 50), (cx, cy - 6), 7)
        # Neck
        pygame.draw.line(self.canvas, (160, 40, 40), (cx, cy - 6), (cx, cy + 4), 3)
        # Main wing crossbar
        pygame.draw.polygon(self.canvas, (170, 45, 45), [
            (cx, cy + 3),
            (cx - 14, cy + 10),
            (cx - 12, cy + 14),
            (cx + 12, cy + 14),
            (cx + 14, cy + 10),
        ])
        # Warp engines
        pygame.draw.rect(self.canvas, (100, 25, 25), (cx - 15, cy + 8, 4, 8))
        pygame.draw.rect(self.canvas, (100, 25, 25), (cx + 11, cy + 8, 4, 8))

        # Health bar above Klingon
        for k in self.state.klingons_in_quadrant:
            if k.sector_x == sx and k.sector_y == sy and k.is_alive:
                pct = max(0.0, k.shields / max(1.0, k.max_shields))
                pygame.draw.rect(self.canvas, (40, 20, 20), (cx - 14, cy - 18, 28, 4))
                pygame.draw.rect(self.canvas, Palette.CRIMSON_LIGHT, (cx - 14, cy - 18, int(28 * pct), 4))
                break

    def _draw_starbase_sprite(self, cx: int, cy: int) -> None:
        # Federation Spacedock / Starbase Ring
        pygame.draw.circle(self.canvas, Palette.GOLD_LIGHT, (cx, cy), 13, 2)
        pygame.draw.circle(self.canvas, (80, 160, 240), (cx, cy), 6)
        # Solar arrays / docking pylons
        pygame.draw.line(self.canvas, Palette.GOLD_PALE, (cx - 16, cy), (cx + 16, cy), 2)
        pygame.draw.line(self.canvas, Palette.GOLD_PALE, (cx, cy - 16), (cx, cy + 16), 2)

    def _draw_star_sprite(self, cx: int, cy: int) -> None:
        # Twinkling 4-point yellow star flare
        pygame.draw.line(self.canvas, Palette.GOLD_PALE, (cx - 8, cy), (cx + 8, cy), 2)
        pygame.draw.line(self.canvas, Palette.GOLD_PALE, (cx, cy - 8), (cx, cy + 8), 2)
        pygame.draw.circle(self.canvas, (255, 255, 220), (cx, cy), 3)

    def _draw_telemetry_cockpit(self) -> None:
        """Top right panel showing ship conditions, energy, shields, and torpedoes."""
        card_rect = pygame.Rect(655, 68, 600, 240)
        pygame.draw.rect(self.canvas, (16, 20, 32), card_rect, border_radius=6)
        pygame.draw.rect(self.canvas, (45, 80, 150), card_rect, width=2, border_radius=6)

        # Header
        pygame.draw.rect(self.canvas, (25, 34, 55), (card_rect.x, card_rect.y, card_rect.width, 32), border_top_left_radius=6, border_top_right_radius=6)
        hdr_txt = FontManager.header(13).render("TACTICAL SHIP TELEMETRY & RESOURCES", True, Palette.GOLD_LIGHT)
        self.canvas.blit(hdr_txt, (card_rect.x + 14, card_rect.y + 8))

        # Stardate & Condition Tag
        stardate_txt = f"STARDATE: {self.state.stardate:.1f}  (Time Left: {self.state.days_remaining:.1f} days)"
        s_surf = FontManager.body(13).render(stardate_txt, True, Palette.TEXT_TITLE)
        self.canvas.blit(s_surf, (card_rect.x + 18, card_rect.y + 44))

        # Condition Badge
        cond = self.state.condition
        cond_col = Palette.SUCCESS_GREEN if cond == ShipCondition.GREEN else (
            Palette.GOLD_LIGHT if cond == ShipCondition.YELLOW else (
                Palette.CRIMSON_LIGHT if cond == ShipCondition.RED else (80, 180, 240)
            )
        )
        badge_rect = pygame.Rect(card_rect.right - 145, card_rect.y + 40, 125, 26)
        pygame.draw.rect(self.canvas, cond_col, badge_rect, border_radius=4)
        c_txt = FontManager.header(12).render(f"COND: {cond.value}", True, (15, 20, 30))
        self.canvas.blit(c_txt, (badge_rect.centerx - c_txt.get_width() // 2, badge_rect.y + 5))

        # Energy Bar (0-3000)
        ey = card_rect.y + 80
        lbl_e = FontManager.small(12).render(f"ENERGY RESERVES: {int(self.state.energy)} / {int(MAX_ENERGY)}", True, Palette.TEXT_MUTED)
        self.canvas.blit(lbl_e, (card_rect.x + 18, ey))

        e_pct = max(0.0, min(1.0, self.state.energy / MAX_ENERGY))
        bar_w = 400
        pygame.draw.rect(self.canvas, (25, 30, 45), (card_rect.x + 18, ey + 18, bar_w, 14), border_radius=3)
        if e_pct > 0:
            e_col = Palette.SUCCESS_GREEN if e_pct > 0.4 else (Palette.AMBER_WARN if e_pct > 0.2 else Palette.CRIMSON_LIGHT)
            pygame.draw.rect(self.canvas, e_col, (card_rect.x + 18, ey + 18, int(bar_w * e_pct), 14), border_radius=3)
        pygame.draw.rect(self.canvas, (65, 115, 210), (card_rect.x + 18, ey + 18, bar_w, 14), width=1, border_radius=3)

        # Deflector Shields Bar (0-1500)
        sy = card_rect.y + 124
        lbl_s = FontManager.small(12).render(f"DEFLECTOR SHIELDS: {int(self.state.shields)} / {int(MAX_SHIELDS)}", True, Palette.TEXT_MUTED)
        self.canvas.blit(lbl_s, (card_rect.x + 18, sy))

        s_pct = max(0.0, min(1.0, self.state.shields / MAX_SHIELDS))
        pygame.draw.rect(self.canvas, (25, 30, 45), (card_rect.x + 18, sy + 18, bar_w, 14), border_radius=3)
        if s_pct > 0:
            s_col = (80, 160, 240) if s_pct > 0.4 else (Palette.AMBER_WARN if s_pct > 0.2 else Palette.CRIMSON_LIGHT)
            pygame.draw.rect(self.canvas, s_col, (card_rect.x + 18, sy + 18, int(bar_w * s_pct), 14), border_radius=3)
        pygame.draw.rect(self.canvas, (65, 115, 210), (card_rect.x + 18, sy + 18, bar_w, 14), width=1, border_radius=3)

        # Torpedo Tubes & Mission Targets
        ty = card_rect.y + 172
        torp_txt = f"PHOTON TORPEDOES: {self.state.torpedoes} / {MAX_TORPEDOES}"
        self.canvas.blit(FontManager.small(12).render(torp_txt, True, Palette.TEXT_MUTED), (card_rect.x + 18, ty))
        # Torpedo icons
        for i in range(MAX_TORPEDOES):
            col = Palette.CRIMSON_LIGHT if i < self.state.torpedoes else (40, 50, 70)
            pygame.draw.circle(self.canvas, col, (card_rect.x + 220 + i * 16, ty + 7), 5)

        # Mission summary
        my = card_rect.y + 200
        ms_txt = f"KLINGONS IN GALAXY: {self.state.total_klingons_remaining}  •  STARBASES: {self.state.total_starbases_remaining}  •  LOCATION: Sector {self.state.sector_x+1},{self.state.sector_y+1}"
        self.canvas.blit(FontManager.body(12).render(ms_txt, True, Palette.GOLD_PALE), (card_rect.x + 18, my))

    def _draw_lrs_and_subsystems(self) -> None:
        """Right middle panel showing Long Range Sensor radar and Subsystems."""
        pnl_rect = pygame.Rect(655, 318, 600, 220)
        pygame.draw.rect(self.canvas, (16, 20, 32), pnl_rect, border_radius=6)
        pygame.draw.rect(self.canvas, (45, 80, 150), pnl_rect, width=2, border_radius=6)

        # Header
        pygame.draw.rect(self.canvas, (25, 34, 55), (pnl_rect.x, pnl_rect.y, pnl_rect.width, 32), border_top_left_radius=6, border_top_right_radius=6)
        hdr_txt = FontManager.header(13).render("LONG-RANGE RADAR (LRS)  &  SUBSYSTEM DIAGNOSTICS", True, Palette.GOLD_LIGHT)
        self.canvas.blit(hdr_txt, (pnl_rect.x + 14, pnl_rect.y + 8))

        # Left subpanel: LRS 3x3 Radar Grid
        rx = pnl_rect.x + 20
        ry = pnl_rect.y + 46
        lbl_radar = FontManager.small(11).render("LRS SCAN (KBS: Klingons Bases Stars)", True, (130, 180, 240))
        self.canvas.blit(lbl_radar, (rx, ry))

        # Get or compute 3x3 scan
        scan = self.active_lrs_scan or long_range_scan(self.state)
        cell_w, cell_h = 58, 38
        for r_idx, row in enumerate(scan):
            for c_idx, (k, b, s) in enumerate(row):
                box_x = rx + c_idx * cell_w
                box_y = ry + 22 + r_idx * cell_h
                b_rect = pygame.Rect(box_x, box_y, cell_w, cell_h)

                is_center = (r_idx == 1 and c_idx == 1)
                bg_col = (35, 48, 80) if is_center else (22, 28, 44)
                border_col = Palette.GOLD_LIGHT if is_center else (45, 65, 105)

                pygame.draw.rect(self.canvas, bg_col, b_rect)
                pygame.draw.rect(self.canvas, border_col, b_rect, width=1)

                code_str = f"{k}{b}{s}" if k >= 0 else "***"
                code_col = Palette.CRIMSON_LIGHT if k > 0 else (Palette.GOLD_LIGHT if b > 0 else Palette.TEXT_TITLE)
                c_surf = FontManager.mono(14).render(code_str, True, code_col)
                self.canvas.blit(c_surf, (b_rect.centerx - c_surf.get_width() // 2, b_rect.centery - c_surf.get_height() // 2))

        # Right subpanel: Subsystem Damage Table
        dx = pnl_rect.x + 235
        dy = pnl_rect.y + 46
        lbl_sys = FontManager.small(11).render("SUBSYSTEM OPERATIONAL STATUS", True, (130, 180, 240))
        self.canvas.blit(lbl_sys, (dx, dy))

        devices = [
            (Device.WARP_ENGINES, "Warp Engines (NAV)"),
            (Device.SHORT_RANGE_SENSORS, "Short-Range Sensors (SRS)"),
            (Device.LONG_RANGE_SENSORS, "Long-Range Sensors (LRS)"),
            (Device.PHASER_CONTROL, "Phaser Banks (PHA)"),
            (Device.PHOTON_TUBES, "Photon Torpedo Tubes (TOR)"),
            (Device.SHIELD_CONTROL, "Deflector Shields (SHE)"),
            (Device.COMPUTER, "Library Computer (COM)"),
        ]

        curr_y = dy + 22
        for dev, name in devices:
            is_ok = self.state.is_device_operational(dev)
            status_txt = "OPERATIONAL" if is_ok else f"OFFLINE ({self.state.devices[dev]:.1f}d)"
            status_col = Palette.SUCCESS_GREEN if is_ok else Palette.CRIMSON_LIGHT

            n_surf = FontManager.small(11).render(name, True, Palette.TEXT_TITLE)
            s_surf = FontManager.small(11).render(status_txt, True, status_col)

            self.canvas.blit(n_surf, (dx, curr_y))
            self.canvas.blit(s_surf, (dx + 230, curr_y))
            curr_y += 19

    def _draw_command_deck(self) -> None:
        """Draws the bottom command buttons and quick course/warp bars."""
        # Row 1: Action Commands
        self.btn_cmd_nav.draw(self.canvas)
        self.btn_cmd_pha.draw(self.canvas)
        self.btn_cmd_tor.draw(self.canvas)
        self.btn_cmd_she.draw(self.canvas)
        self.btn_cmd_lrs.draw(self.canvas)
        self.btn_cmd_doc.draw(self.canvas)
        self.btn_cmd_log.draw(self.canvas)

        # Row 2: Course & Warp Steppers
        lbl_crs = FontManager.small(11).render(f"COURSE: {self.current_course:.0f} ({self._heading_name(self.current_course)})", True, Palette.GOLD_PALE)
        self.canvas.blit(lbl_crs, (25, 600))

        lbl_wrp = FontManager.small(11).render(f"WARP FACTOR: {self.current_warp:.1f}", True, Palette.GOLD_PALE)
        self.canvas.blit(lbl_wrp, (630, 600))

        self.btn_course_e.draw(self.canvas)
        self.btn_course_ne.draw(self.canvas)
        self.btn_course_n.draw(self.canvas)
        self.btn_course_nw.draw(self.canvas)
        self.btn_course_w.draw(self.canvas)
        self.btn_course_sw.draw(self.canvas)
        self.btn_course_s.draw(self.canvas)
        self.btn_course_se.draw(self.canvas)

        self.btn_warp_imp.draw(self.canvas)
        self.btn_warp_1.draw(self.canvas)
        self.btn_warp_2.draw(self.canvas)
        self.btn_warp_4.draw(self.canvas)
        self.btn_warp_8.draw(self.canvas)
        self.btn_exec_nav.draw(self.canvas)

    def _draw_rules_modal(self) -> None:
        """Starfleet manual overlay."""
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 220))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 880, 590
        px, py = (BASE_WIDTH - pw) // 2, (BASE_HEIGHT - ph) // 2
        pnl = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, (18, 24, 38), pnl, border_radius=8)
        pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT, pnl, width=2, border_radius=8)

        title = FontManager.title(20).render("STARFLEET COMMAND STRATEGIC OPERATIONS MANUAL", True, Palette.GOLD_LIGHT)
        self.canvas.blit(title, (pnl.centerx - title.get_width() // 2, py + 22))

        rules = [
            ("HISTORICAL ORIGIN (1971 / 1974 MAYFIELD, AHL & LEEDOM):", Palette.GOLD_BASE, True),
            ("Created in 1971 by Mike Mayfield and expanded into Super Star Trek by David H. Ahl & Bob Leedom (1974).", Palette.SAND_LIGHT, False),
            ("Published in Creative Computing and BASIC Computer Games (1978, pp. 157-163).", Palette.SAND_LIGHT, False),
            ("", Palette.TEXT_MUTED, False),
            ("GALAXY & TACTICAL NAVIGATION:", Palette.GOLD_BASE, True),
            ("• The galaxy contains 64 Quadrants (8x8 grid). Each quadrant contains 64 Sectors (8x8 grid).", Palette.SAND_LIGHT, False),
            ("• Course direction runs from 1 to 8: 1=East, 2=NE, 3=North, 4=NW, 5=West, 6=SW, 7=South, 8=SE.", Palette.SAND_LIGHT, False),
            ("• Warp < 1.0 (e.g. Warp 0.2) moves within sector. Warp >= 1.0 travels across neighboring quadrants.", Palette.SAND_LIGHT, False),
            ("", Palette.TEXT_MUTED, False),
            ("WEAPONS SYSTEMS & COMBAT:", Palette.GOLD_BASE, True),
            ("• PHASERS: Discharges energy divided evenly among all Klingons in quadrant; hits attenuate by distance.", Palette.SAND_LIGHT, False),
            ("• TORPEDOES: Fires high-yield photon torpedoes along straight-line course. Destroys Klingon on direct hit.", Palette.SAND_LIGHT, False),
            ("• SHIELDS: Deflectors absorb Klingon counterattack disruptors. Transfer energy between supply and shields.", Palette.SAND_LIGHT, False),
            ("• STARBASE DOCKING: When adjacent to Starbase (>!<), docking restores full 3000 energy, 10 torpedoes, and repairs.", Palette.SUCCESS_GREEN, False),
        ]

        curr_y = py + 65
        for text, col, is_bold in rules:
            if text:
                f = FontManager.header(14) if is_bold else FontManager.small(12)
                s = f.render(text, True, col)
                self.canvas.blit(s, (px + 40, curr_y))
            curr_y += 22

        self.btn_rules_close.draw(self.canvas)

    def _draw_log_modal(self) -> None:
        """Starfleet mission log chronicle."""
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 220))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 840, 560
        px, py = (BASE_WIDTH - pw) // 2, (BASE_HEIGHT - ph) // 2
        pnl = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, (18, 24, 38), pnl, border_radius=8)
        pygame.draw.rect(self.canvas, (45, 80, 150), pnl, width=2, border_radius=8)

        title = FontManager.title(18).render("STARFLEET CAPTAIN'S LOG & COMBAT CHRONICLE", True, Palette.GOLD_LIGHT)
        self.canvas.blit(title, (pnl.centerx - title.get_width() // 2, py + 25))

        entries = self.state.history_log[-14:] if self.state.history_log else ["No entries recorded."]
        curr_y = py + 70
        for entry in entries:
            e_surf = FontManager.small(12).render(f"•  {entry}", True, Palette.TEXT_BODY)
            self.canvas.blit(e_surf, (px + 40, curr_y))
            curr_y += 28

        self.btn_log_close.draw(self.canvas)

    def _draw_outcome_modal(self) -> None:
        """Mission complete or defeat scorecard."""
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 18, 230))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 760, 480
        px, py = (BASE_WIDTH - pw) // 2, (BASE_HEIGHT - ph) // 2
        pnl = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, (18, 24, 38), pnl, border_radius=8)
        pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT if self.state.victory else Palette.CRIMSON_LIGHT, pnl, width=2, border_radius=8)

        if self.state.victory:
            title_text = "FEDERATION VICTORY! MISSION ACCOMPLISHED!"
            title_col = Palette.SUCCESS_GREEN
            score = calculate_score(self.state)
            desc_lines = [
                "All Klingon battlecruisers in the galaxy have been destroyed!",
                f"Mission completed on Stardate {self.state.stardate:.1f} ({self.state.days_remaining:.1f} days ahead of deadline).",
                f"Remaining energy reserves: {int(self.state.energy)} units  •  Starbases preserved: {self.state.total_starbases_remaining}",
                f"FINAL STARFLEET COMMAND RATING: {score:,} POINTS",
            ]
        else:
            title_text = "MISSION FAILED! USS ENTERPRISE LOST!"
            title_col = Palette.CRIMSON_LIGHT
            reason = self.state.game_over_reason or "The Enterprise was unable to complete the mission."
            desc_lines = [
                reason,
                f"Stardate reached: {self.state.stardate:.1f} / {self.state.stardate_limit:.1f}",
                f"Klingon battlecruisers surviving in galaxy: {self.state.total_klingons_remaining}",
                "Starfleet Command has recorded your honorable service in the archives.",
            ]

        title_surf = FontManager.title(20).render(title_text, True, title_col)
        self.canvas.blit(title_surf, (pnl.centerx - title_surf.get_width() // 2, py + 35))

        curr_y = py + 110
        for line in desc_lines:
            f = FontManager.header(15) if "FINAL STARFLEET COMMAND RATING" in line else FontManager.body(14)
            col = Palette.GOLD_LIGHT if "FINAL STARFLEET COMMAND RATING" in line else Palette.TEXT_BODY
            s = f.render(line, True, col)
            self.canvas.blit(s, (pnl.centerx - s.get_width() // 2, curr_y))
            curr_y += 38

        self.btn_outcome_restart.draw(self.canvas)
        self.btn_outcome_library.draw(self.canvas)

    def _draw_toast(self) -> None:
        if not self.toast_message:
            return
        surf = FontManager.body(14).render(self.toast_message, True, Palette.TEXT_TITLE)
        tw = surf.get_width() + 40
        th = 38
        tx = (BASE_WIDTH - tw) // 2
        ty = BASE_HEIGHT - 55
        pygame.draw.rect(self.canvas, (20, 26, 42), (tx, ty, tw, th), border_radius=6)
        pygame.draw.rect(self.canvas, (65, 115, 210), (tx, ty, tw, th), width=2, border_radius=6)
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
    app = TrekApp()
    app.run()
