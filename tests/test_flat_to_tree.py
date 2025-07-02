from __future__ import annotations
from dataclasses import dataclass
from typing import Collection, Mapping

from tracer.tracer import copy, disjunction
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


a_pointer = PathsOf(Flat).eg(["a"])
b_pointer = PathsOf(Flat).eg(["b"])
c_pointer = PathsOf(Flat).eg(["c"])
d_pointer = PathsOf(Flat).eg(["d"])

a_start = PathsOf(Collection[Flat]).eg({_: a_pointer})
a_end = PathsOf(A).eg(["a", _, "key"])

b_start = PathsOf(Collection[Flat]).eg({_: b_pointer})
b_end = PathsOf(A).eg(["a", _, "value", "b", _, "key"])

c_start = PathsOf(Collection[Flat]).eg({_: c_pointer})
c_end = PathsOf(A).eg(["a", _, "value", "b", _, "value", "c", _, "key"])

d_start = PathsOf(Collection[Flat]).eg({_: d_pointer})
d_end = PathsOf(A).eg(["a", _, "value", "b", _, "value", "c", _, "value", "d", _])

flat_to_tree = disjunction(
    copy(a_start, a_end),
    copy(b_start, b_end),
    copy(c_start, c_end),
    copy(d_start, d_end),
)


def test_a_forward():
    assert flat_to_tree.trace(a_start) == a_end


def test_a_backward():
    assert flat_to_tree.reverse.trace(a_end) == a_start


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


a_value_start = PathsOf(Collection[Flat]).eg([_, "a"], PathsOf.a("1"))
a_value_end = PathsOf(A).eg(["a", _, "key"], PathsOf.a("1"))
b_value_start = PathsOf(Collection[Flat]).eg([_, "b"], PathsOf.a("2"))
b_value_end = PathsOf(A).eg(["a", _, "value", "b", _, "key"], PathsOf.a("2"))
c_value_start = PathsOf(Collection[Flat]).eg([_, "c"], PathsOf.a("3"))
c_value_end = PathsOf(A).eg(
    ["a", _, "value", "b", _, "value", "c", _, "key"], PathsOf.a("3")
)
d_value_start = PathsOf(Collection[Flat]).eg([_, "d"], PathsOf.a("4"))
d_value_end = PathsOf(A).eg(
    ["a", _, "value", "b", _, "value", "c", _, "value", "d", _], PathsOf.a("4")
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
        .eg([_, "a"])
        .merge(PathsOf(Collection[Flat]).eg([_, "d"], PathsOf.a("4")))
    )
    end = (
        PathsOf(A)
        .eg(["a", _, "key"])
        .merge(
            PathsOf(A).eg(
                ["a", _, "value", "b", _, "value", "c", _, "value", "d", _],
                PathsOf.a("4"),
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
    assert flat_to_tree.reverse(tree) == flat_list
