from __future__ import annotations
from dataclasses import fields, is_dataclass, replace
from datetime import datetime
from types import EllipsisType
from typing import (
    TYPE_CHECKING,
    Any,
    Collection,
    Mapping,
    Sequence,
    cast,
    get_args,
    get_origin,
)


from ..cache import cache
from ..type_manipulation import annotation_type, instance_union_member

from .mapping import MappingItem
from .wildcard import Wildcard, normalise_wildcards

if TYPE_CHECKING:
    from . import PathsOf

from . import PathKey


@property
@cache
def paths[T](self: PathsOf[T]) -> Mapping[PathKey, PathsOf[Any]]:
    # Importing properly seems to have inevitable loop
    from . import PathsOf

    if self.explicit_paths is not None:
        if self.instance is not None:
            raise Exception(
                "Can't supply both `explicit_paths` and concrete data instance"
            )
        # TODO maybe more stuff explicit_paths conflicts with
        return normalise_wildcards(self.explicit_paths)

    if self.instance is None:
        return {}

    if self.union:
        union_member = instance_union_member(self.instance, self.union)
        return {union_member: replace(self, prototype=union_member)}

    match self.instance:
        case EllipsisType():
            return {}
        case datetime() | str() | int() | None:
            return {self.instance: PathsOf(EllipsisType)}
        case _:
            pass

    if is_dataclass(self.instance):
        return {
            f.name: PathsOf(
                annotation_type(f.type, ctx_class=self.type),
                getattr(self.instance, f.name),
            )
            for f in fields(self.instance)
        }

    type_origin = get_origin(self.type) or self.type

    if issubclass(type_origin, Mapping):
        mapping_instance = cast(Mapping[Any, Any], self.instance)
        match get_args(self.type):
            case (key_type, value_type):
                return {
                    key: PathsOf(MappingItem[key_type, value_type]).eg(
                        {
                            "key": PathsOf(key_type, key),
                            "value": PathsOf(value_type, value),
                        }
                    )
                    for key, value in mapping_instance.items()
                }
            case ():
                return {
                    key: PathsOf(MappingItem[Any, Any]).eg(
                        {"key": PathsOf(key), "value": PathsOf(value)}
                    )
                    for key, value in mapping_instance.items()
                }
            case args:
                raise Exception(
                    "Expected 0 or 2 (really, just 2 but `PathsOf(value)` is nice)"
                    f" type args to a `Mapping` subclass but got {args}"
                )

    # FIXME having numbers on sequences doesn't work with wildcardy
    #       `link`s. But whose problem is that, links not showing
    #       whether they think of stuff as wildcards, or are numbers
    #       just not a good idea?
    #
    #       Probably the first one is the problem, but forcing
    #       tracers to show their input specs sounds like a pain
    #
    # if issubclass(type_origin, Sequence):
    #     sequence_instance = cast(Sequence[Any], self.instance)
    #     match get_args(self.type):
    #         case sequence_type,:
    #             return {
    #                 n: PathsOf(sequence_type, value)
    #                 for n, value in enumerate(sequence_instance)
    #             }
    #         case ():
    #             return {n: PathsOf(value) for n, value in enumerate(sequence_instance)}
    #         case args:
    #             raise Exception(
    #                 f"Expected 1 type arg to a `Sequence` subclass but got {args}"
    #             )

    if issubclass(type_origin, Collection):
        collection_instance = cast(Collection[Any], self.instance)
        match get_args(self.type):
            case collection_type,:
                return {
                    Wildcard(item_paths): item_paths
                    for item_paths in map(
                        lambda item: PathsOf(collection_type, item),
                        collection_instance,
                    )
                }
            case ():
                return {
                    Wildcard(item_paths): item_paths
                    for item_paths in map(PathsOf, collection_instance)
                }
            case args:
                raise Exception(
                    f"Expected 1 type arg to a `Collection` subclass but got {args}"
                )

    raise Exception(
        f"Don't know how to make paths out of {self.instance}, type {self.type}."
    )
