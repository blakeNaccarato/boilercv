"""Fix up subcooled boiling test notebooks."""

from pathlib import Path
from string import digits

from pandas import read_hdf

NB_DIR = Path(
    "data/docs/study_the_fit_of_bubble_collapse_correlations/prove_the_concept"
)
GLOB_STEM = "23-09-21T19_subcool*"
OLD_NBS, H5S = (
    sorted(NB_DIR.glob(f"{GLOB_STEM}{suffix}")) for suffix in (".ipynb", ".h5")
)
LINKS_LINE = 75
LINKS_START = 88
LINKS_END = -6
LINKS_POS = slice(LINKS_START, LINKS_END)
LINK_NUM_POS = slice(-4, -3)
RUNS = {
    1: "2023-09-20T17-34-38",
    2: "2023-09-20T17-01-04",
    3: "2023-09-20T18-22-37",
    4: "2023-09-20T17-05-15",
    5: "2023-09-20T17-14-18",
    6: "2023-09-20T17-26-15",
    7: "2023-09-20T16-52-06",
    8: "2023-09-20T17-42-19",
    9: "2023-09-20T17-47-49",
}
BOILING = 97.33  # (C) inferred from mean pressure over the time span
time = "time"
T_s = "T_s (C)"
water_temps = ["Tw1cal (C)", "Tw2cal (C)", "Tw3cal (C)"]
cols = [T_s, *water_temps]
RESULTS = NB_DIR / "results_2023-09-20T16-20-24.csv"
DATA = read_hdf(NB_DIR / "subcool_2023-09-20_thermal.h5")


def main():
    for nb in OLD_NBS:
        rename_run(nb)
    nbs = dict(
        zip(
            RUNS.values(),
            (NB_DIR / get_nb_name(run) for run in RUNS.values()),
            strict=True,
        )
    )
    for run, nb in nbs.items():
        rename_link(nb, run)


def rename_run(nb: Path):
    links = nb.read_text(encoding="utf-8").splitlines()[LINKS_LINE][LINKS_POS]
    link_num = int(links[LINK_NUM_POS] if links[LINK_NUM_POS] in digits else "1")
    run = RUNS[link_num]
    nb.rename(nb.parent / get_nb_name(run))


def rename_link(nb: Path, run: str):
    lines = nb.read_text(encoding="utf-8").splitlines()
    lines[LINKS_LINE - 1] = '''"RELINK = False\n"'''
    line = lines[LINKS_LINE]
    lines[LINKS_LINE] = (
        f"{line[:LINKS_START]}{nb.with_suffix('.h5').name}{line[LINKS_END:]}"
    )
    h5 = NB_DIR / get_h5_name(run)
    if not h5.exists():
        nb.write_text(encoding="utf-8", data="\n".join(lines))
        old_h5 = Path(NB_DIR / line[LINKS_POS])
        old_h5.rename(nb.with_suffix(".h5"))


def get_nb_name(run: str):
    return Path(f"subcool_{run}").with_suffix(".ipynb")


def get_h5_name(run: str):
    return Path(f"subcool_{run}").with_suffix(".h5")


if __name__ == "__main__":
    main()
