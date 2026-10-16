import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { HeroClass, AuthSession } from '../types';
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Dices,
  CheckCircle,
  ShieldAlert,
  Lock,
  Check,
  Building2,
  Users,
  UserPlus,
  LogIn,
  LogOut,
  KeyRound,
} from 'lucide-react';

interface ClassOption {
  id: HeroClass;
  title: string;
  role: string;
  icon: string;
  description: string;
  starterWeapon: string;
  skill: string;
  stats: { strength: number; intelligence: number; constitution: number; perception: number };
}

const AVAILABLE_CLASSES: ClassOption[] = [
  {
    id: 'WARRIOR',
    title: 'WARRIOR',
    role: 'Backend Dev',
    icon: '⚔️',
    description: 'Especialista em integridade ACID, concorrência massiva e resiliência de dados.',
    starterWeapon: 'Blade of Postgres Indices',
    skill: 'Refatoração Brutal',
    stats: { strength: 24, intelligence: 12, constitution: 20, perception: 10 },
  },
  {
    id: 'MAGE',
    title: 'MAGE',
    role: 'Frontend Dev',
    icon: '🪄',
    description: 'Mestre da reatividade de estado, animações pixel-perfect e Tailwind CSS.',
    starterWeapon: 'Staff of Tailwind CSS',
    skill: 'Script de Automação',
    stats: { strength: 11, intelligence: 25, constitution: 13, perception: 15 },
  },
  {
    id: 'PALADIN',
    title: 'PALADIN',
    role: 'DevOps / SRE',
    icon: '🛡️',
    description: 'Guardião do 99.99% Uptime, clusters Kubernetes e esteiras de CI/CD blindadas.',
    starterWeapon: 'Hammer of Kubernetes',
    skill: 'Escudo de CI/CD',
    stats: { strength: 18, intelligence: 14, constitution: 24, perception: 12 },
  },
  {
    id: 'RANGER',
    title: 'RANGER',
    role: 'QA / Tester',
    icon: '🏹',
    description: 'Caçador de bugs ocultos em produção e mestre de testes E2E com Cypress/Playwright.',
    starterWeapon: 'Bow of Cypress End-to-End',
    skill: 'Golpe de Edge Case',
    stats: { strength: 12, intelligence: 16, constitution: 14, perception: 24 },
  },
  {
    id: 'TACTICIAN',
    title: 'TACTICIAN',
    role: 'Tech Lead',
    icon: '📜',
    description: 'Estrategista que desbloqueia a squad, guia a arquitetura e orquestra a sprint.',
    starterWeapon: 'Tome of Clean Architecture',
    skill: 'Rally de Sprint',
    stats: { strength: 16, intelligence: 20, constitution: 16, perception: 18 },
  },
  {
    id: 'NOVICE',
    title: 'NOVICE',
    role: 'Iniciante / Trainee',
    icon: '🐣',
    description: 'O herói aprendiz pronto para absorver conhecimento e trilhar qualquer caminho.',
    starterWeapon: 'Teclado Mecânico Básico',
    skill: 'Vontade de Aprender',
    stats: { strength: 12, intelligence: 12, constitution: 12, perception: 12 },
  },
];

interface OnboardingPageProps {
  onFinish: (guildId?: string) => void;
}

