import socket
import numpy as np
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QLineEdit, QPushButton,
    QFormLayout, QHBoxLayout, QMessageBox
)


class TCPWidget(QWidget):
    """
    Blocking TCP client: connect/disconnect and send ROIs in-place.
    WARNING: all operations block the UI thread!
    """
    # Signals you already wire up:
    state_changed         = Signal(bool)    # True=connected, False=disconnected
    classification_result = Signal(int)     # each ROI’s result
    inference_complete    = Signal()        # after the last ROI
    error_occurred        = Signal(str)     # on any socket error

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sock = None

        # --- UI ---
        self.host_input    = QLineEdit("127.0.0.1")
        self.port_input    = QLineEdit("8000")
        self.port_input.setFixedWidth(80)
        self.connect_btn    = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)

        form = QFormLayout(self)
        form.addRow("Host:", self.host_input)
        form.addRow("Port:", self.port_input)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.connect_btn)
        btn_row.addWidget(self.disconnect_btn)
        form.addRow(btn_row)

        # --- Signals ---
        self.connect_btn.clicked.connect(self._on_connect)
        self.disconnect_btn.clicked.connect(self._on_disconnect)

    @Slot()
    def _on_connect(self):
        host = self.host_input.text().strip()
        try:
            port = int(self.port_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Port", "Port must be an integer.")
            return

        # disable UI while connecting
        self.connect_btn.setEnabled(False)
        self.host_input.setEnabled(False)
        self.port_input.setEnabled(False)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((host, port))
            self._sock = sock
            self._set_connected(True)
        except Exception as e:
            self.error_occurred.emit(str(e))
            QMessageBox.critical(self, "Connect Error", str(e))
            # restore UI
            self.connect_btn.setEnabled(True)
            self.host_input.setEnabled(True)
            self.port_input.setEnabled(True)

    @Slot()
    def _on_disconnect(self):
        if not self._sock:
            return

        try:
            self._sock.close()
            self._sock = None
            self._set_connected(False)
        except Exception as e:
            self.error_occurred.emit(str(e))
            QMessageBox.warning(self, "Disconnect Error", str(e))

    def _set_connected(self, state: bool):
        """Enable/disable UI elements and emit state_changed."""
        self.connect_btn.setEnabled(not state)
        self.disconnect_btn.setEnabled(state)
        self.host_input.setEnabled(not state)
        self.port_input.setEnabled(not state)
        self.state_changed.emit(state)

    @Slot(list)
    def send_rois(self, rois: list):
        """
        **Blocking**: for each ROI, send 4×1 KB float32 chunks with ACKs,
        then read 1 KB result, emit classification_result, and finally
        inference_complete.
        """
        if not self._sock or not rois:
            self.inference_complete.emit()
            return

        try:
            for roi in rois:
                # normalize to [0,1], cast float32, flatten
                # arr = (roi.astype(np.float32) / 255.0).ravel()
                # data = arr.tobytes()  # = 4096 bytes
                
                
                image_value_32b_numpy = ((roi)/255.0).astype(np.float32)#.astype(np.uint8)
                img_raw = image_value_32b_numpy.tobytes()#将图片转化为二进制格式
                for i in range(1,5):#4个数据包,每个数据包1k,整个图片4kb float32 归一化 !!低地址存高字节
                    self._sock.send(img_raw[1024*(i-1):1024*i])#发送图像矩阵
                    packet_flag = -1#结果返回标志
                    #第四个数据包是最后一个数据包,不用应答and i!=4
                    while(packet_flag==-1 and i!=4):#等待FPGA确认接收到这个1K数据包则发送下一个数据包
                        msg = self._sock.recv(1024)#接收来自FPGA 1字节验证数据,用于表示已经成功接收到1KB数据包
                        packet_flag = 1                   
                Result_flag = -1#结果返回标志
                while(Result_flag==-1):
                    msg = self._sock.recv(1024)#接收来自FPGA 1字节验证数据,用于表示已经成功接收到这张图片
                    Result_flag = 1
                    Result = int.from_bytes(msg,byteorder='little',signed=False)#bytes 转int byteorder 大端还是小端   
                    self.classification_result.emit(Result)
                #添加结果
                
                # for i range(1, 5):
                    
                #     if len(data) < 1024 * i:
                #         raise ValueError(f"ROI data too short: {len(data)} bytes")

                # # send in four 1024‐byte chunks
                # for i in range(4):
                #     chunk = data[1024*i : 1024*(i+1)]
                #     self._sock.sendall(chunk)
                #     # wait ACK after each of the first three
                #     if i < 3:
                #         _ = self._sock.recv(1024)

                # # final classification reply
                # result_bytes = self._sock.recv(1024)
                # result = int.from_bytes(result_bytes,
                #                         byteorder='little',
                #                         signed=False)
                # self.classification_result.emit(result)

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.inference_complete.emit()
