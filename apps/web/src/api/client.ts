import { AuthSession, DashboardPayload } from '../types';

export interface RegisterHeroParams {
  name: string;
  email: string;
  hero_class: string;
  avatar_url?: string;
  sso_token?: string;
  sso_provider?: string;
  tenant_id?: string;
  organization_name?: string;
}

export interface CreateGuildParams {
  name: string;
  description?: string;
  creator_hero_id?: string;
  tenant_id?: string;
}

function getTenantHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = { ...extraHeaders };
  try {
    const raw = localStorage.getItem('tech_guilds_auth');
    if (raw) {
      const session: AuthSession = JSON.parse(raw);
      const tenantId = session.tenant_id || session.user?.tenant_id;
      if (tenantId) {
        headers['X-Tenant-ID'] = tenantId;
      }
      if (session.access_token && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
      }
    }
  } catch {
    // ignore storage errors
  }
  return headers;
}

export const api = {
  // 1. Autenticação & SSO (Microsserviço Auth)
  async registerAccount(params: {
    name: string;
    email: string;
    password?: string;
    avatar_url?: string;
    organization_name?: string;
    tenant_id?: string;
  }): Promise<AuthSession> {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao registrar conta real.');
    }
    return res.json();
  },

  async loginDirect(params: {
    email: string;
    password?: string;
    tenant_id?: string;
  }): Promise<AuthSession> {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao realizar login com e-mail corporativo.');
    }
    return res.json();
  },

  async loginSSO(provider: string, token: string, tenantId?: string): Promise<AuthSession> {
    const res = await fetch('/api/auth/sso/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, token, tenant_id: tenantId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao autenticar com provedor SSO.');
    }
    return res.json();
  },

  async validateToken(token: string) {
    const res = await fetch('/api/auth/validate', {
      method: 'POST',
      headers: getTenantHeaders({
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      }),
      body: JSON.stringify({ token }),
    });
    if (!res.ok) return { is_valid: false };
    return res.json();
  },

  // 2. Cadastro & Onboarding (Microsserviço Registration)
  async registerHero(params: RegisterHeroParams) {
    const res = await fetch('/api/registration/heroes', {
      method: 'POST',
      headers: getTenantHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao registrar herói.');
    }
    return res.json();
  },

  async getHeroByEmail(email: string) {
    const res = await fetch(`/api/registration/heroes/by-email/${encodeURIComponent(email)}`, {
      headers: getTenantHeaders(),
    });
    if (!res.ok) return null;
    return res.json();
  },

  async getHeroById(heroId: string) {
    const res = await fetch(`/api/registration/heroes/${heroId}`, {
      headers: getTenantHeaders(),
    });
    if (!res.ok) return null;
    return res.json();
  },

  // 3. Guildas & Esquadrões (Microsserviço Guilds)
  async listGuilds() {
    const res = await fetch('/api/guilds/', {
      headers: getTenantHeaders(),
    });
    if (!res.ok) return [];
    return res.json();
  },

  async getGuild(guildId: string) {
    const res = await fetch(`/api/guilds/${guildId}`, {
      headers: getTenantHeaders(),
    });
    if (!res.ok) return null;
    return res.json();
  },

  async getHeroGuild(heroId: string) {
    const res = await fetch(`/api/guilds/heroes/${heroId}`, {
      headers: getTenantHeaders(),
    });
    if (!res.ok) return null;
    return res.json();
  },

  async createGuild(params: CreateGuildParams) {
    const res = await fetch('/api/guilds/', {
      method: 'POST',
      headers: getTenantHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao criar esquadrão.');
    }
    return res.json();
  },

  async addMember(guildId: string, heroId: string) {
    const res = await fetch(`/api/guilds/${guildId}/members`, {
      method: 'POST',
      headers: getTenantHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ hero_id: heroId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao associar herói à guilda.');
    }
    return res.json();
  },

  // 4. Gamificação & Combate (Microsserviço Gamification)
  async castSkill(params: {
    hero_id: string;
    skill_id: string;
    target_boss_id?: string;
    target_guild_id?: string;
  }) {
    const res = await fetch('/api/gamification/skills/cast', {
      method: 'POST',
      headers: getTenantHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao conjurar habilidade.');
    }
    return res.json();
  },

  async completeQuest(params: {
    external_id: string;
    guild_id: string;
    title: string;
    assignee_hero_id?: string;
  }) {
    const res = await fetch('/api/gamification/webhooks/card-event', {
      method: 'POST',
      headers: getTenantHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        external_id: params.external_id,
        external_source: 'WEB',
        title: params.title,
        guild_id: params.guild_id,
        new_status: 'DONE',
        assignee_hero_id: params.assignee_hero_id,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao concluir quest.');
    }
    return res.json();
  },

  // 5. Dashboard Data Agregado do Gateway
  async getDashboardData(guildId: string): Promise<DashboardPayload> {
    const res = await fetch(`/dashboard/data/${guildId}`, {
      headers: getTenantHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Falha ao carregar dashboard para guilda: ${guildId}`);
    }
    return res.json();
  },
};
