"""File metadata and pattern analysis."""
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from datetime import datetime
import re
from pathlib import Path

from .file_parser import FileNameParser, ParsedName
from .directory_parser import DirectoryAnalyzer, DirectoryGroup

@dataclass(frozen=True)  # Make it immutable and hashable
class FilePattern:
    """Pattern detected in file names or content."""
    pattern: str
    description: str
    matches: int = 0
    examples: tuple[str, ...] = field(default_factory=tuple)  # Use tuple instead of list
    
    def matches_file(self, file_name: str) -> bool:
        """Check if file matches this pattern."""
        return bool(re.search(self.pattern, file_name, re.IGNORECASE))

@dataclass(frozen=True)  # Make it immutable and hashable
class FileTag:
    """User-defined or auto-generated tag."""
    name: str
    source: str  # 'auto' or 'user'
    confidence: float = 1.0  # 0.0 to 1.0
    created: datetime = field(default_factory=datetime.now)
    
    def __hash__(self):
        """Make tag hashable based on name and source."""
        return hash((self.name, self.source))
    
    def __eq__(self, other):
        """Tags are equal if they have the same name and source."""
        if not isinstance(other, FileTag):
            return NotImplemented
        return self.name == other.name and self.source == other.source

@dataclass
class FileMetadata:
    """Extended metadata for a file."""
    file_path: Path
    tags: Set[FileTag] = field(default_factory=set)
    patterns: Set[FilePattern] = field(default_factory=set)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    parsed_name: Optional[ParsedName] = None
    directory_group: Optional[DirectoryGroup] = None
    notes: str = ""
    last_analyzed: Optional[datetime] = None

class PatternAnalyzer:
    """Analyzes files for common patterns."""
    
    # Common file patterns
    COMMON_PATTERNS = [
        FilePattern(
            r"\d{4}-\d{2}-\d{2}",
            "Date pattern (YYYY-MM-DD)",
        ),
        FilePattern(
            r"v\d+",
            "Version number",
        ),
        FilePattern(
            r"[\w-]+_\d+",
            "Sequence number",
        ),
        FilePattern(
            r"backup|bak|old|new|final|draft",
            "Version indicator",
        ),
        FilePattern(
            r"temp|tmp|cache",
            "Temporary file",
        ),
        FilePattern(
            r"test|demo|sample|example",
            "Test/Demo file",
        ),
        FilePattern(
            r"data|export|import|report",
            "Data file",
        ),
        FilePattern(
            r"config|settings|preferences",
            "Configuration file",
        ),
    ]
    
    def __init__(self):
        """Initialize analyzer."""
        self.patterns: Dict[str, FilePattern] = {
            p.pattern: p for p in self.COMMON_PATTERNS
        }
    
    def analyze_file(self, file_path: Path) -> Set[FilePattern]:
        """Analyze a file for patterns."""
        matches = set()
        file_name = file_path.name.lower()
        
        for pattern in self.patterns.values():
            if pattern.matches_file(file_name):
                # Create new pattern instance with updated matches and examples
                new_pattern = FilePattern(
                    pattern=pattern.pattern,
                    description=pattern.description,
                    matches=pattern.matches + 1,
                    examples=tuple(list(pattern.examples)[:4] + [file_name])
                )
                # Update pattern in dictionary
                self.patterns[pattern.pattern] = new_pattern
                matches.add(new_pattern)
        
        return matches

