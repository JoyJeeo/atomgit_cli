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


from huggingface_hub import (
    hf_hub_download, upload_folder, create_repo, snapshot_download,
    constants as hf_constants, HfApi,
)

try:
    from .config import config
    from .utils import normalize_path_in_repo, parse_ignore_patterns
except ImportError:
    from config import config
    from utils import normalize_path_in_repo, parse_ignore_patterns

try:
    # 单文件上传专用：直接以 path_or_fileobj 上传，避免本地拷贝
    from huggingface_hub import upload_file as hf_upload_file
except ImportError:  # 老版本兜底
    hf_upload_file = None

try:
    # huggingface_hub >= 0.14 提供的进度条程序化开关
    from huggingface_hub.utils import enable_progress_bars, disable_progress_bars
except ImportError:  # 老版本无此 API 时，提供 no-op 回退，保证可用
    def enable_progress_bars(*args, **kwargs):
        pass

    def disable_progress_bars(*args, **kwargs):
        pass


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
                   revision: str = None,
                   ignore_patterns=None) -> bool:
        """上传单个文件 - 使用Hugging Face Hub SDK

        优先使用 HF ``upload_file`` 直接以文件路径上传，避免旧实现中
        "先 copy 到 ``.tmp_upload`` 再上传"的额外本地拷贝开销；仅在
        HF 版本过旧（无 ``upload_file``）时回退到 ``upload_folder``
        + 临时目录拷贝的旧行为。

        Args:
            path_in_repo: 仓库内目标目录前缀。为空/``./`` 时上传到仓库根目录；
                否则文件会被放到该前缀下（如 ``sub/`` → ``sub/<文件名>``）。
            repo_type: 仓库类型，``model`` 或 ``dataset``。为空时由 HF
                默认按 ``model`` 处理（保持既有行为）。
            revision: 上传目标分支/版本。为空时提交到 HF 默认分支（通常
                ``main``）；指定时若分支不存在会自动创建。注意：目标分支
                不存在已有文件时，上传会从空状态开始。
            ignore_patterns: 单文件上传路径下该参数仅会匹配 ``file_path.name``，
                几乎不生效——主要对目录上传有意义。新实现（``upload_file``）
                不支持该参数，传入时若非空会回退到 ``upload_folder`` 旧路径
                以保留语义。
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

            # 显式设置 HF Hub 进度条状态（进程级，try/finally 中恢复默认开启）
            _set_progress_bar(progress_bar)

            commit_message = message or "Upload folder using atomgit client"
            # 使用 Monkey Patch 方式临时修改 huggingface_hub 的默认超时配置
            hf_constants.DEFAULT_REQUEST_TIMEOUT = upload_timeout

            try:
                # 路径2（推荐）：直接 upload_file，无本地拷贝
                if hf_upload_file is not None and not ignore_patterns:
                    # upload_file 需要完整的 path_in_repo（含文件名）
                    remote_file_path = f"{pipr}/{file_path.name}" if pipr else file_path.name
                    file_kwargs = dict(
                        path_or_fileobj=str(file_path),
                        path_in_repo=remote_file_path,
                        repo_id=repo_id,
                        token=credentials['token'],
                        commit_message=commit_message,
                    )
                    if repo_type is not None:
                        file_kwargs['repo_type'] = repo_type
                    if revision is not None:
                        file_kwargs['revision'] = revision
                    hf_upload_file(**file_kwargs)
                    return True

                # 路径1（回退）：upload_folder + 临时目录拷贝（旧实现）
                # 触发条件：HF 版本过旧无 upload_file，或用户传了 ignore_patterns
                temp_dir = Path.cwd() / ".tmp_upload"
                temp_dir.mkdir(exist_ok=True)
                try:
                    if pipr:
                        target_file = temp_dir / pipr / file_path.name
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        upload_path_in_repo = f"{pipr}/"
                    else:
                        target_file = temp_dir / file_path.name
                        upload_path_in_repo = "./"
                    import shutil
                    shutil.copy2(file_path, target_file)
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
                    if ignore_patterns:
                        upload_kwargs['ignore_patterns'] = ignore_patterns
                    upload_folder(**upload_kwargs)
                    return True
                finally:
                    import shutil
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
            finally:
                # 恢复 HF Hub 进度条为默认开启状态，避免污染同进程后续调用
                _set_progress_bar(True)
        except Exception as e:
            print(f"上传文件失败: {e}")
            return False

    def upload_directory(self, dir_path: Path, repo_id: str,
                        message: str = None, progress_callback=None,
                        upload_timeout: float = 300.0,
                        progress_bar: bool = True,
                        path_in_repo: str = None,
                        repo_type: str = None,
                        revision: str = None,
                        ignore_patterns=None,
                        resumable: bool = False,
                        num_workers: int = None) -> bool:
        """上传目录 - 使用Hugging Face Hub SDK

        Args:
            path_in_repo: 仓库内目标目录前缀。为空/``./`` 时上传到仓库根目录；
                否则目录内容会被放到该前缀下。
            repo_type: 仓库类型，``model`` 或 ``dataset``。为空时由 HF
                默认按 ``model`` 处理（保持既有行为）。
            revision: 上传目标分支/版本。为空时提交到 HF 默认分支（通常
                ``main``）；指定时若分支不存在会自动创建。
            ignore_patterns: 忽略的文件模式列表（fnmatch/glob 风格，如
                ``*.tmp``、``logs/``、``**/.DS_Store``）。为 None 时不忽略。
            resumable: 是否启用可断点续传/分块上传模式。为 True 时改用 HF
                ``upload_large_folder``：进程级元数据写入目录下
                ``.cache/.huggingface/``，中断后再次执行可自动续传；适合
                大目录。注意该模式下的限制（HF 既定）：
                (1) ``path_in_repo`` 不生效（需本地自行组织目录结构）；
                (2) ``message`` / ``commit_message`` 不生效（会产生多次提交）；
                (3) ``repo_type`` 必须有值（HF 要求），为空时默认 ``model``。
            num_workers: 仅 ``resumable=True`` 生效，并发 worker 数；为空时
                由 HF 默认决定。
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

            # 显式设置 HF Hub 进度条状态（进程级，try/finally 中恢复默认开启）
            _set_progress_bar(progress_bar)

            try:
                commit_message = message or "Upload folder using atomgit client"
                hf_constants.DEFAULT_REQUEST_TIMEOUT = upload_timeout

                if resumable:
                    # 断点续传/分块上传：走 upload_large_folder
                    eff_repo_type = repo_type or "model"
                    lf_kwargs = dict(
                        repo_id=repo_id,
                        folder_path=str(dir_path),
                        repo_type=eff_repo_type,
                        token=credentials['token'],
                    )
                    if revision is not None:
                        lf_kwargs['revision'] = revision
                    if ignore_patterns:
                        lf_kwargs['ignore_patterns'] = ignore_patterns
                    if num_workers is not None:
                        lf_kwargs['num_workers'] = num_workers
                    if pipr:
                        # upload_large_folder 不支持 path_in_repo，显式提示
                        print("⚠ 注意：resumable 模式不支持 path_in_repo，"
                              "如需子目录请本地自行组织目录结构")
                    # 构造带端点/token 的 HfApi 实例（endpoint 已由环境变量重定向）
                    hf_api = HfApi()
                    hf_api.upload_large_folder(**lf_kwargs)
                else:
                    # 仓库内目标前缀：空 → "./"（根目录）
                    upload_path_in_repo = pipr + "/" if pipr else "./"
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
                    if ignore_patterns:
                        upload_kwargs['ignore_patterns'] = ignore_patterns
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