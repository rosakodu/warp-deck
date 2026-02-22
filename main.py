import functools
import os
import time
import traceback as _traceback
from typing import Dict, List, Optional

from vpn_deck import BinaryManager, ConfigManager, ServiceManager

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
        configs = [c for c in configs if c.get("managed_by") == "vpn-deck"]
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


    # Migrations that should be performed before entering `_main()`.
    async def _migration(self):
        decky.logger.info("VPN Deck plugin migrating")
        # Migrations can be added here if needed in the future
        pass
