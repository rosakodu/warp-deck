#!/usr/bin/env python3
"""
Test script for ConfigManager functionality
Tests: import, validation, list, delete operations
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock decky module for testing
class MockLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")

    def debug(self, msg):
        pass

    def warning(self, msg):
        print(f"[WARN] {msg}")

    def error(self, msg):
        print(f"[ERROR] {msg}")

class MockDecky:
    def __init__(self):
        self.logger = MockLogger()
        self.DECKY_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
        self.DECKY_PLUGIN_LOG_DIR = os.path.join(self.DECKY_PLUGIN_DIR, "logs")

sys.modules['decky'] = MockDecky()

# Now import our modules
from main import BinaryManager, ConfigManager


# Test configuration samples
VALID_CONFIG = """[Interface]
PrivateKey = YAnz5TF+lXXJte14tji3zlMNftft3UL32bbjzVEwPBs=
Address = 10.8.1.2/24
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = HIgo9xNzJMWLKASShiTqIybxZ0U3wGLiUeJ1PKf8ykw=
Endpoint = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""

VALID_AMNEZIA_CONFIG = """[Interface]
PrivateKey = YAnz5TF+lXXJte14tji3zlMNftft3UL32bbjzVEwPBs=
Address = 10.8.1.2/24
DNS = 1.1.1.1, 1.0.0.1
Jc = 5
Jmin = 40
Jmax = 70
S1 = 75
S2 = 85
H1 = 1234567890
H2 = 2345678901
H3 = 3456789012
H4 = 4567890123

[Peer]
PublicKey = HIgo9xNzJMWLKASShiTqIybxZ0U3wGLiUeJ1PKf8ykw=
PresharedKey = YAnz5TF+lXXJte14tji3zlMNftft3UL32bbjzVEwPBs=
Endpoint = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""

INVALID_CONFIG = """[Interface]
# Missing PrivateKey
Address = 10.8.1.2/24

