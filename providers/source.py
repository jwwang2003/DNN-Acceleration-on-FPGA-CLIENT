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
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._grab_frame)

        # initial setup
        self._fps = fps
        self._update_interval()

        # set up attrs
        self.source = source
        self.mode = mode
        self.manual = manual
        self.image_list = image_list or []
        self.image_index = 0
        self.cam: cv2.VideoCapture | None = None

        if mode in (VideoModes.WEBCAM, VideoModes.VIDEO):
            self.init_camera(source)

    def init_camera(self, source: int):
        self.cam = cv2.VideoCapture(source)
        if not self.cam.isOpened():
            raise RuntimeError(f"Cannot open {self.mode.name} source {source}")

    def _update_interval(self):
        interval_ms = max(1, int(1000 / self._fps))
        self._timer.setInterval(interval_ms)

    @Slot()
    def run(self):
        if not self._timer.isActive():
            self._timer.start()
        if self.mode in (VideoModes.WEBCAM, VideoModes.VIDEO) and not self.cam:
            self.init_camera(self.source)

    @Slot()
    def stop(self):
        self._timer.stop()
        # note: we keep cam around until change_source to avoid flicker

    @Slot(int)
    def set_fps(self, fps: int):
        if fps <= 0:
            return
        self._fps = fps
        self._update_interval()
        if self._timer.isActive():
            self._timer.start()

    def _grab_frame(self):
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

    @Slot(int, object, list)
    def change_source(self, source, mode, image_list=None):
        """
        Switch to a new input source *in-place*.
        If we were grabbing, it will restart on the new source.
        """
        was_running = self._timer.isActive()
        self.stop()

        # release old camera if any
        if self.cam:
            self.cam.release()
            self.cam = None

        # update attrs
        self.source = source
        self.mode = mode
        self.image_list = image_list or []
        self.image_index = 0

        # init new source if needed
        if mode in (VideoModes.WEBCAM, VideoModes.VIDEO):
            self.init_camera(source)

        # restart if we were running
        if was_running:
            self.run()