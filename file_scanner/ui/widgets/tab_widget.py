"""Tab widget for organizing settings and configurations."""
from PySide6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt

class ScrollableWidget(QFrame):
    """Widget that provides scrolling for its content."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
    
    @property
    def layout(self) -> QVBoxLayout:
        """Get the widget's layout."""
        return self._layout

class SettingsTabWidget(QTabWidget):
    """Tab widget for organizing settings and configurations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set tab position and style
        self.setTabPosition(QTabWidget.North)
        self.setDocumentMode(True)  # Cleaner look
        
        # Configure tab bar
        tab_bar = self.tabBar()
        tab_bar.setExpanding(False)  # Don't expand tabs to fill width
        tab_bar.setDrawBase(True)  # Draw base line
        
        # Set uniform tab size
        self.setStyleSheet("""
            QTabBar::tab {
                min-width: 100px;
                padding: 8px 16px;
            }
        """)
    
    def add_tab_widget(self, widget: QWidget, title: str) -> QScrollArea:
        """Add a widget as a scrollable tab.
        
        Args:
            widget: Widget to add as tab content
            title: Tab title
            
        Returns:
            The scroll area containing the widget
        """
        # Create scrollable container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)  # Remove frame
        
        # Create content widget
        content = ScrollableWidget()
        content.layout.addWidget(widget)
        content.layout.addStretch()
        
        # Set content widget in scroll area
        scroll.setWidget(content)
        
        # Add to tab widget
        self.addTab(scroll, title)
        
        return scroll
    
    def add_widget_to_tab(self, tab_index: int, widget: QWidget):
        """Add a widget to an existing tab.
        
        Args:
            tab_index: Index of the tab to add to
            widget: Widget to add
        """
        scroll_area = self.widget(tab_index)
        if isinstance(scroll_area, QScrollArea):
            content = scroll_area.widget()
            if isinstance(content, ScrollableWidget):
                content.layout.insertWidget(content.layout.count() - 1, widget)
    
    def set_tab_tooltip(self, index: int, tooltip: str):
        """Set tooltip for a tab.
        
        Args:
            index: Index of the tab
            tooltip: Tooltip text
        """
        self.tabBar().setTabToolTip(index, tooltip)
    
    def set_current_tab(self, index: int):
        """Set the current tab.
        
        Args:
            index: Index of the tab to select
        """
        if 0 <= index < self.count():
            self.setCurrentIndex(index)
