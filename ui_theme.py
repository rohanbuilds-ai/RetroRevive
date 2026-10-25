"""
ui_theme.py - Design system, colors, fonts, procedural sounds, and UI widgets for RetroRevive.

Provides a warm, cohesive ancient Mesopotamian aesthetic:
- Sandstone, clay, lapis lazuli blue, gold, and fertile green palette
- Scalable typography with safe system font fallbacks
- Procedural retro 8-bit sound synthesizer (no external audio assets required)
- Reusable UI components: UIButton, UINumberInput, UIPanel, UIModal, UIToast
"""

import math
import struct
from typing import Callable, List, Optional, Tuple
import pygame


# ---------------------------------------------------------------------------
# Mesopotamian Color Palette
# ---------------------------------------------------------------------------

class Palette:
    # Sandstone & Clay
    SAND_LIGHT = (235, 218, 185)
    SAND_BASE = (210, 185, 145)
    SAND_DARK = (165, 135, 95)
    CLAY_DEEP = (120, 85, 55)

    # Dark Stone / Bronze Backgrounds
    BG_DARK = (24, 20, 18)
    PANEL_BG = (38, 30, 24)
    PANEL_BG_LIGHT = (52, 42, 34)
    PANEL_BORDER = (180, 145, 90)
    PANEL_BORDER_LIGHT = (215, 180, 115)

    # Lapis Lazuli & Water
    LAPIS_DARK = (22, 44, 88)
    LAPIS_BASE = (36, 72, 144)
    LAPIS_LIGHT = (64, 115, 210)
    RIVER_BLUE = (45, 95, 175)
    RIVER_HIGHLIGHT = (90, 150, 235)

    # Royal Gold & Amber
    GOLD_DARK = (180, 135, 25)
    GOLD_BASE = (225, 175, 40)
    GOLD_LIGHT = (250, 215, 80)
    GOLD_PALE = (255, 240, 160)

    # Agriculture & Nature
    CROP_GREEN = (65, 140, 70)
    CROP_GOLD = (215, 170, 50)
    FERTILE_EARTH = (95, 65, 40)
    PALM_GREEN = (45, 115, 55)

    # State & Alerts
    CRIMSON = (195, 45, 45)
    CRIMSON_LIGHT = (230, 75, 75)
    PESTILENCE = (145, 45, 155)
    SUCCESS_GREEN = (50, 175, 75)

    # Text & Overlays
    TEXT_TITLE = (255, 245, 225)
    TEXT_BODY = (235, 225, 210)
    TEXT_MUTED = (175, 160, 140)
    TEXT_DARK = (30, 24, 18)
    OVERLAY_DIM = (12, 10, 8, 190)


# ---------------------------------------------------------------------------
# Font Manager with Graceful Fallbacks
# ---------------------------------------------------------------------------

class FontManager:
    """Provides cached fonts across various sizes with safe system fallbacks."""

    _cache = {}

    @classmethod
    def get_font(cls, size: int, bold: bool = False, serif: bool = False) -> pygame.font.Font:
        key = (size, bold, serif)
        if key in cls._cache:
            return cls._cache[key]

        if serif:
            font_names = ["georgia", "times new roman", "palatino", "dejavuserif", "serif"]
        else:
            font_names = ["segoe ui", "arial", "tahoma", "dejavusans", "sans-serif"]

        font = None
        for name in font_names:
            try:
                font = pygame.font.SysFont(name, size, bold=bold)
                if font:
                    break
            except Exception:
                continue

        if not font:
            font = pygame.font.Font(None, size)

        cls._cache[key] = font
        return font

    @classmethod
    def title(cls, size: int = 40) -> pygame.font.Font:
        return cls.get_font(size, bold=True, serif=True)

    @classmethod
    def header(cls, size: int = 24) -> pygame.font.Font:
        return cls.get_font(size, bold=True, serif=False)

    @classmethod
    def body(cls, size: int = 18) -> pygame.font.Font:
        return cls.get_font(size, bold=False, serif=False)

    @classmethod
    def small(cls, size: int = 14) -> pygame.font.Font:
        return cls.get_font(size, bold=False, serif=False)

    @classmethod
    def mono(cls, size: int = 18) -> pygame.font.Font:
        return cls.get_font(size, bold=True, serif=False)


# ---------------------------------------------------------------------------
# Procedural Retro Sound Synthesizer
# ---------------------------------------------------------------------------

