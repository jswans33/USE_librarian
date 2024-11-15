"""Panel for scan configuration options."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox,
    QSpinBox, QLabel, QGroupBox,
    QFormLayout, QListWidget, QPushButton,
    QHBoxLayout, QLineEdit, QInputDialog,
    QMessageBox
)
from PySide6.QtCore import Signal, Qt

from ...core.models import ScanOptions
from ..widgets import PanelWidget, SettingsTabWidget

class GeneralSettingsWidget(QWidget):
    """Widget for general scan settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        
        # Hidden files option
        self.include_hidden = QCheckBox()
        self.include_hidden.setChecked(True)
        self.include_hidden.setToolTip("Include hidden files and directories in scan")
        layout.addRow("Include Hidden Files:", self.include_hidden)
        
        # Symlinks option
        self.follow_links = QCheckBox()
        self.follow_links.setChecked(False)
        self.follow_links.setToolTip("Follow symbolic links when scanning")
        layout.addRow("Follow Symbolic Links:", self.follow_links)

class FilterSettingsWidget(QWidget):
    """Widget for filter settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Pattern list
        self.pattern_list = QListWidget()
        self.pattern_list.setToolTip("Patterns to ignore during scan (e.g., *.tmp, *.cache)")
        layout.addWidget(self.pattern_list)
        
        # Pattern controls
        pattern_controls = QHBoxLayout()
        
        # Pattern input
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter pattern (e.g., *.tmp)")
        pattern_controls.addWidget(self.pattern_input)
        
        # Add button
        add_button = QPushButton("Add")
        add_button.setToolTip("Add ignore pattern")
        add_button.clicked.connect(self._add_pattern)
        pattern_controls.addWidget(add_button)
        
        # Remove button
        remove_button = QPushButton("Remove")
        remove_button.setToolTip("Remove selected pattern")
        remove_button.clicked.connect(self._remove_pattern)
        pattern_controls.addWidget(remove_button)
        
        layout.addLayout(pattern_controls)
        
        # Add common patterns
        self._add_common_patterns()
        
        # Connect enter key
        self.pattern_input.returnPressed.connect(self._add_pattern)
    
    def _add_common_patterns(self):
        """Add some common ignore patterns."""
        common_patterns = [
            "*.tmp",
            "*.cache",
            "*.log",
            "__pycache__",
            ".git",
            ".svn",
            "node_modules"
        ]
        self.pattern_list.addItems(common_patterns)
    
    def _add_pattern(self):
        """Add new ignore pattern."""
        pattern = self.pattern_input.text().strip()
        if pattern:
            # Check for duplicates
            existing_items = [
                self.pattern_list.item(i).text()
                for i in range(self.pattern_list.count())
            ]
            if pattern not in existing_items:
                self.pattern_list.addItem(pattern)
                self.pattern_input.clear()
            else:
                QMessageBox.warning(
                    self,
                    "Duplicate Pattern",
                    f"The pattern '{pattern}' is already in the list."
                )
    
    def _remove_pattern(self):
        """Remove selected ignore pattern."""
        current_item = self.pattern_list.currentItem()
        if current_item:
            self.pattern_list.takeItem(self.pattern_list.row(current_item))

class AdvancedSettingsWidget(QWidget):
    """Widget for advanced settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        
        # Max depth option
        self.max_depth = QSpinBox()
        self.max_depth.setSpecialValueText("No Limit")  # For value 0
        self.max_depth.setRange(0, 999)
        self.max_depth.setValue(0)
        self.max_depth.setToolTip("Maximum directory depth to scan (0 for unlimited)")
        layout.addRow("Maximum Depth:", self.max_depth)

class ConfigPanel(PanelWidget):
    """Panel for configuring scan options."""
    
    config_changed = Signal(object)  # Emits ScanOptions
    
    def __init__(self, parent=None):
        super().__init__("Configuration", parent)
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create tab widget
        self.tab_widget = SettingsTabWidget()
        
        # Create settings widgets
        self.general_settings = GeneralSettingsWidget()
        self.filter_settings = FilterSettingsWidget()
        self.advanced_settings = AdvancedSettingsWidget()
        
        # Add tabs
        self.tab_widget.add_tab_widget(self.general_settings, "General")
        self.tab_widget.add_tab_widget(self.filter_settings, "Filters")
        self.tab_widget.add_tab_widget(self.advanced_settings, "Advanced")
        
        # Add to panel
        self.add_widget(self.tab_widget)
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.general_settings.include_hidden.stateChanged.connect(self._emit_config)
        self.general_settings.follow_links.stateChanged.connect(self._emit_config)
        self.advanced_settings.max_depth.valueChanged.connect(self._emit_config)
        self.filter_settings.pattern_list.model().rowsInserted.connect(self._emit_config)
        self.filter_settings.pattern_list.model().rowsRemoved.connect(self._emit_config)
    
    def _emit_config(self, _=None):
        """Emit current configuration."""
        options = self.get_options()
        self.config_changed.emit(options)
    
    def get_options(self) -> ScanOptions:
        """Get current scan options."""
        return ScanOptions(
            include_hidden=self.general_settings.include_hidden.isChecked(),
            follow_links=self.general_settings.follow_links.isChecked(),
            max_depth=self.advanced_settings.max_depth.value() if self.advanced_settings.max_depth.value() > 0 else None,
            ignore_patterns=[
                self.filter_settings.pattern_list.item(i).text()
                for i in range(self.filter_settings.pattern_list.count())
            ]
        )
