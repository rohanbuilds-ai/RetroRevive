"""
games/hunt_the_wumpus/app.py - Pygame desktop application for Hunt the Wumpus (1973/1978).

Features:
- Cavern chamber perspective with 3 tunnel archway portals
- Real-time Planar Schlegel Projection Map of the 20-vertex Dodecahedron
- Live sensory warning indicators: Smell Wumpus, Feel Draft, Hear Bats
- Interactive Crooked Arrow Path Planner (1 to 5 chained rooms)
- Atmospheric particle torch flickers & audio synthesis
- Single-window lifecycle with seamless return to RetroRevive platform library
"""

import math
import os
import random
import sys
from typing import Callable, List, Optional, Tuple

import pygame

from games.hunt_the_wumpus import engine
from ui_theme import CRTEffect, FontManager, Palette, SoundSynthesizer, UIButton


BASE_WIDTH = 1280
BASE_HEIGHT = 720


class TorchFlame:
    """Procedural flickering torch ember in the cavern."""

    def __init__(self, x: float, y: float) -> None:
        self.base_x = x
        self.base_y = y
        self.reset()

    def reset(self) -> None:
        self.x = self.base_x + random.uniform(-6, 6)
        self.y = self.base_y + random.uniform(-4, 4)
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-30, -12)
        self.life = random.uniform(0.3, 0.8)
        self.max_life = self.life
        self.size = random.uniform(3.0, 7.0)

    def update(self, dt: float) -> None:
        self.life -= dt
        if self.life <= 0:
            self.reset()
        else:
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.size = max(1.0, self.size - 4.0 * dt)

    def draw(self, surface: pygame.Surface) -> None:
        progress = max(0.0, self.life / self.max_life)
        if progress > 0.6:
            color = (255, 230, 110)
        elif progress > 0.3:
            color = (245, 140, 40)
        else:
            color = (200, 50, 20)
        alpha = int(220 * progress)
        dot_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(dot_surf, (*color, alpha), (int(self.size), int(self.size)), int(self.size))
        surface.blit(dot_surf, (int(self.x - self.size), int(self.y - self.size)))


