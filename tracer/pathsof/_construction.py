from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from frozendict import frozendict

if TYPE_CHECKING:
    from . import PathsOf

from . import PathKey


def eg[T](self: PathsOf[T], paths: Mapping[PathKey, PathsOf[Any]]) -> PathsOf[T]:
    return replace(self, explicit_paths=frozendict(paths))


def around[
    T
](self: PathsOf[T], path: Sequence[PathKey], subobj: PathsOf[Any]) -> PathsOf[T]:
    # Importing properly seems to have inevitable loop
    from . import PathsOf

    if self.paths:
        raise Exception("Not using `around` on nonempty objects yet")

    key, *rest = path
    return replace(
        self,
        explicit_paths=frozendict(
            {
                key: (
                    PathsOf(self._type_at_key(key)).around(rest, subobj)
                    if rest
                    else subobj
                )
            }
        ),
    )
