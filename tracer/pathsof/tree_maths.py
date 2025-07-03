from __future__ import annotations
from dataclasses import replace
from itertools import product
from typing import TYPE_CHECKING, Iterator

from frozendict import frozendict


if TYPE_CHECKING:
    from . import PathsOf

from .wildcard import Wildcard, is_wildcard

from . import PathKey, PathValue


def covers[T](
    self: PathsOf[T], other: PathsOf[T], *, all_the_way_to_the_leaves: bool = False
) -> bool:
    """
    If we have at least all of `other`'s paths and don't conflict

    `all_the_way_to_the_leaves` means what it says, if it's False then `other`
    can extend past `self`'s leaves as long as it's on subtrees of those leaves

    FIXME good report
    """
    if not all_the_way_to_the_leaves and not self.paths:
        return True

    for key, paths in other.items():
        if key in self and self[key].covers(
            paths, all_the_way_to_the_leaves=all_the_way_to_the_leaves
        ):
            continue

        for self_key, self_paths in self.items():
            if is_wildcard(self_key):
                if self_paths.covers(
                    paths, all_the_way_to_the_leaves=all_the_way_to_the_leaves
                ):
                    break
        else:
            return False

    return True


def extends[T](self: PathsOf[T], other: PathsOf[T]) -> bool:
    return self.covers(other, all_the_way_to_the_leaves=True)


def _remove_lowest_level[T](
    self: PathsOf[T], depth: int = 0
) -> tuple[PathsOf[T], int] | None:
    if not self.paths:
        return None

    reduced = tuple(
        (key, reduced_child, reduced_child_depth)
        for key, child in self.items()
        for reduced_child_pair in (_remove_lowest_level(child, depth + 1),)
        if reduced_child_pair is not None
        for reduced_child, reduced_child_depth in (reduced_child_pair,)
    )

    if not reduced:
        return replace(self, paths=frozendict()), depth

    reduced_child_keys, reduced_children, reduced_child_depths = zip(*reduced)

    max_reduced_child_depth = max(reduced_child_depths)

    return (
        replace(
            self,
            paths=frozendict(
                {
                    **self,
                    **{
                        key: reduced_child
                        for key, reduced_child, reduced_child_depth in zip(
                            reduced_child_keys, reduced_children, reduced_child_depths
                        )
                        if reduced_child_depth == max_reduced_child_depth
                    },
                }
            ),
        ),
        max_reduced_child_depth,
    )


def remove_lowest_level_or_none[T](self: PathsOf[T]) -> PathsOf[T] | None:
    removed = _remove_lowest_level(self)
    return removed[0] if removed else None


def remove_lowest_level[T](self: PathsOf[T]) -> PathsOf[T]:
    removed = remove_lowest_level_or_none(self)
    if removed is None:
        raise Exception(f"{self} has no children")
    return removed


def merge[T](
    self: PathsOf[T], *others: PathsOf[T], merge_wildcards: bool = False
) -> PathsOf[T]:
    for other in others:
        assert self.type == other.type, f"{self.type} != {other.type}"

    # TODO possibly bad to just merge these, not sure
    not_none_sequence_lengths = tuple(paths.sequence_length for paths in (self, *others) if paths.sequence_length is not None)
    if not_none_sequence_lengths:
        # assert self.sequence_length == other.sequence_length
        # FIXME is this right? sequences give me heebie jeebies
        sequence_length = max(not_none_sequence_lengths)
    else:
        sequence_length = None

    if not any(paths.paths for paths in (self, *others)):
        return replace(self, sequence_length=sequence_length)

    # Importing properly seems to have inevitable loop
    from . import PathsOf

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


def extract[T](self: PathsOf[T], paths: PathsOf[T]) -> PathsOf[T]:
    extracted = replace(self, paths=frozendict())

    for subtree in single_wildcard_subtrees(self):
        if (single_extracted := _extract_single_wildcards(subtree, paths)) is not None:
            extracted = extracted.merge(single_extracted)

    return extracted


def _extract_single_wildcards[T](
    source: PathsOf[T], paths: PathsOf[T]
) -> PathsOf[T] | None:
    if not paths:
        return source

    if any(not is_wildcard(key) and key not in source for key in paths):
        # Revisit for sums? Dunno
        return None

    extracted_paths_unmerged: dict[PathKey, PathValue] = {}
    for key, subpaths in paths.items():
        if is_wildcard(key):
            for source_key, source_subpaths in source.items():
                extracted = _extract_single_wildcards(source_subpaths, subpaths)
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
            extracted = _extract_single_wildcards(source[key], subpaths)
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
