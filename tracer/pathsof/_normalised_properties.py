from __future__ import annotations
from typing import TYPE_CHECKING, get_origin
from ..cache import cache

from .hole import Hole

if TYPE_CHECKING:
    from . import PathsOf


@cache
def _type_and_instance[T](self: PathsOf[T]) -> tuple[type[T], T | None]:
    if isinstance(self.prototype, type) or get_origin(self.prototype):
        return self.prototype, (
            None if isinstance(self.explicit_instance, Hole) else self.explicit_instance
        )
    elif self.explicit_instance is None:
        return type(self.prototype), self.prototype
    else:
        raise Exception("If `instance` is not `None`, `prototype` must be a type")


@property
def type_[T](self: PathsOf[T]) -> type[T]:
    type_, _ = _type_and_instance(self)
    return type_


@property
def instance[T](self: PathsOf[T]) -> T | None:
    _, instance = _type_and_instance(self)
    return instance
