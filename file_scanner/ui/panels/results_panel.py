"""Panel for displaying scan results."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QProgressBar, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Slot

from ...core.models import ScanResult
from ..widgets import PanelWidget, SettingsTabWidget

class SummaryWidget(QWidget):
    """Widget for displaying scan summary."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)
    
    def update_summary(self, result: ScanResult):
        """Update summary with scan results."""
        summary = (
            f"Scan Results for: {result.root_path}\n\n"
            f"Total Files: {result.total_files:,}\n"
            f"Total Size: {result.formatted_total_size}\n"
            f"Total Directories: {len(result.directories)}\n"
            f"Unique Extensions: {len(result.extension_stats)}"
        )
        self.text_display.setText(summary)

class ExtensionsWidget(QWidget):
    """Widget for displaying extension statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Extension", "Count", "Total Size"])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)
        
        layout.addWidget(self.table)
    
    def update_extensions(self, result: ScanResult):
        """Update table with extension statistics."""
        self.table.setRowCount(0)
        
        # Sort extensions by count
        sorted_extensions = sorted(
            result.extension_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        # Add rows to table
        for ext, stats in sorted_extensions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Extension
            ext_item = QTableWidgetItem(ext)
            self.table.setItem(row, 0, ext_item)
            
            # Count
            count_item = QTableWidgetItem(f"{stats['count']:,}")
            count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, count_item)
            
            # Size
            if stats['size'] < 1024:
                size_str = f"{stats['size']} B"
            elif stats['size'] < 1024*1024:
                size_str = f"{stats['size']/1024:.1f} KB"
            elif stats['size'] < 1024*1024*1024:
                size_str = f"{stats['size']/(1024*1024):.1f} MB"
            else:
                size_str = f"{stats['size']/(1024*1024*1024):.2f} GB"
            
            size_item = QTableWidgetItem(size_str)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, size_item)

class ResultsPanel(PanelWidget):
    """Panel for displaying scan results and progress."""
    
    def __init__(self, parent=None):
        super().__init__("Results", parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create status area
        status_layout = QVBoxLayout()
        status_layout.setSpacing(2)
        
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        self.add_layout(status_layout)
        
        # Create tab widget
        self.tab_widget = SettingsTabWidget()
        
        # Create results widgets
        self.summary_widget = SummaryWidget()
        self.extensions_widget = ExtensionsWidget()
        
        # Add tabs
        self.tab_widget.add_tab_widget(self.summary_widget, "Summary")
        self.tab_widget.add_tab_widget(self.extensions_widget, "Extensions")
        
        self.add_widget(self.tab_widget)
    
    @Slot(str, int)
    def update_progress(self, status: str, percentage: int):
        """Update progress display."""
        self.status_label.setText(status)
        self.progress_bar.setVisible(True)
        
        if percentage < 0:
            self.progress_bar.setRange(0, 0)  # Indeterminate
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percentage)
    
    def show_error(self, message: str):
        """Display error message."""
        self.status_label.setText("Error")
        self.progress_bar.setVisible(False)
        self.summary_widget.text_display.setText(f"Error: {message}")
        self.extensions_widget.table.setRowCount(0)
    
    def show_results(self, result: ScanResult):
        """Display scan results."""
        self.status_label.setText("Scan completed")
        self.progress_bar.setVisible(False)
        
        # Update widgets
        self.summary_widget.update_summary(result)
        self.extensions_widget.update_extensions(result)
