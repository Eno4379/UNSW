import helper as unswbc
from helper import Direction
from memory import Memory
from movement import Movement
from constants import *

ct: unswbc.Controller
game: unswbc.Game

def execute_turn() -> None: 
    memory.update_memory()
    if DEBUG:
        memory.display_memory()

    if game.get_round_num() < 200:
        if ct.can_split(2):
            if DEBUG:
                ct.output_log("decision: split (early growth)")
            ct.do_split(2)
        else:
            movement.execute()
    elif game.get_round_num() < 450:
        if ct.get_unit_count() < 15 and ct.can_split(2):
            if DEBUG:
                ct.output_log("decision: split (unit count below 15)")
            ct.do_split(2)
        else:
            movement.execute()
    else:
        movement.execute()

    if DEBUG:
        movement.draw_cached_path()

        # for x in game.width:
        #     for y in game.





def main() -> None:
    global ct, game, memory, movement
    ct, game = unswbc.init()
    memory = Memory(ct, game)
    movement = Movement(ct, game, memory)

    while unswbc.update(ct, game):
        execute_turn()
        unswbc.end_turn()

if __name__ == "__main__":
    main()