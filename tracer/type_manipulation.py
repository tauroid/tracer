from typing import Any, Collection, get_origin


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
