"""File name parsing and analysis."""
import re
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from pathlib import Path

@dataclass(frozen=True)
class NameComponent:
    """Component extracted from a file name."""
    type: str  # date, version, sequence, project, etc.
    value: str
    confidence: float = 1.0
    position: int = 0  # Position in filename

@dataclass
class ParsedName:
    """Parsed information from a file name."""
    original: str
    components: List[NameComponent] = field(default_factory=list)
    project_code: Optional[str] = None
    version: Optional[str] = None
    date: Optional[datetime] = None
    sequence: Optional[int] = None
    discipline: Optional[str] = None
    status: Optional[str] = None

class FileNameParser:
    """Parser for extracting information from file names."""
    
    # Known file extensions and their categories
    EXTENSIONS = {
        # Documents
        '.doc': 'document:word',
        '.docx': 'document:word',
        '.pdf': 'document:pdf',
        '.txt': 'document:text',
        '.rtf': 'document:rich_text',
        
        # Spreadsheets
        '.xls': 'spreadsheet:excel',
        '.xlsx': 'spreadsheet:excel',
        '.xlsm': 'spreadsheet:excel_macro',
        '.csv': 'spreadsheet:csv',
        
        # Email
        '.msg': 'email:outlook',
        '.eml': 'email:standard',
        
        # CAD/BIM
        '.rvt': 'model:revit',
        '.dwg': 'model:autocad',
        '.ifc': 'model:ifc',
        '.skp': 'model:sketchup',
        
        # Images
        '.jpg': 'image:jpeg',
        '.jpeg': 'image:jpeg',
        '.png': 'image:png',
        '.gif': 'image:gif',
        '.bmp': 'image:bitmap',
        '.tif': 'image:tiff',
        '.tiff': 'image:tiff',
        
        # Code
        '.py': 'code:python',
        '.js': 'code:javascript',
        '.html': 'code:html',
        '.css': 'code:css',
        '.cpp': 'code:cpp',
        '.h': 'code:cpp_header',
        
        # Data
        '.json': 'data:json',
        '.xml': 'data:xml',
        '.sql': 'data:sql',
        '.db': 'data:database',
        
        # Archives
        '.zip': 'archive:zip',
        '.rar': 'archive:rar',
        '.7z': 'archive:7zip',
        '.tar': 'archive:tar',
        '.gz': 'archive:gzip',
    }
    
    # Common patterns
    PROJECT_PATTERNS = [
        (r'(?P<code>[A-Z]{2,4}-\d{3,6})', 0.9),  # ABC-12345
        (r'(?P<code>\d{4,6}-[A-Z]{2,4})', 0.9),  # 12345-ABC
        (r'(?P<code>PRJ-\d{4,6})', 0.8),         # PRJ-12345
        (r'(?P<code>P\d{5,8})', 0.7),            # P12345
    ]
    
    VERSION_PATTERNS = [
        r'[vV](?P<version>\d+(\.\d+)*)',  # v1.2.3
        r'[rR](?P<version>\d+(\.\d+)*)',  # r1.2
        r'_(?P<version>\d+(\.\d+)*)$',    # _1.0
    ]
    
    DATE_PATTERNS = [
        (r'(?P<date>\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
        (r'(?P<date>\d{8})', '%Y%m%d'),
        (r'(?P<date>\d{2}-\d{2}-\d{4})', '%d-%m-%Y'),
    ]
    
    # Discipline codes
    DISCIPLINES = {
        'ARCH': 'Architecture',
        'STR': 'Structural',
        'MEP': 'Mechanical/Electrical/Plumbing',
        'CIVIL': 'Civil',
        'LAND': 'Landscape',
        'INT': 'Interior',
        'GEN': 'General',
    }
    
    # Status indicators
    STATUS_TERMS = {
        'DRAFT': 'Draft',
        'REVIEW': 'Under Review',
        'APPROVED': 'Approved',
        'FINAL': 'Final',
        'ISSUED': 'Issued',
        'WIP': 'Work in Progress',
        'SUPERSEDED': 'Superseded',
        'ARCHIVED': 'Archived',
    }
    
    def parse_file_name(self, file_path: Path) -> ParsedName:
        """Parse a file name into components.
        
        Args:
            file_path: Path to file
        
        Returns:
            ParsedName containing extracted information
        """
        # Initialize result
        name = file_path.stem
        result = ParsedName(original=name)
        components = []
        
        # Extract project code
        for pattern, confidence in self.PROJECT_PATTERNS:
            match = re.search(pattern, name)
            if match:
                code = match.group('code')
                result.project_code = code
                components.append(NameComponent(
                    type='project_code',
                    value=code,
                    confidence=confidence,
                    position=match.start()
                ))
                break
        
        # Extract version
        for pattern in self.VERSION_PATTERNS:
            match = re.search(pattern, name)
            if match:
                version = match.group('version')
                result.version = version
                components.append(NameComponent(
                    type='version',
                    value=version,
                    position=match.start()
                ))
                break
        
        # Extract date
        for pattern, format_str in self.DATE_PATTERNS:
            match = re.search(pattern, name)
            if match:
                try:
                    date_str = match.group('date')
                    date = datetime.strptime(date_str, format_str)
                    result.date = date
                    components.append(NameComponent(
                        type='date',
                        value=date_str,
                        position=match.start()
                    ))
                    break
                except ValueError:
                    continue
        
        # Extract sequence numbers
        seq_match = re.search(r'_(\d+)(?=_|$)', name)
        if seq_match:
            seq = int(seq_match.group(1))
            result.sequence = seq
            components.append(NameComponent(
                type='sequence',
                value=str(seq),
                position=seq_match.start()
            ))
        
        # Extract discipline
        for code, desc in self.DISCIPLINES.items():
            if code in name.upper():
                result.discipline = desc
                components.append(NameComponent(
                    type='discipline',
                    value=desc,
                    position=name.upper().find(code)
                ))
                break
        
        # Extract status
        for term, desc in self.STATUS_TERMS.items():
            if term in name.upper():
                result.status = desc
                components.append(NameComponent(
                    type='status',
                    value=desc,
                    position=name.upper().find(term)
                ))
                break
        
        # Store components sorted by position
        result.components = sorted(components, key=lambda x: x.position)
        
        return result
    
    def get_category(self, file_path: Path) -> Optional[str]:
        """Get the category of a file based on its extension.
        
        Args:
            file_path: Path to file
        
        Returns:
            Category string if known, None otherwise
        """
        return self.EXTENSIONS.get(file_path.suffix.lower())
    
    def get_category_parts(self, file_path: Path) -> tuple[Optional[str], Optional[str]]:
        """Get the main category and subcategory of a file.
        
        Args:
            file_path: Path to file
        
        Returns:
            Tuple of (main_category, subcategory)
        """
        category = self.get_category(file_path)
        if category:
            main, sub = category.split(':')
            return main, sub
        return None, None
    
    def format_parsed_name(self, parsed: ParsedName) -> str:
        """Format parsed name information as a readable string.
        
        Args:
            parsed: ParsedName to format
        
        Returns:
            Formatted string representation
        """
        parts = []
        
        if parsed.project_code:
            parts.append(f"Project: {parsed.project_code}")
        if parsed.discipline:
            parts.append(f"Discipline: {parsed.discipline}")
        if parsed.version:
            parts.append(f"Version: {parsed.version}")
        if parsed.date:
            parts.append(f"Date: {parsed.date.strftime('%Y-%m-%d')}")
        if parsed.sequence is not None:
            parts.append(f"Sequence: {parsed.sequence}")
        if parsed.status:
            parts.append(f"Status: {parsed.status}")
        
        return " | ".join(parts)
