"""Diagnostics - connectivity probes for VPN troubleshooting."""

import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import decky

from ._utils import clean_env


DEFAULT_TARGETS: List[Dict] = [
    {"name": "1.1.1.1", "kind": "ping", "host": "1.1.1.1"},
    {"name": "google.com", "kind": "http", "url": "https://www.google.com"},
    {"name": "rutracker.org", "kind": "http", "url": "https://rutracker.org"},
]


class Diagnostics:
    def check(self, targets: Optional[List[Dict]] = None) -> List[Dict]:
        probes = targets if targets else DEFAULT_TARGETS
        if not probes:
            return []
        with ThreadPoolExecutor(max_workers=len(probes)) as pool:
            return list(pool.map(self._probe, probes))

    def _probe(self, t: Dict) -> Dict:
        kind = t.get("kind")
        name = t.get("name") or t.get("host") or t.get("url") or "?"
        if kind == "ping":
            return self._ping(name, t["host"])
        if kind == "http":
            return self._http(name, t["url"])
        return {"name": name, "kind": kind or "unknown", "ok": False, "detail": f"unknown kind: {kind}", "target": "", "latency_ms": None}

    @staticmethod
    def _ping(name: str, host: str) -> Dict:
        try:
            r = subprocess.run(
                ["ping", "-c", "3", "-W", "2", "-n", host],
                capture_output=True, text=True, timeout=12, check=False,
                env=clean_env(),
            )
            ok = r.returncode == 0
            avg_ms = None
            if ok:
                m = re.search(r"min/avg/max/\S+\s*=\s*[\d.]+/([\d.]+)/", r.stdout)
                if m:
                    avg_ms = float(m.group(1))
            detail = f"avg {avg_ms:.1f} ms" if avg_ms is not None else (r.stderr.strip() or "no response")
            return {"name": name, "kind": "ping", "target": host, "ok": ok, "detail": detail, "latency_ms": avg_ms}
        except subprocess.TimeoutExpired:
            return {"name": name, "kind": "ping", "target": host, "ok": False, "detail": "timeout", "latency_ms": None}
        except FileNotFoundError:
            decky.logger.warning("ping not found for diagnostics")
            return {"name": name, "kind": "ping", "target": host, "ok": False, "detail": "ping not found", "latency_ms": None}

    @staticmethod
    def _http(name: str, url: str) -> Dict:
        try:
            r = subprocess.run(
                ["curl", "-sS", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                 "-o", "/dev/null", "-w", "%{http_code} %{time_total}",
                 "--max-time", "6", "-L", url],
                capture_output=True, text=True, timeout=10, check=False,
                env=clean_env(),
            )
            out = r.stdout.strip()
            parts = out.split()
            code = parts[0] if parts else "0"
            time_s = float(parts[1]) if len(parts) > 1 else None
            ok = code.startswith(("2", "3"))
            detail = f"HTTP {code}" + (f", {time_s:.2f}s" if time_s is not None else "")
            if not ok and r.stderr:
                detail += f" ({r.stderr.strip().splitlines()[-1]})"
            return {"name": name, "kind": "http", "target": url, "ok": ok, "detail": detail, "latency_ms": time_s * 1000 if time_s else None}
        except subprocess.TimeoutExpired:
            return {"name": name, "kind": "http", "target": url, "ok": False, "detail": "timeout", "latency_ms": None}
        except FileNotFoundError:
            decky.logger.warning("curl not found for diagnostics")
            return {"name": name, "kind": "http", "target": url, "ok": False, "detail": "curl not found", "latency_ms": None}
