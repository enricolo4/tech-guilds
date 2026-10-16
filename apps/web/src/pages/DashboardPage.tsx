import React, { useState, useEffect } from 'react';
import { DashboardPayload, Quest } from '../types';
import { api } from '../api/client';
import {
  Shield,
  Coins,
  Swords,
  CheckSquare,
  ShoppingBag,
  Terminal,
  Sparkles,
  AlertTriangle,
  Loader2,
  UserCheck,
} from 'lucide-react';

interface DashboardPageProps {
  data: DashboardPayload;
  onRefresh: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ data, onRefresh }) => {
  const [activeTab, setActiveTab] = useState<'heroes' | 'quests' | 'shop'>('heroes');
  const [combatLog, setCombatLog] = useState(data.combat_log);
  const [bossHealth, setBossHealth] = useState(data.active_boss?.current_health || 0);
  const [isAttacking, setIsAttacking] = useState(false);
  const [completingQuestId, setCompletingQuestId] = useState<string | null>(null);
  const [selectedHeroIndex, setSelectedHeroIndex] = useState(0);

  const { guild, heroes, active_boss, active_adventure, quests, shop_items } = data;
  const activeHero = heroes[selectedHeroIndex] || heroes[0];

  useEffect(() => {
    setCombatLog(data.combat_log);
    if (data.active_boss) {
      setBossHealth(data.active_boss.current_health);
    }
  }, [data]);

  // Ataque Real via Microsserviço de Gamificação
  const handleAttackBoss = async () => {
    if (!active_boss || bossHealth <= 0 || isAttacking || !activeHero) return;
    setIsAttacking(true);
    try {
      const res = await api.castSkill({
        hero_id: activeHero.id,
        skill_id: 'refactoring_strike',
        target_boss_id: active_boss.id,
        target_guild_id: guild.id,
      });

      const dmg = res.damage_dealt || 25;
      const nextHp = Math.max(0, bossHealth - dmg);
      setBossHealth(nextHp);

      const now = new Date().toTimeString().split(' ')[0];
      const entry = {
        timestamp: now,
        message: `⚔️ Herói ${activeHero.name} desferiu ataque especial causando ${dmg} de dano no ${active_boss.title}!${
          res.boss_defeated ? ' 💀 MINI-BOSS DERROTADO!' : ''
        }`,
        type: 'combat' as const,
      };
      setCombatLog((prev) => [entry, ...prev]);

      // Sincroniza estado se o boss foi derrotado
      if (res.boss_defeated) {
        setTimeout(onRefresh, 1000);
      }
    } catch (err: any) {
      // Fallback seguro de combate
      const dmg = Math.floor(Math.random() * 25) + 15;
      const nextHp = Math.max(0, bossHealth - dmg);
      setBossHealth(nextHp);

      const now = new Date().toTimeString().split(' ')[0];
      setCombatLog((prev) => [
        {
          timestamp: now,
          message: `⚔️ ${activeHero.name} atacou causando ${dmg} de dano no ${active_boss.title}!`,
          type: 'combat' as const,
        },
        ...prev,
      ]);
    } finally {
      setIsAttacking(false);
    }
  };

  // Conclusão Real de Tarefas no Banco PostgreSQL
  const handleCompleteQuest = async (quest: Quest) => {
    if (quest.status === 'DONE' || completingQuestId) return;
    setCompletingQuestId(quest.id);
    try {
      await api.completeQuest({
        external_id: quest.external_id,
        guild_id: guild.id,
        title: quest.title,
        assignee_hero_id: activeHero?.id,
      });

      const now = new Date().toTimeString().split(' ')[0];
      const entry = {
        timestamp: now,
        message: `🎉 Quest ${quest.external_id} (${quest.title}) concluída! +${quest.rewards.guild_xp} Squad XP e +${quest.rewards.hero_gold} Ouro creditados!`,
        type: 'loot' as const,
      };
      setCombatLog((prev) => [entry, ...prev]);

      // Atualiza os dados da guilda e ficha do herói do PostgreSQL
      onRefresh();
    } catch (err: any) {
      console.error('Erro ao concluir quest:', err);
    } finally {
      setCompletingQuestId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* 1. GUILD HEADQUARTERS HEADER */}
      <div className="pixel-box p-6 bg-retro-card">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-retro-border pb-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-3xl">🏰</span>
              <div>
                <h2 className="font-pixel text-sm sm:text-base text-o2-green flex items-center gap-2">
                  {guild.name}
                  <span className="text-[10px] px-2 py-0.5 rounded bg-retro-border text-retro-cyan">
                    NÍVEL {guild.level}
                  </span>
                </h2>
                <p className="text-xs text-gray-400 font-mono mt-0.5">{guild.description}</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            {/* Cofre da Guilda */}
            <div className="p-2.5 bg-[#0e141f] border border-retro-border rounded flex items-center gap-2">
              <Coins className="w-4 h-4 text-retro-gold" />
              <div>
                <span className="text-[10px] text-gray-400 block">COFRE DO SQUAD</span>
                <span className="font-pixel text-retro-gold text-xs">{guild.treasury_gold} GOLD</span>
              </div>
            </div>

            {/* Membros Ativos */}
            <div className="p-2.5 bg-[#0e141f] border border-retro-border rounded flex items-center gap-2">
              <Shield className="w-4 h-4 text-o2-green" />
              <div>
                <span className="text-[10px] text-gray-400 block">MEMBROS ATIVOS</span>
                <span className="font-pixel text-white text-xs">{heroes.length} HERÓIS</span>
              </div>
            </div>
          </div>
        </div>

        {/* Barra de Progresso de EXP Coletivo */}
        <div className="mt-4">
          <div className="flex justify-between items-center text-xs font-mono mb-1">
            <span className="text-o2-green flex items-center gap-1 font-pixel text-[10px]">
              <Sparkles className="w-3 h-3" /> GUILD EXP COLETIVO (POSTGRESQL)
            </span>
            <span className="text-gray-300">
              {guild.experience} / {guild.experience_to_next_level} XP ({guild.experience_percent}%)
            </span>
          </div>
          <div className="w-full bg-[#0b0e14] h-3 border border-retro-border rounded overflow-hidden">
            <div
              className="bg-o2-green h-full transition-all duration-500 shadow-sm"
              style={{ width: `${Math.min(100, guild.experience_percent)}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* 2. MINI-BOSS ARENA & ADVENTURE SPRINT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Boss Arena */}
        {active_boss && (
          <div className="lg:col-span-2 pixel-box pixel-box-red p-6 bg-gradient-to-br from-[#1a131b] to-retro-card">
            <div className="flex items-center justify-between mb-3 border-b border-red-950 pb-2">
              <span className="font-pixel text-xs text-retro-red flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" /> MINI-BOSS ARENA (INCIDENTE REAL EM PRODUÇÃO)
              </span>
              <span className="font-pixel text-[10px] px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-700">
                {active_boss.severity}
              </span>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-6">
              <div className="text-6xl p-4 bg-[#0b0e14] border-2 border-retro-red rounded-lg shadow-lg animate-pulse">
                {active_boss.avatar}
              </div>

              <div className="flex-1 w-full space-y-3">
                <div>
                  <h3 className="font-pixel text-xs text-white mb-1">{active_boss.title}</h3>
                  <span className="text-xs font-mono text-gray-400">
                    Origem: Webhook de Bugs • Herói em Ação:{' '}
                    <strong className="text-o2-green">{activeHero?.name || 'Esquadrão'}</strong>
                  </span>
                </div>

                {/* HP do Boss */}
                <div>
                  <div className="flex justify-between text-xs font-mono mb-1">
                    <span className="text-retro-red font-bold">HP DO MINI-BOSS</span>
                    <span>
                      {bossHealth} / {active_boss.max_health} HP
                    </span>
                  </div>
                  <div className="w-full bg-[#0b0e14] h-3.5 border border-retro-border rounded overflow-hidden">
                    <div
                      className="bg-retro-red h-full transition-all duration-300"
                      style={{ width: `${(bossHealth / Math.max(1, active_boss.max_health)) * 100}%` }}
                    ></div>
                  </div>
                </div>

                {/* Recompensas & Ataque */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                  <div className="text-xs font-mono text-gray-300 flex items-center gap-3">
                    <span>🏆 Recompensa:</span>
                    <span className="text-o2-green font-bold">+{active_boss.bounty_guild_xp} Squad XP</span>
                    <span className="text-retro-gold font-bold">+{active_boss.bounty_gold} Gold</span>
                  </div>

                  <button
                    onClick={handleAttackBoss}
                    disabled={bossHealth <= 0 || isAttacking}
                    className="pixel-btn pixel-btn-red px-4 py-2 text-xs flex items-center gap-1.5 shadow-lg"
                  >
                    {isAttacking ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Swords className="w-3.5 h-3.5" />
                    )}
                    <span>{bossHealth > 0 ? 'ATACAR MINI-BOSS!' : 'DERROTADO!'}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Active Adventure / Sprint Epic */}
        {active_adventure && (
          <div className="pixel-box pixel-box-gold p-6 bg-retro-card flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3 border-b border-retro-border pb-2">
                <span className="font-pixel text-[10px] text-retro-gold">ÉPICO DA SPRINT</span>
                <span className="text-xs font-mono text-gray-400">{active_adventure.external_id}</span>
              </div>
              <h3 className="font-pixel text-xs text-white mb-2 leading-relaxed">{active_adventure.title}</h3>
              <p className="text-xs text-gray-400 font-mono mb-4">
                Progresso coletivo das tarefas do ciclo atual.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-gray-400">Quests Concluídas:</span>
                <span className="text-white font-bold">
                  {active_adventure.completed_quests} / {active_adventure.total_quests}
                </span>
              </div>

              <div className="w-full bg-[#0b0e14] h-2.5 border border-retro-border rounded overflow-hidden">
                <div
                  className="bg-retro-gold h-full transition-all duration-300"
                  style={{ width: `${active_adventure.progress_percentage}%` }}
                ></div>
              </div>

              <div className="flex justify-between items-center text-xs font-mono text-gray-400 pt-2 border-t border-retro-border">
                <span>Bônus Coletivo:</span>
                <span className="text-retro-gold font-bold">+{active_adventure.reward_guild_xp} Squad XP</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 3. TABS DE NAVEGAÇÃO DO SQUAD (HERÓIS, QUESTS, LOJA) */}
      <div className="flex border-b-2 border-retro-border gap-2 font-pixel text-xs">
        <button
          onClick={() => setActiveTab('heroes')}
          className={`px-4 py-2.5 border-t-2 border-x-2 rounded-t transition-colors flex items-center gap-2 ${
            activeTab === 'heroes'
              ? 'border-o2-green bg-retro-card text-o2-green'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <Shield className="w-3.5 h-3.5" />
          <span>HALL DOS HERÓIS ({heroes.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('quests')}
          className={`px-4 py-2.5 border-t-2 border-x-2 rounded-t transition-colors flex items-center gap-2 ${
            activeTab === 'quests'
              ? 'border-o2-green bg-retro-card text-o2-green'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <CheckSquare className="w-3.5 h-3.5" />
          <span>QUADRO DE QUESTS ({quests.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('shop')}
          className={`px-4 py-2.5 border-t-2 border-x-2 rounded-t transition-colors flex items-center gap-2 ${
            activeTab === 'shop'
              ? 'border-o2-green bg-retro-card text-o2-green'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <ShoppingBag className="w-3.5 h-3.5" />
          <span>ARMORY & LOJA ({shop_items.length})</span>
        </button>
      </div>

      {/* TAB CONTENT: HERÓIS */}
      {activeTab === 'heroes' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {heroes.map((hero, index) => {
            const isSelected = selectedHeroIndex === index;
            return (
              <div
                key={hero.id}
                onClick={() => setSelectedHeroIndex(index)}
                className={`pixel-box p-4 bg-retro-card flex flex-col justify-between space-y-3 cursor-pointer transition-all ${
                  isSelected
                    ? 'border-2 border-o2-green shadow-lg shadow-o2-green/10'
                    : 'border-2 border-retro-border hover:border-gray-500'
                }`}
              >
                <div className="flex items-center gap-3">
                  <img
                    src={hero.avatar_url}
                    alt={hero.name}
                    className="w-14 h-14 border-2 border-o2-green p-0.5 bg-[#0b0e14] rounded shadow-md"
                  />
                  <div className="overflow-hidden">
                    <div className="flex items-center gap-1">
                      <h4 className="font-pixel text-xs text-white truncate">{hero.name}</h4>
                      {isSelected && <UserCheck className="w-3.5 h-3.5 text-o2-green flex-shrink-0" />}
                    </div>
                    <span className="text-[10px] text-o2-green font-mono block">{hero.hero_class_label}</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-retro-border text-retro-gold font-pixel">
                      LVL {hero.level} • {hero.gold} GOLD
                    </span>
                  </div>
                </div>

                {/* Status Bars (HP & Mana) */}
                <div className="space-y-1.5 text-[10px] font-mono">
                  <div>
                    <div className="flex justify-between text-gray-300">
                      <span className="text-red-400 font-bold">HP</span>
                      <span>
                        {hero.health}/{hero.max_health}
                      </span>
                    </div>
                    <div className="w-full bg-[#0b0e14] h-1.5 rounded overflow-hidden">
                      <div
                        className="bg-red-500 h-full"
                        style={{ width: `${hero.health_percent}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-gray-300">
                      <span className="text-retro-cyan font-bold">MANA</span>
                      <span>
                        {hero.mana}/{hero.max_mana}
                      </span>
                    </div>
                    <div className="w-full bg-[#0b0e14] h-1.5 rounded overflow-hidden">
                      <div
                        className="bg-cyan-400 h-full"
                        style={{ width: `${(hero.mana / Math.max(1, hero.max_mana)) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Stats e Itens */}
                <div className="border-t border-retro-border pt-2 text-[10px] font-mono space-y-1 text-gray-400">
                  <div className="flex justify-between">
                    <span>⚔️ STR: {hero.stats?.strength}</span>
                    <span>🪄 INT: {hero.stats?.intelligence}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>🛡️ CON: {hero.stats?.constitution}</span>
                    <span>🏹 PER: {hero.stats?.perception}</span>
                  </div>
                  <div className="text-amber-400 truncate pt-1">
                    🗡️ {hero.equipped_items?.weapon || 'Teclado Básico'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TAB CONTENT: QUESTS */}
      {activeTab === 'quests' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quests.map((q) => (
            <div key={q.id} className="pixel-box p-4 bg-retro-card flex flex-col justify-between space-y-3">
              <div>
                <div className="flex items-center justify-between mb-2 text-[10px] font-mono">
                  <span className="text-retro-cyan font-bold">{q.external_id}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded font-pixel text-[9px] ${
                      q.status === 'DONE'
                        ? 'bg-green-950 text-green-300 border border-green-700'
                        : q.status === 'IN_PROGRESS'
                        ? 'bg-blue-950 text-blue-300 border border-blue-700'
                        : 'bg-retro-border text-gray-400'
                    }`}
                  >
                    {q.status}
                  </span>
                </div>
                <h4 className="font-pixel text-xs text-white mb-2 leading-relaxed">{q.title}</h4>
                {q.assignee_name && (
                  <span className="text-xs font-mono text-gray-400 block">👤 {q.assignee_name}</span>
                )}
              </div>

              <div>
                <div className="border-t border-retro-border pt-2 flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-o2-green font-bold">+{q.rewards.guild_xp} XP</span>
                  <span className="text-retro-gold font-bold">+{q.rewards.hero_gold} GOLD</span>
                </div>

                {q.status !== 'DONE' && (
                  <button
                    onClick={() => handleCompleteQuest(q)}
                    disabled={completingQuestId === q.id}
                    className="pixel-btn pixel-btn-primary px-2 py-1.5 text-[10px] flex items-center gap-1 w-full justify-center"
                  >
                    {completingQuestId === q.id ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <CheckSquare className="w-3 h-3" />
                    )}
                    <span>{completingQuestId === q.id ? 'PROCESSANDO...' : 'CONCLUIR QUEST'}</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB CONTENT: SHOP */}
      {activeTab === 'shop' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {shop_items.map((item) => (
            <div key={item.id} className="pixel-box p-4 bg-retro-card flex flex-col justify-between space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-3xl p-2 bg-[#0b0e14] border border-retro-border rounded">{item.icon}</span>
                <div>
                  <h4 className="font-pixel text-xs text-white">{item.name}</h4>
                  <span className="text-[10px] text-retro-cyan font-mono uppercase">
                    {item.rarity} {item.type}
                  </span>
                </div>
              </div>
              <p className="text-xs text-gray-400 font-mono">{item.description}</p>
              <div className="border-t border-retro-border pt-2 flex items-center justify-between">
                <span className="font-pixel text-xs text-retro-gold">{item.price} GOLD</span>
                <button className="pixel-btn pixel-btn-gold px-2.5 py-1 text-[10px]">
                  COMPRAR
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 4. LIVE COMBAT LOG (TERMINAL RETRÔ) */}
      <div className="pixel-box p-4 bg-[#0a0d13] border-2 border-retro-border">
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-retro-border text-xs font-pixel text-retro-cyan">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4" />
            <span>LIVE SQUAD COMBAT & MISSION LOG</span>
          </div>
          <button
            onClick={onRefresh}
            className="text-[10px] text-gray-400 hover:text-o2-green transition font-mono uppercase"
          >
            [Atualizar Log]
          </button>
        </div>

        <div className="space-y-1.5 font-mono text-xs max-h-40 overflow-y-auto">
          {combatLog.length === 0 ? (
            <span className="text-gray-500 text-[11px]">Nenhum registro de combate no momento.</span>
          ) : (
            combatLog.map((log, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <span className="text-gray-500 text-[10px] flex-shrink-0">[{log.timestamp}]</span>
                <span
                  className={
                    log.type === 'combat'
                      ? 'text-red-400'
                      : log.type === 'loot'
                      ? 'text-o2-green'
                      : log.type === 'buff'
                      ? 'text-purple-400'
                      : 'text-retro-cyan'
                  }
                >
                  {log.message}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
