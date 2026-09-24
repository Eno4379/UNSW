import helper as unswbc
from random import choice, shuffle

from combat import Combat
from constants import *
from helper import DEBUG, Direction, Position
from memory import Memory
from pathfinding import Pathfinding
from searching import Searching


class Movement:
    def __init__(self, ct: unswbc.Controller, game: unswbc.Game, memory: "Memory"):
        self.memory = memory
        self.ct = ct
        self.game = game
        self.pathfinding = Pathfinding(ct, game, memory)
        self.combat = Combat(ct, game, memory, self.pathfinding)
        self.searching = Searching(ct, game, memory, self.pathfinding)
        self.width = game.width
        self.height = game.height

        self.starting_position = ct.get_position()
        self._pick_random_direction()

    def _pick_random_direction(self):
        self.rand_dir: Direction = choice(unswbc._DIRECTIONS)

    def move_towards_greedy(self, pos: Position):
        here = self.ct.get_position()
        x_delta = pos.x - here.x
        y_delta = pos.y - here.y

        w_half, h_half = self.width / 2, self.height / 2
        if abs(x_delta) > w_half:
            x_delta -= self.width if x_delta > 0 else -self.width
        if abs(y_delta) > h_half:
            y_delta -= self.height if y_delta > 0 else -self.height

        directions_to_move_in = []
        if x_delta > 0:
            directions_to_move_in.append(Direction.EAST)
        if x_delta < 0:
            directions_to_move_in.append(Direction.WEST)
        if y_delta > 0:
            directions_to_move_in.append(Direction.SOUTH)
        if y_delta < 0:
            directions_to_move_in.append(Direction.NORTH)

        required_space = self.ct.get_length() + SAFETY_BUFFER
        if directions_to_move_in:
            for dir in directions_to_move_in:
                if self.pathfinding.move_is_safe(dir, required_space):
                    self.ct.make_move(dir)
                    DEBUG(f"move: {dir.value} (greedy toward pearl)")
                    return

        DEBUG("move: no safe route toward pearl; trying random move")
        self.move_randomly()
        return

    def move_towards(self, pos: Position) -> bool:
        here = self.ct.get_position()
        direction = self.pathfinding.get_next_step(here, pos)

        if direction is None:
            DEBUG("target: unreachable; abandoning pearl")
            return False

        required_space = self.ct.get_length() + SAFETY_BUFFER
        if self.pathfinding.move_is_safe(direction, required_space):
            self.ct.make_move(direction)
            self.pathfinding.has_moved_along_path()
            DEBUG(f"move: {direction.value} (path toward pearl)")
            return True

        DEBUG(f"move: planned {direction.value} unsafe; using greedy fallback")
        self.move_towards_greedy(pos)
        return True

    def calculate_best_pearl_anchor(self):
        candidate = self.memory.sample_best_pearl_anchor(
            self.ct.get_position(),
            PEARL_ANCHOR_PRIMARY_SEARCH_NODES,
            PEARL_ANCHOR_SECONDARY_SEARCH_NODES,
        )
        if candidate is not None:
            score = self.memory.pearl_density_score(
                candidate, PEARL_ANCHOR_SECONDARY_SEARCH_NODES
            )
            self.memory.consider_pearl_anchor(candidate, score)
            

    def searching_behaviour(self) -> bool:
        percentage_till_game_end = 1 - self.game.get_round_num() / 500
        if self.memory.get_explored_percentage() > (0.4 * percentage_till_game_end):
            self.calculate_best_pearl_anchor()

        best_direction = self.searching.choose_direction()

        if best_direction is not None:
            self.ct.make_move(best_direction)
            DEBUG(f"move: {best_direction.value} (search)")
            return True
        else:
            DEBUG("move: no safe scored direction")
            return False

    def move_randomly(self) -> None:
        directions = unswbc._DIRECTIONS[::]
        shuffle(directions)
        for direction in directions:
            if self.pathfinding.can_move(direction):
                self.ct.make_move(direction)
                DEBUG(f"move: {direction.value} (random fallback)")
                return
        DEBUG(f"thought: completely stuck - gonna killmyself")
        self.sucide()

    def force_move_forwards(self) -> None:
        self.ct.make_move(self.ct.get_dir())
        DEBUG("move: forced forward (no safe direction found)")

    def try_reverse_direction_split(self) -> bool:
        """Splits (2) but on the tail end, so it 'reverses' itself"""
        if self.ct.can_split(self.ct.get_length() - 2):
            DEBUG("decision: Reverse direction split")
            self.ct.do_split(self.ct.get_length() - 2)
            return True
        DEBUG("decision: Want to split due to no safe spaces")
        DEBUG("but cannot")
        return False

    def sucide(self) -> bool:
        """Kills itself by moving backwards, always return true"""
        DEBUG("Killing myself")
        current_dir = self.ct.get_dir()
        self.ct.make_move(current_dir.get_opposite())
        return True

    def should_sacrifice(self) -> bool:
        team_dragons_dict_exclude_self, enemy_dragons_dict = self.memory.dragon_part_distribution_in_vision(include_detail=True, 
                                                                                                       exclude_self=True)
        enemy_dragons_count = sum(enemy_dragons_dict.values())
        team_dragons_count_exclude_self = sum(team_dragons_dict_exclude_self.values())
        self_length = self.ct.get_length()

        highest_friendly_length = max(team_dragons_dict_exclude_self.values(), default=0)

        if enemy_dragons_count == 0 and team_dragons_count_exclude_self > 0:
            if highest_friendly_length > self_length:
                DEBUG(f"decision: I found a dragon near me with length {highest_friendly_length}")
                DEBUG(f"I should commit sucide")
                return True
        DEBUG(f"decision: I am the longest dragon near me, will not commit sucide")    
        return False

    def pearl_behaviour(self):
        pearl_location = self.memory.get_target_pearl()
        if pearl_location is not None:
            DEBUG(f"decision: pearl target {pearl_location}")
            if self.move_towards(pearl_location):
                # move_towards returns false when can't find a path
                DEBUG(f"decision: moving towards {pearl_location}") 
                return True
            self.memory.give_up_on_target_pearl()

        return False


    # ------------------ main execution loops -------------------------
    # returns True when an action is chosen
    def execute_early_game_plan(self) -> bool:
        if self.combat.execute():
            return True

        if self.pearl_behaviour():
            return True

        if self.searching_behaviour():
            DEBUG("decision: searching for unexplored space")
            return True            

        if self.try_reverse_direction_split():
            DEBUG("split: forced to split due to no safe spaces")
            return True

        return False

    def execute_late_game_plan(self) -> bool:
        if self.combat.execute():
            return True

        if self.should_sacrifice():
            self.sucide()
            return True

        if self.pearl_behaviour():
            return True

        if self.searching_behaviour():
            DEBUG("decision: searching for unexplored space")
            return True

        if self.try_reverse_direction_split():
            DEBUG("split: forced to split due to no safe spaces")
            return True

        return False
    # ------------------ main execution loops -------------------------
    
    def draw_cached_path(self):
        self.pathfinding.draw_cached_path()