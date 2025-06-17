from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Hashable, Iterator, Mapping, get_origin

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

    from ._construction import eg, around
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

    @cache
    def __str__(self) -> str:
        return self._as_indent_tree()

    def __getitem__(self, key: PathKey) -> PathsOf[Any]:
        paths = self.paths[key]
        # FIXME commenting out but this and other sanity checks need to happen
        # if isinstance(key, PathsOf):
        # Can this be relaxed? Not sure yet
        # Think of it like the key is matching, and paths are pointing to
        #
        # Do we point to things we didn't match?
        # Do we match things without pointing to them?
        #
        # I'm dubious of either but could be swayed by an example
        #
        # TODO also this check should be by self.type not key
        #      and be in __post_init__
        # origin = get_origin(self.type) or self.type
        # if issubclass(origin, Mapping):
        #     assert key == paths["key"]
        # else:
        #     assert key == paths
        return paths

    def __iter__(self) -> Iterator[PathKey]:
        return iter(self.paths)

    def __len__(self) -> int:
        return len(self.paths)
