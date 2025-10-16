#!/usr/bin/env python3
"""
Upload file(s) to a server.

Usage:
    python upload_traders.py
    python upload_traders.py --file path/to/file.ext
    python upload_traders.py --dir path/to/directory
    python upload_traders.py --server https://api.example.com/upload
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List
import requests


# Default configuration variables
DEFAULT_FILE = None  # Default file (None = not used)
DEFAULT_FILE_DIR = '.'  # Default directory containing files
DEFAULT_SERVER = 'http://profitvestai.lnk.mn/api/upload'  # Default server URL


def get_files_from_directory(directory: Path) -> List[Path]:
    """
    Get all files from a directory (excluding hidden files and subdirectories).
    
    Args:
        directory: Path to the directory
        
    Returns:
        List of file paths
    """
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a valid directory")
        return []
    
    # Get all files, excluding hidden files and directories
    files = [f for f in directory.iterdir() if f.is_file() and not f.name.startswith('.')]
    
    if not files:
        print(f"Warning: No files found in '{directory}'")
    
    return files


def upload_file_to_server(
    file_path: Path,
    server_url: str
) -> bool:
    """
    Upload a single file to the server.
    
    Args:
        file_path: Path to the file
        server_url: URL of the server endpoint
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"  Uploading: {file_path.name}...", end=' ')
        
        # Prepare the file for upload
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            
            # Prepare headers
            headers = {}
            
            # Make the upload request
            response = requests.post(
                server_url,
                files=files,
                headers=headers,
                timeout=300
            )
            
            # Check response
            if response.status_code in (200, 201):
                print("✓ Success")
                return True
            else:
                print(f"✗ Failed (HTTP {response.status_code})")
                print(f"    Response: {response.text[:200]}")
                return False
    
    except requests.exceptions.ConnectionError:
        print("✗ Failed (Connection Error)")
        print(f"    Could not connect to server: {server_url}")
        return False
    except requests.exceptions.Timeout:
        print("✗ Failed (Timeout)")
        print(f"    Request timed out after 300 seconds")
        return False
    except Exception as e:
        print(f"✗ Failed")
        print(f"    Error: {str(e)}")
        return False


def main():
    """Main function to handle command-line arguments and orchestrate the upload."""
    parser = argparse.ArgumentParser(
        description='Upload file(s) to a server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python upload_traders.py
  python upload_traders.py --file document.pdf
  python upload_traders.py --dir ./data/files/
  python upload_traders.py --server https://custom-server.com/upload
  python upload_traders.py --file traders.csv --server https://api.example.com/upload
        """
    )
    
    # File input arguments
    parser.add_argument(
        '--file',
        type=str,
        default=DEFAULT_FILE,
        help=f'Path to a single file to upload (default: {DEFAULT_FILE}, uses --dir instead)'
    )
    parser.add_argument(
        '--dir',
        type=str,
        default=DEFAULT_FILE_DIR,
        help=f'Path to a directory containing files to upload (default: "{DEFAULT_FILE_DIR}")'
    )
    
    # Server configuration
    parser.add_argument(
        '--server',
        type=str,
        default=DEFAULT_SERVER,
        help=f'Server URL endpoint for file upload (default: {DEFAULT_SERVER})'
    )
    
    args = parser.parse_args()
    
    # Collect all files to upload
    files_to_upload = []
    
    # If --file is specified, use only that file
    if args.file:
        file_path = Path(args.file)
        print(f"Processing single file: {file_path}")
        if file_path.exists() and file_path.is_file():
            files_to_upload.append(file_path)
        else:
            print(f"Error: File '{file_path}' does not exist or is not a file")
            sys.exit(1)
    else:
        # Otherwise, use dir (default is current directory)
        dir_path = Path(args.dir)
        print(f"Processing files from directory: {dir_path}")
        files = get_files_from_directory(dir_path)
        files_to_upload.extend(files)
    
    if not files_to_upload:
        print("\nNo files found to upload")
        sys.exit(1)
    
    print(f"\nTotal files to upload: {len(files_to_upload)}")
    print(f"Server: {args.server}\n")
    
    # Upload files to server
    successful_uploads = 0
    failed_uploads = 0
    
    for file_path in files_to_upload:
        success = upload_file_to_server(
            file_path,
            args.server
        )
        
        if success:
            successful_uploads += 1
        else:
            failed_uploads += 1
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Upload Summary:")
    print(f"  Successful: {successful_uploads}")
    print(f"  Failed:     {failed_uploads}")
    print(f"  Total:      {len(files_to_upload)}")
    print(f"{'='*50}\n")
    
    # Exit with appropriate code
    sys.exit(0 if failed_uploads == 0 else 1)


if __name__ == '__main__':
    main()

