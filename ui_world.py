"""
ui_world.py - Animated ancient Sumerian kingdom scene renderer for RetroRevive.

Renders a rich, animated landscape featuring:
- Time-of-day sky with celestial sun and drifting clouds
- Distant Zagros mountain silhouettes
- Grand stepped Ziggurat of Ur with flaming braziers
- Flowing Euphrates river with animated water waves
- Agricultural fields reflecting current planted acreage and harvest state
- Mudbrick granary towers reflecting current stored bushels
- Animated walking citizens along riverbank pathways
- Weather & event particles (harvest chaff, scurrying rodents, plague mist)
"""

import math
import random
from typing import List, Optional, Tuple
import pygame

from game_logic import GameState
from ui_theme import Palette


class Cloud:
    """Drifting cloud sprite."""

    def __init__(self, x: float, y: float, speed: float, width: int, height: int) -> None:
        self.x = x
        self.y = y
        self.speed = speed
        self.width = width
        self.height = height

    def update(self, dt: float) -> None:
        self.x += self.speed * dt
        if self.x > 1350:
            self.x = -self.width - random.randint(20, 100)
            self.y = random.uniform(30, 140)

    def draw(self, surface: pygame.Surface) -> None:
        cloud_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        col = (255, 245, 230, 130)
        # 3 overlapping ellipses
        pygame.draw.ellipse(cloud_surf, col, (0, self.height // 3, self.width // 2, self.height * 2 // 3))
        pygame.draw.ellipse(cloud_surf, col, (self.width // 4, 0, self.width // 2, self.height))
        pygame.draw.ellipse(cloud_surf, col, (self.width // 2, self.height // 4, self.width // 2, self.height * 3 // 4))
        surface.blit(cloud_surf, (int(self.x), int(self.y)))


class CitizenWalker:
    """Animated procedural villager walking back and forth."""

    def __init__(self, x: float, y: float, speed: float, min_x: float, max_x: float, color: Tuple[int, int, int]) -> None:
        self.x = x
        self.y = y
        self.speed = speed
        self.min_x = min_x
        self.max_x = max_x
        self.color = color
        self.facing = 1  # 1 = right, -1 = left
        self.walk_phase = random.uniform(0, 6.28)

    def update(self, dt: float) -> None:
        self.x += self.speed * self.facing * dt
        self.walk_phase += 8.0 * dt
        if self.x > self.max_x:
            self.facing = -1
        elif self.x < self.min_x:
            self.facing = 1

    def draw(self, surface: pygame.Surface) -> None:
        stride = math.sin(self.walk_phase) * 3
        # Head
        pygame.draw.circle(surface, (230, 195, 160), (int(self.x), int(self.y) - 14), 4)
        # Body (robe)
        body_poly = [
            (int(self.x) - 3, int(self.y) - 10),
            (int(self.x) + 3, int(self.y) - 10),
            (int(self.x) + 5, int(self.y) + 2),
            (int(self.x) - 5, int(self.y) + 2),
        ]
        pygame.draw.polygon(surface, self.color, body_poly)
        # Legs
        pygame.draw.line(surface, (160, 120, 80), (int(self.x) - 2, int(self.y) + 2), (int(self.x) - 2 + int(stride), int(self.y) + 8), 2)
        pygame.draw.line(surface, (160, 120, 80), (int(self.x) + 2, int(self.y) + 2), (int(self.x) + 2 - int(stride), int(self.y) + 8), 2)


class BirdFlock:
    """Procedural silhouette birds gliding gracefully across the Sumerian sky."""

    def __init__(self) -> None:
        self.x = -80.0
        self.y = 80.0
        self.speed = 36.0
        self.offsets = [(0, 0), (-16, -10), (-32, -18), (-16, 12), (-32, 22)]

    def update(self, dt: float) -> None:
        self.x += self.speed * dt
        if self.x > 1400:
            self.x = -120.0
            self.y = random.uniform(50, 140)
            self.speed = random.uniform(30.0, 48.0)

    def draw(self, surface: pygame.Surface, time_elapsed: float) -> None:
        flap = math.sin(time_elapsed * 8.0) * 3
        col = (48, 38, 30)
        for ox, oy in self.offsets:
            bx = int(self.x + ox)
            by = int(self.y + oy)
            if 0 <= bx <= 1280 and 0 <= by <= 720:
                pygame.draw.line(surface, col, (bx, by), (bx - 5, by - int(3 + flap)), 1)
                pygame.draw.line(surface, col, (bx, by), (bx + 5, by - int(3 + flap)), 1)


class Particle:
    """Cosmetic particle for harvest, rat, or celebration effects."""

    def __init__(self, x: float, y: float, vx: float, vy: float, color: Tuple[int, int, int], lifetime: float, size: int = 3) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_life = lifetime
        self.size = size

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface) -> None:
        alpha = int((self.lifetime / self.max_life) * 255)
        p_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        r, g, b = self.color
        pygame.draw.circle(p_surf, (r, g, b, alpha), (self.size, self.size), self.size)
        surface.blit(p_surf, (int(self.x) - self.size, int(self.y) - self.size))


class WorldRenderer:
    """Manages procedural rendering and animation of the Sumerian kingdom."""

    def __init__(self) -> None:
        self.time_elapsed = 0.0
        self.clouds: List[Cloud] = [
            Cloud(50, 45, 12.0, 120, 40),
            Cloud(420, 80, 16.0, 150, 45),
            Cloud(850, 35, 10.0, 110, 35),
            Cloud(1150, 95, 14.0, 140, 42),
        ]
        self.citizens: List[CitizenWalker] = [
            CitizenWalker(180, 395, 22.0, 120, 360, Palette.LAPIS_BASE),
            CitizenWalker(260, 405, 18.0, 150, 380, Palette.CLAY_DEEP),
            CitizenWalker(680, 410, 24.0, 620, 850, Palette.PALM_GREEN),
            CitizenWalker(750, 400, 20.0, 650, 900, Palette.GOLD_DARK),
            CitizenWalker(310, 390, 16.0, 200, 420, (140, 60, 60)),
        ]
        self.birds = BirdFlock()
        self.particles: List[Particle] = []

    def trigger_harvest_particles(self, count: int = 40) -> None:
        """Spawns golden grain dust over the fields."""
        for _ in range(count):
            px = random.uniform(550, 1200)
            py = random.uniform(430, 620)
            vx = random.uniform(-15, 15)
            vy = random.uniform(-40, -10)
            self.particles.append(Particle(px, py, vx, vy, Palette.GOLD_LIGHT, random.uniform(0.8, 1.8), size=random.randint(2, 4)))

    def trigger_rat_particles(self, count: int = 30) -> None:
        """Spawns scurrying rodent particles near the granary silos."""
        for _ in range(count):
            px = random.uniform(380, 520)
            py = random.uniform(370, 440)
            vx = random.uniform(-60, 60)
            vy = random.uniform(-10, 15)
            self.particles.append(Particle(px, py, vx, vy, (40, 30, 25), random.uniform(1.0, 2.0), size=3))

    def trigger_victory_fireworks(self, count: int = 60) -> None:
        """Spawns celebratory golden stars across the temple sky."""
        for _ in range(count):
            px = random.uniform(200, 1080)
            py = random.uniform(80, 260)
            angle = random.uniform(0, 6.28)
            spd = random.uniform(30, 120)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            col = random.choice([Palette.GOLD_LIGHT, Palette.LAPIS_LIGHT, Palette.CROP_GREEN, Palette.SAND_LIGHT])
            self.particles.append(Particle(px, py, vx, vy, col, random.uniform(1.2, 2.5), size=random.randint(2, 5)))

    def update(self, dt: float) -> None:
        self.time_elapsed += dt
        for cloud in self.clouds:
            cloud.update(dt)
        self.birds.update(dt)
        for citizen in self.citizens:
            citizen.update(dt)
        self.particles = [p for p in self.particles if p.update(dt)]

    def render(self, surface: pygame.Surface, state: Optional[GameState] = None) -> None:
        """Draws the complete living kingdom scenery onto surface."""
        # 0. Solid background clearing
        surface.fill(Palette.BG_DARK)

        # 1. Sky Gradient (Reflects reign progression and Mesopotamian atmosphere)
        yr = getattr(state, "year", 1) if state else 1
        # Interpolate sky top color: Year 1 dawn azure -> Year 5 bright azure -> Year 10 royal dusk amber
        if yr <= 5:
            t = (yr - 1) / 4.0
            top_r = int(35 + (25 - 35) * t)
            top_g = int(65 + (85 - 65) * t)
            top_b = int(125 + (165 - 125) * t)
        else:
            t = (yr - 5) / 5.0
            top_r = int(25 + (75 - 25) * t)
            top_g = int(85 + (45 - 85) * t)
            top_b = int(165 + (95 - 165) * t)

        for y in range(0, 320):
            factor = y / 320.0
            r = int(top_r + (225 - top_r) * factor)
            g = int(top_g + (170 - top_g) * factor)
            b = int(top_b + (95 - top_b) * factor)
            pygame.draw.line(surface, (r, g, b), (0, y), (1280, y))

        # 2. Celestial Sun
        sun_x, sun_y = 960, 95
        pulse = math.sin(self.time_elapsed * 2.0) * 3
        # Outer glow ring
        glow_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 230, 130, 50), (60, 60), int(45 + pulse))
        pygame.draw.circle(glow_surf, (255, 240, 160, 90), (60, 60), int(32 + pulse))
        surface.blit(glow_surf, (sun_x - 60, sun_y - 60))
        # Sun core
        pygame.draw.circle(surface, Palette.GOLD_PALE, (sun_x, sun_y), 24)

        # 3. Drifting Clouds & Flying Birds
        for cloud in self.clouds:
            cloud.draw(surface)
        self.birds.draw(surface, self.time_elapsed)

        # 4. Zagros Mountains Silhouette (Distance)
        mountains_poly = [
            (0, 310),
            (120, 230),
            (260, 275),
            (410, 210),
            (560, 265),
            (720, 205),
            (880, 255),
            (1050, 195),
            (1190, 240),
            (1280, 220),
            (1280, 340),
            (0, 340),
        ]
        pygame.draw.polygon(surface, (135, 105, 85), mountains_poly)

        # 5. Midground Desert Dunes & Plain (Solid ground base)
        dune_poly = [
            (0, 325),
            (300, 310),
            (650, 328),
            (1000, 312),
            (1280, 320),
            (1280, 445),
            (0, 445),
        ]
        pygame.draw.polygon(surface, Palette.SAND_BASE, dune_poly)
        pygame.draw.rect(surface, Palette.SAND_DARK, (0, 375, 1280, 70))

        # 6. Grand Ziggurat of Ur (Left side: x = 60 to 340)
        self._draw_ziggurat(surface)

        # 7. Granary Silo Storehouses (Middle: x = 370 to 520)
        bushels = state.bushels if state else 2800
        self._draw_granary(surface, bushels)

        # 8. Euphrates River (Flowing across middle ground: y = 375 to 445)
        self._draw_river(surface)

        # 9. Palm Trees along Riverbank
        self._draw_palm_trees(surface)

        # 10. Citizens walking
        for citizen in self.citizens:
            citizen.draw(surface)

        # 11. Fertile Farmland & Crops (Foreground: y = 440 to 720)
        acres = state.acres if state else 1000
        yield_rate = state.harvest_yield if state else 3
        self._draw_farmland(surface, acres, yield_rate)

        # 12. Active Particles
        for particle in self.particles:
            particle.draw(surface)

    def _draw_ziggurat(self, surface: pygame.Surface) -> None:
        """Renders the stepped ancient Sumerian mudbrick temple."""
        base_x = 80
        base_y = 380

        # Tier 1 (Lowest terrace)
        t1_w, t1_h = 240, 50
        pygame.draw.rect(surface, Palette.SAND_DARK, (base_x, base_y - t1_h, t1_w, t1_h), border_radius=4)
        pygame.draw.rect(surface, Palette.CLAY_DEEP, (base_x, base_y - t1_h, t1_w, t1_h), width=2, border_radius=4)

        # Tier 2 (Middle terrace)
        t2_x = base_x + 35
        t2_w, t2_h = 170, 45
        t2_y = base_y - t1_h - t2_h
        pygame.draw.rect(surface, Palette.SAND_DARK, (t2_x, t2_y, t2_w, t2_h), border_radius=3)
        pygame.draw.rect(surface, Palette.CLAY_DEEP, (t2_x, t2_y, t2_w, t2_h), width=2, border_radius=3)

        # Tier 3 (Upper terrace)
        t3_x = t2_x + 30
        t3_w, t3_h = 110, 40
        t3_y = t2_y - t3_h
        pygame.draw.rect(surface, Palette.SAND_DARK, (t3_x, t3_y, t3_w, t3_h), border_radius=2)
        pygame.draw.rect(surface, Palette.CLAY_DEEP, (t3_x, t3_y, t3_w, t3_h), width=2, border_radius=2)

        # Golden High Shrine at top
        shrine_x = t3_x + 25
        shrine_w, shrine_h = 60, 32
        shrine_y = t3_y - shrine_h
        pygame.draw.rect(surface, Palette.LAPIS_BASE, (shrine_x, shrine_y, shrine_w, shrine_h))
        pygame.draw.rect(surface, Palette.GOLD_LIGHT, (shrine_x, shrine_y, shrine_w, shrine_h), width=2)
        # Gold roof dome
        pygame.draw.arc(surface, Palette.GOLD_LIGHT, (shrine_x + 5, shrine_y - 12, shrine_w - 10, 24), 0, 3.14, width=3)

        # Central Grand Staircase
        stair_x = base_x + 105
        stair_poly = [
            (stair_x + 15, shrine_y + shrine_h),
            (stair_x - 15, base_y),
            (stair_x + 45, base_y),
            (stair_x + 15, shrine_y + shrine_h),
        ]
        pygame.draw.polygon(surface, Palette.CLAY_DEEP, stair_poly)
        for sy in range(shrine_y + shrine_h + 10, base_y, 8):
            w_step = 10 + int((sy - shrine_y) * 0.2)
            pygame.draw.line(surface, Palette.SAND_LIGHT, (stair_x + 15 - w_step // 2, sy), (stair_x + 15 + w_step // 2, sy), 2)

        # Animated temple flame braziers on summit
        flame_flicker = math.sin(self.time_elapsed * 12.0) * 3
        # Left brazier
        pygame.draw.circle(surface, (255, 140, 20), (shrine_x - 4, shrine_y + 8), int(5 + flame_flicker))
        pygame.draw.circle(surface, (255, 230, 60), (shrine_x - 4, shrine_y + 8), 3)
        # Right brazier
        pygame.draw.circle(surface, (255, 140, 20), (shrine_x + shrine_w + 4, shrine_y + 8), int(5 - flame_flicker))
        pygame.draw.circle(surface, (255, 230, 60), (shrine_x + shrine_w + 4, shrine_y + 8), 3)

    def _draw_granary(self, surface: pygame.Surface, bushels: int) -> None:
        """Renders the mudbrick grain storage silos with fill indicators."""
        gx, gy = 380, 375
        silo_w, silo_h = 36, 70
        spacing = 44

        # 3 Silo towers
        for i in range(3):
            sx = gx + i * spacing
            sy = gy - silo_h
            # Tower base
            pygame.draw.rect(surface, Palette.CLAY_DEEP, (sx, sy, silo_w, silo_h), border_top_left_radius=8, border_top_right_radius=8)
            pygame.draw.rect(surface, Palette.PANEL_BORDER, (sx, sy, silo_w, silo_h), width=2, border_top_left_radius=8, border_top_right_radius=8)

            # Domed clay cap
            pygame.draw.circle(surface, Palette.SAND_DARK, (sx + silo_w // 2, sy), silo_w // 2)
            pygame.draw.circle(surface, Palette.PANEL_BORDER, (sx + silo_w // 2, sy), silo_w // 2, width=1)

            # Silo fill window
            fill_pct = min(1.0, max(0.0, (bushels - i * 1000) / 1000.0))
            if fill_pct > 0.0:
                filled_h = int((silo_h - 22) * fill_pct)
                fill_rect = pygame.Rect(sx + 6, gy - 8 - filled_h, silo_w - 12, filled_h)
                pygame.draw.rect(surface, Palette.GOLD_BASE, fill_rect, border_radius=2)

            # Silo doorway/grate
            pygame.draw.rect(surface, (20, 16, 12), (sx + 10, gy - 16, silo_w - 20, 14), border_top_left_radius=4, border_top_right_radius=4)

    def _draw_river(self, surface: pygame.Surface) -> None:
        """Renders the flowing Euphrates river with sinusoidal wave highlights."""
        river_poly = [
            (0, 385),
            (280, 395),
            (580, 385),
            (920, 400),
            (1280, 390),
            (1280, 440),
            (950, 448),
            (620, 435),
            (320, 445),
            (0, 435),
        ]
        pygame.draw.polygon(surface, Palette.RIVER_BLUE, river_poly)

        # Flowing water wave highlights
        for i in range(12):
            rx = (i * 110 + int(self.time_elapsed * 35.0)) % 1280
            wave_y = 398 + int(math.sin(self.time_elapsed * 3.0 + i) * 6) + (i % 3) * 10
            pygame.draw.arc(surface, Palette.RIVER_HIGHLIGHT, (rx, wave_y, 45, 12), 0, 3.14, width=2)

    def _draw_palm_trees(self, surface: pygame.Surface) -> None:
        """Draws palm trees along the riverbank."""
        palm_locations = [(340, 380), (530, 375), (860, 385), (920, 380)]
        for tx, ty in palm_locations:
            # Trunk
            pygame.draw.arc(surface, (110, 80, 50), (tx - 15, ty - 45, 30, 50), 1.2, 2.5, width=4)
            # Palm fronds
            frond_origin = (tx - 2, ty - 42)
            for angle in [-1.2, -0.6, 0.0, 0.6, 1.2]:
                sway = math.sin(self.time_elapsed * 2.0 + angle) * 4
                fx = frond_origin[0] + int(math.sin(angle) * 22) + int(sway)
                fy = frond_origin[1] - int(math.cos(angle) * 14)
                pygame.draw.line(surface, Palette.PALM_GREEN, frond_origin, (fx, fy), 3)

    def _draw_farmland(self, surface: pygame.Surface, acres: int, yield_rate: int) -> None:
        """Renders agricultural plots and golden wheat crops."""
        # Fertile mud soil base
        pygame.draw.rect(surface, Palette.FERTILE_EARTH, (0, 440, 1280, 280))

        # Rows of cultivated furrows
        for row_y in range(455, 715, 28):
            pygame.draw.line(surface, (78, 52, 32), (0, row_y), (1280, row_y), 2)
            # Wheat stalks waving in the breeze
            sway = math.sin(self.time_elapsed * 3.5 + row_y) * 4
            crop_col = Palette.CROP_GOLD if yield_rate >= 3 else Palette.CROP_GREEN
            stalk_spacing = max(18, 50 - (acres // 60))
            for x in range(30, 1250, stalk_spacing):
                sx = x + int(sway)
                pygame.draw.line(surface, crop_col, (x, row_y), (sx, row_y - 16), 2)
                # Wheat ear tip
                pygame.draw.circle(surface, Palette.GOLD_LIGHT, (sx, row_y - 17), 2)
