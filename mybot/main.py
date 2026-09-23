import helper as unswbc
from helper import DEBUG
from memory import Memory
from movement import Movement
from constants import DEBUG_ACTIVE

ct: unswbc.Controller
game: unswbc.Game
unit_count_at_200: int | None = None


def try_split(reason: str) -> bool:
    if not ct.can_split(2):
        return False

    DEBUG(f"decision: split ({reason})")
    ct.do_split(2)
    return True


def execute_turn() -> None: 
    global unit_count_at_200
    # Update memory every round
    memory.update_memory()

    if DEBUG_ACTIVE:
        memory.display_memory()

    if game.get_round_num() == 200:
        unit_count_at_200 = ct.get_unit_count()

    round_number = game.get_round_num()

    # --------- Boolean flags ---------------
    should_grow_early = round_number <= 200

    if unit_count_at_200 is None:
        below_round_200_baseline = ct.get_unit_count() < 50
    else:
        below_round_200_baseline = ct.get_unit_count() < unit_count_at_200
    # --------- Boolean flags ---------------


    # ---------------- main decision tree --------------------------------
    if should_grow_early and try_split("early growth"):
        pass
    elif round_number < 450 and below_round_200_baseline and try_split("recovering unit count"): 
        pass
    elif (movement.execute_early_game_plan() if round_number < 450 else movement.execute_late_game_plan()):
        pass
    else:
        movement.move_randomly()

    if DEBUG_ACTIVE:
        # needs to be called after movement.execute()
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