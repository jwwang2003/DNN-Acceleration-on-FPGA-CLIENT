import cv2
from PySide6.QtCore import QObject, Signal, Slot

class ROIFilter(QObject):
    """
    Takes a list of BGR ROIs, converts each to 32×32 gray, increases contrast, inverts the colors,
    and emits the batch.
    """
    filtered_rois = Signal(list)  # will carry List[np.ndarray]

    @Slot(list)
    def on_rois(self, rois):
        processed = []
        for roi in rois:
            # 1) Convert to grayscale
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # 2) Increase contrast (using convertScaleAbs with a factor of 2)
            contrast = cv2.convertScaleAbs(gray, alpha=2.0, beta=0)

            # 3) Invert colors (make the digits bright and background black)
            inverted = cv2.bitwise_not(contrast)

            # 4) Resize to 32×32
            small = cv2.resize(inverted, (32, 32), interpolation=cv2.INTER_AREA)

            # 5) Convert back to BGR for uniformity in ROIViewerWidget
            bgr = cv2.cvtColor(small, cv2.COLOR_GRAY2BGR)

            processed.append(bgr)

        # Emit all processed ROIs at once
        self.filtered_rois.emit(processed)
