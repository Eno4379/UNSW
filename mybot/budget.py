"""
budget.py — estimates remaining judge CPU points for the current turn.

This is a *model*, not a live meter: the judge's sandbox is the only source
of ground truth (`unswbc run --sandbox -v`). COST_TABLE values below should
be replaced with numbers derived from the dual-run calibration process
(log real unit counts locally, match them against --sandbox -v totals per
round, and fit per-function constants) rather than hand-derived guesses.

Usage:
    budget = Budget()
    pathfinding = Pathfinding(ct, game, memory, budget)   # threaded through
    ...
    if budget.remaining() > SEARCH_MIN_RESERVE:
        movement.searching_behaviour()
"""

import functools
import inspect
from constants import *
# Empirically derived from calibration runs, NOT hand-derived from the price
# table — recalibrate whenever the sandbox toolchain or your code changes.
# Format: name -> (fixed_overhead_points, points_per_unit)
COST_TABLE = {
    "reachable": (5_000, 750_000),
    "get_next_step": (5_000, 850_000),
    "output_log":   (0, 0),   # per byte, straight from the docs
    "move_is_safe": (5_000, 850_000),
    "calculate_best_pearl_anchor" : (15_000_000, 0)
}


class Budget:
    """Tracks estimated CPU points spent this turn against the judge's cap."""

    def __init__(self, total: int = 100_000_000, safety_factor: float = 1.15):
        self.total = total
        self.safety_factor = 1
        self.spent = STARTING_BUDGET
        self.log: list[tuple[str, int, float]] = []

    def charge(self, name: str, units: int = 1) -> None:
        base, per_unit = COST_TABLE[name]
        cost = self.safety_factor * (base + per_unit * units)
        self.spent += cost
        self.log.append((name, units, cost))

    def remaining(self) -> float:
        return self.total - self.spent

    def reset(self) -> None:
        """Call once per turn — points don't carry over between turns."""
        self.spent = STARTING_BUDGET
        self.log.clear()

    def breakdown(self) -> str:
        """Human-readable per-call cost log, for local (non-sandbox) debugging only."""
        lines = [f"{n}: {u} units -> {c:,.0f} pts" for n, u, c in self.log]
        lines.append(f"TOTAL: {self.spent:,.0f} / {self.total:,.0f} pts")
        return "\n".join(lines)


def costed(name: str, arg_name: str | None = None):
    """
    Decorator: charges self.budget for every call to the wrapped method.

    - arg_name given -> units are read from that named argument (bound
      before the call, works whether it was passed positionally or by
      keyword). Use when cost is driven by an input, e.g. a configured cap.

    - arg_name omitted -> units come from the outcome instead: either an
      explicit self._last_units the function set before returning, or,
      failing that, the return value itself when it's a plain int. Use
      when cost depends on actual work done (usually more accurate).

    Requires the wrapped method's class to have a `self.budget: Budget`
    attribute, set in __init__ the same way self.ct/self.game/self.memory
    already are.
    """
    def decorator(fn):
        sig = inspect.signature(fn) if arg_name is not None else None

        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            if arg_name is not None:
                bound = sig.bind(self, *args, **kwargs)
                bound.apply_defaults()
                units = bound.arguments[arg_name]
                result = fn(self, *args, **kwargs)
            else:
                self._last_units = None  # reset so a stale value can't leak in
                result = fn(self, *args, **kwargs)
                units = self._last_units
                if units is None:
                    if isinstance(result, int) and not isinstance(result, bool):
                        units = result
                    else:
                        units = 0

            self.budget.charge(name, units)
            return result

        return wrapper
    return decorator


# --------------------------------------------------------------------------
# Example usage (not run automatically — for reference when wiring this in)
# --------------------------------------------------------------------------
if __name__ == "__main__":
    class FakePathfinding:
        def __init__(self, budget: Budget):
            self.budget = budget


        # Uses return value as "per unit" - uses output
        @costed("flood_fill")
        def flood_fill_area(self, start_pos, max_nodes):
            visited_node_count = min(max_nodes, 37)  # stand-in for real BFS
            return visited_node_count
        
        #  Uses self._last_units as "per unit" - uses variable found inside function
        @costed("a_star")
        def find_path(self, start_pos, goal_pos, max_nodes=25):
            nodes_expanded = 12  # stand-in for real A*
            self._last_units = nodes_expanded # <- last unit
            return ["N", "N", "E"]

        #  Uses arg_name as "per unit" - uses input
        @costed("reachability", arg_name="max_nodes")
        def reachability(self, max_nodes: int):
            # insert fodder
            return True


    budget = Budget()
    pf = FakePathfinding(budget)
    # pf.flood_fill_area((0, 0), 50)
    # pf.find_path((0, 0), (5, 5))
    pf.reachability(45)

    print(budget.breakdown())
    print(f"Remaining: {budget.remaining():,.0f} pts")