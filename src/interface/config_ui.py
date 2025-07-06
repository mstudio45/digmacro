## ui editor ##
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit,
    QPushButton, QLabel, QGroupBox, QComboBox, QMessageBox,
    QScrollArea
)

from config import Config, settings_table
from utils.images.screen import scale_x, scale_y

class ConfigUI(QWidget):
    def __init__(self):
        super().__init__()
        self.start_macro_now = False

        self.setWindowTitle("DIG Macro Configuration | https://github.com/mstudio45/digmacro")
        self.setGeometry(100, 100, 800 * scale_x, 700 * scale_y)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.widgets = {}

        self.create_ui()
        self.load_current_settings()

    def create_ui(self):
        global Config, config_tooltips

        # info label #
        info_label = QLabel("Hover over the options to see more information.")
        self.layout.addWidget(info_label)

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
                
                elif widget_type == "QLineEdit":
                    widget = QLineEdit()
                
                else:
                    widget = QLineEdit()  # fallback #

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

    def start_macro(self):
        self.start_macro_now = True
        self.close()

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

                    if new_value is not None:
                        Config.set(section, key, new_value, save_config=False)
        
        Config.save_config()
        QMessageBox.information(self, "Settings Saved", "Configuration has been saved successfully!")

    def load_default_settings(self):
        reply = QMessageBox.question(self, "Confirm Reset", "Are you sure you want to reset all settings to default values?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        Config.reset_to_defaults()
        self.load_current_settings()

        QMessageBox.information(self, "Defaults Loaded", "Configuration has been reset to default values!")