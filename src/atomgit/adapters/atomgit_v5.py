"""AtomGit V5 adapter with bounded, credential-safe calls."""


class AtomGitV5Adapter:
    """Adapt the verified V5 service helpers to core repository ports."""

    def __init__(self, *, service_module=None, api=None):
        if service_module is None:
            from ..services import repositories as service_module
        self.service = service_module
        if api is None:
            from ..api import api as api_object

            api = api_object
        self.api = api

    def create(
        self,
        repo_id: str,
        repo_type: str,
        private: bool,
        exist_ok: bool,
        token: str = None,
    ):
        from huggingface_hub import create_repo

        if not token:
            raise ValueError("missing AtomGit credential")
        result = create_repo(
            repo_id=repo_id,
            token=token,
            private=True,
            repo_type="model" if repo_type == "dataset" else repo_type,
            exist_ok=exist_ok,
        )
        if not private and not self.set_visibility(repo_id, False, token):
            raise RuntimeError("repository visibility could not be verified")
        return result

    def list(self, token: str):
        payload = self.service._atomgit_v5_get_json("/user/repos", token)
        if isinstance(payload, dict):
            for key in ("data", "repositories"):
                if isinstance(payload.get(key), list):
                    payload = payload[key]
                    break
        if not isinstance(payload, list) or not all(
            isinstance(item, dict) for item in payload
        ):
            raise ValueError("repository collection is malformed")
        return payload

    def set_visibility(self, repo_id: str, private: bool, token: str) -> bool:
        path = self.service._atomgit_v5_repo_path(repo_id)
        self.service._atomgit_v5_request_json(
            "PATCH", path, token, {"private": private}
        )
        payload = self.service._atomgit_v5_get_json(path, token)
        return self.service._repo_private_state(payload) is private

    def create_branch(self, repo_id: str, branch: str, source: str, token: str) -> bool:
        repo_path = self.service._atomgit_v5_repo_path(repo_id)
        source_payload = self.service._atomgit_v5_get_json(
            repo_path + "/commits/" + self.service.quote(source, safe=""), token
        )
        source_commit = self.service._atomgit_v5_commit_sha(source_payload)
        if source_commit is None:
            raise ValueError("source revision commit is unavailable")
        base_path = repo_path + "/branches"
        self.service._atomgit_v5_request_json(
            "POST", base_path, token, {"branch_name": branch, "refs": source}
        )
        payload = self.service._atomgit_v5_get_json(
            base_path + "/" + self.service.quote(branch, safe=""), token
        )
        return (
            isinstance(payload, dict)
            and payload.get("name") == branch
            and self.service._atomgit_v5_branch_commit_id(payload) == source_commit
        )

    def delete(self, repo_id: str, confirmation: str, token: str) -> bool:
        path = self.service._atomgit_v5_repo_path(repo_id)
        self.service._atomgit_v5_get_json(path, token)
        self.service._atomgit_v5_request_json("DELETE", path, token)
        try:
            self.service._atomgit_v5_get_json(path, token)
        except Exception as error:
            if getattr(error, "code", None) == 404:
                return True
            raise
        return False

    def authenticate(self, token: str):
        return self.api._get_login_user_by_token(token)

    def current_identity(self, token: str):
        return self.authenticate(token)

    def clear(self):
        from ..infrastructure.config import config

        config.clear_credentials()


__all__ = ["AtomGitV5Adapter"]
