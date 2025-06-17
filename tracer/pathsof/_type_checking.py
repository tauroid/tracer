from __future__ import annotations
from dataclasses import fields, is_dataclass
from types import UnionType
from typing import TYPE_CHECKING, Any, Collection, Union, cast, get_args, get_origin

from ..cache import cache

if TYPE_CHECKING:
    from . import PathsOf

from . import PathKey


@property
@cache
def union[T](self: PathsOf[T]) -> Collection[type[Any]] | None:
    if get_origin(self.type) in [Union, UnionType]:
        return get_args(self.type)
    else:
        return None


def type_at_key[T](self: PathsOf[T], key: PathKey) -> type[Any]:
    if self.union:
        assert isinstance(key, type)
        assert key in self.union
        return key

    if is_dataclass(self.type):
        assert isinstance(key, str)
        (key_type,) = (f.type for f in fields(self.type) if f.name == key)
        return cast(type[Any], key_type)

    # FIXME dodgy but fast to write (just planning on handling Mapping, Sequence,
    #       Collection or anything that has the item type as the last typevar)
    *_, type_arg = get_args(self.type)

    return type_arg
