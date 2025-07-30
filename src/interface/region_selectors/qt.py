from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPen, QColor
from variables import Variables

__all__ = ["RegionSelector"]
class RegionSelector(QWidget):
    def __init__(self, stop_macro=False):
        super().__init__()
        self.stop_macro = stop_macro
        self.stopped = False

        self.selection = None
        self.start_pos = None
        self.end_pos = None

        # init gui #
        screen = QApplication.primaryScreen()
        self.screen_geometry = screen.geometry()

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setGeometry(self.screen_geometry)
        
        self.setWindowOpacity(0.4)
        self.setStyleSheet("background-color: black;")
        
        self.setCursor(Qt.CrossCursor)

    def start(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def stop(self):
        if self.stopped: return
        self.stopped = True

        if self.stop_macro == True: Variables.is_running = False
        self.close()

    def get_selection(self):
        return self.selection
    
    #######################################################################################

    def mousePressEvent(self, event):
        self.start_pos = event.pos()
        self.end_pos = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        self.end_pos = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        rect = QRect(self.start_pos, self.end_pos).normalized()
        self.selection = {
            "left": rect.left(),
            "top": rect.top(),
            "width": rect.width(),
            "height": rect.height()
        }
        self.stop()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.selection = None
            self.close() # use close so the macro doesnt exit with stop_macro = true #

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        if self.start_pos and self.end_pos:
            qp.setPen(QPen(QColor(0, 255, 0), 2, Qt.SolidLine))
            qp.setBrush(QColor(0, 255, 0, 64))
            qp.drawRect(QRect(self.start_pos, self.end_pos).normalized())

        qp.end()