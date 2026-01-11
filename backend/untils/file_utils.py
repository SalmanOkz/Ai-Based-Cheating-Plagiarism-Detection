"""
File utility functions
FIXED: Added missing read_json function
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

def ensure_directory(directory: Path):
    """Ensure directory exists"""
    if isinstance(directory, str):
        directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

def save_json(data: Dict, filepath: Path, indent: int = 2):
    """Save data as JSON file"""
    if isinstance(filepath, str):
        filepath = Path(filepath)
    ensure_directory(filepath.parent)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)

def read_json(filepath: Path) -> Optional[Dict]:
    """Read JSON file"""
    if isinstance(filepath, str):
        filepath = Path(filepath)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON from {filepath}: {e}")
        return None

def read_file(filepath: str, encoding: str = 'utf-8') -> Optional[str]:
    """Read file content"""
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except (FileNotFoundError, UnicodeDecodeError):
        # Try with different encoding
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None

def write_file(filepath: str, content: str, encoding: str = 'utf-8'):
    """Write content to file"""
    filepath_obj = Path(filepath)
    ensure_directory(filepath_obj.parent)
    with open(filepath, 'w', encoding=encoding) as f:
        f.write(content)

def file_exists(filepath: str) -> bool:
    """Check if file exists"""
    return os.path.exists(filepath) and os.path.isfile(filepath)

def get_file_size(filepath: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0