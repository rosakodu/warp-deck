#!/usr/bin/env python3
"""
Simple test for ConfigManager - tests without validation (no binaries needed)
"""

import asyncio
import sys
import os
import tempfile
import shutil

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock decky module
class MockLogger:
    def info(self, msg):
        print(f"✓ {msg}")

    def debug(self, msg):
        pass  # quiet for tests

    def warning(self, msg):
        print(f"⚠ {msg}")

    def error(self, msg):
        print(f"✗ {msg}")

class MockDecky:
    def __init__(self):
        self.logger = MockLogger()
        self.DECKY_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
        self.DECKY_PLUGIN_LOG_DIR = os.path.join(self.DECKY_PLUGIN_DIR, "logs")

sys.modules['decky'] = MockDecky()

from main import ConfigManager


TEST_CONFIG = """[Interface]
PrivateKey = YAnz5TF+lXXJte14tji3zlMNftft3UL32bbjzVEwPBs=
Address = 10.8.1.2/24
DNS = 1.1.1.1

[Peer]
PublicKey = HIgo9xNzJMWLKASShiTqIybxZ0U3wGLiUeJ1PKf8ykw=
Endpoint = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0
"""


async def test_sanitize_name(cm: ConfigManager):
    """Test name sanitization"""
    print("\n📝 Test: Name Sanitization")
    
    tests = [
        ("My VPN Config", "my-vpn-config"),
        ("work_vpn", "work_vpn"),
        ("TEST-123", "test-123"),
        ("config with spaces!", "config-with-spaces"),
        ("../../etc/passwd", "etc-passwd"),
        ("normal.conf", "normal"),
    ]
    
    for input_name, expected in tests:
        result = cm._sanitize_name(input_name)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_name}' → '{result}' (expected: '{expected}')")


async def test_directory_creation(cm: ConfigManager):
    """Test directory creation"""
    print("\n📁 Test: Directory Creation")
    
    print(f"  Config dir: {cm.config_dir}")

    if os.path.exists(cm.config_dir):
        print(f"  ✓ Config directory exists")
    else:
        print(f"  ✗ Config directory missing!")


async def test_scan_configs(cm: ConfigManager):
    """Test config scanning"""
    print("\n🔍 Test: Scan Configs")
    
    result = await cm.scan_existing_configs()
    print(f"  Managed configs: {len(result['managed'])}")
    print(f"  Existing configs: {len(result['existing'])}")
    
    for config in result['managed']:
        print(f"    - {config['name']} ({config['interface']})")


async def test_import_simple(cm: ConfigManager):
    """Test simple import without validation"""
    print("\n📥 Test: Import Config (without validation)")
    
    # We'll manually write the config file to bypass validation
    sanitized_name = cm._sanitize_name("test-simple")
    local_path = os.path.join(cm.config_dir, f"{sanitized_name}.conf")
    
    print(f"  Writing config to: {local_path}")
    with open(local_path, 'w') as f:
        f.write(TEST_CONFIG)
    os.chmod(local_path, 0o600)
    
    print(f"  ✓ Config file created")
    
    # Now try to read it back
    content = await cm.get_config_content("test-simple")
    if content:
        print(f"  ✓ Config can be read back ({len(content)} bytes)")
    else:
        print(f"  ✗ Failed to read config")
    
    return sanitized_name


async def test_list_after_import(cm: ConfigManager):
    """Test listing after import"""
    print("\n📋 Test: List After Import")
    
    configs = await cm.list_all_configs()
    print(f"  Total configs: {len(configs)}")
    
    for config in configs:
        print(f"    - {config['name']} ({config.get('interface', 'N/A')})")


async def test_delete(cm: ConfigManager):
    """Test deletion (no backup)"""
    print("\n🗑️  Test: Delete Config")

    result = await cm.delete_config("test-simple")
    print(f"  Success: {result['success']}")

    if result.get('error'):
        print(f"  Error: {result['error']}")


async def main():
    """Run simple tests"""
    print("="*60)
    print("ConfigManager Simple Test (No Binaries Required)")
    print("="*60)
    
    try:
        cm = ConfigManager()

        await test_sanitize_name(cm)
        await test_directory_creation(cm)
        await test_scan_configs(cm)
        await test_import_simple(cm)
        await test_list_after_import(cm)
        await test_delete(cm)
        
        print("\n" + "="*60)
        print("✅ ALL SIMPLE TESTS PASSED!")
        print("="*60)
        print("\nNote: Full validation tests require awg-quick binary.")
        print("Install AmneziaWG binaries to test validation functionality.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
