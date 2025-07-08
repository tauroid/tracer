import random
from typing import Any, cast
import sys

HOLE_HASH = random.randint(0, sys.maxsize)


class Hole:
    def __eq__(self, other: Any) -> bool:
        if is_hole(other):
            return True
        return False

    def __hash__(self) -> int:
        return HOLE_HASH


def hole[T](_: type[T]) -> T:
    return cast(T, Hole())


def is_hole(x: Any) -> bool:
    return isinstance(x, Hole)
