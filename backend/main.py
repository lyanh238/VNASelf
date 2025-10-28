"""
Main entry point for the VNASelf backend API
"""

from backend_api import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
