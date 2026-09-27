from typing import NamedTuple

from helper import Direction, Position

class Portal(NamedTuple):
    """A single portal pair, tracked by id. position_b is None until the far
    end has actually been seen — portals are double-sided, and you can't see
    through one, so knowing one side tells you nothing about the other."""
    portal_id: int
    position_a: Position
    is_horizontal: bool  # both ends of a pair are guaranteed the same orientation
    position_b: Position | None = None

    @property
    def canonical_direction(self) -> Direction:
        """The 'forward' exit direction out of either owner tile —
        SOUTH for a horizontal edge, EAST for a vertical one."""
        return Direction.SOUTH if self.is_horizontal else Direction.EAST

    def is_confirmed(self) -> bool:
        """Whether both physical ends have been seen."""
        return self.position_b is not None

    def other_owner(self, from_pos: Position) -> Position | None:
        """The paired owner tile, given the owner tile you're standing on."""
        if not self.is_confirmed():
            return None
        if from_pos == self.position_a:
            return self.position_b
        if from_pos == self.position_b:
            return self.position_a
        return None  # from_pos isn't one of this portal's two owners

    def get_destination(self, from_pos: Position, direction: Direction) -> Position | None:
        """Where entering this portal from from_pos heading `direction` leads."""
        other = self.other_owner(from_pos)
        if other is None:
            return None
        entering_forward = direction in (Direction.SOUTH, Direction.EAST)
        return other.add_dir(self.canonical_direction) if entering_forward else other

    def with_sighting(self, owner_pos: Position) -> "Portal":
        """A copy of this portal with a newly-seen owner recorded, if it's new."""
        if owner_pos in (self.position_a, self.position_b):
            return self
        if self.position_b is None:
            return self._replace(position_b=owner_pos)
        return self  # already have two owners; ignore anomalies