from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING

from frozendict import frozendict


if TYPE_CHECKING:
    from .. import PathsOf


def _remove_lowest_level[T](
    self: PathsOf[T], depth: int = 0
) -> tuple[PathsOf[T], int] | None:
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
        return replace(self, paths=frozendict()), depth

    reduced_child_keys, reduced_children, reduced_child_depths = zip(*reduced)

    max_reduced_child_depth = max(reduced_child_depths)

    return (
        replace(
            self,
            paths=frozendict(
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
