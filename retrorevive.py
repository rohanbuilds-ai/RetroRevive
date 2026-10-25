"""
retrorevive.py - Graphical Game Library and Hub for RetroRevive.

The central entry point for discovering and playing classic computer games.
Provides game catalog cards, category filters, real-time search, detail modals,
and seamless launch / return routing for Hammurabi and 23 Matches.
"""

import math
import sys
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from game_registry import CATALOG, GameCategory, GameMetadata, GameRegistry, GameStatus
from games import lander_app, matches_app, oregon_app, trek_app, wumpus_app
from ui_pygame import BASE_HEIGHT, BASE_WIDTH, GameApp
from ui_theme import CRTEffect, FontManager, Palette, SoundSynthesizer, UIButton

GAME_BADGES = {
    "hammurabi": "SUMER",
    "23_matches": "NIM",
    "lunar_lander": "APOLLO",
    "oregon_trail": "TRAIL",
    "super_star_trek": "FLEET",
    "hunt_the_wumpus": "CAVERN",
}


class CardArtRenderer:
    """Procedural vintage pixel-art renderer for game catalog thumbnails."""

    _cache: Dict[Tuple[str, int, int], pygame.Surface] = {}

    @classmethod
    def get_art(cls, game_id: str, w: int = 94, h: int = 132) -> pygame.Surface:
        key = (game_id, w, h)
        if key in cls._cache:
            return cls._cache[key]

        surf = pygame.Surface((w, h))
        if game_id == "hammurabi":
            cls._draw_hammurabi(surf, w, h)
        elif game_id == "23_matches":
            cls._draw_matches(surf, w, h)
        elif game_id == "lunar_lander":
            cls._draw_lander(surf, w, h)
        elif game_id == "oregon_trail":
            cls._draw_oregon(surf, w, h)
        elif game_id == "super_star_trek":
            cls._draw_trek(surf, w, h)
        elif game_id == "hunt_the_wumpus":
            cls._draw_wumpus(surf, w, h)
        else:
            surf.fill((30, 24, 20))

        # Add subtle CRT scanlines & dark border bevel
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(0, h, 2):
            pygame.draw.line(overlay, (0, 0, 0, 16), (0, y), (w, y), 1)
        pygame.draw.rect(overlay, (0, 0, 0, 60), (0, 0, w, h), width=2)
        surf.blit(overlay, (0, 0))

        cls._cache[key] = surf
        return surf

    @classmethod
    def _draw_hammurabi(cls, surf: pygame.Surface, w: int, h: int) -> None:
        surf.fill((16, 20, 42))
        for y in range(40, 85):
            t = (y - 40) / 45.0
            col = (int(16 + 32 * t), int(20 + 22 * t), int(42 + 25 * t))
            pygame.draw.line(surf, col, (0, y), (w, y))

        # Stars
        stars = [(12, 12), (38, 16), (55, 10), (74, 18), (86, 14), (88, 28), (64, 30), (28, 34)]
        for sx, sy in stars:
            surf.set_at((sx, sy), (235, 245, 255))
        for sx, sy in [(38, 16), (74, 18)]:
            surf.set_at((sx - 1, sy), (200, 220, 255))
            surf.set_at((sx + 1, sy), (200, 220, 255))
            surf.set_at((sx, sy - 1), (200, 220, 255))
            surf.set_at((sx, sy + 1), (200, 220, 255))

        # Golden Crescent Moon
        pygame.draw.circle(surf, (250, 225, 120), (22, 20), 8)
        pygame.draw.circle(surf, (16, 20, 42), (25, 18), 7)

        # Stepped Terracotta Ziggurat of Ur
        base_y = 66
        # Tier 1 (Base)
        pygame.draw.rect(surf, (155, 90, 45), (14, base_y, 66, 20))
        pygame.draw.line(surf, (190, 120, 60), (14, base_y), (80, base_y), 2)
        pygame.draw.line(surf, (115, 65, 30), (80, base_y), (80, base_y + 20), 2)
        # Tier 2 (Middle)
        pygame.draw.rect(surf, (165, 100, 50), (24, base_y - 16, 46, 16))
        pygame.draw.line(surf, (200, 130, 65), (24, base_y - 16), (70, base_y - 16), 2)
        pygame.draw.line(surf, (120, 70, 35), (70, base_y - 16), (70, base_y), 2)
        # Tier 3 (Top)
        pygame.draw.rect(surf, (180, 115, 55), (35, base_y - 30, 24, 14))
        pygame.draw.line(surf, (215, 145, 75), (35, base_y - 30), (59, base_y - 30), 2)
        # High Shrine of Nanna
        pygame.draw.rect(surf, (225, 180, 50), (41, base_y - 39, 12, 9))
        pygame.draw.rect(surf, (40, 25, 15), (45, base_y - 36, 4, 6))

        # Central Grand Staircase
        stair_pts = [(44, base_y - 30), (50, base_y - 30), (54, base_y + 20), (40, base_y + 20)]
        pygame.draw.polygon(surf, (120, 70, 35), stair_pts)
        for sy in range(base_y - 26, base_y + 20, 6):
            pygame.draw.line(surf, (190, 140, 70), (43, sy), (51, sy), 1)

        # Fertile Alluvium Ground
        pygame.draw.rect(surf, (105, 75, 42), (0, base_y + 20, w, h - (base_y + 20)))

        # Winding Euphrates River
        river_pts = [(0, 96), (25, 94), (55, 100), (80, 98), (w, 104), (w, 118), (75, 112), (48, 112), (20, 106), (0, 110)]
        pygame.draw.polygon(surf, (32, 105, 145), river_pts)
        pygame.draw.line(surf, (65, 165, 205), (8, 100), (28, 98), 1)
        pygame.draw.line(surf, (65, 165, 205), (55, 105), (78, 103), 1)

        # Swaying Wheat Stalks
        wheat_stalks = [(6, h - 2, 20), (12, h - 4, 25), (18, h - 2, 18), (76, h - 2, 22), (82, h - 4, 26), (88, h - 2, 19)]
        for wx, wy, wh in wheat_stalks:
            pygame.draw.line(surf, (180, 145, 45), (wx, wy), (wx + 2, wy - wh), 1)
            pygame.draw.circle(surf, (235, 195, 65), (wx + 2, wy - wh), 2)
            pygame.draw.circle(surf, (245, 215, 85), (wx + 1, wy - wh - 2), 2)

    @classmethod
    def _draw_matches(cls, surf: pygame.Surface, w: int, h: int) -> None:
        surf.fill((46, 24, 14))
        for y in range(0, h, 6):
            pygame.draw.line(surf, (38, 18, 10), (0, y), (w, y), 1)
            if y % 18 == 0:
                pygame.draw.line(surf, (56, 30, 18), (0, y + 2), (w, y + 2), 1)

        # Match 1 (Left, angled)
        m1_pts = [(22, 60), (28, 58), (40, 120), (34, 122)]
        pygame.draw.polygon(surf, (215, 195, 160), m1_pts)
        pygame.draw.line(surf, (245, 230, 195), (23, 60), (35, 121), 1)
        pygame.draw.circle(surf, (205, 35, 30), (25, 56), 5)
        pygame.draw.circle(surf, (245, 80, 45), (24, 55), 3)

        # Match 3 (Right, angled)
        m3_pts = [(66, 58), (72, 60), (60, 122), (54, 120)]
        pygame.draw.polygon(surf, (215, 195, 160), m3_pts)
        pygame.draw.line(surf, (245, 230, 195), (67, 59), (55, 121), 1)
        pygame.draw.circle(surf, (205, 35, 30), (69, 56), 5)
        pygame.draw.circle(surf, (245, 80, 45), (68, 55), 3)

        # Match 2 (Center, ignited!)
        pygame.draw.rect(surf, (215, 195, 160), (44, 52, 6, 70))
        pygame.draw.line(surf, (245, 230, 195), (45, 52), (45, 122), 1)
        pygame.draw.rect(surf, (65, 35, 20), (44, 52, 6, 10))
        pygame.draw.circle(surf, (210, 60, 20), (47, 50), 5)
        pygame.draw.circle(surf, (255, 160, 30), (47, 49), 3)

        # Fiery plume
        flame_pts = [(47, 22), (56, 36), (54, 48), (40, 48), (38, 36)]
        pygame.draw.polygon(surf, (255, 120, 20), flame_pts)
        core_pts = [(47, 28), (53, 38), (51, 48), (43, 48), (41, 38)]
        pygame.draw.polygon(surf, (255, 215, 50), core_pts)
        pygame.draw.circle(surf, (255, 255, 220), (47, 42), 3)

        # Sparks / embers
        sparks = [(39, 20), (54, 16), (45, 10), (58, 26), (36, 32)]
        for sx, sy in sparks:
            surf.set_at((sx, sy), (255, 200, 50))
            surf.set_at((sx + 1, sy), (255, 140, 30))

    @classmethod
    def _draw_lander(cls, surf: pygame.Surface, w: int, h: int) -> None:
        surf.fill((6, 8, 14))
        stars = [(10, 14), (24, 8), (42, 18), (60, 10), (84, 12), (88, 42), (15, 50), (32, 34), (68, 32)]
        for sx, sy in stars:
            surf.set_at((sx, sy), (230, 245, 255))

        # Earthrise in upper right
        pygame.draw.circle(surf, (45, 125, 215), (74, 24), 12)
        pygame.draw.circle(surf, (240, 245, 255), (72, 22), 5)
        pygame.draw.circle(surf, (240, 245, 255), (78, 26), 4)
        pygame.draw.circle(surf, (20, 70, 150), (70, 27), 4)
        atm = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(atm, (90, 180, 255, 60), (74, 24), 14, width=2)
        surf.blit(atm, (0, 0))

        # Lunar terrain
        surf_y = 96
        pygame.draw.polygon(surf, (75, 80, 90), [(0, surf_y), (18, surf_y - 2), (38, surf_y + 4), (62, surf_y), (82, surf_y + 2), (w, surf_y - 2), (w, h), (0, h)])
        pygame.draw.ellipse(surf, (50, 55, 62), (16, surf_y + 10, 26, 12))
        pygame.draw.arc(surf, (120, 125, 138), (16, surf_y + 10, 26, 12), 3.14, 6.28, 2)
        pygame.draw.ellipse(surf, (50, 55, 62), (64, surf_y + 12, 22, 10))
        pygame.draw.arc(surf, (120, 125, 138), (64, surf_y + 12, 22, 10), 3.14, 6.28, 2)

        # Target Landing Pad
        pygame.draw.rect(surf, (105, 110, 122), (38, surf_y + 2, 24, 4))
        pygame.draw.line(surf, (60, 255, 80), (38, surf_y + 1), (38, surf_y - 2), 1)
        pygame.draw.line(surf, (60, 255, 80), (62, surf_y + 1), (62, surf_y - 2), 1)

        # Apollo LEM
        cx, cy = 48, 52
        pygame.draw.rect(surf, (215, 175, 50), (cx - 10, cy, 20, 14))
        pygame.draw.line(surf, (165, 130, 30), (cx - 10, cy + 7), (cx + 10, cy + 7), 1)
        pygame.draw.line(surf, (165, 130, 30), (cx, cy), (cx, cy + 14), 1)
        cabin_pts = [(cx - 8, cy), (cx - 6, cy - 12), (cx + 6, cy - 12), (cx + 8, cy)]
        pygame.draw.polygon(surf, (180, 185, 195), cabin_pts)
        pygame.draw.polygon(surf, (30, 75, 95), [(cx - 5, cy - 8), (cx - 2, cy - 8), (cx - 3, cy - 4), (cx - 6, cy - 4)])
        pygame.draw.polygon(surf, (30, 75, 95), [(cx + 2, cy - 8), (cx + 5, cy - 8), (cx + 6, cy - 4), (cx + 3, cy - 4)])
        pygame.draw.line(surf, (210, 215, 225), (cx, cy - 12), (cx, cy - 18), 1)

        pygame.draw.line(surf, (190, 195, 205), (cx - 8, cy + 12), (cx - 15, cy + 24), 2)
        pygame.draw.circle(surf, (200, 205, 215), (cx - 15, cy + 24), 2)
        pygame.draw.line(surf, (190, 195, 205), (cx + 8, cy + 12), (cx + 15, cy + 24), 2)
        pygame.draw.circle(surf, (200, 205, 215), (cx + 15, cy + 24), 2)

        flame_cone = [(cx - 4, cy + 14), (cx + 4, cy + 14), (cx, cy + 28)]
        pygame.draw.polygon(surf, (80, 215, 255), flame_cone)
        core_cone = [(cx - 2, cy + 14), (cx + 2, cy + 14), (cx, cy + 20)]
        pygame.draw.polygon(surf, (255, 230, 100), core_cone)

    @classmethod
    def _draw_oregon(cls, surf: pygame.Surface, w: int, h: int) -> None:
        for y in range(0, 62):
            t = y / 62.0
            col = (int(220 + 25 * t), int(160 + 45 * t), int(110 + 30 * t))
            pygame.draw.line(surf, col, (0, y), (w, y))

        pygame.draw.ellipse(surf, (245, 240, 230), (12, 14, 28, 8))
        pygame.draw.ellipse(surf, (245, 240, 230), (58, 20, 30, 9))

        mtn_pts = [(0, 62), (16, 42), (28, 54), (44, 34), (58, 52), (76, 32), (90, 50), (w, 44), (w, 64), (0, 64)]
        pygame.draw.polygon(surf, (115, 105, 130), mtn_pts)
        pygame.draw.polygon(surf, (245, 250, 255), [(16, 42), (12, 48), (20, 48)])
        pygame.draw.polygon(surf, (245, 250, 255), [(44, 34), (38, 42), (50, 42)])
        pygame.draw.polygon(surf, (245, 250, 255), [(76, 32), (70, 40), (82, 40)])

        pygame.draw.polygon(surf, (90, 120, 60), [(0, 64), (28, 60), (60, 66), (w, 62), (w, 82), (0, 82)])

        pygame.draw.rect(surf, (135, 95, 55), (0, 82, w, h - 82))
        rut_pts1 = [(0, 110), (28, 106), (58, 102), (w, 100)]
        pygame.draw.lines(surf, (95, 65, 35), False, rut_pts1, 2)
        rut_pts2 = [(0, 124), (32, 120), (66, 116), (w, 114)]
        pygame.draw.lines(surf, (95, 65, 35), False, rut_pts2, 2)

        wx, wy = 36, 80
        pygame.draw.ellipse(surf, (242, 238, 228), (wx - 16, wy - 16, 32, 20))
        pygame.draw.arc(surf, (195, 190, 180), (wx - 16, wy - 16, 32, 20), 0, 3.14, 2)
        pygame.draw.polygon(surf, (95, 55, 30), [(wx - 15, wy + 2), (wx + 15, wy + 2), (wx + 12, wy + 9), (wx - 12, wy + 9)])

        rwx, rwy = wx - 9, wy + 11
        pygame.draw.circle(surf, (65, 45, 30), (rwx, rwy), 9, 2)
        pygame.draw.circle(surf, (170, 115, 60), (rwx, rwy), 7)
        pygame.draw.line(surf, (65, 45, 30), (rwx - 7, rwy), (rwx + 7, rwy), 1)
        pygame.draw.line(surf, (65, 45, 30), (rwx, rwy - 7), (rwx, rwy + 7), 1)

        fwx, fwy = wx + 11, wy + 12
        pygame.draw.circle(surf, (65, 45, 30), (fwx, fwy), 7, 2)
        pygame.draw.circle(surf, (170, 115, 60), (fwx, fwy), 5)
        pygame.draw.line(surf, (65, 45, 30), (fwx - 5, fwy), (fwx + 5, fwy), 1)
        pygame.draw.line(surf, (65, 45, 30), (fwx, fwy - 5), (fwx, fwy + 5), 1)

        pygame.draw.line(surf, (95, 55, 30), (wx + 15, wy + 6), (wx + 30, wy + 7), 2)
        pygame.draw.rect(surf, (65, 45, 30), (wx + 26, wy + 1, 16, 10), border_radius=2)
        pygame.draw.polygon(surf, (65, 45, 30), [(wx + 40, wy + 1), (wx + 46, wy - 2), (wx + 46, wy + 6), (wx + 40, wy + 6)])

    @classmethod
    def _draw_trek(cls, surf: pygame.Surface, w: int, h: int) -> None:
        surf.fill((8, 12, 22))
        for x in range(0, w, 18):
            pygame.draw.line(surf, (16, 45, 28), (x, 0), (x, h), 1)
        for y in range(0, h, 18):
            pygame.draw.line(surf, (16, 45, 28), (0, y), (w, y), 1)

        pygame.draw.circle(surf, (22, 65, 38), (47, 66), 42, width=1)
        for sx, sy in [(12, 14), (32, 24), (84, 16), (74, 110), (18, 105)]:
            surf.set_at((sx, sy), (200, 230, 255))

        ex, ey = 36, 66
        pygame.draw.rect(surf, (165, 180, 200), (ex - 22, ey - 14, 22, 4), border_radius=2)
        pygame.draw.line(surf, (60, 175, 255), (ex - 20, ey - 12), (ex - 4, ey - 12), 2)
        pygame.draw.circle(surf, (245, 50, 40), (ex - 22, ey - 12), 2)

        pygame.draw.rect(surf, (165, 180, 200), (ex - 22, ey + 10, 22, 4), border_radius=2)
        pygame.draw.line(surf, (60, 175, 255), (ex - 20, ey + 12), (ex - 4, ey + 12), 2)
        pygame.draw.circle(surf, (245, 50, 40), (ex - 22, ey + 12), 2)

        pygame.draw.line(surf, (140, 155, 175), (ex - 12, ey - 10), (ex - 6, ey - 2), 2)
        pygame.draw.line(surf, (140, 155, 175), (ex - 12, ey + 10), (ex - 6, ey + 2), 2)

        pygame.draw.rect(surf, (165, 180, 200), (ex - 10, ey - 3, 16, 6), border_radius=3)
        pygame.draw.circle(surf, (245, 170, 45), (ex + 6, ey), 3)

        pygame.draw.ellipse(surf, (195, 210, 230), (ex - 2, ey - 11, 26, 22))
        pygame.draw.ellipse(surf, (240, 245, 255), (ex + 6, ey - 5, 8, 10))

        kx, ky = 76, 32
        pygame.draw.rect(surf, (75, 105, 85), (kx - 8, ky - 4, 16, 6), border_radius=2)
        pygame.draw.circle(surf, (85, 120, 95), (kx - 12, ky - 1), 4)
        pygame.draw.circle(surf, (255, 50, 40), (kx - 14, ky - 1), 2)

        pygame.draw.line(surf, (255, 235, 75), (ex + 18, ey - 2), (kx - 12, ky - 1), 2)
        pygame.draw.line(surf, (255, 235, 75), (ex + 18, ey + 2), (kx - 12, ky - 1), 2)

        exp = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(exp, (255, 90, 40, 120), (kx - 12, ky - 1), 8)
        pygame.draw.circle(exp, (255, 230, 80, 200), (kx - 12, ky - 1), 4)
        surf.blit(exp, (0, 0))

    @classmethod
    def _draw_wumpus(cls, surf: pygame.Surface, w: int, h: int) -> None:
        surf.fill((24, 20, 28))
        stalactites = [(10, 26), (25, 20), (40, 30), (60, 22), (76, 28), (88, 18)]
        for sx, sh in stalactites:
            pygame.draw.polygon(surf, (50, 40, 55), [(sx - 6, 0), (sx + 6, 0), (sx, sh)])

        stalagmites = [(14, 22), (32, 16), (68, 24), (84, 20)]
        for sx, sh in stalagmites:
            pygame.draw.polygon(surf, (50, 40, 55), [(sx - 6, h), (sx + 6, h), (sx, h - sh)])

        tx, ty = 18, 64
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(glow, (140, 85, 30, 70), (tx, ty), 34)
        pygame.draw.circle(glow, (200, 120, 40, 90), (tx, ty), 18)
        surf.blit(glow, (0, 0))

        pygame.draw.rect(surf, (45, 35, 30), (tx - 5, ty + 2, 4, 8))
        pygame.draw.line(surf, (85, 55, 30), (tx - 4, ty + 6), (tx - 1, ty - 6), 2)
        pygame.draw.circle(surf, (255, 140, 25), (tx - 1, ty - 8), 5)
        pygame.draw.circle(surf, (255, 220, 50), (tx - 1, ty - 9), 3)

        pygame.draw.ellipse(surf, (8, 6, 10), (44, 46, 40, 52))
        pygame.draw.rect(surf, (8, 6, 10), (44, 72, 40, 28))

        pygame.draw.circle(surf, (255, 35, 40), (58, 62), 4)
        pygame.draw.circle(surf, (255, 220, 60), (58, 62), 2)
        pygame.draw.circle(surf, (255, 35, 40), (70, 62), 4)
        pygame.draw.circle(surf, (255, 220, 60), (70, 62), 2)

        ax, ay = 32, 104
        pygame.draw.polygon(surf, (255, 225, 75), [(ax + 18, ay - 6), (ax + 12, ay - 10), (ax + 14, ay - 4)])
        pygame.draw.lines(surf, (215, 175, 45), False, [(ax - 10, ay + 6), (ax, ay + 2), (ax + 8, ay - 8), (ax + 16, ay - 5)], 2)
        pygame.draw.line(surf, (215, 45, 40), (ax - 10, ay + 6), (ax - 14, ay + 2), 2)
        pygame.draw.line(surf, (215, 45, 40), (ax - 8, ay + 7), (ax - 12, ay + 11), 2)


