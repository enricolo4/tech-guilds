import { DashboardPayload } from '../types';

export interface RegisterHeroParams {
  name: string;
  email: string;
  hero_class: string;
  avatar_url?: string;
  sso_token?: string;
  sso_provider?: string;
}

export interface CreateGuildParams {
  name: string;
  description?: string;
  creator_hero_id?: string;
}

export const api = {
  // 1. Cadastro de Herói (Microsserviço Registration)
  async registerHero(params: RegisterHeroParams) {
    const res = await fetch('/api/registration/heroes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao registrar herói.');
    }
    return res.json();
  },

  // 2. Guildas (Microsserviço Guilds)
  async listGuilds() {
    const res = await fetch('/api/guilds/');
    if (!res.ok) return [];
    return res.json();
  },

  async createGuild(params: CreateGuildParams) {
    const res = await fetch('/api/guilds/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hero_id: heroId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao associar herói à guilda.');
    }
    return res.json();
  },

  // 3. Dashboard Data
  async getDashboardData(guildId: string = 'demo'): Promise<DashboardPayload> {
    const res = await fetch(`/dashboard/data/${guildId}`);
    if (!res.ok) {
      throw new Error(`Falha ao carregar dashboard para guilda: ${guildId}`);
    }
    return res.json();
  },
};
