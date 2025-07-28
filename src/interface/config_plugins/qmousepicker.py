from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal

import time
import pynput

class QMousePicker(QWidget):
    valueChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.picking = False
        self._pos = (0, 0)

        self.info_label = QLabel("No position picked")

        self.pick_button = QPushButton("Pick Position")
        self.pick_button.clicked.connect(self.start_picking)

        row_layout = QHBoxLayout()

        row_layout.addWidget(self.info_label)
        row_layout.addWidget(self.pick_button)

        self.setLayout(row_layout)

    def on_click(self, x, y, button, pressed):
        if pressed and button == pynput.mouse.Button.left:
            self.set(x, y)
            self.picking = False

            return False

    def start_picking(self):
        if self.picking: return
        self.info_label.setText("Waiting...")
        self.picking = True
        
        self.mouse_listener = pynput.mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()

        while self.picking: time.sleep(0.05)
        
        self.mouse_listener.stop()
        
    def value(self):
        return self._pos

    def set(self, x=None, y=None):
        if not x or not y: return

        self._pos = (int(x), int(y))
        self.info_label.setText(f"X={x}, Y={y}")

        self.valueChanged.emit(self.value())
