import helper as unswbc
from helper import DEBUG
from budget import Budget

from constants import DEBUG_ACTIVE
from memory import Memory
from movement import Movement

from testing import exhaust_points

ct: unswbc.Controller
game: unswbc.Game
unit_count_at_200: int | None = None
budget: Budget

def print_budget():
    ct.output_log("====== Budget ======")
    for line in budget.breakdown().splitlines():
        ct.output_log(line)
    ct.output_log("====== Budget ======")

def try_split() -> bool:
    global unit_count_at_200, should_grow_early, below_round_200_baseline, round_number

    if not ct.can_split(2):
        return False

    if should_grow_early:
        DEBUG(f"decision: split (Early growth)")
        ct.do_split(2)
        return True
    
    if  (ct.get_unit_count() < unit_count_at_200) and 200 < round_number <= 450:
        DEBUG(f"decision: split (recovering unit count)")
        ct.do_split(2)
        return True
    return False


def execute_turn() -> None: 
    global unit_count_at_200, should_grow_early, below_round_200_baseline, round_number
    # Update memory every round
    memory.update_memory()

    if game.get_round_num() >= 200 and unit_count_at_200 is None:
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
    if try_split():
        pass
    elif (movement.execute_early_game_plan() if round_number < 450 else movement.execute_late_game_plan()):
        pass
    else:
        movement.move_randomly()

    # ---------------- main decision tree --------------------------------


    # exhaust_points(50_000)
    # ct.output_log(f"CPU budget spent: {(100_000_000 - budget.remaining())/1_000_000:.1f}M")
    


    if DEBUG_ACTIVE:
        # needs to be called after movement.execute()
        movement.draw_cached_path()
        memory.display_memory()
        print_budget()


def main() -> None:
    global ct, game, memory, movement, budget
    ct, game = unswbc.init()
    memory = Memory(ct, game)
    budget = Budget()
    movement = Movement(ct, game, memory, budget)

    while unswbc.update(ct, game):
        execute_turn()
        budget.reset()
        unswbc.end_turn()

if __name__ == "__main__":
    main()
