"""Docs config."""

from datetime import date
from hashlib import sha256
from pathlib import Path

from ruamel.yaml import YAML
from sphinx.application import Sphinx

from boilercv_docs import DOCS, PYPROJECT, chdir_docs
from boilercv_docs.intersphinx import get_ispx, get_rtd, get_url
from boilercv_docs.nbs import init_nb_env
from boilercv_docs.patch_nbs import patch_nbs
from boilercv_docs.types import IspxMappingValue

# ! Initialization
patch_nbs()
ROOT = chdir_docs()
"""Root directory of the project."""
# ! Paths
STATIC = DOCS / "_static"
"""Static assets folder, used in configs and setup."""
CSS = STATIC / "local.css"
"""Local CSS file, used in configs and setup."""
BIB_TEMPLATE = DOCS / "refs-template.bib"
"""Project template bibliography file."""
BIB = DOCS / "refs.bib"
"""Bibliography file."""
COPIER_ANSWERS = ROOT / ".copier-answers.yml"
"""Copier answers file."""
# ! Template answers
ANS = YAML().load(COPIER_ANSWERS.read_text(encoding="utf-8"))
"""Project template answers."""
AUTHORS = ANS["project_owner_name"]
"""Authors of the project."""
USER = ANS["project_owner_github_username"]
"""Host GitHub user or organization for this repository."""
REPO = ANS["github_repo_name"]
"""GitHub repository name."""
PACKAGE = ANS["project_name"]
"""Package name."""
VERSION = ANS["project_version"]
"""Package version."""
# ! Intersphinx and related
ISPX_MAPPING: dict[str, IspxMappingValue] = {
    **{pkg: get_rtd(pkg) for pkg in ["myst_parser", "nbformat", "numpydoc", "tomlkit"]},
    **{pkg: get_rtd(pkg, latest=True) for pkg in ["pyqtgraph"]},
    "jupyterbook": get_url("jupyterbook.org/en"),
    "numpy": get_url("numpy.org/doc"),
    "matplotlib": get_url("matplotlib.org"),
    "pytest": get_url("docs.pytest.org/en"),
    "sympy": get_url("docs.sympy.org", latest=True),
    "colorcet": get_ispx("https://colorcet.holoviz.org/"),
    "cv2": get_ispx("docs.opencv.org/2.4"),
    "pandas": get_ispx("pandas.pydata.org/docs"),
    "python": get_ispx("docs.python.org/3"),
}
"""Intersphinx mapping."""
TIPPY_RTD_URLS = [
    ispx.url
    for pkg, ispx in ISPX_MAPPING.items()
    if pkg not in ["python", "pandas", "matplotlib"]
]
"""Tippy ReadTheDocs-compatible URLs."""
REV = "7cc78e6d87a8603b9633ab0084241b504952f815"
"""Binder revision."""

# ! Setup


def setup(app: Sphinx):
    """Add functions to Sphinx setup."""
    init_nb_env()
    app.connect("html-page-context", add_version_to_css)


def add_version_to_css(app: Sphinx, _pagename, _templatename, ctx, _doctree):
    """Add the version number to the local.css file, to bust the cache for changes.

    See Also
    --------
    https://github.com/executablebooks/MyST-Parser/blob/978e845543b5bcb7af0ff89cac9f798cb8c16ab3/docs/conf.py#L241-L249
    """
    if app.builder.name != "html":
        return
    css = dpath(CSS)
    if css in ctx.get((k := "css_files"), {}):
        ctx[k][ctx[k].index(css)] = f"{css}?hash={sha256(CSS.read_bytes()).hexdigest()}"


def dpaths(*paths: Path, rel: Path = DOCS) -> list[str]:
    """Get the string-representation of paths relative to docs for Sphinx config.

    Parameters
    ----------
    paths
        Paths to convert.
    rel
        Relative path to convert to. Defaults to the 'docs' directory.
    """
    return [dpath(path, rel) for path in paths]


def dpath(path: Path, rel: Path = DOCS) -> str:
    """Get the string-representation of a path relative to docs for Sphinx config.

    Parameters
    ----------
    path
        Path to convert.
    rel
        Relative path to convert to. Defaults to the 'docs' directory.
    """
    return path.relative_to(rel).as_posix()


