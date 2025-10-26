#!/usr/bin/env python3
"""
VNASelf - All-in-One Startup Script
Tự động build frontend và chạy backend trong một file duy nhất
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path
import webbrowser
from datetime import datetime

def print_banner():
    """In banner khởi động"""
    print("=" * 60)
    print("VNASelf Multi-Agent System")
    print("AI Assistant for Healthcare & Scheduling")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def check_environment():
    """Kiểm tra environment variables"""
    print("\n[INFO] Checking environment...")
    
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing_vars)}")
        print("[INFO] Please create a .env file with:")
        print("OPENAI_API_KEY=your-openai-api-key-here")
        return False
    
    print("[OK] Environment variables are set")
    return True

def check_dependencies():
    """Kiểm tra dependencies"""
    print("\n[INFO] Checking dependencies...")
    
    # Check Python dependencies
    try:
        import fastapi
        import uvicorn
        import langgraph
        import langchain_openai
        print("[OK] Python dependencies are installed")
    except ImportError as e:
        print(f"[ERROR] Missing Python package: {e.name}")
        print("[TIP] Install with: pip install -r requirements.txt")
        return False
    
    # Check Node.js and npm
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"[OK] Node.js version: {result.stdout.strip()}")
        else:
            print("[ERROR] Node.js not found")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("[ERROR] Node.js not found")
        return False
    
    # Skip npm check here - will check during build
    print("[INFO] npm check will be performed during frontend build")
    
    return True

def build_frontend():
    """Build React frontend"""
    print("\n[INFO] Building React frontend...")
    
    deploy_path = Path("deploy")
    if not deploy_path.exists():
        print("[ERROR] Deploy folder not found!")
        return False
    
    try:
        # Install dependencies if needed
        if not (deploy_path / "node_modules").exists():
            print("[INFO] Installing frontend dependencies...")
            result = subprocess.run(
                ["powershell", "-Command", "npm install"], 
                cwd=deploy_path, 
                check=True, 
                timeout=300
            )
            if result.returncode != 0:
                print("[ERROR] Failed to install dependencies")
                return False
        
        # Build for production
        print("[INFO] Building React app...")
        result = subprocess.run(
            ["powershell", "-Command", "npm run build"], 
            cwd=deploy_path, 
            check=True, 
            timeout=300
        )
        
        if result.returncode == 0:
            print("[OK] Frontend built successfully!")
            return True
        else:
            print("[ERROR] Frontend build failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] Build timed out")
        return False
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

def start_backend():
    """Start FastAPI backend"""
    print("\n[INFO] Starting VNASelf Backend...")
    
    try:
        # Import and run the backend
        from backend_api import app
        import uvicorn
        
        print("[INFO] Server starting on http://localhost:8001")
        print("[INFO] API documentation: http://localhost:8001/docs")
        print("[INFO] Press Ctrl+C to stop")
        print("=" * 60)
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down VNASelf...")
        print("[OK] Goodbye!")
    except Exception as e:
        print(f"[ERROR] Backend error: {e}")
        return False

def open_browser():
    """Mở trình duyệt sau khi backend khởi động"""
    def open_delay():
        time.sleep(3)  # Đợi backend khởi động
        try:
            webbrowser.open("http://localhost:8001")
            print("[INFO] Opening browser...")
        except Exception as e:
            print(f"[WARN] Could not open browser: {e}")
            print("[TIP] Please manually open: http://localhost:8001")
    
    # Chạy trong thread riêng để không block
    browser_thread = threading.Thread(target=open_delay, daemon=True)
    browser_thread.start()

def main():
    """Main function"""
    print_banner()
    
    # Kiểm tra environment
    if not check_environment():
        print("\n[ERROR] Environment check failed!")
        print("[TIP] Please set up your environment variables and try again.")
        sys.exit(1)
    
    # Kiểm tra dependencies
    if not check_dependencies():
        print("\n[ERROR] Dependency check failed!")
        print("[TIP] Please install required dependencies and try again.")
        sys.exit(1)
    
    # Build frontend
    if not build_frontend():
        print("\n[ERROR] Frontend build failed!")
        print("[TIP] Please check the errors above and try again.")
        sys.exit(1)
    
    # Mở trình duyệt
    open_browser()
    
    # Start backend
    print("\n[SUCCESS] All checks passed! Starting VNASelf...")
    start_backend()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down VNASelf...")
        print("[OK] Goodbye!")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        print("[TIP] Please check the error and try again.")
        sys.exit(1)