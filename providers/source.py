import cv2
from PySide6.QtCore import Signal, QObject, QThread, Slot

from modes import VideoModes


class FrameGrabber(QObject):
    frame_ready = Signal(object)

    def __init__(
        self,
        source: int = 0,
        mode: VideoModes = VideoModes.WEBCAM,
        image_list=None,
        manual: bool = False
    ):
        super().__init__()
        self.mode = mode
        self.manual = manual
        self.running = False
        self.image_list = image_list or []
        self.image_index = 0

        if mode in (VideoModes.WEBCAM, VideoModes.VIDEO):
            self.cam = cv2.VideoCapture(source)
            if not self.cam.isOpened():
                raise RuntimeError(f"Cannot open {mode.name} source {source}")
        else:
            self.cam = None

    @Slot()
    def start(self):
        """Begin the capture loop in its own QThread."""
        self.running = True

    @Slot()
    def stop(self):
        """Stop the loop and release any camera/video handle."""
        self.running = False
        if self.cam:
            self.cam.release()

    @Slot()
    def next_frame(self):
        """Manually advance one frame (VIDEO or IMAGES only)."""
        if self.mode in (VideoModes.VIDEO, VideoModes.IMAGES):
            self._grab_frame()

    @Slot()
    def capture_frame(self):
        """Manually grab one frame from the webcam."""
        if self.mode == VideoModes.WEBCAM:
            self._grab_frame()

    def run(self):
        """Automatic loop for non-manual modes."""
        self.running = True
        while self.running:
            if (self.mode in (VideoModes.WEBCAM, VideoModes.VIDEO) and not self.manual) \
               or self.mode == VideoModes.IMAGES:
                self._grab_frame()
            # QThread.msleep(int(1000/30))  # ~30 FPS
        if self.cam:
            self.cam.release()

    def _grab_frame(self):
        """Internal single‐frame grab & emit."""
        if self.mode in (VideoModes.WEBCAM, VideoModes.VIDEO):
            ret, frame = self.cam.read()
            if not ret:
                if self.mode == VideoModes.VIDEO:
                    # loop back to start of video
                    self.cam.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cam.read()
                else:
                    return
            if ret:
                self.frame_ready.emit(frame)

        elif self.mode == VideoModes.IMAGES:
            if not self.image_list:
                return
            path = self.image_list[self.image_index]
            frame = cv2.imread(path)
            if frame is None:
                return
            self.frame_ready.emit(frame)
            # advance index (wrap around)
            self.image_index = (self.image_index + 1) % len(self.image_list)