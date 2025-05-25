import cv2
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QScrollArea, QLabel, QHBoxLayout, QVBoxLayout
)
from PySide6.QtGui import QImage, QPixmap


class ThumbnailLabel(QLabel):
    """
    QLabel that stores its original QPixmap and can rescale dynamically.
    """
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._original = pixmap
        self.setPixmap(pixmap)
        self.setScaledContents(False)

    def rescale(self, height: int):
        """
        Rescale the stored pixmap to the given height, preserving aspect ratio.
        """
        scaled = self._original.scaledToHeight(height, Qt.SmoothTransformation)
        self.setPixmap(scaled)
        self.setFixedSize(scaled.size())


class ROIViewerWidget(QWidget):
    """
    A horizontally-scrollable widget that displays ROIs emitted
    from the BoundingBox processor, dynamically scaling thumbnails
    to the height of the viewport.
    """
    def __init__(self, parent=None, margin: int = 2):
        super().__init__(parent)
        self._margin = margin

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area setup
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        main_layout.addWidget(self._scroll)

        # Container widget to hold the horizontal layout
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self._inner = QWidget()
        self._hbox = QHBoxLayout(self._inner)
        self._hbox.setContentsMargins(0, 0, 0, 0)
        self._hbox.setSpacing(self._margin)
        self._hbox.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._inner.setLayout(self._hbox)
        container_layout.addWidget(self._inner)

        self._scroll.setWidget(container)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale_thumbnails()

    def _rescale_thumbnails(self):
        # Determine available height inside the scroll viewport
        height = self._scroll.viewport().height() - 2 * self._margin
        for i in range(self._hbox.count()):
            item = self._hbox.itemAt(i)
            widget = item.widget()
            if isinstance(widget, ThumbnailLabel):
                widget.rescale(height)

    @Slot(object)
    def add_roi(self, roi_frame):
        """
        Slot to receive one ROI (NumPy BGR array), convert to QPixmap,
        scale to viewport height, and append it horizontally.
        """
        # Convert BGR to RGB and wrap in QPixmap
        rgb = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)

        # Create thumbnail label and scale to current height
        thumb = ThumbnailLabel(pix, self)
        height = self._scroll.viewport().height() - 2 * self._margin
        thumb.rescale(height)

        self._hbox.addWidget(thumb)
        self._scroll.widget().update()

    @Slot()
    def clear(self):
        """
        Clears all currently displayed ROIs.
        """
        while self._hbox.count():
            item = self._hbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    @Slot(object)
    def set_rois(self, roi_list):
        """
        Replace the current thumbnails with this list of ROI frames.
        Clears first, then adds each ROI in order.
        """
        self.clear()
        for roi in roi_list:
            self.add_roi(roi)
