import helper as unswbc
from helper import Direction, Tile, Position
from typing import List
from typing import TYPE_CHECKING
from memory import Memory
from constants import *
from heapq import heappop, heappush
from itertools import count

class Pathfinding:
    def __init__(self, ct: unswbc.Controller, game: unswbc.Game, memory: "Memory"):
        self.ct = ct
        self.game = game
        self.memory = memory

        # A* algo
        self._cached_path: list[Direction] = []
        self._cached_goal: Position | None = None
        self._cached_from: Position | None = None

    def can_move(self, direction: Direction) -> bool:
        """checks if it can move a direction safely"""
        here = self.ct.get_position()
        return self._passable(here, direction)

    # need to add a memory version of passible #    
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

    # ---------------- Flood fill check start ---------------------
    # returns how far the snake can potentially go
    def flood_fill_area(self, start_pos: Position, max_nodes: int) -> int:
        seen = {start_pos}
        frontier = [start_pos]

        visited_node_count: int = 0

        while frontier and visited_node_count < max_nodes:
            pos = frontier.pop()
            visited_node_count += 1
            for dir in Direction.get_direction_list():
                next_pos = pos.add_dir(dir)
                if next_pos in seen:
                    continue
                if not self._passable(pos, dir):
                    continue

                seen.add(next_pos)
                frontier.append(next_pos)
        return visited_node_count

    def move_is_safe(self, dir: Direction, required_reach: int) -> bool:
        """A move is 'safe enough' if the space behind it can fit the dragon."""
        here = self.ct.get_position()
        target = here.add_dir(dir)
        if not self._passable(here, dir):
            return False
        reached = self.flood_fill_area(target, MAX_FLOOD_NODES)
        return reached >= required_reach
    # ---------------- Flood fill check end ---------------------


    # -------------------- A* algo -------------------------------
    def _find_path_to(self, start_pos: Position, goal_pos: Position, max_nodes: int = MAX_A_STAR_NODES):
        def heuristic(pos: Position):
            # dx dy but with wrap around
            dx = min(abs(pos.x - goal_pos.x), self.game.width - abs(pos.x - goal_pos.x))
            dy = min(abs(pos.y - goal_pos.y), self.game.height - abs(pos.y - goal_pos.y))
            return dx + dy

        tie_breaker = count()
        frontier = [(heuristic(start_pos), 0, next(tie_breaker), start_pos, [])]
        # frontier = [priority, cost so far, position, path taken]
        visited = {start_pos: 0}
        nodes_expanded = 0

        while frontier and (nodes_expanded < max_nodes):
            _, cost, _, pos, path = heappop(frontier)
            nodes_expanded += 1

            if pos == goal_pos:
                return path

            for dir in Direction.get_direction_list():
                next_pos = pos.add_dir(dir)
                if not self._passable(pos, dir):
                    continue
                new_cost = cost + 1

                if next_pos not in visited or new_cost < visited[next_pos]:
                    visited[next_pos] = new_cost
                    priority = new_cost + heuristic(next_pos)
                    heappush(frontier, (priority, new_cost, next(tie_breaker), next_pos, path + [dir]))

        return None

    def _path_sill_valid(self, start_pos: Position, goal_pos: Position) -> bool:
        if not self._cached_path:
            return False
        if self._cached_goal != goal_pos:
            return False

        # check if the next tile is still valid using flood cheap (for cheaper computation)
        next_dir = self._cached_path[0]
        return self._passable(start_pos, next_dir)

    def get_next_step(self, start_pos: Position, goal_pos: Position, max_nodes: int = MAX_A_STAR_NODES) -> Direction | None:
        """Returns the next direction to move toward goal, reusing a cached
        path when it's still valid, and only recomputing when it isn't."""

        if not self._path_sill_valid(start_pos, goal_pos):
            path = self._find_path_to(start_pos, goal_pos, max_nodes)
            self._cached_path = path or []
            self._cached_goal = goal_pos

        # if it can't find a path
        if not self._cached_path:
            return None

        return self._cached_path[0]

    def has_moved_along_path(self):
        """Call this after you've actually taken the step, to consume it."""
        if self._cached_path:
            self._cached_path.pop(0)

    # def _danger_tiles(self) -> set[Position]:
    #     """Tiles occupied by enemies now, plus tiles an enemy head could reach next turn."""
    #     danger = set()
    #     for tile in self.ct.get_tiles():
    #         dragon = tile.get_dragon()
    #         if dragon is None or dragon.get_team() == self.ct.get_team():
    #             continue
    #         danger.add(tile.position)
    #         if dragon.is_head():
    #             for direction in Direction.get_direction_list():
    #                 danger.add(tile.position.add_dir(direction))
    #     return danger


            


        
            
            

 
        
    

    