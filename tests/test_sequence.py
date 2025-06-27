from typing import Sequence

from tracer import PathsOf, Tracer, assert_isinstance


def reverse_forward[T](l: PathsOf[Sequence[T]]) -> PathsOf[Sequence[T]]:
    n = l.sequence_length
    assert n is not None
    return PathsOf(Sequence[T], sequence_length=n).eg(
        {n - pos - 1: elem for pos, elem in l.items() if assert_isinstance(pos, int)},
    )


def reverse_backward[T](l: PathsOf[Sequence[T]]) -> PathsOf[Sequence[T]]:
    return reverse_forward(l)


reverse = Tracer(forward=reverse_forward, backward=reverse_backward)


def test_reverse():
    reverse.trace(
        PathsOf(Sequence[str], sequence_length=10).eg(
            {3: PathsOf.an("apple"), 7: PathsOf.a("pear"), 2: PathsOf.a("banana")},
        )
    )
