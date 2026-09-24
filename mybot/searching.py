import helper as unswbc
from random import shuffle

from constants import *
from helper import DEBUG, Direction, Position
from memory import Memory
from pathfinding import Pathfinding


class Searching:
    """Chooses the safest, most useful direction when no higher-priority target exists."""

    def __init__(self, ct: unswbc.Controller, game: unswbc.Game, memory: Memory, pathfinding: Pathfinding):
        self.ct = ct
        self.memory = memory
        self.game = game
        self.pathfinding = pathfinding

    def choose_direction(self) -> Direction | None:
        """Return the best safe search direction, or None when all are unsafe. Defaults to moving away from crowds."""
        here = self.ct.get_position()
        directions = unswbc._DIRECTIONS[::]
        shuffle(directions)
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
            pearl_anchor_score = self._pearl_anchor_score(here, direction)
            exploration_weighted = EXPLORATION_WEIGHT * exploration_score
            crowd_weighted = CROWD_AVOIDANCE_WEIGHT * crowd_score
            pearl_anchor_weighted = PEARL_ANCHOR_WEIGHT * pearl_anchor_score

            score = exploration_weighted + crowd_weighted + pearl_anchor_weighted

            DEBUG(
                f"search {direction.value}: total={score:.1f} | "
                f"explore {exploration_score:.1f} x {EXPLORATION_WEIGHT:.1f}="
                f"{exploration_weighted:.1f} | "
                f"crowd {crowd_score:.1f} x {CROWD_AVOIDANCE_WEIGHT:.1f}="
                f"{crowd_weighted:.1f} | "
                f"pearl anchor {pearl_anchor_score:.1f} x "
                f"{PEARL_ANCHOR_WEIGHT:.1f}={pearl_anchor_weighted:.1f}"
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

    def _pearl_anchor_score(self, here: Position, direction: Direction) -> float:
        """Penalises moving further from the current pearl hot-zone anchor, if one is set.
        Returns 0.0 when no anchor exists, so this term is inert until the snake commits to one."""
        anchor = self.memory.pearl_anchor
        if anchor is None:
            return 0.0

        current_dx, current_dy = self.pathfinding.wrapped_delta(here, anchor)
        current_distance = abs(current_dx) + abs(current_dy)

        candidate = here.add_dir(direction)
        candidate_dx, candidate_dy = self.pathfinding.wrapped_delta(candidate, anchor)
        candidate_distance = abs(candidate_dx) + abs(candidate_dy)

        step_reward = current_distance - candidate_distance
        distance_penalty = candidate_distance * DISTANCE_FROM_PEARL_ANCHOR_PENALTY_WEIGHT

        # positive when this direction moves closer to the anchor, negative when it moves away
        DEBUG(
            f"anchor: here={here}, target={anchor}, "
            f"direction={direction.value}, "
            f"step_reward={current_distance}, "
            f"distance_penalty={distance_penalty}, "
            f"score={step_reward - distance_penalty:.3f}"
        )
        return step_reward - distance_penalty