[Peer]
# Missing PublicKey and Endpoint
AllowedIPs = 0.0.0.0/0
"""


async def test_binary_manager():
    """Test BinaryManager functionality"""
    print("\n" + "="*60)
    print("TEST: BinaryManager")
    print("="*60)
    
    bm = BinaryManager()
    
    print("\n1. Detecting binaries...")
    binaries = bm.detect_binaries()
    for name, path in binaries.items():
        print(f"  {name}: {path or 'NOT FOUND'}")
    
    print("\n2. Getting binaries info...")
    info = bm.get_binaries_info()
    for name, data in info.items():
        print(f"  {name}: path={data['path']}, version={data['version']}")
    
    return bm


async def test_config_validation(cm: ConfigManager):
    """Test config validation"""
    print("\n" + "="*60)
    print("TEST: Config Validation")
    print("="*60)
    
    print("\n1. Validating VALID config...")
    result = await cm.validate_config(VALID_CONFIG)
    print(f"  Valid: {result['valid']}")
    print(f"  Errors: {result['errors']}")
    print(f"  Warnings: {result['warnings']}")
    print(f"  Info: {result['info']}")
    
    print("\n2. Validating VALID Amnezia config...")
    result = await cm.validate_config(VALID_AMNEZIA_CONFIG)
    print(f"  Valid: {result['valid']}")
    print(f"  Has AmneziaWG params: {result['info'].get('has_amnezia_params')}")
    print(f"  Info: {result['info']}")
    
    print("\n3. Validating INVALID config...")
    result = await cm.validate_config(INVALID_CONFIG)
    print(f"  Valid: {result['valid']}")
    print(f"  Errors: {result['errors']}")


async def test_config_import(cm: ConfigManager):
    """Test config import"""
    print("\n" + "="*60)
    print("TEST: Config Import")
    print("="*60)
    
    print("\n1. Importing 'test-config'...")
    result = await cm.import_config("test-config", VALID_CONFIG)
    print(f"  Success: {result['success']}")
    print(f"  Config name: {result['config_name']}")
    print(f"  Interface name: {result['interface_name']}")
    print(f"  Local path: {result['local_path']}")
    print(f"  System path: {result['system_path']}")
    print(f"  Symlink created: {result['symlink_created']}")
    if result.get('error'):
        print(f"  Error: {result['error']}")
    
    print("\n2. Importing 'work-vpn' (Amnezia)...")
    result = await cm.import_config("work-vpn", VALID_AMNEZIA_CONFIG)
    print(f"  Success: {result['success']}")
    print(f"  Config name: {result['config_name']}")
    
    print("\n3. Re-importing 'test-config' (overwrite)...")
    result = await cm.import_config("test-config", VALID_CONFIG)
    print(f"  Success: {result['success']}")


async def test_config_list(cm: ConfigManager):
    """Test config listing"""
    print("\n" + "="*60)
    print("TEST: Config List")
    print("="*60)
    
    print("\n1. Scanning existing configs...")
    result = await cm.scan_existing_configs()
    print(f"\n  Managed configs ({len(result['managed'])}):")
    for config in result['managed']:
        print(f"    - {config['name']} ({config['interface']})")
        print(f"      Path: {config['path']}")
        print(f"      Symlink: {config['is_symlink']}")
    
    print(f"\n  Existing configs ({len(result['existing'])}):")
    for config in result['existing']:
        print(f"    - {config['name']} ({config['interface']})")
        print(f"      Path: {config['path']}")
    
    print("\n2. Listing all configs...")
    all_configs = await cm.list_all_configs()
    print(f"  Total configs: {len(all_configs)}")


async def test_config_content(cm: ConfigManager):
    """Test reading config content"""
    print("\n" + "="*60)
    print("TEST: Config Content")
    print("="*60)
    
    print("\n1. Reading 'test-config'...")
    content = await cm.get_config_content("test-config")
    if content:
        print(f"  Content length: {len(content)} bytes")
        print(f"  First line: {content.split(chr(10))[0]}")
    else:
        print("  Config not found!")
    
    print("\n2. Reading non-existent config...")
    content = await cm.get_config_content("non-existent")
    print(f"  Result: {content}")


async def test_config_delete(cm: ConfigManager):
    """Test config deletion"""
    print("\n" + "="*60)
    print("TEST: Config Deletion")
    print("="*60)
    
    print("\n1. Deleting 'work-vpn'...")
    result = await cm.delete_config("work-vpn")
    print(f"  Success: {result['success']}")
    print(f"  Symlink removed: {result['symlink_removed']}")
    if result.get('error'):
        print(f"  Error: {result['error']}")
    
    print("\n2. Deleting 'test-config'...")
    result = await cm.delete_config("test-config")
    print(f"  Success: {result['success']}")
    
    print("\n3. Trying to delete non-existent config...")
    result = await cm.delete_config("non-existent")
    print(f"  Success: {result['success']}")
    print(f"  Error: {result.get('error')}")


async def cleanup(cm: ConfigManager):
    """Clean up test files"""
    print("\n" + "="*60)
    print("CLEANUP")
    print("="*60)
    
    configs = await cm.scan_existing_configs()
    for config in configs['managed']:
        name = config['name']
        print(f"  Removing test config: {name}")
        await cm.delete_config(name)
    
    print("  Done!")


async def main():
    """Run all tests"""
    print("="*60)
    print("ConfigManager Test Suite")
    print("="*60)
    
    try:
        # Test BinaryManager
        bm = await test_binary_manager()
        
        # Check if binaries are available
        awg_quick = bm.get_binary_path("awg-quick")
        if not awg_quick:
            print("\n" + "!"*60)
            print("WARNING: awg-quick not found!")
            print("Validation tests will fail. Install AmneziaWG binaries first.")
            print("!"*60)
            return
        
        # Create ConfigManager
        cm = ConfigManager(bm)
        
        # Run tests
        await test_config_validation(cm)
        await test_config_import(cm)
        await test_config_list(cm)
        await test_config_content(cm)
        await test_config_delete(cm)
        
        # Cleanup
        await cleanup(cm)
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n" + "!"*60)
        print(f"TEST FAILED: {e}")
        print("!"*60)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
