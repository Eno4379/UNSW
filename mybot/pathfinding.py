import helper as unswbc
from helper import Direction, Tile, Position
from typing import List
from typing import TYPE_CHECKING
from memory import Memory
from constants import *

class Pathfinding:
    def __init__(self, ct: unswbc.Controller, game: unswbc.Game, memory: "Memory"):
        self.ct = ct
        self.game = game
        self.memory = memory

    def can_move(self, direction: Direction) -> bool:
        """checks if it can move a direction safely"""
        here = self.ct.get_position()
        return self._passable(here, direction)
        
    def _passable(self, pos: Position, direction: Direction) -> bool:
        """given a tile, checks if its safe to move in a direction"""
        tile = self.ct.get_tile(pos)

        if tile is None:
            return False
        
        edge = tile.get_edge(direction)
        if edge.get_edge_type() == unswbc.EdgeType.KELP:
            return False

        ahead = self.ct.get_tile(pos.add_dir(direction))

        if ahead is None or ahead.get_dragon() is None:
            return True
        
        return False

    # returns how far the snake can potentially go
    def flood_fill_area(self, start_pos: Position, max_nodes: int) -> int:
        seen = {start_pos}
        frontier = [start_pos]

        visited_node_count: int = 0

        while frontier and visited_node_count < max_nodes:
            pos = frontier.pop()
            visited_node_count += 1
            for dir in Direction.get_direction_list():
                next = pos.add_dir(dir)
                if next in seen:
                    continue
                if not self._passable(pos, dir):
                    continue

                seen.add(next)
                frontier.append(next)
        return visited_node_count

    def move_is_safe(self, dir: Direction, required_reach: int) -> bool:
        """A move is 'safe enough' if the space behind it can fit the dragon."""
        here = self.ct.get_position()
        target = here.add_dir(dir)
        if not self._passable(here, dir):
            return False
        reached = self.flood_fill_area(target, MAX_FLOOD_NODES)
        return reached >= required_reach

    # def has_two_escapes_from(self, pos: Position):
    #     n_of_
    #     for dir in Direction.get_direction_list():
            

 
        
    

    