#!/usr/bin/env python3
"""
Run script for Finvo AI Streamlit application
"""

import subprocess
import sys
from pathlib import Path

def main():
    # Path to the Streamlit app
    app_path = Path(__file__).parent / "src" / "finvo_ai_streamlit" / "app.py"
    
    if not app_path.exists():
        print(f"Error: Streamlit app not found at {app_path}")
        sys.exit(1)
    
    # Run Streamlit with uv
    try:
        subprocess.run([
            "uv", "run", "streamlit", "run", str(app_path),
            "--server.port", "8501",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down Streamlit app...")

if __name__ == "__main__":
    main()