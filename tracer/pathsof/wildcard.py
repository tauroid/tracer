from __future__ import annotations
from dataclasses import dataclass, replace
import sys
from typing import TYPE_CHECKING, Any, Mapping

if sys.version_info >= (3, 13):
    from typing import TypeIs
else:
    from typing_extensions import TypeIs

from frozendict import frozendict


if TYPE_CHECKING:
    from . import PathsOf, PathKey


@dataclass(frozen=True)
class Wildcard:
    subtree: PathsOf[Any] | None = None


_ = Wildcard()


def is_wildcard(x: Any) -> TypeIs[Wildcard]:
    return isinstance(x, Wildcard)


def populate_wildcards(
    paths: Mapping[PathKey, PathsOf[Any]],
) -> frozendict[PathKey, PathsOf[Any]]:
    populated: dict[PathKey, PathsOf[Any]] = {}
    for key, subpaths in paths.items():
        populated_paths = replace(subpaths, paths=populate_wildcards(subpaths))
        populated_key = (
            Wildcard(populated_paths)
            if is_wildcard(key) and key.subtree is None
            else key
        )
        populated[populated_key] = populated_paths

    return frozendict(populated)
