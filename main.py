import sys
from PySide6.QtWidgets import QApplication

from mainwindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1400, 800)
    w.show()
    sys.exit(app.exec())

# import sys
# import cv2
# from PySide6.QtCore import Qt, QThread, Slot
# from PySide6.QtGui import QImage, QPixmap
# from PySide6.QtWidgets import (
#     QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel, QVBoxLayout
# )

# from modes import VideoModes, VIDEOMODES_STR_MAP
# from widgets import SourceControlWidget
# from providers import FrameGrabber


# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("TCP / FrameGrabber Test")

#         # ——— UI setup ——————————————————————————————
#         container = QWidget()
#         layout = QHBoxLayout(container)

#         # 1) Video display
#         self.video_label = QLabel("No Frame")
#         self.video_label.setFixedSize(640, 480)
#         self.video_label.setAlignment(Qt.AlignCenter)
#         layout.addWidget(self.video_label, 3)

#         # 2) Source controls
        
#         self.setCentralWidget(container)

#         # ——— FrameGrabber + thread ——————————————————————
#         self._setup_grabber(
#             source=0,
#             mode=VideoModes.WEBCAM,
#             image_list=[]
#         )
        
#         self.controls = SourceControlWidget(frame_grabber=self.grabber)
#         layout.addWidget(self.controls, 1)


#         # ——— Wire buttons / signals —————————————————————————
#         self.controls.start_button.clicked.connect(self.grabber.start)
#         self.controls.stop_button.clicked.connect(self.grabber.stop)
#         self.controls.next_frame_button.clicked.connect(self.grabber.next_frame)
#         self.controls.reset_button.clicked.connect(self._reset_grabber)
#         self.controls.source_selector.currentIndexChanged.connect(
#             self._on_source_change
#         )

#     def _setup_grabber(self, source, mode, image_list):
#         """Instantiate a new grabber + QThread, hook up signals."""
#         # clean up old thread if any
#         try:
#             self.grabber.stop()
#             self._thread.quit()
#             self._thread.wait()
#         except AttributeError:
#             pass

#         self._thread = QThread(self)
#         self.grabber = FrameGrabber(source=source, mode=mode, image_list=image_list)
#         self.grabber.moveToThread(self._thread)

#         # when thread starts, enter its run loop
#         self._thread.started.connect(self.grabber.run)
#         # connect frame output
#         self.grabber.frame_ready.connect(self._on_frame_ready)

#         self._thread.start()

#     @Slot(object)
#     def _on_frame_ready(self, frame):
#         """Convert BGR ndarray to QPixmap and show it."""
#         h, w, ch = frame.shape
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         qt_img = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
#         self.video_label.setPixmap(QPixmap.fromImage(qt_img))

#     @Slot()
#     def _reset_grabber(self):
#         """Reset video back to start or image index to zero."""
#         if self.grabber.mode == VideoModes.VIDEO:
#             self.grabber.cam.set(cv2.CAP_PROP_POS_FRAMES, 0)
#         elif self.grabber.mode == VideoModes.IMAGES:
#             self.grabber.image_index = 0

#     @Slot(int)
#     def _on_source_change(self, idx):
#         """Recreate the grabber whenever the user picks a new source."""
#         mode = self.controls.source_selector.itemData(idx)
#         paths = getattr(self.controls, "selected_paths", None) or []

#         if mode == VideoModes.WEBCAM:
#             source, imgs = 0, []
#         elif mode == VideoModes.VIDEO:
#             source, imgs = paths[0], []
#         elif mode == VideoModes.IMAGES:
#             source, imgs = 0, paths
#         else:
#             return

#         # restart grabber with new config
#         self._setup_grabber(source=source, mode=mode, image_list=imgs)

#     def closeEvent(self, event):
#         # ensure clean shutdown
#         self.grabber.stop()
#         self._thread.quit()
#         self._thread.wait()
#         super().closeEvent(event)


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     w = MainWindow()
#     w.resize(1200, 600)
#     w.show()
#     sys.exit(app.exec())

