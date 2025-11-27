import os
from typing import Optional, Dict, Any
from pathlib import Path
import json
import urllib.request
import urllib.error

# 设置Hugging Face Hub的API端点为AtomGit
os.environ["HF_ENDPOINT"] = "https://hub.atomgit.com"
# 设置缓存目录
cache_dir = os.path.expanduser("~/.cache/atomgit")
os.makedirs(cache_dir, exist_ok=True)
os.environ["HF_HOME"] = cache_dir


from huggingface_hub import hf_hub_download, upload_folder, create_repo, snapshot_download, whoami

try:
    from .config import config
except ImportError:
    from config import config


class HuggingFaceAPI:
    """AtomGit API 客户端，完全基于Hugging Face Hub SDK"""
    
    def __init__(self):
        pass
    
    def _normalize_repo_id(self, repo_id: str) -> str:
        """标准化仓库ID，处理三层格式转换"""
        parts = repo_id.split('/')
        
        # 如果是三层格式（如 hf_mirrors/Qwen/Qwen2.5-Coder-0.5B-Instruct）
        # 转换为特殊格式（如 hf_mirrors-Qwen/Qwen2.5-Coder-0.5B-Instruct）
        if len(parts) >= 3:
            # 只编码第一个斜杠，保留后面的斜杠
            first_part = parts[0]
            second_part = parts[1]
            remaining_parts = parts[2:]
            
            # 构建新格式：第一部分-第二部分/其余部分
            normalized = first_part + '-' + second_part
            if remaining_parts:
                normalized += '/' + '/'.join(remaining_parts)
            
            print(f"三层仓库名称转换: {repo_id} -> {normalized}")
            return normalized
        
        # 二层或单层格式直接返回
        return repo_id
    
    def login(self, token: str) -> bool:
        """登录验证"""
        if not token or len(token) < 10:
            print("❌ Token格式不正确")
            return False
            
        # 简单保存token，先不验证API
        config.set_credentials(token)
        print("✅ Token已保存")
        return True
    
    def get_login_user(self):
        try:
            credentials = config.get_credentials()
            if not credentials:
                print("❌ 未找到登录凭证")
                return None
            api_url = 'https://atomgit.com/api/v5/user'
            req = urllib.request.Request(
                api_url,
                headers={
                    'Authorization': credentials['token'],
                    'User-Agent': 'atomgit-cli',
                    'Accept': 'application/json'
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    login = data.get('login')
                    if login and login.strip():
                        return {
                            'login': login,
                            'name': data.get('name'),
                            'email': data.get('email')
                        }
            return None
        except Exception as e:
            return None
    
    def create_repo(self, 
                    repo_name: str,
                    repo_type: str = "model", 
                    private: bool = False) -> bool:
        """创建仓库 - 使用Hugging Face Hub SDK"""
        try:
            credentials = config.get_credentials()
            if not credentials:
                print("❌ 未找到登录凭证")
                return False
            # 使用Hugging Face Hub SDK创建仓库
            create_repo(
                repo_id=repo_name,
                token=credentials['token'],
                repo_type=repo_type,
                private=private,
                exist_ok=True
            )
            return True
        except Exception as e:
            return False
    
    def upload_folder(self, file_path: Path, repo_id: str, 
                   remote_path: str = None, message: str = None) -> bool:
        """上传文件 - 使用Hugging Face Hub SDK"""
        try:
            if not file_path.exists():
                print(f"文件不存在: {file_path}")
                return False
            
            credentials = config.get_credentials()
            if not credentials:
                print("未找到登录凭证")
                return False
            
            # 创建一个临时目录在当前工作目录下
            temp_dir = Path.cwd() / ".tmp_upload"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                if remote_path:
                    # 如果指定了远程路径，创建相应的目录结构
                    target_file = temp_dir / remote_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                else:
                    target_file = temp_dir / file_path.name
                # 复制文件到临时目录
                import shutil
                shutil.copy2(file_path, target_file)
                # 使用Hugging Face Hub SDK上传整个目录
                commit_message = message or "Upload folder using atomgit client"
                upload_folder(
                    repo_id=repo_id,
                    folder_path=str(temp_dir),
                    token=credentials['token'],
                    commit_message=commit_message
                )
                return True
            finally:
                # 清理临时目录
                import shutil
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"上传文件失败: {e}")
            return False
    
    def upload_directory(self, dir_path: Path, repo_id: str, 
                        message: str = None, progress_callback=None) -> bool:
        """上传目录 - 使用Hugging Face Hub SDK"""
        try:
            if not dir_path.exists() or not dir_path.is_dir():
                print(f"目录不存在: {dir_path}")
                return False
            
            credentials = config.get_credentials()
            if not credentials:
                print("未找到登录凭证")
                return False
            
            # 直接使用Hugging Face Hub SDK上传目录
            commit_message = message or "Upload folder using atomgit client"
            upload_folder(
                repo_id=repo_id,
                folder_path=str(dir_path),
                token=credentials['token'],
                commit_message=commit_message
            )
            
            return True
            
        except Exception as e:
            print(f"上传目录失败: {e}")
            return False
    
    def download_repo(self, repo_id: str, local_path: Path = None, force_download: bool = False) -> bool:
        """下载仓库 - 使用Hugging Face Hub SDK，支持公开仓库无需token和断点续传"""
        try:
            # 标准化仓库ID（处理三层格式）
            normalized_repo_id = self._normalize_repo_id(repo_id)
            
            if local_path is None:
                local_path = Path.cwd() / repo_id.split('/')[-1]
            
            # 创建本地目录
            local_path.mkdir(parents=True, exist_ok=True)
            
            # 首先尝试不使用token下载（适用于公开仓库）
            credentials = config.get_credentials()
            try:
                snapshot_download(
                    repo_id=normalized_repo_id,
                    local_dir=str(local_path),
                    force_download=force_download,  # 根据用户选择决定是否强制下载
                    token=credentials['token'] if credentials and 'token' in credentials else None
                )
                print(f"✅ 仓库下载成功")
                return True
            except Exception as e:
                error_msg = str(e)                
                # 其他类型的错误（如仓库不存在）
                print(f"仓库下载失败: {error_msg}")
                return False
        except Exception as e:
            print(f"下载仓库失败: {e}")
            return False
    
    def download_file(self, repo_id: str, filename: str, local_path: Path = None, force_download: bool = False) -> bool:
        """下载单个文件 - 使用Hugging Face Hub SDK，支持公开仓库无需token和断点续传"""
        try:
            # 标准化仓库ID（处理三层格式）
            normalized_repo_id = self._normalize_repo_id(repo_id)
            
            if local_path is None:
                local_path = Path.cwd()
            
            # 创建本地目录
            local_path.mkdir(parents=True, exist_ok=True)
            
            # 首先尝试不使用token下载（适用于公开仓库）
            try:
                hf_hub_download(
                    repo_id=normalized_repo_id,
                    filename=filename,
                    local_dir=str(local_path)
                )
                print(f"✅ 文件下载成功")
                return True
            except Exception as e:
                error_msg = str(e)
                print(f"公开下载失败: {error_msg}")
                
                # 检查是否是认证问题
                if "403" in error_msg or "FORBIDDEN" in error_msg or "no scopes" in error_msg:
                    print("检测到认证问题，尝试使用token下载...")
                    
                    # 如果公开下载失败，尝试使用token下载
                    credentials = config.get_credentials()
                    if credentials:
                        try:
                            hf_hub_download(
                                repo_id=normalized_repo_id,
                                filename=filename,
                                local_dir=str(local_path),
                                token=credentials['token']
                            )
                            print(f"✅ 下载完成")
                            return True
                        except Exception as token_e:
                            print(f"下载失败: {token_e}")
                            return False
                    else:
                        print("未找到登录凭证，无法尝试私有仓库下载")
                        print("💡 建议：如果这是私有仓库，请先使用 'atomgit login' 登录")
                        return False
                else:
                    # 其他类型的错误（如仓库不存在、文件不存在）
                    print(f"文件下载失败: {error_msg}")
                    return False
            
        except Exception as e:
            print(f"下载文件失败: {e}")
            return False
    
    def get_repo_info(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """获取仓库信息 - 此功能需要Hugging Face Hub SDK支持"""
        try:
            # 目前Hugging Face Hub SDK可能不直接支持获取仓库信息
            # 这里返回基础信息
            return {
                "repo_id": repo_id,
                "status": "需要Hugging Face Hub SDK支持"
            }
            
        except Exception as e:
            print(f"获取仓库信息失败: {e}")
            return None


# 全局API实例
api = HuggingFaceAPI() 