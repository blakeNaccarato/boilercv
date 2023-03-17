"""Contour-finding examples."""


import cv2 as cv
import numpy as np

from boilercv import WHITE, convert_image
from boilercv.types import ArrIntDef, Img, NBit_T


def mask(image: Img[NBit_T], roi: ArrIntDef) -> Img[NBit_T]:
    blank = np.zeros_like(image)
    mask: Img[NBit_T] = ~cv.fillConvexPoly(blank, roi, WHITE)
    return cv.add(image, mask)


def threshold(image: Img[NBit_T]) -> Img[NBit_T]:
    return cv.adaptiveThreshold(
        src=image,
        maxValue=np.iinfo(image.dtype).max,
        adaptiveMethod=cv.ADAPTIVE_THRESH_MEAN_C,
        thresholdType=cv.THRESH_BINARY,
        blockSize=11,
        C=2,
    )


def find_contours(image: Img[NBit_T]) -> tuple[list[ArrIntDef], ArrIntDef]:
    return cv.findContours(
        image=~image,
        mode=cv.RETR_EXTERNAL,
        method=cv.CHAIN_APPROX_SIMPLE,
    )


def draw_contours(image: Img[NBit_T], contours) -> Img[NBit_T]:
    # Need three-channel image to paint colored contours
    three_channel_gray = convert_image(image, cv.COLOR_GRAY2RGB)
    # ! Careful: cv.drawContours modifies in-place AND returns
    return cv.drawContours(
        image=three_channel_gray,
        contours=contours,
        contourIdx=-1,
        color=(0, 255, 0),
        thickness=3,
    )
