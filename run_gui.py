#!/usr/bin/env python3
"""
Simple launcher for TikTok Video Generator GUI
"""

import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Import and run the GUI
    from tiktok_gui import main
    main()
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in directory: {os.listdir('.')}")
    print("\nTrying to run GUI directly...")
    
    # Try running the GUI file directly
    try:
        exec(open('tiktok_gui.py').read())
    except Exception as e2:
        print(f"Failed to run GUI: {e2}")
        print("\nPlease make sure all files are in the same directory:")
        print("- tiktok_gui.py")
        print("- tiktok_generator.py")
        print("- config.json")
        print("- questions.json")
        print("- hooks.json")
except Exception as e:
    print(f"Error running GUI: {e}")
    print("Please check the error message above.")
