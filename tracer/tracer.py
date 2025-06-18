from __future__ import annotations
from dataclasses import dataclass
import logging
from typing import Callable, Collection


from .cache import cache
from .pathsof import PathsOf

logger = logging.getLogger()


def _forward_from_link[
    S, T
](t_type: type[T], link_source: PathsOf[S], link_target: PathsOf[T]) -> Callable[
    [PathsOf[S]], PathsOf[T]
]:
    def forward(s: PathsOf[S]) -> PathsOf[T]:
        if s.covers(link_source):
            return link_target
        else:
            return PathsOf(t_type)

    return forward


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


def link[
    S, T
](s_type: type[S], t_type: type[T], s: PathsOf[S], t: PathsOf[T]) -> Tracer[S, T]:
    return Tracer(
        forward=_forward_from_link(t_type, s, t),
        backward=_forward_from_link(s_type, t, s),
    )


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
