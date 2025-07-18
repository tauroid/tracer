from __future__ import annotations
from dataclasses import dataclass, replace
import logging
from typing import Any, Callable, Collection, Sequence

from frozendict import frozendict


from .cache import cache
from .pathsof import PathKey, PathsOf
from .pathsof.mapping import consolidate_mapping_tree
from .pathsof.tree_maths.single_wildcard_subtrees import single_wildcard_subtrees
from .pathsof.wildcard import Wildcard, is_wildcard

logger = logging.getLogger()


def _get_identical_leaf_subtree[T](
    possibilities: PathsOf[T], selection: PathsOf[T]
) -> PathsOf[Any] | None:
    if not possibilities:
        return selection

    possibility_selections = {
        key: (
            (
                *((selection[key],) if key in selection else ()),
                *(
                    subtree
                    for selection_key, subtree in selection.items()
                    if is_wildcard(selection_key)
                ),
            )
            or (PathsOf(selection._type_at_key(key)),)
        )
        for key in possibilities
    }

    subtrees = (
        _get_identical_leaf_subtree(possibilities[key], selection_subtree)
        for key in possibilities
        for selection_subtree in possibility_selections[key]
    )

    subtrees = tuple(subtree for subtree in subtrees if subtree is not None)

    if not subtrees:
        return None

    first, *rest = subtrees

    for subtree in rest:
        if subtree != first:
            raise Exception(
                f"Different leaf subtrees: {repr(first)} and {repr(subtree)}"
            )

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
    link_source: PathsOf[S],
    link_target: PathsOf[T],
    *,
    leaf_mapping: Callable[[PathsOf[Any]], PathsOf[Any]] | None = None,
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
            if leaf_mapping is not None:
                subtree = _get_identical_leaf_subtree(link_source, s)
                # Due to wildcard weirdness and recursion the return type
                # has a possibility of None, but due to `s` covering
                # `link_source` we should get a subtree out
                assert subtree is not None
                return _place_leaf_subtree(link_target, leaf_mapping(subtree))
            return link_target
        else:
            return PathsOf(link_target.type)

    return forward


def link[S, T](
    s: PathsOf[S],
    t: PathsOf[T],
    *,
    leaf_mapping: Tracer[Any, Any] | None = None,
) -> Tracer[S, T]:
    return Tracer(
        forward=_forward_from_link(
            s, t, leaf_mapping=leaf_mapping.trace if leaf_mapping else None
        ),
        backward=_forward_from_link(
            t, s, leaf_mapping=leaf_mapping.reverse.trace if leaf_mapping else None
        ),
    )


def copy[S, T](s: PathsOf[S], t: PathsOf[T]) -> Tracer[S, T]:
    return link(
        s, t, leaf_mapping=Tracer[Any, Any](forward=lambda x: x, backward=lambda x: x)
    )


def _forward_through_multiple[S, T](
    paths: PathsOf[S],
    forwards: Collection[Callable[[PathsOf[S]], PathsOf[T]]],
    *,
    _conjunction: bool,
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

    `_conjunction` means that, for a particular input, all of
    `forwards` must produce a (nonempty) tree, otherwise the
    result is discarded. Being false ("disjunction") means that
    the empty trees are merged in with the nonempty regardless.
    """

    def single_subtree_forward(subtree: PathsOf[S]) -> PathsOf[T]:
        first, *rest = forwards
        result = first(subtree)

        if _conjunction and not result:
            return result

        for forward in rest:
            forwarded = forward(subtree)

            if _conjunction and not forwarded:
                return forwarded

            result = result.merge(forwarded, merge_wildcards=True)

        return result

    subtrees_iter = single_wildcard_subtrees(paths)
    result = single_subtree_forward(next(subtrees_iter))
    for subtree in subtrees_iter:
        result = result.merge(single_subtree_forward(subtree))

    return consolidate_mapping_tree(result)


def _combination[S, T](
    *members: Tracer[S, T], _conjunction: bool, fully_specified: bool
) -> Tracer[S, T]:

    def forward(s: PathsOf[S]) -> PathsOf[T]:
        return _forward_through_multiple(
            s, tuple(m.forward for m in members), _conjunction=_conjunction
        )

    def backward(t: PathsOf[T]) -> PathsOf[S]:
        return _forward_through_multiple(
            t, tuple(m.backward for m in members), _conjunction=_conjunction
        )

    return Tracer(forward=forward, backward=backward, fully_specified=fully_specified)


def conjunction[S, T](
    *members: Tracer[S, T], fully_specified: bool = True
) -> Tracer[S, T]:
    return _combination(*members, _conjunction=True, fully_specified=fully_specified)


def disjunction[S, T](
    *members: Tracer[S, T], fully_specified: bool = True
) -> Tracer[S, T]:
    return _combination(*members, _conjunction=False, fully_specified=fully_specified)


def opaque[S, T](
    *, forward: Callable[[S], T], backward: Callable[[T], S]
) -> Tracer[S, T]:
    """
    Not thinking about this very hard

    I guess depending on the actual implementations of `forward`
    and `backward` this can be somewhat non-opaque but in
    generality it's just "give whole specific input, get whole
    specific output"

    Also should have some kind of human informational description
    field on these
    """
    return Tracer(
        forward=lambda s: PathsOf.a(forward(s.assembled)),
        backward=lambda t: PathsOf.a(backward(t.assembled)),
        fully_specified=False,
    )


@dataclass(frozen=True, kw_only=True)
class Tracer[S, T]:
    forward: Callable[[PathsOf[S]], PathsOf[T]]
    backward: Callable[[PathsOf[T]], PathsOf[S]]
    fully_specified: bool = True

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
        if self.fully_specified:
            self._check_coherence(s, t)
        return t

    def __call__(self, s: S) -> T:
        # Assumes that result of `trace` is assemblable (should be)
        return self.trace(PathsOf.an(s)).assembled

    @property
    @cache
    def reverse(self):
        return Tracer(
            forward=self.backward,
            backward=self.forward,
            fully_specified=self.fully_specified,
        )

    def loop(
        self, t_query: PathsOf[T], resource: Callable[[PathsOf[S]], PathsOf[S]]
    ) -> PathsOf[T]:
        s_query = self.reverse.trace(t_query)
        return self.trace(resource(s_query).extract(s_query)).extract(
            t_query,
            # The logic here is, if it's fully specified, then the round trip
            # should have brought back all the requested data. But no such
            # guarantee for partially specified. `must_match_all` does need to
            # special case for sums if this is going to work though (you can
            # legitimately query both sum branches, but not legitimately expect
            # data back on _both_)
            must_match_all=self.fully_specified,
        )
