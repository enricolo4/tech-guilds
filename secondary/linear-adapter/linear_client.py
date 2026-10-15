import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class LinearClient:
    """Cliente assíncrono para a API GraphQL do Linear.
    Suporta autenticação via API Key e modo mock/offline resiliente para testes.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.linear.app/graphql",
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 10.0,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._custom_client = client is not None
        self._client = client or httpx.AsyncClient(timeout=timeout)

    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executa uma query ou mutation GraphQL contra o endpoint do Linear."""
        if not self.api_key or self.api_key == "mock":
            logger.info("[LinearClient (Mock)] Executando GraphQL query sem chave real.")
            return {"data": {"mock": True, "query": query, "variables": variables or {}}}

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"query": query, "variables": variables or {}}

        try:
            response = await self._client.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                logger.error(f"[LinearClient] Erros retornados pelo Linear: {data['errors']}")
            return data
        except httpx.HTTPError as e:
            logger.error(f"[LinearClient] Falha HTTP na requisição GraphQL: {e}")
            raise

    async def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """Recupera detalhes de uma Issue no Linear."""
        query = """
        query GetIssue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                priority
                estimate
                state {
                    id
                    name
                    type
                }
                assignee {
                    id
                    name
                    email
                }
                project {
                    id
                    name
                }
                cycle {
                    id
                    number
                    name
                }
                labels {
                    nodes {
                        id
                        name
                        color
                    }
                }
            }
        }
        """
        if not self.api_key or self.api_key == "mock":
            return {
                "data": {
                    "issue": {
                        "id": issue_id,
                        "identifier": "LIN-101",
                        "title": "Tarefa Mock Linear",
                        "description": "Descrição mockada da tarefa",
                        "priority": 2,
                        "estimate": 3,
                        "state": {"id": "state-1", "name": "In Progress", "type": "started"},
                        "assignee": {"id": "user-1", "name": "Hero Dev", "email": "dev@company.local"},
                        "project": {"id": "proj-1", "name": "Épico Principal"},
                        "cycle": {"id": "cycle-1", "number": 1, "name": "Sprint 1"},
                        "labels": {"nodes": [{"id": "lbl-1", "name": "Feature"}]},
                    }
                }
            }

        return await self.execute_query(query, {"id": issue_id})

    async def update_issue_status(self, issue_id: str, state_id: str) -> Dict[str, Any]:
        """Atualiza o estado de uma Issue no Linear."""
        mutation = """
        mutation UpdateIssueState($id: String!, $stateId: String!) {
            issueUpdate(id: $id, input: { stateId: $stateId }) {
                success
                issue {
                    id
                    identifier
                    state {
                        id
                        name
                    }
                }
            }
        }
        """
        if not self.api_key or self.api_key == "mock":
            return {
                "data": {
                    "issueUpdate": {
                        "success": True,
                        "issue": {
                            "id": issue_id,
                            "identifier": "LIN-101",
                            "state": {"id": state_id, "name": "Done"},
                        },
                    }
                }
            }

        return await self.execute_query(mutation, {"id": issue_id, "stateId": state_id})

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Recupera detalhes de um Projeto (Aventura/Épico) no Linear."""
        query = """
        query GetProject($id: String!) {
            project(id: $id) {
                id
                name
                description
                progress
                state
            }
        }
        """
        if not self.api_key or self.api_key == "mock":
            return {
                "data": {
                    "project": {
                        "id": project_id,
                        "name": "Épico Linear Mock",
                        "description": "Aventura épica de Squad",
                        "progress": 0.5,
                        "state": "started",
                    }
                }
            }

        return await self.execute_query(query, {"id": project_id})

    async def get_viewer(self) -> Dict[str, Any]:
        """Verifica as credenciais do usuário autenticado no Linear."""
        query = """
        query GetViewer {
            viewer {
                id
                name
                email
            }
        }
        """
        if not self.api_key or self.api_key == "mock":
            return {
                "data": {
                    "viewer": {
                        "id": "viewer-mock",
                        "name": "Tech Guild Master",
                        "email": "guildmaster@company.local",
                    }
                }
            }

        return await self.execute_query(query)

    async def aclose(self) -> None:
        """Encerra a conexão HTTP subjacente se foi instanciada localmente."""
        if not self._custom_client:
            await self._client.aclose()

    async def __aenter__(self) -> "LinearClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
