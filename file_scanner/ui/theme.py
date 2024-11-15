"""Theme and styling for the application."""

# Color palette
COLORS = {
    'background': '#1e1e1e',
    'surface': '#252526',
    'primary': '#007acc',
    'primary_hover': '#0098ff',
    'text': '#ffffff',
    'text_secondary': '#cccccc',
    'border': '#404040',
    'error': '#f44747',
    'success': '#6a9955',
    'header': '#333333',
    'selected': '#094771',
    'hover': '#2a2d2e'
}

# Main application style
MAIN_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['background']};
}}

QWidget {{
    color: {COLORS['text']};
    font-size: 12px;
}}

QSplitter::handle {{
    background-color: {COLORS['border']};
}}

QStatusBar {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
}}
"""

# Panel style
PANEL_STYLE = f"""
QFrame {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
}}

QLabel {{
    color: {COLORS['text']};
    padding: 4px;
}}

QPushButton {{
    background-color: {COLORS['primary']};
    color: {COLORS['text']};
    border: none;
    border-radius: 3px;
    padding: 6px 12px;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['selected']};
}}

QPushButton:disabled {{
    background-color: {COLORS['border']};
    color: {COLORS['text_secondary']};
}}

QLineEdit {{
    background-color: {COLORS['background']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 6px;
}}

QLineEdit:focus {{
    border-color: {COLORS['primary']};
}}

QComboBox {{
    background-color: {COLORS['background']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 6px;
}}

QComboBox:hover {{
    border-color: {COLORS['primary']};
}}

QComboBox::drop-down {{
    border: none;
}}

QComboBox::down-arrow {{
    image: none;
    border: none;
}}

QProgressBar {{
    background-color: {COLORS['background']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
}}
"""

# Table style
TABLE_STYLE = f"""
QTableView {{
    background-color: {COLORS['background']};
    alternate-background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    gridline-color: {COLORS['border']};
    selection-background-color: {COLORS['selected']};
    selection-color: {COLORS['text']};
}}

QTableView::item {{
    padding: 4px;
}}

QTableView::item:hover {{
    background-color: {COLORS['hover']};
}}

QHeaderView::section {{
    background-color: {COLORS['header']};
    color: {COLORS['text']};
    padding: 6px;
    border: none;
    border-right: 1px solid {COLORS['border']};
    border-bottom: 1px solid {COLORS['border']};
}}

QHeaderView::section:hover {{
    background-color: {COLORS['hover']};
}}
"""

# Tab style
TAB_STYLE = f"""
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['surface']};
}}

QTabBar::tab {{
    background-color: {COLORS['background']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['surface']};
    color: {COLORS['text']};
    border-bottom: none;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['hover']};
}}
"""

# Scrollbar style
SCROLLBAR_STYLE = f"""
QScrollBar:vertical {{
    background-color: {COLORS['background']};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border']};
    min-height: 20px;
    border-radius: 3px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['primary']};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['background']};
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border']};
    min-width: 20px;
    border-radius: 3px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['primary']};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""

# Combined styles
COMBINED_STYLE = "\n".join([
    MAIN_STYLE,
    PANEL_STYLE,
    TABLE_STYLE,
    TAB_STYLE,
    SCROLLBAR_STYLE
])
