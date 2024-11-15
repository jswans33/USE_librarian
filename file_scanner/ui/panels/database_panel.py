"""Panel for database viewing and filtering."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QLineEdit, QPushButton,
    QComboBox, QLabel, QHeaderView,
    QSizePolicy, QMessageBox, QMenu,
    QDialog, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem, QCursor

from ..widgets import PanelWidget
from ...services import DatabaseService, DatabaseEntry

class FileDetailsDialog(QDialog):
    """Dialog for showing detailed file information."""
    
    def __init__(self, entry: DatabaseEntry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Details")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Create text display
        text = QTextEdit()
        text.setReadOnly(True)
        
        # Build details text
        details = []
        details.append(f"Name: {entry.name}")
        details.append(f"Path: {entry.path}")
        details.append(f"Size: {entry.size}")
        details.append(f"Created: {entry.created}")
        details.append(f"Modified: {entry.modified}")
        details.append(f"Extension: {entry.extension}")
        
        if entry.category:
            details.append(f"\nCategory: {entry.category}")
        if entry.subcategory:
            details.append(f"Subcategory: {entry.subcategory}")
        
        if entry.tags:
            details.append("\nTags:")
            for tag in sorted(entry.tags):
                details.append(f"  • {tag}")
        
        if entry.patterns:
            details.append("\nPatterns:")
            for pattern in sorted(entry.patterns):
                details.append(f"  • {pattern}")
        
        if entry.parsed_info:
            details.append(f"\nParsed Information:\n{entry.parsed_info}")
        
        text.setPlainText("\n".join(details))
        layout.addWidget(text)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

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
        
        # Quick filters button
        self.quick_filter_button = QPushButton("Quick Filters")
        self.quick_filter_button.setToolTip("Show common filters")
        self.quick_filter_button.clicked.connect(self._show_quick_filters)
        layout.addWidget(self.quick_filter_button)
        
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
    
    def _show_quick_filters(self):
        """Show quick filters menu."""
        menu = QMenu(self)
        
        # Add category submenu
        categories = QMenu("Categories", menu)
        for category in ['document', 'image', 'video', 'audio', 'code', 'data', 'model']:
            action = categories.addAction(category)
            action.triggered.connect(
                lambda checked, c=category: self._apply_filter("Category", c)
            )
        menu.addMenu(categories)
        
        # Add size submenu
        sizes = QMenu("Sizes", menu)
        for size in ['tiny', 'small', 'medium', 'large', 'huge']:
            action = sizes.addAction(size)
            action.triggered.connect(
                lambda checked, s=size: self._apply_filter("Tags", f"size:{s}")
            )
        menu.addMenu(sizes)
        
        # Add pattern submenu
        patterns = QMenu("Patterns", menu)
        common_patterns = [
            "Date pattern", "Version number", "Sequence number",
            "Version indicator", "Temporary file", "Test/Demo file",
            "Data file", "Configuration file"
        ]
        for pattern in common_patterns:
            action = patterns.addAction(pattern)
            action.triggered.connect(
                lambda checked, p=pattern: self._apply_filter("Patterns", p)
            )
        menu.addMenu(patterns)
        
        # Show menu at button
        menu.popup(QCursor.pos())
    
    def _apply_filter(self, column: str, value: str):
        """Apply a quick filter."""
        self.column_combo.setCurrentText(column)
        self.filter_input.setText(value)

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
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, position):
        """Show context menu for selected item."""
        # Get selected row
        index = self.indexAt(position)
        if not index.isValid():
            return
        
        # Create menu
        menu = QMenu(self)
        
        # Add actions
        view_details = menu.addAction("View Details")
        view_details.triggered.connect(lambda: self._show_details(index))
        
        # Show menu
        menu.exec_(self.viewport().mapToGlobal(position))
    
    def _show_details(self, index):
        """Show details dialog for selected item."""
        # Get row data
        row = index.row()
        entry = DatabaseEntry(
            name=self.model().data(self.model().index(row, 0)),
            path=self.model().data(self.model().index(row, 1)),
            size=self.model().data(self.model().index(row, 2)),
            created=self.model().data(self.model().index(row, 3)),
            modified=self.model().data(self.model().index(row, 4)),
            extension=self.model().data(self.model().index(row, 5)),
            category=self.model().data(self.model().index(row, 6)),
            subcategory=self.model().data(self.model().index(row, 7)),
            tags=set(self.model().data(self.model().index(row, 8)).split(", ")) if self.model().data(self.model().index(row, 8)) else set(),
            patterns=set(self.model().data(self.model().index(row, 9)).split(", ")) if self.model().data(self.model().index(row, 9)) else set(),
            parsed_info=self.model().data(self.model().index(row, 10))
        )
        
        # Show dialog
        dialog = FileDetailsDialog(entry, self)
        dialog.exec_()
    
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
            row_items = [
                QStandardItem(str(value))
                for value in [
                    entry.name,
                    entry.path,
                    entry.size,
                    entry.created,
                    entry.modified,
                    entry.extension,
                    entry.category or "",
                    entry.subcategory or "",
                    ", ".join(sorted(entry.tags)) if entry.tags else "",
                    ", ".join(sorted(entry.patterns)) if entry.patterns else "",
                    entry.parsed_info or ""
                ]
            ]
            self.table_view.source_model.appendRow(row_items)
        
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