export const OnboardingPage: React.FC<OnboardingPageProps> = ({ onFinish }) => {
  const [currentStep, setCurrentStep] = useState(1);

  // Autenticação & Conta Real
  const [authMode, setAuthMode] = useState<'register' | 'login' | 'sso'>('register');
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [ssoProvider, setSsoProvider] = useState<'google' | 'github' | 'azure' | 'direct'>('direct');
  const [customToken, setCustomToken] = useState('');
  const [showTokenInput, setShowTokenInput] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Herói
  const [heroName, setHeroName] = useState('');
  const [heroEmail, setHeroEmail] = useState('');
  const [avatarSeed, setAvatarSeed] = useState('HeroDev');
  const [selectedClass, setSelectedClass] = useState<HeroClass>('WARRIOR');
  const [existingHeroId, setExistingHeroId] = useState<string | null>(null);

  // Esquadrão / Guilda
  const [guildMode, setGuildMode] = useState<'create' | 'join' | 'solo'>('create');
  const [newGuildName, setNewGuildName] = useState('');
  const [newGuildDescription, setNewGuildDescription] = useState('');
  const [selectedGuildId, setSelectedGuildId] = useState('');
  const [existingGuilds, setExistingGuilds] = useState<
    Array<{ id: string; name: string; level: number; member_ids: string[] }>
  >([]);

  // Submissão & Feedback
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [registeredHeroId, setRegisteredHeroId] = useState<string | null>(null);
  const [finalGuildId, setFinalGuildId] = useState<string | null>(null);

  const avatarUrl = `https://api.dicebear.com/7.x/pixel-art/svg?seed=${encodeURIComponent(avatarSeed)}`;
  const currentClassDetails =
    AVAILABLE_CLASSES.find((c) => c.id === selectedClass) || AVAILABLE_CLASSES[0];

  // Carrega guildas ativas do PostgreSQL
  const fetchGuilds = () => {
    api
      .listGuilds()
      .then((guilds) => {
        if (Array.isArray(guilds)) {
          setExistingGuilds(guilds);
          if (guilds.length > 0 && !selectedGuildId) {
            setSelectedGuildId(guilds[0].id);
          }
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetchGuilds();

    // Recupera sessão salva, se houver
    const savedAuth = localStorage.getItem('tech_guilds_auth');
    if (savedAuth) {
      try {
        const parsed: AuthSession = JSON.parse(savedAuth);
        setAuthSession(parsed);
        setHeroName(parsed.user.name);
        setHeroEmail(parsed.user.email);
        setSsoProvider((parsed.user.provider as any) || 'direct');
        if (parsed.user.name) setAvatarSeed(parsed.user.name);

        // Checa se já tem herói cadastrado
        api
          .getHeroByEmail(parsed.user.email)
          .then((hero) => {
            if (hero) {
              setExistingHeroId(hero.id);
              if (hero.hero_class) setSelectedClass(hero.hero_class as HeroClass);
            }
          })
          .catch(() => {});
      } catch (e) {
        localStorage.removeItem('tech_guilds_auth');
      }
    }
  }, []);

  const handleNameChange = (name: string) => {
    setHeroName(name);
    if (name.trim()) {
      setAvatarSeed(name.trim());
    }
  };

  const randomizeAvatar = () => {
    const seeds = ['Gandalf', 'Conan', 'Legolas', 'Uther', 'Trinity', 'Neo', 'Ada', 'Turing'];
    const picked =
      seeds[Math.floor(Math.random() * seeds.length)] + '_' + Math.floor(Math.random() * 999);
    setAvatarSeed(picked);
  };

  const handleLogout = () => {
    localStorage.removeItem('tech_guilds_auth');
    setAuthSession(null);
    setHeroName('');
    setHeroEmail('');
    setPassword('');
    setExistingHeroId(null);
    setErrorMessage('');
  };

  // 1. Criação de Conta Real no Microsserviço de Auth
  const handleRegisterAccount = async () => {
    if (!heroName.trim() || heroName.trim().length < 2) {
      setErrorMessage('Por favor, informe seu nome ou apelido (mínimo 2 caracteres).');
      return;
    }
    if (!heroEmail.trim() || !heroEmail.includes('@')) {
      setErrorMessage('Por favor, informe um e-mail corporativo válido.');
      return;
    }

    setIsLoggingIn(true);
    setErrorMessage('');
    try {
      const session = await api.registerAccount({
        name: heroName.trim(),
        email: heroEmail.trim().toLowerCase(),
        password: password.trim() || undefined,
        avatar_url: avatarUrl,
      });

      setAuthSession(session);
      setSsoProvider('direct');
      localStorage.setItem('tech_guilds_auth', JSON.stringify(session));

      // Verifica se o herói já foi cadastrado
      const existing = await api.getHeroByEmail(session.user.email).catch(() => null);
      if (existing) {
        setExistingHeroId(existing.id);
        if (existing.hero_class) setSelectedClass(existing.hero_class as HeroClass);
        const membership = await api.getHeroGuild(existing.id).catch(() => null);
        if (membership && membership.guild_id) {
          setSelectedGuildId(membership.guild_id);
        }
      }

      // Avança diretamente para Escolha de Classe!
      setCurrentStep(2);
    } catch (err: any) {
      setErrorMessage(err.message || 'Falha ao criar conta real.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  // 2. Login Direto com Conta Existente
  const handleLoginDirect = async () => {
    if (!heroEmail.trim() || !heroEmail.includes('@')) {
      setErrorMessage('Por favor, informe o e-mail da sua conta.');
      return;
    }

    setIsLoggingIn(true);
    setErrorMessage('');
    try {
      const session = await api.loginDirect({
        email: heroEmail.trim().toLowerCase(),
        password: password.trim() || undefined,
      });

      setAuthSession(session);
      setHeroName(session.user.name);
      setHeroEmail(session.user.email);
      setAvatarSeed(session.user.name || 'HeroDev');
      setSsoProvider('direct');
      localStorage.setItem('tech_guilds_auth', JSON.stringify(session));

      const existing = await api.getHeroByEmail(session.user.email).catch(() => null);
      if (existing) {
        setExistingHeroId(existing.id);
        if (existing.hero_class) setSelectedClass(existing.hero_class as HeroClass);
        const membership = await api.getHeroGuild(existing.id).catch(() => null);
        if (membership && membership.guild_id) {
          setSelectedGuildId(membership.guild_id);
        }
      }

      setCurrentStep(2);
    } catch (err: any) {
      setErrorMessage(err.message || 'Falha ao entrar com a conta informada.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  // 3. Login via Provedor SSO
  const executeSSOLogin = async (
    provider: 'google' | 'github' | 'azure',
    explicitToken?: string
  ) => {
    setIsLoggingIn(true);
    setErrorMessage('');
    try {
      const token =
        explicitToken ||
        customToken.trim() ||
        `dev-${provider}-${avatarSeed.toLowerCase().replace(/[^a-z0-9]/g, '') || 'developer'}`;

      const session = await api.loginSSO(provider, token);
      setAuthSession(session);
      setSsoProvider(provider);
      setHeroName(session.user.name);
      setHeroEmail(session.user.email);
      setAvatarSeed(session.user.name || 'HeroDev');

      // Persiste sessão
      localStorage.setItem('tech_guilds_auth', JSON.stringify(session));

      // Verifica se o herói já foi cadastrado no banco PostgreSQL
      const existing = await api.getHeroByEmail(session.user.email).catch(() => null);
      if (existing) {
        setExistingHeroId(existing.id);
        if (existing.hero_class) setSelectedClass(existing.hero_class as HeroClass);

        const membership = await api.getHeroGuild(existing.id).catch(() => null);
        if (membership && membership.guild_id) {
          setSelectedGuildId(membership.guild_id);
        }
      }

      setCurrentStep(2);
    } catch (err: any) {
      setErrorMessage(err.message || 'Falha ao autenticar via SSO.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleNextStep = (targetStep: number) => {
    setErrorMessage('');
    if (targetStep === 2) {
      if (!authSession) {
        setErrorMessage(
          'Por favor, crie sua conta real ou faça login para avançar.'
        );
        return;
      }
      if (!heroName.trim() || heroName.trim().length < 2) {
        setErrorMessage('Nome do herói deve conter pelo menos 2 caracteres.');
        return;
      }
    }
    if (targetStep === 4) {
      if (guildMode === 'create' && !newGuildName.trim()) {
        setErrorMessage('Por favor, informe o nome do seu novo esquadrão.');
        return;
      }
      if (guildMode === 'join' && !selectedGuildId) {
        setErrorMessage('Por favor, selecione um esquadrão existente da lista.');
        return;
      }
    }
    setCurrentStep(targetStep);
  };

  // Submissão Final do Fluxo Real
  const handleSubmit = async () => {
    setIsSubmitting(true);
    setErrorMessage('');
    try {
      // 1. Cadastra o herói no microsserviço de Registration
      const token = authSession ? authSession.access_token : undefined;
      const provider = authSession?.user?.provider || ssoProvider;
      const regRes = await api.registerHero({
        name: heroName.trim(),
        email: heroEmail.trim().toLowerCase(),
        hero_class: selectedClass,
        avatar_url: avatarUrl,
        sso_token: token,
        sso_provider: provider,
      });

      const hero = regRes.hero || regRes;
      const heroId = hero.id;
      setRegisteredHeroId(heroId);

      let targetGuildId = '';

      // 2. Trata criação ou associação de guilda no microsserviço de Guilds
      if (guildMode === 'create' && newGuildName.trim()) {
        const createdGuild = await api.createGuild({
          name: newGuildName.trim(),
          description: newGuildDescription.trim() || 'Squad de Desenvolvimento Ágil',
          creator_hero_id: heroId,
        });
        targetGuildId = createdGuild.id;

        // Associa o herói como membro fundador da guilda
        await api.addMember(targetGuildId, heroId);
      } else if (guildMode === 'join' && selectedGuildId) {
        await api.addMember(selectedGuildId, heroId);
        targetGuildId = selectedGuildId;
      }

      setFinalGuildId(targetGuildId || null);
      setCurrentStep(5);
    } catch (err: any) {
      setErrorMessage(err.message || 'Falha ao processar o registro do herói no backend.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Stepper Retrô */}
      <div className="mb-8">
        <div className="flex justify-between items-center relative">
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-retro-border -z-0"></div>
          <div
            className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-o2-green transition-all duration-300 -z-0"
            style={{ width: `${(currentStep - 1) * 25}%` }}
          ></div>

          {[
            { step: 1, label: 'SSO & Identidade' },
            { step: 2, label: 'Classe RPG' },
            { step: 3, label: 'Esquadrão' },
            { step: 4, label: 'Prontidão' },
          ].map((item) => (
            <div key={item.step} className="relative z-10 flex flex-col items-center">
              <div
                className={`w-9 h-9 rounded border-2 flex items-center justify-center font-pixel text-xs transition-colors ${
                  currentStep >= item.step
                    ? 'border-o2-green bg-retro-card text-o2-green font-bold shadow-md shadow-o2-green/20'
                    : 'border-retro-border bg-retro-dark text-gray-500'
                }`}
              >
                {item.step}
              </div>
              <span
                className={`text-[11px] mt-1.5 font-mono uppercase tracking-wider ${
                  currentStep >= item.step ? 'text-o2-green font-bold' : 'text-gray-500'
                }`}
              >
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ERROS */}
      {errorMessage && (
        <div className="p-3 mb-6 bg-red-950/80 border-2 border-retro-red text-red-200 text-xs font-mono rounded flex items-center gap-2 shadow-lg animate-pulse">
          <ShieldAlert className="w-4 h-4 flex-shrink-0 text-retro-red" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* PASSO 1: AUTENTICAÇÃO REAL & IDENTIDADE */}
      {currentStep === 1 && (
        <div className="pixel-box p-6 md:p-8 bg-retro-card">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6 border-b border-retro-border pb-3">
            <div>
              <h2 className="font-pixel text-sm md:text-base text-o2-green flex items-center gap-2">
                <span>🔐</span> IDENTIDADE & CONTA REAL
              </h2>
              <p className="text-xs text-gray-400 font-mono mt-1">
                Crie sua conta real ou faça login corporativo para acessar seu esquadrão e registrar seu herói.
              </p>
            </div>
            {authSession && (
              <span className="inline-flex items-center gap-1.5 text-xs font-mono bg-green-950 text-green-300 border border-green-700 px-2.5 py-1 rounded">
                <Check className="w-3.5 h-3.5" /> Sessão Ativa
              </span>
            )}
          </div>

          {/* SESSÃO ATIVA DETECTADA */}
          {authSession ? (
            <div className="p-5 bg-[#122318] border-2 border-o2-green rounded mb-6 space-y-4 shadow-xl">
              <div className="flex flex-col sm:flex-row items-center gap-4">
                <img
                  src={avatarUrl}
                  alt="Avatar"
                  className="w-16 h-16 border-2 border-o2-green p-1 bg-retro-card rounded shadow-md"
                />
                <div className="flex-1 text-center sm:text-left">
                  <div className="text-[11px] font-pixel text-o2-green uppercase tracking-wider">
                    Herói Autenticado
                  </div>
                  <h3 className="font-pixel text-base text-white">{authSession.user.name}</h3>
                  <p className="text-xs font-mono text-gray-300">{authSession.user.email}</p>
                  <div className="flex items-center gap-2 mt-1.5 justify-center sm:justify-start">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/40 border border-retro-border text-gray-300">
                      Provedor: <strong className="text-o2-green uppercase">{authSession.user.provider}</strong>
                    </span>
                    <span
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/40 border border-retro-border text-gray-300"
                      title={authSession.session_id}
                    >
                      Sessão: <strong className="text-retro-cyan font-mono">{authSession.session_id ? `${authSession.session_id.slice(0, 8)}...` : 'Ativa'}</strong>
                    </span>
                    {existingHeroId && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950/60 border border-retro-cyan text-cyan-200" title={existingHeroId}>
                        Herói Vinculado: <strong>{existingHeroId.slice(0, 8)}...</strong>
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-o2-green/30">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="pixel-btn pixel-btn-dark py-2 px-3 text-xs flex items-center gap-1.5 text-gray-300"
                >
                  <LogOut className="w-3.5 h-3.5" /> Trocar de Conta / Sair
                </button>
                <button
                  type="button"
                  onClick={() => handleNextStep(2)}
                  className="pixel-btn pixel-btn-primary py-2 px-5 text-xs flex items-center gap-2 shadow-lg"
                >
                  <span>ESCOLHER CLASSE RPG</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* TABS DE SELEÇÃO: CRIAR CONTA REAL / LOGIN / SSO */}
              <div className="flex border-b-2 border-retro-border mb-6 gap-2">
                <button
                  type="button"
                  onClick={() => setAuthMode('register')}
                  className={`py-2.5 px-4 font-pixel text-xs flex items-center gap-2 border-b-2 transition -mb-[2px] ${
                    authMode === 'register'
                      ? 'border-o2-green text-o2-green bg-[#17261b] font-bold'
                      : 'border-transparent text-gray-400 hover:text-white'
                  }`}
                >
                  <UserPlus className="w-4 h-4" />
                  <span>CRIAR CONTA REAL</span>
                </button>

                <button
                  type="button"
                  onClick={() => setAuthMode('login')}
                  className={`py-2.5 px-4 font-pixel text-xs flex items-center gap-2 border-b-2 transition -mb-[2px] ${
                    authMode === 'login'
                      ? 'border-o2-green text-o2-green bg-[#17261b] font-bold'
                      : 'border-transparent text-gray-400 hover:text-white'
                  }`}
                >
                  <LogIn className="w-4 h-4" />
                  <span>JÁ TENHO CONTA (ENTRAR)</span>
                </button>

                <button
                  type="button"
                  onClick={() => setAuthMode('sso')}
                  className={`py-2.5 px-4 font-pixel text-xs flex items-center gap-2 border-b-2 transition -mb-[2px] ${
                    authMode === 'sso'
                      ? 'border-o2-green text-o2-green bg-[#17261b] font-bold'
                      : 'border-transparent text-gray-400 hover:text-white'
                  }`}
                >
                  <Lock className="w-4 h-4" />
                  <span>SSO CORPORATIVO</span>
                </button>
              </div>

              {/* ABA 1: CRIAR CONTA REAL */}
              {authMode === 'register' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Visual retrô */}
                    <div className="flex flex-col items-center justify-center p-4 bg-[#0e141f] border-2 border-retro-border rounded text-center">
                      <span className="text-[10px] font-pixel text-gray-400 mb-2">SPRITE 16-BIT RETRÔ</span>
                      <img
                        src={avatarUrl}
                        alt="Avatar Preview"
                        className="w-28 h-28 border-2 border-o2-green p-1 bg-retro-card rounded mb-3 shadow-lg"
                      />
                      <span className="text-xs font-mono text-o2-green truncate max-w-full font-bold">
                        {heroName || 'Novo Herói'}
                      </span>
                      <button
                        type="button"
                        onClick={randomizeAvatar}
                        className="mt-2 text-xs text-retro-cyan hover:underline flex items-center gap-1 font-mono"
                      >
                        <Dices className="w-3.5 h-3.5" /> Sortear Visual
                      </button>
                    </div>

                    {/* Campos de formulário real */}
                    <div className="md:col-span-2 space-y-4">
                      <div>
                        <label className="block text-xs font-pixel text-gray-300 mb-1">
                          NOME DO HERÓI / DESENVOLVEDOR *
                        </label>
                        <input
                          type="text"
                          value={heroName}
                          onChange={(e) => handleNameChange(e.target.value)}
                          placeholder="Ex: Enrico Dev, Alex Backend"
                          className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-pixel text-gray-300 mb-1">
                          E-MAIL CORPORATIVO *
                        </label>
                        <input
                          type="email"
                          value={heroEmail}
                          onChange={(e) => setHeroEmail(e.target.value)}
                          placeholder="Ex: seu-nome@empresa.com"
                          className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-pixel text-gray-300 mb-1">
                          SENHA DE ACESSO (OPCIONAL)
                        </label>
                        <div className="relative">
                          <input
                            type={showPassword ? 'text' : 'password'}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Defina uma senha ou deixe em branco para token direto"
                            className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded pr-16"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-mono text-retro-cyan hover:underline px-1 py-0.5"
                          >
                            {showPassword ? 'Ocultar' : 'Exibir'}
                          </button>
                        </div>
                      </div>

                      <div className="pt-2 text-[11px] text-gray-400 font-mono">
                        🛡️ Sua conta e credenciais são autenticadas com criptografia e segurança de ponta a ponta.
                      </div>
                    </div>
                  </div>

                  <div className="mt-8 flex justify-end">
                    <button
                      type="button"
                      onClick={handleRegisterAccount}
                      disabled={isLoggingIn}
                      className="pixel-btn pixel-btn-primary px-6 py-3 text-xs flex items-center gap-2 shadow-xl"
                    >
                      <Sparkles className="w-4 h-4" />
                      <span>{isLoggingIn ? 'CRIANDO SUA CONTA...' : 'CRIAR MINHA CONTA REAL & AVANÇAR'}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}

              {/* ABA 2: JÁ TENHO CONTA (LOGIN DIRETO) */}
              {authMode === 'login' && (
                <div className="space-y-4 max-w-lg mx-auto p-6 bg-[#0e141f] border-2 border-retro-border rounded">
                  <h3 className="font-pixel text-xs text-o2-green uppercase tracking-wider mb-2">
                    Entrar com E-mail Corporativo
                  </h3>

                  <div>
                    <label className="block text-xs font-pixel text-gray-300 mb-1">
                      E-MAIL CORPORATIVO *
                    </label>
                    <input
                      type="email"
                      value={heroEmail}
                      onChange={(e) => setHeroEmail(e.target.value)}
                      placeholder="Ex: alex@empresa.com"
                      className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-pixel text-gray-300 mb-1">
                      SENHA DE ACESSO
                    </label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Sua senha (se cadastrada)"
                      className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                    />
                  </div>

                  <div className="pt-4 flex justify-between items-center">
                    <button
                      type="button"
                      onClick={() => setAuthMode('register')}
                      className="text-xs text-retro-cyan hover:underline font-mono"
                    >
                      Não tem conta? Crie aqui
                    </button>
                    <button
                      type="button"
                      onClick={handleLoginDirect}
                      disabled={isLoggingIn}
                      className="pixel-btn pixel-btn-primary px-5 py-2.5 text-xs flex items-center gap-2"
                    >
                      <LogIn className="w-3.5 h-3.5" />
                      <span>{isLoggingIn ? 'ENTRANDO...' : 'ENTRAR & AVANÇAR'}</span>
                    </button>
                  </div>
                </div>
              )}

              {/* ABA 3: SSO CORPORATIVO */}
              {authMode === 'sso' && (
                <div className="p-4 bg-[#0e141f] border-2 border-retro-border rounded space-y-4">
                  <span className="text-xs font-pixel text-gray-300 block mb-2 uppercase tracking-wider">
                    Selecione o Provedor OAuth Corporativo:
                  </span>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        setSsoProvider('github');
                        executeSSOLogin('github');
                      }}
                      disabled={isLoggingIn}
                      className="pixel-btn pixel-btn-dark py-3 px-3 text-xs flex items-center justify-center gap-2 hover:border-o2-green"
                    >
                      <span>🐙</span> GitHub Enterprise
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setSsoProvider('google');
                        executeSSOLogin('google');
                      }}
                      disabled={isLoggingIn}
                      className="pixel-btn pixel-btn-dark py-3 px-3 text-xs flex items-center justify-center gap-2 hover:border-o2-green"
                    >
                      <span>🌐</span> Google Workspace
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setSsoProvider('azure');
                        executeSSOLogin('azure');
                      }}
                      disabled={isLoggingIn}
                      className="pixel-btn pixel-btn-dark py-3 px-3 text-xs flex items-center justify-center gap-2 hover:border-o2-green"
                    >
                      <span>🔷</span> Microsoft Azure AD
                    </button>
                  </div>

                  <div className="border-t border-retro-border/60 pt-3 flex flex-wrap items-center justify-between text-xs font-mono text-gray-400 gap-2">
                    <button
                      type="button"
                      onClick={() => setShowTokenInput(!showTokenInput)}
                      className="text-retro-cyan hover:underline flex items-center gap-1"
                    >
                      <KeyRound className="w-3.5 h-3.5" />
                      {showTokenInput ? 'Ocultar entrada de token' : 'Inserir Personal Access Token / OAuth Token'}
                    </button>
                  </div>

                  {showTokenInput && (
                    <div className="mt-2 flex gap-2">
                      <input
                        type="text"
                        value={customToken}
                        onChange={(e) => setCustomToken(e.target.value)}
                        placeholder={`Cole seu token ${ssoProvider}...`}
                        className="flex-1 bg-[#0b0e14] border border-retro-border focus:border-o2-green px-3 py-1.5 text-xs text-white font-mono rounded"
                      />
                      <button
                        type="button"
                        onClick={() => executeSSOLogin(ssoProvider as any, customToken)}
                        className="pixel-btn pixel-btn-primary px-3 py-1 text-xs"
                      >
                        AUTENTICAR
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* PASSO 2: CLASSE RPG */}
      {currentStep === 2 && (
        <div className="pixel-box p-6 md:p-8 bg-retro-card">
          <h2 className="font-pixel text-sm md:text-base text-o2-green mb-2 flex items-center gap-2">
            <span>🪄</span> ESPECIALIZAÇÃO DE ENGENHARIA & CLASSE
          </h2>
          <p className="text-sm text-gray-400 mb-6 font-mono">
            Sua classe define suas habilidades de combate em bugs e seus atributos de RPG.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mb-6">
            {AVAILABLE_CLASSES.map((c) => (
              <div
                key={c.id}
                onClick={() => setSelectedClass(c.id)}
                className={`p-4 border-2 rounded cursor-pointer transition-all ${
                  selectedClass === c.id
                    ? 'border-o2-green bg-[#17261b] shadow-lg shadow-o2-green/20'
                    : 'border-retro-border bg-[#0e141f] hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-3xl">{c.icon}</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-pixel ${
                      selectedClass === c.id
                        ? 'bg-o2-green text-black font-bold'
                        : 'bg-retro-border text-gray-400'
                    }`}
                  >
                    {c.role}
                  </span>
                </div>
                <h3 className="font-pixel text-xs text-white mb-1">{c.title}</h3>
                <p className="text-xs text-gray-400 font-mono mb-3 leading-tight">{c.description}</p>
                <div className="border-t border-retro-border pt-2 text-xs font-mono space-y-1">
                  <div className="text-amber-400 flex items-center gap-1">
                    <span>🗡️</span> <span>{c.starterWeapon}</span>
                  </div>
                  <div className="text-retro-cyan flex items-center gap-1">
                    <span>⚡</span> <span>{c.skill}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Ficha da Classe */}
          <div className="p-4 bg-[#0e141f] border-2 border-o2-green rounded mb-6">
            <div className="flex items-center justify-between mb-3 border-b border-retro-border pb-2">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{currentClassDetails.icon}</span>
                <div>
                  <span className="font-pixel text-xs text-o2-green">{currentClassDetails.title}</span>
                  <span className="text-xs text-gray-400 font-mono ml-2">
                    ({currentClassDetails.role})
                  </span>
                </div>
              </div>
              <span className="font-pixel text-xs text-retro-gold">NÍVEL 1</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-red-400 font-bold">FORÇA (STR)</span>
                  <span>{currentClassDetails.stats.strength}</span>
                </div>
                <div className="w-full bg-[#1b2333] h-2 rounded overflow-hidden">
                  <div
                    className="bg-red-500 h-2 transition-all duration-300"
                    style={{ width: `${(currentClassDetails.stats.strength / 30) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-retro-cyan font-bold">INTELIGÊNCIA (INT)</span>
                  <span>{currentClassDetails.stats.intelligence}</span>
                </div>
                <div className="w-full bg-[#1b2333] h-2 rounded overflow-hidden">
                  <div
                    className="bg-cyan-400 h-2 transition-all duration-300"
                    style={{ width: `${(currentClassDetails.stats.intelligence / 30) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-green-400 font-bold">CONSTITUIÇÃO (CON)</span>
                  <span>{currentClassDetails.stats.constitution}</span>
                </div>
                <div className="w-full bg-[#1b2333] h-2 rounded overflow-hidden">
                  <div
                    className="bg-green-500 h-2 transition-all duration-300"
                    style={{ width: `${(currentClassDetails.stats.constitution / 30) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-purple-400 font-bold">PERCEPÇÃO (PER)</span>
                  <span>{currentClassDetails.stats.perception}</span>
                </div>
                <div className="w-full bg-[#1b2333] h-2 rounded overflow-hidden">
                  <div
                    className="bg-purple-400 h-2 transition-all duration-300"
                    style={{ width: `${(currentClassDetails.stats.perception / 30) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              className="pixel-btn pixel-btn-dark px-4 py-2 text-xs flex items-center gap-2"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> VOLTAR
            </button>
            <button
              type="button"
              onClick={() => handleNextStep(3)}
              className="pixel-btn pixel-btn-primary px-5 py-2.5 text-xs flex items-center gap-2"
            >
              <span>VINCULAR A UM ESQUADRÃO</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* PASSO 3: ESQUADRÃO / GUILDA */}
      {currentStep === 3 && (
        <div className="pixel-box p-6 md:p-8 bg-retro-card">
          <h2 className="font-pixel text-sm md:text-base text-o2-green mb-2 flex items-center gap-2">
            <span>🏰</span> ESQUADRÃO (GUILDA) & COOPERAÇÃO
          </h2>
          <p className="text-sm text-gray-400 mb-6 font-mono">
            Vincule seu herói a um Squad existente ou funde uma nova guilda para seu time.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div
              onClick={() => setGuildMode('create')}
              className={`p-4 border-2 rounded cursor-pointer transition ${
                guildMode === 'create'
                  ? 'border-o2-green bg-[#17261b] shadow-md shadow-o2-green/10'
                  : 'border-retro-border bg-[#0e141f]'
              }`}
            >
              <Building2 className="w-6 h-6 text-o2-green mb-2" />
              <span className="font-pixel text-xs text-white block mb-1">CRIAR NOVO SQUAD</span>
              <p className="text-xs text-gray-400 font-mono">
                Fundar um novo time e se tornar o criador/líder.
              </p>
            </div>

            <div
              onClick={() => {
                setGuildMode('join');
                fetchGuilds();
              }}
              className={`p-4 border-2 rounded cursor-pointer transition ${
                guildMode === 'join'
                  ? 'border-o2-green bg-[#17261b] shadow-md shadow-o2-green/10'
                  : 'border-retro-border bg-[#0e141f]'
              }`}
            >
              <Users className="w-6 h-6 text-retro-cyan mb-2" />
              <span className="font-pixel text-xs text-white block mb-1">ENTRAR EM SQUAD</span>
              <p className="text-xs text-gray-400 font-mono">
                Unir forças com um time já existente.
              </p>
            </div>

            <div
              onClick={() => setGuildMode('solo')}
              className={`p-4 border-2 rounded cursor-pointer transition ${
                guildMode === 'solo'
                  ? 'border-o2-green bg-[#17261b] shadow-md shadow-o2-green/10'
                  : 'border-retro-border bg-[#0e141f]'
              }`}
            >
              <span className="text-2xl block mb-2">🐺</span>
              <span className="font-pixel text-xs text-white block mb-1">LOBO SOLITÁRIO</span>
              <p className="text-xs text-gray-400 font-mono">
                Iniciar sem esquadrão e vincular-se posteriormente.
              </p>
            </div>
          </div>

          {guildMode === 'create' && (
            <div className="space-y-4 p-4 bg-[#0e141f] border border-retro-border rounded mb-6">
              <div>
                <label className="block text-xs font-pixel text-gray-300 mb-1">
                  NOME DO ESQUADRÃO / GUILDA *
                </label>
                <input
                  type="text"
                  value={newGuildName}
                  onChange={(e) => setNewGuildName(e.target.value)}
                  placeholder="Ex: Core Backend Vanguard, Frontend Ninjas"
                  className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                />
              </div>
              <div>
                <label className="block text-xs font-pixel text-gray-300 mb-1">
                  MISSÃO OU DESCRIÇÃO DO TIME
                </label>
                <input
                  type="text"
                  value={newGuildDescription}
                  onChange={(e) => setNewGuildDescription(e.target.value)}
                  placeholder="Ex: Squad responsável por microsserviços de alta disponibilidade"
                  className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                />
              </div>
            </div>
          )}

          {guildMode === 'join' && (
            <div className="space-y-4 p-4 bg-[#0e141f] border border-retro-border rounded mb-6">
              <label className="block text-xs font-pixel text-gray-300 mb-1">
                SELECIONE O ESQUADRÃO DISPONÍVEL *
              </label>
              {existingGuilds.length > 0 ? (
                <select
                  value={selectedGuildId}
                  onChange={(e) => setSelectedGuildId(e.target.value)}
                  className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                >
                  {existingGuilds.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name} (Nível {g.level} • {g.member_ids?.length || 0} heróis)
                    </option>
                  ))}
                </select>
              ) : (
                <div className="p-3 bg-amber-950/40 border border-retro-gold text-amber-300 text-xs font-mono rounded">
                  ⚠️ Nenhum esquadrão ativo encontrado no momento. Recomendamos selecionar{' '}
                  <strong>CRIAR NOVO SQUAD</strong> para fundar seu primeiro time!
                </div>
              )}
            </div>
          )}

          {guildMode === 'solo' && (
            <div className="p-4 bg-[#0e141f] border border-retro-border rounded mb-6 text-xs text-gray-400 font-mono">
              💡 Você iniciará como um herói autônomo. Poderá se vincular a uma guilda ou criar um
              esquadrão a qualquer momento através do painel.
            </div>
          )}

          <div className="flex justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              className="pixel-btn pixel-btn-dark px-4 py-2 text-xs flex items-center gap-2"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> VOLTAR
            </button>
            <button
              type="button"
              onClick={() => handleNextStep(4)}
              className="pixel-btn pixel-btn-primary px-5 py-2.5 text-xs flex items-center gap-2"
            >
              <span>REVISAR FICHA & FORJAR</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* PASSO 4: CONFIRMAÇÃO & FORJA */}
      {currentStep === 4 && (
        <div className="pixel-box p-6 md:p-8 bg-retro-card">
          <h2 className="font-pixel text-sm md:text-base text-o2-green mb-2 flex items-center gap-2">
            <span>📜</span> CONFIRMAÇÃO & FORJA DO HERÓI
          </h2>
          <p className="text-sm text-gray-400 mb-6 font-mono">
            Ao confirmar, seu Herói será registrado oficialmente e suas fichas de RPG serão sincronizadas em todo o sistema.
          </p>

          <div className="p-6 bg-[#0e141f] border-2 border-o2-green rounded mb-6 shadow-xl">
            <div className="flex flex-col sm:flex-row items-center gap-6 border-b border-retro-border pb-6">
              <img
                src={avatarUrl}
                alt="Avatar Final"
                className="w-24 h-24 border-2 border-o2-green p-1 bg-retro-card rounded shadow-md"
              />
              <div className="text-center sm:text-left space-y-1">
                <h3 className="font-pixel text-base text-white">{heroName}</h3>
                <p className="text-sm text-o2-green font-mono">{heroEmail}</p>
                <div className="flex flex-wrap gap-2 pt-1 justify-center sm:justify-start">
                  <span className="text-[10px] px-2 py-0.5 rounded font-pixel bg-retro-border text-retro-cyan">
                    {currentClassDetails.title}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded font-pixel bg-retro-border text-retro-gold">
                    {guildMode === 'create'
                      ? `Novo Squad: ${newGuildName}`
                      : guildMode === 'join'
                      ? 'Ingressando em Squad Existente'
                      : 'Lobo Solitário'}
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 text-xs font-mono">
              <div>
                <span className="text-gray-400 block">Arma Inicial:</span>
                <span className="text-amber-400 font-bold">{currentClassDetails.starterWeapon}</span>
              </div>
              <div>
                <span className="text-gray-400 block">Habilidade Chave:</span>
                <span className="text-retro-cyan font-bold">{currentClassDetails.skill}</span>
              </div>
              <div>
                <span className="text-gray-400 block">Provedor SSO:</span>
                <span className="text-white uppercase font-bold">{ssoProvider}</span>
              </div>
              <div>
                <span className="text-gray-400 block">Protocolo:</span>
                <span className="text-o2-green font-bold">Convocação Oficial do Herói</span>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <button
              type="button"
              onClick={() => setCurrentStep(3)}
              disabled={isSubmitting}
              className="pixel-btn pixel-btn-dark px-4 py-2 text-xs"
            >
              ⬅️ VOLTAR
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="pixel-btn pixel-btn-primary px-6 py-3 text-xs flex items-center gap-2 shadow-2xl"
            >
              <Sparkles className="w-4 h-4" />
              <span>
                {isSubmitting
                  ? 'FORJANDO HERÓI & SINCRONIZANDO...'
                  : 'FORJAR HERÓI & ENTRAR NA BATALHA'}
              </span>
            </button>
          </div>
        </div>
      )}

      {/* PASSO 5: SUCESSO */}
      {currentStep === 5 && (
        <div className="pixel-box pixel-box-green p-8 text-center space-y-6 bg-retro-card">
          <div className="text-6xl animate-bounce">🎉</div>
          <h2 className="font-pixel text-base md:text-lg text-o2-green">
            HERÓI FORJADO COM SUCESSO!
          </h2>
          <p className="text-sm text-gray-300 font-mono max-w-md mx-auto">
            O herói <strong className="text-white">{heroName}</strong> foi registrado com sucesso e sua jornada no esquadrão foi iniciada!
          </p>

          <div className="p-4 bg-[#0e141f] border border-retro-border rounded max-w-sm mx-auto text-xs font-mono text-left space-y-1.5">
            <div>
              <span className="text-gray-400">ID do Herói:</span>{' '}
              <span className="text-retro-cyan truncate block">{registeredHeroId}</span>
            </div>
            <div>
              <span className="text-gray-400">Classe Atribuída:</span>{' '}
              <span className="text-retro-gold font-bold">{selectedClass}</span>
            </div>
            {finalGuildId && (
              <div>
                <span className="text-gray-400">ID do Esquadrão:</span>{' '}
                <span className="text-o2-green truncate block">{finalGuildId}</span>
              </div>
            )}
            <div className="pt-1">
              <span className="text-o2-green font-bold flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> HERÓI PRONTO PARA A BATALHA
              </span>
            </div>
          </div>

          <div className="pt-4">
            <button
              type="button"
              onClick={() => onFinish(finalGuildId || undefined)}
              className="pixel-btn pixel-btn-primary px-6 py-3 text-xs sm:text-sm inline-flex items-center gap-2 shadow-2xl"
            >
              <span>🏰 ENTRAR NO SQUAD DASHBOARD REAL</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
