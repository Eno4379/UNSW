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

    def move_towards(self, pos: Position):
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


    def searching_behaviour(self):
        if self.pathfinding.can_move(self.rand_dir):
            self.ct.make_move(self.rand_dir)
        else:
            self.move_randomly()

    def move_randomly(self) -> None:
        directions = Direction.get_direction_list()
        random.shuffle(directions)
        for direction in directions:
            if self.pathfinding.can_move(direction):
                self.ct.make_move(direction)
                return

        self.force_move_forwards()

    def force_move_forwards(self) -> None:
        self.ct.make_move(self.ct.get_dir())  
        self.ct.output_log("Couldn't find a safe move, now moving fowards")

            
    def execute(self):
        if pearl_location := self.memory.pearl_within_vision():
            self.ct.output_log(f"currently moving towards pearl at {pearl_location.x, pearl_location.y}")
            self.move_towards(pearl_location)
        else:
            self.ct.output_log(f"searching behaviour with direction: {self.rand_dir}")
            self.searching_behaviour()
