from __future__ import annotations
from dataclasses import dataclass, replace
import logging
from typing import Any, Callable, Collection

from frozendict import frozendict


from .cache import cache
from .pathsof import PathsOf

logger = logging.getLogger()


def _get_identical_leaf_subtree[
    T
](possibilities: PathsOf[T], selection: PathsOf[T]) -> PathsOf[Any]:
    # `not selection` means the selection was above the `possibilities` leaves.
    # In this case we don't want a subtree (there being a subtree in another
    # branch could be meaningful, but I'm choosing to complain rather than
    # implicitly substitute a copy, given the user is being vague).
    if not possibilities or not selection:
        return selection

    first, *rest = (
        _get_identical_leaf_subtree(possibilities[key], selection[key])
        # FIXME wildcards
        for key in possibilities
    )

    for subtree in rest:
        if subtree != first:
            raise Exception(f"Different subtrees in copy: {first} and {subtree}")

    return first


def _place_leaf_subtree[
    T
](paths_of_target: PathsOf[T], subtree: PathsOf[Any]) -> PathsOf[T]:
    """FIXME typecheckinggg"""
    if not paths_of_target:
        return subtree

    return replace(
        paths_of_target,
        explicit_instance=None,
        explicit_paths=frozendict(
            {
                key: _place_leaf_subtree(paths, subtree)
                for key, paths in paths_of_target.items()
            }
        ),
    )


def _forward_from_link[
    S, T
](
    t_type: type[T], link_source: PathsOf[S], link_target: PathsOf[T], copy: bool = True
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
                return _place_leaf_subtree(
                    link_target, _get_identical_leaf_subtree(link_source, s)
                )
            return link_target
        else:
            return PathsOf(t_type)

    return forward


def link[
    S, T
](s_type: type[S], t_type: type[T], s: PathsOf[S], t: PathsOf[T]) -> Tracer[S, T]:
    return Tracer(
        forward=_forward_from_link(t_type, s, t),
        backward=_forward_from_link(s_type, t, s),
    )


def disjunction[
    S, T
](s_type: type[S], t_type: type[T], members: Collection[Tracer[S, T]]) -> Tracer[S, T]:

    def forward(s: PathsOf[S]) -> PathsOf[T]:
        t = PathsOf(t_type)
        for member in members:
            t = t.merge(member.forward(s))
        return t

    def backward(t: PathsOf[T]) -> PathsOf[S]:
        s = PathsOf(s_type)
        for member in members:
            s = s.merge(member.backward(t))
        return s

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
        assert s_.extends(s), f"{s_} does not extend {s}"

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
        return self.trace(PathsOf(s)).assembled

    @property
    @cache
    def reverse(self):
        return Tracer(forward=self.backward, backward=self.forward)
