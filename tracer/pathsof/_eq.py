"""
This file contains unused thoughts about if you could use
`PathsOf` as a `PathKey` to match something different to the
paths the key maps to. E.g. match on date, link to name.

But this doesn't seem to offer anything over just a wildcard,
as the paths can select the (specific) date and the (specific
or not) name. I guess you signify that the name is involved in
the "computation" and the date isn't, but given arguably
selection is part of the computation, this seems not that
crucial.

Anyway I super can't see a use for a nontrivial PathsOf key
_within_ a PathsOf key, which this opens the door for, so I
reckon nip this in the bud unless I come upon something
essential it would enable.
"""

from typing import TYPE_CHECKING, Any, Collection, Mapping


if TYPE_CHECKING:
    from . import PathsOf, PathKey


def _filling_overlap(
    key: PathKey, other_keys: Collection[PathKey]
) -> Collection[PathKey] | None:
    if not isinstance(key, PathsOf):
        return (key,) if key in other_keys else None
    else:
        # FIXME what goes here
        pass


def _filled_and_equal(
    filled: Mapping[PathKey, PathsOf[Any]], fillers: Mapping[PathKey, PathsOf[Any]]
) -> bool:
    for key, paths in filled.items():
        overlapping_filler_keys = _filling_overlap(key, tuple(fillers))

        if overlapping_filler_keys is None:
            return False

        for filler_key in overlapping_filler_keys:
            if paths != fillers[filler_key]:
                return False

    return True


def eq[T](self: PathsOf[T], other: Any) -> bool:
    if not isinstance(other, PathsOf) or self.type != other.type:
        return False

    if not self and not other:
        return True

    self_children = self.paths or {
        key: PathsOf(paths.type) for key, paths in other.items()
    }

    other_children = other.paths or {
        key: PathsOf(paths.type) for key, paths in self.items()
    }

    return _filled_and_equal(self_children, other_children) and _filled_and_equal(
        other_children, self_children
    )
