import cv2

from PySide6.QtCore import Qt, QTimer, QThread, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
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
)

from providers import FrameGrabber

class VideoWidget(QWidget):
    def __init__(self, cam_id=0, parent=None, target_fps=30):
        super().__init__(parent)
        self.setWindowTitle("OpenCV Feed with Controls")

        # Video display label
        self.video_label = QLabel(alignment=Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMinimumSize(1, 1)
        self.last_pixmap = None

        # Side controls
        self.controls_box = self._create_controls_box()

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.video_label, stretch=3)
        main_layout.addWidget(self.controls_box, stretch=1)

        # Threaded frame grabber
        self.grabber = FrameGrabber(cam_id)
        self.thread = QThread(self)
        self.grabber.moveToThread(self.thread)
        self.grabber.frame_ready.connect(self.on_frame)
        self.thread.started.connect(self.grabber.run)
        self.thread.start()

        # Timer to refresh display at fixed rate
        interval = int(1000/target_fps)
        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(interval)

    def _create_controls_box(self):
        box = QGroupBox("Connection Settings & Info")
        form = QFormLayout()

        # Server address input
        self.server_input = QLineEdit("127.0.0.1")
        form.addRow("Server Address:", self.server_input)

        # Port input
        self.port_input = QLineEdit("8080")
        form.addRow("Port:", self.port_input)

        # Protocol radio buttons
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

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.on_connect)
        form.addRow(self.connect_button)

        # Server message display
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        form.addRow("Server Message:", self.message_display)

        # Points and leaderboard table
        self.leaderboard = QTableWidget(0, 2)
        self.leaderboard.setHorizontalHeaderLabels(["User", "Points"])
        form.addRow("Leaderboard:", self.leaderboard)

        # Debug button
        self.debug_button = QPushButton("Debug")
        self.debug_button.clicked.connect(self.on_debug)
        form.addRow(self.debug_button)

        box.setLayout(form)
        return box

    @Slot(object)
    def on_frame(self, frame):
        self.latest_frame = frame

    def update_display(self):
        if hasattr(self, 'latest_frame'):
            frame = self.latest_frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.last_pixmap = QPixmap.fromImage(qt_image)
            scaled = self.last_pixmap.scaled(
                self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label.setPixmap(scaled)

    def resizeEvent(self, event):
        if self.last_pixmap:
            scaled = self.last_pixmap.scaled(
                self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label.setPixmap(scaled)
        super().resizeEvent(event)

    @Slot()
    def on_connect(self):
        address = self.server_input.text()
        port = self.port_input.text()
        protocol = 'TCP' if self.tcp_radio.isChecked() else 'UDP'
        print(f"Connecting to {address}:{port} via {protocol}")
        # TODO: implement actual connection logic

    @Slot()
    def on_debug(self):
        print("Debug info:")
        print(f"Server: {self.server_input.text()}:{self.port_input.text()}")
        print(f"Protocol: {'TCP' if self.tcp_radio.isChecked() else 'UDP'}")
        # TODO: add more debug outputs

    def closeEvent(self, event):
        self.grabber.stop()
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)