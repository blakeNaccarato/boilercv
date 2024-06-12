"""Equations."""

from inspect import Signature
from tomllib import loads

import pytest
from numpy import allclose, bool_
from sympy import lambdify

from boilercv.correlations import SYMBOLS, beta
from boilercv.correlations import beta as symbolic
from boilercv.correlations.beta import (
    EXPECTATIONS_TOML,
    SYMBOL_EXPECTATIONS,
    get_correlations,
    get_ranges,
)

lambdify  # noqa: B018

EXPECTATIONS = loads(EXPECTATIONS_TOML.read_text("utf-8"))
CORRELATIONS = get_correlations()
RANGES = get_ranges()


@pytest.mark.parametrize(("name", "expected"), EXPECTATIONS.items())
def test_python(name, expected):
    """Equations evaluate as expected."""
    equation = getattr(beta, name)
    result = equation(**{
        SYMBOLS[kwd]: value
        for kwd, value in SYMBOL_EXPECTATIONS.items()
        if SYMBOLS[kwd] in Signature.from_callable(equation).parameters
    })
    assert allclose(result, expected)


@pytest.mark.skip()
@pytest.mark.parametrize("symbol_group_name", ["SYMS", "LONG_SYMS"])
def test_syms(symbol_group_name: str):
    """Declared symbolic variables assigned to correct symbols."""
    symbols = [group_sym.name for group_sym in getattr(symbolic, symbol_group_name)]
    variables = [name for name in symbols if getattr(symbolic, name)]
    assert symbols == variables


@pytest.mark.parametrize(
    ("name", "corr", "expected"),
    (
        (name, CORRELATIONS[name], expected)  # pyright: ignore[reportArgumentType]
        for name, expected in EXPECTATIONS.items()
        if name in EXPECTATIONS
    ),
    ids=EXPECTATIONS,
)
def test_sympy(name, corr, expected):
    """Symbolic equations evaluate as expected."""
    result = corr(**{
        kwd: value
        for kwd, value in SYMBOL_EXPECTATIONS.items()
        if kwd in Signature.from_callable(corr).parameters
    })
    assert allclose(result, expected, rtol=1.0e-4)


@pytest.mark.parametrize(
    ("name", "range_", "expected"),
    (
        (name, RANGES[name], expected)  # pyright: ignore[reportArgumentType]
        for name, expected in EXPECTATIONS.items()
        if name in EXPECTATIONS
    ),
    ids=EXPECTATIONS,
)
def test_sympy_range(name, range_, expected):
    """Symbolic ranges evaluate as expected."""
    if not range_:
        return
    assert isinstance(
        range_(**{
            kwd: value
            for kwd, value in {
                "Nu_c": 1.0,
                "Ja": 1.0,
                "Re_b": 1.0,
                "Pe": 1.0,
                "Pr": 1.0,
                "alpha": 1.0,
            }.items()
            if kwd in Signature.from_callable(range_).parameters
        }),
        bool_,
    )
