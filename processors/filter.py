import cv2
from PySide6.QtCore import QObject, Signal, Slot

class ROIFilter(QObject):
    """
    Takes a list of BGR ROIs, converts each to 32×32 gray, increases contrast,
    inverts colors, adds thickness, pads 3px on each side, and emits the batch.
    """
    filtered_rois = Signal(list)  # will carry List[np.ndarray]

    @Slot(list)
    def on_rois(self, rois):
        processed = []
        for roi in rois:
            # 1) Grayscale
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # 2) Increase contrast
            contrast = cv2.convertScaleAbs(gray, alpha=2.0, beta=0)

            # 3) Invert colors
            inverted = cv2.bitwise_not(contrast)

            # 4) Thicken strokes via dilation
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (12, 12))
            thick   = cv2.dilate(inverted, kernel, iterations=1)

            # 5) Pad 3px border (black)
            padded = cv2.copyMakeBorder(
                thick,
                top=3, bottom=3,
                left=3, right=3,
                borderType=cv2.BORDER_CONSTANT,
                value=0
            )

            # 6) Resize back to 32×32
            small = cv2.resize(padded, (32, 32), interpolation=cv2.INTER_AREA)

            # 7) Convert back to BGR for uniform downstream handling
            bgr = cv2.cvtColor(small, cv2.COLOR_GRAY2BGR)

            processed.append(bgr)

        self.filtered_rois.emit(processed)
