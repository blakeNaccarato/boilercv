"""Tools for datasets."""

from collections.abc import Callable, Sequence
from itertools import chain
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr
from pytz import timezone

from boilercv.data.models import Dimension, get_dims
from boilercv.types import DA, DS, ArrLike

VIDEO = "video"
"""Name of the video array in a dataset."""
ROI = "roi"
"""Name of the ROI array in a dataset."""
HEADER = "header"
"""Name of the header metadata (attache to an empty array) in a dataset."""
TIMEZONE = timezone("US/Pacific")
"""Timezone for all data."""

FRAME = "frame"
"""Frame dimension name."""
TIME = "time"
"""Time dimension name."""
UTC_TIME = "utc"
"""UTC time dimension name."""

Y = "y"
"""Y dimension name."""
X = "x"
"""X dimension name."""
YX = ["y", "x"]
"""Lenth dimension names."""

PX = "px"
"""Pixel length dimension suffix."""
YPX = f"{Y}{PX}"
"""Y pixel length dimension name."""
XPX = f"{X}{PX}"
"""X pixel length dimension name."""
YX_PX = [YPX, XPX]
"""Pixel length dimension names."""

DIMS = [FRAME, YPX, XPX]
"""Initial dimensions in a dataset."""

PACKED_DIM_INDEX = 2
"""Index of the packed dimension in the dimensions list. Corresponds to X."""
PACKED = "packed"
"""Packed suffix."""
XPX_PACKED = f"xpx_{PACKED}"
"""X pixel length dimension name when bit-packed."""
PACKED_DIMS = [FRAME, YPX, XPX_PACKED]
"""Initial dimensions in a dataset when bit-packed."""

VIDEO_NAME = "video_name"
"""Dimension for the video name, for datasets with frames from multiple videos."""

LENGTH = "um"
"""Length dimension units."""
SAMPLE_DIAMETER_UM = 9_525_000
"""Sample diameter in micrometers."""
ROI = "roi"
"""ROI dimension name."""

islice = pd.IndexSlice
"""Helper for slicing multi-index dataframes."""


def identity_da(da: DA, dim: str) -> DA:
    """Construct a data array that maps a dimension's coordinates to itself.

    Useful to apply `xr.apply_ufunc` along coordinate values.

    Args:
        da: Data array.
        dim: The dimension to extract.
    """
    return xr.DataArray(
        dims=(dim),
        coords={dim: da[dim].values},
        data=da[dim],
    )


def apply_to_img_da(
    func: Callable[..., Any],
    *args: Any,
    returns: int | None = 1,
    vectorize: bool = False,
    name: Sequence[str] | str = "",
    kwargs: dict[str, Any] | None = None,
) -> Any:
    """Apply functions that transform images to transform data arrays instead."""
    core_dims = [YX_PX]
    common_kwargs = dict(
        input_core_dims=core_dims * len(args),
        vectorize=vectorize,
        keep_attrs=True,
        kwargs=kwargs,
    )
    if returns and returns > 0:
        result = xr.apply_ufunc(
            func,
            *args,
            **common_kwargs,
            output_core_dims=core_dims * returns,
        )
        if name and returns == 1:
            result = result.rename(name)
        if name and returns > 1:
            result = tuple(
                part.rename(name_) for name_, part in zip(name, result, strict=True)
            )
        return result
    if not returns or returns == 0:
        xr.apply_ufunc(
            func,
            *args,
            **common_kwargs,
        )


def assign_ds(
    name: str,
    data: ArrLike,
    dims: Sequence[Dimension],
    secondary_dims: Sequence[Dimension] = (),
    fixed_dims: Sequence[Dimension] = (),
    fixed_secondary_dims: Sequence[Dimension] = (),
    ds: DS | None = None,
    long_name: str = "",
    units: str = "",
) -> DS:
    """Build a data array and assign it to a dataset."""
    if not ds:
        ds = xr.Dataset()
    da = build_da(
        name,
        data,
        dims,
        secondary_dims,
        fixed_dims,
        fixed_secondary_dims,
        long_name,
        units,
    )
    ds[name] = da
    return ds


def build_da(
    name: str,
    data: ArrLike,
    dims: Sequence[Dimension],
    secondary_dims: Sequence[Dimension] = (),
    fixed_dims: Sequence[Dimension] = (),
    fixed_secondary_dims: Sequence[Dimension] = (),
    long_name: str = "",
    units: str = "",
):
    """Build a data array."""
    all_primary_dims = chain(fixed_dims, dims)
    all_fixed_dims = chain(fixed_dims, fixed_secondary_dims)
    all_variable_dims = chain(dims, secondary_dims)
    if not long_name:
        long_name = name.capitalize() if len(name) > 1 else name
    if isinstance(data, Sequence) and not len(data):
        shape: list[int] = []
        for dim in all_primary_dims:
            if dim.coords is None:
                shape.append(1)
            else:
                shape.append(len(dim.coords))
        data = np.full(shape, None)
    attrs = {"long_name": long_name}
    if units:
        attrs["units"] = units
    da = xr.DataArray(
        name=name,
        dims=get_dims(*all_primary_dims),
        data=data,
        attrs=attrs,
    )
    for dim in chain(all_fixed_dims, all_variable_dims):
        da = dim.assign_to(da)
    return da
