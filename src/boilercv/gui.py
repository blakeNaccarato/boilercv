"""Graphical user interface utilities."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import numpy as np
import pyqtgraph as pg
import yaml
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton

from boilercv.images import load_roi
from boilercv.types import ArrIntDef, Img, ImgSeq, NBit_T


def compare_images(results: Sequence[Img[NBit_T] | ImgSeq[NBit_T]]):
    """Compare multiple sets of images or sets of timeseries of images."""
    results = [np.array(result) for result in results]
    num_results = len(results)
    with image_viewer(num_results) as (
        _app,
        _window,
        _layout,
        _button_layout,
        image_views,
    ):
        for result, image_view in zip(results, image_views, strict=False):
            image_view.setImage(result)


def preview_images(result: Img[NBit_T] | ImgSeq[NBit_T]):
    """Preview a single image or timeseries of images."""
    result = np.array(result)
    with image_viewer() as (_app, _window, _layout, _button_layout, image_views):
        image_views[0].setImage(result)


# * -------------------------------------------------------------------------------- * #


def edit_roi(
    image: Img[NBit_T], roi_path: Path, roi_type: Literal["poly", "line"] = "poly"
) -> ArrIntDef:
    """Edit the region of interest for an image."""

    with image_viewer() as (_app, window, _layout, button_layout, image_views):
        common_roi_args = dict(
            pen=pg.mkPen("red"),
            hoverPen=pg.mkPen("magenta"),
            handlePen=pg.mkPen("blue"),
            handleHoverPen=pg.mkPen("magenta"),
            positions=load_roi(image, roi_path, roi_type),
        )
        roi = (
            pg.PolyLineROI(
                **common_roi_args,
                closed=True,
            )
            if roi_type == "poly"
            else pg.LineSegmentROI(**common_roi_args)
        )

        def main():
            """Allow ROI interaction."""
            window.key_signal.connect(keyPressEvent)
            button = QPushButton("Save ROI")
            button.clicked.connect(save_roi)  # type: ignore
            button_layout.addWidget(button)
            image_views[0].setImage(image)
            image_views[0].addItem(roi)

        def keyPressEvent(ev: QKeyEvent):  # noqa: N802
            """Save ROI or quit on key presses."""
            if ev.key() == Qt.Key.Key_S:
                save_roi()
                ev.accept()

        def save_roi():
            """Save the ROI."""
            vertices = get_roi_vertices()
            roi_path.write_text(
                encoding="utf-8", data=yaml.safe_dump(vertices.tolist(), indent=2)
            )

        def get_roi_vertices() -> ArrIntDef:
            """Get the vertices of the ROI."""
            return np.array(roi.saveState()["points"], dtype=int)

        main()

    return get_roi_vertices()


@contextmanager
def image_viewer(num_views: int = 1):  # noqa: C901
    """View and interact with images and video."""
    # Isolate pg.ImageView in a layout cell. It is complicated to directly modify the UI
    # of pg.ImageView. Can't use the convenient pg.LayoutWidget because
    # GraphicsLayoutWidget cannot contain it, and GraphicsLayoutWidget is convenient on
    # its own.
    image_view_grid_size = int(np.ceil(np.sqrt(num_views)))
    app = pg.mkQApp()
    image_views: list[pg.ImageView] = []
    layout = QGridLayout()
    button_layout = QHBoxLayout()
    window = GraphicsLayoutWidgetWithKeySignal(show=True, size=(800, 600))
    window.setLayout(layout)

    def main():
        add_image_views()
        add_actions()
        try:
            yield app, window, layout, button_layout, image_views
        finally:
            app.exec()

    def add_image_views():
        if num_views == 2:  # noqa: PLR2004
            coordinates = [(0, 0), (0, 1)]
        else:
            coordinates = get_square_grid_coordinates(image_view_grid_size)
        for column in range(image_view_grid_size):
            layout.setColumnStretch(column, 1)
        for coordinate in coordinates:
            image_view = get_image_view()
            layout.addWidget(image_view, *coordinate)
            image_views.append(image_view)

    def add_actions():
        window.key_signal.connect(keyPressEvent)
        layout.addLayout(
            button_layout, image_view_grid_size, 0, 1, image_view_grid_size
        )
        if num_views > 1:
            add_button(button_layout, "Toggle Play All", trigger_space).setFocus()
        add_button(button_layout, "Continue", app.quit)

    def keyPressEvent(ev: QKeyEvent):  # noqa: N802
        """Handle quit events and propagate keypresses to image views."""
        if ev.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Q, Qt.Key.Key_Enter):
            app.quit()
            ev.accept()
        for image_view in image_views:
            image_view.keyPressEvent(ev)

    def trigger_space():
        keyPressEvent(
            QKeyEvent(
                QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier
            )
        )

    yield from main()


class GraphicsLayoutWidgetWithKeySignal(pg.GraphicsLayoutWidget):
    """Emit key signals on `key_signal`."""

    key_signal = Signal(QKeyEvent)

    def keyPressEvent(self, ev: QKeyEvent):  # noqa: N802
        super().keyPressEvent(ev)
        self.key_signal.emit(ev)


def add_button(layout, label, callback):
    button = QPushButton(label)
    button.clicked.connect(callback)  # type: ignore
    layout.addWidget(button)
    return button


def get_image_view() -> pg.ImageView:
    """Get an image view suitable for previewing images."""
    image_view = pg.ImageView()
    image_view.playRate = 30
    image_view.ui.histogram.hide()
    image_view.ui.roiBtn.hide()
    image_view.ui.menuBtn.hide()
    return image_view


def get_square_grid_coordinates(n: int) -> Iterator[ArrIntDef]:
    """Get the coordinates of a square grid."""
    x, y = np.indices((n, n))
    yield from np.column_stack((x.ravel(), y.ravel()))
