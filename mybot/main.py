import helper as unswbc
from helper import Direction
from memory import Memory
from movement import Movement

ct: unswbc.Controller
game: unswbc.Game

def execute_turn() -> None:
    memory.update_memory()
    memory.display_memory()

    if game.get_round_num() < 200:
        if ct.can_split(2):
            ct.do_split(2)
        else:
            movement.execute()
    elif game.get_round_num() < 400:
        if ct.get_unit_count() < 15 and ct.can_split(2):
            ct.do_split(2)
        else:
            movement.execute()

    movement.draw_cached_path()




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