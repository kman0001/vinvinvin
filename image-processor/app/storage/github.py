import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.storage.base import Storage


class GitHubStorage(Storage):
    """GitHub repository storage using the GitHub Contents API."""

    def __init__(self, config):
        super().__init__(config)
        self.repository = config.get("repository", "").strip()
        self.branch = config.get("branch", "main").strip() or "main"
        self.base_path = config.get("path", "").strip().strip("/")
        self.token = (
            os.environ.get(config.get("token_env", "GITHUB_TOKEN"), "").strip()
            or config.get("token", "").strip()
        )
        if not self.repository:
            raise ValueError("github.repository is required")
        if not self.token:
            raise ValueError("GitHub token is required")
        if "/" not in self.repository:
            raise ValueError("github.repository must be in owner/repository form")

    def _url(self, destination):
        path = "/".join(part for part in (self.base_path, destination.strip("/")) if part)
        encoded = "/".join(__import__("urllib.parse", fromlist=["quote"]).quote(p, safe="") for p in path.split("/"))
        return f"https://api.github.com/repos/{self.repository}/contents/{encoded}"

    def _request(self, method, url, body=None):
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "vinvinvin-image-processor/1.0",
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=data, headers=headers, method=method)
        return urlopen(request, timeout=30)  # nosec B310 - fixed GitHub API host

    def _get_sha(self, destination):
        try:
            with self._request("GET", f"{self._url(destination)}?ref={self.branch}") as response:
                return json.load(response).get("sha")
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise

    def upload(self, source: Path, destination: str):
        content = source.read_bytes()
        payload = {
            "message": f"Update menu image: {destination}",
            "content": __import__("base64").b64encode(content).decode("ascii"),
            "branch": self.branch,
        }
        sha = self._get_sha(destination)
        if sha:
            payload["sha"] = sha
        with self._request("PUT", self._url(destination), payload):
            pass

    def delete(self, destination: str):
        sha = self._get_sha(destination)
        if not sha:
            return
        payload = {
            "message": f"Delete menu image: {destination}",
            "sha": sha,
            "branch": self.branch,
        }
        with self._request("DELETE", self._url(destination), payload):
            pass

    def exists(self, destination: str) -> bool:
        return self._get_sha(destination) is not None
