"""Paths for this project."""

from pathlib import Path

from pydantic import DirectoryPath, FilePath

from boilercv import DATA_DIR, LOCAL_DATA
from boilercv.models import CreatePathsModel


def get_sorted_paths(path: Path) -> list[Path]:
    """Iterate over a sorted directory."""
    return sorted(path.iterdir())


class Paths(CreatePathsModel):
    """Paths associated with project data."""

    # ! REQUIREMENTS
    requirements: FilePath = Path("requirements.txt")
    dev_requirements: DirectoryPath = Path(".tools/requirements")

    # ! PACKAGE
    package: DirectoryPath = Path("src") / "boilercv"
    stages: DirectoryPath = package / "stages"
    models: DirectoryPath = package / "models"
    paths_module: FilePath = models / "paths.py"

    # ! STAGES
    stage_contours: FilePath = stages / "contours.py"
    stage_fill: FilePath = stages / "fill.py"

    # ! PREVIEW STAGES
    update_previews: DirectoryPath = stages / "update_previews"
    stage_binarized_preview: FilePath = update_previews / "binarized.py"
    stage_gray_preview: FilePath = update_previews / "gray.py"
    stage_filled_preview: FilePath = update_previews / "filled.py"

    # ! DATA
    data: DirectoryPath = DATA_DIR
    contours: DirectoryPath = data / "contours"
    examples: DirectoryPath = data / "examples"
    filled: DirectoryPath = data / "filled"
    rois: DirectoryPath = data / "rois"
    samples: DirectoryPath = data / "samples"
    sources: DirectoryPath = data / "sources"

    # ! PREVIEW DATA
    previews: DirectoryPath = data / "previews"
    binarized_preview: Path = previews / "binarized.nc"
    gray_preview: Path = previews / "gray.nc"
    filled_preview: Path = previews / "filled.nc"


class LocalPaths(CreatePathsModel):
    """Local paths for larger files not stored in the cloud."""

    data: DirectoryPath = LOCAL_DATA
    hierarchical_data: DirectoryPath = data / "data"

    large_examples: DirectoryPath = data / "large_examples"
    large_sources: DirectoryPath = data / "large_sources"
    notes: DirectoryPath = data / "notes"
    sheets: DirectoryPath = data / "sheets"
    uncompressed_contours: DirectoryPath = data / "uncompressed_contours"
    uncompressed_filled: DirectoryPath = data / "uncompressed_filled"
    uncompressed_sources: DirectoryPath = data / "uncompressed_sources"

    cines: DirectoryPath = data / "cines"
    large_example_cine: Path = cines / "2022-01-06T16-57-31.cine"

    media: Path = Path("G:/My Drive/Blake/School/Grad/Reports/Content/boilercv")
