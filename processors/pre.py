import cv2

from PySide6.QtCore import (QObject, Signal, Slot)


class PreProcessorBase(QObject):
    """Abstract base for frame processors."""
    processed_frame = Signal(object)

    def __init__(self, enabled: bool = True):
        super().__init__()
        self.enabled = enabled

    @Slot(object)
    def on_frame(self, frame):
        # Default: pass-through
        self.processed_frame.emit(frame)

class BoundingBox(PreProcessorBase):
    """Bounding box processor."""
    
    roi_frame = Signal(object)  # ROI -> region of interest
    
    def __init__(self, min_area: int = 5000, enabled: bool = True):
        super().__init__(enabled)
        self.min_area = min_area
        self.bbox = None
    
    @Slot(object)
    def on_frame(self, frame):
        # Check if current preprocessing layer is enabled
        if not self.enabled:
            # Pass-through if not enabled
            self.processed_frame.emit(frame)
            return

        # Convert BGR to grayscale:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Threshold via Otsu (invert so foreground=white):
        _, binary = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        # Flood-fill the border to remove any border-connected region
        cv2.floodFill(binary, None, (0,0), 0)

        # Find external contours
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        out = frame.copy()  # Copy of the original frame for drawing (displaying)
        h_img, w_img = frame.shape[:2]
        for c in contours:
            x,y,w,h = cv2.boundingRect(c)
            if w*h < self.min_area:
                continue
            
            # Make the box square by expanding the smaller side
            size = max(w, h)
            cx = x + w // 2
            cy = y + h // 2

            # New top-left corner for the square
            x1 = int(cx - size // 2)
            y1 = int(cy - size // 2)

            # Clamp to image bounds
            x1 = max(x1, 0)
            y1 = max(y1, 0)
            x2 = min(x1 + size, w_img)
            y2 = min(y1 + size, h_img)

            # Draw the square on a copy (out)
            cv2.rectangle(
                out,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )
            
            # Extract the square ROI
            roi = frame[y1:y2, x1:x2]
            
            # Downscale to 32×32
            # smallROI = cv2.resize(roi, (32, 32), interpolation=cv2.INTER_AREA)
            # Convert to grayscale
            # smallGray = cv2.cvtColor(smallROI, cv2.COLOR_BGR2GRAY)
            # NOTE: leave further processing for another processing element
            self.roi_frame.emit(roi)    # Emit the ROI for further processing
        self.processed_frame.emit(out)  # Emit the processed frame with bounding boxes
