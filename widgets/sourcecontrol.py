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
)

from modes import VideoModes, VIDEOMODES_STR_MAP
from providers.source import FrameGrabber

class SourceControlWidget(QWidget):
    start_requested = Signal()
    stop_requested  = Signal()
    
    def __init__(self, parent=None, source_change_callback=None):
        super().__init__(parent)
        if parent is None:
            self.setWindowTitle("Source Control")
        
        self.source_change_callback = source_change_callback or (lambda source, mode: None)
        
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        box = QGroupBox("Source Controls")
        form = QFormLayout()

        # 1) The combo box populated by our enum
        self.source_selector = QComboBox()
        for mode, label in VIDEOMODES_STR_MAP.items():
            # store the enum in userData()
            self.source_selector.addItem(label, mode)
        self.source_selector.currentIndexChanged.connect(self.on_source_change)
        form.addRow("Input Source:", self.source_selector)
        
        # 2) Control buttons
        btn_layout = QHBoxLayout()
        self.play_btn  = QPushButton("►")
        self.pause_btn = QPushButton("❚❚")
        self.play_btn.clicked.connect(self.start_requested)
        self.pause_btn.clicked.connect(self.stop_requested)
        
        self.next_frame_button  = QPushButton("Next Frame")
        self.reset_button       = QPushButton("Reset")
        for btn in (self.play_btn,
                    self.pause_btn,
                    self.next_frame_button,
                    self.reset_button):
            btn_layout.addWidget(btn)
        form.addRow(btn_layout)

        box.setLayout(form)
        main_layout.addWidget(box)
        
        # Below the controls: a grey label for showing selected path(s)
        self.path_label = QLabel("", alignment=Qt.AlignLeft)
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.path_label)

    @Slot(int)
    def on_source_change(self, index):
        """Handle source changes via the VideoModes enum."""
        mode = self.source_selector.itemData(index)
        # Clear any previous selections
        self.selected_paths = None
        self.path_label.clear()

        if mode == VideoModes.WEBCAM:
            # nothing else to do
            self.source_change_callback(mode=VideoModes.WEBCAM)
            return

        if mode == VideoModes.VIDEO:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Video File",
                "",
                "Video Files (*.mp4 *.avi *.mov)"
            )
            if path:
                self.selected_paths = [path]
                self.source_change_callback(source=path, mode=VideoModes.VIDEO)

        elif mode == VideoModes.IMAGES:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Image Files",
                "",
                "Image Files (*.png *.jpg *.jpeg)"
            )
            if files:
                self.selected_paths = files
                self.source_change_callback(source=files, mode=VideoModes.IMAGES)

        self._update_path_label()

    def _update_path_label(self):
        """Show one or more paths in the gray label below the controls."""
        if not self.selected_paths:
            self.path_label.clear()
        else:
            display = "\n".join(self.selected_paths)
            self.path_label.setText(f"Selected:\n{display}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = SourceControlWidget()
    w.resize(500, 200)
    w.show()
    sys.exit(app.exec())