class WumpusApp:
    """Hunt the Wumpus graphical desktop application controller."""

    def __init__(
        self,
        shared_window: Optional[pygame.Surface] = None,
        on_exit_to_library: Optional[Callable[[], None]] = None,
        start_fullscreen: bool = False,
    ) -> None:
        self.on_exit_to_library = on_exit_to_library

        if shared_window is not None:
            self.window = shared_window
            self.screen_width = shared_window.get_width()
            self.screen_height = shared_window.get_height()
        else:
            flags = pygame.FULLSCREEN if start_fullscreen else pygame.RESIZABLE
            info = pygame.display.Info()
            self.screen_width = info.current_w if start_fullscreen else BASE_WIDTH
            self.screen_height = info.current_h if start_fullscreen else BASE_HEIGHT
            self.window = pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                flags,
            )
            pygame.display.set_caption("RetroRevive — Hunt the Wumpus (1973/1978)")

        self.canvas = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        self.clock = pygame.time.Clock()
        self.is_running = True

        # Core Game State
        self.state: engine.WumpusState = engine.init_game()
        self.selected_arrow_path: List[int] = []
        self.arrow_anim_timer: float = 0.0
        self.arrow_anim_path: List[int] = []

        # Visual / Modals
        self.show_rules_modal = False
        self.show_log_modal = False
        self.show_outcome_modal = False
        self.toast_message: Optional[str] = None
        self.toast_timer: float = 0.0
        self.anim_pulse_timer: float = 0.0

        # Torches
        self.torches: List[TorchFlame] = [
            TorchFlame(120, 260) for _ in range(12)
        ] + [TorchFlame(530, 260) for _ in range(12)]

        self._init_buttons()

    def _init_buttons(self) -> None:
        btn_y = 12
        self.btn_back = UIButton((18, btn_y, 110, 36), "← LIBRARY", self._on_back_clicked, color_scheme="sand", font_size=13)
        self.btn_rules = UIButton((136, btn_y, 130, 36), "CAVERN RULES", self._toggle_rules, color_scheme="lapis", font_size=13)
        self.btn_log = UIButton((274, btn_y, 110, 36), "JOURNAL", self._toggle_log, color_scheme="sand", font_size=13)
        self.btn_restart = UIButton((392, btn_y, 110, 36), "RESTART", self._restart_game, color_scheme="crimson", font_size=13)

        # Tunnel Archway Action Buttons (Left pane)
        self.btn_tunnel_1 = UIButton((40, 380, 160, 46), "TUNNEL 1", lambda: self._traverse_tunnel(0), primary=True, font_size=15)
        self.btn_tunnel_2 = UIButton((230, 380, 160, 46), "TUNNEL 2", lambda: self._traverse_tunnel(1), primary=True, font_size=15)
        self.btn_tunnel_3 = UIButton((420, 380, 160, 46), "TUNNEL 3", lambda: self._traverse_tunnel(2), primary=True, font_size=15)

        # Crooked Arrow Actions
        self.btn_shoot_arrow = UIButton((40, 650, 220, 46), "SHOOT ARROW", self._execute_shoot_arrow, color_scheme="crimson", font_size=15)
        self.btn_clear_arrow = UIButton((270, 650, 140, 46), "CLEAR PATH", self._clear_arrow_path, color_scheme="sand", font_size=14)

        # Modal close buttons
        self.btn_rules_close = UIButton((580, 610, 120, 40), "CLOSE", self._toggle_rules, color_scheme="gold", font_size=14)
        self.btn_log_close = UIButton((580, 610, 120, 40), "CLOSE", self._toggle_log, color_scheme="sand", font_size=14)
        self.btn_outcome_restart = UIButton((460, 520, 160, 44), "EXPLORE AGAIN", self._restart_game, primary=True, font_size=14)
        self.btn_outcome_library = UIButton((650, 520, 160, 44), "RETURN TO HUB", self._on_back_clicked, color_scheme="sand", font_size=14)

    def _on_back_clicked(self) -> None:
        self.is_running = False
        if self.on_exit_to_library:
            self.on_exit_to_library()

    def _toggle_rules(self) -> None:
        self.show_rules_modal = not self.show_rules_modal
        if self.show_rules_modal:
            self.show_log_modal = False
            self.show_outcome_modal = False

    def _toggle_log(self) -> None:
        self.show_log_modal = not self.show_log_modal
        if self.show_log_modal:
            self.show_rules_modal = False
            self.show_outcome_modal = False

    def _restart_game(self) -> None:
        self.state = engine.init_game()
        self.selected_arrow_path.clear()
        self.arrow_anim_timer = 0.0
        self.arrow_anim_path.clear()
        self.show_rules_modal = False
        self.show_log_modal = False
        self.show_outcome_modal = False
        self.show_toast("Caverns re-generated! Good hunting, explorer.")
        SoundSynthesizer.play("fanfare")

    def show_toast(self, msg: str) -> None:
        self.toast_message = msg
        self.toast_timer = 2.5

    def _traverse_tunnel(self, tunnel_idx: int) -> None:
        if self.state.is_game_over:
            return
        tunnels = engine.DODECAHEDRON_ROOMS[self.state.hunter_room]
        if 0 <= tunnel_idx < len(tunnels):
            target = tunnels[tunnel_idx]
            res = engine.move_hunter(self.state, target)
            self.show_toast(res.message)
            if res.bat_transported:
                SoundSynthesizer.play("warning")
            elif self.state.is_game_over:
                self.show_outcome_modal = True
                SoundSynthesizer.play("victory" if self.state.victory else "defeat")
            else:
                SoundSynthesizer.play("thrust")

    def _add_room_to_arrow_path(self, room: int) -> None:
        if self.state.is_game_over:
            return
        if len(self.selected_arrow_path) >= 5:
            self.show_toast("Maximum 5 rooms per crooked arrow shot!")
            return
        self.selected_arrow_path.append(room)
        SoundSynthesizer.play("click")

    def _clear_arrow_path(self) -> None:
        self.selected_arrow_path.clear()
        SoundSynthesizer.play("click")

    def _execute_shoot_arrow(self) -> None:
        if self.state.is_game_over:
            return
        if not self.selected_arrow_path:
            self.show_toast("Select at least 1 room on the map or click adjacent rooms!")
            return

        self.arrow_anim_timer = 0.65
        self.arrow_anim_path = [self.state.hunter_room] + list(self.selected_arrow_path)
        SoundSynthesizer.play("laser")

        res = engine.shoot_arrow(self.state, self.selected_arrow_path)
        self.show_toast(res.message)
        self.selected_arrow_path.clear()

        if self.state.is_game_over:
            self.show_outcome_modal = True
            SoundSynthesizer.play("victory" if self.state.victory else "defeat")

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.is_running = False
            return

        if event.type == pygame.VIDEORESIZE:
            self.screen_width = event.w
            self.screen_height = event.h
            self.window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            return

        # Handle modals
        if self.show_rules_modal:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_m):
                self._toggle_rules()
                return
            if self.btn_rules_close.handle_event(event):
                return
            return

        if self.show_log_modal:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_l):
                self._toggle_log()
                return
            if self.btn_log_close.handle_event(event):
                return
            return

        if self.show_outcome_modal:
            if self.btn_outcome_restart.handle_event(event):
                return
            if self.btn_outcome_library.handle_event(event):
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._restart_game()
                return
            return

        # Global Hotkeys
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2:
                CRTEffect.toggle()
                return
            elif event.key == pygame.K_F3:
                SoundSynthesizer.set_enabled(not SoundSynthesizer._enabled)
                return
            elif event.key == pygame.K_ESCAPE:
                self._on_back_clicked()
                return
            elif event.key == pygame.K_m:
                self._toggle_rules()
                return
            elif event.key == pygame.K_l:
                self._toggle_log()
                return
            elif event.key == pygame.K_r:
                self._restart_game()
                return
            elif event.key in (pygame.K_1, pygame.K_KP1):
                self._traverse_tunnel(0)
                return
            elif event.key in (pygame.K_2, pygame.K_KP2):
                self._traverse_tunnel(1)
                return
            elif event.key in (pygame.K_3, pygame.K_KP3):
                self._traverse_tunnel(2)
                return
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._execute_shoot_arrow()
                return
            elif event.key == pygame.K_c:
                self._clear_arrow_path()
                return

        # Click on Schlegel map rooms to add to arrow path
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cx, cy = self._screen_to_canvas(event.pos)
            map_rect = pygame.Rect(630, 80, 610, 530)
            if map_rect.collidepoint(cx, cy):
                for r_id, (rx, ry) in engine.DODECAHEDRON_COORDS.items():
                    node_cx = map_rect.x + int(rx * map_rect.width)
                    node_cy = map_rect.y + int(ry * map_rect.height)
                    dist = math.hypot(cx - node_cx, cy - node_cy)
                    if dist <= 18:
                        # If it's adjacent to current room, player can move or add to arrow path!
                        self._add_room_to_arrow_path(r_id)
                        return

        # UI Buttons
        self.btn_back.handle_event(event)
        self.btn_rules.handle_event(event)
        self.btn_log.handle_event(event)
        self.btn_restart.handle_event(event)
        self.btn_tunnel_1.handle_event(event)
        self.btn_tunnel_2.handle_event(event)
        self.btn_tunnel_3.handle_event(event)
        self.btn_shoot_arrow.handle_event(event)
        self.btn_clear_arrow.handle_event(event)

    def update(self, dt: float) -> None:
        self.anim_pulse_timer += dt
        if self.toast_timer > 0.0:
            self.toast_timer = max(0.0, self.toast_timer - dt)
            if self.toast_timer <= 0.0:
                self.toast_message = None

        if self.arrow_anim_timer > 0.0:
            self.arrow_anim_timer = max(0.0, self.arrow_anim_timer - dt)

        for torch in self.torches:
            torch.update(dt)

        # Update dynamic tunnel button text
        tunnels = engine.DODECAHEDRON_ROOMS[self.state.hunter_room]
        self.btn_tunnel_1.text = f"[1] ROOM {tunnels[0]}"
        self.btn_tunnel_2.text = f"[2] ROOM {tunnels[1]}"
        self.btn_tunnel_3.text = f"[3] ROOM {tunnels[2]}"

    def draw(self) -> None:
        self.canvas.fill(Palette.BG_DARK)

        # Draw cavern background textures
        self._draw_header()
        self._draw_cavern_chamber()
        self._draw_sensory_warnings()
        self._draw_dodecahedron_map()
        self._draw_arrow_path_deck()

        # Torches
        for torch in self.torches:
            torch.draw(self.canvas)

        # Modals
        if self.show_rules_modal:
            self._draw_rules_modal()
        elif self.show_log_modal:
            self._draw_log_modal()
        elif self.show_outcome_modal:
            self._draw_outcome_modal()

        if self.toast_message:
            self._draw_toast()

        self._present()

    def _draw_header(self) -> None:
        header_rect = pygame.Rect(0, 0, BASE_WIDTH, 60)
        pygame.draw.rect(self.canvas, Palette.BG_DARK, header_rect)
        pygame.draw.line(self.canvas, Palette.GOLD_BASE, (0, 60), (BASE_WIDTH, 60), 2)

        self.btn_back.draw(self.canvas)
        self.btn_rules.draw(self.canvas)
        self.btn_log.draw(self.canvas)
        self.btn_restart.draw(self.canvas)

        title_surf = FontManager.title(22).render("HUNT THE WUMPUS", True, Palette.AMBER_WARN)
        self.canvas.blit(title_surf, (520, 10))

        sub_surf = FontManager.small(13).render("Gregory Yob (1973/1978) — Cavern of the Dodecahedron", True, Palette.TEXT_MUTED)
        self.canvas.blit(sub_surf, (520, 34))

        # Arrows status badge
        arrows_bg = pygame.Rect(1080, 12, 180, 36)
        pygame.draw.rect(self.canvas, Palette.BG_DARK, arrows_bg, border_radius=6)
        pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT, arrows_bg, width=1, border_radius=6)

        arrow_icon = "🏹"
        arrow_txt = f"{arrow_icon} ARROWS: {self.state.arrows}/5"
        arrow_surf = FontManager.header(16).render(arrow_txt, True, Palette.GOLD_LIGHT)
        self.canvas.blit(arrow_surf, (arrows_bg.x + 16, arrows_bg.y + 8))

    def _draw_cavern_chamber(self) -> None:
        """Draw the left cavern perspective chamber with archway portals."""
        chamber_rect = pygame.Rect(20, 75, 590, 375)
        pygame.draw.rect(self.canvas, (18, 22, 28), chamber_rect, border_radius=10)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, chamber_rect, width=1, border_radius=10)

        # Stone arch frame
        arch_pts = [
            (chamber_rect.left + 50, chamber_rect.bottom - 40),
            (chamber_rect.left + 50, chamber_rect.top + 100),
            (chamber_rect.centerx, chamber_rect.top + 30),
            (chamber_rect.right - 50, chamber_rect.top + 100),
            (chamber_rect.right - 50, chamber_rect.bottom - 40),
        ]
        pygame.draw.lines(self.canvas, (65, 75, 90), False, arch_pts, 4)

        # Current Room Header
        room_title = f"CAVERN CHAMBER {self.state.hunter_room}"
        r_surf = FontManager.title(26).render(room_title, True, Palette.GOLD_LIGHT)
        self.canvas.blit(r_surf, (chamber_rect.centerx - r_surf.get_width() // 2, chamber_rect.top + 50))

        desc = "Dark basalt passages stretch outwards into the subterranean depths."
        desc_surf = FontManager.body(14).render(desc, True, Palette.TEXT_MUTED)
        self.canvas.blit(desc_surf, (chamber_rect.centerx - desc_surf.get_width() // 2, chamber_rect.top + 85))

        # 3 Tunnel Archway Portals
        tunnels = engine.DODECAHEDRON_ROOMS[self.state.hunter_room]
        portal_x = [chamber_rect.left + 40, chamber_rect.left + 230, chamber_rect.left + 420]

        # Flickering radial torchlight warmth on wall
        glow_pulse = 22 + int(6 * math.sin(self.anim_pulse_timer * 10.0))
        for tx, ty in [(chamber_rect.left + 90, chamber_rect.top + 160), (chamber_rect.right - 90, chamber_rect.top + 160)]:
            glow_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 170, 50, glow_pulse), (60, 60), 55)
            pygame.draw.circle(glow_surf, (255, 220, 100, glow_pulse + 12), (60, 60), 28)
            self.canvas.blit(glow_surf, (tx - 60, ty - 60))

        for i, tx in enumerate(portal_x):
            p_rect = pygame.Rect(tx, chamber_rect.top + 140, 130, 160)
            # Archway shape
            pygame.draw.rect(self.canvas, (10, 12, 16), p_rect, border_radius=30)
            pygame.draw.rect(self.canvas, Palette.GOLD_BASE, p_rect, width=2, border_radius=30)

            # Portal text
            p_num = FontManager.title(32).render(str(tunnels[i]), True, Palette.GOLD_LIGHT)
            self.canvas.blit(p_num, (p_rect.centerx - p_num.get_width() // 2, p_rect.top + 45))

            lbl = FontManager.small(13).render("TUNNEL", True, Palette.TEXT_MUTED)
            self.canvas.blit(lbl, (p_rect.centerx - lbl.get_width() // 2, p_rect.top + 90))

        # Tunnel action buttons
        self.btn_tunnel_1.draw(self.canvas)
        self.btn_tunnel_2.draw(self.canvas)
        self.btn_tunnel_3.draw(self.canvas)

    def _draw_sensory_warnings(self) -> None:
        """Draw pulsating sensory warning panels on left pane."""
        warnings = engine.get_sensory_warnings(self.state)
        warn_y = 465

        # Wumpus warning
        if warnings.smell_wumpus:
            pulse = (math.sin(self.anim_pulse_timer * 6.0) + 1.0) * 0.5
            w_color = (int(220 + 35 * pulse), int(40 + 20 * pulse), 40)
            w_rect = pygame.Rect(20, warn_y, 590, 40)
            pygame.draw.rect(self.canvas, (40, 12, 16), w_rect, border_radius=8)
            pygame.draw.rect(self.canvas, w_color, w_rect, width=2, border_radius=8)
            msg = "⚠️  I SMELL A WUMPUS! (The beast is lurkng in an adjacent cavern!)"
            s_surf = FontManager.header(16).render(msg, True, w_color)
            self.canvas.blit(s_surf, (w_rect.x + 18, w_rect.y + 10))
            warn_y += 48

        # Draft warning
        if warnings.feel_draft:
            pulse = (math.cos(self.anim_pulse_timer * 4.0) + 1.0) * 0.5
            d_color = (70, int(180 + 50 * pulse), 240)
            d_rect = pygame.Rect(20, warn_y, 590, 40)
            pygame.draw.rect(self.canvas, (12, 28, 44), d_rect, border_radius=8)
            pygame.draw.rect(self.canvas, d_color, d_rect, width=2, border_radius=8)
            msg = "💨  I FEEL A DRAFT. (A bottomless pit opens nearby!)"
            s_surf = FontManager.header(16).render(msg, True, d_color)
            self.canvas.blit(s_surf, (d_rect.x + 18, d_rect.y + 10))
            warn_y += 48

        # Bats warning
        if warnings.hear_bats:
            pulse = (math.sin(self.anim_pulse_timer * 5.0) + 1.0) * 0.5
            b_color = (int(200 + 40 * pulse), 90, 230)
            b_rect = pygame.Rect(20, warn_y, 590, 40)
            pygame.draw.rect(self.canvas, (32, 14, 40), b_rect, border_radius=8)
            pygame.draw.rect(self.canvas, b_color, b_rect, width=2, border_radius=8)
            msg = "🦇  BATS NEARBY! (Colonies of giant snatch-bats flutter close!)"
            s_surf = FontManager.header(16).render(msg, True, b_color)
            self.canvas.blit(s_surf, (b_rect.x + 18, b_rect.y + 10))
            warn_y += 48

        if not (warnings.smell_wumpus or warnings.feel_draft or warnings.hear_bats):
            s_rect = pygame.Rect(20, warn_y, 590, 40)
            pygame.draw.rect(self.canvas, (20, 26, 32), s_rect, border_radius=8)
            pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, s_rect, width=1, border_radius=8)
            msg = "The cavern air is still and quiet. No immediate hazards detected."
            s_surf = FontManager.body(14).render(msg, True, Palette.TEXT_MUTED)
            self.canvas.blit(s_surf, (s_rect.x + 18, s_rect.y + 11))

    def _draw_dodecahedron_map(self) -> None:
        """Render the 2D Planar Schlegel Projection of the 20-vertex Dodecahedron."""
        map_rect = pygame.Rect(630, 75, 630, 520)
        pygame.draw.rect(self.canvas, (14, 18, 24), map_rect, border_radius=10)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, map_rect, width=1, border_radius=10)

        # Title
        t_surf = FontManager.body(15).render("SUBTERRANEAN DODECAHEDRON CHART", True, Palette.GOLD_LIGHT)
        self.canvas.blit(t_surf, (map_rect.x + 16, map_rect.y + 12))

        sub_txt = "Click rooms to queue crooked arrow path (up to 5 chained rooms)"
        sub_surf = FontManager.small(12).render(sub_txt, True, Palette.TEXT_MUTED)
        self.canvas.blit(sub_surf, (map_rect.x + 16, map_rect.y + 32))

        # Graph area
        g_x = map_rect.x + 20
        g_y = map_rect.y + 55
        g_w = map_rect.width - 40
        g_h = map_rect.height - 70

        # Draw edges (tunnels) first
        drawn_edges = set()
        for u, neighbors in engine.DODECAHEDRON_ROOMS.items():
            ux, uy = engine.DODECAHEDRON_COORDS[u]
            u_pt = (g_x + int(ux * g_w), g_y + int(uy * g_h))
            for v in neighbors:
                edge = tuple(sorted((u, v)))
                if edge not in drawn_edges:
                    drawn_edges.add(edge)
                    vx, vy = engine.DODECAHEDRON_COORDS[v]
                    v_pt = (g_x + int(vx * g_w), g_y + int(vy * g_h))

                    # Highlight if edge is part of planned arrow path
                    is_arrow_edge = False
                    for idx in range(len(self.selected_arrow_path)):
                        prev_r = self.state.hunter_room if idx == 0 else self.selected_arrow_path[idx - 1]
                        curr_r = self.selected_arrow_path[idx]
                        if tuple(sorted((prev_r, curr_r))) == edge:
                            is_arrow_edge = True
                            break

                    if is_arrow_edge:
                        pygame.draw.line(self.canvas, Palette.CRIMSON_LIGHT, u_pt, v_pt, 4)
                    else:
                        pygame.draw.line(self.canvas, (45, 55, 68), u_pt, v_pt, 2)

        # Draw vertices (rooms)
        for r_id, (rx, ry) in engine.DODECAHEDRON_COORDS.items():
            cx = g_x + int(rx * g_w)
            cy = g_y + int(ry * g_h)

            radius = 16
            is_current = (r_id == self.state.hunter_room)
            is_visited = (r_id in self.state.visited_rooms)
            is_in_path = (r_id in self.selected_arrow_path)

            if is_current:
                # Pulsing golden aura
                pulse = (math.sin(self.anim_pulse_timer * 5.0) + 1.0) * 0.5
                aura_rad = radius + int(5 * pulse)
                pygame.draw.circle(self.canvas, (240, 180, 50, 100), (cx, cy), aura_rad)
                pygame.draw.circle(self.canvas, Palette.GOLD_LIGHT, (cx, cy), radius)
                text_col = Palette.BG_DARK
            elif is_in_path:
                pygame.draw.circle(self.canvas, Palette.CRIMSON_LIGHT, (cx, cy), radius)
                text_col = (255, 255, 255)
            elif is_visited:
                pygame.draw.circle(self.canvas, (25, 45, 38), (cx, cy), radius)
                pygame.draw.circle(self.canvas, Palette.SUCCESS_GREEN, (cx, cy), radius, 2)
                text_col = Palette.SUCCESS_GREEN
            else:
                pygame.draw.circle(self.canvas, (22, 28, 36), (cx, cy), radius)
                pygame.draw.circle(self.canvas, (55, 68, 85), (cx, cy), radius, 1)
                text_col = Palette.TEXT_MUTED

            num_surf = FontManager.small(13).render(str(r_id), True, text_col)
            self.canvas.blit(num_surf, (cx - num_surf.get_width() // 2, cy - num_surf.get_height() // 2))

        # Crooked arrow active flight tracer
        if self.arrow_anim_timer > 0.0 and len(self.arrow_anim_path) >= 2:
            pts = []
            for r_id in self.arrow_anim_path:
                rx, ry = engine.DODECAHEDRON_COORDS[r_id]
                pts.append((g_x + int(rx * g_w), g_y + int(ry * g_h)))
            if len(pts) >= 2:
                pygame.draw.lines(self.canvas, (255, 230, 80), False, pts, 4)
                pygame.draw.lines(self.canvas, (255, 255, 200), False, pts, 2)
                pygame.draw.circle(self.canvas, (255, 255, 220), pts[-1], 6)

    def _draw_arrow_path_deck(self) -> None:
        """Render the bottom control bar for Crooked Arrow shooting."""
        deck_rect = pygame.Rect(20, 615, 1240, 90)
        pygame.draw.rect(self.canvas, (18, 22, 28), deck_rect, border_radius=10)
        pygame.draw.rect(self.canvas, Palette.PANEL_BORDER, deck_rect, width=1, border_radius=10)

        # Path label
        path_str = " -> ".join(str(r) for r in self.selected_arrow_path) if self.selected_arrow_path else "(Empty — Click map nodes)"
        path_txt = f"PLANNED ARROW FLIGHT PATH: [Room {self.state.hunter_room}] -> {path_str}"
        p_surf = FontManager.body(15).render(path_txt, True, Palette.GOLD_LIGHT)
        self.canvas.blit(p_surf, (deck_rect.x + 20, deck_rect.y + 12))

        # Buttons
        self.btn_shoot_arrow.draw(self.canvas)
        self.btn_clear_arrow.draw(self.canvas)

        # Shortcut hint
        hint = "Commands: [1-3] Move Tunnel | [Space/Enter] Shoot Crooked Arrow | [C] Clear Path | [M] Rules | [R] Restart"
        h_surf = FontManager.small(13).render(hint, True, Palette.TEXT_MUTED)
        self.canvas.blit(h_surf, (deck_rect.x + 430, deck_rect.y + 50))

    def _draw_rules_modal(self) -> None:
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.canvas.blit(overlay, (0, 0))

        m_rect = pygame.Rect(240, 50, 800, 620)
        pygame.draw.rect(self.canvas, Palette.BG_DARK, m_rect, border_radius=12)
        pygame.draw.rect(self.canvas, Palette.GOLD_BASE, m_rect, width=2, border_radius=12)

        title = FontManager.title(24).render("HUNT THE WUMPUS — RULES & SURVIVAL GUIDE", True, Palette.GOLD_LIGHT)
        self.canvas.blit(title, (m_rect.centerx - title.get_width() // 2, m_rect.top + 24))

        rules = [
            "1. THE CAVE: 20 rooms connected as the vertices of a regular dodecahedron.",
            "   Each room connects to exactly 3 adjacent rooms through dark stone tunnels.",
            "",
            "2. THE WUMPUS: The ferocious beast sleeps inside one of the 20 caverns.",
            "   If you enter its room, it devours you immediately!",
            "   Shooting an arrow may awaken it, causing it to creep to an adjacent room.",
            "",
            "3. BOTTOMLESS PITS: Two rooms contain fatal bottomless abysses.",
            "   Entering a pit room results in an inescapable fall to your doom.",
            "",
            "4. SUPER BATS: Two rooms are infested with colonies of giant snatch-bats.",
            "   Entering a bat room causes bats to pick you up and drop you in a random room!",
            "",
            "5. SENSORY WARNINGS: When adjacent (1 room away) to hazards:",
            "   * 'I smell a Wumpus!' - The beast is in a neighboring cavern.",
            "   * 'I feel a draft.' - A bottomless pit is next door.",
            "   * 'Bats nearby!' - Giant snatch-bats flutter in an adjacent passage.",
            "",
            "6. CROOKED ARROWS: You carry 5 crooked arrows. You can shoot through a chain",
            "   of 1 to 5 connected rooms. If an arrow hits the Wumpus, YOU WIN!",
            "   If it flies back into your room, YOU DIE. If you run out of arrows, YOU LOSE.",
        ]

        curr_y = m_rect.top + 70
        for line in rules:
            l_surf = FontManager.body(14).render(line, True, Palette.TEXT_BODY)
            self.canvas.blit(l_surf, (m_rect.x + 36, curr_y))
            curr_y += 24

        self.btn_rules_close.draw(self.canvas)

    def _draw_log_modal(self) -> None:
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.canvas.blit(overlay, (0, 0))

        m_rect = pygame.Rect(240, 50, 800, 620)
        pygame.draw.rect(self.canvas, Palette.BG_DARK, m_rect, border_radius=12)
        pygame.draw.rect(self.canvas, Palette.GOLD_BASE, m_rect, width=2, border_radius=12)

        title = FontManager.title(24).render("CAVERN EXPLORATION JOURNAL", True, Palette.GOLD_LIGHT)
        self.canvas.blit(title, (m_rect.centerx - title.get_width() // 2, m_rect.top + 24))

        curr_y = m_rect.top + 80
        # Show last 18 log entries
        recent = self.state.history_log[-18:]
        for entry in recent:
            e_surf = FontManager.body(14).render(f"• {entry}", True, Palette.TEXT_BODY)
            self.canvas.blit(e_surf, (m_rect.x + 40, curr_y))
            curr_y += 26

        self.btn_log_close.draw(self.canvas)

    def _draw_outcome_modal(self) -> None:
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.canvas.blit(overlay, (0, 0))

        m_rect = pygame.Rect(300, 140, 680, 440)
        pygame.draw.rect(self.canvas, Palette.BG_DARK, m_rect, border_radius=14)
        border_col = Palette.SUCCESS_GREEN if self.state.victory else Palette.CRIMSON_LIGHT
        pygame.draw.rect(self.canvas, border_col, m_rect, width=3, border_radius=14)

        if self.state.victory:
            t_str = "VICTORY! YOU HAVE SLAIN THE WUMPUS!"
            t_col = Palette.SUCCESS_GREEN
            sub_str = "Your crooked arrow found its mark in the darkness! The beast is vanquished!"
        else:
            t_str = "EXPEDITION TERMINATED — DEFEAT"
            t_col = Palette.CRIMSON_LIGHT
            sub_str = self.state.game_over_reason or "You were lost in the cavern of the Wumpus."

        title = FontManager.title(26).render(t_str, True, t_col)
        self.canvas.blit(title, (m_rect.centerx - title.get_width() // 2, m_rect.top + 40))

        sub = FontManager.body(16).render(sub_str, True, Palette.TEXT_BODY)
        self.canvas.blit(sub, (m_rect.centerx - sub.get_width() // 2, m_rect.top + 95))

        # Expedition statistics
        stats = [
            f"Cavern Rooms Visited: {len(self.state.visited_rooms)} / 20",
            f"Crooked Arrows Remaining: {self.state.arrows} / 5",
            f"Final Cavern Room: Room {self.state.hunter_room}",
            f"Wumpus Lair Location: Room {self.state.wumpus_room}",
        ]
        s_y = m_rect.top + 160
        for s in stats:
            s_surf = FontManager.body(16).render(s, True, Palette.GOLD_LIGHT)
            self.canvas.blit(s_surf, (m_rect.centerx - s_surf.get_width() // 2, s_y))
            s_y += 36

        self.btn_outcome_restart.draw(self.canvas)
        self.btn_outcome_library.draw(self.canvas)

    def _draw_toast(self) -> None:
        if not self.toast_message:
            return
        t_surf = FontManager.body(15).render(self.toast_message, True, Palette.TEXT_BODY)
        pad = 20
        t_rect = pygame.Rect(
            BASE_WIDTH // 2 - (t_surf.get_width() + pad * 2) // 2,
            BASE_HEIGHT - 60,
            t_surf.get_width() + pad * 2,
            38,
        )
        pygame.draw.rect(self.canvas, (24, 28, 36), t_rect, border_radius=8)
        pygame.draw.rect(self.canvas, Palette.GOLD_BASE, t_rect, width=1, border_radius=8)
        self.canvas.blit(t_surf, (t_rect.x + pad, t_rect.y + 9))

    def _screen_to_canvas(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        win_w, win_h = self.screen_width, self.screen_height
        scale = min(win_w / BASE_WIDTH, win_h / BASE_HEIGHT)
        scaled_w = int(BASE_WIDTH * scale)
        scaled_h = int(BASE_HEIGHT * scale)
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2

        cx = (pos[0] - offset_x) / scale
        cy = (pos[1] - offset_y) / scale
        return int(cx), int(cy)

    def _present(self) -> None:
        CRTEffect.apply(self.canvas)
        win_w, win_h = self.screen_width, self.screen_height
        scale = min(win_w / BASE_WIDTH, win_h / BASE_HEIGHT)
        scaled_w = int(BASE_WIDTH * scale)
        scaled_h = int(BASE_HEIGHT * scale)
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2

        self.window.fill((0, 0, 0))
        if scale == 1.0 and offset_x == 0 and offset_y == 0:
            self.window.blit(self.canvas, (0, 0))
        else:
            scaled_surf = pygame.transform.smoothscale(self.canvas, (scaled_w, scaled_h))
            self.window.blit(scaled_surf, (offset_x, offset_y))

        pygame.display.flip()

    def run(self) -> None:
        while self.is_running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()


def main() -> None:
    pygame.init()
    app = WumpusApp()
    app.run()
    pygame.quit()


if __name__ == "__main__":
    main()
