"""Base panel widget with standard layout and styling."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame,
    QLabel, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class PanelWidget(QFrame):
    """Base widget for panels with standard styling and layout."""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        
        # Set frame style
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        
        # Create main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(4, 4, 4, 4)
        self._main_layout.setSpacing(4)
        
        # Add title if provided
        if title:
            title_layout = QHBoxLayout()
            title_layout.setContentsMargins(4, 4, 4, 4)
            
            title_label = QLabel(title)
            font = QFont()
            font.setPointSize(10)
            font.setBold(True)
            title_label.setFont(font)
            
            # Create title bar
            title_bar = QFrame()
            title_bar_layout = QHBoxLayout(title_bar)
            title_bar_layout.setContentsMargins(8, 4, 8, 4)
            title_bar_layout.addWidget(title_label)
            
            title_layout.addWidget(title_bar)
            self._main_layout.addLayout(title_layout)
        
        # Create content widget
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(4, 4, 4, 4)
        self._content_layout.setSpacing(4)
        
        # Add content widget to main layout
        self._main_layout.addWidget(self._content)
    
    @property
    def content_layout(self) -> QVBoxLayout:
        """Get the content layout for adding widgets."""
        return self._content_layout
    
    def add_widget(self, widget: QWidget):
        """Add a widget to the panel's content area."""
        self._content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add a layout to the panel's content area."""
        self._content_layout.addLayout(layout)
    
    def add_stretch(self, stretch: int = 1):
        """Add stretch to the panel's content area."""
        self._content_layout.addStretch(stretch)
    
    def set_content_margin(self, left: int, top: int, right: int, bottom: int):
        """Set content area margins."""
        self._content_layout.setContentsMargins(left, top, right, bottom)
    
    def set_spacing(self, spacing: int):
        """Set spacing between widgets in content area."""
        self._content_layout.setSpacing(spacing)
