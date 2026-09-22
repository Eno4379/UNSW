import helper as unswbc
from helper import Direction, Tile, Position
from typing import List
from typing import TYPE_CHECKING
from pathfinding import Pathfinding
import random
from memory import Memory
from constants import *


type coords = list[(int, int)]

class Movement:
    def __init__(self, ct: unswbc.Controller, game: unswbc.Game, memory: "Memory"):
        self.memory = memory
        self.ct = ct
        self.game = game
        self.pathfinding = Pathfinding(ct, game, memory)

        self.starting_position = ct.get_position()
        self._pick_random_direction()

    def _pick_random_direction(self):
        self.rand_dir: Direction = random.choice(Direction.get_direction_list())
        self.ct.output_log(f"I chose {self.rand_dir}")


    # dumb algorithm to move towards the position
    def move_towards_greedy(self, pos: Position):
        here = self.ct.get_position()
        x_delta = pos.x - here.x
        y_delta = pos.y - here.y

        # Choose the shorter route across the wrapped map edges.
        if abs(x_delta) > self.game.width / 2:
            x_delta -= self.game.width if x_delta > 0 else -self.game.width
        if abs(y_delta) > self.game.height / 2:
            y_delta -= self.game.height if y_delta > 0 else -self.game.height

        directions_to_move_in = []
        if x_delta > 0:
            directions_to_move_in.append(Direction.EAST)
        if x_delta < 0:
            directions_to_move_in.append(Direction.WEST)
        if y_delta > 0:
            directions_to_move_in.append(Direction.SOUTH)
        if y_delta < 0:
            directions_to_move_in.append(Direction.NORTH)     

        required_space = self.ct.get_length() + SAFETY_BUFFER
        if directions_to_move_in:
            for dir in directions_to_move_in:
                if self.pathfinding.move_is_safe(dir, required_space):
                    self.ct.make_move(dir)
                    return

        self.ct.output_log("Couldn't find a safe move towards the pearl, now moving randomly")
        self.move_randomly()
        return

    def move_towards(self, pos: Position) -> bool:
        """Tries to move toward pos. Returns False if the target is unreachable."""
        here = self.ct.get_position()
        self.ct.output_log(f"target={pos.x},{pos.y} from={here.x},{here.y}")
        direction = self.pathfinding.get_next_step(here, pos)

        if direction is None:
            self.ct.output_log("target unreachable; abandoning target")
            return False  # unreachable within known/optimistic map

        required_space = self.ct.get_length() + SAFETY_BUFFER
        self.ct.output_log(f"path suggests {direction}; required space={required_space}")
        if self.pathfinding.move_is_safe(direction, required_space):
            self.ct.output_log(f"moving toward target: {direction}")
            self.ct.make_move(direction)
            self.pathfinding.has_moved_along_path()
            return True

        # path exists but next step looks unsafe right now — nudge closer,
        # stay committed to the target
        self.ct.output_log(f"path step {direction} unsafe; using greedy fallback")
        self.move_towards_greedy(pos)
        return True

    def searching_behaviour(self):
        here = self.ct.get_position()
        directions = Direction.get_direction_list()
        random.shuffle(directions)

        self.ct.output_log(f"searching from {here.x},{here.y}")

        best_direction = None
        best_score = float("-inf")

        for direction in directions:
            if not self.pathfinding.move_is_safe(direction, self.ct.get_length()):
                self.ct.output_log(f"search rejected {direction}: unsafe")
                continue

            exploration_score = self.memory.count_unexplored_ahead(here, direction, EXPLORATION_LOOKAHEAD)
            crowd_score = self._crowd_repulsion_score(direction)

            score = (EXPLORATION_WEIGHT * exploration_score) + (CROWD_AVOIDANCE_WEIGHT * crowd_score)
            self.ct.output_log(
                f"search option {direction}: unexplored={exploration_score}, "
                f"away={crowd_score:.2f}, score={score:.2f}"
            )

            self_length = self.ct.get_length()
            if score > best_score:
                best_score = score
                best_direction = direction

        if best_direction is not None:
            self.ct.output_log(f"search chose {best_direction} with score={best_score:.2f}")
            self.ct.make_move(best_direction)
        else:
            self.ct.output_log("search found no scored direction; moving randomly")
            self.move_randomly()

    def move_randomly(self) -> None:
        directions = Direction.get_direction_list()
        random.shuffle(directions)
        for direction in directions:
            if self.pathfinding.can_move(direction):
                self.ct.output_log(f"random move selected: {direction}")
                self.ct.make_move(direction)
                return

        self.ct.output_log("no safe move found; forcing forward move")
        self.force_move_forwards()

    def force_move_forwards(self) -> None:
        self.ct.make_move(self.ct.get_dir())  
        self.ct.output_log("Couldn't find a safe move, now moving fowards")

    # ----------------- crowd avoidance --------------------
    def _crowd_repulsion_score(self, direction: Direction) -> float:
        """Higher = moving further away from the average teammate position."""
        teammates = self.memory.get_teammate_positions()
        if not teammates:
            return 0.0

        here = self.ct.get_position()

        # average wrapped offset to teammates gives a rough centroid direction
        avg_dx, avg_dy = 0.0, 0.0
        for pos in teammates:
            dx, dy = self.pathfinding.wrapped_delta(here, pos)
            avg_dx += dx
            avg_dy += dy
        avg_dx /= len(teammates)
        avg_dy /= len(teammates)

        move_dx, move_dy = direction.get_offset()
        # negative dot product = moving opposite to the crowd = good
        return -(move_dx * avg_dx + move_dy * avg_dy)
    # ----------------- crowd avoidance --------------------

            
    def execute(self):
        pearl_location = self.memory.get_target_pearl()
        if pearl_location is not None:
            self.ct.output_log("target pearl found")
            if self.move_towards(pearl_location):
                return
            self.memory.give_up_on_target_pearl()
            self.ct.output_log("target abandoned; searching instead")

        self.ct.output_log(f"no target; SEARCHING BEHAVIOUR")
        self.searching_behaviour()


    def draw_cached_path(self):
        self.pathfinding.draw_cached_path()