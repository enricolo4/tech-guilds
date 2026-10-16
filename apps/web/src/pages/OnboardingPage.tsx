import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { HeroClass } from '../types';
import { Sparkles, ArrowRight, ArrowLeft, Dices, CheckCircle, ShieldAlert } from 'lucide-react';

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
    description: 'Especialista em integridade ACID, arquiteturas resilientes e concorrência massiva.',
    starterWeapon: 'Blade of Postgres Indices',
    skill: 'Refatoração Brutal',
    stats: { strength: 24, intelligence: 12, constitution: 20, perception: 10 },
  },
  {
    id: 'MAGE',
    title: 'MAGE',
    role: 'Frontend Dev',
    icon: '🪄',
    description: 'Mestre da experiência do usuário, animações reativas fluidas e Tailwind CSS.',
    starterWeapon: 'Staff of Tailwind CSS',
    skill: 'Script de Automação',
    stats: { strength: 11, intelligence: 25, constitution: 13, perception: 15 },
  },
  {
    id: 'PALADIN',
    title: 'PALADIN',
    role: 'DevOps / SRE',
    icon: '🛡️',
    description: 'Guardião de alta disponibilidade (99.99% Uptime) e esteiras de CI/CD blindadas.',
    starterWeapon: 'Hammer of Kubernetes',
    skill: 'Escudo de CI/CD',
    stats: { strength: 18, intelligence: 14, constitution: 24, perception: 12 },
  },
  {
    id: 'RANGER',
    title: 'RANGER',
    role: 'QA / Tester',
    icon: '🏹',
    description: 'Atirador de precisão caçador de bugs ocultos e mestre de testes E2E.',
    starterWeapon: 'Bow of Cypress End-to-End',
    skill: 'Golpe de Edge Case',
    stats: { strength: 12, intelligence: 16, constitution: 14, perception: 24 },
  },
  {
    id: 'TACTICIAN',
    title: 'TACTICIAN',
    role: 'Tech Lead',
    icon: '📜',
    description: 'Estrategista que desbloqueia squads, guia a arquitetura e orquestra a sprint.',
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
  const [heroName, setHeroName] = useState('');
  const [heroEmail, setHeroEmail] = useState('');
  const [avatarSeed, setAvatarSeed] = useState('Adventurer');
  const [selectedClass, setSelectedClass] = useState<HeroClass>('WARRIOR');
  const [guildMode, setGuildMode] = useState<'create' | 'join' | 'solo'>('create');
  const [newGuildName, setNewGuildName] = useState('');
  const [newGuildDescription, setNewGuildDescription] = useState('');
  const [selectedGuildId, setSelectedGuildId] = useState('');
  const [existingGuilds, setExistingGuilds] = useState<Array<{ id: string; name: string; level: number; member_ids: string[] }>>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [registeredHeroId, setRegisteredHeroId] = useState<string | null>(null);

  const avatarUrl = `https://api.dicebear.com/7.x/pixel-art/svg?seed=${encodeURIComponent(avatarSeed)}`;
  const currentClassDetails = AVAILABLE_CLASSES.find((c) => c.id === selectedClass) || AVAILABLE_CLASSES[0];

  useEffect(() => {
    api.listGuilds().then((guilds) => {
      if (Array.isArray(guilds)) setExistingGuilds(guilds);
    }).catch(() => {});
  }, []);

  const handleNameChange = (name: string) => {
    setHeroName(name);
    if (name.trim()) {
      setAvatarSeed(name.trim());
    }
  };

  const randomizeAvatar = () => {
    const seeds = ['Gandalf', 'Conan', 'Legolas', 'Uther', 'Trinity', 'Neo', 'Ada', 'Turing'];
    const picked = seeds[Math.floor(Math.random() * seeds.length)] + '_' + Math.floor(Math.random() * 999);
    setAvatarSeed(picked);
  };

  const fillSSO = (provider: 'google' | 'github' | 'azure') => {
    const mockSSO = {
      google: { name: 'Alex Google Dev', email: 'alex@company.com' },
      github: { name: 'DevOctocat', email: 'octocat@github-enterprise.corp' },
      azure: { name: 'Morgan Azure Cloud', email: 'morgan@enterprise.onmicrosoft.com' },
    };
    const user = mockSSO[provider];
    handleNameChange(user.name);
    setHeroEmail(user.email);
  };

  const handleNextStep = (targetStep: number) => {
    setErrorMessage('');
    if (targetStep === 2) {
      if (heroName.trim().length < 2 || !heroEmail.includes('@')) {
        setErrorMessage('Por favor, informe seu nome e um e-mail corporativo válido.');
        return;
      }
    }
    if (targetStep === 4 && guildMode === 'create' && !newGuildName.trim()) {
      setErrorMessage('Por favor, forneça o nome do seu novo esquadrão.');
      return;
    }
    setCurrentStep(targetStep);
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setErrorMessage('');
    try {
      // 1. Cadastro no microsserviço de Registration (dispara evento NATS)
      const hero = await api.registerHero({
        name: heroName.trim(),
        email: heroEmail.trim().toLowerCase(),
        hero_class: selectedClass,
        avatar_url: avatarUrl,
      });

      setRegisteredHeroId(hero.id);
      let targetGuildId = '';

      // 2. Trata associação de guilda
      if (guildMode === 'create' && newGuildName.trim()) {
        const guild = await api.createGuild({
          name: newGuildName.trim(),
          description: newGuildDescription.trim() || 'Squad de Desenvolvimento',
          creator_hero_id: hero.id,
        });
        targetGuildId = guild.id;
      } else if (guildMode === 'join' && selectedGuildId) {
        await api.addMember(selectedGuildId, hero.id);
        targetGuildId = selectedGuildId;
      }

      // 3. Sucesso!
      setCurrentStep(5);
      if (targetGuildId) {
        setSelectedGuildId(targetGuildId);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Falha ao forjar herói.');
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
            style={{ width: `${(currentStep - 1) * 33.3}%` }}
          ></div>

          {[
            { step: 1, label: 'Identidade' },
            { step: 2, label: 'Classe RPG' },
            { step: 3, label: 'Esquadrão' },
            { step: 4, label: 'Prontidão' },
          ].map((item) => (
            <div key={item.step} className="relative z-10 flex flex-col items-center">
              <div
                className={`w-9 h-9 rounded border-2 flex items-center justify-center font-pixel text-xs transition-colors ${
                  currentStep >= item.step
                    ? 'border-o2-green bg-retro-card text-o2-green font-bold'
                    : 'border-retro-border bg-retro-dark text-gray-500'
                }`}
              >
                {item.step}
              </div>
              <span
                className={`text-xs mt-1 font-mono uppercase tracking-wider ${
                  currentStep >= item.step ? 'text-o2-green' : 'text-gray-500'
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
        <div className="p-3 mb-6 bg-red-950 border-2 border-retro-red text-red-200 text-xs font-mono rounded flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* PASSO 1: IDENTIDADE */}
      {currentStep === 1 && (
        <div className="pixel-box p-6 md:p-8">
          <h2 className="font-pixel text-sm md:text-base text-o2-green mb-2 flex items-center gap-2">
            <span>👤</span> IDENTIFICAÇÃO DO DESENVOLVEDOR
          </h2>
          <p className="text-sm text-gray-400 mb-6 font-mono">
            Todo herói precisa de um codinome e de um canal corporativo para receber ordens de missão.
          </p>

          {/* Quick SSO */}
          <div className="mb-6 p-4 bg-[#0e141f] border border-retro-border rounded">
            <span className="text-xs font-mono text-gray-400 block mb-2 uppercase">Login Rápido via SSO Corporativo:</span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => fillSSO('google')}
                className="pixel-btn pixel-btn-dark py-2 px-3 text-xs flex items-center justify-center gap-2"
              >
                <span>🌐</span> Google Workspace
              </button>
              <button
                type="button"
                onClick={() => fillSSO('github')}
                className="pixel-btn pixel-btn-dark py-2 px-3 text-xs flex items-center justify-center gap-2"
              >
                <span>🐙</span> GitHub Enterprise
              </button>
              <button
                type="button"
                onClick={() => fillSSO('azure')}
                className="pixel-btn pixel-btn-dark py-2 px-3 text-xs flex items-center justify-center gap-2"
              >
                <span>🔷</span> Azure Active Directory
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex flex-col items-center justify-center p-4 bg-[#0e141f] border-2 border-retro-border rounded text-center">
              <span className="text-[10px] font-pixel text-gray-400 mb-2">SPRITE 16-BIT</span>
              <img
                src={avatarUrl}
                alt="Avatar Preview"
                className="w-28 h-28 border-2 border-o2-green p-1 bg-retro-card rounded mb-3 shadow-lg"
              />
              <span className="text-xs font-mono text-o2-green truncate max-w-full">
                {heroName || 'Herói Anônimo'}
              </span>
              <button
                type="button"
                onClick={randomizeAvatar}
                className="mt-2 text-xs text-retro-cyan hover:underline flex items-center gap-1"
              >
                <Dices className="w-3.5 h-3.5" /> Sortear Visual
              </button>
            </div>

            <div className="md:col-span-2 space-y-4">
              <div>
                <label className="block text-xs font-pixel text-gray-300 mb-1">NOME DO HERÓI / DEVELOPER *</label>
                <input
                  type="text"
                  value={heroName}
                  onChange={(e) => handleNameChange(e.target.value)}
                  placeholder="Ex: Gandalf Dev, Alice Frontend"
                  className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                />
              </div>

              <div>
                <label className="block text-xs font-pixel text-gray-300 mb-1">E-MAIL CORPORATIVO *</label>
                <input
                  type="email"
                  value={heroEmail}
                  onChange={(e) => setHeroEmail(e.target.value)}
                  placeholder="Ex: seu.nome@empresa.com"
                  className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                />
              </div>

              <div className="pt-2">
                <span className="text-xs text-gray-500 font-mono">
                  * O cadastro emitirá o evento <code>tech_guilds.hero.registered</code> no barramento NATS JetStream.
                </span>
              </div>
            </div>
          </div>

          <div className="mt-8 flex justify-end">
            <button
              type="button"
              onClick={() => handleNextStep(2)}
              className="pixel-btn pixel-btn-primary px-4 py-2 text-xs flex items-center gap-2"
            >
              <span>ESCOLHER CLASSE</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* PASSO 2: CLASSE RPG */}
      {currentStep === 2 && (
        <div className="pixel-box p-6 md:p-8">
          <h2 className="font-pixel text-sm md:text-base text-o2-green mb-2 flex items-center gap-2">
            <span>🪄</span> SELEÇÃO DE CLASSE & ATRIBUTOS
          </h2>
          <p className="text-sm text-gray-400 mb-6 font-mono">
            Sua classe define seu papel no esquadrão, suas habilidades ativas e o tipo de tarefas que amplificam seus pontos de XP.
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
                      selectedClass === c.id ? 'bg-o2-green text-black font-bold' : 'bg-retro-border text-gray-400'
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
                  <span className="text-xs text-gray-400 font-mono ml-2">({currentClassDetails.role})</span>
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
              className="pixel-btn pixel-btn-primary px-4 py-2 text-xs flex items-center gap-2"
            >
              <span>CONFIGURAR ESQUADRÃO</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* PASSO 3: ESQUADRÃO / GUILDA */}
      {currentStep === 3 && (
        <div className="pixel-box p-6 md:p-8">
          <h2 className="font-pixel text-sm md:text-base text-o2-green mb-2 flex items-center gap-2">
            <span>🏰</span> ASSOCIAÇÃO A UM ESQUADRÃO (GUILDA)
          </h2>
          <p className="text-sm text-gray-400 mb-6 font-mono">
            Em Tech Guilds, os bônus de XP, recompensas de sprint e combate a Mini-Bosses acontecem cooperativamente em esquadrões.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div
              onClick={() => setGuildMode('create')}
              className={`p-4 border-2 rounded cursor-pointer transition ${
                guildMode === 'create' ? 'border-o2-green bg-[#17261b]' : 'border-retro-border bg-[#0e141f]'
              }`}
            >
              <span className="text-2xl block mb-1">🏗️</span>
              <span className="font-pixel text-xs text-white block mb-1">CRIAR NOVO SQUAD</span>
              <p className="text-xs text-gray-400 font-mono">Fundar uma nova guilda e se tornar o líder fundador.</p>
            </div>

            <div
              onClick={() => setGuildMode('join')}
              className={`p-4 border-2 rounded cursor-pointer transition ${
                guildMode === 'join' ? 'border-o2-green bg-[#17261b]' : 'border-retro-border bg-[#0e141f]'
              }`}
            >
              <span className="text-2xl block mb-1">🤝</span>
              <span className="font-pixel text-xs text-white block mb-1">ENTRAR EM SQUAD</span>
              <p className="text-xs text-gray-400 font-mono">Unir forças com uma equipe já existente no sistema.</p>
            </div>

            <div
              onClick={() => setGuildMode('solo')}
              className={`p-4 border-2 rounded cursor-pointer transition ${
                guildMode === 'solo' ? 'border-o2-green bg-[#17261b]' : 'border-retro-border bg-[#0e141f]'
              }`}
            >
              <span className="text-2xl block mb-1">🐺</span>
              <span className="font-pixel text-xs text-white block mb-1">LOBO SOLITÁRIO</span>
              <p className="text-xs text-gray-400 font-mono">Iniciar sem esquadrão e ingressar em uma guilda depois.</p>
            </div>
          </div>

          {guildMode === 'create' && (
            <div className="space-y-4 p-4 bg-[#0e141f] border border-retro-border rounded mb-6">
              <div>
                <label className="block text-xs font-pixel text-gray-300 mb-1">NOME DO ESQUADRÃO / GUILDA *</label>
                <input
                  type="text"
                  value={newGuildName}
                  onChange={(e) => setNewGuildName(e.target.value)}
                  placeholder="Ex: Core Backend Vanguard, Frontend Ninjas"
                  className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                />
              </div>
              <div>
                <label className="block text-xs font-pixel text-gray-300 mb-1">MISSÃO OU DESCRIÇÃO DO TIME</label>
                <input
                  type="text"
                  value={newGuildDescription}
                  onChange={(e) => setNewGuildDescription(e.target.value)}
                  placeholder="Ex: Responsáveis por microsserviços de alta escala e 99.99% uptime"
                  className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                />
              </div>
            </div>
          )}

          {guildMode === 'join' && (
            <div className="space-y-4 p-4 bg-[#0e141f] border border-retro-border rounded mb-6">
              <label className="block text-xs font-pixel text-gray-300 mb-1">SELECIONE O ESQUADRÃO ALVO *</label>
              {existingGuilds.length > 0 ? (
                <select
                  value={selectedGuildId}
                  onChange={(e) => setSelectedGuildId(e.target.value)}
                  className="w-full bg-[#0b0e14] border-2 border-retro-border focus:border-o2-green px-3 py-2 text-white font-mono text-base outline-none rounded"
                >
                  <option value="">-- Escolha uma guilda ativa --</option>
                  {existingGuilds.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name} (Nível {g.level} • {g.member_ids?.length || 0} membros)
                    </option>
                  ))}
                </select>
              ) : (
                <p className="text-xs text-amber-400 font-mono">
                  Nenhuma guilda encontrada no banco. Recomendamos escolher "CRIAR NOVO SQUAD".
                </p>
              )}
            </div>
          )}

          {guildMode === 'solo' && (
            <div className="p-4 bg-[#0e141f] border border-retro-border rounded mb-6 text-xs text-gray-400 font-mono">
              💡 Você iniciará como um herói autônomo. Poderá ser recrutado ou criar uma guilda a qualquer momento no painel.
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
              className="pixel-btn pixel-btn-primary px-4 py-2 text-xs flex items-center gap-2"
            >
              <span>REVISAR FICHA</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* PASSO 4: CONFIRMAÇÃO & FORJA */}
      {currentStep === 4 && (
        <div className="pixel-box p-6 md:p-8">
          <h2 className="font-pixel text-sm md:text-base text-o2-green mb-2 flex items-center gap-2">
            <span>📜</span> FICHA FINAL DO PERSONAGEM
          </h2>
          <p className="text-sm text-gray-400 mb-6 font-mono">
            Confira seus dados antes de registrar seu herói e disparar a propagação de eventos no NATS JetStream.
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
                      ? `Squad: ${newGuildName}`
                      : guildMode === 'join'
                      ? 'Ingressando em Squad'
                      : 'Solo'}
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
                <span className="text-gray-400 block">Atributos Base:</span>
                <span className="text-white">
                  STR: {currentClassDetails.stats.strength} | INT: {currentClassDetails.stats.intelligence} | CON:{' '}
                  {currentClassDetails.stats.constitution} | PER: {currentClassDetails.stats.perception}
                </span>
              </div>
              <div>
                <span className="text-gray-400 block">Sincronização NATS:</span>
                <span className="text-o2-green font-bold">tech_guilds.hero.registered</span>
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
              className="pixel-btn pixel-btn-primary px-5 py-2.5 text-xs flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isSubmitting ? 'DISPARANDO NATS JETSTREAM...' : 'FORJAR HERÓI & ENTRAR NA BATALHA'}</span>
            </button>
          </div>
        </div>
      )}

      {/* PASSO 5: SUCESSO */}
      {currentStep === 5 && (
        <div className="pixel-box pixel-box-green p-8 text-center space-y-6">
          <div className="text-6xl animate-bounce">🎉</div>
          <h2 className="font-pixel text-base md:text-lg text-o2-green">HERÓI FORJADO COM SUCESSO!</h2>
          <p className="text-sm text-gray-300 font-mono max-w-md mx-auto">
            O herói <strong className="text-white">{heroName}</strong> foi registrado no schema{' '}
            <code className="text-retro-cyan">registration</code> e sincronizado via NATS JetStream para Guilds e Gamification!
          </p>

          <div className="p-4 bg-[#0e141f] border border-retro-border rounded max-w-sm mx-auto text-xs font-mono text-left space-y-1">
            <div>
              <span className="text-gray-400">ID do Herói:</span>{' '}
              <span className="text-retro-cyan truncate">{registeredHeroId}</span>
            </div>
            <div>
              <span className="text-gray-400">Classe Atribuída:</span>{' '}
              <span className="text-retro-gold">{selectedClass}</span>
            </div>
            <div>
              <span className="text-gray-400">Status:</span>{' '}
              <span className="text-o2-green font-bold flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> PRONTO PARA BATALHA
              </span>
            </div>
          </div>

          <div className="pt-4">
            <button
              type="button"
              onClick={() => onFinish(selectedGuildId || undefined)}
              className="pixel-btn pixel-btn-primary px-6 py-3 text-xs sm:text-sm inline-flex items-center gap-2 shadow-2xl"
            >
              <span>🏰 ENTRAR NO SQUAD DASHBOARD</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
