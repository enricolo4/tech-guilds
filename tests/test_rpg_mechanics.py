import unittest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from tech_guilds.domain.entities.hero import Hero, HeroClass, HeroStats
from tech_guilds.domain.entities.guild import Guild
from tech_guilds.domain.entities.mini_boss import MiniBoss, BossSeverity
from tech_guilds.domain.entities.item import (
    Item,
    ItemType,
    Equipment,
    EquipmentSlot,
    create_weapon,
    create_armor,
    create_shield,
    create_charm,
)
from tech_guilds.domain.entities.skill import (
    Skill,
    BRUTAL_REFACTOR,
    SCRIPT_AUTOMATION,
    CICD_SHIELD,
    EDGE_CASE_STRIKE,
    SPRINT_RALLY,
)
from tech_guilds.domain.entities.shop import (
    ShopItem,
    ShopCategory,
    PurchaseTarget,
    PERK_COFFEE_BUDGET,
    PERK_TEAM_DINNER,
    SKIN_CYBERPUNK,
    SKIN_DARK_MODE,
    SHOP_WEAPON_KEYBOARD,
    SHOP_ARMOR_HOODIE,
    SHOP_SHIELD_DOCKER,
    SHOP_CHARM_RUBBER_DUCK,
)
from tech_guilds.domain.use_cases.equip_item import (
    EquipItemUseCase,
    EquipItemCommand,
    UnequipItemCommand,
)
from tech_guilds.domain.use_cases.cast_skill import (
    CastSkillUseCase,
    CastSkillCommand,
)
from tech_guilds.domain.use_cases.purchase_shop_item import (
    PurchaseShopItemUseCase,
    PurchaseShopItemCommand,
)
from tech_guilds.secondary.postgresql.database import init_models
from tech_guilds.secondary.postgresql.repositories.repositories_impl import (
    InMemoryHeroRepository,
    InMemoryGuildRepository,
    InMemoryMiniBossRepository,
)
from tech_guilds.secondary.postgresql.repositories.postgres_repositories import (
    PostgresHeroRepository,
    PostgresGuildRepository,
)


