#!/usr/bin/env python3
"""
File System MCP Server
Provides safe file operations in a playground directory.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("FileSystem")

# Define the safe playground directory
PLAYGROUND_DIR = Path(__file__).parent.parent.parent / "playground"
PLAYGROUND_DIR.mkdir(exist_ok=True)

def _ensure_safe_path(path: str) -> Path:
    """Ensure the path is within the playground directory."""
    try:
        # Resolve the path and ensure it's within playground
        full_path = (PLAYGROUND_DIR / path).resolve()
        playground_abs = PLAYGROUND_DIR.resolve()
        
        # Check if the resolved path is within the playground directory
        if not str(full_path).startswith(str(playground_abs)):
            raise ValueError(f"Path {path} is outside the safe playground directory")
            
        return full_path
    except Exception as e:
        raise ValueError(f"Invalid path {path}: {str(e)}")

@mcp.tool
def list_files(directory: str = ".") -> Dict[str, Any]:
    """List files and directories in the specified playground directory."""
    try:
        target_path = _ensure_safe_path(directory)
        
        if not target_path.exists():
            return {"error": f"Directory {directory} does not exist"}
            
        if not target_path.is_dir():
            return {"error": f"{directory} is not a directory"}
        
        items = []
        for item in sorted(target_path.iterdir()):
            relative_path = item.relative_to(PLAYGROUND_DIR)
            items.append({
                "name": item.name,
                "path": str(relative_path),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        
        return {
            "directory": directory,
            "items": items,
            "total_items": len(items)
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool
def read_file(file_path: str) -> Dict[str, Any]:
    """Read the contents of a file in the playground directory."""
    try:
        target_path = _ensure_safe_path(file_path)
        
        if not target_path.exists():
            return {"error": f"File {file_path} does not exist"}
            
        if not target_path.is_file():
            return {"error": f"{file_path} is not a file"}
        
        # Check file size (limit to 1MB for safety)
        if target_path.stat().st_size > 1024 * 1024:
            return {"error": "File too large (>1MB)"}
        
        content = target_path.read_text(encoding='utf-8')
        return {
            "file_path": file_path,
            "content": content,
            "size": len(content)
        }
    except UnicodeDecodeError:
        return {"error": "File contains non-text data"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool
def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """Write content to a file in the playground directory."""
    try:
        target_path = _ensure_safe_path(file_path)
        
        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Limit content size (1MB)
        if len(content) > 1024 * 1024:
            return {"error": "Content too large (>1MB)"}
        
        target_path.write_text(content, encoding='utf-8')
        return {
            "file_path": file_path,
            "bytes_written": len(content.encode('utf-8')),
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool
def create_directory(directory_path: str) -> Dict[str, Any]:
    """Create a directory in the playground."""
    try:
        target_path = _ensure_safe_path(directory_path)
        
        if target_path.exists():
            return {"error": f"Directory {directory_path} already exists"}
        
        target_path.mkdir(parents=True)
        return {
            "directory_path": directory_path,
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool
def delete_file(file_path: str) -> Dict[str, Any]:
    """Delete a file from the playground directory."""
    try:
        target_path = _ensure_safe_path(file_path)
        
        if not target_path.exists():
            return {"error": f"File {file_path} does not exist"}
            
        if not target_path.is_file():
            return {"error": f"{file_path} is not a file"}
        
        target_path.unlink()
        return {
            "file_path": file_path,
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.resource("file://playground_info")
def get_playground_info() -> str:
    """Get information about the playground directory."""
    return json.dumps({
        "playground_path": str(PLAYGROUND_DIR),
        "description": "Safe file operations sandbox",
        "max_file_size": "1MB",
        "allowed_operations": ["list", "read", "write", "create_dir", "delete"]
    })

if __name__ == "__main__":
    mcp.run()