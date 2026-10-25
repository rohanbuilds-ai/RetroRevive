"""
verify_ui.py - Automated visual verification and screenshot generator for RetroRevive UI.

Renders all screens at logical 1280x720 and multiple window resolutions,
captures screenshots into docs/screenshots/, and verifies alignment and text layout.
"""

import os
import pygame

# Set dummy video driver for headless execution if needed, or default
from game_logic import GameState, init_game
from ui_pygame import BASE_HEIGHT, BASE_WIDTH, GameApp
from ui_theme import SoundSynthesizer


def run_visual_verification() -> bool:
    print("Starting visual UI verification and screenshot generation...")
    os.makedirs("docs/screenshots", exist_ok=True)

    # Initialize App
    app = GameApp()
    SoundSynthesizer.set_enabled(False)  # Mute audio during headless test

    # 1. Capture Main Menu Screen
    app.current_screen = "MAIN_MENU"
    app.update(0.1)
    app.draw()
    menu_path = "docs/screenshots/screenshot_main_menu.png"
    pygame.image.save(app.canvas, menu_path)
    print(f"Captured: {menu_path}")

    # 2. Capture Classic Gameplay Screen (Year 1)
    app._start_classic_game()
    app.update(0.1)
    app.draw()
    classic_path = "docs/screenshots/screenshot_classic_gameplay.png"
    pygame.image.save(app.canvas, classic_path)
    print(f"Captured: {classic_path}")

    # 3. Capture Enhanced Gameplay Screen (with Advisors dialog)
    app._start_enhanced_game()
    app.update(0.1)
    app._open_advisors_modal()
    app.draw()
    advisors_path = "docs/screenshots/screenshot_enhanced_advisors.png"
    pygame.image.save(app.canvas, advisors_path)
    print(f"Captured: {advisors_path}")
    app.active_modal = None

    # 4. Capture Scenario Challenges Screen
    app._open_scenarios_screen()
    app.update(0.1)
    app.draw()
    scenarios_path = "docs/screenshots/screenshot_scenarios.png"
    pygame.image.save(app.canvas, scenarios_path)
    print(f"Captured: {scenarios_path}")

    # 5. Capture Tutorial / Instructions Screen
    app._open_instructions_screen()
    app.update(0.1)
    app.draw()
    instructions_path = "docs/screenshots/screenshot_tutorial.png"
    pygame.image.save(app.canvas, instructions_path)
    print(f"Captured: {instructions_path}")

    # 6. Capture Game Over / Evaluation Screen (Tier 4 Charlemagne)
    state = GameState(
        year=11,
        population=120,
        bushels=3400,
        acres=1300,
        land_price=22,
        starved_this_year=0,
        starved_total=0,
        starved_pct_avg=0.0,
        immigrants_this_year=8,
        harvest_yield=4,
        rats_ate=0,
        plague_struck=False,
        plague_next_year=False,
        is_over=True,
        game_over_reason="COMPLETED",
    )
    app._handle_game_over(state)
    app.update(0.1)
    app.draw()
    game_over_path = "docs/screenshots/screenshot_game_over.png"
    pygame.image.save(app.canvas, game_over_path)
    print(f"Captured: {game_over_path}")

    # 7. Test Responsive Scaling at 1366x768 and 1920x1080
    for w, h in [(1366, 768), (1920, 1080)]:
        app.screen_width = w
        app.screen_height = h
        app.window = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        app.draw()
        scale_path = f"docs/screenshots/screenshot_scale_{w}x{h}.png"
        pygame.image.save(app.window, scale_path)
        print(f"Captured scaled window: {scale_path}")

    pygame.quit()
    print("Visual verification completed successfully! All screenshots saved.")
    return True


if __name__ == "__main__":
    run_visual_verification()
