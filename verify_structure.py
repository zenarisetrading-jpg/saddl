#!/usr/bin/env python3
"""
Verification script to ensure all files are present and correct.
Run this after extraction to verify the package is complete.
"""

import os
import sys

def check_file(path, required=True):
    """Check if a file exists."""
    exists = os.path.isfile(path)
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {path}")
    return exists

def check_dir(path):
    """Check if a directory exists."""
    exists = os.path.isdir(path)
    status = "✅" if exists else "❌"
    print(f"{status} {path}/")
    return exists

def main():
    print("🔍 Verifying PPC Suite Structure\n")
    print("=" * 60)
    
    errors = 0
    
    # Check main file
    print("\n📄 Main Application:")
    if not check_file("ppcsuite.py"):
        errors += 1
    
    # Check directories
    print("\n📁 Directory Structure:")
    for directory in ["core", "features", "api", "ui", "utils"]:
        if not check_dir(directory):
            errors += 1
    
    # Check core files
    print("\n🔧 Core Files:")
    if not check_file("core/__init__.py"):
        errors += 1
    if not check_file("core/data_loader.py"):
        errors += 1
    if not check_file("core/performance_calc.py"):
        errors += 1
    
    # Check features
    print("\n⚡ Features:")
    if not check_file("features/__init__.py"):
        errors += 1
    if not check_file("features/_base.py"):
        errors += 1
    if not check_file("features/asin_mapper.py"):
        errors += 1
    if not check_file("features/ai_insights.py"):
        errors += 1
    if not check_file("features/optimizer.py"):
        errors += 1
    if not check_file("features/creator.py"):
        errors += 1
    
    # Check API clients
    print("\n🌐 API Clients:")
    if not check_file("api/__init__.py"):
        errors += 1
    if not check_file("api/rainforest_client.py"):
        errors += 1
    if not check_file("api/anthropic_client.py"):
        errors += 1
    
    # Check UI
    print("\n🎨 UI Components:")
    if not check_file("ui/__init__.py"):
        errors += 1
    if not check_file("ui/layout.py"):
        errors += 1
    if not check_file("ui/readme.py"):
        errors += 1
    
    # Check utils
    print("\n🛠️ Utilities:")
    if not check_file("utils/__init__.py"):
        errors += 1
    if not check_file("utils/validators.py"):
        errors += 1
    if not check_file("utils/formatters.py"):
        errors += 1
    
    # Check documentation
    print("\n📖 Documentation:")
    check_file("README.md", required=False)
    check_file("requirements.txt", required=False)
    
    # Summary
    print("\n" + "=" * 60)
    if errors == 0:
        print("✅ All files present! Structure is correct.")
        print("\n🚀 Ready to run:")
        print("   streamlit run ppcsuite.py")
        return 0
    else:
        print(f"❌ Missing {errors} required files!")
        print("\n⚠️ Please re-extract the package:")
        print("   tar -xzf ppcsuite_refactored_v2.tar.gz")
        return 1

if __name__ == "__main__":
    sys.exit(main())
