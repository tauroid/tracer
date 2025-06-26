from __future__ import annotations
from dataclasses import dataclass
from typing import Collection, Mapping

from frozendict import frozendict

from tracer.tracer import disjunction, link
from tracer.pathsof import PathsOf
from tracer.pathsof.wildcard import _


@dataclass(frozen=True)
class Flat:
    a: str
    b: str
    c: str
    d: str


@dataclass(frozen=True)
class A:
    a: Mapping[str, B]


@dataclass(frozen=True)
class B:
    b: Mapping[str, C]


@dataclass(frozen=True)
class C:
    c: Mapping[str, D]


@dataclass(frozen=True)
class D:
    d: Collection[str]


a_pointer = PathsOf(Flat).eg({"a": PathsOf(str)})
b_pointer = PathsOf(Flat).eg({"b": PathsOf(str)})
c_pointer = PathsOf(Flat).eg({"c": PathsOf(str)})
d_pointer = PathsOf(Flat).eg({"d": PathsOf(str)})

a_start = PathsOf(Collection[Flat]).eg({_: a_pointer})
a_end = PathsOf(A).eg(["a", _, "key"], PathsOf(str))

b_start = PathsOf(Collection[Flat]).eg({_: b_pointer})
b_end = PathsOf(A).eg(["a", _, "value", "b", _, "key"], PathsOf(str))

c_start = PathsOf(Collection[Flat]).eg({_: c_pointer})
c_end = PathsOf(A).eg(
    ["a", _, "value", "b", _, "value", "c", _, "key"],
    PathsOf(str),
)

d_start = PathsOf(Collection[Flat]).eg({_: d_pointer})
d_end = PathsOf(A).eg(
    ["a", _, "value", "b", _, "value", "c", _, "value", "d", _],
    PathsOf(str),
)

flat_to_tree = disjunction(
    (
        link(a_start, a_end),
        link(b_start, b_end),
        link(c_start, c_end),
        link(d_start, d_end),
    ),
)


def test_a_forward():
    assert flat_to_tree.trace(a_value_start) == a_value_end


def test_a_backward():
    assert flat_to_tree.reverse.trace(a_value_end) == a_value_start


def test_b_forward():
    assert flat_to_tree.trace(b_start) == b_end


def test_b_backward():
    assert flat_to_tree.reverse.trace(b_end) == b_start


def test_c_forward():
    assert flat_to_tree.trace(c_start) == c_end


def test_c_backward():
    assert flat_to_tree.reverse.trace(c_end) == c_start


def test_d_forward():
    assert flat_to_tree.trace(d_start) == d_end


def test_d_backward():
    assert flat_to_tree.reverse.trace(d_end) == d_start


a_value_start = PathsOf(Collection[Flat]).eg([_, "a"], PathsOf("1"))
a_value_end = PathsOf(A).eg(["a", _, "key"], PathsOf("1"))
b_value_start = PathsOf(Collection[Flat]).eg([_, "b"], PathsOf("2"))
b_value_end = PathsOf(A).eg(["a", _, "value", "b", _, "key"], PathsOf("2"))
c_value_start = PathsOf(Collection[Flat]).eg([_, "c"], PathsOf("3"))
c_value_end = PathsOf(A).eg(
    ["a", _, "value", "b", _, "value", "c", _, "key"], PathsOf("3")
)
d_value_start = PathsOf(Collection[Flat]).eg([_, "d"], PathsOf("4"))
d_value_end = PathsOf(A).eg(
    ["a", _, "value", "b", _, "value", "c", _, "value", "d", _], PathsOf("4")
)


def test_a_value_forward():
    assert flat_to_tree.trace(a_value_start) == a_value_end


def test_a_value_backward():
    assert flat_to_tree.reverse.trace(a_value_end) == a_value_start


def test_b_value_forward():
    assert flat_to_tree.trace(b_value_start) == b_value_end


def test_b_value_backward():
    assert flat_to_tree.reverse.trace(b_value_end) == b_value_start


def test_c_value_forward():
    assert flat_to_tree.trace(c_value_start) == c_value_end


def test_c_value_backward():
    assert flat_to_tree.reverse.trace(c_value_end) == c_value_start


def test_d_value_forward():
    assert flat_to_tree.trace(d_value_start) == d_value_end


def test_d_value_backward():
    assert flat_to_tree.reverse.trace(d_value_end) == d_value_start


def test_a_wildcard_d_fixed():
    start = (
        PathsOf(Collection[Flat])
        .eg([_, "a"], PathsOf(str))
        .merge(PathsOf(Collection[Flat]).eg([_, "d"], PathsOf("4")))
    )
    end = (
        PathsOf(A)
        .eg(["a", _, "key"], PathsOf(str))
        .merge(
            PathsOf(A).eg(
                ["a", _, "value", "b", _, "value", "c", _, "value", "d", _],
                PathsOf("4"),
            )
        )
    )
    assert flat_to_tree.trace(start) == end
    assert start == flat_to_tree.reverse.trace(end)


flat_list = (
    Flat("x", "x", "x", "x"),
    Flat("y", "y", "y", "y"),
    Flat("y", "z", "z", "z"),
    Flat("y", "z", "w", "w"),
    Flat("y", "z", "w", "a"),
)

tree = A(
    {
        "x": B({"x": C({"x": D(("x",))})}),
        "y": B(
            {
                "y": C({"y": D(("y",))}),
                "z": C({"z": D(("z",)), "w": D(("w", "a"))}),
            }
        ),
    }
)


def test_flat_to_tree():
    assert flat_to_tree(flat_list) == tree
    # FIXME this would work if dict was hashable. I think now is
    #       the time to "hide" the raw PathsOf constructor and
    #       remove the prototype and instance fields, just storing
    #       explicit paths. Then it doesn't matter if the
    #       prototype value is mutable
    assert flat_to_tree.reverse(tree) == flat_list
