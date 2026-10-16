import httpx
from services.auth.domain.model.user_claims import UserClaims
from services.auth.domain.ports.secondary.sso_port import SSOIdentityPort


class MultiProviderSSOAdapter(SSOIdentityPort):
    """Adaptador secundário para validação de identidade SSO corporativa.
    Suporta Google Workspace, GitHub Enterprise, Microsoft / Azure AD.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None):
        self._client = http_client

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=10.0)

    async def verify_token(self, token: str, provider: str) -> UserClaims:
        provider_normalized = provider.lower().strip()

        # Suporte a tokens de desenvolvimento corporativo / offline demo
        if token.startswith("dev-") or token.startswith("dev_"):
            clean_token = token.replace("dev-", "").replace("dev_", "")
            parts = clean_token.split("-")
            if len(parts) > 1 and parts[0].lower() == provider_normalized:
                username = parts[1]
            else:
                username = parts[0] if parts else "developer"
            name_part = username.capitalize()
            email = f"{username.lower()}@{provider_normalized}-corp.io"
            return UserClaims(
                email=email,
                name=f"{name_part} ({provider_normalized.title()})",
                avatar_url=f"https://api.dicebear.com/7.x/pixel-art/svg?seed={name_part}",
                provider=provider_normalized,
                provider_user_id=f"dev_{provider_normalized}_{clean_token}",
            )

        if provider_normalized == "google":
            return await self._verify_google(token)
        elif provider_normalized == "github":
            return await self._verify_github(token)
        elif provider_normalized in ["azure", "microsoft"]:
            return await self._verify_microsoft_azure(token)
        else:
            raise ValueError(f"Provedor de SSO não suportado: {provider}. Suportados: google, github, azure, microsoft")

    async def _verify_google(self, token: str) -> UserClaims:
        """Valida token de ID do Google via endpoint de tokeninfo do Google."""
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        client = self._get_client()
        should_close = self._client is None
        try:
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
        finally:
            if should_close:
                await client.aclose()

    async def _verify_github(self, token: str) -> UserClaims:
        """Valida token OAuth/Personal Access Token do GitHub buscando o perfil do usuário."""
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        client = self._get_client()
        should_close = self._client is None
        try:
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
        finally:
            if should_close:
                await client.aclose()

    async def _verify_microsoft_azure(self, token: str) -> UserClaims:
        """Valida token de acesso do Microsoft Graph / Azure Entra ID."""
        headers = {"Authorization": f"Bearer {token}"}
        client = self._get_client()
        should_close = self._client is None
        try:
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
        finally:
            if should_close:
                await client.aclose()
