#!/usr/bin/env python3
"""
Flask server providing API endpoints for file operations.

This server stores and serves files locally (no external server dependencies).

Endpoints:
    GET/POST /api/download          - Download files from today's timestamp directory
    POST     /api/upload            - Upload file to server's storage
    GET      /api/health            - Health check endpoint
    GET      /api/list-files        - List all stored files
    GET      /api/file/<type>/<path> - Download specific file by type and path
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
BASE_FOLDER = Path('/tools/trader_sender/data/')
ALLOWED_EXTENSIONS = None  # None = allow all file types
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

app.config['BASE_FOLDER'] = BASE_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


# ============================================================================
# Utility Functions (standalone - no external dependencies)
# ============================================================================

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


# Note: Removed external download/upload functions
# This server stores and serves files locally only


# ============================================================================
# Initialize directories
# ============================================================================
ensure_directory_exists(BASE_FOLDER)


def allowed_file(filename):
    """Check if file has an allowed extension."""
    if ALLOWED_EXTENSIONS is None:
        return True  # Allow all file types
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def home():
    ""# Home endpoint."""
    return jsonify({
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'service': 'Traders API'
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Traders API'
    }), 200


@app.route('/api/download', methods=['POST', 'GET'])
def download_file():
    """
    Download files from the current timestamp directory (today's date).
    
    No parameters required - automatically uses today's date directory (MM-DD-YY).
    
    Returns:
        - If one file exists: Downloads the file
        - If multiple files exist: JSON list of available files
        - If no files exist: JSON error message
    """
    try:
        # Get today's timestamp directory
        today = datetime.now().strftime('%m-%d-%y')
        today_dir = BASE_FOLDER / today
        
        # Check if today's directory exists
        if not today_dir.exists() or not today_dir.is_dir():
            return jsonify({
                'success': False,
                'error': f'No downloads directory found for today ({today})',
                'directory': today
            }), 404
        
        # Get all files in today's directory (excluding hidden files and directories)
        all_files = [f for f in today_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
        
        # If no files found
        if not all_files:
            return jsonify({
                'success': False,
                'error': f'No files found in today\'s directory ({today})',
                'directory': today
            }), 404
        
        # If only one file, download it directly
        if len(all_files) == 1:
            file_path = all_files[0]
            return send_file(
                file_path,
                as_attachment=True,
                download_name=file_path.name
            )
        
        # If multiple files, return list for user to choose
        files_info = [
            {
                'filename': f.name,
                'size_bytes': f.stat().st_size,
                'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                'download_url': f'/api/file/downloads/{today}/{f.name}'
            }
            for f in sorted(all_files, key=lambda p: p.stat().st_mtime, reverse=True)
        ]
        
        return jsonify({
            'success': True,
            'message': f'Multiple files found in today\'s directory ({today})',
            'directory': today,
            'count': len(all_files),
            'files': files_info
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload a file to the server's uploads folder.
    
    Form data:
        file: File (required)
        folder: Target folder - 'uploads' or 'downloads' (optional, default: 'uploads')
    
    Returns:
        JSON response with upload status
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'File type not allowed'
            }), 400
        
        # Determine target folder (uploads or downloads)
        target_folder = request.form.get('folder', 'uploads').lower()
        if target_folder == 'downloads':
            base_folder = BASE_FOLDER
        else:
            base_folder = BASE_FOLDER
        
        # Create timestamp directory
        timestamp = datetime.now().strftime('%m-%d-%y')
        timestamp_dir = base_folder / timestamp
        
        # Ensure timestamp directory exists
        ensure_directory_exists(timestamp_dir)
        
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Save file in timestamp directory
        file_path = timestamp_dir / filename
        file.save(file_path)
        
        response_data = {
            'success': True,
            'message': 'File uploaded successfully',
            'filename': filename,
            'directory': timestamp,
            'file_path': str(file_path),
            'folder': target_folder,
            'size_bytes': file_path.stat().st_size
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/list-files', methods=['GET'])
def list_files():
    """
    List all downloaded and uploaded files.
    
    Query parameters:
        type: 'downloads' or 'uploads' (optional, default: both)
    
    Returns:
        JSON response with list of files
    """
    try:
        file_type = request.args.get('type', 'both')
        
        files = {
            'downloads': [],
            'uploads': []
        }
        
        if file_type in ['both', 'downloads']:
            # Search recursively in subdirectories (date folders), excluding hidden files
            downloads = [f for f in BASE_FOLDER.glob('**/*') if f.is_file() and not f.name.startswith('.')]
            files['downloads'] = [
                {
                    'filename': f.name,
                    'directory': f.parent.name if f.parent != BASE_FOLDER else '',
                    'path': str(f),
                    'relative_path': str(f.relative_to(BASE_FOLDER)),
                    'size_bytes': f.stat().st_size,
                    'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in sorted(downloads, key=lambda p: p.stat().st_mtime, reverse=True)
            ]
        
        if file_type in ['both', 'uploads']:
            # Search recursively in subdirectories (date folders), excluding hidden files
            uploads = [f for f in BASE_FOLDER.glob('**/*') if f.is_file() and not f.name.startswith('.')]
            files['uploads'] = [
                {
                    'filename': f.name,
                    'directory': f.parent.name if f.parent != BASE_FOLDER else '',
                    'path': str(f),
                    'relative_path': str(f.relative_to(BASE_FOLDER)),
                    'size_bytes': f.stat().st_size,
                    'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in sorted(uploads, key=lambda p: p.stat().st_mtime, reverse=True)
            ]
        
        return jsonify({
            'success': True,
            'files': files
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/file/<file_type>/<path:filepath>', methods=['GET'])
def get_file(file_type, filepath):
    """
    Download a specific file.
    
    Path parameters:
        file_type: 'downloads' or 'uploads'
        filepath: Path to the file (can include directory, e.g., '10-15-25/traders.csv')
    
    Returns:
        File download
    """
    try:
        # Secure the filepath components
        filepath_parts = filepath.split('/')
        secure_parts = [secure_filename(part) for part in filepath_parts]
        secure_filepath = '/'.join(secure_parts)
        
        # Determine directory based on file_type
        if file_type == 'downloads':
            base_directory = BASE_FOLDER
        elif file_type == 'uploads':
            base_directory = BASE_FOLDER
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid file_type. Must be "downloads" or "uploads"'
            }), 400
        
        file_path = base_directory / secure_filepath
        
        # Security check: ensure file is within the base directory
        try:
            file_path.resolve().relative_to(base_directory.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 400
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_path.name
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size is {MAX_CONTENT_LENGTH // (1024*1024)}MB'
    }), 413


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Traders API Server')
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    args = parser.parse_args()
    
    print(f"""
{'='*60}
Traders API Server Starting
{'='*60}
Host: {args.host}
Port: {args.port}
Debug: {args.debug}

Endpoints:
  GET      /api/health                - Health check
  GET/POST /api/download              - Download files from today's timestamp directory
  POST     /api/upload                - Upload file to server's storage
  GET      /api/list-files            - List all stored files
  GET      /api/file/<type>/<path>    - Download specific file

Upload folder:   {BASE_FOLDER.absolute()}
Download folder: {BASE_FOLDER.absolute()}
{'='*60}
    """)
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

