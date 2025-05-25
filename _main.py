import sys
import cv2
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QLineEdit,
    QGroupBox,
    QFormLayout,
    QRadioButton,
    QButtonGroup,
    QTextEdit,
    QTableWidget,
    QDialog,
    QSpinBox,
    QDialogButtonBox,
    QComboBox,
    QFileDialog,
    QMainWindow
)

from windows import MainWindow

from providers.source import FrameGrabber

class DebugDialog(QDialog):
    fps_changed = Signal(int)

    def __init__(self, current_fps, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Debug Settings")
        layout = QFormLayout(self)

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(current_fps)
        layout.addRow("Target FPS:", self.fps_spin)
        self.fps_spin.valueChanged.connect(self.fps_changed)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class VideoPopup(QWidget):
    def __init__(self, grabber, target_fps):
        super().__init__()
        self.setWindowTitle("Detached Video View")
        self.grabber = grabber
        self.grabber.frame_ready.connect(self.on_frame)
        self.latest_frame = None
        self.last_pixmap = None

        self.label = QLabel(alignment=Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setMinimumSize(1, 1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label, stretch=1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_display)
        self.timer.start(int(1000/target_fps))

    @Slot(object)
    def on_frame(self, frame):
        self.latest_frame = frame

    def update_display(self):
        if self.latest_frame is None:
            return
        rgb = cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.last_pixmap = pixmap
        self._scale_pixmap()

    def resizeEvent(self, event):
        self._scale_pixmap()
        super().resizeEvent(event)

    def _scale_pixmap(self):
        if self.last_pixmap:
            scaled = self.last_pixmap.scaled(
                self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled)


class VideoWidget(QWidget):
    def __init__(self, cam_id=0, parent=None, target_fps=30):
        super().__init__(parent)
        self.setWindowTitle("OpenCV Feed with Controls")
        self.target_fps = target_fps
        self.source_mode = 'webcam'

        self.video_label = QLabel(alignment=Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMinimumSize(1, 1)
        self.last_pixmap = None

        self.controls_box = self._create_controls_box()

        layout = QHBoxLayout(self)
        layout.addWidget(self.video_label, stretch=3)
        layout.addWidget(self.controls_box, stretch=1)

        self._start_grabber(cam_id, 'webcam')

        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_display)
        self._update_timer_interval()

    def _start_grabber(self, source, mode, image_list=None):
        if hasattr(self, 'grabber'):
            self.grabber.frame_ready.disconnect()
            self.grabber.stop()
            self.thread.quit()
            self.thread.wait()
        self.grabber = FrameGrabber(source, image_list=image_list)
        self.thread = QThread(self)
        self.grabber.moveToThread(self.thread)
        self.grabber.frame_ready.connect(self.on_frame)
        self.thread.started.connect(self.grabber.run)
        self.thread.start()
        self.source_mode = mode

    def _update_timer_interval(self):
        self.display_timer.start(int(1000/self.target_fps))

    def _create_controls_box(self):
        box = QGroupBox("Connection & Controls")
        form = QFormLayout()

        self.source_selector = QComboBox()
        self.source_selector.addItems(["webcam", "images", "video file"])
        self.source_selector.currentTextChanged.connect(self.on_source_change)
        form.addRow("Input Source:", self.source_selector)

        self.server_input = QLineEdit("127.0.0.1")
        form.addRow("Server Address:", self.server_input)

        self.port_input = QLineEdit("8080")
        form.addRow("Port:", self.port_input)

        proto_layout = QHBoxLayout()
        self.tcp_radio = QRadioButton("TCP")
        self.udp_radio = QRadioButton("UDP")
        self.tcp_radio.setChecked(True)
        proto_group = QButtonGroup(box)
        proto_group.addButton(self.tcp_radio)
        proto_group.addButton(self.udp_radio)
        proto_layout.addWidget(self.tcp_radio)
        proto_layout.addWidget(self.udp_radio)
        form.addRow("Protocol:", proto_layout)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.on_connect)
        form.addRow(self.connect_button)

        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        form.addRow("Server Msg:", self.message_display)

        self.leaderboard = QTableWidget(0, 2)
        self.leaderboard.setHorizontalHeaderLabels(["User", "Points"])
        form.addRow("Leaderboard:", self.leaderboard)

        self.debug_button = QPushButton("Debug")
        self.debug_button.clicked.connect(self.on_debug)
        form.addRow(self.debug_button)

        self.popup_button = QPushButton("Pop Out Video")
        self.popup_button.clicked.connect(self.on_popup)
        form.addRow(self.popup_button)

        box.setLayout(form)
        return box

    @Slot(object)
    def on_frame(self, frame):
        self.latest_frame = frame

    def update_display(self):
        if hasattr(self, 'latest_frame'):
            rgb = cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            image = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.last_pixmap = pixmap
            self._scale_main_pixmap()

    def resizeEvent(self, event):
        self._scale_main_pixmap()
        super().resizeEvent(event)

    def _scale_main_pixmap(self):
        if self.last_pixmap:
            scaled = self.last_pixmap.scaled(
                self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label.setPixmap(scaled)

    @Slot(str)
    def on_source_change(self, text):
        if text == 'webcam':
            self._start_grabber(0, 'webcam')
        elif text == 'video file':
            path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi)")
            if path:
                self._start_grabber(path, 'video')
        elif text == 'images':
            files, _ = QFileDialog.getOpenFileNames(self, "Select Image Files", "", "Images (*.png *.jpg)")
            if files:
                self._start_grabber(None, 'images', files)

    @Slot()
    def on_connect(self):
        print(f"Connect to {self.server_input.text()}:{self.port_input.text()}")

    @Slot()
    def on_debug(self):
        dlg = DebugDialog(self.target_fps, self)
        dlg.fps_changed.connect(self._set_fps)
        dlg.open()

    @Slot(int)
    def _set_fps(self, fps):
        self.target_fps = fps
        self._update_timer_interval()
        print(f"FPS set to {fps}")

    @Slot()
    def on_popup(self):
        self.popup = VideoPopup(self.grabber, self.target_fps)
        self.popup.resize(640, 480)
        self.popup.show()

    def closeEvent(self, event):
        self.grabber.stop()
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1200, 600)
    w.show()
    sys.exit(app.exec())