class LibraryCard:
    """Interactive visual card with procedural pixel art for a retro game in the library."""

    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        metadata: GameMetadata,
        on_play: Callable[[], None],
        on_details: Callable[[], None],
        index: int = 1,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.meta = metadata
        self.on_play = on_play
        self.on_details = on_details
        self.index = index
        self.is_hovered = False
        self.is_selected = False
        self.hover_progress = 0.0
        self.pulse_timer = 0.0

        # Action buttons on bottom row
        btn_w = (self.rect.width - 32) // 2
        btn_y = self.rect.bottom - 46
        btn_h = 36

        if self.meta.is_playable:
            play_label = f"PLAY NOW [{self.index}]"
            self.btn_play = UIButton((self.rect.x + 12, btn_y, btn_w, btn_h), play_label, self.on_play, primary=True, font_size=13)
        else:
            self.btn_play = UIButton((self.rect.x + 12, btn_y, btn_w, btn_h), "COMING SOON", None, font_size=13, color_scheme="sand")
            self.btn_play.is_enabled = False

        self.btn_details = UIButton((self.rect.x + 20 + btn_w, btn_y, btn_w, btn_h), "DETAILS", self.on_details, font_size=13, color_scheme="lapis")

    def update(self, dt: float = 0.016) -> None:
        target = 1.0 if (self.is_hovered or self.is_selected) else 0.0
        self.hover_progress += (target - self.hover_progress) * min(1.0, dt * 10.0)
        self.pulse_timer += dt
        self.btn_play.update(dt)
        self.btn_details.update(dt)

    def handle_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]) -> bool:
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if self.btn_play.handle_event(event, mouse_pos):
            return True
        if self.btn_details.handle_event(event, mouse_pos):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.on_details()
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        # Card Drop Shadow
        shadow_rect = self.rect.copy()
        shadow_rect.y += 4
        pygame.draw.rect(surface, (12, 10, 8, 180), shadow_rect, border_radius=12)

        # Card Background
        bg_col = (48, 38, 30) if (self.is_hovered or self.is_selected) else Palette.PANEL_BG
        pygame.draw.rect(surface, bg_col, self.rect, border_radius=12)

        # Border with selection glow
        if self.is_selected:
            pulse = 0.5 + 0.5 * math.sin(self.pulse_timer * 5.0)
            border_col = (
                int(Palette.GOLD_LIGHT[0] * 0.8 + 50 * pulse),
                int(Palette.GOLD_LIGHT[1] * 0.8 + 50 * pulse),
                int(Palette.GOLD_LIGHT[2] * 0.8 + 50 * pulse),
            )
            border_width = 3
        elif self.is_hovered:
            border_col = Palette.GOLD_BASE
            border_width = 2
        else:
            border_col = Palette.PANEL_BORDER
            border_width = 1

        pygame.draw.rect(surface, border_col, self.rect, width=border_width, border_radius=12)

        # --- Top Row Badges ---
        badge_y = self.rect.y + 8

        # Hotkey badge [1] .. [6]
        hotkey_rect = pygame.Rect(self.rect.x + 12, badge_y, 28, 20)
        pygame.draw.rect(surface, (50, 36, 14), hotkey_rect, border_radius=5)
        pygame.draw.rect(surface, Palette.GOLD_BASE, hotkey_rect, width=1, border_radius=5)
        hk_surf = FontManager.micro(11).render(f"[{self.index}]", True, Palette.GOLD_LIGHT)
        surface.blit(hk_surf, (hotkey_rect.centerx - hk_surf.get_width() // 2, badge_y + 3))

        # Status Badge Pill
        status_x = self.rect.x + 46
        if self.meta.is_playable:
            pill_rect = pygame.Rect(status_x, badge_y, 88, 20)
            pygame.draw.rect(surface, (25, 75, 40), pill_rect, border_radius=10)
            pygame.draw.rect(surface, Palette.SUCCESS_GREEN, pill_rect, width=1, border_radius=10)
            badge_txt = FontManager.micro(11).render("● PLAYABLE", True, Palette.SUCCESS_GREEN)
            surface.blit(badge_txt, (status_x + 8, badge_y + 3))
        else:
            pill_rect = pygame.Rect(status_x, badge_y, 102, 20)
            pygame.draw.rect(surface, (60, 45, 30), pill_rect, border_radius=10)
            pygame.draw.rect(surface, Palette.SAND_DARK, pill_rect, width=1, border_radius=10)
            badge_txt = FontManager.micro(11).render("○ COMING SOON", True, Palette.SAND_LIGHT)
            surface.blit(badge_txt, (status_x + 8, badge_y + 3))

        # Thematic tag and year (Right-aligned)
        theme_glyph = GAME_BADGES.get(self.meta.game_id, "")
        tag_str = f"{theme_glyph} • {self.meta.year}" if theme_glyph else f"{self.meta.year}"
        tag_surf = FontManager.micro(11).render(tag_str, True, Palette.GOLD_BASE)
        surface.blit(tag_surf, (self.rect.right - tag_surf.get_width() - 14, badge_y + 4))

        # --- Middle Row: Procedural Art Frame (Left) + Content (Right) ---
        art_frame_x = self.rect.x + 12
        art_frame_y = self.rect.y + 34
        art_w = 98
        art_h = 142

        # Outer Monitor Frame Bevel
        frame_rect = pygame.Rect(art_frame_x, art_frame_y, art_w, art_h)
        pygame.draw.rect(surface, (22, 18, 14), frame_rect, border_radius=6)
        pygame.draw.rect(surface, (65, 52, 40), frame_rect, width=1, border_radius=6)

        # Draw Procedural Pixel Art Thumbnail
        thumbnail = CardArtRenderer.get_art(self.meta.game_id, art_w - 4, art_h - 4)
        surface.blit(thumbnail, (art_frame_x + 2, art_frame_y + 2))

        # Inner CRT Monitor Glass Gloss
        gloss_col = (255, 255, 255, 20)
        pygame.draw.line(surface, gloss_col, (art_frame_x + 3, art_frame_y + 3), (art_frame_x + art_w - 3, art_frame_y + 3), 1)

        # Right Content Area
        content_x = self.rect.x + 118
        avail_w = self.rect.width - 130

        # Game Title
        title_surf = FontManager.header(18).render(self.meta.title, True, Palette.GOLD_PALE)
        surface.blit(title_surf, (content_x, self.rect.y + 34))

        # Subtitle
        sub_surf = FontManager.small(11).render(self.meta.subtitle, True, Palette.SAND_LIGHT)
        surface.blit(sub_surf, (content_x, self.rect.y + 56))

        # Divider line
        pygame.draw.line(surface, Palette.PANEL_BORDER, (content_x, self.rect.y + 74), (self.rect.right - 14, self.rect.y + 74), 1)

        # Description text (wrapped up to 3 lines)
        desc_words = self.meta.description.split()
        lines: List[str] = []
        curr_line = ""
        font = FontManager.small(12)
        for w in desc_words:
            test = curr_line + (" " if curr_line else "") + w
            if font.size(test)[0] < avail_w:
                curr_line = test
            else:
                lines.append(curr_line)
                curr_line = w
                if len(lines) >= 3:
                    break
        if curr_line and len(lines) < 3:
            lines.append(curr_line)

        dy = self.rect.y + 80
        for line in lines:
            txt_surf = font.render(line, True, Palette.TEXT_BODY)
            surface.blit(txt_surf, (content_x, dy))
            dy += 16

        # Modes & Tags Badge Pill
        mode_clean_map = {
            "Classic 1978 Mode": "Classic",
            "Enhanced Mode (Advisors & Scenarios)": "Enhanced",
            "Classic 1978 Mode (Albrecht AI)": "Classic",
            "Master Mode (Optimal Modular AI)": "Master AI",
            "Classic 1978 Mode (Jim Storer Model)": "Classic",
            "Enhanced Flight Telemetry HUD": "Telemetry",
            "1848 Pioneer Journey": "1848 Trail",
            "Survival Simulation & Trail Guide": "Survival",
            "1978 Strategic Space Combat": "Strategic",
            "Tactical Sensor Array & Star Map": "Sensors",
            "Classic 1978 Dodecahedron Cavern": "Cavern",
            "Sensory Warnings & Crooked Arrow": "Hazards",
        }
        short_modes = [mode_clean_map.get(m, m.split()[0]) for m in self.meta.modes[:2]]
        modes_str = " • ".join(short_modes) if short_modes else "Classic"

        modes_pill_rect = pygame.Rect(content_x, self.rect.y + 148, avail_w, 20)
        pygame.draw.rect(surface, (28, 22, 18), modes_pill_rect, border_radius=4)
        pygame.draw.rect(surface, (55, 45, 35), modes_pill_rect, width=1, border_radius=4)
        modes_surf = FontManager.micro(10).render(f"MODES: {modes_str}", True, Palette.SAND_LIGHT)
        surface.blit(modes_surf, (content_x + 8, self.rect.y + 152))

        # Action Buttons
        self.btn_play.draw(surface)
        self.btn_details.draw(surface)


class RetroReviveHub:
    """Main graphical platform application controller."""

    def __init__(self, start_fullscreen: bool = False) -> None:
        pygame.init()
        SoundSynthesizer.init()

        self.registry = GameRegistry()
        self.screen_width = BASE_WIDTH
        self.screen_height = BASE_HEIGHT

        flags = pygame.RESIZABLE
        if start_fullscreen:
            flags |= pygame.FULLSCREEN
        self.window = pygame.display.set_mode((self.screen_width, self.screen_height), flags)
        pygame.display.set_caption("RetroRevive — Classic Computer Games Platform")

        self.canvas = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        self.clock = pygame.time.Clock()
        self.is_running = True

        # Navigation & Filtering
        self.current_category = GameCategory.ALL
        self.search_query: str = ""
        self.is_search_active: bool = False
        self.selected_card_index: int = 0
        self.selected_game_for_modal: Optional[GameMetadata] = None
        self.status_pulse_timer: float = 0.0

        # Active sub-game controller (delegates events/updates/drawing)
        self.active_subapp: Optional[object] = None

        # Build UI Elements
        self._init_category_buttons()
        self._init_header_buttons()
        self._refresh_game_cards()

    def _init_header_buttons(self) -> None:
        crt_label = f"[F2] CRT: {'ON' if CRTEffect.is_enabled() else 'OFF'}"
        audio_label = f"[F3] AUDIO: {'ON' if SoundSynthesizer.is_enabled() else 'OFF'}"
        self.btn_crt = UIButton((BASE_WIDTH - 380, 18, 124, 36), crt_label, self._toggle_crt, color_scheme="lapis", font_size=12)
        self.btn_audio = UIButton((BASE_WIDTH - 246, 18, 126, 36), audio_label, self._toggle_audio, color_scheme="gold", font_size=12)
        self.btn_quit = UIButton((BASE_WIDTH - 110, 18, 70, 36), "[ESC] QUIT", self.quit, color_scheme="crimson", font_size=12)

        # Modal buttons
        self.btn_modal_launch = UIButton((BASE_WIDTH // 2 - 180, 565, 160, 44), "LAUNCH GAME", self._launch_modal_game, primary=True)
        self.btn_modal_close = UIButton((BASE_WIDTH // 2 + 20, 565, 160, 44), "BACK", self._close_modal, color_scheme="sand")

    def _init_category_buttons(self) -> None:
        all_count = len(self.registry.list_all())
        strat_count = len(self.registry.filter_by_category(GameCategory.STRATEGY_SIMULATION))
        puz_count = len(self.registry.filter_by_category(GameCategory.PUZZLE_LOGIC))
        space_count = len(self.registry.filter_by_category(GameCategory.ADVENTURE_SPACE))

        categories = [
            (GameCategory.ALL, f"ALL GAMES ({all_count})"),
            (GameCategory.STRATEGY_SIMULATION, f"STRATEGY ({strat_count})"),
            (GameCategory.PUZZLE_LOGIC, f"PUZZLE ({puz_count})"),
            (GameCategory.ADVENTURE_SPACE, f"SPACE / EXPLORE ({space_count})"),
        ]
        self.cat_buttons: List[Tuple[GameCategory, UIButton]] = []
        bw = 180
        start_x = 40
        y = 106

        for i, (cat, label) in enumerate(categories):
            btn = UIButton((start_x + i * (bw + 12), y, bw, 36), label, lambda c=cat: self._set_category(c), font_size=13, color_scheme="sand")
            self.cat_buttons.append((cat, btn))

    def _set_category(self, cat: GameCategory) -> None:
        self.current_category = cat
        self._refresh_game_cards()
        SoundSynthesizer.play("click")

    def _toggle_crt(self) -> None:
        enabled = CRTEffect.toggle()
        self.btn_crt.text = f"[F2] CRT: {'ON' if enabled else 'OFF'}"
        SoundSynthesizer.play("blip")

    def _toggle_audio(self) -> None:
        enabled = not SoundSynthesizer._enabled
        SoundSynthesizer.set_enabled(enabled)
        self.btn_audio.text = f"[F3] AUDIO: {'ON' if enabled else 'OFF'}"

    def _refresh_game_cards(self) -> None:
        """Filters catalog games based on category and search text, then builds cards."""
        # 1. Filter by category
        if self.current_category == GameCategory.ALL:
            games = self.registry.list_all()
        else:
            games = self.registry.filter_by_category(self.current_category)

        # 2. Search query filter
        if self.search_query.strip():
            q = self.search_query.strip().lower()
            games = [g for g in games if (q in g.title.lower() or q in g.subtitle.lower() or q in g.author.lower() or any(q in t.lower() for t in g.tags))]

        self.cards: List[LibraryCard] = []
        if not games:
            return

        card_w = 370
        card_h = 236
        start_x = 55
        start_y = 154
        gap_x = 30
        gap_y = 18
        cols = 3

        for i, g in enumerate(games):
            row = i // cols
            col = i % cols
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            card = LibraryCard(
                (x, y, card_w, card_h),
                g,
                on_play=lambda meta=g: self.launch_game(meta.game_id),
                on_details=lambda meta=g: self._open_details(meta),
                index=i + 1,
            )
            self.cards.append(card)

        # Clamp selection index
        self.selected_card_index = min(max(0, self.selected_card_index), max(0, len(self.cards) - 1))
        if self.cards:
            self.cards[self.selected_card_index].is_selected = True

    def _open_details(self, meta: GameMetadata) -> None:
        self.selected_game_for_modal = meta
        SoundSynthesizer.play("click")

    def _close_modal(self) -> None:
        self.selected_game_for_modal = None
        SoundSynthesizer.play("click")

    def _launch_modal_game(self) -> None:
        if self.selected_game_for_modal and self.selected_game_for_modal.is_playable:
            gid = self.selected_game_for_modal.game_id
            self.selected_game_for_modal = None
            self.launch_game(gid)

    def launch_game(self, game_id: str) -> None:
        """Launches the selected game subapp cleanly using the shared display window."""
        SoundSynthesizer.play("fanfare")

        if game_id == "hammurabi":
            self.active_subapp = GameApp(
                shared_window=self.window,
                on_exit_to_library=self._return_to_hub,
            )
        elif game_id == "23_matches":
            self.active_subapp = matches_app.MatchesApp(
                shared_window=self.window,
                on_exit_to_library=self._return_to_hub,
            )
        elif game_id == "lunar_lander":
            self.active_subapp = lander_app.LanderApp(
                shared_window=self.window,
                on_exit_to_library=self._return_to_hub,
            )
        elif game_id == "oregon_trail":
            self.active_subapp = oregon_app.OregonApp(
                shared_window=self.window,
                on_exit_to_library=self._return_to_hub,
            )
        elif game_id == "super_star_trek":
            self.active_subapp = trek_app.TrekApp(
                shared_window=self.window,
                on_exit_to_library=self._return_to_hub,
            )
        elif game_id == "hunt_the_wumpus":
            self.active_subapp = wumpus_app.WumpusApp(
                shared_window=self.window,
                on_exit_to_library=self._return_to_hub,
            )
        else:
            # Non-playable or unknown
            return

    def _return_to_hub(self) -> None:
        """Callback invoked by game subapps when the player returns to the library."""
        self.active_subapp = None
        pygame.display.set_caption("RetroRevive — Classic Computer Games Platform")
        self._refresh_game_cards()
        SoundSynthesizer.play("click")

    def quit(self) -> None:
        self.is_running = False

    def handle_event(self, event: pygame.event.Event) -> None:
        # If a game subapp is actively running, delegate all events to it!
        if self.active_subapp is not None:
            self.active_subapp.handle_event(event)
            return

        raw_pos = getattr(event, "pos", None) or pygame.mouse.get_pos()
        canvas_mouse = self._screen_to_canvas(raw_pos)

        if event.type == pygame.QUIT:
            self.is_running = False
            return

        if event.type == pygame.VIDEORESIZE:
            self.screen_width = event.w
            self.screen_height = event.h
            self.window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            return

        # Modal Event Handling
        if self.selected_game_for_modal is not None:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self._close_modal()
                    return
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._launch_modal_game()
                    return
            if self.selected_game_for_modal.is_playable and self.btn_modal_launch.handle_event(event, canvas_mouse):
                return
            if self.btn_modal_close.handle_event(event, canvas_mouse):
                return
            return

        # Header buttons
        if self.btn_crt.handle_event(event, canvas_mouse):
            return
        if self.btn_audio.handle_event(event, canvas_mouse):
            return
        if self.btn_quit.handle_event(event, canvas_mouse):
            return

        # Category buttons
        for cat, btn in self.cat_buttons:
            if btn.handle_event(event, canvas_mouse):
                return

        # Search bar click
        search_rect = pygame.Rect(BASE_WIDTH - 360, 106, 320, 36)
        clear_rect = pygame.Rect(search_rect.right - 28, search_rect.y + 6, 22, 24)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.search_query and clear_rect.collidepoint(canvas_mouse):
                self.search_query = ""
                self._refresh_game_cards()
                SoundSynthesizer.play("click")
                return
            self.is_search_active = search_rect.collidepoint(canvas_mouse)

        # Search text input
        if self.is_search_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.search_query = self.search_query[:-1]
                self._refresh_game_cards()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                self.is_search_active = False
            else:
                u_char = getattr(event, "unicode", "")
                if u_char and u_char.isprintable():
                    self.search_query += u_char
                    self._refresh_game_cards()
            return

        # Game Card Clicks
        for card in self.cards:
            if card.handle_event(event, canvas_mouse):
                return

        # Keyboard Navigation Shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2:
                self._toggle_crt()
                return
            elif event.key == pygame.K_F3:
                self._toggle_audio()
                return
            elif event.key in (pygame.K_1, pygame.K_KP1):
                self.launch_game("hammurabi")
            elif event.key in (pygame.K_2, pygame.K_KP2):
                self.launch_game("23_matches")
            elif event.key in (pygame.K_3, pygame.K_KP3):
                self.launch_game("lunar_lander")
            elif event.key in (pygame.K_4, pygame.K_KP4):
                self.launch_game("oregon_trail")
            elif event.key in (pygame.K_5, pygame.K_KP5):
                self.launch_game("super_star_trek")
            elif event.key in (pygame.K_6, pygame.K_KP6):
                self.launch_game("hunt_the_wumpus")
            elif event.key == pygame.K_s:
                self.is_search_active = True
            elif event.key == pygame.K_LEFT:
                if self.cards:
                    self.selected_card_index = (self.selected_card_index - 1) % len(self.cards)
                    for i, c in enumerate(self.cards):
                        c.is_selected = (i == self.selected_card_index)
            elif event.key == pygame.K_RIGHT:
                if self.cards:
                    self.selected_card_index = (self.selected_card_index + 1) % len(self.cards)
                    for i, c in enumerate(self.cards):
                        c.is_selected = (i == self.selected_card_index)
            elif event.key == pygame.K_d:
                if self.cards and 0 <= self.selected_card_index < len(self.cards):
                    self._open_details(self.cards[self.selected_card_index].meta)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if self.cards and 0 <= self.selected_card_index < len(self.cards):
                    card = self.cards[self.selected_card_index]
                    if card.meta.is_playable:
                        self.launch_game(card.meta.game_id)
                    else:
                        self._open_details(card.meta)
            elif event.key == pygame.K_ESCAPE:
                if self.search_query:
                    self.search_query = ""
                    self._refresh_game_cards()
                else:
                    self.quit()

    def update(self, dt: float) -> None:
        if self.active_subapp is not None:
            self.active_subapp.update(dt)
            return

        self.status_pulse_timer += dt
        self.btn_crt.update(dt)
        self.btn_audio.update(dt)
        self.btn_quit.update(dt)

        for _, btn in self.cat_buttons:
            btn.update(dt)

        for card in self.cards:
            card.update(dt)

    def draw(self) -> None:
        # If subapp active, delegate drawing directly!
        if self.active_subapp is not None:
            self.active_subapp.draw()
            return

        # 1. Background
        self.canvas.fill(Palette.BG_DARK)

        # Subtle gold Mesopotamian / arcade top stripe
        pygame.draw.rect(self.canvas, Palette.GOLD_DARK, (0, 0, BASE_WIDTH, 4))

        # 2. Top Header Bar
        header_rect = pygame.Rect(0, 4, BASE_WIDTH, 88)
        pygame.draw.rect(self.canvas, Palette.PANEL_BG, header_rect)
        pygame.draw.line(self.canvas, Palette.GOLD_BASE, (0, 92), (BASE_WIDTH, 92), 2)

        # Arcade Marquee Title Treatment with Multi-Layer Shadow
        title_text = "RETROREVIVE"
        shadow_surf = FontManager.title(32).render(title_text, True, (12, 10, 8))
        amber_surf = FontManager.title(32).render(title_text, True, (140, 95, 30))
        gold_surf = FontManager.title(32).render(title_text, True, Palette.GOLD_PALE)
        title_w = gold_surf.get_width()

        self.canvas.blit(shadow_surf, (42, 18))
        self.canvas.blit(amber_surf, (41, 17))
        self.canvas.blit(gold_surf, (40, 16))

        # Release Badge positioned dynamically after title
        ver_x = 40 + title_w + 14
        ver_rect = pygame.Rect(ver_x, 21, 46, 22)
        pygame.draw.rect(self.canvas, (45, 34, 20), ver_rect, border_radius=5)
        pygame.draw.rect(self.canvas, Palette.GOLD_BASE, ver_rect, width=1, border_radius=5)
        ver_surf = FontManager.micro(11).render("v1.2", True, Palette.GOLD_LIGHT)
        self.canvas.blit(ver_surf, (ver_rect.centerx - ver_surf.get_width() // 2, 25))

        # Live Animated Pulsing Online LED Status Badge positioned after version badge
        led_x = ver_x + 56
        led_pill = pygame.Rect(led_x, 20, 182, 24)
        pygame.draw.rect(self.canvas, (18, 30, 22), led_pill, border_radius=12)
        pygame.draw.rect(self.canvas, Palette.SUCCESS_GREEN, led_pill, width=1, border_radius=12)

        pulse = 0.5 + 0.5 * math.sin(self.status_pulse_timer * 4.0)
        halo_surf = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(halo_surf, (40, 190, 80, int(70 + 80 * pulse)), (9, 9), 8)
        pygame.draw.circle(halo_surf, (90, 255, 130), (9, 9), 4)
        self.canvas.blit(halo_surf, (led_x + 8, 23))

        led_txt = FontManager.micro(11).render("ONLINE [6/6 PLAYABLE]", True, Palette.SUCCESS_GREEN)
        self.canvas.blit(led_txt, (led_x + 30, 25))

        # Subtitle & Buildathon badge
        sub_surf = FontManager.header(15).render("CLASSIC COMPUTER GAMES PLATFORM", True, Palette.SAND_LIGHT)
        build_badge = FontManager.small(12).render("Confluence Buildathon 2026 — Track: Resurrections", True, Palette.TEXT_MUTED)

        self.canvas.blit(sub_surf, (40, 56))
        self.canvas.blit(build_badge, (360, 58))

        # Header action buttons
        self.btn_crt.draw(self.canvas)
        self.btn_audio.draw(self.canvas)
        self.btn_quit.draw(self.canvas)

        # 3. Category Buttons
        for cat, btn in self.cat_buttons:
            btn.primary = (cat == self.current_category)
            btn.draw(self.canvas)

        # 4. Search Bar
        search_rect = pygame.Rect(BASE_WIDTH - 360, 106, 320, 36)
        s_bg = (50, 40, 32) if self.is_search_active else (32, 26, 20)
        pygame.draw.rect(self.canvas, s_bg, search_rect, border_radius=8)
        s_border = Palette.GOLD_LIGHT if self.is_search_active else Palette.PANEL_BORDER
        pygame.draw.rect(self.canvas, s_border, search_rect, width=1, border_radius=8)

        # Search placeholder or text
        if self.search_query:
            query_surf = FontManager.body(14).render(self.search_query, True, Palette.TEXT_TITLE)
            self.canvas.blit(query_surf, (search_rect.x + 12, search_rect.y + 9))
            # Clear button [X]
            clear_rect = pygame.Rect(search_rect.right - 26, search_rect.y + 7, 20, 22)
            pygame.draw.rect(self.canvas, (55, 42, 34), clear_rect, border_radius=4)
            x_surf = FontManager.micro(11).render("X", True, Palette.SAND_LIGHT)
            self.canvas.blit(x_surf, (clear_rect.centerx - x_surf.get_width() // 2, clear_rect.centery - x_surf.get_height() // 2))
        else:
            query_surf = FontManager.small(13).render("Search games [S]...", True, Palette.TEXT_MUTED)
            self.canvas.blit(query_surf, (search_rect.x + 12, search_rect.y + 9))

        # 5. Game Cards Grid
        if self.cards:
            for card in self.cards:
                card.draw(self.canvas)
        else:
            no_games = FontManager.header(20).render("No games match the current filter or search.", True, Palette.TEXT_MUTED)
            self.canvas.blit(no_games, no_games.get_rect(center=(BASE_WIDTH // 2, 360)))

        # 6. Bottom Navigation Bar / Shortcuts
        bot_rect = pygame.Rect(0, BASE_HEIGHT - 38, BASE_WIDTH, 38)
        pygame.draw.rect(self.canvas, (18, 14, 12), bot_rect)
        pygame.draw.line(self.canvas, Palette.PANEL_BORDER, (0, BASE_HEIGHT - 38), (BASE_WIDTH, BASE_HEIGHT - 38), 1)

        shortcuts = "[1..6] Quick Play   •   [F2] CRT Scanlines   •   [F3] Audio FX   •   [←/→] Navigate   •   [Enter] Launch   •   [Esc] Quit"
        sc_surf = FontManager.small(12).render(shortcuts, True, Palette.TEXT_MUTED)
        self.canvas.blit(sc_surf, sc_surf.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT - 19)))

        # 7. Game Details Modal
        if self.selected_game_for_modal is not None:
            self._draw_details_modal()

        # 8. Scale canvas to window
        self._present()

    def _draw_details_modal(self) -> None:
        g = self.selected_game_for_modal
        if not g:
            return

        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 8, 6, 220))
        self.canvas.blit(overlay, (0, 0))

        pw, ph = 780, 560
        px = (BASE_WIDTH - pw) // 2
        py = (BASE_HEIGHT - ph) // 2
        p_rect = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.canvas, Palette.PANEL_BG, p_rect, border_radius=14)
        pygame.draw.rect(self.canvas, Palette.GOLD_LIGHT, p_rect, width=2, border_radius=14)

        # Header Title
        title_surf = FontManager.title(28).render(g.title, True, Palette.GOLD_PALE)
        self.canvas.blit(title_surf, (px + 36, py + 28))

        sub_surf = FontManager.body(16).render(g.subtitle, True, Palette.SAND_LIGHT)
        self.canvas.blit(sub_surf, (px + 36, py + 66))

        # Divider
        pygame.draw.line(self.canvas, Palette.PANEL_BORDER, (px + 36, py + 95), (px + pw - 36, py + 95), 1)

        # Metadata Details
        meta_items = [
            ("Historical Origin:", f"{g.author} ({g.year})"),
            ("Publisher:", g.original_publisher),
            ("Source Book:", g.book_source),
            ("Genre & Category:", f"{g.category_display} (Status: {g.status.value})"),
            ("Available Modes:", " • ".join(g.modes)),
        ]

        curr_y = py + 108
        for label, val in meta_items:
            l_surf = FontManager.header(14).render(label, True, Palette.GOLD_BASE)
            v_surf = FontManager.body(14).render(val, True, Palette.TEXT_BODY)
            self.canvas.blit(l_surf, (px + 36, curr_y))
            self.canvas.blit(v_surf, (px + 200, curr_y))
            curr_y += 24

        # Rules Overview
        curr_y += 8
        r_title = FontManager.header(15).render("RULES & MECHANICS OVERVIEW:", True, Palette.GOLD_BASE)
        self.canvas.blit(r_title, (px + 36, curr_y))
        curr_y += 22

        r_words = g.rules_summary.split()
        r_line = ""
        for w in r_words:
            test = r_line + (" " if r_line else "") + w
            if FontManager.small(13).size(test)[0] < pw - 72:
                r_line = test
            else:
                self.canvas.blit(FontManager.small(13).render(r_line, True, Palette.SAND_LIGHT), (px + 36, curr_y))
                curr_y += 18
                r_line = w
        if r_line:
            self.canvas.blit(FontManager.small(13).render(r_line, True, Palette.SAND_LIGHT), (px + 36, curr_y))
            curr_y += 22

        # Historical Provenance
        curr_y += 6
        p_title = FontManager.header(15).render("HISTORICAL PROVENANCE & FIDELITY:", True, Palette.GOLD_BASE)
        self.canvas.blit(p_title, (px + 36, curr_y))
        curr_y += 22

        p_words = g.historical_provenance.split()
        p_line = ""
        for w in p_words:
            test = p_line + (" " if p_line else "") + w
            if FontManager.small(13).size(test)[0] < pw - 72:
                p_line = test
            else:
                self.canvas.blit(FontManager.small(13).render(p_line, True, Palette.TEXT_MUTED), (px + 36, curr_y))
                curr_y += 18
                p_line = w
        if p_line:
            self.canvas.blit(FontManager.small(13).render(p_line, True, Palette.TEXT_MUTED), (px + 36, curr_y))

        # Launch / Close buttons
        if g.is_playable:
            self.btn_modal_launch.is_enabled = True
            self.btn_modal_launch.draw(self.canvas)
        else:
            self.btn_modal_launch.is_enabled = False

        self.btn_modal_close.draw(self.canvas)

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
        while self.is_running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()


def main() -> None:
    start_fullscreen = "--fullscreen" in sys.argv
    hub = RetroReviveHub(start_fullscreen=start_fullscreen)
    hub.run()
    pygame.quit()


if __name__ == "__main__":
    main()
