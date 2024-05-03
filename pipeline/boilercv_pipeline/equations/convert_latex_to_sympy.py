"""Convert LaTeX equations to SymPy equations."""

from collections.abc import Mapping
from pathlib import Path
from shlex import quote, split
from subprocess import run

from cyclopts import App
from loguru import logger
from tqdm import tqdm

from boilercv_pipeline.correlations.dimensionless_bubble_diameter.generated import (
    SYMPY_REPL,
    equations,
)
from boilercv_pipeline.equations import LATEX_PARSER, PIPX

APP = App()


def main():  # noqa: D103
    APP()


@APP.default
def default(module: Path):  # noqa: D103
    contents = module.read_text(encoding="utf-8")
    for expression in tqdm(equations.values()):
        latex = expression.forms.latex
        if not latex:
            continue
        latex = quote(latex.strip().replace("\n", "").replace("    ", ""))
        if expression.forms.sympy:
            continue
        symbolic = convert(latex, SYMPY_REPL)
        contents = update(contents, expression.name, symbolic)
    contents = module.write_text(encoding="utf-8", data=contents)


#     toml[EQS][i][SYMPY] = convert_latex_to_sympy(latex)  # pyright: ignore[reportArgumentType, reportIndexIssue]  1.1.356, tomlkit 0.12.4
# data = dumps(toml)
# for old, new in TOML_REPL.items():
#     data = data.replace(old, new)
# TOML.write_text(encoding="utf-8", data=data)


def convert(latex: str, repl: Mapping[str, str]) -> str:
    """Convert LaTeX equation to SymPy equation."""
    result = run(
        args=split(f"{PIPX} run {LATEX_PARSER} {latex}"),
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)
    eq = result.stdout.strip()
    for old, new in repl.items():
        eq = eq.replace(old, new)
    return eq


def update(contents: str, _name: str, _eq: str) -> str:
    """Update equations module with new SymPy equation."""
    return contents


if __name__ == "__main__":
    logger.info("Start converting LaTeX expressions to SymPy expressions.")
    main()
    logger.info("Finish converting LaTeX expressions to SymPy expressions.")