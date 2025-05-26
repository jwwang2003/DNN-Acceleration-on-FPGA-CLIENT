import cv2
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QThread

from modes import VideoModes


class FrameGrabber(QObject):
    frame_ready = Signal(object)

    def __init__(
        self,
        source: int = 0,
        mode: VideoModes = VideoModes.WEBCAM,
        image_list=None,
        manual: bool = False,
        fps: int = 60,
    ):
        super().__init__()
        self.mode = mode
        self.manual = manual
        self.image_list = image_list or []
        self.image_index = 0

        # store current FPS, default 60
        self._fps = fps

        # build timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._grab_frame)
        self._update_interval()

        self.source = source
        self.mode = mode
        self.cam: cv2.VideoCapture = None
        if mode in (VideoModes.WEBCAM, VideoModes.VIDEO):
            self.init_camera(source)
    
    def init_camera(self, source: int):
        # open camera if needed
        self.cam = cv2.VideoCapture(source)
        if not self.cam.isOpened():
            raise RuntimeError(f"Cannot open {self.mode.name} source {source}")

    def _update_interval(self):
        """Helper to recompute and set timer interval from self._fps."""
        interval_ms = max(1, int(1000 / self._fps))
        self._timer.setInterval(interval_ms)

    @Slot()
    def run(self):
        """Start grabbing at whatever FPS is currently set."""
        if not self._timer.isActive():
            self._timer.start()
        if not self.cam:
            self.init_camera(self.source)
        

    @Slot()
    def stop(self):
        """Stop grabbing, release resources, and quit thread."""
        self._timer.stop()
        if self.cam:
            pass
            # self.cam.release()
        # QThread.currentThread().quit()

    @Slot(int)
    def set_fps(self, fps: int):
        """Change FPS on the fly. Recalculates interval immediately."""
        if fps <= 0:
            return
        self._fps = fps
        self._update_interval()
        # if the timer is already running, apply the new interval immediately
        if self._timer.isActive():
            self._timer.start()

    def _grab_frame(self):
        """Internal slot called each timeout to capture & emit a frame."""
        if self.mode in (VideoModes.WEBCAM, VideoModes.VIDEO):
            ret, frame = self.cam.read()
            if not ret and self.mode == VideoModes.VIDEO:
                self.cam.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cam.read()
            if ret:
                self.frame_ready.emit(frame)

        elif self.mode == VideoModes.IMAGES:
            if not self.image_list:
                return
            path = self.image_list[self.image_index]
            frame = cv2.imread(path)
            if frame is not None:
                self.frame_ready.emit(frame)
            self.image_index = (self.image_index + 1) % len(self.image_list)
