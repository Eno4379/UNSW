import helper as unswbc
from helper import Direction
from memory import Memory
from movement import Movement

ct: unswbc.Controller
game: unswbc.Game

def execute_turn() -> None:
    memory.update_memory()
    movement.move()

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