# Traders API Server

A Flask-based REST API server for managing file uploads and downloads.

## Features

- **Upload Files**: Accept any file type uploads and store them on the server
- **Download Files**: Serve files from the server's storage
- **File Management**: List and retrieve stored files
- **Health Check**: Monitor server status
- **Standalone**: No external server dependencies - all files stored locally

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure required directories exist (created automatically on first run):
   - `/tools/trader_sender/data/` - Stores uploaded and downloaded files in date-based subdirectories

## Running the Server

### Basic Usage
```bash
python server.py
```

### With Custom Configuration
```bash
# Custom host and port
python server.py --host 0.0.0.0 --port 8080

# Enable debug mode
python server.py --debug
```

The server will start on `http://0.0.0.0:5000` by default.

## API Endpoints

### Health Check
```
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-15T12:00:00",
  "service": "Traders API"
}
```

---

### Download Files
```
GET  /api/download
POST /api/download
```

Downloads files from **today's timestamp directory** (current date in MM-DD-YY format).

**No parameters required!** Automatically uses today's date.

**Response Behaviors:**

1. **One file in today's directory:** Downloads the file directly
2. **Multiple files:** Returns JSON list of available files with download URLs
3. **No files:** Returns JSON error message

**Response for single file:**
- Direct file download

**Response for multiple files:**
```json
{
  "success": true,
  "message": "Multiple files found in today's directory (10-15-25)",
  "directory": "10-15-25",
  "count": 3,
  "files": [
    {
      "filename": "traders.csv",
      "size_bytes": 1024,
      "modified": "2025-10-15T12:00:00",
      "download_url": "/api/file/downloads/10-15-25/traders.csv"
    },
    {
      "filename": "accounts.csv",
      "size_bytes": 2048,
      "modified": "2025-10-15T11:30:00",
      "download_url": "/api/file/downloads/10-15-25/accounts.csv"
    }
  ]
}
```

**Example using curl:**
```bash
# Download from today's directory (no parameters needed)
curl http://localhost:5000/api/download -O

# If multiple files, get the list first
curl http://localhost:5000/api/download

# Then download specific file using URL from response
curl -O http://localhost:5000/api/file/downloads/10-15-25/traders.csv
```

---

### Upload File
```
POST /api/upload
```

Uploads a file to the server's storage. **Supports any file type.**

**Form Data:**
- `file`: Any file type (required)
- `folder`: Target folder - `uploads` or `downloads` (optional, default: `uploads`)

**Response:**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "filename": "traders.csv",
  "directory": "10-15-25",
  "file_path": "./uploads/10-15-25/traders.csv",
  "folder": "uploads",
  "size_bytes": 1024
}
```

**Note:** Files are stored in timestamp directories with format `MM-DD-YY/` (e.g., `uploads/10-15-25/traders.csv`)

**Example using curl:**
```bash
# Upload to uploads folder (default)
curl -X POST http://localhost:5000/api/upload \
  -F "file=@traders.csv"

# Upload to downloads folder
curl -X POST http://localhost:5000/api/upload \
  -F "file=@traders.csv" \
  -F "folder=downloads"
```

---

### List Files
```
GET /api/list-files?type=both
```

Lists all files in the uploads and downloads directories.

**Query Parameters:**
- `type`: `downloads`, `uploads`, or `both` (default: `both`)

**Response:**
```json
{
  "success": true,
  "files": {
    "downloads": [
      {
        "filename": "traders_20231015_120000.csv",
        "path": "./downloads/traders_20231015_120000.csv",
        "size_bytes": 2048,
        "modified": "2025-10-15T12:00:00"
      }
    ],
    "uploads": [
      {
        "filename": "20231015_120000_traders.csv",
        "path": "./uploads/20231015_120000_traders.csv",
        "size_bytes": 1024,
        "modified": "2025-10-15T12:00:00"
      }
    ]
  }
}
```

**Example using curl:**
```bash
# List all files
curl http://localhost:5000/api/list-files

