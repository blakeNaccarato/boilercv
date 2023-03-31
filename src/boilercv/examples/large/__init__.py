"""Examples that operate on large files, which are not in the cloud."""

from collections.abc import Iterator
from contextlib import contextmanager

import xarray as xr

from boilercv import LARGE_EXAMPLES, LARGE_SOURCES
from boilercv.data import VIDEO
from boilercv.gui import view_images
from boilercv.types import DS

EXAMPLE = LARGE_SOURCES / "2022-09-14T13-20-54.nc"


@contextmanager
def example_dataset(
    source: str = "",
    destination: str = "",
    preview: bool = True,
    save: bool = True,
    **kwargs,
) -> Iterator[DS]:  # sourcery skip: move-assign
    """Open the example dataset and write it to a destination file with a suffix.

    Yield a dataset and the name of its video data array.

    Args:
        source: If provided, use a dataset derived from the example with this suffix.
        destination: If provided, add this suffix to the destination dataset file.
        kwargs: Keyword arguments to pass to `xarray.Dataset.to_netcdf`.
        preview: Preview the original and modified datasets.
        save: Whether to save the file.
    """
    _source = LARGE_EXAMPLES / f"{EXAMPLE.stem}_{source}.nc" if source else EXAMPLE
    _destination = LARGE_EXAMPLES / f"{EXAMPLE.stem}_{destination}.nc"
    with xr.open_dataset(_source) as ds:
        original = ds[VIDEO]
        try:
            yield ds
        finally:
            updated = ds[VIDEO]
            if preview:
                view_images(dict(original=original, updated=updated))
            if save:
                ds.to_netcdf(path=_destination, **kwargs)
