"""Test script to verify module imports."""
import sys
from pathlib import Path
from importlib import import_module

def test_import(module_path: str) -> None:
    """Test importing a module and print result.
    
    Args:
        module_path: Dotted path to module
    """
    try:
        print(f"Testing import of {module_path}...")
        module = import_module(module_path)
        print(f"✓ Successfully imported {module_path}")
        
        # Print what was imported
        if hasattr(module, '__all__'):
            print(f"  Exports: {module.__all__}")
    except ImportError as e:
        print(f"✗ Failed to import {module_path}")
        print(f"  Error: {str(e)}")
    except Exception as e:
        print(f"✗ Unexpected error importing {module_path}")
        print(f"  Error: {str(e)}")
    print()

def main():
    """Test all module imports."""
    modules = [
        'file_scanner',
        'file_scanner.core',
        'file_scanner.core.models',
        'file_scanner.core.scanner',
        'file_scanner.database',
        'file_scanner.database.base',
        'file_scanner.database.stats',
        'file_scanner.database.catalog',
        'file_scanner.ui',
        'file_scanner.ui.cli',
        'file_scanner.ui.formatters',
        'file_scanner.utils'
    ]
    
    for module in modules:
        test_import(module)

if __name__ == '__main__':
    main()
