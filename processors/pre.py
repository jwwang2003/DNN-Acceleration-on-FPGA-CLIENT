import cv2
from PySide6.QtCore import QObject, Signal, Slot


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
    """Bounding box processor with max‐ROI, size‐and‐boundary filtering."""
    
    roi_frames = Signal(list)
    
    def __init__(self, min_area: int = 5000, max_rois: int = 4, max_frac: float = 0.45, enabled: bool = True):
        super().__init__(enabled)
        self.min_area = min_area
        self.max_rois = max_rois
        self.max_frac = max_frac  # maximum allowed fraction of frame area
    
    @Slot(object)
    def on_frame(self, frame):
        if not self.enabled:
            self.processed_frame.emit(frame)
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        cv2.floodFill(binary, None, (0, 0), 0)

        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        h_img, w_img = frame.shape[:2]
        total_area = w_img * h_img

        # 1) collect candidate boxes
        boxes = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            area = w * h
            if area < self.min_area:
                continue

            # make it square
            size = max(w, h)
            cx, cy = x + w // 2, y + h // 2
            x1 = max(int(cx - size // 2), 0)
            y1 = max(int(cy - size // 2), 0)
            x2 = min(x1 + size, w_img)
            y2 = min(y1 + size, h_img)

            # 2) skip if covers > max_frac of the frame
            if (size * size) / float(total_area) > self.max_frac:
                continue

            # 3) skip if touching any boundary
            if x1 == 0 or y1 == 0 or x2 == w_img or y2 == h_img:
                continue

            boxes.append((x1, y1, x2, y2))

        # 4) if too many ROIs, bail out entirely
        if len(boxes) > self.max_rois:
            self.processed_frame.emit(frame)
            return

        # 5) otherwise draw & emit each ROI
        out = frame.copy()
        rois = []
        for x1, y1, x2, y2 in boxes:
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)
            roi = frame[y1:y2, x1:x2]
            rois.append(roi)
        
        self.roi_frames.emit(rois)
        self.processed_frame.emit(out)