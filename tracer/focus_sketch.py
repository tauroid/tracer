from datetime import datetime
from typing import Callable


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


def transform_model(model: InputModel) -> OutputModel: ...


# Narrow a tracing function by supplying sub areas of `S` and `T`
# This obviously has no guarantee `S`, `T`, `A` and `B` are related,
# but see below...
def focus[S, T, *A, B](
    f: Callable[[S], T], a: tuple[*A], b: B
) -> Callable[[*A], B]: ...


# This is a lie to the type system, it creates a special object
# we can use to implement `focus` by narrowing the tracing
#
# Accessing attributes of this special object extrudes a sort of index
# into `T`. I.e. A linear (always?) `PathsOf` from this repo
#
# Name is just riffing on "lens"
def create_aperture[T](t: type[T]) -> T: ...


input_aperture = create_aperture(InputModel)
output_aperture = create_aperture(OutputModel)

# Type of `transform_parameters` is inferred as
# (list[InputParameter], datetime) -> list[OutputParameter]
transform_parameters = focus(
    transform_model,
    (input_aperture.parameters, input_aperture.time),
    output_aperture.parameters,
)

# transform_parameters([x, y], datetime(2024, 5, 12))
# >>> [OutputParameter(...)]

# transform_parameters.reverse([z])
# >>> ([InputParameter(...), InputParameter(...)], datetime(...))
#
# How can the reverse traced time be meaningful...

# If for some reason one of the output parameters depends on e.g. the input
# model name (outside the focussed tracing area), that's a runtime error
# (or `focus` time error if possible)
