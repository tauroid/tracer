from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Any, Mapping, Sequence, overload

from frozendict import frozendict

if TYPE_CHECKING:
    from . import PathsOf

from . import PathKey


@overload
def eg[
    T
](self: PathsOf[T], paths_or_prefix: Sequence[PathKey], paths: PathsOf[Any]) -> PathsOf[
    T
]: ...


@overload
def eg[
    T
](
    self: PathsOf[T],
    paths_or_prefix: Mapping[PathKey, PathsOf[Any]],
    paths: None = None,
) -> PathsOf[T]: ...


def eg[
    T
](
    self: PathsOf[T],
    paths_or_prefix: Mapping[PathKey, PathsOf[Any]] | Sequence[PathKey],
    paths: PathsOf[Any] | None = None,
) -> PathsOf[T]:
    """This is probably going to end up with bananas syntax"""
    if paths is None:
        return replace(self, explicit_paths=frozendict(paths_or_prefix))
    else:
        # Importing properly seems to have inevitable loop
        from . import PathsOf

        if self.paths:
            raise Exception(
                "Not using prefix path on nonempty objects yet,"
                " but it makes sense to do"
            )

        key, *rest = paths_or_prefix
        return replace(
            self,
            explicit_paths=frozendict(
                {
                    key: (
                        PathsOf(self._type_at_key(key)).eg(rest, paths)
                        if rest
                        else paths
                    )
                }
            ),
        )