class AutoTagger:
    """Automatically generates tags based on file analysis."""
    
    def __init__(self):
        """Initialize tagger."""
        self.file_parser = FileNameParser()
    
    def generate_tags(self, file_path: Path, patterns: Set[FilePattern], 
                     parsed_name: ParsedName, directory_group: Optional[DirectoryGroup]) -> Set[FileTag]:
        """Generate tags for a file."""
        tags = set()
        
        # Add category tags
        main_cat, sub_cat = self.file_parser.get_category_parts(file_path)
        if main_cat:
            tags.add(FileTag(
                name=f"type:{main_cat}",
                source='auto',
                confidence=1.0
            ))
            if sub_cat:
                tags.add(FileTag(
                    name=f"subtype:{sub_cat}",
                    source='auto',
                    confidence=1.0
                ))
        
        # Add pattern-based tags
        for pattern in patterns:
            tags.add(FileTag(
                name=f"pattern:{pattern.description}",
                source='auto',
                confidence=0.8
            ))
        
        # Add size-based tags
        size_tag = self._get_size_tag(file_path)
        if size_tag:
            tags.add(size_tag)
        
        # Add parsed name tags
        if parsed_name.project_code:
            tags.add(FileTag(
                name=f"project:{parsed_name.project_code}",
                source='auto',
                confidence=0.9
            ))
        
        if parsed_name.discipline:
            tags.add(FileTag(
                name=f"discipline:{parsed_name.discipline}",
                source='auto',
                confidence=0.9
            ))
        
        if parsed_name.status:
            tags.add(FileTag(
                name=f"status:{parsed_name.status}",
                source='auto',
                confidence=0.9
            ))
        
        # Add directory-based tags
        if directory_group:
            if directory_group.project_code:
                tags.add(FileTag(
                    name=f"dir_project:{directory_group.project_code}",
                    source='auto',
                    confidence=0.95
                ))
            
            if directory_group.pattern:
                tags.add(FileTag(
                    name=f"dir_pattern:{directory_group.pattern}",
                    source='auto',
                    confidence=0.9
                ))
            
            if 'projects' in directory_group.metadata:
                tags.add(FileTag(
                    name="multi_project_dir",
                    source='auto',
                    confidence=0.9
                ))
        
        return tags
    
    def _get_size_tag(self, file_path: Path) -> Optional[FileTag]:
        """Generate size-based tag."""
        try:
            size = file_path.stat().st_size
            if size < 1024:  # < 1KB
                return FileTag("size:tiny", 'auto')
            elif size < 1024 * 1024:  # < 1MB
                return FileTag("size:small", 'auto')
            elif size < 10 * 1024 * 1024:  # < 10MB
                return FileTag("size:medium", 'auto')
            elif size < 100 * 1024 * 1024:  # < 100MB
                return FileTag("size:large", 'auto')
            else:  # >= 100MB
                return FileTag("size:huge", 'auto')
        except Exception:
            return None

class MetadataService:
    """Service for managing file metadata."""
    
    def __init__(self):
        """Initialize service."""
        self.pattern_analyzer = PatternAnalyzer()
        self.auto_tagger = AutoTagger()
        self.file_parser = FileNameParser()
        self.directory_analyzer = DirectoryAnalyzer()
        self.metadata: Dict[Path, FileMetadata] = {}
        self.current_root: Optional[Path] = None
    
    def analyze_directory(self, root_path: Path) -> DirectoryGroup:
        """Analyze directory structure."""
        self.current_root = root_path
        return self.directory_analyzer.analyze_directory(root_path)
    
    def analyze_file(self, file_path: Path) -> FileMetadata:
        """Analyze a file and generate metadata."""
        # Get or create metadata
        metadata = self.metadata.get(file_path) or FileMetadata(file_path)
        
        # Parse file name
        parsed_name = self.file_parser.parse_file_name(file_path)
        metadata.parsed_name = parsed_name
        
        # Get directory group if available
        if self.current_root:
            metadata.directory_group = self.directory_analyzer.get_group_for_file(file_path)
        
        # Get category
        main_cat, sub_cat = self.file_parser.get_category_parts(file_path)
        metadata.category = main_cat
        metadata.subcategory = sub_cat
        
        # Analyze patterns
        patterns = self.pattern_analyzer.analyze_file(file_path)
        metadata.patterns.update(patterns)
        
        # Generate tags
        tags = self.auto_tagger.generate_tags(
            file_path, patterns, parsed_name, metadata.directory_group
        )
        metadata.tags.update(tags)
        
        # Update analysis time
        metadata.last_analyzed = datetime.now()
        
        # Store metadata
        self.metadata[file_path] = metadata
        
        return metadata
    
    def add_tag(self, file_path: Path, tag_name: str) -> None:
        """Add a user tag to a file."""
        metadata = self.metadata.get(file_path)
        if metadata:
            metadata.tags.add(FileTag(
                name=tag_name,
                source='user'
            ))
    
    def remove_tag(self, file_path: Path, tag_name: str) -> None:
        """Remove a tag from a file."""
        metadata = self.metadata.get(file_path)
        if metadata:
            metadata.tags = {
                tag for tag in metadata.tags
                if tag.name != tag_name
            }
    
    def get_metadata(self, file_path: Path) -> Optional[FileMetadata]:
        """Get metadata for a file."""
        return self.metadata.get(file_path)
    
    def get_all_tags(self) -> Set[str]:
        """Get all unique tags in use."""
        tags = set()
        for metadata in self.metadata.values():
            tags.update(tag.name for tag in metadata.tags)
        return tags
    
    def get_all_patterns(self) -> List[FilePattern]:
        """Get all detected patterns."""
        return list(self.pattern_analyzer.patterns.values())
    
    def get_files_by_tag(self, tag_name: str) -> List[Path]:
        """Get all files with a specific tag."""
        return [
            path for path, metadata in self.metadata.items()
            if any(tag.name == tag_name for tag in metadata.tags)
        ]
    
    def get_files_by_pattern(self, pattern: str) -> List[Path]:
        """Get all files matching a pattern."""
        return [
            path for path, metadata in self.metadata.items()
            if any(p.pattern == pattern for p in metadata.patterns)
        ]
