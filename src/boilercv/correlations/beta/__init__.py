"""Dimensionless bubble diameter correlations for subcooled boiling bubble collapse."""

from collections.abc import Callable
from pathlib import Path
from tomllib import loads
from typing import Any, cast, get_args

import numpy
import sympy
from numpy import linspace, pi, sqrt

from boilercv.correlations import SYMBOLS
from boilercv.correlations.beta.types import SolveSym
from boilercv.correlations.models import Equations, Expectations, SolvedEquations
from boilercv.correlations.types import Eq, Equation, Sym

PNGS = Path("data/png_equations_beta")
"""Equation PNGs."""

_base = Path(__file__).with_suffix(".toml")

EQUATIONS_TOML = _base.with_stem("equations")
"""TOML file with equations."""
EXPECTATIONS_TOML = _base.with_stem("expectations")
"""TOML file with expectations."""
SOLUTIONS_TOML = _base.with_stem("solutions")
"""TOML file with solutions."""
SYMBOL_EXPECTATIONS = Expectations[Sym].context_model_validate(
    obj={
        "Nu_c": 1.0,
        "Fo_0": linspace(start=0.0, stop=5.0e-3, num=10),
        "Ja": 1.0,
        "Re_b0": 100.0,
        "Pr": 1.0,
        "beta": 0.5,
        "alpha": 1.0,
        "pi": pi,
    },
    context=Expectations[Sym].get_context(),
)
"""Common keyword arguments applied to correlations.

A single test condition has been chosen to exercise each correlation across as wide of a
range as possible without returning `np.nan` values. This is done as follows:

- Let `Re_b0`, `Pr`, and `Ja` be 100.0, 1.0, and 1.0, respectively.
- Apply the correlation {eq}`eq_beta_tang_et_al_2016` with `Fo_0` such that `beta` is
  very close to zero. This is the correlation with the most rapidly vanishing value of
  `beta`.
- Choose ten linearly-spaced points for `Fo_0` between `0` and the maximum
  `Fo_0` just found.
"""


def get_equations() -> Equations[Eq]:
    """Get equations."""
    return Equations[Eq].context_model_validate(
        obj=loads(EQUATIONS_TOML.read_text("utf-8") if EQUATIONS_TOML.exists() else ""),
        context=Equations[Eq].get_context(symbols=get_args(Sym)),
    )


def get_solutions() -> dict[Equation, sympy.Expr]:  # noqa: D103
    equations = EQUATIONS_TOML
    solutions = SOLUTIONS_TOML
    context = SolvedEquations[str].get_context(
        symbols=get_args(Sym), solve_syms=get_args(SolveSym)
    )
    return cast(
        dict[Equation, sympy.Expr],
        {
            name: soln["beta"].solutions[0]
            for name, soln in (
                SolvedEquations[SolveSym]
                .context_model_validate(
                    dict(
                        equations=loads(
                            equations.read_text("utf-8") if equations.exists() else ""
                        ),
                        solutions=loads(
                            solutions.read_text("utf-8") if solutions.exists() else ""
                        ),
                    ),
                    context=context,
                )
                .solutions
            ).items()
        },
    )


def get_correlations() -> dict[Equation, Callable[..., Any]]:
    """Get symbolic functions."""
    return {
        name: sympy.lambdify(
            expr=soln,
            modules=numpy,
            args=[s for s in soln.free_symbols if s.name in SYMBOLS],  # type: ignore
        )
        for name, soln in get_solutions().items()
    }


def florschuetz_chao_1965(bubble_fourier, bubble_jakob):
    """Florschuetz and Chao (1965) dimensionless bubble diameter {cite}`florschuetzMechanicsVaporBubble1965,tangReviewDirectContact2022`.

    Parameters
    ----------
    bubble_fourier
        Bubble Fourier number.
    bubble_jakob
        Bubble Jakob number.
    """
    return 1 - 4 * bubble_jakob * sqrt(bubble_fourier / pi)


def isenberg_sideman_1970(
    bubble_fourier, bubble_initial_reynolds, liquid_prandtl, bubble_jakob
):
    """Bubble history correlation for condensation of a stagnant bubble {cite}`tangReviewDirectContact2022`."""
    return (
        1
        - (3 / sqrt(pi))
        * bubble_initial_reynolds ** (1 / 2)
        * liquid_prandtl ** (1 / 3)
        * bubble_jakob
        * bubble_fourier
    ) ** (2 / 3)


