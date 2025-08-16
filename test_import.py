#!/usr/bin/env python3
"""
Test script to check imports
"""

import os
import sys

print("Current directory:", os.getcwd())
print("Python path:", sys.path[:3])  # Show first 3 entries

print("\nTrying to import tiktok_generator...")

try:
    # Method 1: Direct import
    from tiktok_generator import TikTokVideoGenerator
    print("✅ Direct import successful!")
except ImportError as e:
    print(f"❌ Direct import failed: {e}")
    
    try:
        # Method 2: Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        print(f"Added {current_dir} to Python path")
        
        from tiktok_generator import TikTokVideoGenerator
        print("✅ Import successful after adding to path!")
    except ImportError as e2:
        print(f"❌ Import still failed: {e2}")
        
        try:
            # Method 3: Import using importlib
            import importlib.util
            spec = importlib.util.spec_from_file_location("tiktok_generator", "tiktok_generator.py")
            if spec and spec.loader:
                tiktok_generator = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(tiktok_generator)
                TikTokVideoGenerator = tiktok_generator.TikTokVideoGenerator
                print("✅ Import successful using importlib!")
            else:
                print("❌ Could not create spec from file")
        except Exception as e3:
            print(f"❌ Importlib method failed: {e3}")

print("\nChecking if TikTokVideoGenerator is available...")
try:
    if 'TikTokVideoGenerator' in locals():
        print("✅ TikTokVideoGenerator class is available!")
        print("Class name:", TikTokVideoGenerator.__name__)
    else:
        print("❌ TikTokVideoGenerator class not found")
except Exception as e:
    print(f"❌ Error checking class: {e}")

print("\nTest complete!")
