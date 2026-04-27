"""Shared helpers used across vpn_deck modules."""

import os
from typing import Dict


def clean_env() -> Dict[str, str]:
    """Strips PyInstaller / Decky MEI paths from LD_LIBRARY_PATH.

    Decky bundles the plugin runtime via PyInstaller, which injects
    /tmp/_MEI* into LD_LIBRARY_PATH. Child processes like `awg-quick`,
    `ping`, `curl` must not inherit these or they pick up bundled libs
    that conflict with the system ones.
    """
    env = os.environ.copy()
    if "LD_LIBRARY_PATH" in env:
        paths = [p for p in env["LD_LIBRARY_PATH"].split(":") if "/tmp/" not in p and "_MEI" not in p]
        if paths:
            env["LD_LIBRARY_PATH"] = ":".join(paths)
        else:
            del env["LD_LIBRARY_PATH"]
    return env
