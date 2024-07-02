"""Test configuration."""

import pickle
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from logging import warning
from os import environ, getpid
from pathlib import Path
from re import fullmatch
from shutil import rmtree
from types import SimpleNamespace

import pytest
import pytest_harvest
from _pytest.python import Function
from boilercore import WarningFilter, filter_certain_warnings
from boilercore.notebooks.namespaces import get_nb_ns, get_ns_attrs
from boilercore.testing import get_session_path
from matplotlib.axis import Axis
from matplotlib.figure import Figure

import boilercv
from boilercv_tests import Case, get_cached_nb_ns, normalize_cases
from boilercv_tests.types import FixtureStore

CASER = "C"
"""Module-level variable in test modules containing notebook cases for that module."""

# * -------------------------------------------------------------------------------- * #
# * Autouse


@pytest.fixture(autouse=True, scope="session")
def _project_session_path(tmp_path_factory):
    """Set project directory."""
    get_session_path(tmp_path_factory, boilercv)


@pytest.fixture(autouse=True, scope="session")
def _filter_certain_warnings():
    """Filter certain warnings."""
    filter_certain_warnings(
        package="boilercv",
        other_warnings=[
            WarningFilter(
                category=RuntimeWarning, message="numpy.ndarray size changed"
            ),
            *[
                WarningFilter(
                    message="invalid escape sequence",
                    category=category,
                    module="colorspacious.comparison",
                )
                for category in [DeprecationWarning, SyntaxWarning]
            ],
        ],
    )


# * -------------------------------------------------------------------------------- * #
# * Notebook namespaces


@pytest.fixture(scope="module", autouse=True)
def _get_ns_attrs(request):
    module = request.module
    caser = getattr(module, CASER, None)
    if not caser:
        yield
        return
    cases = caser.cases
    notebook_namespace_tests = (
        node
        for node in request.node.collect()
        if isinstance(node, Function) and "ns" in node.fixturenames
    )
    for case, test in zip(cases, notebook_namespace_tests, strict=True):
        name = getattr(module, test.originalname)
        case.results |= dict.fromkeys(get_ns_attrs(name))
    normalize_cases(*cases)
    yield
    for nb in [c.clean_path for c in cases if c.clean_path]:
        nb.unlink(missing_ok=True)


@pytest.fixture()
@pytest_harvest.saved_fixture
def ns(request, fixture_stores) -> Iterator[SimpleNamespace]:
    """Namespace."""
    case: Case = request.param
    if environ.get("CI"):
        yield get_nb_ns(nb=case.nb, params=case.params, attributes=case.results.keys())
        return
    yield get_cached_nb_ns(
        nb=case.clean_nb(), params=case.params, attributes=case.results.keys()
    )
    update_fixture_stores(
        fixture_stores,
        request.fixturename,
        test=request.node.name,
        path=request.node.path,
    )


# * -------------------------------------------------------------------------------- * #
# * Harvest


@dataclass
class FixtureStores:
    """Fixture stores from `pytest-harvest`."""

    flat: FixtureStore
    """The default flat fixture store from `pytest-harvest`."""
    nested: FixtureStore
    """Fixture for test cases, nested by fixture name, module, then node."""


def update_fixture_stores(
    fixture_stores: FixtureStores, fixturename: str, test: str, path: Path
):
    """Update nested fixture store with the new namespace."""
    module = fixture_stores.nested[fixturename][
        path.relative_to(Path("tests/boilercv_tests").resolve())
        .with_suffix("")
        .as_posix()
    ]
    # Pattern for e.g. `test[case]`
    if match := fullmatch(pattern=r"(?P<node>[^\[]+)\[(?P<case>[^\]]+)\]", string=test):
        node, case = match.groups()
        key = f"{path.relative_to(Path.cwd()).as_posix()}::{test}"
        module[node][case] = fixture_stores.flat[fixturename][key]


