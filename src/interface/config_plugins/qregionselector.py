from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox
from PySide6.QtCore import Signal, QTimer, QEventLoop

import logging
import platform
import traceback

from interface.web_ui import GuideUI
from interface.region_selectors.qt import RegionSelector

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

        # Timer for checking process status
        self.pick_button = QPushButton("Pick Region [ No Region Selected ]")
        self.pick_button.clicked.connect(self.start_picking)

        row_layout = QVBoxLayout()
        row_layout.addWidget(self.pick_button)
        self.setLayout(row_layout)

    ##############################################################################

    def start_picking(self):
        if self.picking: return
        self.picking = True
        
        old_text = self.pick_button.text()
        self.pick_button.setText("Waiting...")

        try:
            guide_ui = GuideUI(image=self.image, steps=self.steps, note=self.note)
            guide_ui.start()

            # block until guide UI closes #
            if current_os == "Darwin":
                loop = QEventLoop()
                timer = QTimer()

                def check_status():
                    if guide_ui.did_close:
                        timer.stop()
                        loop.quit()

                timer.timeout.connect(check_status)
                timer.start(100)
                loop.exec()

            # clicked exit #
            if not guide_ui.is_running:
                self.picking = False
                self.pick_button.setText(old_text)

                QMessageBox.information(
                    self,
                    "Region Select",
                    "No region selected."
                )
                return

            # start region selector #
            region_selector = RegionSelector(False)
            region_selector.start()

            # block until region selector closes #
            if current_os == "Darwin":
                loop = QEventLoop()
                timer = QTimer()

                def check_status():
                    if region_selector.stopped:
                        timer.stop()
                        loop.quit()

                timer.timeout.connect(check_status)
                timer.start(100)
                loop.exec()
            
            region = region_selector.get_selection()
            if not region:
                self.picking = False
                self.pick_button.setText(old_text)

                QMessageBox.information(
                    self,
                    "Region Select",
                    "No region selected."
                )
                return

            self.picking = False
            self.set(region["left"], region["top"], region["width"], region["height"])

        except Exception as e:
            logging.error("Error during region selection: %s", str(e))
            logging.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to pick region: {e}")
        
            self.picking = False
            self.pick_button.setText(self.old_text)

    ##############################################################################

    def closeEvent(self, event):
        self.process_timer.stop()
        self.cleanup_all_processes()
        super().closeEvent(event)
        
    def value(self):
        return self._region

    def set(self, left=None, top=None, width=None, height=None):
        if not left or not top or not width or not height: 
            return

        self._region = (int(left), int(top), int(width), int(height))
        self.pick_button.setText(f"Select Region [ ({left}, {top}, {width}, {height}) ]")
        self.valueChanged.emit(self.value())
    
    def setImage(self, image): self.image = image
    def setSteps(self, steps): self.steps = steps
    def setNote(self, note): self.note = note