# List only downloads
curl http://localhost:5000/api/list-files?type=downloads

# List only uploads
curl http://localhost:5000/api/list-files?type=uploads
```

**Response includes directory information:**
```json
{
  "success": true,
  "files": {
    "uploads": [
      {
        "filename": "traders.csv",
        "directory": "10-15-25",
        "relative_path": "10-15-25/traders.csv",
        "size_bytes": 1024,
        "modified": "2025-10-15T12:00:00"
      }
    ]
  }
}
```

---

### Get File
```
GET /api/file/<file_type>/<filepath>
```

Downloads a specific file using its full path.

**Path Parameters:**
- `file_type`: `downloads` or `uploads`
- `filepath`: Full path to file including directory (e.g., `10-15-25/traders.csv`, `10-15-25/document.pdf`)

**Response:**
File download (any type)

**Example using curl:**
```bash
# Download from uploads folder
curl -O http://localhost:5000/api/file/uploads/10-15-25/traders.csv

# Download from downloads folder
curl -O http://localhost:5000/api/file/downloads/10-15-25/report.csv
```

---

## Standalone Scripts

The project also includes standalone command-line scripts:

### get_traders.py
Downloads files from a remote server.

```bash
# Basic usage
python get_traders.py

# Custom download directory
python get_traders.py --dir ./data/files/

# Custom server URL
python get_traders.py --server https://api.example.com/download

# Both custom
python get_traders.py --dir ./downloads --server https://custom-server.com/download
```

### upload_traders.py
Uploads files to a remote server. **Supports any file type.**

```bash
# Upload all files from current directory
python upload_traders.py

# Upload a specific file
python upload_traders.py --file document.pdf

# Upload from a specific directory
python upload_traders.py --dir ./data/files/

# Upload to custom server
python upload_traders.py --server https://custom-server.com/upload

# Combine options
python upload_traders.py --file traders.csv --server https://api.example.com/upload
```

## Configuration

### Server Configuration
Edit the following variables in `server.py`:

```python
BASE_FOLDER = Path('./uploads')
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
```

### Script Defaults
Edit the following variables in `get_traders.py` and `upload_traders.py`:

**get_traders.py:**
```python
DEFAULT_DIR = './downloads'
DEFAULT_SERVER = 'https://api.example.com/download'
```

**upload_traders.py:**
```python
DEFAULT_FILE_DIR = '.'
DEFAULT_SERVER = 'https://api.example.com/upload'
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `400` - Bad request (invalid parameters)
- `404` - File or endpoint not found
- `413` - File too large (max 50MB)
- `500` - Internal server error

All error responses follow this format:
```json
{
  "success": false,
  "error": "Error message here"
}
```

## File Naming

### Uploaded Files
- Structure: `MM-DD-YY/filename.ext` (timestamp as directory)
- Example: `10-15-25/traders.csv`, `10-15-25/document.pdf`, `10-15-25/data.json`
- The timestamp directory represents the date when files were uploaded (month-day-year)
- Multiple files uploaded on the same day go into the same directory

### Downloaded Files
- Structure: `MM-DD-YY/filename.ext` (timestamp as directory)
- Example: `10-15-25/report.csv`, `10-15-25/invoice.pdf`
- The timestamp directory represents the date when files were made available
- Multiple files from the same day go into the same directory

## Security Notes

- All file types are accepted for uploads (configurable via `ALLOWED_EXTENSIONS` in `server.py`)
- Filenames are sanitized using `werkzeug.utils.secure_filename`
- Maximum file size is 50MB (configurable)
- Server binds to `0.0.0.0` by default (accessible from network)
- Hidden files (starting with `.`) are excluded from listings and uploads

## Requirements

- Python 3.7+
- Flask 3.0.0+
- werkzeug 3.0.0+

See `requirements.txt` for complete dependencies.

**Note:** This server is fully standalone and only stores/serves files locally. No external server dependencies.

