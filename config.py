import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """配置管理类，用于管理用户认证信息和设置"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.atomgit'
        self.config_file = self.config_dir / 'config.json'
        self.config_dir.mkdir(exist_ok=True)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_config(self) -> None:
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise Exception(f"无法保存配置文件: {e}")
    
    def set_credentials(self, token: str) -> None:
        """设置用户认证信息"""
        self._config['token'] = token
        self._save_config()
    
    def get_credentials(self) -> Optional[Dict[str, str]]:
        """获取用户认证信息"""
        token = self._config.get('token')
        if token:
            return {'token': token}
        return None
    
    def clear_credentials(self) -> None:
        """清除用户认证信息"""
        self._config.pop('username', None)  # 保留以兼容旧配置
        self._config.pop('token', None)
        self._save_config()
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.get_credentials() is not None
    
    def set_value(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._config[key] = value
        self._save_config()
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)


# 全局配置实例
config = Config() 