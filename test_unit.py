#!/usr/bin/env python3
"""
Unit test for ConfigManager - uses temp directory
"""

import asyncio
import sys
import os
import tempfile
import shutil

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock decky module for testing
class MockLogger:
    def info(self, msg):
        pass  # Silence for cleaner output

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

class MockDecky:
    def __init__(self):
        self.logger = MockLogger()
        self.DECKY_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
        self.DECKY_PLUGIN_LOG_DIR = os.path.join(self.DECKY_PLUGIN_DIR, "logs")

sys.modules['decky'] = MockDecky()

# Import from vpn_deck module
from vpn_deck import ConfigManager


TEST_CONFIG = """[Interface]
PrivateKey = YAnz5TF+lXXJte14tji3zlMNftft3UL32bbjzVEwPBs=
Address = 10.8.1.2/24
DNS = 1.1.1.1

[Peer]
PublicKey = HIgo9xNzJMWLKASShiTqIybxZ0U3wGLiUeJ1PKf8ykw=
Endpoint = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0
"""


def create_test_config_manager():
    """Create ConfigManager with temp directories"""
    cm = ConfigManager()
    
    # Override directories to use temp
    temp_base = tempfile.mkdtemp(prefix="vpn-deck-test-")
    cm.config_dir = os.path.join(temp_base, "configs")
    cm.system_config_dir = os.path.join(temp_base, "system")

    # Create directories
    os.makedirs(cm.config_dir, mode=0o700, exist_ok=True)
    os.makedirs(cm.system_config_dir, mode=0o755, exist_ok=True)
    
    return cm, temp_base


async def test_sanitize():
    """Test name sanitization"""
    print("Test 1: Name Sanitization")
    cm = ConfigManager()
    
    tests = [
        ("My VPN", "my-vpn"),
        ("work_vpn", "work_vpn"),
        ("test-123", "test-123"),
    ]
    
    for input_val, expected in tests:
        result = cm._sanitize_name(input_val)
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("  ✓ Passed")


async def test_file_operations():
    """Test file read/write operations"""
    print("Test 2: File Operations")
    cm, temp_base = create_test_config_manager()
    
    try:
        # Write config manually
        config_path = os.path.join(cm.config_dir, "test.conf")
        with open(config_path, 'w') as f:
            f.write(TEST_CONFIG)
        os.chmod(config_path, 0o600)
        
        # Read it back
        content = await cm.get_config_content("test")
        assert content is not None
        assert len(content) > 0
        assert "[Interface]" in content
        
        print("  ✓ Passed")
    finally:
        shutil.rmtree(temp_base, ignore_errors=True)


async def test_scan_empty():
    """Test scanning empty directories"""
    print("Test 3: Scan Empty Configs")
    cm, temp_base = create_test_config_manager()
    
    try:
        result = await cm.scan_existing_configs()
        assert len(result['managed']) == 0
        assert len(result['existing']) == 0
        
        print("  ✓ Passed")
    finally:
        shutil.rmtree(temp_base, ignore_errors=True)


async def test_scan_with_configs():
    """Test scanning with configs present"""
    print("Test 4: Scan With Configs")
    cm, temp_base = create_test_config_manager()
    
    try:
        # Create test configs
        config1 = os.path.join(cm.config_dir, "home.conf")
        config2 = os.path.join(cm.config_dir, "work.conf")
        
        for path in [config1, config2]:
            with open(path, 'w') as f:
                f.write(TEST_CONFIG)
        
        result = await cm.scan_existing_configs()
        assert len(result['managed']) == 2
        
        # Check names
        names = [c['name'] for c in result['managed']]
        assert 'home' in names
        assert 'work' in names
        
        print("  ✓ Passed")
    finally:
        shutil.rmtree(temp_base, ignore_errors=True)


async def test_delete():
    """Test config deletion"""
    print("Test 5: Config Deletion")
    cm, temp_base = create_test_config_manager()

    try:
        # Create a config
        config_path = os.path.join(cm.config_dir, "test.conf")
        with open(config_path, 'w') as f:
            f.write(TEST_CONFIG)

        assert os.path.exists(config_path)

        # Delete it (no backup)
        result = await cm.delete_config("test")
        assert result['success'] is True

        # Check it's gone
        assert not os.path.exists(config_path)

        print("  ✓ Passed")
    finally:
        shutil.rmtree(temp_base, ignore_errors=True)


async def test_list_all():
    """Test list_all_configs"""
    print("Test 6: List All Configs")
    cm, temp_base = create_test_config_manager()
    
    try:
        # Create configs
        for name in ['home', 'work', 'test']:
            config_path = os.path.join(cm.config_dir, f"{name}.conf")
            with open(config_path, 'w') as f:
                f.write(TEST_CONFIG)
        
        configs = await cm.list_all_configs()
        assert len(configs) == 3
        
        names = [c['name'] for c in configs]
        assert 'home' in names
        assert 'work' in names
        assert 'test' in names
        
        print("  ✓ Passed")
    finally:
        shutil.rmtree(temp_base, ignore_errors=True)


async def main():
    print("="*60)
    print("ConfigManager Unit Tests")
    print("="*60)
    print()
    
    try:
        await test_sanitize()
        await test_file_operations()
        await test_scan_empty()
        await test_scan_with_configs()
        await test_delete()
        await test_list_all()
        
        print()
        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
    except AssertionError as e:
        print()
        print(f"❌ ASSERTION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
