import helper as unswbc
from collections import deque
from heapq import heappop, heappush
from itertools import count

from constants import *
from helper import Direction, Position, Tile
from memory import Memory

class Pathfinding:
    def __init__(self, ct: unswbc.Controller, game: unswbc.Game, memory: "Memory"):
        self.ct = ct
        self.game = game
        self.memory = memory
        self.width = game.width
        self.height = game.height

        # A* algo
        self._cached_path: list[Direction] = []
        self._cached_goal: Position | None = None
        self._cached_from: Position | None = None

    def can_move(self, direction: Direction) -> bool:
        """checks if it can move a direction without dying immediately"""
        here = self.ct.get_position()
        return self._passable(here, direction)

    def _passable(self, pos: Position, direction: Direction) -> bool:
        tile = self.memory.board[pos.x][pos.y]
        if tile is None:
            return True  # unexplored — optimistic

        edge = tile.get_edge(direction)
        if edge.get_edge_type() == unswbc.EdgeType.KELP:
            return False

        ahead_pos = pos.add_dir(direction)
        ahead_live = self.ct.get_tile(ahead_pos)  # live vision, not memory — dragons move
        if ahead_live is not None and ahead_live.get_dragon() is not None:
            return False

        # makes sure it doesn't reverse after going through a portal
        if pos == self.ct.get_position():
            behind_direction = self.ct.get_dir().get_opposite()
            edge_behind_dragon_head = tile.get_edge(behind_direction)
            if edge_behind_dragon_head.get_edge_type() == unswbc.EdgeType.PORTAL:
                if direction == behind_direction:
                    return False 

        return True  # either clear, or outside vision — optimistic on occupancy

    # ---------------- Flood fill check start ---------------------
    def flood_fill_area(self, start_pos: Position, max_nodes: int) -> int:
        """Explores outward in solid concentric rings (BFS), counting reachable open space."""
        seen = {start_pos}
        frontier = deque([start_pos])  # FIFO Queue for true Breadth-First Search
        visited_node_count = 0
        directions = unswbc._DIRECTIONS  # Reuse global list to prevent allocations

        while frontier and visited_node_count < max_nodes:
            pos = frontier.popleft()    # Process closest tiles first
            visited_node_count += 1

            for dir in directions:
                next_pos = pos.add_dir(dir)
                if next_pos in seen:
                    continue
                if not self._passable(pos, dir):
                    continue

                seen.add(next_pos)      # Mark SEEN immediately when queuing to avoid duplicate entries
                frontier.append(next_pos)

        # if DEBUG:
        #     for pos in seen:
        #         self.ct.draw_indicator_dot(pos, 50, 90, 90)
        #     self.ct.output_log(f"flood_fill_area: reached={visited_node_count}, seen={len(seen)}")

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
        w, h = self.width, self.height
        def heuristic(pos: Position):
            dx = min(abs(pos.x - goal_pos.x), w - abs(pos.x - goal_pos.x))
            dy = min(abs(pos.y - goal_pos.y), h - abs(pos.y - goal_pos.y))
            return dx + dy

        tie_breaker = count()
        frontier = [(heuristic(start_pos), 0, next(tie_breaker), start_pos, [])]
        visited = {start_pos: 0}
        nodes_expanded = 0
        directions = unswbc._DIRECTIONS

        while frontier and (nodes_expanded < max_nodes):
            _, cost, _, pos, path = heappop(frontier)
            nodes_expanded += 1

            if pos == goal_pos:
                return path

            for dir in directions:
                next_pos = pos.add_dir(dir)
                if not self._passable(pos, dir):
                    continue
                new_cost = cost + 1

                if next_pos not in visited or new_cost < visited[next_pos]:
                    visited[next_pos] = new_cost
                    priority = new_cost + heuristic(next_pos)
                    heappush(frontier, (priority, new_cost, next(tie_breaker), next_pos, path + [dir]))

        return None

    def _path_still_valid(self, start_pos: Position, goal_pos: Position) -> bool:
        if not self._cached_path:
            return False
        if self._cached_goal != goal_pos:
            return False

        next_dir = self._cached_path[0]
        return self._passable(start_pos, next_dir)

    def get_next_step(self, start_pos: Position, goal_pos: Position,
                      max_a_star_nodes: int = MAX_A_STAR_NODES,
                      max_reachability_nodes: int = MAX_REACHABILITY_NODES) -> Direction | None:
        if PATHFINDING_CACHE_ENABLED and self._path_still_valid(start_pos, goal_pos):
            return self._cached_path[0]

        if not self._reachable(start_pos, goal_pos, max_reachability_nodes):
            self._cached_path = []
            self._cached_goal = goal_pos
            return None

        path = self._find_path_to(start_pos, goal_pos, max_a_star_nodes)
        if PATHFINDING_CACHE_ENABLED:
            self._cached_path = path or []
            self._cached_goal = goal_pos
            return self._cached_path[0] if self._cached_path else None
        else:
            self._cached_path = []
            self._cached_goal = None
            return path[0] if path else None

    def has_moved_along_path(self):
        if self._cached_path:
            self._cached_path.pop(0)

    def _reachable(self, start_pos: Position, goal_pos: Position, max_nodes: int = MAX_REACHABILITY_NODES) -> bool:
        """Checks if goal_pos is connected to start_pos via a solid BFS flood-fill expansion."""
        if start_pos == goal_pos:
            return True

        seen = {start_pos}
        frontier = deque([start_pos])
        visited_node_count = 0
        directions = unswbc._DIRECTIONS

        while frontier and visited_node_count < max_nodes:
            pos = frontier.popleft()
            visited_node_count += 1

            for dir in directions:
                next_pos = pos.add_dir(dir)
                if next_pos in seen:
                    continue
                if not self._passable(pos, dir):
                    continue
                if next_pos == goal_pos:
                    return True

                seen.add(next_pos)      # Mark SEEN immediately when queuing
                frontier.append(next_pos)

        # if DEBUG:
        #     for pos in seen:
        #         self.ct.draw_indicator_dot(pos, 90, 90, 50)
        #     self.ct.output_log(f"_reachable: goal not found, visited={visited_node_count}, seen={len(seen)}")

        return False
    # -------------------- A* algo -------------------------------


    def wrapped_delta(self, from_pos: Position, to_pos: Position) -> tuple[float, float]:
        dx = to_pos.x - from_pos.x
        dy = to_pos.y - from_pos.y
        w_half, h_half = self.width / 2, self.height / 2
        if abs(dx) > w_half:
            dx -= self.width if dx > 0 else -self.width
        if abs(dy) > h_half:
            dy -= self.height if dy > 0 else -self.height
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


    