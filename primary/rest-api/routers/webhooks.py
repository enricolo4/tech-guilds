from typing import Any, Dict, Optional
from uuid import UUID
from fastapi import APIRouter, Body, Depends, Header, Query, status

from ..dependencies.container import DependencyContainer, get_container
from tech_guilds.domain.entities.guild import Guild
from tech_guilds.domain.use_cases.process_card_event import ProcessCardEventCommand
from tech_guilds.domain.use_cases.process_bug_event import BugEventCommand
from tech_guilds.secondary.linear_adapter.linear_parser import LinearWebhookParser
from tech_guilds.secondary.github_adapter.github_parser import GitHubWebhookParser
from ..schemas.webhook_schemas import (
    WebhookCardEventRequest,
    WebhookBugEventRequest,
    WebhookEventResponse,
)

router = APIRouter(prefix="/webhooks", tags=["Webhooks & Eventos"])


async def _resolve_guild_id(container: DependencyContainer, guild_id: Optional[UUID]) -> UUID:
    """Recupera o ID da guilda informada, ou busca a primeira guilda existente, ou cria uma default."""
    if guild_id:
        return guild_id
    guilds = await container.guild_repo.list_all()
    if guilds:
        return guilds[0].id

    default_guild = Guild(name="Guilda Principal")
    await container.guild_repo.save(default_guild)
    return default_guild.id


@router.post("/cards", response_model=WebhookEventResponse, status_code=status.HTTP_200_OK)
async def handle_card_event(
    req: WebhookCardEventRequest,
    container: DependencyContainer = Depends(get_container),
):
    """Recebe eventos genéricos de cartões de tarefas vindos do Linear, Jira ou GitHub Issues.
    Se a tarefa for finalizada, calcula e distribui XP individual e coletivo para o Squad.
    """
    cmd = ProcessCardEventCommand(
        external_id=req.external_id,
        external_source=req.external_source,
        title=req.title,
        assignee_email=req.assignee_email,
        guild_id=req.guild_id,
        new_status=req.new_status,
        difficulty=req.difficulty,
        is_pair_programming=req.is_pair_programming,
        adventure_external_id=req.adventure_external_id,
    )
    result = await container.process_card_use_case.execute(cmd)

    msg = f"Card [{req.external_id}] processado com status {req.new_status}."
    if result.reward:
        msg += f" Recompensa: +{result.reward.hero_xp} XP herói, +{result.reward.guild_xp} XP guilda."
    if result.hero_leveled_up:
        msg += " 🎉 O Herói subiu de nível!"
    if result.adventure_completed:
        msg += " 🏆 O Épico da Guilda foi concluído!"

    return WebhookEventResponse(
        success=True,
        event_type="CARD_EVENT",
        message=msg,
        reward_hero_xp=result.reward.hero_xp if result.reward else None,
        reward_guild_xp=result.reward.guild_xp if result.reward else None,
    )


@router.post("/bugs", response_model=WebhookEventResponse, status_code=status.HTTP_200_OK)
async def handle_bug_event(
    req: WebhookBugEventRequest,
    container: DependencyContainer = Depends(get_container),
):
    """Recebe eventos genéricos de bugs e incidentes.
    Cria Mini-Bosses que atacam o Squad até serem resolvidos.
    """
    cmd = BugEventCommand(
        external_id=req.external_id,
        title=req.title,
        guild_id=req.guild_id,
        severity=req.severity,
        is_resolved=req.is_resolved,
        resolver_email=req.resolver_email,
    )
    result = await container.process_bug_use_case.execute(cmd)

    if result.is_defeated:
        msg = f"Mini-Boss [{req.external_id}] derrotado! +{result.bounty_hero_xp} XP ao herói e +{result.bounty_guild_xp} XP à Guilda!"
    else:
        msg = f"Mini-Boss [{req.external_id}] ({req.severity}) invadiu a Guilda! Corrijam o bug para derrotá-lo."

    return WebhookEventResponse(
        success=True,
        event_type="BUG_EVENT",
        message=msg,
        reward_hero_xp=result.bounty_hero_xp if result.is_defeated else None,
        reward_guild_xp=result.bounty_guild_xp if result.is_defeated else None,
    )


@router.post("/linear", response_model=WebhookEventResponse, status_code=status.HTTP_200_OK)
async def handle_linear_webhook(
    payload: Dict[str, Any] = Body(...),
    guild_id: Optional[UUID] = Query(None),
    container: DependencyContainer = Depends(get_container),
):
    """Webhook nativo do Linear.
    Decodifica eventos de criação e atualização de Issues, ciclos (sprints) e projetos (épicos).
    Se rotulado como 'Bug', gera ou combate Mini-Bosses; caso contrário, gerencia Quests.
    """
    event = LinearWebhookParser.parse(payload)

    if event.type != "Issue" or event.action == "remove":
        return WebhookEventResponse(
            success=True,
            event_type="LINEAR_IGNORED",
            message=f"Evento Linear '{event.type}:{event.action}' ignorado.",
        )

    effective_guild_id = await _resolve_guild_id(container, guild_id)

    if event.is_bug:
        cmd = LinearWebhookParser.to_bug_command(event, effective_guild_id)
        result = await container.process_bug_use_case.execute(cmd)

        if result.is_defeated:
            msg = f"Mini-Boss [{event.identifier}] derrotado via Linear! +{result.bounty_hero_xp} XP ao herói e +{result.bounty_guild_xp} XP à Guilda!"
        else:
            msg = f"Mini-Boss [{event.identifier}] ({event.severity.value}) invadiu a Guilda via Linear!"

        return WebhookEventResponse(
            success=True,
            event_type="LINEAR_BUG",
            message=msg,
            reward_hero_xp=result.bounty_hero_xp if result.is_defeated else None,
            reward_guild_xp=result.bounty_guild_xp if result.is_defeated else None,
        )

    # Processa como Quest regular
    cmd_card = LinearWebhookParser.to_card_command(event, effective_guild_id)
    result_card = await container.process_card_use_case.execute(cmd_card)

    msg = f"Card Linear [{event.identifier}] atualizado para status '{event.status.value}'."
    if result_card.reward:
        msg += f" Recompensa: +{result_card.reward.hero_xp} XP herói, +{result_card.reward.guild_xp} XP guilda."
    if result_card.hero_leveled_up:
        msg += " 🎉 O Herói subiu de nível!"
    if result_card.adventure_completed:
        msg += " 🏆 O Épico da Guilda foi concluído!"

    return WebhookEventResponse(
        success=True,
        event_type="LINEAR_CARD",
        message=msg,
        reward_hero_xp=result_card.reward.hero_xp if result_card.reward else None,
        reward_guild_xp=result_card.reward.guild_xp if result_card.reward else None,
    )


