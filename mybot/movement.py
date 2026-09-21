import unswbc
import helper as unswbc
from helper import Direction, Tile
from typing import List
from typing import TYPE_CHECKING
from pathfinding import Pathfinding
import random
from memory import Memory


type coords = list[(int, int)]

class Movement:
    def __init__(self, ct: unswbc.Controller, game: unswbc.Game, memory: "Memory"):
        self.memory = memory
        self.ct = ct
        self.game = game
        self.pathfinding = Pathfinding(ct, game, memory)

        self.starting_position = ct.get_position()
        self._pick_random_dir()

    def _pick_random_dir(self):
        self.rand_dir: Direction = random.choice(Direction.get_direction_list())
        self.ct.output_log(f"I chose {self.rand_dir}")

    def move(self):
        if self.pathfinding.is_safe(self.rand_dir):
            self.ct.make_move(self.rand_dir)
        else:
            directions = Direction.get_direction_list()
            random.shuffle(directions)
            for direction in directions:
                if self.pathfinding.is_safe(direction):
                    self.ct.make_move(direction)
                    return

            self.ct.make_move(self.ct.get_dir())

                

        

    

    