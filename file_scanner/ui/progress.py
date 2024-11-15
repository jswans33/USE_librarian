"""Progress handling for GUI operations."""
from PySide6.QtCore import QObject, Signal

class ProgressHandler(QObject):
    """Handles progress updates for GUI operations."""
    
    progress_updated = Signal(str, int)  # (status, percentage)
    
    def update_progress(self, status: str, percentage: int = -1):
        """Update progress status and percentage.
        
        Args:
            status: Current operation status
            percentage: Progress percentage (-1 for indeterminate)
        """
        self.progress_updated.emit(status, percentage)
