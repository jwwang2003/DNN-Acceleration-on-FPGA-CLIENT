import socket
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject
from PySide6.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QFormLayout, QHBoxLayout, QMessageBox
)


class TCPWorker(QObject):
    """Performs TCP connect/disconnect in a separate thread to avoid UI blocking."""
    finished = Signal(bool, object)  # (success, socket_or_error)

    def __init__(self, host: str, port: int, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self._socket = None

    @Slot()
    def connect(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)
            s.connect((self.host, self.port))
            self._socket = s
            self.finished.emit(True, s)
        except Exception as e:
            self.finished.emit(False, e)

    @Slot()
    def disconnect(self):
        if self._socket:
            try:
                self._socket.close()
                self.finished.emit(True, None)
            except Exception as e:
                self.finished.emit(False, e)
        else:
            self.finished.emit(False, RuntimeError("No active socket"))


class TCPWidget(QWidget):
    """
    A QWidget that lets the user enter host & port, connect/disconnect,
    and emits `state_changed(connected: bool)` for parent/global control.
    """
    state_changed = Signal(bool)          # True = connected, False = disconnected
    error_occurred = Signal(str)          # Emitted on connection errors

    def __init__(self, parent=None):
        super().__init__(parent)
        self.connected = False
        self._socket = None
        self._thread = None
        self._worker = None

        # --- UI Setup ---
        self.host_input = QLineEdit("127.0.0.1")
        self.port_input = QLineEdit("8000")
        self.port_input.setFixedWidth(80)
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)

        form = QFormLayout()
        form.addRow("Host:", self.host_input)
        form.addRow("Port:", self.port_input)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        form.addRow(btn_layout)
        self.setLayout(form)

        # --- Signals & Slots ---
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)

    @Slot()
    def _on_connect_clicked(self):
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

        # spin up a worker thread for connect
        self._worker = TCPWorker(host, port)
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)
        self._worker.finished.connect(self._on_connect_result)
        self._thread.started.connect(self._worker.connect)
        self._thread.start()

    @Slot(bool, object)
    def _on_connect_result(self, success: bool, result):
        self._thread.quit()
        self._thread.wait()
        if success:
            self._socket = result
            self._set_connected(True)
        else:
            self.error_occurred.emit(str(result))
            QMessageBox.critical(self, "Connect Error", str(result))
            self._restore_ui()
        self._worker = None
        self._thread = None

    @Slot()
    def _on_disconnect_clicked(self):
        if not self._socket:
            return
        # disable UI while disconnecting
        self.disconnect_btn.setEnabled(False)
        self._worker = TCPWorker("", 0)
        self._worker._socket = self._socket
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)
        self._worker.finished.connect(self._on_disconnect_result)
        self._thread.started.connect(self._worker.disconnect)
        self._thread.start()

    @Slot(bool, object)
    def _on_disconnect_result(self, success: bool, _):
        self._thread.quit()
        self._thread.wait()
        if success:
            self._socket = None
            self._set_connected(False)
        else:
            QMessageBox.warning(self, "Disconnect Error", str(_))
            self.disconnect_btn.setEnabled(True)
        self._worker = None
        self._thread = None

    def _set_connected(self, state: bool):
        self.connected = state
        self.connect_btn.setEnabled(not state)
        self.disconnect_btn.setEnabled(state)
        # re-enable host/port only when disconnected
        self.host_input.setEnabled(not state)
        self.port_input.setEnabled(not state)
        self.state_changed.emit(state)

    def _restore_ui(self):
        # Called on failed connect
        self.connect_btn.setEnabled(True)
        self.host_input.setEnabled(True)
        self.port_input.setEnabled(True)

    def get_socket(self):
        """Return the active socket, or None if disconnected."""
        return self._socket
