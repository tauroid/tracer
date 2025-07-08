from __future__ import annotations
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Mapping, Sequence, get_origin

from frozendict import frozendict

if TYPE_CHECKING:
    from . import PathsOf


from . import PathKey

from .hole import Hole, is_hole
from .tree_maths import merge
from .wildcard import Wildcard, is_wildcard, _


@dataclass(frozen=True, kw_only=True)
class MappingItem[K, V]:
    key: K
    value: V


def mapping_path[T](
    t: type[T], path: Sequence[PathKey], *, _prefix: Sequence[PathKey] = ()
) -> PathsOf[T]:
    from . import PathsOf

    first, *rest = path
    next_prefix = (*_prefix, _, "value")
    mapping_first = merge(
        PathsOf(t).eg((*_prefix, _, "key", first)),
        PathsOf(t).eg(next_prefix),
        merge_wildcards=True,
    )

    if not rest:
        return mapping_first
    else:
        return merge(
            mapping_first,
            mapping_path(t, rest, _prefix=next_prefix),
            merge_wildcards=True,
        )


def consolidate_mapping_tree[T](paths: PathsOf[T]) -> PathsOf[T]:
    """
    Merge paths with the same (mapping) key (recursive)
    """
    from . import PathValue

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

        return replace(
            paths,
            paths=frozendict(
                {
                    **{
                        (
                            Wildcard(consolidated) if is_wildcard(key) else key
                        ): consolidated
                        for key, subpaths in key_trees.values()
                        for consolidated in (consolidate_mapping_tree(subpaths),)
                    },
                    **{
                        (
                            Wildcard(consolidated) if is_wildcard(key) else key
                        ): consolidated
                        for key, subpaths in hole_trees
                        for consolidated in (consolidate_mapping_tree(subpaths),)
                    },
                }
            ),
        )
    else:
        return replace(
            paths,
            paths=frozendict(
                {
                    Wildcard(consolidated) if is_wildcard(key) else key: consolidated
                    for key, subpaths in paths.items()
                    for consolidated in (consolidate_mapping_tree(subpaths),)
                }
            ),
        )
