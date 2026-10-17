export type HeroClass = 'WARRIOR' | 'MAGE' | 'PALADIN' | 'RANGER' | 'TACTICIAN' | 'NOVICE';

export interface HeroStats {
  strength: number;
  intelligence: number;
  constitution: number;
  perception: number;
}

export interface Hero {
  id: string;
  name: string;
  email: string;
  hero_class: string;
  hero_class_label: string;
  level: number;
  experience: number;
  experience_to_next_level: number;
  health: number;
  max_health: number;
  health_percent: number;
  mana: number;
  max_mana: number;
  gold: number;
  stats: HeroStats;
  equipped_items: Record<string, string>;
  status: string;
  avatar_url: string;
}

export interface Guild {
  id: string;
  name: string;
  description: string;
  level: number;
  experience: number;
  experience_to_next_level: number;
  experience_percent: number;
  treasury_gold: number;
  active_members_count: number;
  active_adventure_title?: string;
  active_boss_count: number;
  tenant_id?: string;
}

export interface MiniBoss {
  id: string;
  external_id: string;
  title: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  max_health: number;
  current_health: number;
  health_percent: number;
  is_defeated: boolean;
  bounty_hero_xp: number;
  bounty_guild_xp: number;
  bounty_gold: number;
  avatar: string;
}

export interface Quest {
  id: string;
  external_id: string;
  external_source: string;
  title: string;
  status: 'TODO' | 'IN_PROGRESS' | 'IN_REVIEW' | 'DONE';
  difficulty: 'EASY' | 'MEDIUM' | 'HARD' | 'EPIC';
  quest_type: string;
  assignee_name?: string;
  is_pair_programming: boolean;
  rewards: {
    hero_xp: number;
    hero_gold: number;
    guild_xp: number;
    guild_gold: number;
  };
}

export interface ShopItem {
  id: string;
  name: string;
  type: string;
  rarity: string;
  price: number;
  icon: string;
  description: string;
}

export interface CombatLogEntry {
  timestamp: string;
  message: string;
  type: 'combat' | 'skill' | 'buff' | 'loot';
}

export interface DashboardPayload {
  guild: Guild;
  heroes: Hero[];
  active_boss?: MiniBoss;
  active_adventure?: {
    id: string;
    external_id: string;
    title: string;
    total_quests: number;
    completed_quests: number;
    progress_percentage: number;
    is_completed: boolean;
    reward_guild_xp: number;
    reward_guild_gold: number;
  };
  quests: Quest[];
  shop_items: ShopItem[];
  combat_log: CombatLogEntry[];
}

export interface UserClaims {
  email: string;
  name: string;
  provider: string;
  provider_user_id: string;
  avatar_url?: string;
  tenant_id?: string;
  organization_name?: string;
}

export interface AuthSession {
  access_token: string;
  token_type: string;
  expires_in: number;
  session_id: string;
  tenant_id?: string;
  user: UserClaims;
}
