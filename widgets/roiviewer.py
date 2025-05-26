import cv2
from collections import deque
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
        scaled = self._original.scaledToHeight(height, Qt.SmoothTransformation)
        self.setPixmap(scaled)
        self.setFixedSize(scaled.size())


class ROIViewerWidget(QWidget):
    """
    A horizontally-scrollable widget that displays ROIs emitted
    from the BoundingBox processor. If inference is enabled and a
    TCP client is provided, each ROI is first sent for classification,
    then drawn with the result overlay.
    """
    def __init__(self, parent=None, tcp_client=None, inference_enabled=True, margin: int = 2):
        super().__init__(parent)
        self._margin = margin
        self.tcp_client = tcp_client
        self.inference_enabled = inference_enabled
        self._roi_queue = deque()
        self._current_roi = None

        # Connect TCP classification signal
        if self.tcp_client:
            self.tcp_client.classification_result.connect(self._on_classification_result)

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
        height = self._scroll.viewport().height() - 2 * self._margin
        for i in range(self._hbox.count()):
            item = self._hbox.itemAt(i)
            widget = item.widget()
            if isinstance(widget, ThumbnailLabel):
                widget.rescale(height)

    @Slot(object)
    def add_roi(self, roi_frame):
        """
        Convert BGR frame to QPixmap thumbnail and append.
        """
        # BGR → RGB
        rgb = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)

        thumb = ThumbnailLabel(pix, self)
        height = self._scroll.viewport().height() - 2 * self._margin
        thumb.rescale(height)
        self._hbox.addWidget(thumb)
        self._scroll.widget().update()

    @Slot()
    def clear(self):
        while self._hbox.count():
            item = self._hbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    @Slot(list)
    def set_rois(self, roi_list):
        """
        Replace current thumbnails. If inference is on, send each ROI
        to the TCP client in turn, await its classification, then draw.
        Otherwise draw immediately.
        """
        self.clear()
        
        if self.inference_enabled and self.tcp_client:
            print(f"[ROIViewer] Received {len(roi_list)} ROIs")
            self._roi_queue.extend(roi_list)
            self._process_next_roi()
        else:
            for roi in roi_list:
                self.add_roi(roi)

    def _process_next_roi(self):
        if not self._roi_queue:
            return
        self._current_roi = self._roi_queue.popleft()
        # send single-ROI batch for inference
        self.tcp_client.send_rois([self._current_roi])

    @Slot(int)
    def _on_classification_result(self, result):
        """
        Receive one classification result, annotate the current ROI,
        draw it, then proceed to the next ROI in queue.
        """
        roi = self._current_roi
        # overlay result text on a copy
        annotated = roi.copy()
        cv2.putText(annotated,
                    str(result),
                    (5, 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                    cv2.LINE_AA)
        self.add_roi(annotated)
        self._process_next_roi()
