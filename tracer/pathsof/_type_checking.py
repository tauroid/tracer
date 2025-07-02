from __future__ import annotations
from dataclasses import fields, is_dataclass
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Any,
    Collection,
    Mapping,
    Union,
    cast,
    get_args,
    get_origin,
)


from ..cache import cache
from ..type_manipulation import annotation_type

from .mapping import MappingItem

if TYPE_CHECKING:
    from . import PathsOf

from . import PathKey


@cache
def union[T](t: type[T]) -> Collection[type[Any]] | None:
    if get_origin(t) in [Union, UnionType]:
        return get_args(t)
    else:
        return None


def type_at_key[T](self: PathsOf[T], key: PathKey) -> type[Any]:
    if t_union := union(self.type):
        assert isinstance(key, type)
        assert key in t_union
        return key

    origin = get_origin(self.type) or self.type

    if is_dataclass(origin):
        assert isinstance(key, str)
        (key_type,) = (
            annotation_type(f.type, ctx_class=self.type)
            for f in fields(origin)
            if f.name == key
        )
        return key_type

    if issubclass(origin, Mapping):
        match get_args(self.type):
            case (key_type, value_type):
                return MappingItem[key_type, value_type]
            case ():
                return MappingItem[Any, Any]
            case _:
                raise Exception("Expected Mapping subclass to have 0 or 2 type args")

    if issubclass(origin, Collection):
        match get_args(self.type):
            case (type_arg,):
                return type_arg
            case ():
                return object
            case _:
                raise Exception("Expected Mapping subclass to have 0 or 2 type args")

    if self.type is object:
        return object

    raise Exception(f"Can't get type at {repr(key)} for {repr(self.type)}")
