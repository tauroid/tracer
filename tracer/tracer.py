from __future__ import annotations
from dataclasses import dataclass, replace
from itertools import product
import logging
from typing import Any, Callable, Collection, Iterator

from frozendict import frozendict


from .cache import cache
from .pathsof import PathsOf
from .pathsof.mapping import consolidate_mapping_tree
from .pathsof.wildcard import Wildcard, is_wildcard

logger = logging.getLogger()


def _get_identical_leaf_subtree[T](
    possibilities: PathsOf[T], selection: PathsOf[T]
) -> PathsOf[Any] | None:
    # `not selection` means the selection was above the `possibilities` leaves.
    # In this case we don't want a subtree (there being a subtree in another
    # branch could be meaningful, but I'm choosing to complain rather than
    # implicitly substitute a copy, given the user is being vague).
    if not possibilities or not selection:
        return selection

    subtrees = (
        _get_identical_leaf_subtree(possibilities[possibilities_key], selection_subtree)
        for possibilities_key in possibilities
        # possibilities just has to be covered. Unfortunately
        # wildcards make it so multiple selection subtrees can
        # match a possibilities subtree but only one of them
        # needs to cover it. So some selection subtrees might
        # have partial coverage
        for selection_subtree in (
            *(
                (selection[possibilities_key],)
                if possibilities_key in selection
                else ()
            ),
            *(
                subtree
                for selection_key, subtree in selection.items()
                if is_wildcard(selection_key)
            ),
        )
    )

    subtrees = tuple(subtree for subtree in subtrees if subtree is not None)

    if not subtrees:
        return None

    first, *rest = subtrees

    for subtree in rest:
        if subtree != first:
            raise Exception(f"Different subtrees in copy: {first} and {subtree}")

    return first


def _place_leaf_subtree[T](
    paths_of_target: PathsOf[T], subtree: PathsOf[Any]
) -> PathsOf[T]:
    """FIXME typecheckinggg"""
    if not paths_of_target:
        return subtree

    return replace(
        paths_of_target,
        paths=frozendict(
            {
                Wildcard(placed_paths) if is_wildcard(key) else key: placed_paths
                for key, paths in paths_of_target.items()
                for placed_paths in (_place_leaf_subtree(paths, subtree),)
            }
        ),
    )


def _forward_from_link[S, T](
    link_source: PathsOf[S], link_target: PathsOf[T], copy: bool = True
) -> Callable[[PathsOf[S]], PathsOf[T]]:
    """
    `copy` determines what to do about subpaths if there are any

    By default (`True`) it will copy the subtrees in `s` of the leaves of
    `link_source`, to under the leaves of `link_target`. For this to be
    coherent, it first makes sure all the source subtrees are the same.
    Then, so are all the target subtrees.

    FIXME this needs typechecking

    `False` just means it outputs the link target directly regardless of subpaths
    """

    def forward(s: PathsOf[S]) -> PathsOf[T]:
        if s.covers(link_source):
            if copy:
                subtree = _get_identical_leaf_subtree(link_source, s)
                # Due to wildcard weirdness and recursion the return type
                # has a possibility of None, but due to `s` covering
                # `link_source` we should get a subtree out
                assert subtree is not None
                return _place_leaf_subtree(link_target, subtree)
            return link_target
        else:
            return PathsOf(link_target.type)

    return forward


def link[S, T](s: PathsOf[S], t: PathsOf[T]) -> Tracer[S, T]:
    return Tracer(
        forward=_forward_from_link(s, t),
        backward=_forward_from_link(t, s),
    )


def _single_wildcard_subtrees[T](paths: PathsOf[T]) -> Iterator[PathsOf[T]]:
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
            for subtree in _single_wildcard_subtrees(subpaths):
                yield replace(paths, paths=frozendict({key: subtree}))
    else:
        for subtrees in product(*map(_single_wildcard_subtrees, paths.values())):
            yield replace(
                paths,
                paths=frozendict(
                    {key: subtree for key, subtree in zip(paths.keys(), subtrees)}
                ),
            )


def _forward_through_multiple[S, T](
    paths: PathsOf[S], forwards: Collection[Callable[[PathsOf[S]], PathsOf[T]]]
) -> PathsOf[T]:
    """
    Opinionated way of putting a single `PathsOf` through multiple
    tracing functions. Basically:
    - For each single-wildcard subtree (where any node only has
      max 1 wildcard child) of `paths`:
      - Get every output tree from each of forwards
      - Merge them, merging wildcards. This then produces another
        single-wildcard tree.
    - Merge the resulting single-wildcard trees, not merging
      wildcards

    This feels like the most "reversible" way to deal with
    wildcards, but until I think about that more, those scare
    quotes remain firmly installed. It is certainly not the only
    way to deal with wildcards.
    """

    def single_subtree_forward(subtree: PathsOf[S]) -> PathsOf[T]:
        first, *rest = forwards
        result = first(subtree)
        for forward in rest:
            result = result.merge(forward(subtree), merge_wildcards=True)
        return result

    subtrees_iter = _single_wildcard_subtrees(paths)
    result = single_subtree_forward(next(subtrees_iter))
    for subtree in subtrees_iter:
        result = result.merge(single_subtree_forward(subtree))

    return consolidate_mapping_tree(result)


def disjunction[S, T](members: Collection[Tracer[S, T]]) -> Tracer[S, T]:

    def forward(s: PathsOf[S]) -> PathsOf[T]:
        return _forward_through_multiple(s, tuple(m.forward for m in members))

    def backward(t: PathsOf[T]) -> PathsOf[S]:
        return _forward_through_multiple(t, tuple(m.backward for m in members))

    return Tracer(forward=forward, backward=backward)


@dataclass(frozen=True, kw_only=True)
class Tracer[S, T]:
    forward: Callable[[PathsOf[S]], PathsOf[T]]
    backward: Callable[[PathsOf[T]], PathsOf[S]]

    def _check_roundtripping(self, s: PathsOf[S], t: PathsOf[T]):
        logger.debug(f"Start: {s}")
        logger.debug(f"Forward: {t}")
        s_ = self.backward(t)
        logger.debug(f"Backward again: {s_}")
        assert s_.extends(s), f"{s_} via {t} does not extend {s}"

    def _check_coherence(
        self,
        s: PathsOf[S] | None,
        t0: PathsOf[T],
        skip_target_check: bool = True,
    ):
        if s is None:
            return

        t = self.forward(s)

        if not skip_target_check:
            assert t.covers(t0), f"{t} does not cover {t0}"

        self._check_roundtripping(s, t)

        self._check_coherence(s.remove_lowest_level_or_none(), t0, False)

    def trace(self, s: PathsOf[S]) -> PathsOf[T]:
        t = self.forward(s)
        self._check_coherence(s, t)
        return t

    def __call__(self, s: S) -> T:
        # Assumes that result of `trace` is assemblable (should be)
        return self.trace(PathsOf.an(s)).assembled

    @property
    @cache
    def reverse(self):
        return Tracer(forward=self.backward, backward=self.forward)
