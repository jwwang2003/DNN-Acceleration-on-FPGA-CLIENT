import sys

from PySide6.QtCore import QThread

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
)

from modes import VideoModes
from providers import FrameGrabber
from processors import PreProcessorBase, BoundingBox
from widgets import VideoWidget, SourceControlWidget
from tcp import TCPWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FPGA Client")

        
        
        # Setting up proprocessor(s)
        
        # 1) Create your layout
        main_layout = QHBoxLayout()
        self.video_widget = VideoWidget()
        # Initialize the FrameGrabber
        self._start_grabber()
        self.source_control = SourceControlWidget(source_change_callback=self._start_grabber)
        
        self.source_control.start_requested.connect(self.grabber.start)
        self.source_control.stop_requested.connect(self.thread.quit)

        self.processor1 = BoundingBox(min_area=5000)
        self.grabber.frame_ready.connect(self.processor1.on_frame)
        self.processor1.processed_frame.connect(self.video_widget.on_frame)
        
        main_layout.addWidget(self.video_widget, stretch=3)
        
        # Side panel
        def on_tcp_state_changed(connected: bool):
            if connected:
                print("Global: TCP is now connected!")
            else:
                print("Global: TCP disconnected.")

        self.tcp_widget = TCPWidget()
        self.tcp_widget.state_changed.connect(on_tcp_state_changed)
        self.side_panel = QVBoxLayout()
        self.side_panel.addWidget(self.source_control)
        self.side_panel.addWidget(self.tcp_widget)
        
        main_layout.addLayout(self.side_panel, stretch=1)
        
        # 2) Wrap layout in a QWidget
        container = QWidget()
        container.setLayout(main_layout)
        
        # 3) Set that QWidget as central
        self.setCentralWidget(container)
        
        # Start the frame grabber in a separate thread
        self.video_widget.show()
        
    def _start_grabber(self, source: int=0, mode: VideoModes=VideoModes.WEBCAM, image_list=None):
        if hasattr(self, 'grabber'):
            self.grabber.frame_ready.disconnect()
            self.grabber.stop()
            self.thread.quit()
            self.thread.wait()
        self.grabber = FrameGrabber(source, mode, image_list=image_list)
        self.thread = QThread(self)
        self.grabber.moveToThread(self.thread)
        self.grabber.frame_ready.connect(self.video_widget.on_frame)
        self.thread.started.connect(self.grabber.run)
        self.thread.start()
        self.source_mode = mode
    