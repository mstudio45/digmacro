from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Signal

import time

class QRegionSelector(QWidget):
    valueChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.picking = False
        self._region = (0, 0, 1, 1)

        self.image = None
        self.steps = None
        self.note = None

        self.info_label = QLabel("No region picked")

        self.pick_button = QPushButton("Pick Region")
        self.pick_button.clicked.connect(self.start_picking)

        row_layout = QHBoxLayout()

        row_layout.addWidget(self.info_label)
        row_layout.addWidget(self.pick_button)

        self.setLayout(row_layout)

    def start_picking(self):
        if self.picking: return

        old_text = self.info_label.text()
        self.info_label.setText("Waiting...")
        self.picking = True
        
        from interface.region_selection import RegionSelector
        from interface.web_ui import GuideUI

        guide_ui = GuideUI(image=self.image, steps=self.steps, note=self.note)
        guide_ui.start()
        
        while guide_ui.did_close == False:
            time.sleep(0.1)

        if guide_ui.is_running == False:
            self.picking = False
            self.info_label.setText(old_text)
            QMessageBox.information(
                self,
                "Region Select",
                "No region selected."
            )
            return

        region_selector = RegionSelector()
        region_selector.start()
        region = region_selector.get_selection()
        if region is None:
            self.picking = False
            self.info_label.setText(old_text)
            QMessageBox.information(
                self,
                "Region Select",
                "No region selected."
            )
            return

        self.picking = False
        self.set(region["left"], region["top"], region["width"], region["height"])
        region_selector.stop()
        
    def value(self):
        return self._region

    def set(self, left=None, top=None, width=None, height=None):
        if not left or not top or not width or not height: return

        self._region = (int(left), int(top), int(width), int(height))
        self.info_label.setText(f"({left}, {top}, {width}, {height})")

        self.valueChanged.emit(self.value())
    
    def setImage(self, image): self.image = image
    def setSteps(self, steps): self.steps = steps
    def setNote(self, note):   self.note = note