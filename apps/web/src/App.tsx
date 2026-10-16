import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { api } from './api/client';
import { DashboardPayload } from './types';
import { Loader2 } from 'lucide-react';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'dashboard' | 'onboarding'>('dashboard');
  const [guildId, setGuildId] = useState<string>('demo');
  const [dashboardData, setDashboardData] = useState<DashboardPayload | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Lê rota e query params iniciais
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const gId = params.get('guild_id');
    if (gId) setGuildId(gId);

    const path = window.location.pathname;
    if (path.includes('onboarding')) {
      setCurrentView('onboarding');
    }
  }, []);

  const loadData = useCallback(async (targetGuildId: string = guildId) => {
    setIsLoading(true);
    try {
      const data = await api.getDashboardData(targetGuildId);
      setDashboardData(data);
    } catch (err) {
      console.warn('Usando payload de demonstração local:', err);
      // Fallback para demo
      const demoData = await api.getDashboardData('demo').catch(() => null);
      if (demoData) setDashboardData(demoData);
    } finally {
      setIsLoading(false);
    }
  }, [guildId]);

  useEffect(() => {
    if (currentView === 'dashboard') {
      loadData(guildId);
    }
  }, [currentView, guildId, loadData]);

  const handleNavigate = (view: 'dashboard' | 'onboarding') => {
    setCurrentView(view);
    const newPath = view === 'onboarding' ? '/onboarding' : '/dashboard';
    window.history.pushState({}, '', newPath + (guildId && guildId !== 'demo' ? `?guild_id=${guildId}` : ''));
  };

  const handleFinishOnboarding = (createdGuildId?: string) => {
    if (createdGuildId) {
      setGuildId(createdGuildId);
    }
    handleNavigate('dashboard');
  };

  return (
    <div className="min-h-screen bg-retro-dark text-white font-terminal selection:bg-o2-green selection:text-black">
      <Header
        currentView={currentView}
        onNavigate={handleNavigate}
        onRefresh={() => loadData(guildId)}
      />

      <main className="scanlines">
        {currentView === 'onboarding' ? (
          <OnboardingPage onFinish={handleFinishOnboarding} />
        ) : isLoading ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
            <Loader2 className="w-10 h-10 text-o2-green animate-spin" />
            <span className="font-pixel text-xs text-o2-green tracking-widest animate-pulse">
              CARREGANDO SQUAD RPG DASHBOARD...
            </span>
          </div>
        ) : dashboardData ? (
          <DashboardPage data={dashboardData} onRefresh={() => loadData(guildId)} />
        ) : (
          <div className="text-center py-20 font-pixel text-xs text-retro-red">
            Erro ao carregar dados do esquadrão.
          </div>
        )}
      </main>
    </div>
  );
};
