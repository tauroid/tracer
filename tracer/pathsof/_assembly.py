from __future__ import annotations
import builtins
from dataclasses import fields, is_dataclass
import datetime
import types
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Collection,
    Mapping,
    cast,
    get_origin,
)

from frozendict import frozendict


from ..cache import cache
from ..type_manipulation import annotation_type

from .hole import Hole, is_hole
from .wildcard import Wildcard, is_wildcard

if TYPE_CHECKING:
    from . import PathsOf


def consolidate_mapping_tree[T](paths: PathsOf[T]) -> PathsOf[T]:
    """
    Merge paths with the same (mapping) key (recursive)
    """
    from . import PathsOf, PathKey, PathValue

    origin = get_origin(paths.type) or paths.type

    if issubclass(origin, Mapping):
        key_trees: dict[Any, tuple[PathKey, PathValue]] = {}
        hole_trees: list[tuple[PathKey, PathValue]] = []
        for path_key, subpaths in paths.items():
            mapping_key = subpaths["key"].assembled if "key" in subpaths else Hole()
            if is_hole(mapping_key):
                hole_trees.append((path_key, subpaths))
            else:
                if mapping_key in key_trees:
                    existing_path_key, existing_key_tree = key_trees[mapping_key]
                    new_key_tree = existing_key_tree.merge(subpaths)
                    match (existing_path_key, path_key):
                        case (Wildcard(), Wildcard()):
                            new_path_key = Wildcard(new_key_tree)
                        case (Wildcard(), new_path_key) | (new_path_key, Wildcard()):
                            pass
                        case (_, _):
                            assert existing_path_key == path_key
                            new_path_key = existing_path_key
                    key_trees[mapping_key] = new_path_key, new_key_tree
                else:
                    key_trees[mapping_key] = path_key, subpaths

        return PathsOf(paths.type, sequence_length=paths.sequence_length).eg(
            {
                **{
                    Wildcard(consolidated) if is_wildcard(key) else key: consolidated
                    for key, subpaths in key_trees.values()
                    for consolidated in (consolidate_mapping_tree(subpaths),)
                },
                **{
                    Wildcard(consolidated) if is_wildcard(key) else key: consolidated
                    for key, subpaths in hole_trees
                    for consolidated in (consolidate_mapping_tree(subpaths),)
                },
            }
        )
    else:
        return PathsOf(paths.type, sequence_length=paths.sequence_length).eg(
            {
                Wildcard(consolidated) if is_wildcard(key) else key: consolidated
                for key, subpaths in paths.items()
                for consolidated in (consolidate_mapping_tree(subpaths),)
            }
        )


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
                    raise Exception("Can't assemble multiple sum branches")
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
        if origin == get_origin(Mapping[Any, Any]):
            origin = frozendict
        return cast(Callable[[Any], T], origin)(
            {
                paths["key"].assembled if "key" in paths else Hole(): (
                    paths["value"].assembled if "value" in paths else Hole()
                )
                for paths in consolidate_mapping_tree(self).values()
            }
        )

    # TODO Sequence

    if issubclass(origin, Collection):
        if origin == get_origin(Collection[Any]):
            origin = tuple
        return cast(Callable[[Any], T], origin)(
            paths.assembled for paths in self.values()
        )

    return cast(T, Hole())
