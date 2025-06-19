from dataclasses import dataclass, field
from typing import Any, cast

# FIXME actually I think holes can be identical, we're not in
#       set land we're in paths land, and paths can merge
#
#       so just one hole key per paths

_id = 0


def get_id() -> int:
    global _id
    _id += 1
    return _id


@dataclass(frozen=True)
class Hole:
    _id: int = field(default_factory=get_id)


def hole[T](_: type[T]) -> T:
    return cast(T, Hole())


def is_hole(x: Any) -> bool:
    return isinstance(x, Hole)
