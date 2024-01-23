"""Helper functions for tests."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from types import SimpleNamespace
from typing import Any, NamedTuple

import pytest
from _pytest.mark.structures import ParameterSet
from boilercore.notebooks.namespaces import NO_PARAMS, Params, get_nb_ns
from boilercore.paths import get_module_rel, walk_modules


def get_nb(exp: Path, name: str) -> Path:
    return exp / f"{name}.ipynb"


class NsArgs(NamedTuple):
    """Indirect parameters for notebook namespace fixture."""

    nb: Path
    params: Params = NO_PARAMS


boilercv_dir = Path("src") / "boilercv"
STAGES: list[ParameterSet] = []
for module in walk_modules(boilercv_dir):
    if module.startswith("boilercv.manual"):
        stage = get_module_rel(module, "manual")
        match stage.split("."):
            case ("update_experiments_from_docs", *_):
                marks = [pytest.mark.skip(reason="Local-only documentation.")]
            case _:
                marks = []
        STAGES.append(
            pytest.param(module, id=get_module_rel(module, "boilercv"), marks=marks)
        )
        continue
    if not module.startswith("boilercv.stages"):
        continue
    stage = get_module_rel(module, "stages")
    match stage.split("."):
        case ("experiments", "e230920_subcool", *_):
            marks = [pytest.mark.skip(reason="Test data missing.")]
        case ("generate_reports" | "generate_experiment_docs", *_):
            marks = [pytest.mark.skip(reason="Local-only documentation generation.")]
        case ("compare_theory" | "find_tracks" | "find_unobstructed", *_):
            marks = [pytest.mark.skip(reason="Implementation trivially does nothing.")]
        case _:
            marks = []
    STAGES.append(
        pytest.param(module, id=get_module_rel(module, "boilercv"), marks=marks)
    )


@dataclass
class Case:
    """Notebook test case.

    Args:
        path: Path to the notebook.
        suffix: Test ID suffix.
        params: Parameters to pass to the notebook.
        results: Variable names to retrieve and optional expectations on their values.
    """

    path: Path
    """Path to the notebook."""
    suffix: str
    """Test ID suffix."""
    params: dict[str, Any] = field(default_factory=dict)
    """Parameters to pass to the notebook."""
    results: dict[str, Any] = field(default_factory=dict)
    """Variable names to retrieve and optional expectations on their values."""

    @property
    def id(self) -> str:  # noqa: A003  # Okay to shadow in this limited context
        """Test ID."""
        return "_".join(
            [p for p in (*self.path.with_suffix("").parts, self.suffix) if p]
        )

    @property
    def nb(self) -> str:
        """Jupyter notebook contents associated with this user's attempt."""
        return self.path.read_text(encoding="utf-8") if self.path.exists() else ""

    def get_ns(self) -> SimpleNamespace:
        """Get notebook namespace for this check."""
        return get_nb_ns(nb=self.nb, params=self.params, attributes=self.results)


def normalize_cases(*cases: Case) -> Iterable[Case]:
    """Normalize cases to minimize number of caches.

    Assign the same results to cases with the same path and parameters, preserving
    expectations. Sort parameters and results.

    Args:
        *cases: Cases to normalize.

    Returns:
        Normalized cases.
    """
    seen: dict[Path, dict[str, Any]] = {}
    all_cases: list[list[Case]] = []
    # Find cases with the same path and parameters and sort parameters
    for c in cases:
        for i, (path, params) in enumerate(seen.items()):
            if c.path == path and c.params == params:
                all_cases[i].append(c)
                break
        else:
            # If the loop doesn't break, no match was found
            seen[c.path] = c.params
            all_cases.append([c])
        c.params = dict(sorted(c.params.items()))
    # Assign the same results to common casees and sort results
    for cs in all_cases:
        all_results: set[str] = set()
        all_results.update(chain.from_iterable(c.results.keys() for c in cs))
        for c in cs:
            c.results |= {r: None for r in all_results if r not in c.results}
            c.results = dict(sorted(c.results.items()))
    return cases
