#!/usr/bin/env python3
"""
Smoke test for Plugin class — verifies all public RPC methods without real binaries.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Mock: decky
# ---------------------------------------------------------------------------

class _MockLogger:
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass
    def debug(self, msg): pass


class _MockDecky:
    logger = _MockLogger()
    DECKY_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
    DECKY_PLUGIN_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    plugin_home = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".test_home")


sys.modules["decky"] = _MockDecky()

# ---------------------------------------------------------------------------
# Mock: vpn_deck managers
# ---------------------------------------------------------------------------

class _MockBinaryManager:
    binary_names = ["amneziawg-go", "awg", "awg-quick"]

    def get_binaries_info(self):
        return {name: {"path": None, "version": None} for name in self.binary_names}

    def detect_binaries(self):
        return {name: None for name in self.binary_names}

    def get_binary_path(self, name):
        return None

    def invalidate_cache(self):
        pass


class _MockConfigManager:
    def __init__(self):
        pass

    async def list_all_configs(self):
        return [{"name": "test", "interface": "awg-test", "managed_by": "vpn-deck"}]

    async def scan_existing_configs(self):
        return {"managed": [], "existing": []}

    def get_interface_name(self, config_name):
        if not config_name:
            raise ValueError("config_name is empty")
        return f"awg-{config_name}"

    async def delete_config(self, name):
        return {"success": True, "config_name": name, "error": ""}

    async def get_config_content(self, name):
        return None

    async def validate_config(self, content):
        return {"valid": True, "errors": [], "warnings": [], "info": {}}


class _MockServiceManager:
    def __init__(self, bm):
        pass

    def start_interface(self, interface):
        return {"success": True, "error": None}

    def stop_interface(self, interface):
        return {"success": True, "error": None}

    def get_status(self, interface):
        return {"status": "inactive", "error": None}

    def get_all_statuses(self):
        return []

    def stop_all_interfaces(self, only_managed=False):
        return {"success": True, "stopped": [], "error": None}


class _MockVpnDeck:
    BinaryManager = _MockBinaryManager
    ConfigManager = _MockConfigManager
    ServiceManager = _MockServiceManager


sys.modules["vpn_deck"] = _MockVpnDeck()

# ---------------------------------------------------------------------------
# Import Plugin (after mocks are in place)
# ---------------------------------------------------------------------------

from main import Plugin  # noqa: E402

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

PASS = 0
FAIL = 0


def ok(name):
    global PASS
    PASS += 1
    print(f"  PASS  {name}")


def fail(name, reason):
    global FAIL
    FAIL += 1
    print(f"  FAIL  {name}: {reason}")


def assert_dict(result, name):
    if isinstance(result, dict):
        ok(name)
    else:
        fail(name, f"expected dict, got {type(result).__name__}: {result!r}")


def assert_list(result, name):
    if isinstance(result, list):
        ok(name)
    else:
        fail(name, f"expected list, got {type(result).__name__}: {result!r}")


def assert_bool(result, name):
    if isinstance(result, bool):
        ok(name)
    else:
        fail(name, f"expected bool, got {type(result).__name__}: {result!r}")


def assert_success_false(result, name):
    if isinstance(result, dict) and result.get("success") is False and result.get("error"):
        ok(name)
    else:
        fail(name, f"expected {{success: False, error: ...}}, got {result!r}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def run_tests():
    plugin = Plugin()

    print("\n[vpn methods]")
    assert_list(await plugin.vpn_status_all(), "vpn_status_all()")
    assert_dict(await plugin.vpn_stop_all(), "vpn_stop_all()")

    print("\n[config list]")
    assert_list(await plugin.list_configs_with_status(), "list_configs_with_status()")

    print("\n[vpn_start_config / vpn_stop_config — normal]")
    assert_dict(await plugin.vpn_start_config("myconf"), "vpn_start_config('myconf')")
    assert_dict(await plugin.vpn_stop_config("myconf"), "vpn_stop_config('myconf')")

    print("\n[REGRESSION: dict coercion]")
    r = await plugin.vpn_start_config({"config_name": "myconf"})
    assert_dict(r, "vpn_start_config({config_name: 'myconf'}) returns dict")
    if isinstance(r, dict) and r.get("success") is True:
        ok("vpn_start_config dict-coercion → success")
    else:
        fail("vpn_start_config dict-coercion → success", f"got {r!r}")

    r = await plugin.vpn_stop_config({"config_name": "myconf"})
    assert_dict(r, "vpn_stop_config({config_name: 'myconf'}) returns dict")
    if isinstance(r, dict) and r.get("success") is True:
        ok("vpn_stop_config dict-coercion → success")
    else:
        fail("vpn_stop_config dict-coercion → success", f"got {r!r}")

    print("\n[REGRESSION: empty config_name]")
    assert_success_false(await plugin.vpn_start_config(""), "vpn_start_config('')")
    assert_success_false(await plugin.vpn_stop_config(""), "vpn_stop_config('')")

    print("\n[REGRESSION: dict with empty config_name]")
    assert_success_false(await plugin.vpn_start_config({"config_name": ""}), "vpn_start_config({config_name: ''})")
    assert_success_false(await plugin.vpn_stop_config({"config_name": ""}), "vpn_stop_config({config_name: ''})")

    print("\n[errors API]")
    assert_list(await plugin.get_errors(), "get_errors()")
    assert_bool(await plugin.clear_errors(), "clear_errors()")

    print("\n[binaries]")
    assert_dict(await plugin.get_binaries_info(), "get_binaries_info()")
    assert_dict(await plugin.check_binaries(), "check_binaries()")

    print("\n[config manager API]")
    assert_list(await plugin.list_all_configs(), "list_all_configs()")
    assert_dict(await plugin.scan_existing_configs(), "scan_existing_configs()")
    assert_dict(await plugin.import_vpn_config("test", path="/nonexistent/file.conf"), "import_vpn_config (missing file)")
    assert_dict(await plugin.delete_vpn_config("test"), "delete_vpn_config('test')")
    # get_vpn_config returns None or str — just no exception
    try:
        await plugin.get_vpn_config("test")
        ok("get_vpn_config('test') no exception")
    except Exception as e:
        fail("get_vpn_config('test')", str(e))

    print("\n[_rpc decorator: exception → dict]")
    # Force an exception by passing a bad arg that gets past coercion
    orig = plugin.config_manager.get_interface_name
    def boom(name): raise RuntimeError("forced error")
    plugin.config_manager.get_interface_name = boom
    r = await plugin.vpn_start_config("anyname")
    plugin.config_manager.get_interface_name = orig
    assert_success_false(r, "_rpc catches exception → {success: False, error: ...}")


async def main():
    print("=" * 60)
    print("Plugin Smoke Test")
    print("=" * 60)

    try:
        await run_tests()
    except Exception as e:
        import traceback
        print(f"\nUNHANDLED EXCEPTION: {e}")
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    if FAIL == 0:
        print(f"ALL {PASS} TESTS PASSED")
    else:
        print(f"{PASS} passed, {FAIL} FAILED")
    print("=" * 60)

    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
