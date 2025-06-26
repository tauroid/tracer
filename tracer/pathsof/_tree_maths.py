from __future__ import annotations
from typing import TYPE_CHECKING

from frozendict import frozendict


if TYPE_CHECKING:
    from . import PathsOf

from .wildcard import Wildcard, is_wildcard

from . import PathKey, PathValue


def covers[T](
    self: PathsOf[T], other: PathsOf[T], *, all_the_way_to_the_leaves: bool = False
) -> bool:
    """
    If we have at least all of `other`'s paths and don't conflict

    `all_the_way_to_the_leaves` means what it says, if it's False then `other`
    can extend past `self`'s leaves as long as it's on subtrees of those leaves

    FIXME good report
    """
    if not all_the_way_to_the_leaves and not self.paths:
        return True

    for key, paths in other.items():
        if key in self and self[key].covers(
            paths, all_the_way_to_the_leaves=all_the_way_to_the_leaves
        ):
            continue

        for self_key, self_paths in self.items():
            if is_wildcard(self_key):
                if self_paths.covers(
                    paths, all_the_way_to_the_leaves=all_the_way_to_the_leaves
                ):
                    break
        else:
            return False

    return True


def extends[T](self: PathsOf[T], other: PathsOf[T]) -> bool:
    return self.covers(other, all_the_way_to_the_leaves=True)


def _remove_lowest_level[T](
    self: PathsOf[T], depth: int = 0
) -> tuple[PathsOf[T], int] | None:
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


def merge[T](
    self: PathsOf[T], other: PathsOf[T], *, merge_wildcards: bool = False
) -> PathsOf[T]:
    # Importing properly seems to have inevitable loop
    from . import PathsOf

    if not self.paths and not other.paths:
        assert self == other
        return self

    assert self.type == other.type
    assert self.sequence_length == other.sequence_length

    new_explicit_paths = dict(self)

    def merge_key(key: PathKey, paths: PathValue):
        if key in new_explicit_paths:
            new_explicit_paths[key] = new_explicit_paths[key].merge(paths)
        else:
            new_explicit_paths[key] = paths

    if merge_wildcards:
        wc_subtree = None
        for key, paths in other.items():
            if is_wildcard(key):
                if wc_subtree is None:
                    wc_subtree = paths
                else:
                    wc_subtree = wc_subtree.merge(paths)
            else:
                merge_key(key, paths)
        if wc_subtree is not None:
            merge_key(Wildcard(wc_subtree), wc_subtree)
    else:
        for key, paths in other.items():
            merge_key(key, paths)

    return PathsOf(
        self.type,
        explicit_paths=frozendict(new_explicit_paths),
        sequence_length=self.sequence_length,
    )
