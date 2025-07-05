from __future__ import annotations
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .. import PathsOf

from ..wildcard import is_wildcard


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
