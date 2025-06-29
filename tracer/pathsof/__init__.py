from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Hashable, Iterator, Mapping

from frozendict import frozendict

from ..cache import cache


PathKey = Hashable
# Just a forward reference for the Mapping inherit
type PathValue = PathsOf[Any]


@dataclass(frozen=True, kw_only=True)
class PathsOf[T](Mapping[PathKey, PathValue]):
    type: type[T] = field(kw_only=False)
    paths: frozendict[PathKey, PathsOf[Any]] = frozendict()
    sequence_length: int | None = None
    """If `T` is a `Sequence` of some kind"""

    def __post_init__(self): ...

    """FIXME Validation of `paths` (and other fields) based on `prototype`"""

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

    from ._construction import a, an, specifically, eg
    from ._serialisation import (
        as_indent_tree as _as_indent_tree,
        as_key_str as _as_key_str,
    )
    from ._type_checking import type_at_key as _type_at_key
    from ._assembly import assembled
    from ._disassembly import paths_from_object as _paths_from_object

    from .tree_maths import (
        extends,
        extract,
        covers,
        merge,
        remove_lowest_level,
        remove_lowest_level_or_none,
    )
