import React from 'react';
import { Shield, Sparkles, RefreshCw, LogOut, ChevronDown } from 'lucide-react';
import { AuthSession } from '../types';

interface HeaderProps {
  currentView: 'dashboard' | 'onboarding';
  onNavigate: (view: 'dashboard' | 'onboarding') => void;
  onRefresh?: () => void;
  authSession?: AuthSession | null;
  guilds?: Array<{ id: string; name: string; level: number }>;
  activeGuildId?: string;
  onSelectGuild?: (guildId: string) => void;
  onLogout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  onNavigate,
  onRefresh,
  authSession,
  guilds = [],
  activeGuildId,
  onSelectGuild,
  onLogout,
}) => {
  return (
    <header className="border-b-2 border-retro-border bg-retro-card px-6 py-3.5 shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Brand */}
        <div
          onClick={() => onNavigate('dashboard')}
          className="flex items-center space-x-3 cursor-pointer group"
        >
          <div className="w-9 h-9 border-2 border-o2-green bg-[#0b0e14] flex items-center justify-center text-xl shadow-md group-hover:scale-105 transition-transform">
            ⚔️
          </div>
          <div>
            <h1 className="font-pixel text-xs sm:text-sm text-o2-green tracking-wider flex items-center gap-2">
              TECH GUILDS{' '}
              <span className="text-[9px] text-retro-cyan bg-retro-border px-1.5 py-0.5 rounded">
                HEXAGONAL MONOREPO
              </span>
            </h1>
            <p className="text-[11px] text-gray-400 font-mono">GAMIFIED SQUAD ARCHITECTURE & COMBAT</p>
          </div>
        </div>

        {/* Guild Switcher & User Profile */}
        <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
          {/* Seletor de Guildas Ativas no PostgreSQL */}
          {guilds.length > 0 && currentView === 'dashboard' && (
            <div className="flex items-center gap-1.5 bg-[#0e141f] border border-retro-border rounded px-2.5 py-1">
              <span className="text-[11px] text-gray-400">Squad:</span>
              <select
                value={activeGuildId || ''}
                onChange={(e) => onSelectGuild && onSelectGuild(e.target.value)}
                className="bg-transparent text-o2-green font-pixel text-[11px] outline-none cursor-pointer"
              >
                {guilds.map((g) => (
                  <option key={g.id} value={g.id} className="bg-retro-dark text-white">
                    {g.name} (LVL {g.level})
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3 h-3 text-gray-400 pointer-events-none" />
            </div>
          )}

          {/* Usuário Autenticado via SSO */}
          {authSession ? (
            <div className="flex items-center gap-2 bg-[#0e141f] border border-o2-green/60 rounded px-2.5 py-1">
              <img
                src={
                  authSession.user.avatar_url ||
                  `https://api.dicebear.com/7.x/pixel-art/svg?seed=${authSession.user.name}`
                }
                alt={authSession.user.name}
                className="w-5 h-5 rounded border border-o2-green"
              />
              <span className="text-white font-bold truncate max-w-[140px]">
                {authSession.user.name}
              </span>
              <span className="text-[9px] px-1 py-0.2 rounded bg-retro-border text-retro-cyan uppercase">
                {authSession.user.provider}
              </span>
              {onLogout && (
                <button
                  onClick={onLogout}
                  title="Encerrar Sessão SSO"
                  className="text-gray-400 hover:text-retro-red ml-1 transition"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ) : (
            <button
              onClick={() => onNavigate('onboarding')}
              className="text-xs text-retro-cyan hover:underline flex items-center gap-1"
            >
              <span>🔑</span> Fazer Login SSO
            </button>
          )}

          {/* Action Buttons */}
          {currentView === 'dashboard' ? (
            <>
              <button
                onClick={() => onNavigate('onboarding')}
                className="pixel-btn pixel-btn-primary px-3 py-1.5 flex items-center gap-1.5 text-xs shadow-md"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>FORJAR NOVO HERÓI / SQUAD</span>
              </button>

              {onRefresh && (
                <button
                  onClick={onRefresh}
                  className="pixel-btn pixel-btn-dark px-3 py-1.5 flex items-center gap-1.5 text-xs text-gray-200"
                  title="Sincronizar com PostgreSQL & NATS"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>SYNC</span>
                </button>
              )}
            </>
          ) : (
            <button
              onClick={() => onNavigate('dashboard')}
              className="pixel-btn pixel-btn-dark px-3 py-1.5 flex items-center gap-1.5 text-xs text-o2-green"
            >
              <Shield className="w-3.5 h-3.5" />
              <span>VOLTAR AO DASHBOARD</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
