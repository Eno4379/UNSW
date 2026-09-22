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
        """checks if it can move a direction without dying immediately"""
        here = self.ct.get_position()
        return self._passable(here, direction)

    # need to add a memory version of passible #    
    def _passable(self, pos: Position, direction: Direction) -> bool:
        tile = self.memory.board[pos.x][pos.y]
        if tile is None:
            return True  # unexplored — optimistic

        edge = tile.get_edge(direction)
        if edge.get_edge_type() == unswbc.EdgeType.KELP:
            return False

        ahead_pos = pos.add_dir(direction)
        ahead_live = self.ct.get_tile(ahead_pos)  # live vision, not memory
        if ahead_live is not None and ahead_live.get_dragon() is not None:
            return False

        return True  # either clear, or outside vision — optimistic on occupancy

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

    def get_next_step(self, start_pos: Position, goal_pos: Position, 
                      max_a_star_nodes: int = MAX_A_STAR_NODES,
                      max_reachability_nodes: int = MAX_REACHABILITY_NODES) -> Direction | None:
        """Returns the next direction to move toward goal, reusing a cached
        path when it's still valid, and only recomputing when it isn't."""

        if not self._reachable(start_pos, goal_pos, max_reachability_nodes):
            self.ct.output_log(f"A* target {goal_pos.x},{goal_pos.y} unreachable")
            self._cached_path = []
            self._cached_goal = goal_pos
            return None

        if not self._path_sill_valid(start_pos, goal_pos):
            path = self._find_path_to(start_pos, goal_pos, max_a_star_nodes)
            self._cached_path = path or []
            self._cached_goal = goal_pos
            self.ct.output_log(f"A* path recalculated: {len(self._cached_path)} steps")

        if not self._cached_path:
            return None

        return self._cached_path[0]
    

    def has_moved_along_path(self):
        """Call this after you've actually taken the step, to consume it."""
        if self._cached_path:
            self._cached_path.pop(0)

    def _reachable(self, start_pos: Position, goal_pos: Position, max_nodes: int = MAX_REACHABILITY_NODES) -> bool:
        """Cheap check: is goal_pos in the same connected region as start_pos?
        Stops as soon as the goal is found, or once max_nodes is exhausted."""
        if start_pos == goal_pos:
            return True

        seen = {start_pos}
        frontier = [start_pos]
        visited_node_count = 0

        while frontier and visited_node_count < max_nodes:
            pos = frontier.pop()
            visited_node_count += 1

            for dir in Direction.get_direction_list():
                next_pos = pos.add_dir(dir)
                if next_pos in seen:
                    continue
                if not self._passable(pos, dir):
                    continue
                if next_pos == goal_pos:
                    return True

                seen.add(next_pos)
                frontier.append(next_pos)

        return False
    # -------------------- A* algo -------------------------------

    def wrapped_delta(self, from_pos: Position, to_pos: Position) -> tuple[float, float]:
        """Shortest x/y offset from from_pos to to_pos, accounting for map wraparound."""
        dx = to_pos.x - from_pos.x
        dy = to_pos.y - from_pos.y
        if abs(dx) > self.game.width / 2:
            dx -= self.game.width if dx > 0 else -self.game.width
        if abs(dy) > self.game.height / 2:
            dy -= self.game.height if dy > 0 else -self.game.height
        return dx, dy


    def draw_cached_path(self):
        if not self._cached_path:
            return

        current = self.ct.get_position()
        for direction in self._cached_path:
            next_position = current.add_dir(direction)
            self.ct.draw_indicator_line(current, next_position, 50, 50, 50)
            current = next_position

        if self._cached_goal is not None:
            self.ct.draw_indicator_dot(self._cached_goal, 255, 255, 0)



        
            
            

 
        
    

    