"""Flatten the data directory structure.

The directory structure looks like:

    data
    └───YYYY-MM-DD
        ├───data
        ├───notes
        └───video
"""

from itertools import chain

from boilercv.models.params import PARAMS


def main():
    source = PARAMS.paths.hierarchical_data
    rename_notes(source)
    rename_cines(source)
    rename_sheets(source)


def rename_notes(source):
    notes_dest = PARAMS.paths.notes
    notes_dirs = {
        trial.stem: trial / "notes"
        for trial in sorted(source.iterdir())
        if trial.is_dir()
    }
    for trial, note_dir in notes_dirs.items():
        if not note_dir.exists():
            continue
        note_dir.rename(notes_dest / trial)


def rename_cines(source):
    destination = PARAMS.paths.cines
    trials = [trial / "video" for trial in source.iterdir() if trial.is_dir()]
    videos = sorted(chain.from_iterable(trial.glob("*.cine") for trial in trials))
    for video in videos:
        video.rename(destination / video.name.removeprefix("results_"))


def rename_sheets(source):
    sheets_dest = PARAMS.paths.sheets
    data = [trial / "data" for trial in sorted(source.iterdir()) if trial.is_dir()]
    sheets = sorted(chain.from_iterable(trial.glob("*.csv") for trial in data))
    for sheet in sheets:
        sheet.rename(sheets_dest / sheet.name.removeprefix("results_"))


if __name__ == "__main__":
    main()
