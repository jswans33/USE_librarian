"""Directory structure analysis and pattern detection."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Protocol
from pathlib import Path
import re
from abc import ABC, abstractmethod

@dataclass
class DirectoryGroup:
    """Group of related files in a directory."""
    path: Path
    level: int  # Directory depth
    pattern: Optional[str] = None  # Detected naming pattern
    project_code: Optional[str] = None
    common_prefix: Optional[str] = None
    file_count: int = 0
    subdirs: List['DirectoryGroup'] = field(default_factory=list)
    files: List[Path] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

class PatternMatcher(ABC):
    """Abstract base class for pattern matching strategies."""
    
    @abstractmethod
    def match(self, text: str) -> Optional[str]:
        """Match pattern in text and return extracted value."""
        pass

class ProjectCodeMatcher(PatternMatcher):
    """Matches project code patterns."""
    
    PATTERNS = [
        (r'(?P<code>[A-Z]{2,4}-\d{3,6})', 0.9),  # ABC-12345
        (r'(?P<code>\d{4,6}-[A-Z]{2,4})', 0.9),  # 12345-ABC
        (r'(?P<code>PRJ-\d{4,6})', 0.8),         # PRJ-12345
        (r'(?P<code>P\d{5,8})', 0.7),            # P12345
    ]
    
    def match(self, text: str) -> Optional[str]:
        """Match project code patterns."""
        for pattern, _ in self.PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group('code')
        return None

class VersionMatcher(PatternMatcher):
    """Matches version number patterns."""
    
    PATTERNS = [
        r'[vV](?P<version>\d+(\.\d+)*)',  # v1.2.3
        r'[rR](?P<version>\d+(\.\d+)*)',  # r1.2
        r'_(?P<version>\d+(\.\d+)*)$',    # _1.0
    ]
    
    def match(self, text: str) -> Optional[str]:
        """Match version patterns."""
        for pattern in self.PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group('version')
        return None

class DirectoryAnalyzer:
    """Analyzes directory structure and file patterns."""
    
    def __init__(self):
        """Initialize analyzer."""
        self.matchers = {
            'project': ProjectCodeMatcher(),
            'version': VersionMatcher(),
        }
        self.groups: Dict[Path, DirectoryGroup] = {}
    
    def analyze_directory(self, root_path: Path) -> DirectoryGroup:
        """Analyze directory structure and patterns.
        
        Args:
            root_path: Root directory to analyze
        
        Returns:
            DirectoryGroup containing analysis results
        """
        self.groups.clear()
        return self._analyze_recursive(root_path, 0)
    
    def _analyze_recursive(self, path: Path, level: int) -> DirectoryGroup:
        """Recursively analyze directory structure.
        
        Args:
            path: Current directory path
            level: Current directory depth
        
        Returns:
            DirectoryGroup for current directory
        """
        group = DirectoryGroup(path=path, level=level)
        
        try:
            # Get all files and directories
            items = list(path.iterdir())
            files = [f for f in items if f.is_file()]
            dirs = [d for d in items if d.is_dir()]
            
            # Analyze files in current directory
            group.files = files
            group.file_count = len(files)
            
            # Find common patterns
            if files:
                # Get common prefix
                names = [f.stem for f in files]
                prefix = self._find_common_prefix(names)
                if prefix and len(prefix) > 3:  # Minimum meaningful length
                    group.common_prefix = prefix
                
                # Look for project codes
                project_codes = set()
                for name in names:
                    code = self.matchers['project'].match(name)
                    if code:
                        project_codes.add(code)
                
                if len(project_codes) == 1:
                    group.project_code = project_codes.pop()
                elif len(project_codes) > 1:
                    # Multiple projects - might be a project container
                    group.metadata['projects'] = ', '.join(sorted(project_codes))
                
                # Detect naming pattern
                pattern = self._detect_naming_pattern(files)
                if pattern:
                    group.pattern = pattern
            
            # Recursively analyze subdirectories
            for subdir in dirs:
                subgroup = self._analyze_recursive(subdir, level + 1)
                group.subdirs.append(subgroup)
                
                # Inherit project code if subdirs have same code
                if subgroup.project_code:
                    if not group.project_code:
                        group.project_code = subgroup.project_code
                    elif group.project_code != subgroup.project_code:
                        # Different project codes - mark as multi-project
                        group.project_code = None
                        if 'projects' not in group.metadata:
                            group.metadata['projects'] = set()
                        group.metadata['projects'].add(subgroup.project_code)
            
            # Store group
            self.groups[path] = group
            
        except Exception as e:
            # Log error but continue analysis
            group.metadata['error'] = str(e)
        
        return group
    
    def _find_common_prefix(self, names: List[str]) -> Optional[str]:
        """Find common prefix among file names.
        
        Args:
            names: List of file names
        
        Returns:
            Common prefix if found, None otherwise
        """
        if not names:
            return None
        
        # Get shortest name length
        s1 = min(names)
        s2 = max(names)
        for i, c in enumerate(s1):
            if c != s2[i]:
                return s1[:i]
        return s1
    
    def _detect_naming_pattern(self, files: List[Path]) -> Optional[str]:
        """Detect common naming pattern in files.
        
        Args:
            files: List of files to analyze
        
        Returns:
            Pattern description if found, None otherwise
        """
        patterns = []
        
        # Check for sequential numbering
        numbers = []
        for f in files:
            match = re.search(r'(\d+)', f.stem)
            if match:
                numbers.append(int(match.group(1)))
        
        if numbers:
            if len(numbers) == len(files):
                if sorted(numbers) == list(range(min(numbers), max(numbers) + 1)):
                    patterns.append("Sequential numbering")
        
        # Check for date-based naming
        dates = []
        for f in files:
            match = re.search(r'\d{4}-\d{2}-\d{2}', f.stem)
            if match:
                dates.append(match.group(0))
        
        if dates:
            if len(dates) > len(files) * 0.5:  # More than 50% have dates
                patterns.append("Date-based naming")
        
        # Check for version-based naming
        versions = []
        for f in files:
            version = self.matchers['version'].match(f.stem)
            if version:
                versions.append(version)
        
        if versions:
            if len(versions) > len(files) * 0.5:  # More than 50% have versions
                patterns.append("Version-based naming")
        
        return " + ".join(patterns) if patterns else None
    
    def get_group_for_file(self, file_path: Path) -> Optional[DirectoryGroup]:
        """Get the directory group containing a file.
        
        Args:
            file_path: Path to file
        
        Returns:
            DirectoryGroup containing the file, or None if not found
        """
        return self.groups.get(file_path.parent)
    
    def format_group_info(self, group: DirectoryGroup) -> str:
        """Format directory group information as readable text.
        
        Args:
            group: DirectoryGroup to format
        
        Returns:
            Formatted string representation
        """
        parts = []
        
        if group.project_code:
            parts.append(f"Project: {group.project_code}")
        elif 'projects' in group.metadata:
            parts.append(f"Projects: {group.metadata['projects']}")
        
        if group.pattern:
            parts.append(f"Pattern: {group.pattern}")
        
        if group.common_prefix:
            parts.append(f"Common prefix: {group.common_prefix}")
        
        parts.append(f"Files: {group.file_count}")
        parts.append(f"Subdirectories: {len(group.subdirs)}")
        
        if 'error' in group.metadata:
            parts.append(f"Error: {group.metadata['error']}")
        
        return " | ".join(parts)
