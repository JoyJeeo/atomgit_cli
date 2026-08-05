import os
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """配置管理类，用于管理用户认证信息和设置"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.atomgit'
        self.config_file = self.config_dir / 'config.json'
        self._config = None

    def _ensure_loaded(self) -> Dict[str, Any]:
        """Load configuration on first use without import-time filesystem I/O."""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                self.config_dir.chmod(0o700)
                self.config_file.chmod(0o600)
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                return loaded if isinstance(loaded, dict) else {}
            except (json.JSONDecodeError, OSError):
                return {}
        return {}
    
    def _save_config(self, updated: Dict[str, Any]) -> None:
        """Atomically replace the credential file with a private temporary."""
        temporary_path = None
        temporary_fd = None
        try:
            self.config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            self.config_dir.chmod(0o700)
            temporary_fd, temporary_name = tempfile.mkstemp(
                prefix='.config.json.',
                suffix='.tmp',
                dir=str(self.config_dir),
            )
            temporary_path = Path(temporary_name)
            os.fchmod(temporary_fd, 0o600)
            temporary_file = os.fdopen(temporary_fd, 'w', encoding='utf-8')
            temporary_fd = None  # ownership transferred to temporary_file
            with temporary_file as f:
                json.dump(updated, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(str(temporary_path), str(self.config_file))
            temporary_path = None
        except (OSError, TypeError, ValueError) as e:
            raise Exception(f"无法保存配置文件: {e}")
        finally:
            if temporary_fd is not None:
                try:
                    os.close(temporary_fd)
                except OSError:
                    pass
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except OSError:
                    pass

    def _commit(self, updated: Dict[str, Any]) -> None:
        """Persist first so a failed save cannot corrupt in-memory state."""
        self._save_config(updated)
        self._config = updated
    
    def set_credentials(self, token: str) -> None:
        """设置用户认证信息"""
        updated = dict(self._ensure_loaded())
        updated['token'] = token
        self._commit(updated)
    
    def get_credentials(self) -> Optional[Dict[str, str]]:
        """获取用户认证信息"""
        token = self._ensure_loaded().get('token')
        if token:
            return {'token': token}
        return None
    
    def clear_credentials(self) -> None:
        """清除用户认证信息"""
        updated = dict(self._ensure_loaded())
        updated.pop('username', None)  # 保留以兼容旧配置
        updated.pop('token', None)
        self._commit(updated)
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.get_credentials() is not None
    
    def set_value(self, key: str, value: Any) -> None:
        """设置配置值"""
        updated = dict(self._ensure_loaded())
        updated[key] = value
        self._commit(updated)
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._ensure_loaded().get(key, default)


# 全局配置实例
config = Config()
