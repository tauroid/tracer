from __future__ import annotations
from typing import TYPE_CHECKING


from ..cache import cache

if TYPE_CHECKING:
    from . import PathsOf

from .wildcard import is_wildcard


@property
@cache
def as_key_str[T](self: PathsOf[T]) -> str:
    return f"PathsOf[{self.type.__name__}]"


def as_indent_tree[T](self: PathsOf[T], level: int = 0) -> str:
    s = "\n"
    if self.paths:
        # origin = get_origin(self.type) or self.type
        for key, paths in self.paths.items():
            # if issubclass(origin, Mapping):
            #     # Cheesy Mapping special treatment
            #     if isinstance(key, PathsOf):
            #         key_str = key._as_key_str
            #     else:
            #         key_str = repr(key)
            #     key_str += " =>"
            #     paths = paths.get("value", PathsOf(Any, None))
            if is_wildcard(key):
                key_str = "*"
            else:
                key_str = str(key)
            s += ("  " * level) + key_str
            s += paths._as_indent_tree(level + 1)
    else:
        s += ("  " * level) + "◌" + "\n"

    return s
