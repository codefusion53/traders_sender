#!/usr/bin/env python3
"""
Download file(s) from a server and store them locally.

Usage:
    python get_traders.py
    python get_traders.py --dir ./downloads
    python get_traders.py --server https://api.example.com/download
"""

import argparse
import os
import sys
from pathlib import Path
import requests


# Default configuration variables
DEFAULT_DIR = './downloads'  # Default directory to save downloaded files
DEFAULT_SERVER = 'http://profitvestai.lnk.mn/api/download'  # Default server URL


def ensure_directory_exists(directory: Path) -> bool:
    """
    Ensure the target directory exists, create if it doesn't.
    
    Args:
        directory: Path to the directory
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error: Could not create directory '{directory}': {str(e)}")
        return False


def download_file_from_server(
    server_url: str,
    save_dir: Path,
    filename: str = None
) -> bool:
    """
    Download a file from the server.
    
    Args:
        server_url: URL of the server endpoint
        save_dir: Directory to save the downloaded file
        filename: Optional filename to save as (extracted from response if not provided)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"  Downloading from: {server_url}...", end=' ')
        
        # Make the download request
        response = requests.get(
            server_url,
            timeout=300,
            stream=True
        )
        
        # Check response
        if response.status_code == 200:
            content_disposition = response.headers.get('Content-Disposition', '')
            content_type = response.headers.get('Content-Type', '')
            
            # Check if response is JSON (multiple files available)
            if 'application/json' in content_type:
                import json
                json_response = response.json()
                if json_response.get('success') and 'files' in json_response:
                    print(f"\n    Multiple files available ({json_response['count']} files):")
                    for i, file_info in enumerate(json_response['files'], 1):
                        print(f"      {i}. {file_info['filename']}")
                    
                    # Download the most recent file (first in the list)
                    most_recent_file = json_response['files'][0]
                    download_url = most_recent_file['download_url']
                    filename_to_use = most_recent_file['filename']
                    
                    print(f"\n    Downloading most recent file: {filename_to_use}")
                    
                    # Construct full URL (handle relative paths)
                    if download_url.startswith('/'):
                        # Extract base URL from server_url
                        from urllib.parse import urlparse
                        parsed = urlparse(server_url)
                        base_url = f"{parsed.scheme}://{parsed.netloc}"
                        full_download_url = base_url + download_url
                    else:
                        full_download_url = download_url
                    
                    # Recursively call this function with the specific file URL
                    return download_file_from_server(
                        full_download_url,
                        save_dir,
                        filename_to_use
                    )
                else:
                    print(f"\n    Unexpected JSON response: {json_response}")
                    return False
            
            # Determine filename
            if not filename:
                # Try to get filename from Content-Disposition header
                if 'filename=' in content_disposition:
                    # Extract filename from header (handles multiple formats)
                    # Format: attachment; filename="file.ext" or filename=file.ext
                    parts = content_disposition.split('filename=')
                    if len(parts) > 1:
                        # Get the part after 'filename='
                        filename_part = parts[1].split(';')[0].strip()
                        # Remove quotes if present
                        filename = filename_part.strip('"\'')
                
                if not filename:
                    # Use default filename with timestamp and generic extension
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    # Try to get file extension from Content-Type header
                    content_type = response.headers.get('Content-Type', '')
                    ext = 'dat'  # Default extension
                    if 'csv' in content_type:
                        ext = 'csv'
                    elif 'json' in content_type:
                        ext = 'json'
                    elif 'pdf' in content_type:
                        ext = 'pdf'
                    elif 'xml' in content_type:
                        ext = 'xml'
                    elif 'text' in content_type:
                        ext = 'txt'
                    
                    filename = f'{timestamp}.{ext}'
            
            # Save the file
            file_path = save_dir / filename
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"[OK] Success")
            print(f"    Saved to: {file_path}")
            return True
        else:
            print(f"[FAIL] Failed (HTTP {response.status_code})")
            print(f"    Response: {response.text[:200]}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("[FAIL] Failed (Connection Error)")
        print(f"    Could not connect to server: {server_url}")
        return False
    except requests.exceptions.Timeout:
        print("[FAIL] Failed (Timeout)")
        print(f"    Request timed out after 300 seconds")
        return False
    except Exception as e:
        print(f"[FAIL] Failed")
        print(f"    Error: {str(e)}")
        return False


def main():
    """Main function to handle command-line arguments and orchestrate the download."""
    parser = argparse.ArgumentParser(
        description='Download file(s) from a server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python get_traders.py
  python get_traders.py --dir ./data/files/
  python get_traders.py --server https://api.example.com/download
  python get_traders.py --dir ./downloads --server https://custom-server.com/download
        """
    )
    
    # Directory argument
    parser.add_argument(
        '--dir',
        type=str,
        default=DEFAULT_DIR,
        help=f'Directory to save downloaded files (default: "{DEFAULT_DIR}")'
    )
    
    # Server configuration
    parser.add_argument(
        '--server',
        type=str,
        default=DEFAULT_SERVER,
        help=f'Server URL endpoint for file download (default: {DEFAULT_SERVER})'
    )
    
    args = parser.parse_args()
    
    # Prepare download directory
    save_dir = Path(args.dir)
    print(f"Download directory: {save_dir}")
    
    if not ensure_directory_exists(save_dir):
        sys.exit(1)
    
    print(f"Server: {args.server}\n")
    
    # Download file from server
    success = download_file_from_server(
        args.server,
        save_dir
    )
    
    # Print summary
    print(f"\n{'='*50}")
    if success:
        print("Download completed successfully!")
    else:
        print("Download failed.")
    print(f"{'='*50}\n")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

