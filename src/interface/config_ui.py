import os
import platform
import json
import logging

## ui editor ##
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit,
    QPushButton, QLabel, QGroupBox, QComboBox, QMessageBox,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt

from config import Config, settings_table
from variables import StaticVariables

import utils.general.filehandler as FileHandler
from utils.images.screen import scale_x, scale_y

import interface.msgbox as msgbox

current_os = platform.system()

from interface.config_plugins.qmousepicker import QMousePicker
from interface.config_plugins.qregionselector import QRegionSelector
from interface.config_plugins.qmulticombobox import QMultiComboBox

class ConfigUI(QWidget):
    def __init__(self):
        super().__init__()
        self.changes_made = False
        self.start_macro_now = False

        self.setWindowTitle("DIG Macro Configuration | https://github.com/mstudio45/digmacro")
        self.setGeometry(100, 100, 600 * scale_x, 500 * scale_y)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.widgets = {}

        self.create_ui()
        self.load_current_settings()
        self.setup_change_handler()
        self.config_loaded = True
    
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
        if self.changes_made:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to exit without saving?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                return
            
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
        if Config.USE_SAVED_POSITION:
            if os.path.isfile(StaticVariables.region_filepath):
                try:
                    pos = FileHandler.read(StaticVariables.region_filepath)
                    if pos is None: pass

                    self.avalaible_regions = json.loads(pos)
                    if self.avalaible_regions:
                        region_group_layout.addWidget(QLabel("Region Format Example: 'Windows 0x0 1920x1080' (os leftxtop widthxheight)"))

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
                region_group_layout.addWidget(QLabel("There were no valid regions found."))
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
            # widget information #
            widget_information = settings_table[section]
            default_widget_settings = settings_table["default"]

            # group box #
            group_box = QGroupBox(section)
            group_layout = QVBoxLayout()
            group_box.setLayout(group_layout)

            # warning text #
            warning_text = widget_information.get("__WARNING", None)
            if warning_text is not None:
                warning_label = QLabel(f"<b>{warning_text}</b>")
                warning_label.setStyleSheet("color: red;")
                group_layout.addWidget(warning_label)

            # info text #
            info_text = widget_information.get("__INFO", None)
            if warning_text is not None:
                info_label = QLabel(info_text)
                group_layout.addWidget(info_label)
            
            # widget #
            for key, value in options.items():
                row_layout = QHBoxLayout()
                label = QLabel(f"{key}:")

                row_layout.addWidget(label)

                widget = None
                widget_settings = widget_information.get(key, default_widget_settings)
                widget_type = widget_settings["widget"]
                tooltip = widget_settings.get("tooltip", settings_table["default"].get("tooltip", ""))
                is_enabled = widget_settings.get("enabled", True)

                if widget_type == "QCheckBox":
                    widget = QCheckBox()
  
                elif widget_type == "QSpinBox":
                    widget = QSpinBox()
                    widget.setMinimum(widget_settings.get("min", 0))
                    widget.setMaximum(widget_settings.get("max", 100))
    
                elif widget_type == "QDoubleSpinBox":
                    widget = QDoubleSpinBox()
                    widget.setMinimum(widget_settings.get("min", 0.0))
                    widget.setMaximum(widget_settings.get("max", 1.0))
                    widget.setSingleStep(widget_settings.get("step", 0.01))

                elif widget_type == "QComboBox":
                    widget = QComboBox()
                    items = widget_settings.get("items", [])
                    
                    # special stuff #
                    if key == "PATHFINDING_MACRO":
                        items = Config.PathfindingMacros.keys()
                        widget.currentTextChanged.connect(self.pathfinding_macro_change)

                    widget.addItems(items)
          
                elif widget_type == "QMousePicker":
                    widget = QMousePicker()
                
                elif widget_type == "QRegionSelector":
                    widget = QRegionSelector()
                    guide_image = widget_settings.get("guide_image", None)
                    steps = widget_settings.get("steps", None)
                    note = widget_settings.get("note", None)

                    widget.setImage(guide_image)
                    widget.setSteps(steps)
                    widget.setNote(note)

                elif widget_type == "QMultiComboBox":
                    widget = QMultiComboBox()
                    items = widget_settings.get("items", [])
                    widget.addItems(items)
   
                elif widget_type == "QLineEdit":
                    widget = QLineEdit()
                    widget.setAlignment(Qt.AlignLeft)

                    if widget_settings.get("password", False) == True:
                        widget.setEchoMode(QLineEdit.Password)
                else:
                    widget = QLineEdit() # fallback #
                    widget.setAlignment(Qt.AlignLeft)
                
                widget.setEnabled(is_enabled)

                # add to ui #
                label.setToolTip(tooltip)
                widget.setToolTip(tooltip)

                widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                row_layout.addWidget(widget)

                logging.info(f"Added widget as '{section}_{key}'.")
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
    def pathfinding_macro_change(self, text):
        if hasattr(self, "config_loaded") == True and text == "risk_spin":
            if current_os != "Windows":
                msgbox.alert("This pathfinding macro only works on Windows.")
            else:
                msgbox.alert("You need to have shiftlock enabled BEFORE you start the macro for this method!\n\nThis method abuses a bug inside DIG.\nIt uses your mouse to allow you to dig at one place without moving.\n\nYou are putting yourself at risk for being banned for bug abuse!", log_level=30)

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

                    elif isinstance(widget, QRegionSelector):
                        widget.valueChanged.connect(self.on_change_made)

                    elif isinstance(widget, QMultiComboBox):
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
                    
                    try:
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

                        elif isinstance(widget, QRegionSelector):
                            widget.set(*value)

                        elif isinstance(widget, QMultiComboBox):
                            widget.setSelectedItems(value)
                            
                    except Exception as e:
                        msgbox.alert(f"Failed to apply saved data to '{key}'. This issue only happens with configs made for older versions.\n\nError: {str(e)}", log_level=logging.ERROR)


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
                    
                    elif isinstance(widget, QRegionSelector):
                        new_value = widget.value()

                    elif isinstance(widget, QMultiComboBox):
                        new_value = widget.getSelectedItems()

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
        self.changes_made = False

        QMessageBox.information(self, "Defaults Loaded", "Configuration has been reset to default values!")