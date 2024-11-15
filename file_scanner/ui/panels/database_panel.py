"""Panel for database viewing and filtering."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QLineEdit, QPushButton,
    QComboBox, QLabel, QHeaderView,
    QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem

from ..widgets import PanelWidget
from ...services import DatabaseService, DatabaseEntry

class FilterBar(QWidget):
    """Widget for filtering table contents."""
    
    filter_changed = Signal(str, str)  # column, text
    
    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Filter label
        filter_label = QLabel("Filter by:")
        filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(filter_label)
        
        # Column selector
        self.column_combo = QComboBox()
        self.column_combo.setMinimumWidth(120)
        self.column_combo.setMaximumWidth(200)
        self.column_combo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(self.column_combo)
        
        # Filter input
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Enter filter text...")
        self.filter_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.filter_input)
        
        # Clear button
        clear_button = QPushButton("Clear")
        clear_button.setFixedWidth(60)
        clear_button.setToolTip("Clear filter")
        clear_button.clicked.connect(self.clear_filter)
        layout.addWidget(clear_button)
        
        # Connect signals
        self.filter_input.textChanged.connect(self._emit_filter)
        self.column_combo.currentTextChanged.connect(self._emit_filter)
        
        # Style
        self.setMaximumHeight(40)
    
    def set_columns(self, columns: list[str]):
        """Set available columns for filtering."""
        current = self.column_combo.currentText()
        self.column_combo.clear()
        self.column_combo.addItems(columns)
        if current in columns:
            self.column_combo.setCurrentText(current)
    
    def clear_filter(self):
        """Clear current filter."""
        self.filter_input.clear()
        self.logger.log_action("Filter cleared")
    
    def _emit_filter(self, _=None):
        """Emit current filter settings."""
        column = self.column_combo.currentText()
        text = self.filter_input.text()
        if column and text:  # Only log non-empty filters
            self.logger.log_action(f"Filter applied: {column}='{text}'")
        self.filter_changed.emit(column, text)

class DatabaseTableView(QTableView):
    """Enhanced table view with sorting and filtering."""
    
    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger
        
        # Setup model and proxy
        self.source_model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setModel(self.proxy_model)
        
        # Configure view
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.ExtendedSelection)
        self.setShowGrid(True)
        self.setGridStyle(Qt.SolidLine)
        
        # Configure header
        header = self.horizontalHeader()
        header.setSectionsMovable(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignLeft)
        
        # Configure vertical header
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(24)  # Compact rows
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def set_filter(self, column: str, text: str):
        """Apply filter to table."""
        try:
            # Find column index
            for i in range(self.source_model.columnCount()):
                header_item = self.source_model.horizontalHeaderItem(i)
                if header_item and header_item.text() == column:
                    self.proxy_model.setFilterKeyColumn(i)
                    self.proxy_model.setFilterFixedString(text)
                    
                    # Log filter results
                    total_rows = self.source_model.rowCount()
                    visible_rows = self.proxy_model.rowCount()
                    
                    # Log with percentage
                    self.logger.log_filter(column, text, visible_rows, total_rows)
                    
                    if visible_rows == 0 and text:
                        # Try to provide helpful suggestions
                        suggestion = None
                        if len(text) > 2:
                            # Check if any rows contain a substring
                            for row in range(total_rows):
                                item = self.source_model.item(row, i)
                                if item and text.lower() in item.text().lower():
                                    suggestion = f"Try a partial match like '{text[:2]}'"
                                    break
                        
                        self.logger.log_filter_no_matches(column, text, suggestion)
                    return
            
            # Column not found
            if text:  # Only log if actually trying to filter
                self.logger.log_error(f"Invalid filter column: {column}")
            
        except Exception as e:
            self.logger.log_error(f"Filter error: {str(e)}")
            self.proxy_model.setFilterFixedString("")
    
    def sizeHint(self) -> QSize:
        """Suggest a good size for the table."""
        return QSize(800, 400)

class DatabasePanel(PanelWidget):
    """Panel for database viewing and filtering."""
    
    def __init__(self, database_service: DatabaseService, logger, parent=None):
        super().__init__("Database", parent)
        self.database_service = database_service
        self.logger = logger
        self._init_ui()
        
        # Register as observer
        self.database_service.add_observer(self)
        
        # Initialize button states and tooltips
        self._update_button_states()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create header area
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 4)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.status_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Database controls
        self.load_button = QPushButton("Load Last Scan")
        self.load_button.clicked.connect(self._load_database)
        header_layout.addWidget(self.load_button)
        
        self.clear_button = QPushButton("Clear View")
        self.clear_button.setToolTip("Clear entries from view")
        self.clear_button.clicked.connect(self._clear_database)
        header_layout.addWidget(self.clear_button)
        
        # Last scan time
        self.scan_time_label = QLabel()
        self.scan_time_label.setStyleSheet("color: #666;")
        self.scan_time_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.scan_time_label)
        
        self.add_layout(header_layout)
        
        # Create filter bar
        self.filter_bar = FilterBar(self.logger)
        self.add_widget(self.filter_bar)
        
        # Create table view
        self.table_view = DatabaseTableView(self.logger)
        self.add_widget(self.table_view)
        
        # Connect signals
        self.filter_bar.filter_changed.connect(self.table_view.set_filter)
        
        # Set compact spacing
        self.set_content_margin(2, 2, 2, 2)
        self.content_layout.setSpacing(2)
        
        # Initialize columns
        self.table_view.source_model.setHorizontalHeaderLabels(
            self.database_service.columns
        )
        self.filter_bar.set_columns(self.database_service.columns)
    
    def _update_button_states(self):
        """Update button enabled states and tooltips."""
        has_data = self.database_service.has_data()
        has_entries = self.table_view.source_model.rowCount() > 0
        
        self.load_button.setEnabled(has_data and not has_entries)
        self.clear_button.setEnabled(has_entries)
        
        # Update load button tooltip
        if has_data and not has_entries:
            scan_info = self.database_service.get_last_scan_info()
            if scan_info:
                self.load_button.setToolTip(
                    f"Load scan from {scan_info.timestamp}\n"
                    f"Path: {scan_info.root_path}\n"
                    f"Files: {scan_info.total_files:,}\n"
                    f"Size: {scan_info.total_size}"
                )
            else:
                self.load_button.setToolTip("Load the most recent scan from database")
        else:
            self.load_button.setToolTip("Load the most recent scan from database")
    
    def _load_database(self):
        """Load database entries."""
        try:
            scan_info = self.database_service.load_last_scan()
            if scan_info:
                self.status_label.setText(f"Loaded {scan_info.total_files:,} files")
            else:
                QMessageBox.information(
                    self,
                    "No Data",
                    "No previous scan data found in database."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load database: {str(e)}"
            )
        finally:
            self._update_button_states()
    
    def _clear_database(self):
        """Clear database entries."""
        self.database_service.clear()
        self._update_button_states()
    
    def on_entries_added(self, entries: list[DatabaseEntry]):
        """Handle new database entries."""
        for entry in entries:
            self.table_view.source_model.appendRow([
                QStandardItem(str(value))
                for value in [
                    entry.name,
                    entry.path,
                    entry.size,
                    entry.created,
                    entry.modified,
                    entry.extension
                ]
            ])
        
        # Update status
        total_rows = self.table_view.source_model.rowCount()
        self.status_label.setText(f"{total_rows:,} files")
        
        # Update button states
        self._update_button_states()
    
    def on_database_cleared(self):
        """Handle database clear event."""
        model = self.table_view.source_model
        model.removeRows(0, model.rowCount())
        self.logger.log_action("Database cleared")
        self.status_label.setText("Ready")
        self.scan_time_label.clear()
        
        # Update button states
        self._update_button_states()
    
    def set_scan_time(self, timestamp: str):
        """Set the last scan timestamp."""
        self.scan_time_label.setText(f"Last scan: {timestamp}")
    
    def closeEvent(self, event):
        """Handle panel close event."""
        # Unregister as observer
        self.database_service.remove_observer(self)
        super().closeEvent(event)
