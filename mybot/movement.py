import helper as unswbc
from helper import DEBUG, Direction, Position
from pathfinding import Pathfinding
from combat import Combat
from searching import Searching
import random
from memory import Memory
from constants import SAFETY_BUFFER


class Movement:
    def __init__(self, ct: unswbc.Controller, game: unswbc.Game, memory: "Memory"):
        self.memory = memory
        self.ct = ct
        self.game = game
        self.pathfinding = Pathfinding(ct, game, memory)
        self.combat = Combat(ct, self.pathfinding)
        self.searching = Searching(ct, memory, self.pathfinding)
        self.width = game.width
        self.height = game.height

        self.starting_position = ct.get_position()
        self._pick_random_direction()

    def _pick_random_direction(self):
        self.rand_dir: Direction = random.choice(unswbc._DIRECTIONS)

    def move_towards_greedy(self, pos: Position):
        here = self.ct.get_position()
        x_delta = pos.x - here.x
        y_delta = pos.y - here.y

        w_half, h_half = self.width / 2, self.height / 2
        if abs(x_delta) > w_half:
            x_delta -= self.width if x_delta > 0 else -self.width
        if abs(y_delta) > h_half:
            y_delta -= self.height if y_delta > 0 else -self.height

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
                    DEBUG(f"move: {dir.value} (greedy toward pearl)")
                    return

        DEBUG("move: no safe route toward pearl; trying random move")
        self.move_randomly()
        return

    def move_towards(self, pos: Position) -> bool:
        here = self.ct.get_position()
        direction = self.pathfinding.get_next_step(here, pos)

        if direction is None:
            DEBUG("target: unreachable; abandoning pearl")
            return False

        required_space = self.ct.get_length() + SAFETY_BUFFER
        if self.pathfinding.move_is_safe(direction, required_space):
            self.ct.make_move(direction)
            self.pathfinding.has_moved_along_path()
            DEBUG(f"move: {direction.value} (path toward pearl)")
            return True

        DEBUG(f"move: planned {direction.value} unsafe; using greedy fallback")
        self.move_towards_greedy(pos)
        return True

    def searching_behaviour(self):
        best_direction = self.searching.choose_direction()

        if best_direction is not None:
            self.ct.make_move(best_direction)
            DEBUG(f"move: {best_direction.value} (search)")
        else:
            DEBUG("move: no safe scored direction; trying random move")
            self.move_randomly()

    def move_randomly(self) -> None:
        directions = unswbc._DIRECTIONS[::]
        random.shuffle(directions)
        for direction in directions:
            if self.pathfinding.can_move(direction):
                self.ct.make_move(direction)
                DEBUG(f"move: {direction.value} (random fallback)")
                return

        self.force_move_forwards()

    def force_move_forwards(self) -> None:
        self.ct.make_move(self.ct.get_dir())
        DEBUG("move: forced forward (no safe direction found)")

    def execute(self):
        pearl_location = self.memory.get_target_pearl()
        if self.combat.execute():
            return

        if pearl_location is not None:
            DEBUG(f"decision: pearl target {pearl_location}")
            if self.move_towards(pearl_location):
                return

            self.memory.give_up_on_target_pearl()
            self.searching_behaviour()
            DEBUG("decision: searching for unexplored space")
            

        else:
            DEBUG("decision: searching for unexplored space")
            self.searching_behaviour()

    def draw_cached_path(self):
        self.pathfinding.draw_cached_path()