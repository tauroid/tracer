from functools import wraps
from typing import (
    Any,
    Callable,
    MutableMapping,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)


F = TypeVar("F", bound=Callable[..., Any])


@overload
def cache(
    fn: None = None, *, cache_obj: Optional[MutableMapping[str, Any]] = None
) -> Callable[[F], F]: ...


@overload
def cache(
    fn: F, *, cache_obj: Optional[MutableMapping[str, Any]] = None
) -> F: ...


def cache(
    fn: Optional[F] = None,
    *,
    cache_obj: Optional[MutableMapping[str, Any]] = None,
) -> Union[Callable[[F], F], F]:
    """
    Really basic unlimited cache (i.e. it's a dict), only use for fixed small
    known input set

    Using this instead of functools because functools has some sort of type
    weirdness when used with properties (IIRC)
    """

    _cache_obj: MutableMapping[str, Any] = (
        {} if cache_obj is None else cache_obj
    )

    def accepts_fn(fn: F) -> F:
        @wraps(fn)
        def cached(*args: Any, **kwargs: Any) -> Any:
            key = str(hash((args, tuple((k, v) for k, v in kwargs.items()))))
            if key not in _cache_obj:
                _cache_obj[key] = fn(*args, **kwargs)

            return _cache_obj[key]

        return cast(F, cached)

    if fn:
        return accepts_fn(fn)
    else:
        return accepts_fn
