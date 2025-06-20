from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Hashable, Iterator, Mapping, cast

from frozendict import frozendict

from ..cache import cache


PathKey = Hashable
# Just a forward reference for the Mapping inherit
type PathValue = PathsOf[Any]


@dataclass(frozen=True, kw_only=True)
class PathsOf[T](Mapping[PathKey, PathValue]):
    prototype: type[T] | T = field(kw_only=False)
    explicit_instance: T | None = field(kw_only=False, default=None)
    explicit_paths: frozendict[PathKey, PathsOf[Any]] | None = field(default=None)
    sequence_length: int | None = None
    """If `T` is a `Sequence` of some kind"""

    def __post_init__(self): ...

    """FIXME Validation of `paths` (and other fields) based on `prototype`"""

    def __eq__(self, other: Any):
        if (
            not isinstance(other, PathsOf)
            or self.type != cast(PathsOf[Any], other).type
        ):
            return False

        return (
            self.paths == other.paths and self.sequence_length == other.sequence_length
        )

    @cache
    def __str__(self) -> str:
        return self._as_indent_tree()

    def __getitem__(self, key: PathKey) -> PathsOf[Any]:
        return self.paths[key]

    def __iter__(self) -> Iterator[PathKey]:
        return iter(self.paths)

    @cache
    def __len__(self) -> int:
        return len(self.paths)

    from ._construction import eg
    from ._serialisation import (
        as_indent_tree as _as_indent_tree,
        as_key_str as _as_key_str,
    )

    from ._normalised_properties import type_ as type, instance as instance
    from ._type_checking import type_at_key as _type_at_key, union
    from ._disassembly import paths
    from ._assembly import assembled

    from ._tree_maths import (
        extends,
        covers,
        merge,
        remove_lowest_level,
        remove_lowest_level_or_none,
    )
