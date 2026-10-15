from typing import Dict, Optional
import httpx
from services.registration.domain.model.user_claims import UserClaims
from services.registration.domain.ports.secondary.sso_port import SSOIdentityPort


class MultiProviderSSOAdapter(SSOIdentityPort):
    """Adaptador de saída (Secondary Adapter) para validação de identidade SSO corporativa.
    Suporta Google Workspace, GitHub Enterprise, Microsoft / Azure AD.
    """

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        self._client = http_client

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def verify_token(self, token: str, provider: str) -> UserClaims:
        provider_normalized = provider.lower().strip()

        if provider_normalized == "google":
            return await self._verify_google(token)
        elif provider_normalized == "github":
            return await self._verify_github(token)
        elif provider_normalized in ["azure", "microsoft"]:
            return await self._verify_microsoft_azure(token)
        else:
            raise ValueError(
                f"Provedor de SSO não suportado: {provider}. Suportados: google, github, azure, microsoft"
            )

    async def _verify_google(self, token: str) -> UserClaims:
        """Valida token de ID do Google via endpoint tokeninfo."""
        client = self._get_client()
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        resp = await client.get(url)
        if resp.status_code != 200:
            raise ValueError("Token do Google inválido ou expirado")

        data = resp.json()
        return UserClaims(
            email=data.get("email", ""),
            name=data.get("name", ""),
            avatar_url=data.get("picture"),
            provider="google",
            provider_user_id=data.get("sub", ""),
        )

    async def _verify_github(self, token: str) -> UserClaims:
        """Valida token OAuth do GitHub buscando o perfil do usuário."""
        client = self._get_client()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        resp = await client.get("https://api.github.com/user", headers=headers)
        if resp.status_code != 200:
            raise ValueError("Token do GitHub inválido ou expirado")

        user_data = resp.json()
        email = user_data.get("email")
        if not email:
            emails_resp = await client.get("https://api.github.com/user/emails", headers=headers)
            if emails_resp.status_code == 200:
                emails = emails_resp.json()
                primary = next((e for e in emails if e.get("primary")), None)
                if primary:
                    email = primary.get("email")

        return UserClaims(
            email=email or f"{user_data.get('login')}@github.local",
            name=user_data.get("name") or user_data.get("login", ""),
            avatar_url=user_data.get("avatar_url"),
            provider="github",
            provider_user_id=str(user_data.get("id")),
        )

    async def _verify_microsoft_azure(self, token: str) -> UserClaims:
        """Valida token do Microsoft Graph / Azure Entra ID."""
        client = self._get_client()
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get("https://graph.microsoft.com/v1.0/me", headers=headers)
        if resp.status_code != 200:
            raise ValueError("Token da Microsoft/Azure inválido ou expirado")

        data = resp.json()
        return UserClaims(
            email=data.get("mail") or data.get("userPrincipalName", ""),
            name=data.get("displayName", ""),
            avatar_url=None,
            provider="azure",
            provider_user_id=data.get("id", ""),
        )


class MockSSOAdapter(SSOIdentityPort):
    """Adaptador mock configurável para testes de integração e unitários."""

    def __init__(self, predefined_claims: Optional[Dict[str, UserClaims]] = None):
        self.claims_by_token: Dict[str, UserClaims] = predefined_claims or {}

    def set_mock_claims(self, token: str, claims: UserClaims) -> None:
        self.claims_by_token[token] = claims

    async def verify_token(self, token: str, provider: str) -> UserClaims:
        if token in self.claims_by_token:
            return self.claims_by_token[token]
        # Fallback genérico para tokens de teste
        return UserClaims(
            email=f"{token.lower()}@{provider.lower()}.test",
            name=f"Hero {token.capitalize()}",
            provider=provider.lower(),
            provider_user_id=f"sub_{token}",
            avatar_url=f"https://avatars.test/{token}.png",
        )
