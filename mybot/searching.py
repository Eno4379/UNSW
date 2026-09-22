import random

import helper as unswbc
from helper import Direction, DEBUG
from memory import Memory
from pathfinding import Pathfinding
from constants import *


class Searching:
    """Chooses the safest, most useful direction when no higher-priority target exists."""

    def __init__(self, ct: unswbc.Controller, memory: Memory, pathfinding: Pathfinding):
        self.ct = ct
        self.memory = memory
        self.pathfinding = pathfinding

    def choose_direction(self) -> Direction | None:
        """Return the best safe search direction, or None when all are unsafe."""
        here = self.ct.get_position()
        directions = unswbc._DIRECTIONS[::]
        random.shuffle(directions)
        teammates = self.memory.get_teammate_positions()
        required_space = self.ct.get_length() + SAFETY_BUFFER

        best_direction = None
        best_score = float("-inf")

        for direction in directions:
            if not self.pathfinding.move_is_safe(direction, required_space):
                DEBUG(f"search: {direction.value} unsafe")
                continue

            exploration_score = self.memory.count_unexplored_ahead(
                here, direction, EXPLORATION_LOOKAHEAD
            )
            crowd_score = self._crowd_repulsion_score(here, direction, teammates)
            exploration_weighted = EXPLORATION_WEIGHT * exploration_score
            crowd_weighted = CROWD_AVOIDANCE_WEIGHT * crowd_score
            score = exploration_weighted + crowd_weighted

            DEBUG(
                f"search: {direction.value} score={score:.1f} "
                f"(explore={exploration_score:.1f}*{EXPLORATION_WEIGHT:.1f}="
                f"{exploration_weighted:.1f}, crowd={crowd_score:.1f}*"
                f"{CROWD_AVOIDANCE_WEIGHT:.1f}={crowd_weighted:.1f})"
            )

            if score > best_score:
                best_score = score
                best_direction = direction

        return best_direction

    def _crowd_repulsion_score(
        self, here, direction: Direction, teammates: list
    ) -> float:
        if not teammates:
            return 0.0

        avg_dx, avg_dy = 0.0, 0.0
        for position in teammates:
            dx, dy = self.pathfinding.wrapped_delta(here, position)
            avg_dx += dx
            avg_dy += dy
        avg_dx /= len(teammates)
        avg_dy /= len(teammates)

        move_dx, move_dy = direction.get_offset()
        return -(move_dx * avg_dx + move_dy * avg_dy)
