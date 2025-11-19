"""
Main entry point for the VNASelf backend API
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root before importing app
# override=True ensures .env file values take precedence over system environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)

from backend_api import app

if __name__ == "__main__":
    import uvicorn
    # Disable reload on Windows to avoid multiprocessing spawn issues
    # On Windows, reload can cause KeyboardInterrupt during process spawning
    use_reload = sys.platform != "win32"
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=use_reload)
