from __future__ import annotations
from dataclasses import dataclass
from typing import Collection, Mapping

from tracer.pathsof.hole import Hole
from tracer.tracer import disjunction, link
from tracer.pathsof import PathsOf


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

a_start = PathsOf(Collection[Flat]).eg({Hole(): a_pointer})
a_end = PathsOf(A).eg(["a", Hole(), "key"], PathsOf(str))

b_start = PathsOf(Collection[Flat]).eg({Hole(): b_pointer})
b_end = PathsOf(A).eg(["a", Hole(), "value", "b", Hole(), "key"], PathsOf(str))

c_start = PathsOf(Collection[Flat]).eg({Hole(): c_pointer})
c_end = PathsOf(A).eg(
    ["a", Hole(), "value", "b", Hole(), "value", "c", Hole(), "key"],
    PathsOf(str),
)

d_start = PathsOf(Collection[Flat]).eg({Hole(): d_pointer})
d_end = PathsOf(A).eg(
    [
        "a",
        Hole(),
        "value",
        "b",
        Hole(),
        "value",
        "c",
        Hole(),
        "value",
        "d",
    ],
    PathsOf(str),
)

flat_to_tree = disjunction(
    Collection[Flat],
    A,
    (
        link(Collection[Flat], A, a_start, a_end),
        link(Collection[Flat], A, b_start, b_end),
        link(Collection[Flat], A, c_start, c_end),
        link(Collection[Flat], A, d_start, d_end),
    ),
)

a_value_start = PathsOf(Collection[Flat]).eg([Hole(), "a"], PathsOf("1"))
a_value_end = PathsOf(A).eg(["a", Hole(), "key"], PathsOf("1"))


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
