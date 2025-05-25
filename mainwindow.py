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
from processors import PreProcessorBase, BoundingBox, ROIFilter
from widgets import VideoWidget, SourceControlWidget, ROIViewerWidget
from tcp import TCPWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DNN-Acceleration-on-FPGA-CLIENT")

        self.source_mode: VideoModes = VideoModes.WEBCAM

        # Main layout
        main_layout = QHBoxLayout()       
        
        # Left side: Video display & ROI 
        self.left_panel = QVBoxLayout()
        self.video_widget = VideoWidget()
        self.roi_filter = ROIFilter()
        self.roi_viewer = ROIViewerWidget()
        self.left_panel.addWidget(self.video_widget, stretch=4)
        self.left_panel.addWidget(self.roi_viewer, stretch=1)

        main_layout.addLayout(self.left_panel, stretch=3)

        # Initialize the FrameGrabber
        self.processor1 = BoundingBox()
        # connect the ROI signal
        # 2) filter emits List[np.ndarray] → viewer.set_rois
        self.processor1.roi_frames.connect(self.roi_filter.on_rois)
        self.roi_filter.filtered_rois.connect(self.roi_viewer.set_rois)

        # if you want to clear for each new frame batch:
        # self.processor1.processed_frame.connect(self.roi_viewer.clear)
        self._start_grabber()
        # Start preprocessor for bounding boxes
        self.grabber.frame_ready.connect(self.processor1.on_frame)
        # self.grabber.frame_ready.connect(self.roi_viewer.clear)
        self.processor1.processed_frame.connect(self.video_widget.on_frame)
        
        # Side panel
        self.source_control = SourceControlWidget(source_change_callback=self._start_grabber)
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
        
        container = QWidget()
        container.setLayout(main_layout)

        self.setCentralWidget(container)
        
    def _start_grabber(self, source: int=0, mode: VideoModes=VideoModes.WEBCAM, image_list=None):
        if hasattr(self, 'grabber') and self.grabber is not None:
            self.grabber.frame_ready.disconnect()
            self.grabber.stop()
            self.thread.quit()
            self.thread.wait()
        self.grabber = FrameGrabber(source, mode, image_list=image_list)
        self.thread = QThread(self)
        self.grabber.moveToThread(self.thread)
        self.grabber.frame_ready.connect(self.processor1.on_frame)
        self.thread.started.connect(self.grabber.run)
        self.thread.start()
        self.source_mode = mode
    