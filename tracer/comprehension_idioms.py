import sys
from typing import Any

if sys.version_info >= (3, 13):
    from typing import TypeIs
else:
    from typing_extensions import TypeIs


def assert_same[T](a: T, b: T) -> bool:
    assert a == b
    return True


def assert_isinstance[T](x: Any, t: type[T], yes: bool = True) -> TypeIs[T]:
    if yes:
        assert isinstance(x, t)
    else:
        assert not isinstance(x, t)
    return yes
