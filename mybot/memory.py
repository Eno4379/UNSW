import helper as unswbc
from helper import Direction, Tile, Position
from typing import List

class Memory:
    def __init__(self, ct: unswbc.Controller, game: unswbc.Game):
        self.ct = ct
        self.game = game
        self.width, self.height = game.get_map_size()

        self.board: List[List[Tile | None]]
        self.board = [[None] * self.height for _ in range(self.width)]

        # the pearl we're currently committed to hunting, if any
        self.target_pearl: Position | None = None

    def update_memory(self):
        visible_tiles: List[Tile] = self.ct.get_tiles()

        for tile in visible_tiles:
            x, y = tile.position.x, tile.position.y
            self.board[x][y] = tile

        self._update_target_pearl(visible_tiles)

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

    def count_unexplored_ahead(self, pos: Position, direction: Direction, depth: int) -> int:
        """Counts unseen (None) tiles walking `depth` steps from pos in direction."""
        count = 0
        current = pos
        for _ in range(depth):
            current = current.add_dir(direction)
            if self.board[current.x][current.y] is None:
                count += 1
        return count

    
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