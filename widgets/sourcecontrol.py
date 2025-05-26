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
    QSlider,
)

from modes import VideoModes, VIDEOMODES_STR_MAP
from providers.source import FrameGrabber

class SourceControlWidget(QWidget):
    """
    The source control widget allows the user to:
    - Select the input source (webcam, video file, or image files).
    - Control playback or live feed.
    - Adjust the frame rate (FPS) for video playback.
    - Step through the video or images frame by frame.
    """
    sig_start = Signal()
    sig_pause = Signal()
    sig_update_fps = Signal(int)
    sig_source_change = Signal(str, VideoModes, list)
    sig_next = Signal()
    sig_reset = Signal()
    
    start_requested = Signal()
    stop_requested  = Signal()
    fps_changed     = Signal(int)
    step_requested  = Signal()  # <-- new signal for stepping through frames
    
    def __init__(self, parent=None):
        super().__init__(parent)
        if parent is None:
            self.setWindowTitle("Source Controls")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)  # Align at the top of the parent widget
        box = QGroupBox("Source Controls")
        form = QFormLayout()

        # Input Source combo
        self.source_selector = QComboBox()
        for mode, label in VIDEOMODES_STR_MAP.items():
            self.source_selector.addItem(label, mode)
        self.source_selector.currentIndexChanged.connect(self.sig_source_change)
        form.addRow("Input Source:", self.source_selector)

        # Control buttons
        btn_layout = QHBoxLayout()
        self.play_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.next_btn = QPushButton("Next")
        self.reset_btn = QPushButton("Reset")
        for btn in (
            self.play_btn,
            self.pause_btn,
            self.next_btn,
            self.reset_btn
        ):
            btn_layout.addWidget(btn)
        self.play_btn.clicked.connect(self.sig_start)
        self.pause_btn.clicked.connect(self.sig_pause)
        self.next_btn.clicked.connect(self.sig_next)
        self.reset_btn.clicked.connect(self.sig_reset)
        form.addRow(btn_layout)
        box.setLayout(form)
        main_layout.addWidget(box)

        # FPS slider
        fps_box = QGroupBox("FPS")
        fps_layout = QHBoxLayout()
        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setRange(1, 60)
        self.fps_slider.setValue(24)
        self.fps_slider.setTickPosition(QSlider.TicksBelow)
        self.fps_slider.setTickInterval(10)
        self.fps_label = QLabel(f"{self.fps_slider.value()} FPS")
        # update label and emit fps_changed
        self.fps_slider.valueChanged.connect(lambda v: self.fps_label.setText(f"{v} FPS"))
        self.fps_slider.valueChanged.connect(self.sig_update_fps)
        fps_layout.addWidget(self.fps_slider)
        fps_layout.addWidget(self.fps_label)
        fps_box.setLayout(fps_layout)
        main_layout.addWidget(fps_box)
        
        # Path display
        self.path_label = QLabel("", alignment=Qt.AlignLeft)
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.path_label)
    
    @Slot(int)
    def sig_source_change(self, index):
        # Get the mode from the combo box (based on the selected index)
        mode = self.source_selector.itemData(index)
        self.change_source(self.source_selector.currentIndex(), mode)
        
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
    # connect step_requested to the method that handles the step-by-step behavior
    # w.step_requested.connect(grabber.step)  # Implement the step method in your FrameGrabber
    w.show()
    sys.exit(app.exec())
