#!/usr/bin/env python3
"""
Minimal test to isolate import issues.
"""

import sys
import os

# Add the secrets module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'secrets'))

print("Starting minimal test...")

try:
    print("Testing basic imports...")
    import subprocess
    import platform
    from typing import Tuple, Optional, Dict, List
    from dataclasses import dataclass
    print("✅ Basic imports successful")
    
    print("Testing dataclass...")
    @dataclass
    class TestInfo:
        name: str
        version: str = ""
    
    test = TestInfo("test")
    print(f"✅ Dataclass works: {test.name}")
    
    print("Testing platform detection...")
    os_name = platform.system()
    print(f"✅ OS detected: {os_name}")
    
    print("Testing file operations...")
    if os.path.exists('/etc/os-release'):
        with open('/etc/os-release', 'r') as f:
            first_line = f.readline().strip()
        print(f"✅ File read successful: {first_line}")
    
    print("All basic tests passed!")
    
except Exception as e:
    print(f"❌ Error in basic tests: {e}")
    import traceback
    traceback.print_exc()

print("Minimal test completed.")
