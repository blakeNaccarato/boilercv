"""Update previews for grayscale videos."""

from loguru import logger

from boilercv.data import FRAME, VIDEO
from boilercv.data.sets import get_dataset
from boilercv.models.params import PARAMS
from boilercv.stages.preview import new_videos_to_preview


def main():
    stage = "large_sources"
    destination = PARAMS.paths.gray_preview
    with new_videos_to_preview(destination) as videos_to_preview:
        for video_name in videos_to_preview:
            if ds := get_dataset(video_name, stage=stage, num_frames=1):
                videos_to_preview[video_name] = ds[VIDEO].isel({FRAME: 0}).values


if __name__ == "__main__":
    logger.info("Start update gray preview")
    main()
    logger.info("Finish update gray preview")