# ! Basics
project = PACKAGE
copyright = f"{date.today().year}, {AUTHORS}"  # noqa: A001
version = VERSION
master_doc = "index"
language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**/_*.md", "**/_*.ipynb"]
extensions = [
    "autodoc2",
    "myst_nb",
    "sphinx_design",
    "sphinx_tippy",
    "sphinx_thebe",
    "sphinx_togglebutton",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinxcontrib.bibtex",
    "sphinxcontrib.mermaid",
    "sphinxcontrib.towncrier",
]
suppress_warnings = [
    "autodoc2.dup_item"  # "Duplicate items in boilercv_tests.test_morphs
]
# ! Theme
html_title = PACKAGE
html_favicon = "_static/favicon.ico"
html_logo = "_static/favicon.ico"
html_static_path = dpaths(STATIC)
html_css_files = dpaths(CSS, rel=STATIC)
html_theme = "sphinx_book_theme"
html_context = {
    # ? MyST elements don't look great with dark mode, but allow dark for accessibility.
    "default_mode": "light"
}
COMMON_OPTIONS = {
    "repository_url": f"https://github.com/{USER}/{PACKAGE}",
    "path_to_docs": dpath(DOCS),
}
html_theme_options = {
    **COMMON_OPTIONS,
    "navigation_with_keys": False,  # https://github.com/pydata/pydata-sphinx-theme/pull/1503
    "repository_branch": "main",
    "show_navbar_depth": 2,
    "show_toc_level": 4,
    "use_download_button": True,
    "use_fullscreen_button": True,
    "use_repository_button": True,
}
# ! MyST
mathjax3_config = {
    "tex": {
        "macros": {
            # ? User-defined macros: https://docs.mathjax.org/en/latest/input/tex/macros.html
            # ? Built-in macros: https://docs.mathjax.org/en/latest/input/tex/macros/index.html#tex-commands
            **{
                const: rf"\mathit{{{const}}}"
                for const in ["Fo", "Ja", "Nu", "Pe", "Pr", "Re"]
            },
            **{f"{const}o": rf"\mathit{{{const}0}}" for const in ["", "b"]},
        }
    }
}
myst_enable_extensions = [
    "attrs_block",
    "colon_fence",
    "deflist",
    "dollarmath",
    "linkify",
    "strikethrough",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 6
myst_substitutions = {
    "binder": f"[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blakeNaccarato/{PACKAGE}/{REV}?labpath=docs%2Fexperiments%2Fe230920_subcool%2Fplot_tracks.ipynb)"
}
# ! BibTeX
bibtex_bibfiles = dpaths(BIB_TEMPLATE, BIB)
bibtex_reference_style = "label"
bibtex_default_style = "unsrt"
# ! NB
nb_execution_mode = "cache"
nb_execution_raise_on_error = True
# ! Thebe
thebe_config = {**COMMON_OPTIONS, "repository_branch": REV, "selector": "div.highlight"}
# ! Other
numfig = True
math_eqref_format = "Eq. {number}"
mermaid_d3_zoom = False
# ! Autodoc2
nitpicky = True
autodoc2_packages = [
    f"../src/{PACKAGE}",
    f"{PACKAGE}_docs",
    f"../pipeline/{PACKAGE}_pipeline",
    f"../tests/{PACKAGE}_tests",
    f"../scripts/{PACKAGE}_tools",
]
autodoc2_render_plugin = "myst"
# ? Autodoc2 does not currently obey `python_display_short_literal_types` or
# ? `python_use_unqualified_type_names`, but `maximum_signature_line_length` makes it a
# ? bit prettier.
# ? https://github.com/sphinx-extensions2/sphinx-autodoc2/issues/58
maximum_signature_line_length = 1
# ? Parse Numpy docstrings
autodoc2_docstring_parser_regexes = [(".*", f"{PACKAGE}_docs.docstrings")]
# ! Intersphinx
intersphinx_mapping = {
    pkg: ispx for pkg, ispx in ISPX_MAPPING.items() if pkg != "colorcet"
}
nitpick_ignore = [
    ("py:class", "cv2.LineSegmentDetector"),
    ("py:class", f"{PACKAGE}.correlations.T"),
    ("py:class", f"{PACKAGE}.data.sets.Stage"),
    ("py:class", f"{PACKAGE}.experiments.e230920_subcool.NbProcess"),
    ("py:class", f"{PACKAGE}.experiments.e230920_subcool.NbProcess"),
    ("py:class", f"{PACKAGE}.morphs.contexts"),
]

nitpick_ignore_regex = [
    # ? Missing inventory
    (r"py:.*", r"docutils\..+"),
    (r"py:.*", r"numpydoc\.docscrape\..+"),
    (r"py:.*", r"_pytest\..+"),
    (r"py:.*", r"numpy\.typing\..+"),
    (r"py:.*", r"tomlkit\.container\..+"),
    (  # ? sympy: https://github.com/sympy/sympy/issues/17619#issuecomment-536781620
        r"py:.*",
        r"sympy\..+",
    ),
    (r"py:.*", r"pydantic\..+"),  # ? https://github.com/pydantic/pydantic/issues/1339
    (r"py:.*", r"PySide6\..+"),  # ? https://bugreports.qt.io/browse/PYSIDE-2215
    # ? TypeAlias: https://github.com/sphinx-doc/sphinx/issues/10785
    (r"py:class", rf"{PACKAGE}.*\.types\..+"),
    (r"py:class", rf"{PACKAGE}_pipeline\.captivate\.previews\..+"),
    (r"py:.*", rf"{PACKAGE}_tests\.test_morphs\..+"),
    # ? Until done with Pydantic v1
    (r"py:.*", r"pydantic\.v1\..+"),
]
# ! Tippy
# ? https://sphinx-tippy.readthedocs.io/en/latest/index.html#confval-tippy_anchor_parent_selector
tippy_anchor_parent_selector = "article.bd-article"
# ? Mermaid tips don't work
tippy_skip_anchor_classes = ["mermaid"]
# ? https://github.com/sphinx-extensions2/sphinx-tippy/issues/6#issuecomment-1627820276
tippy_enable_mathjax = True
tippy_tip_selector = """
    aside,
    div.admonition,
    div.literal-block-wrapper,
    figure,
    img,
    div.math,
    p,
    table
    """
# ? Skip Zenodo DOIs as the hover hint doesn't work properly
tippy_rtd_urls = TIPPY_RTD_URLS
tippy_skip_urls = [
    # ? Skip Zenodo DOIs as the hover hint doesn't work properly
    r"https://doi\.org/10\.5281/zenodo\..+"
]
# ! Towncrier
towncrier_draft_autoversion_mode = "draft"
towncrier_draft_include_empty = True
towncrier_draft_working_directory = ROOT
towncrier_draft_config_path = PYPROJECT
