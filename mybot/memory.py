import unswbc
import helper as unswbc
from helper import Direction, Tile
from typing import List

class Memory:
    def __init__(self, ct: unswbc.Controller, game: unswbc.Game):
        self.ct = ct
        self.game = game
        self.width, self.height = game.get_map_size()

        # False = open path, True = wall, None = Unknown
        # self.h_walls = [[False] * (self.height + 1) for _ in range(self.width)]
        # self.v_walls = [[False] * self.height for _ in range(self.width + 1)]
        # # self.has_pearl = [[None] * self.height for _ in range(self.width)]

        self.board: List[List[Tile | None]]
        self.board = [[None] * self.height for _ in range(self.width)]


    def update_memory(self):
        visible_tiles: List[Tile] = self.ct.get_tiles()

        tile: Tile
        for tile in visible_tiles:
            x, y = tile.position.x , tile.position.y
            self.board[x][y] = tile

            


    # def __has_wall(self, x, y, direction):
    #     """Check if there is a wall in a given direction from cell (x, y)"""
    #     if direction == Direction.NORTH: return self.h_walls[x][y]
    #     if direction == Direction.SOUTH: return self.h_walls[x][y + 1]
    #     if direction == Direction.EAST: return self.v_walls[x][y]
    #     if direction == Direction.WEST: return self.v_walls[x + 1][y]
    #     return True # Out of bounds / invalid

    