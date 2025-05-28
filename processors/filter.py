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

            # 3) Threshold the image to separate both dark and light regions
            # Threshold the contrast image to create a binary image where both dark and light regions are separated
            _, thresholded = cv2.threshold(contrast, 175, 255, cv2.THRESH_BINARY)

            # 4) Denoise and thicken strokes via dilation (works on both black and white regions)
            # Invert the image so that dilation can work on both black and white regions
            inverted = cv2.bitwise_not(thresholded)

            # Dilation: Expanding both black and white regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))  # Smaller kernel
            dilated = cv2.dilate(inverted, kernel, iterations=2)  # Fewer iterations

            # 5) Invert back the image
            thickened = cv2.bitwise_not(dilated)

            # 6) Pad 3px border (black)
            padded = cv2.copyMakeBorder(
                thresholded,
                top=35, bottom=35,
                left=35, right=35,
                borderType=cv2.BORDER_CONSTANT,
                value=255  # White padding
            )

            # 7) Resize back to 32×32
            small = cv2.resize(padded, (32, 32), interpolation=cv2.INTER_AREA)

            # 8) Convert back to BGR for uniform downstream handling
            bgr = cv2.cvtColor(small, cv2.COLOR_GRAY2BGR)

            processed.append(bgr)


        self.filtered_rois.emit(processed)
