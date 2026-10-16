import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { api } from './api/client';
import { AuthSession, DashboardPayload } from './types';
import { Loader2, PlusCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'dashboard' | 'onboarding'>('dashboard');
  const [guildId, setGuildId] = useState<string | null>(null);
  const [guildsList, setGuildsList] = useState<Array<{ id: string; name: string; level: number }>>([]);
  const [dashboardData, setDashboardData] = useState<DashboardPayload | null>(null);
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Carrega lista de guildas do banco PostgreSQL
  const refreshGuildsList = useCallback(async () => {
    try {
      const list = await api.listGuilds();
      if (Array.isArray(list)) {
        setGuildsList(list);
        return list;
      }
    } catch (e) {
      console.warn('Erro ao listar guildas do backend:', e);
    }
    return [];
  }, []);

  // Inicialização de Sessão e Rota
  useEffect(() => {
    const initApp = async () => {
      // 1. Checa autenticação salva
      const savedAuth = localStorage.getItem('tech_guilds_auth');
      let currentAuth: AuthSession | null = null;
      if (savedAuth) {
        try {
          currentAuth = JSON.parse(savedAuth);
          setAuthSession(currentAuth);
        } catch (e) {
          localStorage.removeItem('tech_guilds_auth');
        }
      }

      // 2. Checa rota e parâmetros de URL
      const path = window.location.pathname;
      const params = new URLSearchParams(window.location.search);
      const urlGuildId = params.get('guild_id');

      if (path.includes('onboarding')) {
        setCurrentView('onboarding');
        setIsLoading(false);
        return;
      }

      // 3. Busca lista real de guildas no PostgreSQL
      const guilds = await refreshGuildsList();

      if (urlGuildId) {
        setGuildId(urlGuildId);
      } else if (currentAuth) {
        // Tenta descobrir a guilda vinculada ao herói autenticado
        try {
          const hero = await api.getHeroByEmail(currentAuth.user.email);
          if (hero) {
            const membership = await api.getHeroGuild(hero.id);
            if (membership && membership.guild_id) {
              setGuildId(membership.guild_id);
              return;
            }
          }
        } catch (e) {
          // Continua
        }

        if (guilds.length > 0) {
          setGuildId(guilds[0].id);
        } else {
          // Nenhuma guilda no banco: encaminha para o Onboarding real
          setCurrentView('onboarding');
        }
      } else {
        // Sem autenticação: vai direto para cadastro de conta real e onboarding
        setCurrentView('onboarding');
      }
      setIsLoading(false);
    };

    initApp();
  }, [refreshGuildsList]);

  // Carrega dados da Guilda Real do PostgreSQL
  const loadData = useCallback(async (targetGuildId: string | null) => {
    if (!targetGuildId) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await api.getDashboardData(targetGuildId);
      setDashboardData(data);
    } catch (err: any) {
      console.error('Falha ao carregar dashboard real:', err);
      setErrorMessage(
        err.message ||
          'Não foi possível carregar os dados desta guilda no PostgreSQL. Verifique se o backend está ativo.'
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (currentView === 'dashboard' && guildId) {
      loadData(guildId);
    }
  }, [currentView, guildId, loadData]);

  const handleNavigate = (view: 'dashboard' | 'onboarding') => {
    setCurrentView(view);
    const newPath = view === 'onboarding' ? '/onboarding' : '/dashboard';
    window.history.pushState({}, '', newPath + (guildId ? `?guild_id=${guildId}` : ''));
  };

  const handleFinishOnboarding = async (createdGuildId?: string) => {
    const list = await refreshGuildsList();
    const target = createdGuildId || (list.length > 0 ? list[0].id : null);
    if (target) {
      setGuildId(target);
    }
    // Atualiza authSession da storage
    const savedAuth = localStorage.getItem('tech_guilds_auth');
    if (savedAuth) {
      try {
        setAuthSession(JSON.parse(savedAuth));
      } catch (e) {}
    }
    handleNavigate('dashboard');
  };

  const handleSelectGuild = (newGuildId: string) => {
    setGuildId(newGuildId);
    window.history.pushState({}, '', `/dashboard?guild_id=${newGuildId}`);
    loadData(newGuildId);
  };

  const handleLogout = () => {
    localStorage.removeItem('tech_guilds_auth');
    setAuthSession(null);
    handleNavigate('onboarding');
  };

  return (
    <div className="min-h-screen bg-retro-dark text-white font-terminal selection:bg-o2-green selection:text-black">
      <Header
        currentView={currentView}
        onNavigate={handleNavigate}
        onRefresh={() => loadData(guildId)}
        authSession={authSession}
        guilds={guildsList}
        activeGuildId={guildId || undefined}
        onSelectGuild={handleSelectGuild}
        onLogout={handleLogout}
      />

      <main className="scanlines">
        {currentView === 'onboarding' ? (
          <OnboardingPage onFinish={handleFinishOnboarding} />
        ) : isLoading ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
            <Loader2 className="w-10 h-10 text-o2-green animate-spin" />
            <span className="font-pixel text-xs text-o2-green tracking-widest animate-pulse">
              CONECTANDO AO BANCO POSTGRESQL & NATS JETSTREAM...
            </span>
          </div>
        ) : dashboardData ? (
          <DashboardPage data={dashboardData} onRefresh={() => loadData(guildId)} />
        ) : (
          <div className="max-w-md mx-auto my-20 p-8 pixel-box bg-retro-card text-center space-y-4">
            <div className="text-4xl">🏰</div>
            <h3 className="font-pixel text-sm text-retro-gold">NENHUM SQUAD ATIVO ENCONTRADO</h3>
            <p className="text-xs text-gray-400 font-mono">
              {errorMessage ||
                'Para acessar o dashboard com dados reais, cadastre seu herói e crie ou ingresse em uma guilda corporativa.'}
            </p>
            <button
              onClick={() => handleNavigate('onboarding')}
              className="pixel-btn pixel-btn-primary px-4 py-2 text-xs inline-flex items-center gap-2 mt-2"
            >
              <PlusCircle className="w-4 h-4" />
              <span>CRIAR HERÓI & FUNDAR SQUAD</span>
            </button>
          </div>
        )}
      </main>
    </div>
  );
};