def akiyama_1973(bubble_fourier, bubble_initial_reynolds, liquid_prandtl, bubble_jakob):
    """Bubble history correlation for condensation of a stagnant bubble {cite}`tangReviewDirectContact2022`."""
    return (
        1
        - 1.036
        * bubble_fourier
        * bubble_initial_reynolds ** (1 / 2)
        * bubble_jakob
        * liquid_prandtl ** (1 / 3)
    ) ** 0.714


def chen_mayinger_1992(
    bubble_fourier, bubble_initial_reynolds, liquid_prandtl, bubble_jakob
):
    """Bubble history correlation for condensation of a stagnant bubble {cite}`tangReviewDirectContact2022`."""
    return (
        1
        - 0.56
        * bubble_initial_reynolds**0.7
        * liquid_prandtl**0.5
        * bubble_jakob
        * bubble_fourier
    ) ** 0.9


def kalman_mori_2002(
    bubble_fourier, bubble_initial_reynolds, liquid_prandtl, bubble_jakob
):
    """Bubble history correlation for condensation of a stagnant bubble {cite}`tangReviewDirectContact2022`."""
    return (
        1
        - 0.0094
        * bubble_initial_reynolds**0.855
        * liquid_prandtl**0.855
        * bubble_jakob
        * bubble_fourier
    ) ** 0.873


def yuan_et_al_2009(
    bubble_fourier, bubble_initial_reynolds, liquid_prandtl, bubble_jakob
):
    """Bubble history correlation for condensation of a stagnant bubble {cite}`yuandewenCondensationHeatTransfer2009,tangReviewDirectContact2022`."""
    return (
        1
        - 1.8
        * bubble_initial_reynolds**0.5
        * liquid_prandtl ** (1 / 3)
        * bubble_jakob
        * bubble_fourier
        * (1 - 0.5 * bubble_jakob**0.1 * bubble_fourier)
    ) ** (2 / 3)


def lucic_mayinger_2010(
    bubble_fourier, bubble_initial_reynolds, liquid_prandtl, bubble_jakob
):
    """Bubble history correlation for condensation of a stagnant bubble {cite}`tangReviewDirectContact2022`."""
    return (
        1
        - 2.92
        * bubble_initial_reynolds**0.61
        * liquid_prandtl**0.33
        * bubble_jakob**0.69
        * bubble_fourier
    )


def kim_park_2011(
    bubble_fourier, bubble_initial_reynolds, liquid_prandtl, bubble_jakob
):
    """Bubble history correlation for condensation of a stagnant bubble {cite}`tangReviewDirectContact2022`."""
    return (
        1
        - 0.67
        * bubble_initial_reynolds**0.7
        * liquid_prandtl ** (-0.4564)
        * bubble_jakob**0.7959
        * bubble_fourier
    ) ** 0.769


# def inaba_et_al_2013(
#     bubble_fourier, bubble_initial_reynolds, liquid_prandtl, bubble_jakob
# ):
#     """Bubble history correlation for condensation of a stagnant bubble. {cite}`tangReviewDirectContact2022`."""
#     return (
#         1
#         - 1.1
#         * bubble_initial_reynolds**0.86
#         * liquid_prandtl ** (2 / 3)
#         * bubble_jakob**0.2
#         * bubble_fourier
#     )


def al_issa_et_al_2014(
    bubble_fourier, bubble_initial_reynolds, liquid_prandtl, bubble_jakob
):
    """Bubble history correlation for condensation of a stagnant bubble {cite}`tangReviewDirectContact2022`."""
    return (
        1
        - 0.135
        * bubble_initial_reynolds**0.89
        * liquid_prandtl**0.33
        * bubble_jakob
        * bubble_fourier
    ) ** 0.901


def tang_et_al_2016(
    bubble_fourier, bubble_initial_reynolds, liquid_prandtl, bubble_jakob
):
    """Bubble history correlation for condensation of a stagnant bubble {cite}`tangReviewDirectContact2022`."""
    return (
        1
        - 12.29
        * bubble_initial_reynolds**0.584
        * liquid_prandtl**0.333
        * bubble_jakob**0.581
        * bubble_fourier
    ) ** 0.706