#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the LLM Frontend application"""
    project_root = Path(__file__).parent
    
    if not (project_root / "backend").exists():
        print("Error: Backend directory not found!")
        sys.exit(1)
    
    os.chdir(project_root)
    
    if not (project_root / "backend" / "app").exists():
        print("Error: App directory not found in backend!")
        sys.exit(1)
    
    print("Starting LLM Frontend with uv...")
    print("Backend will be available at http://localhost:8000")
    print("Frontend will be available at http://localhost:8000/")
    print("Press Ctrl+C to stop")
    
    try:
        # Load .env file
        env_file = project_root / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root / "backend")
        
        subprocess.run([
            "uv", "run", "python", "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], env=env, cwd=project_root / "backend")
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting server: {e}")
        print("Make sure uv is installed: curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)

if __name__ == "__main__":
    main()