class SoundSynthesizer:
    """
    Synthesizes pleasant 8-bit retro sound effects directly in memory.
    Requires zero external audio files.
    """

    _sounds = {}
    _enabled = True

    @classmethod
    def init(cls) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            cls._generate_sounds()
        except Exception:
            cls._enabled = False

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        cls._enabled = enabled

    @classmethod
    def is_enabled(cls) -> bool:
        return cls._enabled

    @classmethod
    def _create_tone(cls, freq: float, duration: float, volume: float = 0.25, waveform: str = "sine") -> Optional[pygame.mixer.Sound]:
        try:
            sample_rate = 22050
            total_samples = int(sample_rate * duration)
            buffer = bytearray()

            for i in range(total_samples):
                t = i / sample_rate
                # Decay envelope
                envelope = max(0.0, 1.0 - (i / total_samples))

                if waveform == "sine":
                    val = math.sin(2.0 * math.pi * freq * t)
                elif waveform == "square":
                    val = 1.0 if math.sin(2.0 * math.pi * freq * t) >= 0 else -1.0
                elif waveform == "triangle":
                    val = (2.0 / math.pi) * math.asin(math.sin(2.0 * math.pi * freq * t))
                else:
                    val = math.sin(2.0 * math.pi * freq * t)

                sample = int(val * envelope * volume * 32767)
                sample = max(-32768, min(32767, sample))
                buffer.extend(struct.pack("<h", sample))

            return pygame.mixer.Sound(buffer=bytes(buffer))
        except Exception:
            return None

    @classmethod
    def _generate_sounds(cls) -> None:
        cls._sounds["click"] = cls._create_tone(880, 0.03, volume=0.15, waveform="sine")
        cls._sounds["coin"] = cls._create_tone(987, 0.08, volume=0.2, waveform="sine")
        cls._sounds["harvest"] = cls._create_tone(659, 0.15, volume=0.25, waveform="triangle")
        cls._sounds["warning"] = cls._create_tone(330, 0.25, volume=0.3, waveform="square")
        cls._sounds["bell"] = cls._create_tone(523, 0.4, volume=0.3, waveform="sine")

    @classmethod
    def play(cls, sound_name: str) -> None:
        if not cls._enabled:
            return
        snd = cls._sounds.get(sound_name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Reusable UI Button Component
# ---------------------------------------------------------------------------

class UIButton:
    """An ancient Mesopotamian-styled interactive button."""

    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        text: str,
        callback: Optional[Callable[[], None]] = None,
        font_size: int = 18,
        primary: bool = False,
        color_scheme: str = "gold",  # "gold", "lapis", "crimson", "sand"
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font_size = font_size
        self.primary = primary
        self.color_scheme = color_scheme
        self.is_hovered = False
        self.is_pressed = False
        self.is_enabled = True

    def handle_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]) -> bool:
        if not self.is_enabled:
            return False

        self.is_hovered = self.rect.collidepoint(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.is_pressed = True
                SoundSynthesizer.play("click")
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed and self.is_hovered:
                self.is_pressed = False
                if self.callback:
                    self.callback()
                return True
            self.is_pressed = False

        return False

    def draw(self, surface: pygame.Surface) -> None:
        # Determine colors
        if not self.is_enabled:
            bg_col = (55, 48, 42)
            border_col = (85, 75, 65)
            text_col = Palette.TEXT_MUTED
        elif self.color_scheme == "lapis":
            bg_col = Palette.LAPIS_LIGHT if self.is_hovered else Palette.LAPIS_BASE
            border_col = Palette.GOLD_LIGHT if self.is_hovered else Palette.GOLD_BASE
            text_col = Palette.TEXT_TITLE
        elif self.color_scheme == "crimson":
            bg_col = Palette.CRIMSON_LIGHT if self.is_hovered else Palette.CRIMSON
            border_col = Palette.GOLD_LIGHT if self.is_hovered else Palette.SAND_LIGHT
            text_col = Palette.TEXT_TITLE
        elif self.primary:
            bg_col = Palette.GOLD_LIGHT if self.is_hovered else Palette.GOLD_BASE
            border_col = Palette.SAND_LIGHT if self.is_hovered else Palette.GOLD_DARK
            text_col = Palette.TEXT_DARK
        else:
            bg_col = (68, 54, 42) if self.is_hovered else Palette.PANEL_BG_LIGHT
            border_col = Palette.GOLD_LIGHT if self.is_hovered else Palette.PANEL_BORDER
            text_col = Palette.TEXT_TITLE if self.is_hovered else Palette.TEXT_BODY

        # Shadow
        shadow_rect = self.rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(surface, (15, 12, 10, 160), shadow_rect, border_radius=6)

        # Base body
        draw_rect = self.rect.copy()
        if self.is_pressed:
            draw_rect.y += 2

        pygame.draw.rect(surface, bg_col, draw_rect, border_radius=6)
        pygame.draw.rect(surface, border_col, draw_rect, width=2, border_radius=6)

        # Text label
        font = FontManager.header(self.font_size) if self.primary else FontManager.body(self.font_size)
        text_surf = font.render(self.text, True, text_col)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        surface.blit(text_surf, text_rect)


# ---------------------------------------------------------------------------
# Number Input Box with Quick Steppers and Direct Typing
# ---------------------------------------------------------------------------

class UINumberInput:
    """An interactive number entry widget with keyboard entry, validation, and stepper buttons."""

    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        initial_value: int = 0,
        min_value: int = 0,
        max_value: int = 100000,
        step: int = 10,
        label: str = "",
        on_change: Optional[Callable[[int], None]] = None,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.value = initial_value
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.label = label
        self.on_change = on_change
        self.is_active = False
        self.text_buffer = str(initial_value)
        self.error_message: Optional[str] = None
        self.is_enabled = True

        # Build stepper button positions
        bx, by, bw, bh = self.rect.x, self.rect.y, self.rect.width, self.rect.height
        btn_h = 32
        btn_y = by + bh - btn_h - 6
        spacing = 4

        # Buttons: [-100], [-10], [+10], [+100], [MAX], [CLEAR]
        b_w = 46
        self.buttons: List[UIButton] = [
            UIButton((bx + 8, btn_y, b_w, btn_h), f"-{step * 10}", lambda: self.adjust(-step * 10), font_size=13),
            UIButton((bx + 8 + (b_w + spacing), btn_y, b_w, btn_h), f"-{step}", lambda: self.adjust(-step), font_size=13),
            UIButton((bx + 8 + (b_w + spacing) * 2, btn_y, b_w, btn_h), f"+{step}", lambda: self.adjust(step), font_size=13),
            UIButton((bx + 8 + (b_w + spacing) * 3, btn_y, b_w, btn_h), f"+{step * 10}", lambda: self.adjust(step * 10), font_size=13),
            UIButton((bx + 8 + (b_w + spacing) * 4 + 4, btn_y, 48, btn_h), "MAX", self.set_max, font_size=13, color_scheme="lapis"),
            UIButton((bx + 8 + (b_w + spacing) * 5 + 8, btn_y, 44, btn_h), "CLR", self.clear, font_size=13),
        ]

    def parse_integer(self) -> Tuple[bool, Optional[int], Optional[str]]:
        """Parses the text buffer into an integer, returning (is_valid, parsed_value, error_message)."""
        raw = self.text_buffer.strip()
        if not raw:
            return False, None, "?REDO FROM START: Input cannot be empty."
        try:
            val = int(raw)
            return True, val, None
        except ValueError:
            return False, None, f"?REDO FROM START: '{raw}' is not an integer."

    def set_value(self, val: int) -> None:
        """Sets the numeric value and updates text buffer without silent clamping."""
        self.value = val
        self.text_buffer = str(val)
        self.error_message = None
        if self.on_change:
            self.on_change(self.value)

    def adjust(self, delta: int) -> None:
        """Steps the current value up or down."""
        if not self.is_enabled:
            return
        ok, current_val, _ = self.parse_integer()
        base = current_val if ok and current_val is not None else 0
        new_val = max(0, base + delta)
        self.set_value(new_val)
        SoundSynthesizer.play("coin")

    def set_max(self) -> None:
        """Sets value to the computed maximum allowed."""
        if not self.is_enabled:
            return
        self.set_value(max(0, self.max_value))
        SoundSynthesizer.play("coin")

    def clear(self) -> None:
        """Clears value to zero."""
        if not self.is_enabled:
            return
        self.set_value(0)
        SoundSynthesizer.play("click")

    def handle_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]) -> bool:
        if not self.is_enabled:
            return False

        # Forward to stepper buttons first
        for btn in self.buttons:
            if btn.handle_event(event, mouse_pos):
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Click in upper input area (above steppers) sets focus
            upper_box = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height - 40)
            self.is_active = upper_box.collidepoint(mouse_pos)
            return self.is_active

        if event.type == pygame.KEYDOWN and self.is_active:
            if event.key == pygame.K_BACKSPACE:
                self.text_buffer = self.text_buffer[:-1]
                self.error_message = None
                ok, val, _ = self.parse_integer()
                if ok and val is not None:
                    self.value = val
                    if self.on_change:
                        self.on_change(self.value)
            elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.is_active = False
            else:
                char = event.unicode
                # Accept digits, minus sign (for testing negative values), decimals, letters (to test validation)
                if char and len(self.text_buffer) < 14 and (char.isprintable() or char in "-+."):
                    self.text_buffer += char
                    self.error_message = None
                    ok, val, _ = self.parse_integer()
                    if ok and val is not None:
                        self.value = val
                        if self.on_change:
                            self.on_change(self.value)
            return True

        return False

    def draw(self, surface: pygame.Surface) -> None:
        # Background panel
        bg_col = (45, 38, 32) if not self.is_enabled else Palette.PANEL_BG
        pygame.draw.rect(surface, bg_col, self.rect, border_radius=8)

        # Border color reflects active or error state
        if self.error_message:
            border_col = Palette.CRIMSON_LIGHT
        elif self.is_active:
            border_col = Palette.GOLD_LIGHT
        else:
            border_col = Palette.PANEL_BORDER
        pygame.draw.rect(surface, border_col, self.rect, width=2, border_radius=8)

        # Label
        lbl_col = Palette.TEXT_MUTED if not self.is_enabled else Palette.GOLD_PALE
        lbl_surf = FontManager.header(16).render(self.label, True, lbl_col)
        surface.blit(lbl_surf, (self.rect.x + 12, self.rect.y + 8))

        # Error tag if present
        if self.error_message:
            err_surf = FontManager.small(12).render("! INVALID", True, Palette.CRIMSON_LIGHT)
            surface.blit(err_surf, (self.rect.right - err_surf.get_width() - 14, self.rect.y + 10))

        # Input box
        input_box = pygame.Rect(self.rect.x + 10, self.rect.y + 28, self.rect.width - 20, 36)
        box_bg = (20, 16, 12) if self.is_active else (28, 22, 18)
        pygame.draw.rect(surface, box_bg, input_box, border_radius=5)

        box_border = Palette.CRIMSON_LIGHT if self.error_message else (Palette.GOLD_LIGHT if self.is_active else (80, 65, 50))
        pygame.draw.rect(surface, box_border, input_box, width=1, border_radius=5)

        # Value text: display user's typed buffer whenever editing or invalid, else str(value)
        disp_text = self.text_buffer if (self.is_active or self.error_message or not self.text_buffer.isdigit()) else str(self.value)
        text_col = Palette.TEXT_MUTED if not self.is_enabled else (Palette.CRIMSON_LIGHT if self.error_message else Palette.TEXT_TITLE)
        val_surf = FontManager.mono(22).render(disp_text, True, text_col)
        val_rect = val_surf.get_rect(midleft=(input_box.x + 10, input_box.centery))
        surface.blit(val_surf, val_rect)

        # Cursor when typing
        if self.is_active and (pygame.time.get_ticks() // 500) % 2 == 0:
            cursor_x = val_rect.right + 2
            pygame.draw.line(surface, Palette.GOLD_LIGHT, (cursor_x, input_box.y + 6), (cursor_x, input_box.bottom - 6), 2)

        # Stepper buttons
        for btn in self.buttons:
            btn.is_enabled = self.is_enabled
            btn.draw(surface)


# ---------------------------------------------------------------------------
# Modal Dialog & Popups
# ---------------------------------------------------------------------------

class UIModal:
    """Semi-transparent backdrop modal dialog for notifications and options."""

    def __init__(
        self,
        title: str,
        content_lines: List[str],
        buttons: List[Tuple[str, Callable[[], None]]],
        width: int = 740,
        height: int = 460,
        monospace: bool = False,
    ) -> None:
        self.title = title
        self.width = width
        self.height = height
        self.monospace = monospace
        self.rect = pygame.Rect((1280 - width) // 2, (720 - height) // 2, width, height)

        # Word-wrap content lines so long text wraps cleanly (skip if monospace table)
        font_body = FontManager.mono(15) if monospace else FontManager.body(17)
        max_text_w = width - 72
        wrapped_lines: List[str] = []

        for raw_line in content_lines:
            if not raw_line or monospace:
                wrapped_lines.append(raw_line)
                continue
            words = raw_line.split(" ")
            current_line = []
            for w in words:
                test_line = " ".join(current_line + [w])
                if font_body.size(test_line)[0] > max_text_w and current_line:
                    wrapped_lines.append(" ".join(current_line))
                    current_line = [w]
                else:
                    current_line.append(w)
            if current_line:
                wrapped_lines.append(" ".join(current_line))

        self.content_lines = wrapped_lines

        self.action_buttons: List[UIButton] = []
        total_btns = len(buttons)
        spacing = 12
        # Dynamic button width so buttons never overflow the modal box
        max_total_btn_w = width - 60
        btn_w = min(150, (max_total_btn_w - (total_btns - 1) * spacing) // max(1, total_btns))
        btn_h = 42
        total_w = total_btns * btn_w + (total_btns - 1) * spacing
        start_x = self.rect.centerx - total_w // 2
        btn_y = self.rect.bottom - btn_h - 20

        for i, (btn_text, callback) in enumerate(buttons):
            bx = start_x + i * (btn_w + spacing)
            self.action_buttons.append(
                UIButton((bx, btn_y, btn_w, btn_h), btn_text, callback, font_size=15, primary=(i == 0))
            )

    def handle_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]) -> bool:
        for btn in self.action_buttons:
            if btn.handle_event(event, mouse_pos):
                return True
        return True  # Consume all events while modal is open

    def draw(self, surface: pygame.Surface) -> None:
        # Dim background
        dim_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
        dim_surf.fill((10, 8, 6, 210))
        surface.blit(dim_surf, (0, 0))

        # Modal panel
        pygame.draw.rect(surface, Palette.PANEL_BG, self.rect, border_radius=12)
        pygame.draw.rect(surface, Palette.GOLD_LIGHT, self.rect, width=3, border_radius=12)

        # Header bar
        header_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 56)
        pygame.draw.rect(surface, (50, 38, 28), header_rect, border_top_left_radius=12, border_top_right_radius=12)
        pygame.draw.line(surface, Palette.GOLD_BASE, (self.rect.x, self.rect.y + 56), (self.rect.right, self.rect.y + 56), 2)

        # Title text
        title_surf = FontManager.title(24).render(self.title, True, Palette.GOLD_PALE)
        title_rect = title_surf.get_rect(center=header_rect.center)
        surface.blit(title_surf, title_rect)

        # Body text lines
        font_body = FontManager.mono(15) if self.monospace else FontManager.body(16)
        curr_y = self.rect.y + 72
        line_height = 24
        for line in self.content_lines:
            if curr_y + line_height > self.rect.bottom - 75:
                break  # Don't overlap action buttons
            text_surf = font_body.render(line, True, Palette.TEXT_BODY)
            surface.blit(text_surf, (self.rect.x + 36, curr_y))
            curr_y += line_height

        # Action buttons
        for btn in self.action_buttons:
            btn.draw(surface)


# ---------------------------------------------------------------------------
# Toast Notification Banner
# ---------------------------------------------------------------------------

class UIToast:
    """Sliding feedback notification placed neatly below HUD."""

    def __init__(self, message: str, duration_sec: float = 2.5) -> None:
        self.message = message
        self.duration = duration_sec
        self.created_at = pygame.time.get_ticks()

    def is_alive(self) -> bool:
        return (pygame.time.get_ticks() - self.created_at) < (self.duration * 1000)

    def draw(self, surface: pygame.Surface) -> None:
        font = FontManager.header(17)
        text_surf = font.render(self.message, True, Palette.TEXT_TITLE)
        toast_w = text_surf.get_width() + 40
        toast_h = 38
        # Position below the top HUD in the right-hand sky area clear of cards
        tx = max(610, 1250 - toast_w)
        toast_rect = pygame.Rect(tx, 74, toast_w, toast_h)

        pygame.draw.rect(surface, (32, 26, 20), toast_rect, border_radius=8)
        pygame.draw.rect(surface, Palette.GOLD_LIGHT, toast_rect, width=2, border_radius=8)
        surface.blit(text_surf, (toast_rect.x + 20, toast_rect.y + 8))
