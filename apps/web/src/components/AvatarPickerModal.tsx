import React, { useState } from 'react';
import { Sparkles, Dices, Check, X, Search, Palette } from 'lucide-react';

export interface AvatarPreset {
  id: string;
  name: string;
  title: string;
  category: 'adventurer' | 'personas' | 'bottts' | 'pixel-art';
  url: string;
}

export const AVATAR_PRESETS: AvatarPreset[] = [
  // 1. ILUSTRAÇÕES MODERNAS RPG (Estilo Adventurer - NÃO 8-bit)
  {
    id: 'adv-arthur',
    name: 'Arthur',
    title: 'Cavaleiro Backend & Hexagonal',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Arthur',
  },
  {
    id: 'adv-morgana',
    name: 'Morgana',
    title: 'Feiticeira Frontend & UI',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Morgana',
  },
  {
    id: 'adv-lyra',
    name: 'Lyra',
    title: 'Exploradora Cross-Platform',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Lyra',
  },
  {
    id: 'adv-gideon',
    name: 'Gideon',
    title: 'Guardião de Transações ACID',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Gideon',
  },
  {
    id: 'adv-rowan',
    name: 'Rowan',
    title: 'Navegador Multi-Cloud',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Rowan',
  },
  {
    id: 'adv-diana',
    name: 'Diana',
    title: 'Caçadora de Bugs Críticos',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Diana',
  },
  {
    id: 'adv-finn',
    name: 'Finn',
    title: 'Arquiteto Clean Code',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Finn',
  },
  {
    id: 'adv-sage',
    name: 'Sage',
    title: 'Guru de Engenharia & SRE',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Sage',
  },
  {
    id: 'adv-elena',
    name: 'Elena',
    title: 'Maga de Microsserviços',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Elena',
  },
  {
    id: 'adv-zane',
    name: 'Zane',
    title: 'Ninja de Infraestrutura',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Zane',
  },
  {
    id: 'adv-aria',
    name: 'Aria',
    title: 'Paladina de Testes Automatizados',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Aria',
  },
  {
    id: 'adv-lucas',
    name: 'Lucas',
    title: 'Guerreiro de DevOps & CI/CD',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Lucas',
  },
  {
    id: 'adv-maya',
    name: 'Maya',
    title: 'Alquimista de Dados & Analytics',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Maya',
  },
  {
    id: 'adv-orion',
    name: 'Orion',
    title: 'Estrategista Tech Lead',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Orion',
  },
  {
    id: 'adv-chloe',
    name: 'Chloe',
    title: 'Mestre de Design System & UX',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Chloe',
  },
  {
    id: 'adv-caleb',
    name: 'Caleb',
    title: 'Guardião de Segurança SecOps',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Caleb',
  },
  {
    id: 'adv-nova',
    name: 'Nova',
    title: 'Engenheira de Alta Performance',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Nova',
  },
  {
    id: 'adv-sora',
    name: 'Sora',
    title: 'Arquiteto de Mensageria NATS',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Sora',
  },
  {
    id: 'adv-vesper',
    name: 'Vesper',
    title: 'Hacker de Resiliência',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Vesper',
  },
  {
    id: 'adv-amara',
    name: 'Amara',
    title: 'Campeã de Orquestração Kubernetes',
    category: 'adventurer',
    url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Amara',
  },

  // 2. PERSONAS ILUSTRADAS CLEAN (Estilo Personas)
  {
    id: 'per-felix',
    name: 'Felix',
    title: 'Tech Evangelist',
    category: 'personas',
    url: 'https://api.dicebear.com/7.x/personas/svg?seed=Felix',
  },
  {
    id: 'per-bailey',
    name: 'Bailey',
    title: 'Product Engineer',
    category: 'personas',
    url: 'https://api.dicebear.com/7.x/personas/svg?seed=Bailey',
  },
  {
    id: 'per-alex',
    name: 'Alex',
    title: 'Full Stack Ninja',
    category: 'personas',
    url: 'https://api.dicebear.com/7.x/personas/svg?seed=Alex',
  },
  {
    id: 'per-taylor',
    name: 'Taylor',
    title: 'Cloud Architect',
    category: 'personas',
    url: 'https://api.dicebear.com/7.x/personas/svg?seed=Taylor',
  },
  {
    id: 'per-sam',
    name: 'Sam',
    title: 'QA Automation Lead',
    category: 'personas',
    url: 'https://api.dicebear.com/7.x/personas/svg?seed=Sam',
  },
  {
    id: 'per-jordan',
    name: 'Jordan',
    title: 'Staff Security Engineer',
    category: 'personas',
    url: 'https://api.dicebear.com/7.x/personas/svg?seed=Jordan',
  },

  // 3. MECHS & ROBÔS (Estilo Bottts)
  {
    id: 'bot-sentinel',
    name: 'Sentinel-01',
    title: 'Guardião SRE & Métricas',
    category: 'bottts',
    url: 'https://api.dicebear.com/7.x/bottts/svg?seed=Sentinel',
  },
  {
    id: 'bot-cyber',
    name: 'Cyber-CI',
    title: 'Autômato de Pipelines',
    category: 'bottts',
    url: 'https://api.dicebear.com/7.x/bottts/svg?seed=Cyber',
  },
  {
    id: 'bot-matrix',
    name: 'Matrix-AI',
    title: 'Redes Neurais & Modelos',
    category: 'bottts',
    url: 'https://api.dicebear.com/7.x/bottts/svg?seed=Matrix',
  },
  {
    id: 'bot-optimus',
    name: 'Kube-Prime',
    title: 'Orquestrador de Clusters',
    category: 'bottts',
    url: 'https://api.dicebear.com/7.x/bottts/svg?seed=Optimus',
  },
  {
    id: 'bot-nexus',
    name: 'Nexus-Bus',
    title: 'Protocolo de Alta Escala',
    category: 'bottts',
    url: 'https://api.dicebear.com/7.x/bottts/svg?seed=Nexus',
  },
  {
    id: 'bot-vector',
    name: 'Vector-Core',
    title: 'Engenharia de Embeddings',
    category: 'bottts',
    url: 'https://api.dicebear.com/7.x/bottts/svg?seed=Vector',
  },

  // 4. RETRÔ 16-BIT (Pixel Art - Secundário)
  {
    id: 'pixel-gandalf',
    name: 'Gandalf',
    title: 'Arquimago Retrô',
    category: 'pixel-art',
    url: 'https://api.dicebear.com/7.x/pixel-art/svg?seed=Gandalf',
  },
  {
    id: 'pixel-conan',
    name: 'Conan',
    title: 'Bárbaro Retrô',
    category: 'pixel-art',
    url: 'https://api.dicebear.com/7.x/pixel-art/svg?seed=Conan',
  },
  {
    id: 'pixel-ada',
    name: 'Ada',
    title: 'Pioneira Retrô',
    category: 'pixel-art',
    url: 'https://api.dicebear.com/7.x/pixel-art/svg?seed=Ada',
  },
  {
    id: 'pixel-neo',
    name: 'Neo',
    title: 'O Escolhido Retrô',
    category: 'pixel-art',
    url: 'https://api.dicebear.com/7.x/pixel-art/svg?seed=Neo',
  },
];

