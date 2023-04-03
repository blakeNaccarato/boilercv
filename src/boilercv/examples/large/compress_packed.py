"""Compress the packed video data in a NetCDF file.

This is much quicker, and yields another 8x compresssion ratio on top of the packing.
"""

from boilercv.data import VIDEO
from boilercv.examples.large import example_dataset


@example_dataset(  # type: ignore
    source="packed",
    destination="packed_compressed",
    preview=False,
    encoding={VIDEO: {"zlib": True}},
)
def main():
    pass


if __name__ == "__main__":
    main()
