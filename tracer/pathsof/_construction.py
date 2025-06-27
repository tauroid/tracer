from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Any, Mapping, Sequence, cast, get_origin, overload

from frozendict import frozendict


if TYPE_CHECKING:
    from . import PathsOf

from ._disassembly import paths_from_object
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
    paths: Mapping[PathKey, PathValue],
) -> PathsOf[T]: ...


@overload
def eg[T](
    self: PathsOf[T],
    paths_or_prefix: Mapping[PathKey, PathsOf[Any]],
    paths: None = None,
) -> PathsOf[T]: ...


def eg[T](
    self: PathsOf[T],
    paths_or_prefix: Mapping[PathKey, PathValue] | Sequence[PathKey],
    paths: Mapping[PathKey, PathValue] | None = None,
) -> PathsOf[T]:
    """This is probably going to end up with bananas syntax"""
    if paths is None:
        assert isinstance(paths_or_prefix, Mapping)
        return replace(
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
        subpaths = empty_subpaths.eg(rest, paths) if rest else empty_subpaths.eg(paths)
        return replace(
            self,
            paths=frozendict(
                {Wildcard(subpaths) if is_wildcard(key) else key: subpaths}
            ),
        )
