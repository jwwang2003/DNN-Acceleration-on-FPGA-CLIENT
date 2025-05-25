import cv2
import sys

from PySide6.QtCore import Qt, QTimer, Slot, QThread

from PySide6.QtGui import QPixmap, QImage

from PySide6.QtWidgets import \
    QApplication, QLabel, QWidget, QVBoxLayout, QSizePolicy

from processors.pre import PreProcessorBase, BoundingBox
from providers.source import FrameGrabber

class VideoWidget(QWidget):
    """Widget to display video feed (with or without processing)."""
    def __init__(
        self,
        parent=None,
        disp_fps: int=60                # Default to 60 FPS for smooth GUI
    ):
        super().__init__(parent)
        # Only set window title if used as top-level window
        if parent is None:
            self.setWindowTitle("Live feed")
        self.disp_fps = disp_fps
        
        # Layout
        layout = QVBoxLayout(self)
        self.video_label = QLabel(alignment=Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMinimumSize(1, 1)
        layout.addWidget(self.video_label)

        # Timer to refresh display at fixed rate
        interval = int(1000 / self.disp_fps)
        self.display_timer = QTimer(self)
        self.display_timer.setInterval(interval)
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start()

        # Placeholder for latest frame
        self.latest_frame: cv2.typing.MatLike = None
        self.last_pixmap: QPixmap = None

    def set_processor(self, processor: PreProcessorBase):
        """
        Connects an external processor's processed_frame signal to this widget.
        """
        # Disconnect any previous processor
        try:
            self._current_processor.processed_frame.disconnect(self.on_frame)
        except Exception:
            pass
        # Connect new processor to the on_frame slot
        processor.processed_frame.connect(self.on_frame)
        self._current_processor = processor
        
    @Slot(object)
    def on_frame(self, image):
        """
        Slot to handle incoming frames from the frame grabber.
        """
        self.latest_frame = image

    def update_display(self):
        if self.latest_frame is not None:
            frame = self.latest_frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(
                rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
            )
            pixmap = QPixmap.fromImage(qt_image)
            self.last_pixmap = pixmap
            scaled = pixmap.scaled(
                self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled)

# Example usage as standalone:
if __name__ == '__main__':
    app = QApplication([])
    fg = FrameGrabber(0)
    w = VideoWidget()
    
    processor1 = BoundingBox(min_area=5000)
    fg.frame_ready.connect(processor1.on_frame)
    processor1.processed_frame.connect(w.on_frame)
    # processor1.roi_frame.connect(lambda roi: cv2.imshow("ROI", roi))
    
    w.show()
    fg_thread = QThread()
    fg.moveToThread(fg_thread)
    fg_thread.started.connect(fg.run)
    fg_thread.start()
    app.exec()

