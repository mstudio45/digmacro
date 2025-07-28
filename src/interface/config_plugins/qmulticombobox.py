from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolButton, QMenu, QSizePolicy, QStyleOptionComboBox, QStylePainter, QStyle
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QSize

class QMultiComboBox(QWidget):
    valueChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_text = "Select items"

        self.button = QToolButton(self)
        self.button.setPopupMode(QToolButton.InstantPopup)
        self.button.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.button.setFocusPolicy(Qt.NoFocus)
        self.button.setStyleSheet("""
            QToolButton { border: none; }
            QToolButton::menu-indicator { image: none; width: 0px; height: 0px; }
        """)
        self.button.clicked.connect(self._showMenu)

        self.menu = QMenu(self)
        self.button.setMenu(self.menu)

        layout = QVBoxLayout(self)
        layout.addWidget(self.button)
        layout.setContentsMargins(1, 1, 1, 1)
        
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.items: dict[str, QAction] = {}

    def addItems(self, data):
        for item in data:
            if item not in self.items:
                action = QAction(item, self)
                action.setCheckable(True)
                action.toggled.connect(self._onSelectionChanged)
                self.menu.addAction(action)
                self.items[item] = action
        self._updateButtonText()

    def setSelectedItems(self, data):
        for item, action in self.items.items():
            if action.isChecked() != (item in data):
                action.blockSignals(True)
                action.setChecked(item in data)
                action.blockSignals(False)
        self._updateButtonText()
        self.valueChanged.emit(self.getSelectedItems())

    def getSelectedItems(self):
        return [item for item, action in self.items.items() if action.isChecked()]

    def _onSelectionChanged(self):
        self._updateButtonText()
        self.valueChanged.emit(self.getSelectedItems())

    def _updateButtonText(self):
        selected = self.getSelectedItems()
        self._selected_text = ", ".join(selected) if selected else "Select items"
        self.update()

    def _showMenu(self):
        self.button.showMenu()

    def paintEvent(self, event):
        opt = QStyleOptionComboBox()
        opt.initFrom(self)
        opt.editable = False
        opt.currentText = self._selected_text
        opt.rect = self.rect()

        painter = QStylePainter(self)
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.drawComplexControl(QStyle.CC_ComboBox, opt)

        text_rect = self.style().subControlRect(QStyle.CC_ComboBox, opt, QStyle.SC_ComboBoxEditField, self)
        font_metrics = self.fontMetrics()
        elided = font_metrics.elidedText(self._selected_text, Qt.ElideRight, text_rect.width())

        painter.drawItemText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.palette(), True, elided)

    def sizeHint(self) -> QSize:
        return self.button.sizeHint()