class TestTechGuildsRPGMechanics(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.hero_repo = InMemoryHeroRepository()
        self.guild_repo = InMemoryGuildRepository()
        self.boss_repo = InMemoryMiniBossRepository()

    # =========================================================================
    # 1. TESTES DE ITENS E EQUIPAMENTOS (Weapons, Armors, Shields, Charms)
    # =========================================================================

    async def test_equipment_slots_and_stat_boosts(self):
        """Verifica a criação e os bônus de atributos para todas as categorias de equipamentos."""
        weapon = create_weapon("Katana de Código Limpo", "Refatora tudo", 100, strength=8, intelligence=2)
        armor = create_armor("Manto de Deploy", "Resistente a falhas", 80, constitution=10, perception=3)
        shield = create_shield("Escudo Redundante", "Tolerante a falhas", 90, constitution=7, strength=3)
        charm = create_charm("Pato de Borracha Lendário", "Ouve suas dúvidas", 50, perception=6, intelligence=6)

        self.assertEqual(weapon.slot, EquipmentSlot.WEAPON)
        self.assertEqual(weapon.bonus_stats.strength, 8)
        self.assertEqual(weapon.bonus_stats.intelligence, 2)

        self.assertEqual(armor.slot, EquipmentSlot.ARMOR)
        self.assertEqual(armor.bonus_stats.constitution, 10)

        self.assertEqual(shield.slot, EquipmentSlot.SHIELD)
        self.assertEqual(shield.bonus_stats.constitution, 7)
        self.assertEqual(shield.bonus_stats.strength, 3)

        self.assertEqual(charm.slot, EquipmentSlot.CHARM)
        self.assertEqual(charm.bonus_stats.perception, 6)
        self.assertEqual(charm.bonus_stats.intelligence, 6)

    async def test_equip_and_unequip_item_updates_hero_stats(self):
        """Testa o EquipItemUseCase equipando e desequipando itens, verificando reflexo nos atributos."""
        hero = Hero(email="arthur@company.com", name="Arthur", hero_class=HeroClass.WARRIOR_BACKEND)
        # Stats iniciais: STR 10 (base) + 5 (classe Warrior) = 15
        hero.assign_class(HeroClass.WARRIOR_BACKEND)
        await self.hero_repo.save(hero)

        base_str = hero.stats.strength
        base_int = hero.stats.intelligence

        equip_use_case = EquipItemUseCase(self.hero_repo)

        # 1. Equipa Arma (+8 STR, +2 INT)
        weapon = create_weapon("Espada Git Rebase", "Refatora histórico", 100, strength=8, intelligence=2)
        res_equip = await equip_use_case.execute(EquipItemCommand(hero_id=hero.id, equipment=weapon))

        self.assertEqual(res_equip.hero.stats.strength, base_str + 8)
        self.assertEqual(res_equip.hero.stats.intelligence, base_int + 2)
        self.assertIn(EquipmentSlot.WEAPON.value, res_equip.hero.equipped_gear)

        # 2. Substitui a arma por uma mais poderosa (+12 STR, +0 INT)
        better_weapon = create_weapon("Martelo de Monorepo", "Destrói conflitos", 150, strength=12, intelligence=0)
        res_swap = await equip_use_case.execute(EquipItemCommand(hero_id=hero.id, equipment=better_weapon))

        self.assertEqual(res_swap.hero.stats.strength, base_str + 12)
        self.assertEqual(res_swap.hero.stats.intelligence, base_int)  # O bônus da antiga arma foi removido
        self.assertIsNotNone(res_swap.unequipped_item)
        self.assertEqual(res_swap.unequipped_item.name, "Espada Git Rebase")

        # 3. Desequipa a arma
        res_unequip = await equip_use_case.unequip(UnequipItemCommand(hero_id=hero.id, slot=EquipmentSlot.WEAPON))
        self.assertEqual(res_unequip.hero.stats.strength, base_str)
        self.assertEqual(res_unequip.hero.stats.intelligence, base_int)
        self.assertNotIn(EquipmentSlot.WEAPON.value, res_unequip.hero.equipped_gear)

    async def test_equip_restrictions_level_and_class(self):
        """Valida que requisitos de nível e classe impedem o herói de equipar itens indevidos."""
        hero = Hero(email="junior@company.com", name="Junior Dev", level=1, hero_class=HeroClass.MAGE_FRONTEND)
        await self.hero_repo.save(hero)

        equip_use_case = EquipItemUseCase(self.hero_repo)

        # Item de nível alto
        high_lvl_armor = create_armor("Armadura de Arquiteto", "Exige Nível 5", 200, constitution=20, required_level=5)
        with self.assertRaises(ValueError) as ctx_level:
            await equip_use_case.execute(hero.id, high_lvl_armor)
        self.assertIn("lower than required level", str(ctx_level.exception))

        # Item restrito à classe Warrior
        warrior_shield = create_shield(
            "Escudo de Carga Pesada",
            "Apenas guerreiros",
            100,
            constitution=10,
            allowed_class=HeroClass.WARRIOR_BACKEND,
        )
        with self.assertRaises(ValueError) as ctx_class:
            await equip_use_case.execute(hero.id, warrior_shield)
        self.assertIn("cannot equip item allowed only for", str(ctx_class.exception))

    # =========================================================================
    # 2. TESTES DE HABILIDADES DE CLASSE (CastSkillUseCase)
    # =========================================================================

    async def test_warrior_skill_brutal_refactor_boss_damage(self):
        """Warrior conjura Brutal Refactor causando alto dano contra o Mini-Boss."""
        guild = Guild(name="Backend Squad")
        await self.guild_repo.save(guild)

        warrior = Hero(
            email="warrior@company.com",
            name="Ragnar",
            hero_class=HeroClass.WARRIOR_BACKEND,
            guild_id=guild.id,
            mana=100,
        )
        warrior.assign_class(HeroClass.WARRIOR_BACKEND)
        await self.hero_repo.save(warrior)

        boss = MiniBoss(
            external_id="BUG-101",
            title="Deadlock no PostgreSQL",
            guild_id=guild.id,
            max_health=100,
            current_health=100,
            bounty_hero_xp=50,
            bounty_gold=30,
        )
        await self.boss_repo.save(boss)

        cast_use_case = CastSkillUseCase(
            hero_repo=self.hero_repo,
            boss_repo=self.boss_repo,
            guild_repo=self.guild_repo,
        )

        cmd = CastSkillCommand(
            hero_id=warrior.id,
            skill_id="BRUTAL_REFACTOR",
            target_boss_id=boss.id,
        )
        result = await cast_use_case.execute(cmd)

        self.assertTrue(result.success)
        self.assertGreater(result.damage_dealt, 60)
        self.assertTrue(result.boss_defeated)

        # Mana consumida (100 - 30 = 70)
        updated_warrior = await self.hero_repo.get_by_id(warrior.id)
        self.assertEqual(updated_warrior.mana, 70)
        self.assertTrue(updated_warrior.is_skill_on_cooldown("BRUTAL_REFACTOR"))

        # Recompensa do Boss derrotado foi creditada
        self.assertEqual(updated_warrior.gold, 30)
        self.assertGreater(updated_warrior.experience, 0)

    async def test_mage_skill_script_automation_exp_multiplier(self):
        """Mage conjura Script Automation ativando multiplicador de ganho de EXP."""
        mage = Hero(
            email="mage@company.com",
            name="Merlin",
            hero_class=HeroClass.MAGE_FRONTEND,
            mana=100,
        )
        mage.assign_class(HeroClass.MAGE_FRONTEND)
        await self.hero_repo.save(mage)

        cast_use_case = CastSkillUseCase(hero_repo=self.hero_repo)
        cmd = CastSkillCommand(hero_id=mage.id, skill_id="SCRIPT_AUTOMATION")
        result = await cast_use_case.execute(cmd)

        self.assertTrue(result.success)
        self.assertGreaterEqual(result.exp_multiplier, 2.0)

        # Verifica se o herói ganhou o buff e se o ganho de EXP respeita o multiplicador
        updated_mage = await self.hero_repo.get_by_id(mage.id)
        self.assertEqual(updated_mage.mana, 75)  # 100 - 25
        self.assertEqual(updated_mage.active_buffs.get("exp_multiplier"), result.exp_multiplier)

        # Ganha 50 EXP com multiplicador 2x+ -> deve somar bem mais de 100 EXP e subir de nível!
        leveled = updated_mage.gain_experience(50)
        self.assertTrue(leveled)
        self.assertEqual(updated_mage.level, 2)

    async def test_paladin_skill_cicd_shield_reduces_squad_damage(self):
        """Paladin ergue CI/CD Shield, aplicando redução de dano e pontos de escudo à Guilda."""
        guild = Guild(name="SRE Devops Squad")
        await self.guild_repo.save(guild)

        paladin = Hero(
            email="sre@company.com",
            name="Galahad",
            hero_class=HeroClass.PALADIN_DEVOPS,
            guild_id=guild.id,
            mana=100,
        )
        paladin.assign_class(HeroClass.PALADIN_DEVOPS)
        await self.hero_repo.save(paladin)

        cast_use_case = CastSkillUseCase(hero_repo=self.hero_repo, guild_repo=self.guild_repo)
        cmd = CastSkillCommand(hero_id=paladin.id, skill_id="CICD_SHIELD", target_guild_id=guild.id)
        result = await cast_use_case.execute(cmd)

        self.assertTrue(result.success)
        self.assertGreaterEqual(result.squad_damage_reduction, 0.40)

        updated_guild = await self.guild_repo.get_by_id(guild.id)
        self.assertGreater(updated_guild.shield_points, 50)
        self.assertIn("damage_reduction", updated_guild.active_buffs)

        # Testa a absorção de dano do Squad (dano de 60 mitigado pelo escudo e porcentagem)
        real_damage = updated_guild.take_damage(60)
        self.assertEqual(real_damage, 0)  # O escudo absorveu completamente!

    async def test_ranger_skill_edge_case_strike_critical_bug_damage(self):
        """Ranger conjura Edge Case Strike com acerto crítico letal no Bug."""
        guild = Guild(name="QA Elite Squad")
        await self.guild_repo.save(guild)

        ranger = Hero(
            email="qa@company.com",
            name="Robin",
            hero_class=HeroClass.RANGER_QA,
            guild_id=guild.id,
            mana=100,
        )
        ranger.assign_class(HeroClass.RANGER_QA)
        await self.hero_repo.save(ranger)

        boss = MiniBoss(
            external_id="BUG-202",
            title="NullPointer em Edge Case de autenticação",
            guild_id=guild.id,
            max_health=200,
            current_health=200,
        )
        await self.boss_repo.save(boss)

        cast_use_case = CastSkillUseCase(hero_repo=self.hero_repo, boss_repo=self.boss_repo)
        cmd = CastSkillCommand(hero_id=ranger.id, skill_id="EDGE_CASE_STRIKE", target_boss_id=boss.id)
        result = await cast_use_case.execute(cmd)

        self.assertTrue(result.success)
        # Crítico de 2.5x em cima de (80 + 15 * 2) = 2.5 * 110 = 275 de dano
        self.assertGreater(result.damage_dealt, 200)
        self.assertTrue(result.boss_defeated)

    async def test_tactician_skill_sprint_rally_squad_exp(self):
        """Tactician conjura Sprint Rally concedendo EXP e bônus coletivo ao Squad."""
        guild = Guild(name="Squad Alpha", experience=0, level=1)
        await self.guild_repo.save(guild)

        tactician = Hero(
            email="lead@company.com",
            name="Athena",
            hero_class=HeroClass.TACTICIAN_TL,
            guild_id=guild.id,
            mana=100,
        )
        tactician.assign_class(HeroClass.TACTICIAN_TL)
        await self.hero_repo.save(tactician)

        cast_use_case = CastSkillUseCase(hero_repo=self.hero_repo, guild_repo=self.guild_repo)
        cmd = CastSkillCommand(hero_id=tactician.id, skill_id="SPRINT_RALLY", target_guild_id=guild.id)
        result = await cast_use_case.execute(cmd)

        self.assertTrue(result.success)
        self.assertGreater(result.squad_exp_buff, 100)

        updated_guild = await self.guild_repo.get_by_id(guild.id)
        self.assertGreater(updated_guild.experience, 100)
        self.assertEqual(updated_guild.active_buffs.get("squad_exp_multiplier"), 1.3)

    async def test_cast_skill_validations_class_mana_and_cooldown(self):
        """Valida que restrições de classe, mana insuficiente e tempo de recarga barram a conjuração."""
        hero = Hero(email="novice@company.com", name="Novato", hero_class=HeroClass.NOVICE, mana=10)
        await self.hero_repo.save(hero)

        cast_use_case = CastSkillUseCase(hero_repo=self.hero_repo)

        # 1. Classe incorreta (Novato tentando lançar Brutal Refactor de Guerreiro)
        with self.assertRaises(ValueError) as ctx_class:
            await cast_use_case.execute(hero.id, "BRUTAL_REFACTOR")
        self.assertIn("cannot cast", str(ctx_class.exception))

        # Altera para Guerreiro
        hero.assign_class(HeroClass.WARRIOR_BACKEND)
        await self.hero_repo.save(hero)

        # 2. Mana insuficiente (tem 10, precisa de 30)
        with self.assertRaises(ValueError) as ctx_mana:
            await cast_use_case.execute(hero.id, "BRUTAL_REFACTOR")
        self.assertIn("Insufficient mana", str(ctx_mana.exception))

        # Restaura mana
        hero.restore_mana(100)
        hero.set_skill_cooldown("BRUTAL_REFACTOR", 2)
        await self.hero_repo.save(hero)

        # 3. Em tempo de recarga (Cooldown)
        with self.assertRaises(ValueError) as ctx_cd:
            await cast_use_case.execute(hero.id, "BRUTAL_REFACTOR")
        self.assertIn("is on cooldown", str(ctx_cd.exception))

        # Avança tempo de recarga
        hero.tick_cooldowns()
        self.assertTrue(hero.is_skill_on_cooldown("BRUTAL_REFACTOR"))
        hero.tick_cooldowns()
        self.assertFalse(hero.is_skill_on_cooldown("BRUTAL_REFACTOR"))

    # =========================================================================
    # 3. TESTES DE COMPRA NO MERCADO E PERKS DO TESOURO DA GUILDA
    # =========================================================================

    async def test_purchase_equipment_with_hero_gold(self):
        """Herói compra equipamento com seu próprio ouro e adiciona ao seu inventário."""
        hero = Hero(email="buyer@company.com", name="Dev Shopper", gold=200)
        await self.hero_repo.save(hero)

        shop_use_case = PurchaseShopItemUseCase(hero_repo=self.hero_repo, guild_repo=self.guild_repo)

        cmd = PurchaseShopItemCommand(item_id="WEAPON_MECHANICAL_KEYBOARD", hero_id=hero.id)
        result = await shop_use_case.execute(cmd)

        self.assertFalse(result.paid_from_treasury)
        self.assertEqual(result.gold_spent, 120)

        updated_hero = await self.hero_repo.get_by_id(hero.id)
        self.assertEqual(updated_hero.gold, 80)  # 200 - 120
        self.assertEqual(len(updated_hero.inventory), 1)
        self.assertEqual(updated_hero.inventory[0].slot, EquipmentSlot.WEAPON)

    async def test_purchase_custom_skin_with_hero_gold(self):
        """Herói adquire skins cosméticas (Cyberpunk, Dark Mode) e atualiza seu avatar."""
        hero = Hero(email="stylish@company.com", name="Stylish Dev", gold=150)
        await self.hero_repo.save(hero)

        shop_use_case = PurchaseShopItemUseCase(hero_repo=self.hero_repo, guild_repo=self.guild_repo)

        cmd = PurchaseShopItemCommand(item_id="SKIN_CYBERPUNK", hero_id=hero.id)
        result = await shop_use_case.execute(cmd)

        self.assertEqual(result.gold_spent, 100)
        updated_hero = await self.hero_repo.get_by_id(hero.id)
        self.assertEqual(updated_hero.gold, 50)
        self.assertIn("cyberpunk_hacker", updated_hero.unlocked_skins)
        self.assertEqual(updated_hero.avatar_url, "/skins/cyberpunk_hacker.png")

    async def test_purchase_guild_treasury_perk_coffee_budget(self):
        """Squad adquire Coffee Budget pelo Tesouro da Guilda, restaurando mana do time."""
        guild = Guild(name="Squad Coffee Lovers", treasury_gold=300)
        await self.guild_repo.save(guild)

        hero = Hero(email="thirsty@company.com", name="Thirsty Dev", guild_id=guild.id, mana=20, max_mana=100)
        await self.hero_repo.save(hero)

        shop_use_case = PurchaseShopItemUseCase(hero_repo=self.hero_repo, guild_repo=self.guild_repo)

        cmd = PurchaseShopItemCommand(
            item_id="COFFEE_BUDGET",
            guild_id=guild.id,
            hero_id=hero.id,
            use_treasury=True,
        )
        result = await shop_use_case.execute(cmd)

        self.assertTrue(result.paid_from_treasury)
        self.assertEqual(result.gold_spent, 150)

        updated_guild = await self.guild_repo.get_by_id(guild.id)
        self.assertEqual(updated_guild.treasury_gold, 150)  # 300 - 150
        self.assertIn("Coffee Budget", updated_guild.purchased_perks)

        # O herói teve mana restaurada pelo café (+30 mana)
        updated_hero = await self.hero_repo.get_by_id(hero.id)
        self.assertEqual(updated_hero.mana, 50)

    async def test_purchase_guild_treasury_perk_team_dinner(self):
        """Squad adquire Team Dinner Perk com o tesouro da Guilda, concedendo EXP coletiva."""
        guild = Guild(name="Squad Celebration", treasury_gold=800, experience=50)
        await self.guild_repo.save(guild)

        shop_use_case = PurchaseShopItemUseCase(hero_repo=self.hero_repo, guild_repo=self.guild_repo)

        cmd = PurchaseShopItemCommand(item_id="TEAM_DINNER", guild_id=guild.id, use_treasury=True)
        result = await shop_use_case.execute(cmd)

        self.assertTrue(result.paid_from_treasury)
        self.assertEqual(result.gold_spent, 500)

        updated_guild = await self.guild_repo.get_by_id(guild.id)
        self.assertEqual(updated_guild.treasury_gold, 300)  # 800 - 500
        self.assertIn("Team Dinner Perk", updated_guild.purchased_perks)
        self.assertGreater(updated_guild.experience, 300)  # Ganhou +300 EXP coletiva

    async def test_purchase_shop_item_insufficient_funds_fails(self):
        """Verifica que compras sem ouro suficiente no herói ou no tesouro falham com erro explícito."""
        guild = Guild(name="Broke Squad", treasury_gold=50)
        await self.guild_repo.save(guild)

        hero = Hero(email="broke@company.com", name="Broke Dev", gold=10, guild_id=guild.id)
        await self.hero_repo.save(hero)

        shop_use_case = PurchaseShopItemUseCase(hero_repo=self.hero_repo, guild_repo=self.guild_repo)

        # 1. Falha pessoal: Herói tem 10 gold e tenta comprar item de 120
        with self.assertRaises(ValueError) as ctx_hero:
            await shop_use_case.execute("WEAPON_MECHANICAL_KEYBOARD", hero_id=hero.id)
        self.assertIn("Insufficient hero gold", str(ctx_hero.exception))

        # 2. Falha de tesouro: Guilda tem 50 gold e tenta comprar Coffee Budget de 150
        with self.assertRaises(ValueError) as ctx_treasury:
            await shop_use_case.execute("COFFEE_BUDGET", guild_id=guild.id, use_treasury=True)
        self.assertIn("Insufficient guild treasury gold", str(ctx_treasury.exception))

    # =========================================================================
    # 4. INTEGRAÇÃO COM BANCO DE DADOS (PostgreSQL / SQLite assíncrono)
    # =========================================================================

    async def test_rpg_postgres_persistence_integration(self):
        """Valida que mana, atributos de RPG, escudos e perks são persistidos e recuperados no banco."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        await init_models(engine)

        session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

        async with session_maker() as session:
            pg_hero_repo = PostgresHeroRepository(session)
            pg_guild_repo = PostgresGuildRepository(session)

            # Salva guilda com escudos e perks
            guild = Guild(
                name="Squad High Performance",
                shield_points=120,
                purchased_perks=["Coffee Budget", "Team Dinner Perk"],
            )
            saved_guild = await pg_guild_repo.save(guild)

            # Salva herói com atributos de RPG avançados, mana e skins
            hero = Hero(
                email="database.dev@company.com",
                name="Neo",
                guild_id=saved_guild.id,
                hero_class=HeroClass.MAGE_FRONTEND,
                level=4,
                mana=85,
                max_mana=130,
                stats=HeroStats(strength=15, intelligence=25, constitution=14, perception=16),
                unlocked_skins=["cyberpunk_hacker", "dark_mode_terminal"],
            )
            await pg_hero_repo.save(hero)
            await session.commit()

            # Recupera e valida integridade dos dados
            loaded_hero = await pg_hero_repo.get_by_email("database.dev@company.com")
            self.assertIsNotNone(loaded_hero)
            self.assertEqual(loaded_hero.mana, 85)
            self.assertEqual(loaded_hero.max_mana, 130)
            self.assertEqual(loaded_hero.stats.intelligence, 25)
            self.assertEqual(loaded_hero.stats.perception, 16)
            self.assertIn("cyberpunk_hacker", loaded_hero.unlocked_skins)

            loaded_guild = await pg_guild_repo.get_by_id(saved_guild.id)
            self.assertIsNotNone(loaded_guild)
            self.assertEqual(loaded_guild.shield_points, 120)
            self.assertIn("Coffee Budget", loaded_guild.purchased_perks)

        await engine.dispose()


if __name__ == "__main__":
    unittest.main()
