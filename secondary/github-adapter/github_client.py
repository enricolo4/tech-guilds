import hmac
import hashlib
import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


def verify_github_signature(payload_bytes: bytes, signature_header: Optional[str], secret: str) -> bool:
    """Valida a assinatura HMAC SHA-256 do webhook do GitHub (X-Hub-Signature-256)."""
    if not signature_header or not secret:
        return False
    parts = signature_header.split("=", 1)
    if len(parts) != 2 or parts[0] != "sha256":
        return False
    expected_hash = parts[1]
    mac = hmac.new(secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), expected_hash)


class GitHubClient:
    """Cliente assíncrono para a API REST do GitHub.
    Suporta verificação de assinaturas de webhook e operações com issues/PRs.
    """
    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com",
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 10.0,
    ):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._custom_client = client is not None
        self._client = client or httpx.AsyncClient(timeout=timeout)

    async def get_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """Obtém informações completas de um Pull Request."""
        if not self.token or self.token == "mock":
            return {
                "number": pull_number,
                "title": "PR Mock Title",
                "state": "open",
                "merged": False,
                "user": {"login": "mock_hero", "email": "hero@company.local"},
                "additions": 150,
                "deletions": 20,
            }

        headers = self._headers()
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}"
        res = await self._client.get(url, headers=headers)
        res.raise_for_status()
        return res.json()

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """Obtém detalhes de uma Issue."""
        if not self.token or self.token == "mock":
            return {
                "number": issue_number,
                "title": "Bug Mock Title",
                "state": "open",
                "labels": [{"name": "bug"}],
                "user": {"login": "reporter_hero"},
            }

        headers = self._headers()
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        res = await self._client.get(url, headers=headers)
        res.raise_for_status()
        return res.json()

    async def add_comment(self, owner: str, repo: str, issue_or_pr_number: int, comment: str) -> Dict[str, Any]:
        """Adiciona um comentário no PR ou Issue."""
        if not self.token or self.token == "mock":
            logger.info(f"[GitHubClient (Mock)] Comentário em #{issue_or_pr_number}: {comment}")
            return {"id": 12345, "body": comment}

        headers = self._headers()
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_or_pr_number}/comments"
        res = await self._client.post(url, headers=headers, json={"body": comment})
        res.raise_for_status()
        return res.json()

    async def add_labels(self, owner: str, repo: str, issue_or_pr_number: int, labels: List[str]) -> List[Dict[str, Any]]:
        """Adiciona labels a uma Issue ou PR."""
        if not self.token or self.token == "mock":
            logger.info(f"[GitHubClient (Mock)] Labels adicionadas a #{issue_or_pr_number}: {labels}")
            return [{"name": label} for label in labels]

        headers = self._headers()
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_or_pr_number}/labels"
        res = await self._client.post(url, headers=headers, json={"labels": labels})
        res.raise_for_status()
        return res.json()

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def aclose(self) -> None:
        if not self._custom_client:
            await self._client.aclose()

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
