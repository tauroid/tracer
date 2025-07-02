from dataclasses import dataclass
from itertools import product

from tracer.pathsof import PathsOf
from tracer.tracer import conjunction, copy, disjunction, link


@dataclass(frozen=True)
class XorArgs:
    a: bool
    b: bool


xor = disjunction(
    link(
        PathsOf(XorArgs).eg({"a": PathsOf.a(False), "b": PathsOf.a(False)}),
        PathsOf.a(False),
    ),
    link(
        PathsOf(XorArgs).eg({"a": PathsOf.a(False), "b": PathsOf.a(True)}),
        PathsOf.a(True),
    ),
    link(
        PathsOf(XorArgs).eg({"a": PathsOf.a(True), "b": PathsOf.a(False)}),
        PathsOf.a(True),
    ),
    link(
        PathsOf(XorArgs).eg({"a": PathsOf.a(True), "b": PathsOf.a(True)}),
        PathsOf.a(False),
    ),
)


def test_xor():
    for a, b in product(*([[False, True]] * 2)):
        assert xor(XorArgs(a, b)) == a ^ b


@dataclass(frozen=True)
class SwapArgs:
    swap: bool
    a: str
    b: str


sa = PathsOf(SwapArgs)

# This is probably messily specified. Or what happens to the "swap"
# field is overspecified
swap = disjunction(
    copy(sa.eg(["swap"]), sa.eg(["swap"])),
    conjunction(
        link(sa.eg(["swap"], PathsOf.a(True)), sa.eg(["swap"], PathsOf.a(True))),
        copy(sa.eg(["a"]), sa.eg(["b"])),
    ),
    conjunction(
        link(sa.eg(["swap"], PathsOf.a(True)), sa.eg(["swap"], PathsOf.a(True))),
        copy(sa.eg(["b"]), sa.eg(["a"])),
    ),
    conjunction(
        link(sa.eg(["swap"], PathsOf.a(False)), sa.eg(["swap"], PathsOf.a(False))),
        copy(sa.eg(["a"]), sa.eg(["a"])),
    ),
    conjunction(
        link(sa.eg(["swap"], PathsOf.a(False)), sa.eg(["swap"], PathsOf.a(False))),
        copy(sa.eg(["b"]), sa.eg(["b"])),
    ),
)


def test_swap():
    assert swap(SwapArgs(True, "goat", "jaguar")) == SwapArgs(True, "jaguar", "goat")
    assert swap(SwapArgs(False, "goat", "jaguar")) == SwapArgs(False, "goat", "jaguar")


def test_no_partial_mapping():
    assert swap.trace(PathsOf(SwapArgs).eg(["b"])) == PathsOf(SwapArgs)
