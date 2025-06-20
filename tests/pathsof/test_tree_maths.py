from frozendict import deepfreeze, frozendict

from tracer.pathsof import PathsOf
from tracer.pathsof.hole import Hole


def test_remove_lowest_level():
    paths = PathsOf(
        frozendict,
        deepfreeze({"a": {"a": {"a": {}, "b": {}}, "b": {"a": {"a": {}}}}}),
    )

    assert paths.assembled == {"a": {"a": {"a": {}, "b": {}}, "b": {"a": {"a": {}}}}}
    paths = paths.remove_lowest_level()
    assert paths and paths.assembled == {
        "a": {"a": {"a": {}, "b": {}}, "b": {"a": {Hole(): {}}}}
    }
    paths = paths.remove_lowest_level()
    assert paths and paths.assembled == {
        "a": {"a": {"a": {}, "b": {}}, "b": {"a": {Hole(): Hole()}}}
    }
    paths = paths.remove_lowest_level()
    assert paths and paths.assembled == {"a": {"a": {Hole(): {}}, "b": {Hole(): {}}}}
    paths = paths.remove_lowest_level()
    assert paths and paths.assembled == {
        "a": {"a": {Hole(): Hole()}, "b": {Hole(): Hole()}}
    }
    paths = paths.remove_lowest_level()
    assert paths and paths.assembled == {"a": {Hole(): {}}}
    paths = paths.remove_lowest_level()
    assert paths and paths.assembled == {"a": {Hole(): Hole()}}
    paths = paths.remove_lowest_level()
    assert paths and paths.assembled == {Hole(): {}}
    paths = paths.remove_lowest_level()
    assert paths and paths.assembled == {Hole(): Hole()}
    paths = paths.remove_lowest_level()
    assert paths is not None and paths.assembled == {}
    paths = paths.remove_lowest_level_or_none()
    assert paths is None
