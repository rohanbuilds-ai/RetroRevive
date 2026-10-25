"""
games/__init__.py - Games package for RetroRevive platform.

Provides clean module access even for directories with leading digits.
"""

import importlib

# Dynamic module imports to bypass Python syntax limitation on leading digits (23_matches)
matches_engine = importlib.import_module("games.23_matches.engine")
matches_app = importlib.import_module("games.23_matches.app")
lander_engine = importlib.import_module("games.lunar_lander.engine")
lander_app = importlib.import_module("games.lunar_lander.app")
oregon_engine = importlib.import_module("games.oregon_trail.engine")
oregon_app = importlib.import_module("games.oregon_trail.app")

__all__ = ["matches_engine", "matches_app", "lander_engine", "lander_app", "oregon_engine", "oregon_app"]
