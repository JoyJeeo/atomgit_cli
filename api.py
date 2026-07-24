import os
from typing import Optional, Dict, Any
from pathlib import Path
import json
import urllib.request
import urllib.error

# 设置Hugging Face Hub的API端点为AtomGit
os.environ["HF_ENDPOINT"] = "https://hub.atomgit.com"
# 禁用Xet协议，避免 xet-write-token 请求
os.environ["HF_HUB_DISABLE_XET"] = "1"
# 设置缓存目录
cache_dir = os.path.expanduser("~/.cache/atomgit")
os.makedirs(cache_dir, exist_ok=True)
os.environ["HF_HOME"] = cache_dir


from huggingface_hub import hf_hub_download, upload_folder, create_repo, snapshot_download, constants as hf_constants

try:
    # huggingface_hub >= 0.14 提供的进度条程序化开关
    from huggingface_hub.utils import enable_progress_bars, disable_progress_bars
except ImportError:  # 老版本无此 API 时，提供 no-op 回退，保证可用
    def enable_progress_bars(*args, **kwargs):
        pass

    def disable_progress_bars(*args, **kwargs):
        pass

try:
    from .config import config
    from .utils import normalize_path_in_repo
except ImportError:
    from config import config
    from utils import normalize_path_in_repo


def _set_progress_bar(enabled: bool) -> None:
    """控制 Hugging Face Hub 上传过程中的进度条显示。

    注意：此为进程级全局状态（HF Hub 的设计）。
    - enabled=True  时显式开启进度条（防御性兜底，覆盖任何先前禁用）；
    - enabled=False 时关闭进度条（适用于日志/CI 等非交互场景）。

    若环境变量 HF_HUB_DISABLE_PROGRESS_BARS=1 在 import 前已设置，则其优先级最高，
    程序化开关将被忽略（HF Hub 既定行为）。
    """
    try:
        if enabled:
            enable_progress_bars()
        else:
            disable_progress_bars()
    except Exception:
        # 进度条控制不应影响上传主流程
        pass


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
        user_info = self._get_login_user_by_token(token)
        if not user_info:
            print("❌ 获取用户信息失败")
            return False
        config.set_credentials(token)
        print("✅ Token已保存")
        return True
    
    def _get_login_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            if not token:
                print("❌ 未找到登录凭证")
                return None
            api_url = 'https://atomgit.com/api/v5/user'
            req = urllib.request.Request(
                api_url,
                headers={
                    'Authorization': token,
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

    def get_login_user(self):
        credentials = config.get_credentials()
        if not credentials:
            print("❌ 未找到登录凭证")
            return None
        return self._get_login_user_by_token(credentials['token'])
    
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
                   remote_path: str = None, message: str = None,
                   upload_timeout: float = 300.0,
                   progress_bar: bool = True,
                   path_in_repo: str = None,
                   repo_type: str = None,
                   revision: str = None) -> bool:
        """上传文件 - 使用Hugging Face Hub SDK

        Args:
            path_in_repo: 仓库内目标目录前缀。为空/``./`` 时上传到仓库根目录；
                否则文件会被放到该前缀下（如 ``sub/`` → ``sub/<文件名>``）。
            repo_type: 仓库类型，``model`` 或 ``dataset``。为空时由 HF
                默认按 ``model`` 处理（保持既有行为）。
            revision: 上传目标分支/版本。为空时提交到 HF 默认分支（通常
                ``main``）；指定时若分支不存在会自动创建。注意：目标分支
                不存在已有文件时，上传会从空状态开始。
        """
        try:
            if not file_path.exists():
                print(f"文件不存在: {file_path}")
                return False

            credentials = config.get_credentials()
            if not credentials:
                print("未找到登录凭证")
                return False

            # 规范化 path_in_repo（remote_path 为旧别名，向后兼容）
            try:
                pipr = normalize_path_in_repo(path_in_repo if path_in_repo is not None else remote_path)
            except ValueError as e:
                print(f"上传路径不合法: {e}")
                return False

            # 创建一个临时目录在当前工作目录下
            temp_dir = Path.cwd() / ".tmp_upload"
            temp_dir.mkdir(exist_ok=True)

            # 显式设置 HF Hub 进度条状态（进程级，try/finally 中恢复默认开启）
            _set_progress_bar(progress_bar)

            try:
                if pipr:
                    # 指定仓库内路径：按前缀创建子目录结构
                    target_file = temp_dir / pipr / file_path.name
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    upload_path_in_repo = f"{pipr}/"
                else:
                    target_file = temp_dir / file_path.name
                    upload_path_in_repo = "./"
                # 复制文件到临时目录
                import shutil
                shutil.copy2(file_path, target_file)
                # 使用 Monkey Patch 方式临时修改 huggingface_hub 的默认超时配置
                commit_message = message or "Upload folder using atomgit client"
                hf_constants.DEFAULT_REQUEST_TIMEOUT = upload_timeout
                upload_kwargs = dict(
                    repo_id=repo_id,
                    folder_path=str(temp_dir),
                    path_in_repo=upload_path_in_repo,
                    token=credentials['token'],
                    commit_message=commit_message,
                )
                if repo_type is not None:
                    upload_kwargs['repo_type'] = repo_type
                if revision is not None:
                    upload_kwargs['revision'] = revision
                upload_folder(**upload_kwargs)

                return True
            finally:
                # 恢复 HF Hub 进度条为默认开启状态，避免污染同进程后续调用
                _set_progress_bar(True)
                # 清理临时目录
                import shutil
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"上传文件失败: {e}")
            return False

    def upload_directory(self, dir_path: Path, repo_id: str,
                        message: str = None, progress_callback=None,
                        upload_timeout: float = 300.0,
                        progress_bar: bool = True,
                        path_in_repo: str = None,
                        repo_type: str = None,
                        revision: str = None) -> bool:
        """上传目录 - 使用Hugging Face Hub SDK

        Args:
            path_in_repo: 仓库内目标目录前缀。为空/``./`` 时上传到仓库根目录；
                否则目录内容会被放到该前缀下。
            repo_type: 仓库类型，``model`` 或 ``dataset``。为空时由 HF
                默认按 ``model`` 处理（保持既有行为）。
            revision: 上传目标分支/版本。为空时提交到 HF 默认分支（通常
                ``main``）；指定时若分支不存在会自动创建。
        """
        try:
            if not dir_path.exists() or not dir_path.is_dir():
                print(f"目录不存在: {dir_path}")
                return False

            credentials = config.get_credentials()
            if not credentials:
                print("未找到登录凭证")
                return False

            # 规范化 path_in_repo
            try:
                pipr = normalize_path_in_repo(path_in_repo)
            except ValueError as e:
                print(f"上传路径不合法: {e}")
                return False

            # 仓库内目标前缀：空 → "./"（根目录）
            upload_path_in_repo = pipr + "/" if pipr else "./"

            # 显式设置 HF Hub 进度条状态（进程级，try/finally 中恢复默认开启）
            _set_progress_bar(progress_bar)

            try:
                # 使用 Monkey Patch 方式临时修改 huggingface_hub 的默认超时配置
                commit_message = message or "Upload folder using atomgit client"
                hf_constants.DEFAULT_REQUEST_TIMEOUT = upload_timeout
                upload_kwargs = dict(
                    repo_id=repo_id,
                    folder_path=str(dir_path),
                    path_in_repo=upload_path_in_repo,
                    token=credentials['token'],
                    commit_message=commit_message,
                )
                if repo_type is not None:
                    upload_kwargs['repo_type'] = repo_type
                if revision is not None:
                    upload_kwargs['revision'] = revision
                upload_folder(**upload_kwargs)

                return True
            finally:
                # 恢复 HF Hub 进度条为默认开启状态，避免污染同进程后续调用
                _set_progress_bar(True)

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