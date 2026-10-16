import React from 'react';
import { Shield, Sparkles, RefreshCw } from 'lucide-react';

interface HeaderProps {
  currentView: 'dashboard' | 'onboarding';
  onNavigate: (view: 'dashboard' | 'onboarding') => void;
  onRefresh?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ currentView, onNavigate, onRefresh }) => {
  return (
    <header className="border-b-2 border-retro-border bg-retro-card px-6 py-4 shadow-md sticky top-0 z-50">
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
              TECH GUILDS <span className="text-[10px] text-retro-cyan bg-retro-border px-1.5 py-0.5 rounded">NX MONOREPO</span>
            </h1>
            <p className="text-xs text-gray-400 font-mono">GAMIFIED SQUAD ARCHITECTURE & COMBAT</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-3 font-mono text-xs">
          {currentView === 'dashboard' ? (
            <>
              <button
                onClick={() => onNavigate('onboarding')}
                className="pixel-btn pixel-btn-primary px-3 py-1.5 flex items-center gap-1.5 text-xs"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>FORJAR NOVO HERÓI</span>
              </button>

              {onRefresh && (
                <button
                  onClick={onRefresh}
                  className="pixel-btn pixel-btn-dark px-3 py-1.5 flex items-center gap-1.5 text-xs text-gray-200"
                  title="Sincronizar com Backend"
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
