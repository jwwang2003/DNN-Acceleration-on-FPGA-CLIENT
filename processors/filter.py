import cv2
from PySide6.QtCore import QObject, Signal, Slot

class ROIFilter(QObject):
    """
    Takes a list of BGR ROIs, converts each to 32×32 gray, and emits the batch.
    """
    filtered_rois = Signal(list)  # will carry List[np.ndarray]

    @Slot(list)
    def on_rois(self, rois):
        processed = []
        for roi in rois:
            # 1) grayscale
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            # 2) resize to 32×32
            small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
            # 3) back to BGR so ROIViewerWidget can treat it uniformly
            bgr = cv2.cvtColor(small, cv2.COLOR_GRAY2BGR)
            processed.append(bgr)
        # emit all at once
        self.filtered_rois.emit(processed)
