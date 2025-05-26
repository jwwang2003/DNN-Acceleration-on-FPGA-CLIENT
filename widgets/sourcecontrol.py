import sys
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QVBoxLayout,
    QWidget,
    QGroupBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QSlider,           # <-- import QSlider
)

from modes import VideoModes, VIDEOMODES_STR_MAP
from providers.source import FrameGrabber

class SourceControlWidget(QWidget):
    start_requested = Signal()
    stop_requested  = Signal()
    fps_changed     = Signal(int)        # <-- new signal

    def __init__(self, parent=None, play=None, stop=None, source_change_callback=None):
        super().__init__(parent)
        if parent is None:
            self.setWindowTitle("Source Control")
        
        self.source_change_callback = source_change_callback or (lambda **kwargs: None)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        box = QGroupBox("Source Controls")
        form = QFormLayout()

        # 1) Input Source combo
        self.source_selector = QComboBox()
        for mode, label in VIDEOMODES_STR_MAP.items():
            self.source_selector.addItem(label, mode)
        self.source_selector.currentIndexChanged.connect(self.on_source_change)
        form.addRow("Input Source:", self.source_selector)
        
        # 2) Playback buttons
        btn_layout = QHBoxLayout()
        self.play_btn  = QPushButton("►")
        self.pause_btn = QPushButton("❚❚")
        self.play_btn.pressed.connect(play)
        self.pause_btn.pressed.connect(stop)
        self.play_btn.clicked.connect(self.start_requested)
        self.pause_btn.clicked.connect(self.stop_requested)

        self.next_frame_button = QPushButton("Next Frame")
        self.reset_button      = QPushButton("Reset")
        for btn in (
            self.play_btn,
            self.pause_btn,
            self.next_frame_button,
            self.reset_button
        ):
            btn_layout.addWidget(btn)
        form.addRow(btn_layout)

        box.setLayout(form)
        main_layout.addWidget(box)
        
        # 3) Path display
        self.path_label = QLabel("", alignment=Qt.AlignLeft)
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.path_label)

        # 4) FPS slider
        fps_box = QGroupBox("Frame Rate")
        fps_layout = QHBoxLayout()
        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setRange(1, 120)
        self.fps_slider.setValue(60)
        self.fps_slider.setTickPosition(QSlider.TicksBelow)
        self.fps_slider.setTickInterval(10)

        self.fps_label = QLabel(f"{self.fps_slider.value()} FPS")
        # update label and emit fps_changed
        self.fps_slider.valueChanged.connect(lambda v: self.fps_label.setText(f"{v} FPS"))
        self.fps_slider.valueChanged.connect(self.fps_changed)

        fps_layout.addWidget(self.fps_slider)
        fps_layout.addWidget(self.fps_label)
        fps_box.setLayout(fps_layout)
        main_layout.addWidget(fps_box)

    @Slot(int)
    def on_source_change(self, index):
        mode = self.source_selector.itemData(index)
        self.selected_paths = None
        self.path_label.clear()

        if mode == VideoModes.WEBCAM:
            self.source_change_callback(mode=mode)
            return

        if mode == VideoModes.VIDEO:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)"
            )
            if path:
                self.selected_paths = [path]
                self.source_change_callback(source=path, mode=mode)

        elif mode == VideoModes.IMAGES:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select Image Files", "", "Image Files (*.png *.jpg *.jpeg)"
            )
            if files:
                self.selected_paths = files
                self.source_change_callback(source=files, mode=mode, image_list=files)

        self._update_path_label()

    def _update_path_label(self):
        if not getattr(self, "selected_paths", None):
            self.path_label.clear()
        else:
            self.path_label.setText("Selected:\n" + "\n".join(self.selected_paths))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = SourceControlWidget()
    w.resize(500, 300)
    # Example: connect the fps_changed signal to your FrameGrabber.set_fps
    # grabber = FrameGrabber(...)
    # w.fps_changed.connect(grabber.set_fps)
    w.show()
    sys.exit(app.exec())
