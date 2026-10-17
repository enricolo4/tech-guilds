import re

DEFAULT_TENANT_ID = "default"

PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "yahoo.com",
    "yahoo.com.br",
    "icloud.com",
    "me.com",
    "proton.me",
    "protonmail.com",
    "uol.com.br",
    "bol.com.br",
    "terra.com.br",
}


def slugify_tenant(value: str) -> str:
    """Normaliza um identificador ou nome de organização para um slug de tenant seguro."""
    cleaned = value.strip().lower()
    if not cleaned:
        return DEFAULT_TENANT_ID
    # Mantém letras, números, pontos e hífens (útil para domínios como o2inc.com ou slugs como acme-corp)
    slug = re.sub(r"[^a-z0-9.\-]+", "-", cleaned)
    slug = re.sub(r"-+", "-", slug).strip("-.")
    return slug or DEFAULT_TENANT_ID


def resolve_tenant_id(
    email: str | None = None,
    explicit_tenant_id: str | None = None,
    organization_name: str | None = None,
) -> str:
    """Resolve o tenant_id de forma determinística:
    1. Se explicit_tenant_id for fornecido (e diferente de 'default' vazio), usa ele normalizado.
    2. Se organization_name for fornecido, gera o slug da organização.
    3. Se um e-mail corporativo (não público) for fornecido, usa o domínio do e-mail como tenant_id.
    4. Caso contrário, retorna 'default'.
    """
    if explicit_tenant_id and explicit_tenant_id.strip():
        return slugify_tenant(explicit_tenant_id)

    if organization_name and organization_name.strip():
        return slugify_tenant(organization_name)

    if email and "@" in email:
        domain = email.split("@", 1)[1].strip().lower()
        if domain and domain not in PUBLIC_EMAIL_DOMAINS:
            return slugify_tenant(domain)

    return DEFAULT_TENANT_ID


def resolve_organization_name(tenant_id: str, explicit_name: str | None = None) -> str:
    """Retorna um nome amigável para a Organização / Tenant."""
    if explicit_name and explicit_name.strip():
        return explicit_name.strip()
    if not tenant_id or tenant_id == DEFAULT_TENANT_ID:
        return "Workspace Padrão"
    # Remove extensões comuns de domínio para exibição amigável
    base = re.sub(r"\.(com|io|org|net|br|dev|app|tech|co)(\.[a-z]{2,3})?$", "", tenant_id, flags=re.IGNORECASE)
    return base.replace("-", " ").replace(".", " ").title()
