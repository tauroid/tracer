from __future__ import annotations
from dataclasses import fields, is_dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Mapping,
    cast,
    get_origin,
)

from ..cache import cache
from ..type_manipulation import annotation_type

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
                f.name: self.get(
                    f.name,
                    PathsOf(
                        annotation_type(f.type, ctx_class=self.type),
                        Hole(),
                    ),
                ).assembled
                for f in fields(self.type)
            }
        )

    origin = get_origin(self.type) or self.type

    if issubclass(origin, Mapping):
        return cast(Callable[[Any], T], origin)(
            {
                paths["key"].assembled if "key" in paths else Hole(): (
                    paths["value"].assembled if "value" in paths else Hole()
                )
                for paths in self.values()
            }
        )

    return cast(T, Hole())
