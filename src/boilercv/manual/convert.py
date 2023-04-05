"""Convert all CINEs to NetCDF."""

from loguru import logger

from boilercv.data.video import prepare_dataset
from boilercv.models.paths import LOCAL_PATHS, get_sorted_paths


def main():
    for source in get_sorted_paths(LOCAL_PATHS.cines):
        destination = LOCAL_PATHS.large_sources / f"{source.stem}.nc"
        if destination.exists():
            continue
        try:
            prepare_dataset(source).to_netcdf(path=destination)
        except Exception:
            logger.exception(source.stem)
            continue


if __name__ == "__main__":
    main()
