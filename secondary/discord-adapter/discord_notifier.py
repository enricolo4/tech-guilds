from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
import httpx
from tech_guilds.domain.ports.secondary.notification_port import NotificationPort

logger = logging.getLogger(__name__)


def build_discord_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Gera uma barra de progresso visual estilo RPG."""
    if total <= 0:
        pct = 0
        filled = 0
    else:
        clamped = max(0, min(current, total))
        pct = int((clamped / total) * 100)
        filled = int((clamped / total) * length)

    bar = ("█" * filled) + ("░" * (length - filled))
    return f"[`{bar}`] {pct}%"


class DiscordNotificationAdapter(NotificationPort):
    """Adaptador de saída (Secondary Adapter) para envio de mensagens ricas no Discord
    usando Rich Embeds, cores associadas a severidades e níveis, e campos customizados.
    """
    # Paleta de Cores RPG Hex -> Decimal para Discord Embeds
    COLOR_CRITICAL = 0xE74C3C         # 15158332 - Vermelho Fogo
    COLOR_HIGH = 0xE67E22             # 15105570 - Laranja Chamas
    COLOR_MEDIUM = 0xF1C40F           # 15844367 - Dourado / Amarelo Alerta
    COLOR_LOW = 0x3498DB              # 3447003  - Azul Arcano
    COLOR_VICTORY = 0x2ECC71          # 3066993  - Verde Esmeralda Vitória
    COLOR_LEVEL_UP = 0x9B59B6         # 10181046 - Púrpura Épico
    COLOR_GUARDIAN = 0x5865F2         # 5793266  - Blurple Guardião
    COLOR_DEFAULT = 0x1ABC9C          # 1752220  - Turquesa Guilda

    def __init__(self, webhook_url: Optional[str] = None, client: Optional[httpx.AsyncClient] = None):
        self.webhook_url = webhook_url
        self._custom_client = client is not None
        self._client = client or httpx.AsyncClient(timeout=5.0)
        self.last_payload: Optional[Dict[str, Any]] = None
        self.dispatched_payloads: List[Dict[str, Any]] = []

    async def notify_guild_channel(self, guild_id: UUID, message: str, title: Optional[str] = None) -> None:
        embed = {
            "title": f"⚔️ {title} ⚔️" if title else "📢 Comunicado da Guilda",
            "description": message,
            "color": self.COLOR_DEFAULT,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"Tech Guilds RPG Engine • Guild: {str(guild_id)[:8]}",
            },
        }
        payload = {
            "username": "Tech Guildmaster",
            "embeds": [embed],
        }
        await self._dispatch(payload)

    async def notify_boss_spawned(self, guild_id: UUID, boss_title: str, severity: str, bug_id: str) -> None:
        color_map = {
            "CRITICAL": self.COLOR_CRITICAL,
            "HIGH": self.COLOR_HIGH,
            "MEDIUM": self.COLOR_MEDIUM,
            "LOW": self.COLOR_LOW,
        }
        color = color_map.get(severity.upper(), self.COLOR_HIGH)
        hp_bar = build_discord_progress_bar(100, 100, length=12)

        embed = {
            "title": "🚨 ALERTA: NOVO MINI-BOSS NA ÁREA! 🚨",
            "description": (
                f"Um bug corrompeu o código em produção!\n"
                f"**Corrijam o problema para derrotar o invasor e resgatar o reino.**"
            ),
            "color": color,
            "fields": [
                {
                    "name": "👹 Inimigo",
                    "value": f"`[{bug_id}]` **{boss_title}**",
                    "inline": False,
                },
                {
                    "name": "⚡ Severidade",
                    "value": f"**{severity.upper()}**",
                    "inline": True,
                },
                {
                    "name": "❤️ Barra de HP",
                    "value": f"{hp_bar}",
                    "inline": True,
                },
                {
                    "name": "💰 Bounty do Squad",
                    "value": "✨ EXP & Ouro garantidos ao resolver!",
                    "inline": False,
                },
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"Tech Guilds • Sala de Guerra: {str(guild_id)[:8]}",
            },
        }

        payload = {
            "username": "Boss Radar RPG",
            "embeds": [embed],
        }
        await self._dispatch(payload)

    async def notify_boss_defeated(self, guild_id: UUID, boss_title: str, hero_name: str) -> None:
        hp_bar = build_discord_progress_bar(0, 100, length=12)

        embed = {
            "title": "💥 VITÓRIA ÉPICA! O MINI-BOSS FOI DERROTADO! 💥",
            "description": "O monstro foi exterminado dos servidores! Parabéns ao esquadrão!",
            "color": self.COLOR_VICTORY,
            "fields": [
                {
                    "name": "🛡️ Chefe Eliminado",
                    "value": f"**{boss_title}**",
                    "inline": False,
                },
                {
                    "name": "🗡️ Herói Vitorioso",
                    "value": f"**{hero_name}** (Golpe Final)",
                    "inline": True,
                },
                {
                    "name": "💀 Vida Restante",
                    "value": f"{hp_bar} (0 HP)",
                    "inline": True,
                },
                {
                    "name": "🎁 Recompensa Coletada",
                    "value": "✨ EXP e Moedas de Ouro creditadas na Guilda!",
                    "inline": False,
                },
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"Tech Guilds • Hall da Fama: {str(guild_id)[:8]}",
            },
        }

        payload = {
            "username": "Victory Herald RPG",
            "embeds": [embed],
        }
        await self._dispatch(payload)

    async def notify_level_up(self, guild_id: UUID, hero_name: str, new_level: int, hero_class: str) -> None:
        embed = {
            "title": "✨ LEVEL UP! EVOLUÇÃO DE HERÓI! ✨",
            "description": f"Os céus ressoam com glória! **{hero_name}** alcançou um novo patamar de poder!",
            "color": self.COLOR_LEVEL_UP,
            "fields": [
                {
                    "name": "🧙‍♂️ Herói",
                    "value": f"**{hero_name}**",
                    "inline": True,
                },
                {
                    "name": "⭐ Novo Nível",
                    "value": f"**Nível {new_level}**",
                    "inline": True,
                },
                {
                    "name": "🛡️ Especialização",
                    "value": f"`{hero_class}`",
                    "inline": True,
                },
                {
                    "name": "⚡ Benefícios Adquiridos",
                    "value": "+10 HP Máximo, Vida totalmente restaurada e +1 em todos os Atributos!",
                    "inline": False,
                },
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"Tech Guilds RPG Engine • Guild: {str(guild_id)[:8]}",
            },
        }

        payload = {
            "username": "Hero Herald RPG",
            "embeds": [embed],
        }
        await self._dispatch(payload)

    async def notify_guardian_blessing(self, guild_id: UUID, hero_name: str, xp_gained: int, pr_title: str) -> None:
        embed = {
            "title": "🛡️ BÊNÇÃO DO GUARDIÃO! CODE REVIEW APROVADO! 🛡️",
            "description": f"O Guardião **{hero_name}** inspecionou e aprovou as defesas no Pull Request:\n> *{pr_title}*",
            "color": self.COLOR_GUARDIAN,
            "fields": [
                {
                    "name": "🛡️ Revisor",
                    "value": f"**{hero_name}**",
                    "inline": True,
                },
                {
                    "name": "✨ Bênção Concedida",
                    "value": f"**+{xp_gained} EXP de Code Review**",
                    "inline": True,
                },
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "⚔️ Revisões limpas garantem builds inabaláveis.",
            },
        }

        payload = {
            "username": "Guardian Herald RPG",
            "embeds": [embed],
        }
        await self._dispatch(payload)

    async def _dispatch(self, payload: Dict[str, Any]) -> None:
        self.last_payload = payload
        self.dispatched_payloads.append(payload)

        if not self.webhook_url:
            first_embed = payload.get("embeds", [{}])[0]
            logger.info(f"[DiscordNotificationAdapter (Mock)] {first_embed.get('title')} - {first_embed.get('description')}")
            return
        try:
            res = await self._client.post(self.webhook_url, json=payload)
            res.raise_for_status()
        except Exception as e:
            logger.error(f"Erro ao disparar webhook para o Discord: {e}")

    async def aclose(self) -> None:
        if not self._custom_client:
            await self._client.aclose()
