import unswbc
import helper as unswbc
from helper import Direction, Tile
from typing import List
from typing import TYPE_CHECKING
from memory import Memory

class Pathfinding:
    def __init__(self, ct: unswbc.Controller, game: unswbc.Game, memory: "Memory"):
        self.ct = ct
        self.game = game
        self.memory = memory
        

    def is_safe(self, direction: Direction) -> bool:
        here = self.ct.get_position()
        tile = self.ct.get_tile(here)
        if tile is None:
            return False

        edge = tile.get_edge(direction)
        if edge.get_edge_type() == unswbc.EdgeType.KELP:
            return False

        ahead = self.ct.get_tile(here.add_dir(direction))

        if ahead is None or ahead.get_dragon() is None:
            return True

        return False

    

    