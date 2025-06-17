from frozendict import deepfreeze, frozendict
from tracer.pathsof import PathsOf


def test_remove_lowest_level():
    paths = PathsOf(
        frozendict,
        deepfreeze({"a": {"a": {"a": {}, "b": {}}, "b": {"a": {"a": {}}}}}),
    )

    paths = paths.remove_lowest_level().remove_lowest_level()
    assert paths and paths.assembled == {"a": {"a": {"a": {}, "b": {}}, "b": {"a": {}}}}
    paths = paths.remove_lowest_level().remove_lowest_level()
    assert paths and paths.assembled == {"a": {"a": {}, "b": {}}}
    paths = paths.remove_lowest_level().remove_lowest_level()
    assert paths and paths.assembled == {"a": {}}
    paths = paths.remove_lowest_level().remove_lowest_level()
    assert paths is not None and paths.assembled == {}
    assert paths.remove_lowest_level_or_none() is None
