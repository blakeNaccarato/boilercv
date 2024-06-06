"""Static type annotations used in {mod}`boilercv_pipeline`."""

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from functools import wraps
from pathlib import Path
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Literal,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypeVar,
    _LiteralGenericAlias,  # pyright: ignore[reportAttributeAccessIssue]
    overload,
)

import sympy
from numpydantic import NDArray, Shape
from pydantic import (
    AfterValidator,
    BeforeValidator,
    PlainValidator,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    WrapSerializer,
    WrapValidator,
)
from sympy import sympify
from sympy.logic.boolalg import BooleanAtom

from boilercv.morphs.contexts import ContextValue

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

# ? Notebook handling
NbProcess: TypeAlias = Callable[[Path, SimpleNamespace], None]
"""Notebook process."""
Stage: TypeAlias = Literal["large_sources", "sources", "filled"]
"""Stage."""

# ? `numpy` array shapes
AnyShape: TypeAlias = Shape["*"]  # noqa: F722
"""Any shape."""
Vector: TypeAlias = Shape["*"]  # noqa: F722
"""Vector shape."""

# ? Equations
Expectation: TypeAlias = float | NDArray[Vector, float]  # pyright: ignore[reportInvalidTypeArguments]
"""Expectation."""


P = TypeVar("P", contravariant=True)
"""Contravariant type to represent parameters."""
R = TypeVar("R", covariant=True)
"""Covariant type to represent returns."""
Ps = ParamSpec("Ps")
"""Parameter type specification."""
K = TypeVar("K")
"""Key type."""
V = TypeVar("V")
"""Value type."""
CV = TypeVar("CV", bound=ContextValue, contravariant=True)
"""Context value type."""
CVL = TypeVar("CVL", bound="DataclassInstance | Mapping[Any, Any]", contravariant=True)
"""Context value-like type."""


class Transform(Protocol[P, Ps, R]):  # noqa: D101
    def __call__(self, i: P, /, *args: Ps.args, **kwds: Ps.kwargs) -> R: ...  # noqa: D102


def StrSerializer(  # noqa: N802; Can't inherit from frozen
    when_used: Literal["always", "unless-none", "json", "json-unless-none"] = "always",
) -> WrapSerializer:
    """Serialize as string."""
    return WrapSerializer(_str, when_used=when_used)


def _str(v: Any, nxt: SerializerFunctionWrapHandler):
    """Stringify or try next serializer."""
    try:
        return str(v)
    except ValueError:
        return nxt(v)


@overload
def TypeValidator(typ: type[K], mode: Literal["before"]) -> BeforeValidator: ...
@overload
def TypeValidator(typ: type[K], mode: Literal["wrap"]) -> WrapValidator: ...
@overload
def TypeValidator(typ: type[K], mode: Literal["after"]) -> AfterValidator: ...
@overload
def TypeValidator(typ: type[K], mode: Literal["plain"]) -> PlainValidator: ...
@overload
def TypeValidator(typ: type[K]) -> PlainValidator: ...


# * MARK: `TypeVar`s and `TypeAlias`es for annotations


Validator: TypeAlias = Literal["before", "wrap", "after", "plain"]
"""Validators."""


VALIDATORS: dict[Validator, Any] = {
    "before": BeforeValidator,
    "wrap": WrapValidator,
    "after": AfterValidator,
    "plain": PlainValidator,
}
"""Validators."""


def TypeValidator(typ: type[K], mode: Validator = "plain") -> Any:  # noqa: N802; Can't inherit from frozen
    """Validate type."""

    def validate(v: K) -> K:
        if isinstance(v, typ):
            return v
        raise ValueError(f"Input should be a valid {typ}")

    return VALIDATORS[mode](validate)


LiteralKeys: TypeAlias = _LiteralGenericAlias
"""Keys."""


# * MARK: Annotation parts


def contextualized(context_value_type: type[CVL]):
    """Contextualize function on `context_value_type`."""

    def contextualizer(f: Transform[P, Ps, R]) -> Callable[[P, CVL], R]:
        @wraps(f)
        def unpack_kwds(v: P, context_value: CVL) -> R:
            if not isinstance(context_value, context_value_type):
                raise ValueError(  # noqa: TRY004 so Pydantic catches it
                    f"Expected context value type '{context_value_type}', got '{type(context_value)}."
                )
            context_mapping = (
                context_value
                if isinstance(context_value, Mapping)
                else asdict(context_value)
            )
            return f(v, **context_mapping)  # pyright: ignore[reportCallIssue]

        return unpack_kwds

    return contextualizer


def validator(context_value_type: type[CV]):
    """Transform function expecting `context_value_type` to a Pydantic validator form.

    Get {class}`~boilercv.morphs.types.runtime.ContextValue` of `context_value_type` from `ValidationInfo` and pass to function expecting `context_value_type`.
    """

    def validator_maker(f: Callable[[P, CV], R]) -> Callable[[P, ValidationInfo], R]:
        def validate(v: P, info: ValidationInfo, /) -> R:
            key = context_value_type.name_to_snake()
            context = info.context or {}
            if not context:
                raise ValueError(
                    f"No context given. Expected value at '{key}' of type '{context_value_type}'."
                )
            context_value = context.get(key)
            if not context_value:
                raise ValueError(
                    f"No context value at {key}. Expected context value at '{key}' of type '{context_value_type}'."
                )
            if not isinstance(context_value, context_value_type):
                raise ValueError(  # noqa: TRY004 so Pydantic catches it
                    f"Context value at {key} not of expected type '{context_value_type}'."
                )
            return f(v, context_value)

        return validate

    return validator_maker


@dataclass
class SympifyParams(ContextValue):
    """Sympify parameters."""

    locals: dict[str, Any] | None = None
    convert_xor: bool | None = None
    strict: bool = False
    rational: bool = False
    evaluate: bool | None = None


def sympify_expr(expr: str | sympy.Eq, sympify_params: SympifyParams):
    """Sympify an expression from local variables."""
    return sympify(expr, **asdict(sympify_params))


trivial = sympy.Eq(1, 0, evaluate=False)
"""Trivial equation that won't evaluate to a `True` instance of `sympy.boolean.linalg.BooleanAtom`."""

Basic: TypeAlias = Annotated[
    sympy.Basic, TypeValidator(sympy.Basic), StrSerializer("json")
]
"""Annotated {class}`~sympy.core.basic.Basic` suitable for use in Pydantic models."""


Eq: TypeAlias = Annotated[
    Basic,
    BeforeValidator(validator(SympifyParams)(sympify_expr)),
    BeforeValidator(lambda v: v or trivial),
    TypeValidator(sympy.Eq, "after"),
    # ? SymPy equations sometimes evaluate to `bool` on copy
    WrapSerializer(
        lambda v, nxt: "" if isinstance(v, BooleanAtom) or v == trivial else nxt(v),
        when_used="json",
    ),
]
"""{data}`~boilercv_pipeline.types.Basic` narrowed to {class}`~sympy.core.relational.Eq`."""
# * MARK: Annotations


Expr = Annotated[
    Basic,
    BeforeValidator(validator(SympifyParams)(sympify_expr)),
    TypeValidator(sympy.Expr, "after"),
]
"""{data}`~boilercv_pipeline.types.Basic` narrowed to {class}`~sympy.core.relational.Eq`."""
