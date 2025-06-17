from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Collection, Self


from .cache import cache
from .pathsof import PathsOf


def _forward_from_links[
    S, T
](
    t_type: type[T],
    links: Collection[tuple[PathsOf[S], PathsOf[T]]],
) -> Callable[
    [PathsOf[S]], PathsOf[T]
]:
    def forward(s: PathsOf[S]) -> PathsOf[T]:
        t = PathsOf(t_type)
        for link_source, link_target in links:
            if s.covers(link_source):
                t = t.merge(link_target)
        return t

    return forward


@dataclass(frozen=True, kw_only=True)
class Tracer[S, T]:
    forward: Callable[[PathsOf[S]], PathsOf[T]]
    backward: Callable[[PathsOf[T]], PathsOf[S]]

    @classmethod
    def from_links(
        cls,
        s_type: type[S],
        t_type: type[T],
        *,
        links: Collection[tuple[PathsOf[S], PathsOf[T]]],
    ) -> Self:
        """
        TODO do BasicRelation / Copy in here

        This has reminded me of an aspect missing so far in tracer.

        We're only modelling "this definitely is associated".

        We're not modelling "this could be associated if you had also selected
        this other stuff".

        So, NOTE, reminder about that.
        """
        links_backward = tuple((t, s) for s, t in links)
        return cls(
            forward=_forward_from_links(t_type, links),
            backward=_forward_from_links(s_type, links_backward),
        )

    def _check_roundtripping(self, s: PathsOf[S], t: PathsOf[T]):
        print(f"Start: {s}")
        print(f"Forward: {t}")
        s_ = self.backward(t)
        print(f"Backward again: {s_}")
        # This used to be `extends` - that has some guarantee specificity
        # is not lost (though with sum types that's questionable)
        #
        # `covers` allows information to be lost (but still we have to map back
        # to something at least containing all we originally had)
        assert s_.covers(s), f"{s_} does not cover {s}"

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
            assert t0.extends(t)

        self._check_roundtripping(s, t)

        self._check_coherence(s.lub, t0, False)

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
