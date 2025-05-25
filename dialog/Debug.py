from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QDialog,
    QSpinBox,
    QDialogButtonBox,
)

class DebugDialog(QDialog):
    fps_changed = Signal(int)

    def __init__(self, current_fps, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Debug Settings")
        layout = QFormLayout(self)

        # FPS adjustment
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(current_fps)
        layout.addRow("Target FPS:", self.fps_spin)

        # Placeholder for other parameters
        # e.g., self.param_spin = QSpinBox()
        # layout.addRow("Other Param:", self.param_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def accept(self):
        self.fps_changed.emit(self.fps_spin.value())
        super().accept()