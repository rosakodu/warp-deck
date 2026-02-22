#!/usr/bin/env python3
"""
Test script for BinaryManager functionality.
This can be run independently to verify binary detection works correctly.
"""

import os
import sys

# Mock the decky module for testing
class MockLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")

    def debug(self, msg):
        pass

    def warning(self, msg):
        print(f"[WARNING] {msg}")

    def error(self, msg):
        print(f"[ERROR] {msg}")

class MockDecky:
    logger = MockLogger()

sys.modules['decky'] = MockDecky()

# Now we can import from main
from main import BinaryManager


def test_binary_manager():
    """Test BinaryManager functionality"""
    print("=" * 60)
    print("Testing BinaryManager")
    print("=" * 60)
    
    # Create BinaryManager instance
    bm = BinaryManager()
    
    print("\n1. Testing detect_binaries()...")
    binaries = bm.detect_binaries()
    print(f"   Detected binaries: {binaries}")
    
    print("\n2. Testing get_binary_path() for each binary...")
    for name in bm.binary_names:
        path = bm.get_binary_path(name)
        print(f"   {name}: {path}")
    
    print("\n3. Testing check_binary_version() for found binaries...")
    for name, path in binaries.items():
        if path:
            version = bm.check_binary_version(path)
            print(f"   {name} version: {version}")
        else:
            print(f"   {name}: Not found, skipping version check")
    
    print("\n4. Testing get_binaries_info()...")
    info = bm.get_binaries_info()
    for name, details in info.items():
        print(f"   {name}:")
        print(f"     - path: {details['path']}")
        print(f"     - version: {details['version']}")
    
    print("\n5. Testing invalidate_cache()...")
    bm.invalidate_cache()
    print("   Cache invalidated")
    
    # Re-detect after cache invalidation
    binaries_after = bm.detect_binaries()
    print(f"   Re-detected binaries: {binaries_after}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    available = sum(1 for path in binaries.values() if path is not None)
    total = len(binaries)
    print(f"Found {available}/{total} binaries")
    
    if available == 0:
        print("\nNOTE: No binaries found. This is expected if:")
        print("  - AmneziaWG is not installed on your system")
        print("  - Binaries are not yet in the bin/ directory")
        print("\nTo install binaries:")
        print("  1. Run GitHub Actions workflow to build them")
        print("  2. Download from releases")
        print("  3. Or install AmneziaWG system-wide")
    
    print("\nTest completed!")
    return available > 0


if __name__ == "__main__":
    try:
        success = test_binary_manager()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
