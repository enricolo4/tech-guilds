-- Inicialização dos Schemas isolados dos Microsserviços do Tech Guilds
CREATE SCHEMA IF NOT EXISTS registration;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS guilds;
CREATE SCHEMA IF NOT EXISTS gamification;

-- Garantir privilégios
GRANT ALL ON SCHEMA registration TO postgres;
GRANT ALL ON SCHEMA auth TO postgres;
GRANT ALL ON SCHEMA guilds TO postgres;
GRANT ALL ON SCHEMA gamification TO postgres;
