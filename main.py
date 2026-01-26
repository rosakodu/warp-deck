import os
import subprocess
import time
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List
from abc import ABC, abstractmethod

# The decky plugin module is located at decky-loader/plugin
# For easy intellisense checkout the decky-loader code repo
# and add the `decky-loader/plugin/imports` path to `python.analysis.extraPaths` in `.vscode/settings.json`
import decky


@dataclass
class VPNError:
    """Структура для хранения информации об ошибке VPN"""
    timestamp: float
    operation: str
    error_type: str
    message: str
    details: dict

    def to_dict(self) -> dict:
        """Преобразует ошибку в словарь для передачи в frontend"""
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details
        }


class VPNProvider(ABC):
    """Абстрактный базовый класс для VPN провайдеров"""
    
    @abstractmethod
    def start(self) -> Tuple[bool, Optional[VPNError]]:
        """Запускает VPN сервис. Возвращает (успех, ошибка)"""
        pass
    
    @abstractmethod
    def stop(self) -> Tuple[bool, Optional[VPNError]]:
        """Останавливает VPN сервис. Возвращает (успех, ошибка)"""
        pass
    
    @abstractmethod
    def get_status(self) -> Tuple[str, Optional[VPNError]]:
        """Получает статус VPN сервиса. Возвращает (статус, ошибка)"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Возвращает имя провайдера"""
        pass


class AmneziaWGProvider(VPNProvider):
    """Провайдер для AmneziaWG VPN"""
    
    def __init__(self, service_name: str = "awg-quick@awg0"):
        self.service_name = service_name
    
    def get_name(self) -> str:
        return f"AmneziaWG ({self.service_name})"
    
    def _run_systemctl(self, command: str, operation: str, use_now: bool = False) -> Tuple[bool, Optional[str], Optional[VPNError]]:
        """
        Выполняет systemctl команду.
        Возвращает (успех, вывод, ошибка)
        """
        try:
            cmd = ["systemctl", command]
            if use_now:
                cmd.append("--now")
            cmd.append(self.service_name)
            decky.logger.info(f"Executing: {' '.join(cmd)}")
            
            # Очищаем LD_LIBRARY_PATH чтобы systemctl использовал системные библиотеки
            # а не библиотеки из временной директории PyInstaller
            env = os.environ.copy()
            if 'LD_LIBRARY_PATH' in env:
                # Убираем пути PyInstaller из LD_LIBRARY_PATH
                paths = env['LD_LIBRARY_PATH'].split(':')
                paths = [p for p in paths if '/tmp/' not in p and '_MEI' not in p]
                if paths:
                    env['LD_LIBRARY_PATH'] = ':'.join(paths)
                else:
                    del env['LD_LIBRARY_PATH']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                env=env
            )
            
            if result.returncode == 0:
                return (True, result.stdout.strip(), None)
            else:
                # systemctl is-active возвращает 1 для inactive (это нормально, не ошибка)
                if command == "is-active" and result.returncode == 1:
                    return (True, "inactive", None)
                
                # systemctl is-active возвращает 3 для несуществующего сервиса (тоже не критично для статуса)
                if command == "is-active" and result.returncode == 3:
                    decky.logger.warning(f"Service {self.service_name} not found, returning inactive status")
                    return (True, "inactive", None)
                
                # Для других команд и кодов возвращаем ошибку
                error_type = "CommandFailed"
                if result.returncode == 1:
                    error_type = "ServiceError"
                elif result.returncode == 3:
                    error_type = "ServiceNotFound"
                elif result.returncode == 4:
                    error_type = "PermissionDenied"
                elif result.returncode == 5:
                    error_type = "Timeout"
                
                error = VPNError(
                    timestamp=time.time(),
                    operation=operation,
                    error_type=error_type,
                    message=result.stderr.strip() or f"Command failed with return code {result.returncode}",
                    details={
                        "return_code": result.returncode,
                        "stdout": result.stdout.strip(),
                        "stderr": result.stderr.strip(),
                        "command": " ".join(cmd)
                    }
                )
                return (False, None, error)
                
        except FileNotFoundError:
            error = VPNError(
                timestamp=time.time(),
                operation=operation,
                error_type="FileNotFoundError",
                message="systemctl command not found",
                details={"command": "systemctl"}
            )
            return (False, None, error)
            
        except PermissionError as e:
            error = VPNError(
                timestamp=time.time(),
                operation=operation,
                error_type="PermissionError",
                message=str(e),
                details={"command": " ".join(cmd)}
            )
            return (False, None, error)
            
        except Exception as e:
            error = VPNError(
                timestamp=time.time(),
                operation=operation,
                error_type=type(e).__name__,
                message=str(e),
                details={"command": " ".join(cmd), "exception_type": type(e).__name__}
            )
            return (False, None, error)
    
    def start(self) -> Tuple[bool, Optional[VPNError]]:
        """Запускает AmneziaWG VPN сервис"""
        success, _, error = self._run_systemctl("start", "start", use_now=True)
        return (success, error)
    
    def stop(self) -> Tuple[bool, Optional[VPNError]]:
        """Останавливает AmneziaWG VPN сервис"""
        success, _, error = self._run_systemctl("stop", "stop", use_now=True)
        return (success, error)
    
    def get_status(self) -> Tuple[str, Optional[VPNError]]:
        """Получает статус AmneziaWG VPN сервиса"""
        success, output, error = self._run_systemctl("is-active", "status")
        if success:
            # systemctl is-active возвращает "active" или "inactive"
            # output уже содержит правильный статус от _run_systemctl
            status = output if output else "inactive"
            return (status, None)
        else:
            # Если была ошибка, но это ServiceNotFound для is-active, 
            # то _run_systemctl уже вернул "inactive", так что сюда не должны попасть
            return ("unknown", error)


