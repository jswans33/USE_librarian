# File Scanner

A fast and efficient Python tool for scanning directories and analyzing file distributions with SQLite storage.

## For AI Agents

### Repository Structure
```
file_scanner/
├── core/              # Domain Layer
│   ├── models.py     # Data models and interfaces
│   └── scanner.py    # Core scanning logic
├── database/         # Data Layer
│   ├── base.py      # Abstract database manager
│   ├── stats.py     # Statistics storage
│   └── catalog.py   # File catalog storage
├── ui/              # Presentation Layer
│   ├── cli.py      # Command interface
│   └── formatters.py # Output formatting
└── utils/           # Shared Utilities
    ├── __init__.py  # Basic utilities
    └── formatting.py # Rich output formatting
```

### Key Files
- `models.py`: Contains domain models (FileInfo, DirectoryInfo, ScanResult)
- `scanner.py`: Main scanning logic with progress tracking
- `base.py`: Abstract database operations with SQLite
- `cli.py`: Command-line interface implementation
- `formatting.py`: Rich terminal output formatting

### Dependencies
- Python 3.6+
- rich: Terminal formatting and output
- SQLite3: Built-in database

### Installation Steps
1. Clone repository:
```bash
git clone https://github.com/yourusername/file-scanner.git
cd file-scanner
```

2. Create virtual environment:
```bash
python -m venv venv
```

3. Activate environment:
```powershell
# Windows PowerShell
./venv/Scripts/activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install rich
```

### Usage Examples

1. Basic Directory Scan:
```python
from file_scanner import FileScanner, ScanOptions
from file_scanner.database import StatsManager, CatalogManager

# Initialize scanner
scanner = FileScanner("path/to/scan")
result = scanner.scan()

# Save results
stats_db = StatsManager()
catalog_db = CatalogManager()

scan_id = stats_db.save_scan_results(result)
catalog_id = catalog_db.create_catalog(result)
```

2. Command Line Usage:
```bash
# Scan directory
python -m file_scanner scan path/to/directory

# View results
python -m file_scanner list
python -m file_scanner stats <scan_id>
python -m file_scanner files <catalog_id>
python -m file_scanner tree <catalog_id>
```

3. Advanced Options:
```bash
# Ignore hidden files and patterns
python -m file_scanner scan path/to/directory \
    --no-hidden \
    --ignore "*.tmp" "*.cache"

# Set tree depth
python -m file_scanner scan path/to/directory --depth 3

# Follow symbolic links
python -m file_scanner scan path/to/directory --follow-links
```

### API Reference

1. Core Models:
```python
@dataclass
class FileInfo:
    name: str
    path: Path
    relative_path: Path
    extension: Optional[str]
    size_bytes: int
    created_date: datetime
    modified_date: datetime
    is_hidden: bool

@dataclass
class ScanResult:
    root_path: Path
    total_files: int
    total_size: int
    files: List[FileInfo]
    directories: List[DirectoryInfo]
    extension_stats: Dict[str, Dict[str, int]]
```

2. Scanner Configuration:
```python
@dataclass
class ScanOptions:
    max_depth: Optional[int] = None
    follow_links: bool = False
    ignore_patterns: List[str] = None
    include_hidden: bool = True
```

3. Database Operations:
```python
# Save scan results
stats_manager = StatsManager("file_stats.db")
scan_id = stats_manager.save_scan_results(scan_result)

# Create file catalog
catalog_manager = CatalogManager("file_catalog.db")
catalog_id = catalog_manager.create_catalog(scan_result)
```

### Error Handling

The package defines custom exceptions:
```python
class ScanError(Exception): pass
class AccessError(ScanError): pass
class InvalidPathError(ScanError): pass
```

Handle these when using the scanner:
```python
try:
    scanner = FileScanner(path)
    result = scanner.scan()
except InvalidPathError:
    print("Invalid path specified")
except AccessError:
    print("Permission denied")
except ScanError as e:
    print(f"Scan error: {e}")
```

### Database Schema

1. Statistics Database (file_stats.db):
```sql
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY,
    scan_date TIMESTAMP,
    root_path TEXT,
    total_files INTEGER,
    total_size_bytes INTEGER,
    status TEXT
);

CREATE TABLE file_types (
    id INTEGER PRIMARY KEY,
    scan_id INTEGER,
    extension TEXT,
    count INTEGER,
    total_size_bytes INTEGER,
    FOREIGN KEY (scan_id) REFERENCES scan_results (id)
);
```

2. Catalog Database (file_catalog.db):
```sql
CREATE TABLE catalogs (
    id INTEGER PRIMARY KEY,
    scan_date TIMESTAMP,
    root_path TEXT,
    total_files INTEGER,
    total_size_bytes INTEGER,
    status TEXT
);

CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    catalog_id INTEGER,
    file_name TEXT,
    directory_path TEXT,
    relative_path TEXT,
    extension TEXT,
    size_bytes INTEGER,
    created_date TIMESTAMP,
    modified_date TIMESTAMP,
    is_hidden BOOLEAN,
    FOREIGN KEY (catalog_id) REFERENCES catalogs (id)
);

CREATE TABLE directories (
    id INTEGER PRIMARY KEY,
    catalog_id INTEGER,
    directory_path TEXT,
    relative_path TEXT,
    depth INTEGER,
    parent_path TEXT,
    FOREIGN KEY (catalog_id) REFERENCES catalogs (id)
);
```

### Notes for AI Agents

1. File Operations:
   - Use Path objects from pathlib
   - Handle file access errors gracefully
   - Check permissions before operations

2. Database Operations:
   - Use parameterized queries
   - Handle schema migrations
   - Process large datasets in batches

3. Output Formatting:
   - Use rich for terminal output
   - Format sizes in human-readable form
   - Show progress for long operations

4. Error Handling:
   - Catch specific exceptions
   - Provide meaningful error messages
   - Clean up resources on failure

## License

This project is licensed under the MIT License - see the LICENSE file for details.