@router.post("/github", response_model=WebhookEventResponse, status_code=status.HTTP_200_OK)
async def handle_github_webhook(
    payload: Dict[str, Any] = Body(...),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    guild_id: Optional[UUID] = Query(None),
    container: DependencyContainer = Depends(get_container),
):
    """Webhook nativo do GitHub.
    Lida com Pull Requests (abertos, mergeados), revisões de código (Bênção do Guardião ao aprovar)
    e Issues (criação de Bugs como MiniBosses e derrotas ao fechar).
    """
    event = GitHubWebhookParser.parse(payload, event_header=x_github_event)
    effective_guild_id = await _resolve_guild_id(container, guild_id)

    # 1. Eventos de Pull Request
    if event.event_type == "pull_request":
        cmd_card = GitHubWebhookParser.to_card_command(event, effective_guild_id)
        result_card = await container.process_card_use_case.execute(cmd_card)

        msg = f"GitHub PR [{event.identifier}] processado com status '{event.status.value}'."
        if result_card.reward:
            msg += f" Recompensa: +{result_card.reward.hero_xp} XP herói, +{result_card.reward.guild_xp} XP guilda."
        if result_card.hero_leveled_up:
            msg += " 🎉 O Herói subiu de nível!"

        return WebhookEventResponse(
            success=True,
            event_type="GITHUB_PULL_REQUEST",
            message=msg,
            reward_hero_xp=result_card.reward.hero_xp if result_card.reward else None,
            reward_guild_xp=result_card.reward.guild_xp if result_card.reward else None,
        )

    # 2. Eventos de Code Review (Bênção do Guardião)
    if event.event_type == "pull_request_review":
        if event.is_review_approved:
            cmd_review = GitHubWebhookParser.to_code_review_command(event, effective_guild_id)
            result_review = await container.process_code_review_use_case.execute(cmd_review)

            msg = (
                f"🛡️ Bênção do Guardião concedida a {result_review.hero.name if result_review.hero else 'Revisor'}! "
                f"+{result_review.xp_awarded} XP de Code Review."
            )
            if result_review.hero_leveled_up:
                msg += " 🎉 O Guardião subiu de nível!"

            return WebhookEventResponse(
                success=True,
                event_type="GITHUB_CODE_REVIEW",
                message=msg,
                reward_hero_xp=result_review.xp_awarded,
                reward_guild_xp=result_review.xp_awarded // 2,
            )

        return WebhookEventResponse(
            success=True,
            event_type="GITHUB_CODE_REVIEW_IGNORED",
            message=f"Revisão de código com estado '{event.review_state}' ignorada (apenas aprovações geram Bênção).",
        )

    # 3. Eventos de Issues
    if event.event_type == "issues":
        if event.is_bug:
            cmd_bug = GitHubWebhookParser.to_bug_command(event, effective_guild_id)
            result_bug = await container.process_bug_use_case.execute(cmd_bug)

            if result_bug.is_defeated:
                msg = f"Mini-Boss [{event.identifier}] derrotado via GitHub Issue! +{result_bug.bounty_hero_xp} XP ao herói e +{result_bug.bounty_guild_xp} XP à Guilda!"
            else:
                msg = f"Mini-Boss [{event.identifier}] ({event.severity.value}) invadiu a Guilda via GitHub Issue!"

            return WebhookEventResponse(
                success=True,
                event_type="GITHUB_BUG",
                message=msg,
                reward_hero_xp=result_bug.bounty_hero_xp if result_bug.is_defeated else None,
                reward_guild_xp=result_bug.bounty_guild_xp if result_bug.is_defeated else None,
            )

        # Issue comum tratada como Quest
        cmd_card = GitHubWebhookParser.to_card_command(event, effective_guild_id)
        result_card = await container.process_card_use_case.execute(cmd_card)
        msg = f"GitHub Issue [{event.identifier}] processada com status '{event.status.value}'."
        if result_card.reward:
            msg += f" Recompensa: +{result_card.reward.hero_xp} XP herói, +{result_card.reward.guild_xp} XP guilda."

        return WebhookEventResponse(
            success=True,
            event_type="GITHUB_ISSUE_QUEST",
            message=msg,
            reward_hero_xp=result_card.reward.hero_xp if result_card.reward else None,
            reward_guild_xp=result_card.reward.guild_xp if result_card.reward else None,
        )

    # Outros eventos não tratados
    return WebhookEventResponse(
        success=True,
        event_type="GITHUB_IGNORED",
        message=f"Evento GitHub '{event.event_type}' recebido e ignorado.",
    )