class Plugin:
    def __init__(self):
        """Инициализация плагина"""
        self.errors: List[VPNError] = []
        self.max_errors = 50  # Максимальное количество хранимых ошибок
        self.providers: Dict[str, VPNProvider] = {}
        self.current_provider: Optional[VPNProvider] = None
        self._status_cache: Optional[Tuple[str, float]] = None  # (status, timestamp)
        self._cache_ttl = 1.0  # Время жизни кэша в секундах
    
    def _add_error(self, error: VPNError):
        """Добавляет ошибку в историю"""
        self.errors.append(error)
        # Ограничиваем размер истории ошибок
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        # Логируем критические ошибки
        decky.logger.error(
            f"VPN Error [{error.error_type}] in {error.operation}: {error.message}"
        )
    
    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        # Инициализация провайдеров
        amnezia_provider = AmneziaWGProvider()
        self.providers["amneziawg"] = amnezia_provider
        self.current_provider = amnezia_provider  # Устанавливаем AmneziaWG как провайдер по умолчанию
        
        decky.logger.info("VPN Deck plugin initialized")
        decky.logger.info(f"Available providers: {list(self.providers.keys())}")
        decky.logger.info(f"Current provider: {self.current_provider.get_name()}")

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

    # VPN методы для вызова из frontend
    
    async def vpn_start(self, retry_count: int = 0) -> dict:
        """Запускает VPN сервис с опциональным retry"""
        if not self.current_provider:
            error = VPNError(
                timestamp=time.time(),
                operation="start",
                error_type="NoProvider",
                message="No VPN provider configured",
                details={}
            )
            self._add_error(error)
            return {"success": False, "error": error.to_dict()}
        
        try:
            success, error = self.current_provider.start()
            if success:
                decky.logger.info(f"VPN started successfully: {self.current_provider.get_name()}")
                # Инвалидируем кэш статуса
                self._status_cache = None
                return {"success": True, "error": None}
            else:
                if error:
                    self._add_error(error)
                return {"success": False, "error": error.to_dict() if error else None}
        except Exception as e:
            error = VPNError(
                timestamp=time.time(),
                operation="start",
                error_type=type(e).__name__,
                message=str(e),
                details={"exception_type": type(e).__name__}
            )
            self._add_error(error)
            return {"success": False, "error": error.to_dict()}
    
    async def vpn_stop(self) -> dict:
        """Останавливает VPN сервис"""
        if not self.current_provider:
            error = VPNError(
                timestamp=time.time(),
                operation="stop",
                error_type="NoProvider",
                message="No VPN provider configured",
                details={}
            )
            self._add_error(error)
            return {"success": False, "error": error.to_dict()}
        
        try:
            success, error = self.current_provider.stop()
            if success:
                decky.logger.info(f"VPN stopped successfully: {self.current_provider.get_name()}")
                # Инвалидируем кэш статуса
                self._status_cache = None
                return {"success": True, "error": None}
            else:
                if error:
                    self._add_error(error)
                return {"success": False, "error": error.to_dict() if error else None}
        except Exception as e:
            error = VPNError(
                timestamp=time.time(),
                operation="stop",
                error_type=type(e).__name__,
                message=str(e),
                details={"exception_type": type(e).__name__}
            )
            self._add_error(error)
            return {"success": False, "error": error.to_dict()}
    
    async def vpn_status(self, use_cache: bool = True) -> dict:
        """Получает статус VPN сервиса с опциональным кэшированием"""
        # Проверяем кэш
        if use_cache and self._status_cache:
            cached_status, cache_time = self._status_cache
            if time.time() - cache_time < self._cache_ttl:
                return {
                    "status": cached_status,
                    "error": None,
                    "cached": True
                }
        
        if not self.current_provider:
            error = VPNError(
                timestamp=time.time(),
                operation="status",
                error_type="NoProvider",
                message="No VPN provider configured",
                details={}
            )
            return {"status": "unknown", "error": error.to_dict()}
        
        try:
            status, error = self.current_provider.get_status()
            # Для статуса не логируем ошибки как критические, только если это не просто "сервис не найден"
            if error and error.error_type != "ServiceNotFound":
                # Логируем только не-критические ошибки статуса как warning, не error
                decky.logger.warning(f"Status check warning: {error.message}")
            else:
                # Обновляем кэш только при успешном запросе
                self._status_cache = (status, time.time())
            
            return {
                "status": status,
                "error": error.to_dict() if error else None,
                "cached": False
            }
        except Exception as e:
            error = VPNError(
                timestamp=time.time(),
                operation="status",
                error_type=type(e).__name__,
                message=str(e),
                details={"exception_type": type(e).__name__}
            )
            decky.logger.warning(f"Status check exception: {str(e)}")
            return {"status": "unknown", "error": error.to_dict()}
    
    async def get_errors(self) -> List[dict]:
        """Возвращает историю ошибок"""
        return [error.to_dict() for error in self.errors]
    
    async def clear_errors(self) -> bool:
        """Очищает историю ошибок"""
        self.errors = []
        decky.logger.info("Error history cleared")
        return True
    
    async def get_providers(self) -> List[str]:
        """Возвращает список доступных провайдеров"""
        return list(self.providers.keys())

    # Migrations that should be performed before entering `_main()`.
    async def _migration(self):
        decky.logger.info("VPN Deck plugin migrating")
        # Migrations can be added here if needed in the future
        pass
