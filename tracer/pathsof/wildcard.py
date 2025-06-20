from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping


if TYPE_CHECKING:
    from . import PathsOf, PathKey


@dataclass(frozen=True)
class Wildcard:
    _subtree: PathsOf[Any] | None = None


_ = Wildcard()


def is_wildcard(x: Any) -> bool:
    return isinstance(x, Wildcard)


def normalise_wildcards(
    paths: Mapping[PathKey, PathsOf[Any]],
) -> Mapping[PathKey, PathsOf[Any]]:
    from . import PathsOf

    normalised: dict[PathKey, PathsOf[Any]] = {}
    for key, subpaths in paths.items():
        normalised_paths = PathsOf(
            subpaths.type, sequence_length=subpaths.sequence_length
        ).eg(normalise_wildcards(subpaths))
        normalised_key = Wildcard(normalised_paths) if is_wildcard(key) else key
        normalised[normalised_key] = normalised_paths

    return normalised
