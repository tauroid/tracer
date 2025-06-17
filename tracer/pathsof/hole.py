from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class Hole: ...


def hole[T](_: type[T]) -> T:
    return cast(T, Hole())


def is_hole(x: Any) -> bool:
    return isinstance(x, Hole)
