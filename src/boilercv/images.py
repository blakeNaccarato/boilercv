"""Image acquisition and processing."""

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Literal

import cv2 as cv
import numpy as np
import yaml

from boilercv import MARKER_COLOR, WHITE
from boilercv.types import ArrIntDef, Img8, ImgBool8
from boilercv.types.base import Img, NBit, NBit_T


def load_roi(
    image: Img[NBit_T],
    roi_path: Path,
    roi_type: Literal["poly", "line"] = "poly",
) -> ArrIntDef:
    """Load the region of interest for an image."""
    (width, height) = image.shape[-2:]
    if roi_path.exists():
        vertices: list[tuple[int, int]] = yaml.safe_load(
            roi_path.read_text(encoding="utf-8")
        )
    else:
        vertices = (
            [(0, 0), (0, width), (height, width), (height, 0)]
            if roi_type == "poly"
            else [(0, 0), (height, width)]
        )
    return np.array(vertices, dtype=int)


def mask(image: Img[NBit_T], roi: ArrIntDef) -> Img[NBit_T]:
    blank = np.zeros_like(image)
    mask: Img[NBit_T] = ~cv.fillPoly(
        img=blank,
        pts=[roi],  # Needs a list of arrays
        color=WHITE,
    )
    return cv.add(image, mask)


def threshold(
    image: Img[NBit_T], block_size: int = 11, thresh_dist_from_mean: int = 2
) -> Img[NBit_T]:
    block_size += 1 if block_size % 2 == 0 else 0
    return cv.adaptiveThreshold(
        src=image,
        maxValue=np.iinfo(image.dtype).max,
        adaptiveMethod=cv.ADAPTIVE_THRESH_MEAN_C,
        thresholdType=cv.THRESH_BINARY,
        blockSize=block_size,
        C=thresh_dist_from_mean,
    )


def find_contours(image: Img[NBit_T]) -> list[ArrIntDef]:
    contours, _hierarchy = cv.findContours(
        image=~image,  # OpenCV finds bright contours, bubble edges are dark
        mode=cv.RETR_EXTERNAL,  # No hierarchy needed because we keep external contours
        method=cv.CHAIN_APPROX_SIMPLE,  # Approximate the contours
    )
    return contours


def draw_contours(
    image: Img[NBit_T], contours: list[ArrIntDef], contour_index: int = -1, thickness=2
) -> Img[NBit_T]:
    # Need three-channel image to paint colored contours
    three_channel_gray = convert_image(image, cv.COLOR_GRAY2RGB)
    # ! Careful: cv.drawContours modifies in-place AND returns
    return cv.drawContours(
        image=three_channel_gray,
        contours=contours,
        contourIdx=contour_index,
        color=MARKER_COLOR,
        thickness=thickness,
    )


def flood(image: Img[NBit_T], seed_point: tuple[int, int]) -> ImgBool8:
    """Flood the image, returning the resulting flood as a mask."""
    max_value = np.iinfo(image.dtype).max
    mask = np.pad(
        np.full_like(image, 0),
        pad_width=1,
        constant_values=max_value,
    )
    _retval, _image, mask, _rect = cv.floodFill(
        image=image,
        mask=mask,
        seedPoint=seed_point,
        newVal=None,  # Ignored in mask only mode
        flags=cv.FLOODFILL_MASK_ONLY,
    )
    return mask[1:-1, 1:-1].astype(np.bool_)


# * -------------------------------------------------------------------------------- * #


def _8_bit(image: Img[NBit]) -> Img8:
    """Assume an image is 8-bit."""
    return image  # type: ignore


def convert_image(image: Img[NBit_T], code: int | None = None) -> Img[NBit_T]:
    """Convert image format, handling inconsistent type annotations."""
    return image if code is None else cv.cvtColor(image, code)  # type: ignore


def get_8bit_images(images: Iterable[Img[NBit]]) -> Iterator[Img8]:
    """Assume images are 8-bit."""
    return (_8_bit(image) for image in images)
