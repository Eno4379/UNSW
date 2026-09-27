import helper as unswbc
from collections import deque
from random import sample
from typing import List

from constants import *
from helper import DEBUG, Direction, EdgeType, Position, Tile

class Memory:
    def __init__(self, ct: unswbc.Controller, game: unswbc.Game):
        self.ct = ct
        self.game = game
        self.width, self.height = game.get_map_size()
        self.spawn_round = game.get_round_num()

        self.board: List[List[Tile | None]]
        self.board = [[None] * self.height for _ in range(self.width)]

        self.pearl_board = [[UNOBSERVED_PEARL_TIME] * self.height for _ in range(self.width)]
        # highest countdown ever observed on each tile
        # stays at the unobserved sentinel until a tile has been seen at least once
        self.maximum_pearl_board = [[UNOBSERVED_PEARL_TIME] * self.height for _ in range(self.width)]
        self.worst_max_pearl_time = float("inf")

        self.target_pearl: Position | None = None
        self.known_portal_ids = set()

        self.pearl_anchor: Position | None = None
        self.best_pearl_anchor_score = 0

    @property
    def age(self):
        return self.game.get_round_num() - self.spawn_round

    def update_memory(self):
        visible_tiles: List[Tile] = self.ct.get_tiles()

        for tile in visible_tiles:
            x, y = tile.position.x, tile.position.y
            self.board[x][y] = tile

            pearl_time = tile.get_pearl_time()
            self.pearl_board[x][y] = pearl_time

            previous_max = self.maximum_pearl_board[x][y]
            if pearl_time > previous_max:
                self.maximum_pearl_board[x][y] = pearl_time

                if pearl_time >= 0 and pearl_time < self.worst_max_pearl_time:
                    self.worst_max_pearl_time = pearl_time

            for direction in unswbc._DIRECTIONS:
                edge = tile.get_edge(direction)

                if edge.is_portal():
                    portal_id = edge.get_portal_id()
                    
                    if portal_id not in self.known_portal_ids:
                        self.known_portal_ids.add(portal_id)
        self._update_target_pearl(visible_tiles)


    # ----------------- pearl related functions --------------------------------
    def get_pearl_frequency_baseline(self) -> float:
        """Sum reciprocal frequencies of observed pearl countdowns.
        Returns 0.0 if nothing has been observed yet."""
        observed_pearl_times = [
            self.maximum_pearl_board[x][y]
            for x in range(self.width)
            for y in range(self.height)
            if self.maximum_pearl_board[x][y] >= 0
        ]

        if not observed_pearl_times:
            return 0.0

        sum_of_frequencies = sum(1 / pearl_time for pearl_time in observed_pearl_times if pearl_time > 0)

        return sum_of_frequencies / len(observed_pearl_times)

    def get_effective_pearl_frequency(
        self, pos: Position, average_pearl_frequency: float | None = None
    ) -> float:
        pearl_time = self.get_maximum_pearl_time(pos)
        if pearl_time == UNOBSERVED_PEARL_TIME:
            if average_pearl_frequency is None:
                average_pearl_frequency = self.get_pearl_frequency_baseline()
            return average_pearl_frequency
        if pearl_time == -1:
            return 0
        return 1 / pearl_time

    def pearl_density_score(self, start_pos: Position, max_nodes: int) -> float:
        """Compare a reachable area's pearl frequencies with the map baseline."""
        seen = {start_pos}
        frontier = deque([start_pos])
        visited_node_count = 0
        local_frequencies = []
        average_pearl_frequency = self.get_pearl_frequency_baseline()

        while frontier and visited_node_count < max_nodes:
            pos = frontier.popleft()
            visited_node_count += 1

            local_frequencies.append(
                self.get_effective_pearl_frequency(pos, average_pearl_frequency)
            )

            for direction in unswbc._DIRECTIONS:
                next_pos = pos.add_dir(direction)
                if next_pos in seen:
                    continue
                if not self._pearl_density_passable(pos, direction):
                    continue

                seen.add(next_pos)
                frontier.append(next_pos)

        if not local_frequencies:
            return 0.0

        local_average_frequency = sum(local_frequencies) / len(local_frequencies)
        return local_average_frequency - average_pearl_frequency

    def sample_best_pearl_anchor(self, start_pos: Position, max_search_nodes: int,
                                max_nodes_to_search_at_each_reachable_tile: int) -> Position | None:
        """
        Flood fills outward from start_pos to collect nearby reachable tiles.
        Then sample PEARL_ANCHOR_SAMPLES_PER_TURN within that.
        Run get_pearl_density_score on those tiles
        Returns the highest performing candidate within the sample.
        """
        seen = {start_pos}
        frontier = deque([start_pos])
        visited_node_count = 0
        directions = unswbc._DIRECTIONS

        reachable_tiles = []

        while frontier and visited_node_count < max_search_nodes:
            pos = frontier.popleft()
            visited_node_count += 1
            reachable_tiles.append(pos)

            for dir in directions:
                next_pos = pos.add_dir(dir)
                if next_pos in seen:
                    continue
                if not self._pearl_density_passable(pos, dir):
                    continue

                seen.add(next_pos)
                frontier.append(next_pos)

        sample_size = min(PEARL_ANCHOR_SAMPLES_PER_TURN, len(reachable_tiles))
        sampled_tiles = sample(reachable_tiles, sample_size)

        best_position = None
        best_score = float("-inf")

        for candidate in sampled_tiles:
            score = self.pearl_density_score(candidate, max_nodes_to_search_at_each_reachable_tile)
            if score > best_score:
                best_score = score
                best_position = candidate

        return best_position

    # def set_best_pearl_anchor(self, start_pos: Position, max_search_nodes: int,
    #                             max_nodes_to_search_at_each_reachable_tile: int):
    #     self.pearl_anchor = self.sample_best_pearl_anchor(start_pos, max_search_nodes, max_nodes_to_search_at_each_reachable_tile)
    #     if self.pearl_anchor is None:
    #         DEBUG("decision: no pearl anchor found")
    #     else:
    #         DEBUG(f"decision: set pearl anchor to {self.pearl_anchor.x},{self.pearl_anchor.y}")
    #         # if DEBUG_ACTIVE: self.ct.draw_indicator_dot(self.pearl_anchor, 255, 0, 255)

    def consider_pearl_anchor(self, position: Position, score: float) -> bool:
        if score <= self.best_pearl_anchor_score:
            return False

        self.best_pearl_anchor_score = score
        self.pearl_anchor = position
        DEBUG(
            f"decision: new pearl anchor {position.x},{position.y} "
            f"with density score {score:.2f}"
        )
        return True

    def _pearl_density_passable(self, pos: Position, direction: Direction) -> bool:
        """Use remembered edges and live vision to expand pearl-density areas."""
        tile = self.board[pos.x][pos.y]
        if tile is None:
            return True

        if tile.get_edge(direction).get_edge_type() in (unswbc.EdgeType.KELP, unswbc.EdgeType.PORTAL):
            return False

        return True

    def get_maximum_pearl_time(self, pos: Position):
        return self.maximum_pearl_board[pos.x][pos.y]

    def get_pearl_within_vision_count(self):
        pearl_count = 0
        for tile in self.ct.get_tiles():
            if tile.has_pearl: pearl_count += 1
        return pearl_count

    def _update_target_pearl(self, visible_tiles: List[Tile]):
        # if we can currently see our target's tile, confirm it's still there —
        # otherwise someone else got it
        if self.target_pearl is not None:
            known_tile = self.board[self.target_pearl.x][self.target_pearl.y]
            if known_tile is not None and not known_tile.has_pearl():
                self.target_pearl = None

        # if we have no target, lock onto the first pearl currently visible
        if self.target_pearl is None:
            for tile in visible_tiles:
                if tile.has_pearl():
                    self.target_pearl = tile.position
                    break

    def get_target_pearl(self) -> Position | None:
        return self.target_pearl

    def give_up_on_target_pearl(self):
        """Call when pathfinding decides the current target can't be reached."""
        self.target_pearl = None

    # ----------------- pearl related functions --------------------------------

    def count_unexplored_ahead(self, pos: Position, direction: Direction, depth: int) -> int:
        """Counts unseen (None) tiles walking `depth` steps from pos in direction."""
        count = 0
        current = pos
        for _ in range(depth):
            current = current.add_dir(direction)
            current_tile = self.board[current.x][current.y]
            if current_tile is None:
                count += 1
            if current_tile is not None:
                edge_list = current_tile.edges.values()
                for edge in edge_list:
                    if edge.edge_type == EdgeType.PORTAL:
                        count += PORTAL_EXPLORATION_SCORE
        return count

    def get_explored_percentage(self) -> float:
        """Fraction of the map's tiles that have been observed at least once, from 0.0 to 1.0."""
        total_tiles = self.width * self.height
        if total_tiles == 0:
            return 0.0

        explored_count = sum(
            1
            for x in range(self.width)
            for y in range(self.height)
            if self.board[x][y] is not None
        )

        return explored_count / total_tiles

    
    def get_teammate_positions(self) -> list[Position]:
        """Positions of other dragons on your own team, currently visible."""
        my_team = self.ct.get_team()
        my_id = self.ct.get_id()
        positions = []
        for tile in self.ct.get_tiles():
            dragon = tile.get_dragon()
            if dragon is not None and dragon.get_team() == my_team and dragon.get_id() != my_id:
                positions.append(tile.position)
        return positions

    def display_memory(self):
        # for x in range(self.width):
        #     for y in range(self.height):
        #         tile = self.board[x][y]
        #         if tile == None:
        #             continue
        #         if tile.dragon_part:
        #             self.ct.draw_indicator_dot(Position(x, y), 255, 0, 0)

        if self.target_pearl:
            self.ct.draw_indicator_dot(self.target_pearl, 0, 0, 0)

        if self.pearl_anchor:
            self.ct.draw_indicator_dot(self.pearl_anchor, 255, 0, 255)

    def dragon_part_distribution_in_vision(
        self, include_detail: bool = False,
        exclude_self: bool = False
    ) -> tuple[dict[int, int], dict[int, int]] | tuple[int, int]:
        """Return visible dragon part counts, optionally grouped by dragon ID."""
        team_dragon_lengths: dict[int, int] = {}
        enemy_dragon_lengths: dict[int, int] = {}

        for tile in self.ct.get_tiles():
            if tile.dragon_part == None:
                continue

            dragon_id = tile.dragon_part.get_id()
            dragon_is_friendly: bool = tile.dragon_part.get_team() == self.ct.get_team()

            lengths = team_dragon_lengths if dragon_is_friendly else enemy_dragon_lengths
            if exclude_self and dragon_id == self.ct.get_id():
                continue
            if dragon_id in lengths:
                lengths[dragon_id] += 1
            else:
                lengths[dragon_id] = 1

        if include_detail:
            return team_dragon_lengths, enemy_dragon_lengths

        return sum(team_dragon_lengths.values()), sum(enemy_dragon_lengths.values())