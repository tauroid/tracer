from __future__ import annotations
from dataclasses import fields, is_dataclass
from datetime import datetime
from types import EllipsisType
from typing import (
    Any,
    Collection,
    Mapping,
    # Sequence,
    cast,
    get_args,
    get_origin,
)

from frozendict import frozendict


from ..type_manipulation import annotation_type, instance_union_member

from ._type_checking import union
from .mapping import MappingItem
from .wildcard import Wildcard

from . import PathKey, PathValue


def paths_from_object[T](t: type[T], instance: T) -> frozendict[PathKey, PathValue]:
    # Importing properly seems to have inevitable loop
    from . import PathsOf

    if t_union := union(t):
        union_member = instance_union_member(instance, t_union)
        return frozendict({union_member: PathsOf(union_member).specifically(instance)})

    match instance:
        case EllipsisType():
            return frozendict()
        case datetime() | str() | int() | None:
            return frozendict({instance: PathsOf(EllipsisType)})
        case _:
            pass

    if is_dataclass(instance):
        return frozendict(
            {
                f.name: PathsOf(
                    annotation_type(f.type, ctx_class=t),
                ).specifically(getattr(instance, f.name))
                for f in fields(instance)
            }
        )

    type_origin = get_origin(t) or t

    if issubclass(type_origin, Mapping):
        mapping_instance = cast(Mapping[Any, Any], instance)
        match get_args(t):
            case (key_type, value_type):
                return frozendict(
                    {
                        Wildcard(item): item
                        for key, value in mapping_instance.items()
                        for item in (
                            PathsOf(
                                MappingItem[key_type, value_type],
                                paths=frozendict(
                                    {
                                        "key": PathsOf(key_type).specifically(key),
                                        "value": PathsOf(value_type).specifically(
                                            value
                                        ),
                                    }
                                ),
                            ),
                        )
                    }
                )
            case ():
                return frozendict(
                    {
                        Wildcard(item): item
                        for key, value in mapping_instance.items()
                        for item in (
                            PathsOf(
                                MappingItem[Any, Any],
                                paths=frozendict(
                                    {
                                        "key": PathsOf.a(key),
                                        "value": PathsOf.a(value),
                                    }
                                ),
                            ),
                        )
                    }
                )
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
        collection_instance = cast(Collection[Any], instance)
        match get_args(t):
            case collection_type,:
                return frozendict(
                    {
                        Wildcard(item_paths): item_paths
                        for item_paths in map(
                            lambda item: PathsOf(collection_type).specifically(item),
                            collection_instance,
                        )
                    }
                )
            case ():
                return frozendict(
                    {
                        Wildcard(item_paths): item_paths
                        for item_paths in map(PathsOf.a, collection_instance)
                    }
                )
            case args:
                raise Exception(
                    f"Expected 1 type arg to a `Collection` subclass but got {args}"
                )

    raise Exception(f"Don't know how to make paths out of {instance}, type {t}.")
