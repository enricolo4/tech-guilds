# 🌐 Tech Guilds — Web Frontend (React + Vite)

Frontend Web moderno do **Tech Guilds** construído com **React 18**, **TypeScript**, **Vite** e **Tailwind CSS**, orquestrado pelo **Nx Monorepo**.

---

## 🎨 Características Visuais & UX

- **Estética Retro RPG & Pixel Art:** Tipografia arcade (*Press Start 2P* e *VT323*), paleta inspirada no Design System O2 INC. (*Vivid Green #6BF169, Intense Gray #494949, Neon Cyan e Gold*) e scanlines CRT.
- **Avatares Dinâmicos em Tempo Real:** Integração com a API DiceBear gerando sprites 16-bit únicos baseados no nome do desenvolvedor.
- **Modos de Operação Híbridos:** Suporte tanto a dados reais do banco de dados quanto a payload rico de demonstração (`demo`) para exploração visual imediata.

---

## 📄 Telas Implementadas

1. **Página de Onboarding (`/onboarding`):**
   - **Passo 1 — Identidade:** Nome do herói, e-mail corporativo e botões de atalho SSO (Google, GitHub, Azure AD).
   - **Passo 2 — Classe RPG:** Seleção entre as 6 classes de engenharia (*Warrior, Mage, Paladin, Ranger, Tactician, Novice*), com barras de atributos animados (STR, INT, CON, PER), arma inicial e habilidade ativa.
   - **Passo 3 — Esquadrão:** Criação de novo Squad, ingresso em guilda existente ou modo Solo.
   - **Passo 4 — Ficha & Forja:** Confirmação e chamada real para a API `POST /api/registration/heroes` (emitindo evento no NATS JetStream).
   - **Passo 5 — Sucesso:** Confirmação com redirecionamento automático para o Dashboard.

2. **Dashboard do Esquadrão (`/` ou `/dashboard`):**
   - **Guild Header:** Nível do esquadrão, barra de XP coletivo da sprint, cofre de ouro e membros ativos.
   - **Mini-Boss Arena:** Visualização do bug crítico em produção com barra de HP e botão de ataque interativo.
   - **Sprint Epic:** Progresso coletivo das tarefas do ciclo atual.
   - **Hall dos Heróis:** Cartões dos heróis do squad com HP, Mana, stats e itens equipados.
   - **Quadro de Quests:** Tarefas de desenvolvimento com status e recompensas de XP/Ouro.
   - **Armory & Loja:** Equipamentos lendários e buffs de sprint compráveis com o ouro da guilda.
   - **Live Combat Log:** Terminal retrô com histórico de eventos de combate e tarefas concluídas.

---

## 🚀 Como Executar Localmente

### Via Nx (Recomendado):
```bash
# Na raiz do monorepo:
npx nx serve web
```
Acesse: [http://localhost:3000](http://localhost:3000)

### Proxy para o Backend:
O arquivo `vite.config.ts` está pré-configurado com proxy automático:
- Todas as chamadas para `/api/*` e `/dashboard/data/*` são roteadas para o **API Gateway** na porta `8000`.
