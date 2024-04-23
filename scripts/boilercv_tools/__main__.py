"""CLI for tools."""

import tomllib
from collections.abc import Collection
from pathlib import Path
from re import finditer
from typing import NamedTuple

from cyclopts import App

from boilercv_tools import sync
from boilercv_tools.sync import (
    COMPS,
    PYTEST,
    disable_concurrent_tests,
    escape,
    get_comp_names,
)

APP = App(help_format="markdown")
"""CLI."""


def main():  # noqa: D103
    APP()


class Comp(NamedTuple):
    """Dependency compilation."""

    low: Path
    """Path to the lowest direct dependency compilation."""
    high: Path
    """Path to the highest dependency compilation."""


@APP.command
def lock():
    """Lock dependencies."""
    log(sync.lock())


@APP.command
def compile():  # noqa: A001
    """Prepare a compilation.

    Args:
        get: Get the compilation rather than compile it.
    """
    comp_paths = Comp(*[COMPS / f"{name}.txt" for name in get_comp_names()])
    COMPS.mkdir(exist_ok=True, parents=True)
    for path, comp in zip(comp_paths, sync.compile(), strict=True):
        path.write_text(encoding="utf-8", data=comp)
    log(comp_paths)


@APP.command
def get_actions():
    """Get actions used by this repository.

    For additional security, select "Allow <user> and select non-<user>, actions and
    reusable workflows" in the General section of your Actions repository settings, and
    paste the output of this command into the "Allow specified actions and reusable
    workflows" block.

    Args:
        high: Highest dependencies.
    """
    actions: list[str] = []
    for contents in [
        path.read_text("utf-8") for path in Path(".github/workflows").iterdir()
    ]:
        actions.extend([
            f"{match['action']}@*,"
            for match in finditer(r'uses:\s?"?(?P<action>.+)@', contents)
        ])
    log(sorted(set(actions)))


@APP.command
def sync_local_dev_configs():
    """Synchronize local dev configs to shadow `pyproject.toml`, with some changes.

    Duplicate pytest configuration from `pyproject.toml` to `pytest.ini`. These files
    shadow the configuration in `pyproject.toml`, which drives CI or if shadow configs
    are not present. Shadow configs are in `.gitignore` to facilitate local-only
    shadowing. Concurrent test runs are disabled in the local pytest configuration which
    slows down the usual local, granular test workflow.
    """
    config = tomllib.loads(Path("pyproject.toml").read_text("utf-8"))
    pytest = config["tool"]["pytest"]["ini_options"]
    pytest["addopts"] = disable_concurrent_tests(pytest["addopts"])
    PYTEST.write_text(
        encoding="utf-8",
        data="\n".join(["[pytest]", *[f"{k} = {v}" for k, v in pytest.items()], ""]),
    )


def log(obj):
    """Send object to `stdout`."""
    match obj:
        case str():
            print(obj)  # noqa: T201
        case Collection():
            for o in obj:
                log(o)
        case Path():
            log(escape(obj))
        case _:
            print(obj)  # noqa: T201


if __name__ == "__main__":
    main()