interface AvatarPickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentAvatarUrl: string;
  onSelectAvatar: (url: string) => void;
}

export const AvatarPickerModal: React.FC<AvatarPickerModalProps> = ({
  isOpen,
  onClose,
  currentAvatarUrl,
  onSelectAvatar,
}) => {
  // Padrão: Coleção Adventurer (Ilustração moderna, NÃO 8-bit)
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'adventurer' | 'personas' | 'bottts' | 'pixel-art'>('adventurer');
  const [searchQuery, setSearchQuery] = useState('');
  const [customSeed, setCustomSeed] = useState('');
  const [tempSelectedUrl, setTempSelectedUrl] = useState(currentAvatarUrl);

  if (!isOpen) return null;

  const filteredPresets = AVATAR_PRESETS.filter((p) => {
    const matchesCategory = selectedCategory === 'all' || p.category === selectedCategory;
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.title.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleApplyCustomSeed = () => {
    if (!customSeed.trim()) return;
    const style = selectedCategory === 'all' || selectedCategory === 'pixel-art' ? 'adventurer' : selectedCategory;
    const url = `https://api.dicebear.com/7.x/${style}/svg?seed=${encodeURIComponent(customSeed.trim())}`;
    setTempSelectedUrl(url);
  };

  const handleRandomize = () => {
    // Dá prioridade aos aventureiros modernos ilustrados
    const pool = selectedCategory === 'all' ? AVATAR_PRESETS.filter(p => p.category === 'adventurer') : filteredPresets;
    const targetPool = pool.length > 0 ? pool : AVATAR_PRESETS;
    const randomIndex = Math.floor(Math.random() * targetPool.length);
    const picked = targetPool[randomIndex];
    setTempSelectedUrl(picked.url);
  };

  const handleConfirm = () => {
    onSelectAvatar(tempSelectedUrl);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="pixel-box bg-retro-card max-w-3xl w-full max-h-[90vh] flex flex-col border-2 border-o2-green shadow-2xl overflow-hidden">
        {/* Cabeçalho do Modal */}
        <div className="p-4 border-b border-retro-border flex items-center justify-between bg-[#0e141f]">
          <div className="flex items-center gap-2">
            <Palette className="w-5 h-5 text-o2-green" />
            <div>
              <h3 className="font-pixel text-xs sm:text-sm text-white flex items-center gap-2">
                <span>🎨</span> GALERIA DE AVATARES RPG ILUSTRADOS
              </h3>
              <p className="text-[11px] font-mono text-gray-400">
                Selecione seu herói com traço moderno e expressivo. Clique em qualquer card para aplicar.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-white p-1 rounded hover:bg-white/10 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Barra de Filtros & Busca */}
        <div className="p-4 border-b border-retro-border bg-[#0a0d14] space-y-3">
          {/* Abas de Categorias */}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setSelectedCategory('adventurer')}
              className={`px-3 py-1.5 text-xs font-pixel rounded transition flex items-center gap-1.5 ${
                selectedCategory === 'adventurer'
                  ? 'bg-o2-green text-black font-bold shadow-md'
                  : 'bg-retro-dark border border-retro-border text-gray-300 hover:border-gray-500'
              }`}
            >
              <span>🏹</span> AVENTUREIROS RPG ({AVATAR_PRESETS.filter(p => p.category === 'adventurer').length})
            </button>
            <button
              type="button"
              onClick={() => setSelectedCategory('personas')}
              className={`px-3 py-1.5 text-xs font-pixel rounded transition flex items-center gap-1.5 ${
                selectedCategory === 'personas'
                  ? 'bg-o2-green text-black font-bold shadow-md'
                  : 'bg-retro-dark border border-retro-border text-gray-300 hover:border-gray-500'
              }`}
            >
              <span>✨</span> PERSONAS CLEAN ({AVATAR_PRESETS.filter(p => p.category === 'personas').length})
            </button>
            <button
              type="button"
              onClick={() => setSelectedCategory('bottts')}
              className={`px-3 py-1.5 text-xs font-pixel rounded transition flex items-center gap-1.5 ${
                selectedCategory === 'bottts'
                  ? 'bg-o2-green text-black font-bold shadow-md'
                  : 'bg-retro-dark border border-retro-border text-gray-300 hover:border-gray-500'
              }`}
            >
              <span>🤖</span> MECHS & ROBÔS ({AVATAR_PRESETS.filter(p => p.category === 'bottts').length})
            </button>
            <button
              type="button"
              onClick={() => setSelectedCategory('all')}
              className={`px-3 py-1.5 text-xs font-pixel rounded transition ${
                selectedCategory === 'all'
                  ? 'bg-o2-green text-black font-bold shadow-md'
                  : 'bg-retro-dark border border-retro-border text-gray-300 hover:border-gray-500'
              }`}
            >
              TODOS ({AVATAR_PRESETS.length})
            </button>
            <button
              type="button"
              onClick={() => setSelectedCategory('pixel-art')}
              className={`px-3 py-1.5 text-xs font-pixel rounded transition flex items-center gap-1.5 ${
                selectedCategory === 'pixel-art'
                  ? 'bg-o2-green text-black font-bold shadow-md'
                  : 'bg-retro-dark border border-retro-border text-gray-400 hover:border-gray-500'
              }`}
            >
              <span>👾</span> 16-BIT (LEVE)
            </button>
          </div>

          {/* Busca & Semente Customizada */}
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filtrar por nome ou arquétipo (ex: Arthur, Morgana, SRE)..."
                className="w-full bg-[#0e141f] border border-retro-border focus:border-o2-green pl-9 pr-3 py-1.5 text-xs text-white font-mono rounded outline-none"
              />
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={customSeed}
                onChange={(e) => setCustomSeed(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleApplyCustomSeed()}
                placeholder="Gerar com seu nome..."
                className="bg-[#0e141f] border border-retro-border focus:border-o2-green px-3 py-1.5 text-xs text-white font-mono rounded outline-none w-36 sm:w-44"
              />
              <button
                type="button"
                onClick={handleApplyCustomSeed}
                disabled={!customSeed.trim()}
                className="pixel-btn pixel-btn-dark px-3 py-1.5 text-xs disabled:opacity-50"
              >
                Gerar
              </button>
              <button
                type="button"
                onClick={handleRandomize}
                className="pixel-btn pixel-btn-dark px-3 py-1.5 text-xs flex items-center gap-1 text-retro-cyan hover:border-retro-cyan"
                title="Sortear Aleatório"
              >
                <Dices className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Sortear</span>
              </button>
            </div>
          </div>
        </div>

        {/* Grade de Visuais */}
        <div className="p-4 overflow-y-auto flex-1 max-h-[50vh] bg-retro-dark">
          {filteredPresets.length === 0 ? (
            <div className="text-center py-12 text-gray-400 font-mono text-xs">
              Nenhum visual encontrado com os filtros informados.
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {filteredPresets.map((preset) => {
                const isSelected = tempSelectedUrl === preset.url;
                return (
                  <div
                    key={preset.id}
                    onClick={() => setTempSelectedUrl(preset.url)}
                    className={`relative p-3 rounded-lg border-2 cursor-pointer transition flex flex-col items-center text-center group ${
                      isSelected
                        ? 'border-o2-green bg-[#17261b] shadow-lg shadow-o2-green/20 scale-[1.02]'
                        : 'border-retro-border bg-[#0e141f] hover:border-gray-500 hover:bg-[#121a28]'
                    }`}
                  >
                    {isSelected && (
                      <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-o2-green text-black flex items-center justify-center shadow-md">
                        <Check className="w-3 h-3 stroke-[3]" />
                      </div>
                    )}
                    <img
                      src={preset.url}
                      alt={preset.name}
                      className="w-16 h-16 sm:w-20 sm:h-20 border border-retro-border bg-retro-card rounded p-1 mb-2 group-hover:scale-105 transition object-contain"
                    />
                    <span className="font-pixel text-[11px] text-white truncate max-w-full">
                      {preset.name}
                    </span>
                    <span className="text-[10px] font-mono text-gray-400 truncate max-w-full mt-0.5">
                      {preset.title}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Rodapé com Prévia Selecionada & Ações */}
        <div className="p-4 border-t border-retro-border bg-[#0e141f] flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <img
              src={tempSelectedUrl}
              alt="Visual Selecionado"
              className="w-12 h-12 border-2 border-o2-green rounded bg-retro-card p-1 flex-shrink-0 object-contain"
            />
            <div className="text-left">
              <span className="text-[10px] font-pixel text-o2-green uppercase block">
                Visual Selecionado
              </span>
              <span className="text-xs font-mono text-white truncate block max-w-[200px] sm:max-w-[260px]">
                {AVATAR_PRESETS.find((p) => p.url === tempSelectedUrl)?.name || 'Visual Personalizado'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button
              type="button"
              onClick={onClose}
              className="pixel-btn pixel-btn-dark px-4 py-2 text-xs flex-1 sm:flex-none"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              className="pixel-btn pixel-btn-primary px-5 py-2 text-xs flex items-center justify-center gap-1.5 shadow-lg flex-1 sm:flex-none"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>APLICAR VISUAL</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
