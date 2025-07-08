from __future__ import annotations
from dataclasses import replace
from itertools import product
from typing import TYPE_CHECKING, Iterator

from frozendict import frozendict


if TYPE_CHECKING:
    from .. import PathsOf

from ..wildcard import is_wildcard


def single_wildcard_subtrees[T](paths: PathsOf[T]) -> Iterator[PathsOf[T]]:
    if any(map(is_wildcard, paths)):
        # Basically if there are any wildcards, we'll also proceed
        # through the non-wildcard branches one at a time.
        #
        # An argument could be made for doing the non-wildcards all
        # at once, or in contiguous blocks, but this is it for now
        #
        # So in presence of wildcards you can't have a mapping
        # straddling multiple branches (e.g. list elements) (but
        # without wildcards you can)

        for key, subpaths in paths.items():
            for subtree in single_wildcard_subtrees(subpaths):
                yield replace(paths, paths=frozendict({key: subtree}))
    else:
        for subtrees in product(*map(single_wildcard_subtrees, paths.values())):
            yield replace(
                paths,
                paths=frozendict(
                    {key: subtree for key, subtree in zip(paths.keys(), subtrees)}
                ),
            )
