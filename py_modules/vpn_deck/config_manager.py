"""
ConfigManager - Manages VPN configurations with import and validation
"""

import os
import re
from typing import Optional, Dict, List

import decky


class ConfigManager:
    """Manages VPN configurations with import and validation"""

    def __init__(self):
        # Directories
        self.config_dir = os.path.expanduser("~/.local/share/vpn-deck/configs")
        self.system_config_dir = "/etc/amnezia/amneziawg"

        # Prefix for managed configs (short to leave room for user name; IFNAMSIZ=16)
        self.config_prefix = "vd-"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Creates necessary directories if they don't exist"""
        for directory in [self.config_dir]:
            try:
                os.makedirs(directory, mode=0o700, exist_ok=True)
                decky.logger.info(f"Ensured directory exists: {directory}")
            except Exception as e:
                decky.logger.error(f"Failed to create directory {directory}: {e}")
    
    def _sanitize_name(self, name: str) -> str:
        """
        Sanitizes config name to be filesystem-safe.
        
        Args:
            name: Raw config name
        
        Returns:
            Sanitized name (only a-z, 0-9, -, _)
        """
        # Remove any path separators
        name = os.path.basename(name)
        # Remove .conf extension if present
        if name.endswith('.conf'):
            name = name[:-5]
        # Keep only alphanumeric, dash, underscore
        sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '-', name)
        # Remove multiple consecutive dashes
        sanitized = re.sub(r'-+', '-', sanitized)
        # Remove leading/trailing dashes
        sanitized = sanitized.strip('-')
        # Convert to lowercase
        sanitized = sanitized.lower()
        
        if not sanitized:
            sanitized = "config"

        decky.logger.info(f"Sanitized config name '{name}' to '{sanitized}'")
        return sanitized

    def get_interface_name(self, name: str) -> str:
        return f"{self.config_prefix}{self._sanitize_name(name)}"

    async def scan_existing_configs(self) -> Dict[str, List[Dict]]:
        """
        Scans for all VPN configurations (managed and user-created).
        
        Returns:
            Dictionary with 'managed' and 'existing' config lists
        """
        result = {
            "managed": [],
            "existing": []
        }
        
        try:
            # Scan managed configs in our config directory
            if os.path.isdir(self.config_dir):
                for filename in os.listdir(self.config_dir):
                    if filename.endswith('.conf'):
                        name = filename[:-5]
                        local_path = os.path.join(self.config_dir, filename)
                        interface_name = f"{self.config_prefix}{name}"
                        system_path = os.path.join(self.system_config_dir, f"{interface_name}.conf")
                        
                        is_symlink = False
                        if os.path.islink(system_path):
                            is_symlink = True
                        
                        result["managed"].append({
                            "name": name,
                            "interface": interface_name,
                            "path": local_path,
                            "system_path": system_path,
                            "is_symlink": is_symlink,
                            "managed_by": "vpn-deck"
                        })
            
            # Scan existing configs in system directory
            if os.path.isdir(self.system_config_dir):
                for filename in os.listdir(self.system_config_dir):
                    if filename.endswith('.conf') and not filename.startswith(self.config_prefix):
                        name = filename[:-5]
                        system_path = os.path.join(self.system_config_dir, filename)
                        
                        # Skip if it's a symlink to our managed configs
                        if os.path.islink(system_path):
                            target = os.readlink(system_path)
                            if target.startswith(self.config_dir):
                                continue
                        
                        result["existing"].append({
                            "name": name,
                            "interface": name,
                            "path": system_path,
                            "managed_by": "user"
                        })
            
            decky.logger.debug(f"Found {len(result['managed'])} managed and {len(result['existing'])} existing configs")
            
        except Exception as e:
            decky.logger.error(f"Error scanning configs: {e}")
        
        return result
    
    async def list_all_configs(self) -> List[Dict]:
        """Returns a flat list of all configurations"""
        scanned = await self.scan_existing_configs()
        all_configs = scanned["managed"] + scanned["existing"]
        return all_configs
    
    async def get_config_content(self, name: str) -> Optional[str]:
        """Reads and returns the content of a configuration file"""
        sanitized_name = self._sanitize_name(name)
        config_path = os.path.join(self.config_dir, f"{sanitized_name}.conf")
        
        try:
            if not os.path.isfile(config_path):
                decky.logger.warning(f"Config file not found: {config_path}")
                return None
            
            with open(config_path, 'r') as f:
                content = f.read()
            
            decky.logger.info(f"Read config content from {config_path}")
            return content
            
        except Exception as e:
            decky.logger.error(f"Error reading config {config_path}: {e}")
            return None
    
    def write_config(self, name: str, content: str) -> Dict:
        """Writes config to local store and creates symlink in system directory."""
        sanitized_name = self._sanitize_name(name)
        local_path = os.path.join(self.config_dir, f"{sanitized_name}.conf")
        interface_name = f"{self.config_prefix}{sanitized_name}"
        system_path = os.path.join(self.system_config_dir, f"{interface_name}.conf")

        with open(local_path, "w") as f:
            f.write(content)
        os.chmod(local_path, 0o600)
        decky.logger.info(f"Wrote config to {local_path}")

        try:
            os.makedirs(self.system_config_dir, mode=0o755, exist_ok=True)
            if os.path.exists(system_path) or os.path.islink(system_path):
                os.unlink(system_path)
            os.symlink(local_path, system_path)
            decky.logger.info(f"Created symlink: {system_path} -> {local_path}")
        except Exception as e:
            decky.logger.warning(f"Symlink failed (non-fatal): {e}")

        return {"success": True, "config_name": sanitized_name, "interface_name": interface_name, "error": None}

    async def delete_config(self, name: str) -> Dict:
        """Deletes a VPN configuration (no backup)."""
        result = {
            "success": False,
            "config_name": None,
            "symlink_removed": False,
            "error": None
        }

        try:
            sanitized_name = self._sanitize_name(name)
            result["config_name"] = sanitized_name

            local_path = os.path.join(self.config_dir, f"{sanitized_name}.conf")
            interface_name = f"{self.config_prefix}{sanitized_name}"
            system_path = os.path.join(self.system_config_dir, f"{interface_name}.conf")

            if not os.path.exists(local_path):
                result["error"] = f"Config '{sanitized_name}' not found"
                return result

            os.unlink(local_path)
            decky.logger.info(f"Deleted config file: {local_path}")
            
            if os.path.islink(system_path):
                try:
                    os.unlink(system_path)
                    result["symlink_removed"] = True
                    decky.logger.info(f"Removed symlink: {system_path}")
                except Exception as e:
                    decky.logger.warning(f"Failed to remove symlink {system_path}: {e}")
            
            result["success"] = True
            decky.logger.info(f"Successfully deleted config: {sanitized_name}")
            
        except Exception as e:
            result["error"] = f"Deletion failed: {str(e)}"
            decky.logger.error(f"Error deleting config: {e}")

        return result
