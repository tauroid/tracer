from __future__ import annotations
import builtins
from dataclasses import fields, is_dataclass
import datetime
import types
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

    match self.type:
        case datetime.datetime | builtins.str | builtins.int | types.NoneType:
            match tuple(self.keys()):
                case (key,):
                    return cast(T, key)
                case ():
                    return cast(T, Hole())
                case _:
                    raise Exception("Can't assemble multiple sum brances")
        case _:
            pass

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
