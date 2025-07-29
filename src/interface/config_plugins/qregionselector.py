from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Signal, QTimer, QEventLoop

import logging
import platform
import time

current_os = platform.system()

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
        
        # start guide ui #
        from interface.web_ui import GuideUI
        guide_ui = GuideUI(image=self.image, steps=self.steps, note=self.note)
        guide_ui.start()
        
        # wait for the guide ui to stop (ty macos) #
        if current_os == "Darwin":
            logging.info("Waiting for Guide UI to close...")
            loop = QEventLoop()
            timer = QTimer()
            
            def check_status():
                if guide_ui.did_close:
                    timer.stop()
                    loop.quit()
            
            timer.timeout.connect(check_status)
            timer.start(100)
            loop.exec()

        if guide_ui.is_running == False:
            self.picking = False
            self.info_label.setText(old_text)
            QMessageBox.information(
                self,
                "Region Select",
                "No region selected."
            )
            return

        # start region selector #
        logging.info("Starting Region Selector...")
        from interface.region_selection import RegionSelector
        region_selector = RegionSelector()
        region_selector.start()

        logging.info("Getting region...")
        region = region_selector.get_selection()
        time.sleep(0.1)
        region_selector.stop()
    
        if region is None:
            self.picking = False
            self.info_label.setText(old_text)
            QMessageBox.information(
                self,
                "Region Select",
                "No region selected."
            )
            return

        self.set(region["left"], region["top"], region["width"], region["height"])
        self.picking = False
        
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