"""
games/hunt_the_wumpus/test_engine.py - Comprehensive automated tests for Hunt the Wumpus engine.
"""

import collections
import random
import unittest

from games.hunt_the_wumpus import engine


class TestDodecahedronTopology(unittest.TestCase):
    """Verifies the mathematical properties of Gregory Yob's 20-vertex dodecahedron graph."""

    def test_20_rooms_exist(self) -> None:
        self.assertEqual(len(engine.DODECAHEDRON_ROOMS), 20)
        self.assertEqual(set(engine.DODECAHEDRON_ROOMS.keys()), set(range(1, 21)))

    def test_every_room_has_degree_three(self) -> None:
        for room, neighbors in engine.DODECAHEDRON_ROOMS.items():
            self.assertEqual(len(neighbors), 3, f"Room {room} must have exactly 3 neighbors")
            self.assertEqual(len(set(neighbors)), 3, f"Room {room} must not have duplicate neighbors")
            self.assertNotIn(room, neighbors, f"Room {room} cannot connect to itself")

    def test_graph_edges_are_bidirectional_and_symmetric(self) -> None:
        for room, neighbors in engine.DODECAHEDRON_ROOMS.items():
            for n in neighbors:
                self.assertIn(
                    room,
                    engine.DODECAHEDRON_ROOMS[n],
                    f"Edge ({room} -> {n}) must be bidirectional, but {room} not in neighbors of {n}",
                )

    def test_graph_is_fully_connected(self) -> None:
        visited = set()
        queue = collections.deque([1])
        while queue:
            curr = queue.popleft()
            if curr in visited:
                continue
            visited.add(curr)
            for n in engine.DODECAHEDRON_ROOMS[curr]:
                if n not in visited:
                    queue.append(n)
        self.assertEqual(len(visited), 20, "Every room in the dodecahedron must be reachable")

    def test_planar_schlegel_coordinates(self) -> None:
        self.assertEqual(len(engine.DODECAHEDRON_COORDS), 20)
        for room, (x, y) in engine.DODECAHEDRON_COORDS.items():
            self.assertTrue(0.0 <= x <= 1.0, f"X coord for Room {room} must be in [0, 1]")
            self.assertTrue(0.0 <= y <= 1.0, f"Y coord for Room {room} must be in [0, 1]")


class TestWumpusInitialConditions(unittest.TestCase):
    """Verifies safe startup, hazard placement, and default inventory."""

    def test_deterministic_initial_placement(self) -> None:
        state = engine.init_game(seed=42)
        self.assertEqual(state.arrows, 5)
        self.assertFalse(state.is_game_over)
        self.assertFalse(state.victory)
        self.assertEqual(len(state.pit_rooms), 2)
        self.assertEqual(len(state.bat_rooms), 2)

        # Hunter must not spawn in hazard room
        self.assertNotEqual(state.hunter_room, state.wumpus_room)
        self.assertNotIn(state.hunter_room, state.pit_rooms)
        self.assertNotIn(state.hunter_room, state.bat_rooms)

        # Visited rooms contains initial room
        self.assertIn(state.hunter_room, state.visited_rooms)

    def test_random_initialization_distinct_entities(self) -> None:
        state = engine.init_game()
        entities = {state.hunter_room, state.wumpus_room} | state.pit_rooms | state.bat_rooms
        self.assertEqual(len(entities), 6, "Hunter, Wumpus, 2 pits, and 2 bats must all occupy distinct rooms")


