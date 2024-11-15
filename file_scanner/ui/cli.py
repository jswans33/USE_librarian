"""Command-line interface handling."""
import argparse
import sys
from pathlib import Path
from typing import NoReturn
from rich.console import Console
from rich import print as rprint

from ..core.models import ScanOptions
from ..core.scanner import FileScanner
from ..database.stats import StatsManager
from ..database.catalog import CatalogManager
from ..utils.formatting import (
    create_scan_header,
    create_scan_summary,
    create_file_table,
    create_directory_tree
)

def create_arg_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Fast directory scanner with detailed file cataloging"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan a directory')
    scan_parser.add_argument(
        'directory',
        type=str,
        help='Directory path to scan'
    )
    scan_parser.add_argument(
        '--depth',
        type=int,
        help='Maximum depth for directory tree display'
    )
    scan_parser.add_argument(
        '--no-hidden',
        action='store_true',
        help='Ignore hidden files and directories'
    )
    scan_parser.add_argument(
        '--ignore',
        type=str,
        nargs='+',
        help='Patterns to ignore (e.g., *.tmp)'
    )
    scan_parser.add_argument(
        '--follow-links',
        action='store_true',
        help='Follow symbolic links'
    )
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all scans')
    
    # Files command
    files_parser = subparsers.add_parser('files', help='Show detailed file information')
    files_parser.add_argument(
        'catalog_id',
        type=int,
        help='Catalog ID to show files from'
    )
    files_parser.add_argument(
        '--pattern',
        type=str,
        help='Filter files by path pattern'
    )
    
    # Tree command
    tree_parser = subparsers.add_parser('tree', help='Show directory tree')
    tree_parser.add_argument(
        'catalog_id',
        type=int,
        help='Catalog ID to show tree for'
    )
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show scan statistics')
    stats_parser.add_argument(
        'scan_id',
        type=int,
        help='Scan ID to analyze'
    )
    
    # Database options
    for p in [scan_parser, list_parser, files_parser, tree_parser, stats_parser]:
        p.add_argument(
            '--stats-db',
            type=str,
            default='file_stats.db',
            help='Path to statistics database'
        )
        p.add_argument(
            '--catalog-db',
            type=str,
            default='file_catalog.db',
            help='Path to catalog database'
        )
    
    return parser

def handle_scan_command(args: argparse.Namespace, console: Console) -> NoReturn:
    """Handle scan command execution."""
    try:
        # Configure scan options
        options = ScanOptions(
            max_depth=args.depth,
            follow_links=args.follow_links,
            ignore_patterns=args.ignore,
            include_hidden=not args.no_hidden
        )
        
        # Initialize managers
        stats_manager = StatsManager(args.stats_db)
        catalog_manager = CatalogManager(args.catalog_db)
        
        # Perform scan
        scanner = FileScanner(args.directory, options)
        scan_result = scanner.scan()
        
        # Save results to both databases
        rprint("\n[yellow]Saving results to databases...[/]")
        scan_id = stats_manager.save_scan_results(scan_result)
        catalog_id = catalog_manager.create_catalog(scan_result)
        
        # Display results
        for line in create_scan_header(scan_result):
            console.print(line)
        
        console.print("\n[bold]File Type Distribution:[/]")
        console.print(create_scan_summary(scan_result, console))
        
        rprint(f"\n[green]Scan completed successfully![/]")
        rprint(f"[bold]Scan ID:[/] {scan_id}")
        rprint(f"[bold]Catalog ID:[/] {catalog_id}")
        rprint("\nView results with:")
        rprint(f"  python -m file_scanner stats {scan_id}")
        rprint(f"  python -m file_scanner files {catalog_id}")
        rprint(f"  python -m file_scanner tree {catalog_id}")
        
    except Exception as e:
        rprint(f"[red]Error during scan: {str(e)}[/]")
        sys.exit(1)

def main() -> NoReturn:
    """Main entry point for the CLI."""
    parser = create_arg_parser()
    args = parser.parse_args()
    console = Console()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'scan':
            handle_scan_command(args, console)
        elif args.command == 'list':
            stats_manager = StatsManager(args.stats_db)
            stats_manager.list_scans()
        elif args.command == 'files':
            catalog_manager = CatalogManager(args.catalog_db)
            catalog_manager.get_file_info(args.catalog_id, args.pattern)
        elif args.command == 'tree':
            catalog_manager = CatalogManager(args.catalog_db)
            catalog_manager.get_directory_tree(args.catalog_id)
        elif args.command == 'stats':
            stats_manager = StatsManager(args.stats_db)
            stats_manager.get_scan_details(args.scan_id)
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user.[/]")
        sys.exit(0)
    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/]")
        sys.exit(1)
