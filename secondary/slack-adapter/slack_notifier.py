import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
import httpx
from tech_guilds.domain.ports.notification_port import NotificationPort

logger = logging.getLogger(__name__)


def build_progress_bar(current: int, total: int, length: int = 10, fill_char: str = "█", empty_char: str = "░") -> str:
    """Gera uma barra de progresso visual retrô no estilo RPG."""
    if total <= 0:
        pct = 0
        filled = 0
    else:
        clamped = max(0, min(current, total))
        pct = int((clamped / total) * 100)
        filled = int((clamped / total) * length)

    bar = (fill_char * filled) + (empty_char * (length - filled))
    return f"[{bar}] {pct}%"


class SlackNotificationAdapter(NotificationPort):
    """Adaptador de saída (Secondary Adapter) para envio de mensagens ricas no formato
    Slack Block Kit com temática retrô RPG, botões interativos e barras de progresso.
    """
    def __init__(self, webhook_url: Optional[str] = None, client: Optional[httpx.AsyncClient] = None):
        self.webhook_url = webhook_url
        self._custom_client = client is not None
        self._client = client or httpx.AsyncClient(timeout=5.0)
        self.last_payload: Optional[Dict[str, Any]] = None
        self.dispatched_payloads: List[Dict[str, Any]] = []

    async def notify_guild_channel(self, guild_id: UUID, message: str, title: Optional[str] = None) -> None:
        header_text = f"⚔️ {title} ⚔️" if title else "📢 COMUNICADO DA GUILDA"
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": header_text[:150], "emoji": True},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message},
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"🏰 *Tech Guilds* | Guild ID: `{str(guild_id)[:8]}` • 🎮 Modo Cooperativo"}
                ],
            },
        ]

        payload = {
            "text": f"*{title}*\n{message}" if title else message,
            "blocks": blocks,
        }
        await self._dispatch(payload)

    async def notify_boss_spawned(self, guild_id: UUID, boss_title: str, severity: str, bug_id: str) -> None:
        sev_icons = {
            "CRITICAL": "🔥 P0 - CRÍTICO",
            "HIGH": "⚡ P1 - ALTO",
            "MEDIUM": "⚠️ P2 - MÉDIO",
            "LOW": "🔹 P3 - BAIXO",
        }
        sev_label = sev_icons.get(severity.upper(), f"⚡ {severity}")
        initial_hp_bar = build_progress_bar(100, 100, length=12)

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🚨 ALERTA GERAL: MINI-BOSS DETECTADO! 🚨", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"👾 *Um monstro de código emergiu das profundezas da produção!*\n"
                        f"A guilda precisa se unir para derrotar esta ameaça e restaurar a estabilidade do reino."
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*👹 Nome do Chefe:*\n`[{bug_id}]` {boss_title}"},
                    {"type": "mrkdwn", "text": f"*⚡ Nível de Ameaça:*\n`{sev_label}`"},
                    {"type": "mrkdwn", "text": f"*❤️ Barra de HP Inicial:*\n`{initial_hp_bar}` (100% Vida)"},
                    {"type": "mrkdwn", "text": f"*💰 Recompensa (Bounty):*\n✨ EXP Herói + EXP Guilda + Ouro"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "⚔️ Atacar Boss (Corrigir)", "emoji": True},
                        "style": "danger",
                        "value": f"attack_{bug_id}",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📜 Ver no Issue Tracker", "emoji": True},
                        "style": "primary",
                        "value": f"view_{bug_id}",
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "🛡️ *Batalha em Andamento* • Dano é causado ao abrir PRs e fechar o bug!"}
                ],
            },
        ]

        text_fallback = (
            f"🚨 *MINI-BOSS DETECTADO!* [{bug_id}] {boss_title} ({sev_label})\n"
            f"HP: {initial_hp_bar} | Corrijam para ganhar Bounty!"
        )
        payload = {"text": text_fallback, "blocks": blocks}
        await self._dispatch(payload)

    async def notify_boss_defeated(self, guild_id: UUID, boss_title: str, hero_name: str) -> None:
        defeated_hp_bar = build_progress_bar(0, 100, length=12)

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "💥 VITÓRIA ÉPICA! O MINI-BOSS FOI DERROTADO! 💥", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"🏆 *O monstro foi aniquilado e a paz voltou aos servidores!*\n"
                        f"Todos os heróis envolvidos recebem glória e os cofres da guilda foram abastecidos."
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*🛡️ Chefe Derrotado:*\n{boss_title}"},
                    {"type": "mrkdwn", "text": f"*🗡️ Golpe de Misericórdia:*\n*{hero_name}*"},
                    {"type": "mrkdwn", "text": f"*💀 Status de Vida:*\n`{defeated_hp_bar}` (0 HP)"},
                    {"type": "mrkdwn", "text": f"*🎁 Recompensas Coletadas:*\n✨ EXP Distribuído | 💰 Ouro no Baú"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🏆 Hall da Fama", "emoji": True},
                        "style": "primary",
                        "value": "view_hall_of_fame",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🍻 Taverna da Guilda", "emoji": True},
                        "value": "tavern",
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"✨ Conquista registrada no histórico da Guilda `{str(guild_id)[:8]}`"}
                ],
            },
        ]

        text_fallback = (
            f"💥 *VITÓRIA! O MINI-BOSS FOI DERROTADO!* 💥\n"
            f"Chefe: {boss_title} | Golpe Final: {hero_name}"
        )
        payload = {"text": text_fallback, "blocks": blocks}
        await self._dispatch(payload)

    async def notify_level_up(self, guild_id: UUID, hero_name: str, new_level: int, hero_class: str) -> None:
        level_bar = build_progress_bar(100, 100, length=10, fill_char="★", empty_char="☆")

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "✨ EVOLUÇÃO DE HERÓI: LEVEL UP! ✨", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"🎉 Uma aura dourada envolve o herói *{hero_name}*!\n"
                        f"Seus atributos foram aprimorados e a vida máxima foi restaurada!"
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*🧙‍♂️ Herói:*\n*{hero_name}*"},
                    {"type": "mrkdwn", "text": f"*⭐ Novo Nível:*\n*Nível {new_level}*"},
                    {"type": "mrkdwn", "text": f"*🛡️ Especialização:*\n`{hero_class}`"},
                    {"type": "mrkdwn", "text": f"*⚡ Barra de Vitalidade:*\n`{level_bar}` (HP MAX +10)"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📜 Ficha do Herói", "emoji": True},
                        "style": "primary",
                        "value": f"hero_sheet_{hero_name}",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🎁 Distribuir Pontos", "emoji": True},
                        "value": f"skill_points_{hero_name}",
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "🆙 Continue entregando Quests para alcançar níveis lendários!"}
                ],
            },
        ]

        text_fallback = f"✨ *LEVEL UP!* Parabéns a *{hero_name}* ({hero_class}), que alcançou o *Nível {new_level}*!"
        payload = {"text": text_fallback, "blocks": blocks}
        await self._dispatch(payload)

    async def notify_guardian_blessing(self, guild_id: UUID, hero_name: str, xp_gained: int, pr_title: str) -> None:
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🛡️ BÊNÇÃO DO GUARDIÃO CONCEDIDA! 🛡️", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"✨ O Guardião *{hero_name}* exerceu vigilância e diligência, "
                        f"revisando e aprovando o Pull Request:\n> *{pr_title}*"
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*🛡️ Guardião Revisor:*\n*{hero_name}*"},
                    {"type": "mrkdwn", "text": f"*✨ Bênção de Sabedoria:*\n`+{xp_gained} XP de Code Review`"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📜 Ver Pull Request", "emoji": True},
                        "style": "primary",
                        "value": "view_pr",
                    }
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "⚔️ Revisões minuciosas protegem o reino de bugs ocultos e incidentes."}
                ],
            },
        ]

        text_fallback = (
            f"🛡️ *Bênção do Guardião:* {hero_name} aprovou o PR '{pr_title}' e recebeu +{xp_gained} XP de Code Review!"
        )
        payload = {"text": text_fallback, "blocks": blocks}
        await self._dispatch(payload)

    async def _dispatch(self, payload: Dict[str, Any]) -> None:
        self.last_payload = payload
        self.dispatched_payloads.append(payload)

        if not self.webhook_url:
            logger.info(f"[SlackNotificationAdapter (Mock)] {payload.get('text')}")
            return
        try:
            res = await self._client.post(self.webhook_url, json=payload)
            res.raise_for_status()
        except Exception as e:
            logger.error(f"Erro ao disparar webhook para o Slack: {e}")

    async def aclose(self) -> None:
        if not self._custom_client:
            await self._client.aclose()
