"""Test configuration."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from boilercore import WarningFilter, filter_certain_warnings
from boilercore.testing import get_nb_client, get_nb_namespace, get_session_path

import boilercv


@pytest.fixture(autouse=True, scope="session")
def project_session_path(tmp_path_factory):
    """Set the project directory."""
    return get_session_path(tmp_path_factory, boilercv)


# Can't be session scope
@pytest.fixture(autouse=True)
def _filter_certain_warnings():
    """Filter certain warnings."""
    filter_certain_warnings(
        [
            WarningFilter(
                message=r"numpy\.ndarray size changed, may indicate binary incompatibility\. Expected \d+ from C header, got \d+ from PyObject",
                category=RuntimeWarning,
            ),
            WarningFilter(
                message=r"A grouping was used that is not in the columns of the DataFrame and so was excluded from the result\. This grouping will be included in a future version of pandas\. Add the grouping as a column of the DataFrame to silence this warning\.",
                category=FutureWarning,
            ),
        ]
    )


@pytest.fixture()
def ns(request) -> SimpleNamespace:
    """Notebook namespace to be inspected."""
    param: tuple[Path, dict[str, Any]] = request.param
    path, parameters = param
    return get_nb_namespace(get_nb_client(path), parameters)
