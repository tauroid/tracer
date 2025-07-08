from tracer import conjunction, link, opaque, PathsOf, _
from tracer.pathsof.mapping import mapping_path

int_to_str = opaque(forward=str, backward=int)


def test_int_to_str():
    assert int_to_str(8) == "8"
    assert 12345 == int_to_str.reverse("12345")


A = dict[str, dict[int, dict[str, int]]]
B = dict[int, dict[str, dict[int, str]]]

deep_int_to_str = conjunction(
    link(
        mapping_path(A, ["1", 2, "3"]),
        mapping_path(B, [1, "2", 3]),
    ),
    # Link above to localise, link below to do it
    # This is only required because it's Mappings (dicts);
    # the keys are on different branches to the data and we
    # don't want to map the unit types below the keys
    link(
        PathsOf(A).eg([_, "value", _, "value", _, "value"]),
        PathsOf(B).eg([_, "value", _, "value", _, "value"]),
        leaf_mapping=int_to_str,
    ),
    # I think this is because of the child opaque tracer
    # This could be a problem because the incompleteness
    # necessarily spreads
    #
    # Probably need to just phase out the coherence check
    # eventually in favour of structurally guaranteed coherence
    # (no free form non-opaque tracers)
    fully_specified=False,
)


def test_deep_int_to_str():
    assert deep_int_to_str({"1": {2: {"3": 4}}}) == {1: {"2": {3: "4"}}}
    assert {"1": {2: {"3": 4}}} == deep_int_to_str.reverse({1: {"2": {3: "4"}}})
