"""Generated equations."""

from collections.abc import Sequence
from pathlib import Path
from tomllib import loads

from numpy import linspace

from boilercv_pipeline.equations import (
    Defaults,
    Equation,
    KindModel,
    Param,
    Replacements,
)

EQUATIONS_TOML = Path(__file__).with_suffix(".toml")
"""TOML file with equations."""
EXPECTED_TOML = Path(__file__).with_name("expectations.toml")
"""TOML file with equations."""


def make_param(name: str, param: Param) -> Param:
    p = Param
    return param.apply(Defaults(src=p, dst=p, name=name)).apply(
        Replacements(
            src=p,
            dst=p,
            repls={
                ("latex", k): ("sympy", v)
                for k, v in {r"_\b0": "_bo", r"_\o": "_0", "\\": ""}.items()
            },
        )
    )


args = {
    name: make_param(name, param)
    for name, param in {
        "bubble_initial_reynolds": Param({"latex": r"\Re_\bo"}),
        "bubble_jakob": Param({"latex": r"\Ja"}),
        "bubble_fourier": Param({"latex": r"\Fo_\o"}),
    }.items()
}


params = {
    name: make_param(name, param)
    for name, param in {n: Param({"latex": f"\\{n}"}) for n in ["beta", "pi"]}.items()
}

# args = (
#     _Param(
#         name="bubble_initial_reynolds", forms=KindModel(latex=r"\Re_\bo"), test=100.0
#     ),
#     _Param(name="bubble_jakob", forms=KindModel(latex=r"\Ja"), test=1.0),
#     _Param(
#         name="bubble_fourier",
#         forms=KindModel(latex=r"\Fo_\o"),
#         test=linspace(start=0.0, stop=5.0e-3, num=10),
#     ),
#     _Param(name="liquid_prandtl", forms=KindModel(latex=r"\Pr"), test=1.0),
# )


equations = [
    Equation(
        name=eq["name"],
        forms=KindModel(latex=eq["latex"], sympy=eq["sympy"], python=eq["python"]),
        transforms=[
            Replacements(src=kind, dst=kind, repls={"\n": "", "    ": ""})  # pyright: ignore[reportArgumentType]  1.1.360, pydantic 2.4.2
            for kind in ["latex", "sympy", "python"]
        ],
    )
    for eq in loads(EQUATIONS_TOML.read_text("utf-8"))["equation"]
]

MAKE_RAW = {r"\\": "\\"}
"""Replacement to turn escaped characters in strings back to their raw form."""
SYMPY_REPL = {"{o}": "0", "{bo}": "b0"} | MAKE_RAW
"""Replacements after parsing LaTeX to SymPy."""
LATEX_REPL = {"{0}": r"\o", "{b0}": r"\b0"} | MAKE_RAW
"""Replacements to make after parsing LaTeX from PNGs."""


class _Param(Param):
    transforms: Sequence[Replacements] = (
        Replacements(
            src="latex", dst="sympy", repls={r"_\b0": "_bo", r"_\o": "_0", "\\": ""}
        ),
    )


params = (
    _Param(
        name="dimensionless_bubble_diameter",
        forms=KindModel(latex=r"\beta", sympy="beta"),
        test=1.0,
    ),
    _Param(name="pi"),
)

SUBS = {arg.forms.sympy: arg.name for arg in (*args, *params)}
"""Substitutions from SymPy symbolic variables to descriptive names."""
KWDS = {arg.name: arg.test for arg in args}
"""Common keyword arguments applied to correlations.

A single test condition has been chosen to exercise each correlation across as wide of a
range as possible without returning `np.nan` values. This is done as follows:

- Let `bubble_initial_reynolds`,
`liquid_prandtl`, and `bubble_jakob` be 100.0, 1.0, and 1.0, respectively.
- Apply the correlation `dimensionless_bubble_diameter_tang_et_al_2016` with
`bubble_fourier` such that the `dimensionless_bubble_diameter` is very close to zero.
This is the correlation with the most rapidly vanishing value of
`dimensionless_bubble_diameter`.
- Choose ten linearly-spaced points for `bubble_fourier` between `0` and the maximum
`bubble_fourier` just found.
"""

EXPECTED = {
    expectation.name: expectation.expect
    for expectation in [
        Expectation(
            name=name, test=linspace(start=0.0, stop=5.0e-3, num=10), expect=expect
        )
        for name, expect in loads(EXPECTED_TOML.read_text("utf-8")).items()
    ]
}
"""Expected results for the response of each correlation to `KWDS`."""
