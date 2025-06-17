from __future__ import annotations
from dataclasses import fields, is_dataclass
from typing import TYPE_CHECKING, cast
from ..cache import cache

from .hole import Hole

if TYPE_CHECKING:
    from . import PathsOf


@property
@cache
def assembled[T](self: PathsOf[T]) -> T:
    # Importing properly seems to have inevitable loop
    from . import PathsOf

    if self.instance is not None or self.type is type(None):
        return cast(T, self.instance)

    if is_dataclass(self.type):
        return self.type(
            **{
                f.name: self.get(f.name, PathsOf(f.type, Hole())).assembled
                for f in fields(self.type)
            }
        )

    return cast(T, Hole())
