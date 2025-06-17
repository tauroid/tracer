from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Any, cast

from frozendict import frozendict

from ..cache import cache

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
        match key:
            # PathsOf keys are weird but how else to do wildcarding
            # NOTE this depends on PathsOf keys having key == paths
            #      which is not an entirely 100% assured proposition
            case PathsOf():
                if not any(
                    cast(PathsOf[Any], self_key).covers(cast(PathsOf[Any], key))
                    for self_key in self
                    if isinstance(self_key, PathsOf)
                ):
                    return False
            case _:
                if key not in self or not self[key].covers(paths):
                    return False

    return True


@property
@cache
def lub[T](self: PathsOf[T]) -> PathsOf[T] | None:
    r"""
    Least upper bound of leaf nodes viewing parent-child relationship as poset

                                    --> x
                o            o           o
                |            |
            --> o        --> o
            / \           |
            o   o          o
                |\
                o o
    """
    match tuple(self.items()):
        case ():
            return None
        case (k, v),:
            if v.lub is not None:
                return replace(
                    self,
                    prototype=self.type,
                    explicit_instance=None,
                    explicit_paths=frozendict({k: v.lub}),
                )
            else:
                return replace(
                    self,
                    prototype=self.type,
                    explicit_instance=None,
                    explicit_paths=frozendict({}),
                )
        case _:
            return replace(
                self,
                prototype=self.type,
                explicit_instance=None,
                explicit_paths=frozendict({}),
            )


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
