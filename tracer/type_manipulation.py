import sys
from typing import Any, Collection, get_args, get_origin


def annotation_type(t: type[Any] | str, *, ctx_class: type[Any] | None) -> type[Any]:
    if isinstance(t, str):
        if origin := get_origin(ctx_class):
            type_subs = {
                # This feels a mite precarious
                str(v): t
                for v, t in zip(origin.__type_params__, get_args(ctx_class))
            }
        else:
            type_subs = {}
        return eval(t, {**type_subs, **vars(sys.modules[ctx_class.__module__])})
    else:
        return t


def instance_union_member(inst: Any, union: Collection[type[Any]]) -> type[Any]:
    matches: list[type[Any]] = []
    for t in union:
        base_t = t
        if origin := get_origin(t):
            base_t = origin
        if isinstance(inst, base_t):
            matches.append(t)

    match matches:
        case (t,):
            return t
        case ():
            raise Exception(f"No union members found matching {inst}")
        case ts:
            raise Exception(f"Multiple union members found matching {inst}: {ts}")
