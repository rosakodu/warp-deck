import functools
import os
import time
import traceback as _traceback
import urllib.request
import json
import random
import re
import ssl
import asyncio
from typing import Dict, List, Optional

from vpn_deck import BinaryManager, ConfigManager, Diagnostics, ServiceManager

import decky


def _rpc(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            tb = _traceback.format_exc()
            decky.logger.error(f"{func.__name__} exception: {tb}")
            if hasattr(self, "_add_error"):
                self._add_error(func.__name__, type(e).__name__, str(e), {"traceback": tb})
            return {"success": False, "error": f"{type(e).__name__}: {e}"}
    return wrapper


class Plugin:
    def __init__(self):
        """Инициализация плагина"""
        self.errors: List[dict] = []
        self.max_errors = 50

        # Initialize BinaryManager
        self.binary_manager = BinaryManager()

        # Initialize ConfigManager
        self.config_manager = ConfigManager()

        # Initialize ServiceManager
        self.service_manager = ServiceManager(self.binary_manager)

        # Initialize Diagnostics
        self.diagnostics = Diagnostics()

    def _add_error(self, operation: str, error_type: str, message: str, details: dict = None):
        """Добавляет ошибку в историю"""
        error = {
            "timestamp": time.time(),
            "operation": operation,
            "error_type": error_type,
            "message": message,
            "details": details or {},
        }
        self.errors.append(error)
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        decky.logger.error(f"VPN Error [{error_type}] in {operation}: {message}")

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        decky.logger.info("VPN Deck plugin initialized")
        try:
            repair = await self.config_manager.repair_symlinks()
            if repair["repaired"]:
                decky.logger.info(
                    f"Auto-repaired {repair['repaired']}/{repair['total']} symlinks on startup"
                )
        except Exception as e:
            decky.logger.error(f"Symlink auto-repair failed: {e}")

    # Function called first during the unload process, utilize this to handle your plugin being stopped, but not
    # completely removed
    async def _unload(self):
        decky.logger.info("VPN Deck plugin unloading")
        pass

    # Function called after `_unload` during uninstall, utilize this to clean up processes and other remnants of your
    # plugin that may remain on the system
    async def _uninstall(self):
        decky.logger.info("VPN Deck plugin uninstalling")
        pass

    @_rpc
    async def vpn_status_all(self) -> list:
        """Возвращает статус всех активных VPN интерфейсов"""
        return self.service_manager.get_all_statuses()

    @_rpc
    async def vpn_stop_all(self, only_managed: bool = False) -> dict:
        """Останавливает все (или только managed) VPN интерфейсы"""
        return self.service_manager.stop_all_interfaces(only_managed)

    @_rpc
    async def list_configs_with_status(self) -> list:
        configs = await self.config_manager.list_all_configs()
        configs = [c for c in configs if c.get("managed_by") == "warp-deck"]
        active_statuses = self.service_manager.get_all_statuses()
        active_ifaces = {
            s["interface"] for s in active_statuses if s["status"] == "active"
        }
        for c in configs:
            c["active"] = c["interface"] in active_ifaces
        return configs

    @_rpc
    async def vpn_start_config(self, config_name: str) -> dict:
        if isinstance(config_name, dict):
            config_name = config_name.get("config_name", "")
        if not config_name:
            return {"success": False, "error": "config_name is required", "interface": ""}
        interface = self.config_manager.get_interface_name(config_name)
        result = self.service_manager.start_interface(interface)
        if not result["success"]:
            self._add_error("start", "ServiceError", result["error"] or "unknown", {"interface": interface})
        return {"success": result["success"], "error": result["error"], "interface": interface}

    @_rpc
    async def vpn_stop_config(self, config_name: str) -> dict:
        if isinstance(config_name, dict):
            config_name = config_name.get("config_name", "")
        if not config_name:
            return {"success": False, "error": "config_name is required", "interface": ""}
        interface = self.config_manager.get_interface_name(config_name)
        result = self.service_manager.stop_interface(interface)
        if not result["success"]:
            self._add_error("stop", "ServiceError", result["error"] or "unknown", {"interface": interface})
        return {"success": result["success"], "error": result["error"], "interface": interface}

    @_rpc
    async def get_errors(self) -> List[dict]:
        """Возвращает историю ошибок"""
        return list(self.errors)

    @_rpc
    async def clear_errors(self) -> bool:
        """Очищает историю ошибок"""
        self.errors = []
        decky.logger.info("Error history cleared")
        return True

    # BinaryManager API methods

    @_rpc
    async def get_binaries_info(self) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Возвращает информацию о всех бинарниках AmneziaWG.

        Returns:
            Словарь с информацией о бинарниках (путь и версия)
        """
        info = self.binary_manager.get_binaries_info()
        decky.logger.info(f"Binaries info: {info}")
        return info

    @_rpc
    async def check_binaries(self) -> Dict[str, bool]:
        """
        Проверяет доступность всех необходимых бинарников.

        Returns:
            Словарь с флагами доступности: {"amneziawg-go": True, "awg": False, ...}
        """
        binaries = self.binary_manager.detect_binaries()
        availability = {name: (path is not None) for name, path in binaries.items()}
        decky.logger.info(f"Binary availability: {availability}")
        return availability

    # ConfigManager API methods

    @_rpc
    async def list_all_configs(self) -> List[Dict]:
        """
        Возвращает список всех VPN конфигураций (managed + existing).

        Returns:
            Список конфигураций с информацией о каждой
        """
        try:
            configs = await self.config_manager.list_all_configs()
            decky.logger.info(f"Listed {len(configs)} configs")
            return configs
        except Exception as e:
            decky.logger.error(f"Error listing configs: {e}")
            return []

    @_rpc
    async def scan_existing_configs(self) -> Dict[str, List[Dict]]:
        """
        Сканирует все конфигурации (managed и user-created).

        Returns:
            Dictionary с ключами 'managed' и 'existing', содержащими списки конфигов
        """
        result = await self.config_manager.scan_existing_configs()
        decky.logger.info(
            f"Scanned configs: {len(result['managed'])} managed, {len(result['existing'])} existing"
        )
        return result

    @_rpc
    async def import_vpn_config(self, name: str, path: str = "") -> dict:
        decky.logger.info(f"import_vpn_config: name={name}, path={path}")
        if not os.path.isfile(path):
            return {"success": False, "error": "Файл не найден"}

        with open(path, "r") as f:
            content = f.read()

        if not content.strip():
            return {"success": False, "error": "Файл пустой"}

        result = self.config_manager.write_config(name, content)
        return {"success": result["success"], "error": result["error"] or ""}

    @_rpc
    async def get_downloads_dir(self) -> str:
        """Возвращает путь к папке загрузок текущего пользователя на Steam Deck"""
        try:
            from vpn_deck.config_manager import get_user_home
            user_home = get_user_home()
            downloads = os.path.join(user_home, "Downloads")
            if os.path.isdir(downloads):
                return downloads
            return user_home
        except Exception as e:
            decky.logger.error(f"Error resolving downloads directory: {e}")
            return "/home/deck/Downloads"

    @_rpc
    async def delete_vpn_config(self, name: str) -> Dict:
        """
        Удаляет VPN конфигурацию.
        Сначала останавливает интерфейс, если он поднят, затем удаляет файлы (без бэкапа).

        Args:
            name: Имя конфигурации для удаления (или dict с ключом name)

        Returns:
            Словарь с результатом удаления (success, config_name, error)
        """
        if isinstance(name, dict):
            name = name.get("name", "")
        if not name:
            return {"success": False, "config_name": None, "error": "name is required"}
        interface = self.config_manager.get_interface_name(name)
        stop_result = self.service_manager.stop_interface(interface)
        if not stop_result["success"] and stop_result.get("error") != "awg-quick binary not found":
            decky.logger.warning(f"Stop before delete failed (continuing): {stop_result.get('error')}")
        result = await self.config_manager.delete_config(name)
        if result["success"]:
            decky.logger.info(f"Successfully deleted config: {result['config_name']}")
        else:
            decky.logger.warning(f"Failed to delete config: {result.get('error')}")
        return result

    @_rpc
    async def repair_symlinks(self) -> dict:
        """Re-creates missing symlinks in /etc/amnezia/amneziawg/ for all managed configs.

        SteamOS updates reset /etc, so symlinks need to be rebuilt periodically.
        """
        result = await self.config_manager.repair_symlinks()
        decky.logger.info(f"Symlink repair: {result['repaired']}/{result['total']} rebuilt")
        return result

    @_rpc
    async def diagnose_connectivity(self, targets: Optional[List[Dict]] = None) -> List[Dict]:
        """Runs ping/HTTP probes against default or custom targets."""
        return self.diagnostics.check(targets)

    @_rpc
    async def get_vpn_config(self, name: str) -> Optional[str]:
        """
        Получает содержимое конфигурации.

        Args:
            name: Имя конфигурации

        Returns:
            Содержимое конфигурации или None если не найдена
        """
        try:
            content = await self.config_manager.get_config_content(name)
            if content:
                decky.logger.info(f"Retrieved config content for: {name}")
            else:
                decky.logger.warning(f"Config not found: {name}")
            return content
        except Exception as e:
            decky.logger.error(f"Error getting config {name}: {e}")
            return None


    @_rpc
    async def get_steam_language(self) -> str:
        """Считывает язык из Steam registry.vdf"""
        paths = []
        if os.path.isdir("/home"):
            try:
                for user in os.listdir("/home"):
                    if user != "lost+found":
                        paths.append(f"/home/{user}/.steam/registry.vdf")
                        paths.append(f"/home/{user}/.steam/steam/registry.vdf")
            except Exception:
                pass
        
        # Также добавим стандартные пути на всякий случай
        paths.append(os.path.expanduser("~/.steam/registry.vdf"))
        paths.append(os.path.expanduser("~/.steam/steam/registry.vdf"))
        
        for path in paths:
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    match = re.search(r'"language"\s+"([^"]+)"', content, re.IGNORECASE)
                    if match:
                        lang = match.group(1).lower().strip()
                        decky.logger.info(f"Steam language detected: {lang}")
                        return lang
                except Exception as e:
                    decky.logger.error(f"Error reading Steam language from {path}: {e}")
                    
        decky.logger.info("Steam language not found, defaulting to english")
        return "english"

    @_rpc
    async def generate_warp_config(self) -> dict:
        """Генерирует конфигурацию WARP через AmneziaWG и запускает её"""
        # Сначала остановим все запущенные интерфейсы плагина, чтобы восстановить
        # прямой доступ к интернету для обращения к зеркалам API
        try:
            self.service_manager.stop_all_interfaces(only_managed=True)
            # Даем сетевому стеку 1.5 секунды на обновление таблицы маршрутизации
            await asyncio.sleep(1.5)
        except Exception as e:
            decky.logger.warning(f"Error stopping interfaces before config generation: {e}")

        endpoints = [
            'https://www.warp-generator.workers.dev',
            'https://warp-gen.netlify.app/',
            'https://warp.sub-aggregator.workers.dev',
            'https://warp-vercel-chi.vercel.app/api/warp-data',
            'https://warp-vercel-murex.vercel.app/api/warp-data',
            'https://warp-generator-config.vercel.app/api/warp-data',
            'https://warp3.llimonix.pw',
            'https://warp.llimonix.workers.dev'
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Создаем SSL-контекст без проверки сертификатов для обхода проблем с CA-bundle на Steam Deck
        ssl_context = None
        try:
            ssl_context = ssl._create_unverified_context()
        except AttributeError:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
        config_data = None
        errors = []

        # Опрашиваем зеркала-генераторы (так как прямой доступ к API Cloudflare в РФ заблокирован)
        for i, url in enumerate(endpoints):
            req = urllib.request.Request(url, headers=headers)
            try:
                # 8s timeout
                with urllib.request.urlopen(req, timeout=8, context=ssl_context) as response:
                    if response.status == 200:
                        config_data = json.loads(response.read().decode('utf-8'))
                        decky.logger.info(f"Fetched WARP configuration from endpoint {i} ({url})")
                        break
                    else:
                        raise Exception(f"HTTP Status {response.status}")
            except Exception as e:
                err_msg = f"Endpoint {i} ({url}) failed: {type(e).__name__}: {e}"
                decky.logger.warning(err_msg)
                errors.append(err_msg)
                
        if not config_data:
            # Выводим сводную информацию о сбоях зеркал
            detailed_errors = "; ".join(errors)
            return {
                "success": False,
                "error": f"Failed to fetch config from all generators. Failures: {detailed_errors}"
            }
            
        # Генерация Endpoint (Используем официальные и стабильные эндпоинты Cloudflare WARP)
        endpoints = [
            "engage.cloudflareclient.com:2408",
            "engage.cloudflareclient.com:500",
            "engage.cloudflareclient.com:854",
            "engage.cloudflareclient.com:894",
            "162.159.192.1:2408",
            "162.159.192.2:2408",
            "162.159.192.3:2408",
            "162.159.192.4:2408",
            "162.159.193.1:2408",
            "162.159.193.2:2408",
            "162.159.193.3:2408",
            "162.159.193.4:2408",
            "162.159.195.1:2408",
            "162.159.195.2:2408",
            "162.159.195.3:2408",
            "162.159.195.4:2408",
            "[2606:4700:d0::a29f:c001]:2408",
            "[2606:4700:d0::a29f:c002]:2408",
            "[2606:4700:d0::a29f:c003]:2408",
            "[2606:4700:d0::a29f:c004]:2408"
        ]
        random_endpoint = random.choice(endpoints)

        client_ipv4 = config_data.get("client_ipv4", "")
        client_ipv6 = config_data.get("client_ipv6", "")
        priv_key = config_data.get("privKey", "")
        peer_pub = config_data.get("peer_pub", "")

        # Формируем Address
        addresses = []
        if client_ipv4:
            addresses.append(client_ipv4)
        if client_ipv6:
            addresses.append(client_ipv6)
        address_str = ", ".join(addresses)

        # Профили обфускации AmneziaWG (DPI bypass)
        # ВАЖНО: Серверы Cloudflare WARP работают на стандартном WireGuard.
        # Они НЕ понимают измененные заголовки H1-H4 (отбрасывают пакеты).
        # Поэтому H1-H4 ДОЛЖНЫ быть стандартными (1, 2, 3, 4).
        # Для обхода ТСПУ в РФ маскируем хендшейк под QUIC Client Hello (параметр I1).
        obf_lines = [
            "Jc = 4",
            "Jmin = 40",
            "Jmax = 70",
            "H1 = 1",
            "H2 = 2",
            "H3 = 3",
            "H4 = 4",
            "S1 = 0",
            "S2 = 0",
            "S3 = 0",
            "S4 = 0",
            "I1 = <b 0xce000000010897a297ecc34cd6dd000044d0ec2e2e1ea2991f467ace4222129b5a098823784694b4897b9986ae0b7280135fa85e196d9ad980b150122129ce2a9379531b0fd3e871ca5fdb883c369832f730e272d7b8b74f393f9f0fa43f11e510ecb2219a52984410c204cf875585340c62238e14ad04dff382f2c200e0ee22fe743b9c6b8b043121c5710ec289f471c91ee414fca8b8be8419ae8ce7ffc53837f6ade262891895f3f4cecd31bc93ac5599e18e4f01b472362b8056c3172b513051f8322d1062997ef4a383b01706598d08d48c221d30e74c7ce000cdad36b706b1bf9b0607c32ec4b3203a4ee21ab64df336212b9758280803fcab14933b0e7ee1e04a7becce3e2633f4852585c567894a5f9efe9706a151b615856647e8b7dba69ab357b3982f554549bef9256111b2d67afde0b496f16962d4957ff654232aa9e845b61463908309cfd9de0a6abf5f425f577d7e5f6440652aa8da5f73588e82e9470f3b21b27b28c649506ae1a7f5f15b876f56abc4615f49911549b9bb39dd804fde182bd2dcec0c33bad9b138ca07d4a4a1650a2c2686acea05727e2a78962a840ae428f55627516e73c83dd8893b02358e81b524b4d99fda6df52b3a8d7a5291326e7ac9d773c5b43b8444554ef5aea104a738ed650aa979674bbed38da58ac29d87c29d387d80b526065baeb073ce65f075ccb56e47533aef357dceaa8293a523c5f6f790be90e4731123d3c6152a70576e90b4ab5bc5ead01576c68ab633ff7d36dcde2a0b2c68897e1acfc4d6483aaaeb635dd63c96b2b6a7a2bfe042f6aed82e5363aa850aace12ee3b1a93f30d8ab9537df483152a5527faca21efc9981b304f11fc95336f5b9637b174c5a0659e2b22e159a9fed4b8e93047371175b1d6d9cc8ab745f3b2281537d1c75fb9451871864efa5d184c38c185fd203de206751b92620f7c369e031d2041e152040920ac2c5ab5340bfc9d0561176abf10a147287ea90758575ac6a9f5ac9f390d0d5b23ee12af583383d994e22c0cf42383834bcd3ada1b3825a0664d8f3fb678261d57601ddf94a8a68a7c273a18c08aa99c7ad8c6c42eab67718843597ec9930457359dfdfbce024afc2dcf9348579a57d8d3490b2fa99f278f1c37d87dad9b221acd575192ffae1784f8e60ec7cee4068b6b988f0433d96d6a1b1865f4e155e9fe020279f434f3bf1bd117b717b92f6cd1cc9bea7d45978bcc3f24bda631a36910110a6ec06da35f8966c9279d130347594f13e9e07514fa370754d1424c0a1545c5070ef9fb2acd14233e8a50bfc5978b5bdf8bc1714731f798d21e2004117c61f2989dd44f0cf027b27d4019e81ed4b5c31db347c4a3a4d85048d7093cf16753d7b0d15e078f5c7a5205dc2f87e330a1f716738dce1c6180e9d02869b5546f1c4d2748f8c90d9693cba4e0079297d22fd61402dea32ff0eb69ebd65a5d0b687d87e3a8b2c42b648aa723c7c7daf37abcc4bb85caea2ee8f55bec20e913b3324ab8f5c3304f820d42ad1b9f2ffc1a3af9927136b4419e1e579ab4c2ae3c776d293d397d575df181e6cae0a4ada5d67ecea171cca3288d57c7bbdaee3befe745fb7d634f70386d873b90c4d6c6596bb65af68f9e5121e67ebf0d89d3c909ceedfb32ce9575a7758ff080724e1ab5d5f43074ecb53a479af21ed03d7b6899c36631c0166f9d47e5e1d4528a5d3d3f744029c4b1c190cbfbad06f5f83f7ad0429fa9a2719c56ffe3783460e166de2d8>"
        ]
        obf_str = "\n".join(obf_lines)
        
        # Шаблон конфига AmneziaWG
        config_content = f"""[Interface]
PrivateKey = {priv_key}
Address = {address_str}
DNS = 1.1.1.1, 1.0.0.1, 2606:4700:4700::1111, 2606:4700:4700::1001
MTU = 1280
{obf_str}

[Peer]
PublicKey = {peer_pub}
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = {random_endpoint}
PersistentKeepalive = 25
"""
        
        # Запись конфигурации
        write_result = self.config_manager.write_config("warp-deck", config_content)
        if not write_result["success"]:
            return {"success": False, "error": f"Failed to write config: {write_result.get('error')}"}
            
        # Остановим все запущенные интерфейсы плагина (для избежания конфликтов)
        try:
            self.service_manager.stop_all_interfaces(only_managed=True)
        except Exception as e:
            decky.logger.warning(f"Error stopping interfaces before starting warp: {e}")
            
        # Запуск сгенерированного интерфейса
        interface_name = write_result["interface_name"]
        start_result = self.service_manager.start_interface(interface_name)
        if not start_result["success"]:
            self._add_error("start_warp", "ServiceError", start_result["error"] or "unknown", {"interface": interface_name})
            return {"success": False, "error": f"Failed to start interface: {start_result.get('error')}"}
            
        return {"success": True, "config_name": "warp-deck", "interface": interface_name}


    # Migrations that should be performed before entering `_main()`.
    async def _migration(self):
        decky.logger.info("VPN Deck plugin migrating")
        # Migrations can be added here if needed in the future
        pass
