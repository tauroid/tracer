from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING

from frozendict import frozendict


if TYPE_CHECKING:
    from .. import PathsOf

from .. import PathKey, PathValue

from ..wildcard import Wildcard, is_wildcard

from .single_wildcard_subtrees import single_wildcard_subtrees


def extract[T](
    self: PathsOf[T], paths: PathsOf[T], *, must_match_all: bool = True
) -> PathsOf[T]:
    extracted = replace(self, paths=frozendict())

    for subtree in single_wildcard_subtrees(self):
        if (
            single_extracted := _extract_single_wildcards(
                subtree, paths, must_match_all=must_match_all
            )
        ) is not None:
            extracted = extracted.merge(single_extracted)

    return extracted


def _extract_single_wildcards[T](
    source: PathsOf[T], paths: PathsOf[T], *, must_match_all: bool
) -> PathsOf[T] | None:
    from .. import PathsOf

    if not paths:
        return source

    if must_match_all:
        if any(not is_wildcard(key) and key not in source for key in paths):
            # Revisit for sums?
            # Also is silent omission the way to go about this vs exception?
            # And a complete discrepancy report would be better than giving up
            # part of the way through
            return None

    extracted_paths_unmerged: dict[PathKey, PathValue] = {}
    for key, subpaths in paths.items():
        if is_wildcard(key):
            for source_key, source_subpaths in source.items():
                extracted = _extract_single_wildcards(
                    source_subpaths, subpaths, must_match_all=must_match_all
                )
                if extracted is None:
                    return None
                # I'm kind of hoping this conditional (and for
                # loop) isn't necessary when I get strict about
                # wildcards only being for collections (and
                # collections only using wildcards, ...)
                if is_wildcard(source_key):
                    source_key = Wildcard(extracted)
                extracted_paths_unmerged[source_key] = extracted
        else:
            extracted = _extract_single_wildcards(
                source.get(key, PathsOf(source._type_at_key(key))),
                subpaths,
                must_match_all=must_match_all,
            )
            if extracted is None:
                return None
            extracted_paths_unmerged[key] = extracted

    # Recombine wildcards (`paths` can have multiple, `source` can't)
    # TODO probably faster if this happened at the top of the tree only
    #      but then need a merge_wildcards function
    wc_subpaths = None
    non_wc_extracted_paths: dict[PathKey, PathValue] = {}
    for key, subpaths in extracted_paths_unmerged.items():
        if is_wildcard(key):
            if wc_subpaths is None:
                wc_subpaths = subpaths
            else:
                wc_subpaths = wc_subpaths.merge(subpaths, merge_wildcards=True)
        else:
            non_wc_extracted_paths[key] = subpaths

    extracted_paths = non_wc_extracted_paths
    if wc_subpaths is not None:
        extracted_paths[Wildcard(wc_subpaths)] = wc_subpaths

    return replace(source, paths=frozendict(extracted_paths))
