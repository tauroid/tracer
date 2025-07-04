from __future__ import annotations
from dataclasses import fields, is_dataclass, replace
from typing import (
    TYPE_CHECKING,
    Any,
    Collection,
    Mapping,
    Sequence,
    cast,
    get_origin,
    overload,
)

from frozendict import frozendict

from tracer.pathsof._type_checking import union


if TYPE_CHECKING:
    from . import PathsOf

from ._disassembly import paths_from_object
from .mapping import consolidate_mapping_tree
from .wildcard import Wildcard, is_wildcard, populate_wildcards

from . import PathKey, PathValue


@staticmethod
def a[T](instance: T) -> PathsOf[T]:
    from . import PathsOf

    return PathsOf.an(instance)


@staticmethod
def an[T](instance: T) -> PathsOf[T]:
    from . import PathsOf

    return PathsOf(type(instance)).specifically(instance)


def specifically[T](self: PathsOf[T], instance: T) -> PathsOf[T]:
    assert not self.paths
    origin = get_origin(self.type) or self.type
    assert isinstance(instance, origin)
    return replace(
        self,
        paths=paths_from_object(self.type, instance),
        sequence_length=(
            len(cast(Sequence[Any], instance)) if issubclass(origin, Sequence) else None
        ),
    )


@overload
def eg[T](
    self: PathsOf[T],
    paths_or_prefix: Sequence[PathKey],
    paths: Mapping[PathKey, PathValue] | None = None,
    *,
    _consolidate_mappings: bool = True,
) -> PathsOf[T]: ...


@overload
def eg[T](
    self: PathsOf[T],
    paths_or_prefix: Mapping[PathKey, PathsOf[Any]],
    paths: None = None,
    *,
    _consolidate_mappings: bool = True,
) -> PathsOf[T]: ...


def eg[T](
    self: PathsOf[T],
    paths_or_prefix: Mapping[PathKey, PathValue] | Sequence[PathKey],
    paths: Mapping[PathKey, PathValue] | None = None,
    *,
    _consolidate_mappings: bool = True,
) -> PathsOf[T]:
    """This is probably going to end up with bananas syntax"""
    if isinstance(paths_or_prefix, Mapping):
        pathsof = replace(
            self,
            paths=populate_wildcards(paths_or_prefix),
        )
    else:
        # Importing properly seems to have inevitable loop
        from . import PathsOf

        if self.paths:
            raise Exception(
                "Not using prefix path on nonempty trees yet,"
                " but it makes sense to do"
            )

        key, *rest = paths_or_prefix
        empty_subpaths = PathsOf(self._type_at_key(key))
        subpaths = (
            empty_subpaths.eg(rest, paths, _consolidate_mappings=False)
            if rest
            else empty_subpaths.eg(paths or {}, _consolidate_mappings=False)
        )
        pathsof = replace(
            self,
            paths=frozendict(
                {Wildcard(subpaths) if is_wildcard(key) else key: subpaths}
            ),
        )

    if _consolidate_mappings:
        return consolidate_mapping_tree(pathsof)
    else:
        return pathsof


def all_keys[T](t: type[T]) -> Collection[PathKey]:
    if t_union := union(t):
        return t_union

    origin = get_origin(t) or t

    if is_dataclass(origin):
        return tuple(f.name for f in fields(origin))

    # str is a Collection but damned if I'll treat it as one
    if t is str:
        return ()

    if issubclass(origin, Collection):
        return (Wildcard(),)

    return ()


@property
def full[T](self: PathsOf[T]) -> PathsOf[T]:
    if self.paths or self.sequence_length is not None:
        raise Exception("`full` is only allowed on an empty tree")

    from . import PathsOf

    return replace(
        self,
        paths=frozendict(
            {
                Wildcard(full_at_key) if is_wildcard(key) else key: full_at_key
                for key in all_keys(self.type)
                for full_at_key in (PathsOf(self._type_at_key(key)).full,)
            }
        ),
    )
