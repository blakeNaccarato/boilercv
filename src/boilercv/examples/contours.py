"""Get bubble contours."""

import cv2 as cv
import numpy as np

from boilercv import PREVIEW
from boilercv.captivate.previews import view_images
from boilercv.colors import BLUE
from boilercv.data import VIDEO, islice
from boilercv.data.sets import get_dataset
from boilercv.examples import EXAMPLE_CONTOURS, EXAMPLE_NUM_FRAMES, EXAMPLE_VIDEO_NAME
from boilercv.images import scale_bool
from boilercv.images.cv import draw_contours
from boilercv.stages.find_contours import get_all_contours
from boilercv.types import ArrInt, Img


def main():
    ds = get_dataset(EXAMPLE_VIDEO_NAME, EXAMPLE_NUM_FRAMES)
    video = ds[VIDEO]
    df = get_all_contours(
        cv.bitwise_not(scale_bool(video.values)), method=cv.CHAIN_APPROX_SIMPLE
    )
    df.to_hdf(EXAMPLE_CONTOURS, "contours", complib="zlib", complevel=9)
    result: list[Img] = []
    for frame_num, frame in enumerate(video):
        contours: list[ArrInt] = list(  # type: ignore  # pyright 1.1.333
            df.loc[islice[frame_num], :]  # type: ignore  # pyright 1.1.333
            .groupby("contour")
            .apply(lambda grp: grp.values)  # type: ignore  # pyright 1.1.333
        )
        frame_color = np.repeat(scale_bool(frame.values)[:, :, np.newaxis], 3, axis=-1)
        result.append(draw_contours(frame_color, contours, thickness=2, color=BLUE))
    if PREVIEW:
        view_images(result)


if __name__ == "__main__":
    main()