class TestSensoryWarnings(unittest.TestCase):
    """Verifies smelling the Wumpus, feeling drafts, and hearing bats."""

    def test_smell_wumpus_when_adjacent(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1  # neighbors: 2, 5, 8
        state.wumpus_room = 2
        state.pit_rooms = {15, 16}
        state.bat_rooms = {17, 18}

        warnings = engine.get_sensory_warnings(state)
        self.assertTrue(warnings.smell_wumpus)
        self.assertFalse(warnings.feel_draft)
        self.assertFalse(warnings.hear_bats)

    def test_feel_draft_when_pit_adjacent(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1  # neighbors: 2, 5, 8
        state.wumpus_room = 20
        state.pit_rooms = {5, 16}  # 5 is adjacent
        state.bat_rooms = {17, 18}

        warnings = engine.get_sensory_warnings(state)
        self.assertFalse(warnings.smell_wumpus)
        self.assertTrue(warnings.feel_draft)
        self.assertFalse(warnings.hear_bats)

    def test_hear_bats_when_bats_adjacent(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1  # neighbors: 2, 5, 8
        state.wumpus_room = 20
        state.pit_rooms = {15, 16}
        state.bat_rooms = {8, 18}  # 8 is adjacent

        warnings = engine.get_sensory_warnings(state)
        self.assertFalse(warnings.smell_wumpus)
        self.assertFalse(warnings.feel_draft)
        self.assertTrue(warnings.hear_bats)

    def test_no_warnings_when_distant(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1  # neighbors: 2, 5, 8
        state.wumpus_room = 20
        state.pit_rooms = {13, 14}
        state.bat_rooms = {16, 19}

        warnings = engine.get_sensory_warnings(state)
        self.assertFalse(warnings.smell_wumpus)
        self.assertFalse(warnings.feel_draft)
        self.assertFalse(warnings.hear_bats)


class TestMovementAndHazards(unittest.TestCase):
    """Verifies movement, hazard triggering, and super bat relocation."""

    def test_legal_move_updates_room(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1
        state.wumpus_room = 20
        state.pit_rooms = {13, 14}
        state.bat_rooms = {16, 19}

        res = engine.move_hunter(state, 2)
        self.assertTrue(res.success)
        self.assertEqual(state.hunter_room, 2)
        self.assertIn(2, state.visited_rooms)

    def test_illegal_move_rejected(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1  # neighbors: 2, 5, 8
        res = engine.move_hunter(state, 20)  # Room 20 is not connected to 1
        self.assertFalse(res.success)
        self.assertEqual(state.hunter_room, 1)

    def test_fatal_pit_encounter(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1
        state.pit_rooms = {2, 14}
        res = engine.move_hunter(state, 2)
        self.assertTrue(res.success)
        self.assertTrue(state.is_game_over)
        self.assertFalse(state.victory)
        self.assertIn("FELL IN PIT", state.game_over_reason)

    def test_fatal_wumpus_encounter(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1
        state.wumpus_room = 5
        res = engine.move_hunter(state, 5)
        self.assertTrue(res.success)
        self.assertTrue(state.is_game_over)
        self.assertFalse(state.victory)
        self.assertIn("WUMPUS GOT YOU", state.game_over_reason)

    def test_super_bat_transports_hunter(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1
        state.bat_rooms = {8, 19}
        state.wumpus_room = 20
        state.pit_rooms = {13, 14}

        rng = random.Random(99)
        res = engine.move_hunter(state, 8, rng=rng)
        self.assertTrue(res.success)
        self.assertTrue(res.bat_transported)
        self.assertIn(state.hunter_room, state.visited_rooms)


class TestCrookedArrowCombat(unittest.TestCase):
    """Verifies arrow pathing, ricochets, Wumpus slaying, and ammo exhaustion."""

    def test_direct_hit_slays_wumpus_victory(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1  # 1 -> 2 -> 3
        state.wumpus_room = 3
        self.assertEqual(state.arrows, 5)

        res = engine.shoot_arrow(state, [2, 3])
        self.assertTrue(res.success)
        self.assertTrue(state.is_game_over)
        self.assertTrue(state.victory)
        self.assertEqual(state.arrows, 4)
        self.assertIn("YOU GOT THE WUMPUS", state.game_over_reason)

    def test_arrow_ricochet_strikes_hunter_defeat(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1  # 1 -> 2 -> 1
        state.wumpus_room = 20

        res = engine.shoot_arrow(state, [2, 1])
        self.assertTrue(res.success)
        self.assertTrue(state.is_game_over)
        self.assertFalse(state.victory)
        self.assertIn("ARROW STRUCK YOU", state.game_over_reason)

    def test_arrow_exhaustion_triggers_defeat(self) -> None:
        state = engine.init_game(seed=10)
        state.hunter_room = 1
        state.wumpus_room = 20
        state.arrows = 1

        # Prevent wumpus from stumbling into hunter room during stir
        mock_rng = random.Random(1234)
        res = engine.shoot_arrow(state, [2], rng=mock_rng)
        self.assertTrue(res.success)
        self.assertEqual(state.arrows, 0)
        self.assertTrue(state.is_game_over)
        self.assertFalse(state.victory)

    def test_arrow_path_length_validation(self) -> None:
        state = engine.init_game(seed=10)
        res_empty = engine.shoot_arrow(state, [])
        self.assertFalse(res_empty.success)

        res_long = engine.shoot_arrow(state, [1, 2, 3, 4, 5, 6])
        self.assertFalse(res_long.success)


if __name__ == "__main__":
    unittest.main()
