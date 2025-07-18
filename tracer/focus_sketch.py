from datetime import datetime
from typing import Callable, cast

from .tracer import Tracer


class InputParameter: ...


class InputModel:
    # Things we don't care about mapping right now
    name: str
    version: int
    organisation: str

    # Things we do care about mapping right now
    parameters: list[InputParameter]
    time: datetime


class OutputParameter: ...


class OutputModel:
    # Things we don't care about mapping right now
    name: str
    source_model: InputModel
    processing_description: str

    # Things we do care about mapping right now
    parameters: list[OutputParameter]


transform_model = cast(Tracer[InputModel, OutputModel], ...)


# Narrow a tracing function by supplying sub areas of `S` and `T`
# This unfortunately has no guarantee `A` and `B` live within `S` and `T`
#
# The trick is that `a` and `b` will be called with something like
# a mock object, which records (nested) accessed attributes
#
# Then `focus` can narrow down just to those
#
# If the tracing goes outside the focussed area, that's a runtime error
# (or `focus` time error if possible)
def focus[S, T, A, B](
    f: Tracer[S, T], a: Callable[[S], A], b: Callable[[T], B]
) -> Tracer[A, B]: ...


# Type of `transform_parameters` is inferred as
# Tracer[tuple[list[InputParameter], datetime], list[OutputParameter]]
transform_parameters = focus(
    transform_model,
    lambda input_model: (input_model.parameters, input_model.time),
    lambda output_model: output_model.parameters,
)

# transform_parameters(([x, y], datetime(2024, 5, 12)))
# >>> [OutputParameter(...)]

# transform_parameters.reverse([z])
# >>> ([InputParameter(...), InputParameter(...)], datetime(...))
#
# (How can the reverse traced `time` be meaningful...)
