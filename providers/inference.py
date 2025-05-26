# inference.py
import socket
import numpy as np
from PySide6.QtCore import QObject, QThread, Signal

class InferenceWorker(QThread):
    inference_complete = Signal()
    classification_result = Signal(int)  # emits the integer result per-ROI

    def __init__(self, host, port, rois):
        super().__init__()
        self.host = host
        self.port = port
        self.rois = rois  # list of 32×32 uint8 arrays

    def run(self):
        # 1) Open one persistent TCP connection
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
        except socket.error as e:
            print(f"[InferenceWorker] Failed to connect: {e}")
            self.inference_complete.emit()
            return

        # 2) Send each ROI as 4×1 KB packets of float32 data
        for roi in self.rois:
            # normalize & cast to float32
            arr = (roi.astype(np.float32) / 255.0).ravel()
            data = arr.tobytes()  # total length = 32×32×4 = 4096 bytes

            # send in 4 packets of 1024 bytes
            for i in range(4):
                start = 1024 * i
                end   = start + 1024
                sock.sendall(data[start:end])
                print(f"[InferenceWorker] Sent packet {i+1}/4")

                # for packets 1–3 wait for a 1 KB‐ack before proceeding
                if i < 3:
                    ack = sock.recv(1024)
                    print(f"[InferenceWorker] Received packet-ack: {ack!r}")

            # 3) After the 4th packet, wait for the final result
            result_bytes = sock.recv(1024)
            result = int.from_bytes(result_bytes, byteorder='little', signed=False)
            print(f"[InferenceWorker] Classification result: {result}")
            self.classification_result.emit(result)

        # 4) Clean up
        sock.close()
        self.inference_complete.emit()


class InferenceHandler(QObject):
    inference_complete = Signal()
    classification_result = Signal(int)

    def __init__(self, host='192.168.1.10', port=7):
        super().__init__()
        self.host = host
        self.port = port

    def send_rois(self, rois):
        """
        Kick off the worker thread to:
        - connect once,
        - stream each ROI in 4x1 KB packets with per-chunk ACKs,
        - read the final classification reply,
        - emit inference_complete when done.
        """
        if not rois:
            # nothing to send → go straight to resume
            self.inference_complete.emit()
            return

        worker = InferenceWorker(self.host, self.port, rois)
        worker.inference_complete.connect(self.inference_complete)
        worker.classification_result.connect(self.classification_result)
        worker.start()
