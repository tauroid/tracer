from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING

from frozendict import frozendict


if TYPE_CHECKING:
    from .. import PathsOf

from ..wildcard import Wildcard, is_wildcard

from .. import PathKey, PathValue


def merge[T](
    self: PathsOf[T], *others: PathsOf[T], merge_wildcards: bool = False
) -> PathsOf[T]:
    for other in others:
        assert self.type == other.type, f"{self.type} != {other.type}"

    # TODO possibly bad to just merge these, not sure
    not_none_sequence_lengths = tuple(
        paths.sequence_length
        for paths in (self, *others)
        if paths.sequence_length is not None
    )
    if not_none_sequence_lengths:
        # assert self.sequence_length == other.sequence_length
        # FIXME is this right? sequences give me heebie jeebies
        sequence_length = max(not_none_sequence_lengths)
    else:
        sequence_length = None

    if not any(paths.paths for paths in (self, *others)):
        return replace(self, sequence_length=sequence_length)

    # Importing properly seems to have inevitable loop
    from .. import PathsOf

    def merge_key(key: PathKey, paths: PathValue):
        if key in new_explicit_paths:
            new_explicit_paths[key] = new_explicit_paths[key].merge(
                paths, merge_wildcards=merge_wildcards
            )
        else:
            new_explicit_paths[key] = paths

    if merge_wildcards:
        new_explicit_paths = {
            key: paths for key, paths in self.items() if not is_wildcard(key)
        }
        match [paths for key, paths in self.items() if is_wildcard(key)]:
            case (wc_subtree,):
                pass
            case ():
                wc_subtree = None
            case _:
                raise Exception(
                    "For `merge_wildcards=True`, the source paths are"
                    " currently expected to only have one wildcard:\n"
                    f"{self}"
                )

        for other in others:
            for key, paths in other.items():
                if is_wildcard(key):
                    if wc_subtree is not None:
                        wc_subtree = wc_subtree.merge(paths, merge_wildcards=True)
                    else:
                        wc_subtree = paths
                else:
                    merge_key(key, paths)

        if wc_subtree is not None:
            merge_key(Wildcard(wc_subtree), wc_subtree)
    else:
        new_explicit_paths = dict(self)
        for other in others:
            for key, paths in other.items():
                merge_key(key, paths)

    return PathsOf(
        self.type,
        paths=frozendict(new_explicit_paths),
        sequence_length=sequence_length,
    )