@pytest.fixture(scope="session")
def fixtures(nested_fixture_store) -> SimpleNamespace:
    """Fixtures from `pytest-harvest`."""
    return SimpleNamespace(**{
        key: SimpleNamespace(**{
            key: SimpleNamespace(**{
                key: SimpleNamespace(**value) for key, value in value.items()
            })
            for key, value in value.items()
        })
        for key, value in nested_fixture_store.items()
    })


@pytest.fixture(scope="session")
def nested_fixture_store(fixture_stores) -> FixtureStore:
    """Nested fixture store."""
    return fixture_stores.nested


@pytest.fixture(scope="session")
def fixture_stores(fixture_store) -> FixtureStores:
    """Flat fixture store from `pytest-harvest` and nested fixture store."""
    return FixtureStores(
        flat=fixture_store,
        nested=defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        ),
    )


# * -------------------------------------------------------------------------------- * #
# * Plotting


@pytest.fixture()
def figs(request, pytestconfig) -> Iterator[list[Figure]]:
    """Append to this list of Matplotlib figures to save them after the test run."""
    plots = Path(pytestconfig.option.plots)
    plots.mkdir(exist_ok=True)
    path = plots / f"{request.node.nodeid.replace('/', '.').replace(':', '-')}.png"
    figs = []
    yield figs
    path.unlink(missing_ok=True)
    figs = iter(figs)
    if first_fig := next(figs, None):
        first_fig.savefig(path)
    for i, fig in enumerate(figs):
        path = path.with_stem(f"{path.stem}_{i}")
        path.unlink(missing_ok=True)
        fig.savefig(path)


@pytest.fixture()
def plt(plt):
    """Plot."""
    yield plt
    plt.saveas = f"{plt.saveas[:-4]}.png"


@pytest.fixture()
def fig_ax(plt) -> tuple[Figure, Axis]:
    """Plot figure and axis."""
    fig, ax = plt.subplots()
    return fig, ax


@pytest.fixture()
def fig(fig_ax) -> Figure:
    """Plot figure."""
    return fig_ax[0]


@pytest.fixture()
def ax(fig_ax) -> Axis:
    """Plot axis."""
    return fig_ax[1]


# * -------------------------------------------------------------------------------- * #
# * Harvest hooks
# *   https://github.com/smarie/python-pytest-harvest/issues/46#issuecomment-742367746
# *   https://smarie.github.io/python-pytest-harvest/#pytest-x-dist

HARVEST_ROOT = Path(".xdist_harvested")
"""Root directory for harvested results."""
RESULTS_PATH = HARVEST_ROOT / str(getpid())
"""Path to harvested results for a given `pytest-xdist` subprocess."""

HARVEST_ROOT.mkdir(exist_ok=True)
RESULTS_PATH.mkdir(exist_ok=True)


def pytest_harvest_xdist_init():
    """Reset the recipient folder."""
    rmtree(RESULTS_PATH, ignore_errors=True)
    RESULTS_PATH.mkdir(exist_ok=False)
    return True


def pytest_harvest_xdist_worker_dump(worker_id, session_items, fixture_store):
    """Persist session_items and fixture_store in the file system."""
    with (RESULTS_PATH / f"{worker_id}.pkl").open("wb") as f:
        try:
            pickle.dump((session_items, fixture_store), f)
        except Exception as e:  # noqa: BLE001
            warning(  # noqa: PLE1206
                "Error while pickling worker %s's harvested results: " "[%s] %s",
                (worker_id, e.__class__, e),
            )
    return True


def pytest_harvest_xdist_load():
    """Restore the saved objects from file system."""
    workers_saved_material = {}
    for pkl_file in sorted(RESULTS_PATH.glob("*.pkl")):
        wid = pkl_file.stem
        with pkl_file.open("rb") as f:
            workers_saved_material[wid] = pickle.load(f)
    return workers_saved_material


def pytest_harvest_xdist_cleanup():
    """Don't clean up. Fails to delete directories often."""
    return True
