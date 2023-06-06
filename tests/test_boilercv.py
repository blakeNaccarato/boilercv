"""Test the data process."""

import importlib
from pathlib import Path

import pytest


@pytest.mark.slow()
@pytest.mark.usefixtures("tmp_project")
@pytest.mark.parametrize(
    "stage",
    [stage.stem for stage in Path("src/boilercv/manual").glob("[!__]*.py")],
)
def test_manual(stage: str):
    """Test that manual stages can run."""
    importlib.import_module(f"boilercv.manual.{stage}").main()


@pytest.mark.slow()
@pytest.mark.usefixtures("tmp_project")
@pytest.mark.parametrize(
    "stage",
    [
        stage.stem
        for stage in Path("src/boilercv/stages").glob("[!__]*.py")
        if stage.stem not in {}
    ],
)
def test_stages(stage: str):
    """Test that stages can run."""
    importlib.import_module(f"boilercv.stages.{stage}").main()


@pytest.mark.slow()
@pytest.mark.usefixtures("tmp_project")
@pytest.mark.parametrize(
    "stage",
    [
        stage.stem
        for stage in Path("src/boilercv/stages/update_previews").glob("[!__]*.py")
    ],
)
def test_update_previews(stage: str):
    """Test that preview update stages can run."""
    importlib.import_module(f"boilercv.stages.update_previews.{stage}").main()


@pytest.mark.slow()
@pytest.mark.usefixtures("tmp_project")
@pytest.mark.parametrize(
    "stage",
    [stage.stem for stage in Path("src/boilercv/previews").glob("[!__]*.py")],
)
def test_previews(stage: str):
    """Test that manual stages can run."""
    importlib.import_module(f"boilercv.previews.{stage}").main()
