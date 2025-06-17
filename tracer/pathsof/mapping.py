from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class MappingItem[K, V]:
    """
    Mappings are weird. We probably want to PathsOf(Mapping)[key] because that's
    natural. But we also want to trace keys. So we have to be able to point to them.

    Hence this class. The `paths` of a PathsOf(Mapping[K,V]) will look like
    ```
    {
        "key_1": PathsOf(MappingItem[K,V]).eg({
            "key": PathsOf("key_1"),
            "value": PathsOf(value)
        }),
        # Below is also valid, but would have to be constructed via `explicit_paths`
        # This is so that keys can have wildcards
        PathsOf(OtherKeyType).eg({"field": PathsOf(Field)}): PathsOf(MappingItem[K,V]).eg({
            "key": PathsOf(OtherKeyType).eg({"field": PathsOf(Field)}),
            "value": PathsOf(value)
        })
        ...
    }
    ```

    Best of both worlds, at the cost of making accessing values a bit more awkward.
    """

    key: K
    value: V
