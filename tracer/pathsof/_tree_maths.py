from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Any, cast

from frozendict import deepfreeze, frozendict

if TYPE_CHECKING:
    from . import PathsOf


def extends[T](self: PathsOf[T], other: PathsOf[T]) -> bool:
    """
    DEPRECATED?

    If we have at least all of `other`'s paths and don't conflict

    Purpose of this is not to lose detail in the round trip (though we might
    get conflicting sum branches which would confuse things)

    NOTE "Don't conflict" might not actually be meaningful if we do nothing
            about sum type conflicts
    """
    # NOTE sum types different maybe?
    # FIXME good report
    return all(key in self and self[key].extends(paths) for key, paths in other.items())


def covers[T](self: PathsOf[T], other: PathsOf[T]) -> bool:
    """
    Same as `extends` but `other` is allowed to have subpaths of our termini

    FIXME good report
    """
    # Importing properly seems to have inevitable loop
    from . import PathsOf

    if not self.paths:
        return True

    for key, paths in other.items():
        if key in self and self[key].covers(paths):
            continue

        # Could be inexact match - currently only doing PathsOf covers
        # PathsOf / normal (not normal covers PathsOf)

        covering = False
        for self_key, self_paths in self.items():
            if not isinstance(self_key, PathsOf):
                continue

            paths_of_self_key: PathsOf[Any] = self_key
            paths_of_key: PathsOf[Any] = (
                key if isinstance(key, PathsOf) else PathsOf(key)
            )

            if paths_of_self_key.covers(paths_of_key) and self_paths.covers(paths):
                covering = True

        if not covering:
            return False

    return True


def _remove_lowest_level[
    T
](self: PathsOf[T], depth: int = 0) -> tuple[PathsOf[T], int] | None:
    from . import PathsOf

    if not self.paths:
        return None

    reduced = tuple(
        (key, reduced_child, reduced_child_depth)
        for key, child in self.items()
        for reduced_child_pair in (_remove_lowest_level(child, depth + 1),)
        if reduced_child_pair is not None
        for reduced_child, reduced_child_depth in (reduced_child_pair,)
    )

    if not reduced:
        return PathsOf(self.type, sequence_length=self.sequence_length), depth

    reduced_child_keys, reduced_children, reduced_child_depths = zip(*reduced)

    max_reduced_child_depth = max(reduced_child_depths)

    return (
        PathsOf(self.type, sequence_length=self.sequence_length).eg(
            {
                **self,
                **{
                    key: reduced_child
                    for key, reduced_child, reduced_child_depth in zip(
                        reduced_child_keys, reduced_children, reduced_child_depths
                    )
                    if reduced_child_depth == max_reduced_child_depth
                },
            }
        ),
        max_reduced_child_depth,
    )


def remove_lowest_level_or_none[T](self: PathsOf[T]) -> PathsOf[T] | None:
    removed = _remove_lowest_level(self)
    return removed[0] if removed else None


def remove_lowest_level[T](self: PathsOf[T]) -> PathsOf[T]:
    removed = remove_lowest_level_or_none(self)
    if removed is None:
        raise Exception(f"{self} has no children")
    return removed


def merge[T](self: PathsOf[T], other: PathsOf[T]) -> PathsOf[T]:
    # Importing properly seems to have inevitable loop
    from . import PathsOf

    if not self.paths and not other.paths:
        assert self == other
        return self

    assert self.type == other.type
    assert self.sequence_length == other.sequence_length

    new_explicit_paths = dict(self)
    for key, paths in other.items():
        if key in new_explicit_paths:
            new_explicit_paths[key] = new_explicit_paths[key].merge(paths)
        else:
            new_explicit_paths[key] = paths

    return PathsOf(
        self.type,
        explicit_paths=frozendict(new_explicit_paths),
        sequence_length=self.sequence_length,
    )
