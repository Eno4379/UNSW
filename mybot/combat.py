import helper as unswbc
from helper import Direction, DEBUG
from pathfinding import Pathfinding


class Combat:
    """Chooses whether this dragon should attack an adjacent enemy head."""

    def __init__(self, ct: unswbc.Controller, pathfinding: Pathfinding):
        self.ct = ct
        self.pathfinding = pathfinding

    def choose_attack_direction(self) -> Direction | None:
        """Return an attack direction when combat is preferable to movement."""
        if self.ct.get_length() != 2:
            return None

        # only kill when there are more allies near you than enemies 
        # pushes the battle front, taking more map control or else you'd lo
        # se map control
        self_count, enemy_count = self.dragon_part_distribution_in_vision()
        if not self_count >= enemy_count:
            return None

        here = self.ct.get_position()
        own_team = self.ct.get_team()

        for direction in Direction.get_direction_list():
            current_tile = self.pathfinding.memory.board[here.x][here.y]
            if (current_tile is not None
                    and current_tile.get_edge(direction).get_edge_type() == unswbc.EdgeType.KELP):
                continue

            tile = self.ct.get_tile(here.add_dir(direction))
            if tile is None or tile.dragon_part is None:
                continue

            enemy = tile.dragon_part
            if enemy.is_dragon_head and enemy.get_team() != own_team:
                unswbc.DEBUG(f"combat: attack {direction.value} (enemy head adjacent)")
                return direction

        return None

    def dragon_part_distribution_in_vision(self) -> list[int, int]:
        # might be more efficient to pull from memory
        team_dragon_parts, enemy_dragon_parts = 0, 0
        for tile in self.ct.get_tiles():
            if tile.dragon_part == None:
                continue
            if tile.dragon_part.team == self.ct.get_team():
                team_dragon_parts += 1
            else:
                enemy_dragon_parts += 1
        return team_dragon_parts, enemy_dragon_parts


    def execute(self) -> bool:
        """Attack if the combat policy selected a target."""
        direction = self.choose_attack_direction()
        if direction is None:
            return False
        
        DEBUG("Kill Behaviour")
        self.ct.make_move(direction)
        return True
