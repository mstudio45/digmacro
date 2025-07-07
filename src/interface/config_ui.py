## ui editor ##
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit,
    QPushButton, QLabel, QGroupBox, QComboBox, QMessageBox,
    QScrollArea
)
from PySide6.QtCore import Signal
import os, json, time, pynput

from config import Config, settings_table
from variables import StaticVariables

import utils.general.filehandler as FileHandler
from utils.images.screen import scale_x, scale_y

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
            
            self.mouse_listener.suppress_event()
            return False

    def start_picking(self):
        if self.picking: return
        self.picking = True
        
        self.mouse_listener = pynput.mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()

        self.info_label.setText("Waiting...")
        while self.picking: time.sleep(0.05)

        self.mouse_listener.stop()
        
    def value(self):
        return f"pos:{self._pos[0]}x{self._pos[1]}"

    def set(self, x=None, y=None):
        if not x or not y: return

        self._pos = (int(x), int(y))
        self.info_label.setText(f"X={x}, Y={y}")

        self.valueChanged.emit(self.value())

class ConfigUI(QWidget):
    def __init__(self):
        super().__init__()
        self.changes_made = False
        self.start_macro_now = False

        self.setWindowTitle("DIG Macro Configuration | https://github.com/mstudio45/digmacro")
        self.setGeometry(100, 100, 500 * scale_x, 500 * scale_y)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.widgets = {}

        self.create_ui()
        self.load_current_settings()
        self.setup_change_handler()
    
    # closing #
    def closeEvent(self, event):
        if self.changes_made and not self.start_macro_now:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to exit without saving?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                event.ignore()
                return

        event.accept()

    def start_macro(self):
        self.start_macro_now = True
        self.close()

    # ui creation #
    def create_ui(self):
        global Config, config_tooltips

        # info label #
        info_label = QLabel("Hover over the options to see more information.")
        self.layout.addWidget(info_label)

        # screen regions #
        region_group_box = QGroupBox("Minigame Regions")
        region_group_layout = QVBoxLayout()
        region_group_box.setLayout(region_group_layout)

        self.avalaible_regions = []
        if Config.USE_SAVED_POSITION and os.path.isfile(StaticVariables.region_filepath):
            try:
                pos = FileHandler.read(StaticVariables.region_filepath)
                if pos is None: pass

                self.avalaible_regions = json.loads(pos)
                if self.avalaible_regions:
                    region_group_layout.addWidget(QLabel("Region Format Example: 0x0 1920x1080 (monitor left and top position, display resolution)"))

                    # list #
                    self.region_widget = QComboBox()
                    self.region_widget.addItems(self.avalaible_regions)
                    region_group_layout.addWidget(self.region_widget)

                    # btns #
                    region_button_layout = QHBoxLayout()

                    region_delete_button = QPushButton("Delete Selected Region")
                    region_delete_button.clicked.connect(self.delete_selected_region)
                    region_button_layout.addWidget(region_delete_button)

                    region_group_layout.addLayout(region_button_layout)
                else:
                    region_group_layout.addWidget(QLabel("There were no valid regions found."))
            except Exception as e:
                region_group_layout.addWidget(QLabel(f"Saved regions failed to load: {str(e)}"))
        else:
            region_group_layout.addWidget(QLabel("Saved regions disabled."))

        self.layout.addWidget(region_group_box)

        # scroll area #
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.layout.addWidget(scroll_area)

        # scroll widget #
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        scroll_area.setWidget(self.scroll_widget)

        # dynamic variable creation #
        for section, options in Config.config.items():
            group_box = QGroupBox(section)
            group_layout = QVBoxLayout()
            group_box.setLayout(group_layout)

            for key, value in options.items():
                row_layout = QHBoxLayout()
                label = QLabel(f"{key}:")
                row_layout.addWidget(label)

                settings = settings_table[key]
                widget = None
                widget_type = settings["widget"]
                tooltip = settings.get("tooltip", settings_table["default"].get("tooltip", ""))
                
                if widget_type == "QCheckBox":
                    widget = QCheckBox()

                elif widget_type == "QSpinBox":
                    widget = QSpinBox()
                    widget.setMinimum(settings.get("min", 0))
                    widget.setMaximum(settings.get("max", 100))

                elif widget_type == "QDoubleSpinBox":
                    widget = QDoubleSpinBox()
                    widget.setMinimum(settings.get("min", 0.0))
                    widget.setMaximum(settings.get("max", 1.0))
                    widget.setSingleStep(settings.get("step", 0.01))

                elif widget_type == "QComboBox":
                    widget = QComboBox()
                    items = settings.get("items", [])
                    
                    # special stuff #
                    if key == "PATHFINDING_MACRO":
                        items = Config.PathfindingMacros.keys()

                    widget.addItems(items)
          
                elif widget_type == "QMousePicker":
                    widget = QMousePicker()
   
                elif widget_type == "QLineEdit":
                    widget = QLineEdit()
                 
                else:
                    widget = QLineEdit() # fallback #
                   
                # add to ui #
                label.setToolTip(tooltip)
                widget.setToolTip(tooltip)

                row_layout.addWidget(widget)
                self.widgets[f"{section}_{key}"] = widget
                group_layout.addLayout(row_layout)

            self.scroll_layout.addWidget(group_box)

        # btns #
        button_layout = QHBoxLayout()

        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)

        load_default_button = QPushButton("Load Defaults")
        load_default_button.clicked.connect(self.load_default_settings)
        button_layout.addWidget(load_default_button)

        start_macro_button = QPushButton("Start Macro")
        start_macro_button.clicked.connect(self.start_macro)
        button_layout.addWidget(start_macro_button)

        self.layout.addLayout(button_layout)

    # on change handler #
    def on_change_made(self): self.changes_made = True

    def setup_change_handler(self):
        for section, options in Config.config.items():
            for key, value in options.items():
                widget_key = f"{section}_{key}"

                if widget_key in self.widgets:
                    widget = self.widgets[widget_key]
                    if isinstance(widget, QCheckBox):
                        widget.stateChanged.connect(self.on_change_made)

                    elif isinstance(widget, QSpinBox):
                        widget.valueChanged.connect(self.on_change_made)

                    elif isinstance(widget, QDoubleSpinBox):
                        widget.valueChanged.connect(self.on_change_made)

                    elif isinstance(widget, QLineEdit):
                        widget.textChanged.connect(self.on_change_made)

                    elif isinstance(widget, QComboBox):
                        widget.currentTextChanged.connect(self.on_change_made)

                    elif isinstance(widget, QMousePicker):
                        widget.valueChanged.connect(self.on_change_made)

    # regions #
    def delete_selected_region(self):
        cur_region = self.region_widget.currentText() 
        if self.avalaible_regions and cur_region in self.avalaible_regions:
            self.region_widget.clear()
            del self.avalaible_regions[cur_region]
            self.region_widget.addItems(self.avalaible_regions)

            FileHandler.write(StaticVariables.region_filepath, json.dumps(self.avalaible_regions, indent=4))

    # loading and saving #
    def load_current_settings(self):
        for section, options in Config.config.items():
            for key, value in options.items():
                widget_key = f"{section}_{key}"

                if widget_key in self.widgets:
                    widget = self.widgets[widget_key]
                    if isinstance(widget, QCheckBox):
                        widget.setChecked(value)

                    elif isinstance(widget, QSpinBox):
                        widget.setValue(value)
 
                    elif isinstance(widget, QDoubleSpinBox):
                        widget.setValue(value)

                    elif isinstance(widget, QLineEdit):
                        widget.setText(str(value))

                    elif isinstance(widget, QComboBox):
                        index = widget.findText(str(value))
                        if index != -1:
                            widget.setCurrentIndex(index)

                    elif isinstance(widget, QMousePicker):
                        widget.set(*value)

    def save_settings(self):
        reply = QMessageBox.question(self, "Confirm Save", "Are you sure you want to save the current settings?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        
        for section, options in Config.config.items():
            for key, value in options.items():
                widget_key = f"{section}_{key}"

                if widget_key in self.widgets:
                    widget = self.widgets[widget_key]
                    new_value = None

                    if isinstance(widget, QCheckBox):
                        new_value = widget.isChecked()

                    elif isinstance(widget, QSpinBox):
                        new_value = widget.value()

                    elif isinstance(widget, QDoubleSpinBox):
                        new_value = widget.value()

                    elif isinstance(widget, QLineEdit):
                        text_value = widget.text()
                        if isinstance(value, bool):
                            new_value = text_value.lower() == "true"

                        elif isinstance(value, int):
                            try: new_value = int(text_value)
                            except ValueError: new_value = value

                        elif isinstance(value, float):
                            try: new_value = float(text_value)
                            except ValueError: new_value = value

                        else:
                            new_value = text_value
                        
                    elif isinstance(widget, QComboBox):
                        new_value = widget.currentText()
                    
                    elif isinstance(widget, QMousePicker):
                        new_value = widget.value()

                    if new_value is not None:
                        Config.set(section, key, new_value, save_config=False)
        
        Config.save_config()
        self.changes_made = False
        QMessageBox.information(self, "Settings Saved", "Configuration has been saved successfully!")

    def load_default_settings(self):
        reply = QMessageBox.question(self, "Confirm Reset", "Are you sure you want to reset all settings to default values?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        Config.reset_to_defaults()
        self.load_current_settings()

        QMessageBox.information(self, "Defaults Loaded", "Configuration has been reset to default values!")