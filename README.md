# File Scanner

A fast and efficient Python tool for scanning directories and analyzing file distributions.

## Features

- Fast directory scanning with progress tracking
- Detailed file cataloging
- File type statistics
- Directory structure visualization
- Database storage for historical analysis
- Rich terminal output with colors and formatting

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/file-scanner.git
cd file-scanner
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```powershell
# Windows PowerShell
./venv/Scripts/activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install rich tqdm
```

## Usage

1. Basic Directory Scan:
```bash
python -m file_scanner scan path/to/directory
```

2. Advanced Options:
```bash
# Ignore hidden files and specific patterns
python -m file_scanner scan path/to/directory \
    --no-hidden \
    --ignore "*.tmp" "*.cache"

# Limit tree depth display
python -m file_scanner scan path/to/directory --depth 3

# Follow symbolic links
python -m file_scanner scan path/to/directory --follow-links
```

3. View Results:
```bash
# List all scans
python -m file_scanner list

# View detailed statistics
python -m file_scanner stats <scan_id>

# View files with filtering
python -m file_scanner files <catalog_id> --pattern ".pdf"

# View directory tree
python -m file_scanner tree <catalog_id>
```

## Project Structure

```
file_scanner/
├── core/              # Domain Layer
│   ├── models.py     # Domain models
│   └── scanner.py    # Core scanning logic
├── database/         # Data Layer
│   ├── base.py      # Abstract database
│   ├── stats.py     # Statistics storage
│   └── catalog.py   # File catalog storage
├── ui/              # Presentation Layer
│   ├── cli.py      # Command interface
│   └── formatters.py # Output formatting
└── utils/           # Shared Utilities
    └── formatting.py # Formatting helpers
```

## Features

1. File Analysis:
   - Total file count and size
   - File type distribution
   - Hidden file detection
   - Creation/modification dates

2. Directory Analysis:
   - Directory structure visualization
   - Depth analysis
   - Path relationships

3. Database Storage:
   - Historical scan data
   - Detailed file catalogs
   - Query capabilities

4. Rich Output:
   - Progress tracking
   - Colorized display
   - Tree visualization
   - Formatted tables

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
