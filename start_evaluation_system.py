#!/usr/bin/env python3
"""
Startup script for the Movie Profile Evaluation System

This script starts the evaluation API server and provides instructions for accessing
the web interface.
"""

import os
import sys
import subprocess
import time
import webbrowser
from threading import Timer


def check_requirements():
    """Check if required files exist"""
    required_files = [
        'movie_profiles_merged.json',
        '.env',
        'llm_movie_evaluator.py',
        'llm_validation_system.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all required files are present before starting the evaluation system.")
        return False
    
    return True


def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = ['flask', 'openai', 'anthropic', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required Python packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True


def open_browser():
    """Open the evaluation dashboard in the default browser"""
    webbrowser.open('http://localhost:5001')


def main():
    """Main startup function"""
    print("🎬 Movie Profile Evaluation System")
    print("=" * 50)
    
    # Check requirements
    print("Checking requirements...")
    if not check_requirements():
        sys.exit(1)
    
    print("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    print("✅ All requirements satisfied!")
    print()
    
    # Start the API server
    print("🚀 Starting evaluation API server...")
    print("   - Server will run on: http://localhost:5001")
    print("   - Dashboard will open automatically in your browser")
    print("   - Press Ctrl+C to stop the server")
    print()
    
    # Schedule browser opening after server starts
    Timer(3.0, open_browser).start()
    
    try:
        # Import and run the Flask app
        from evaluation_api import app
        app.run(debug=False, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n👋 Shutting down evaluation system...")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
