-- RAPHA 40 | Metadados de fotos historicas e memorias enviadas
-- Executar no SQL Editor do projeto rapha-40anos.
-- NAO altera rsvps, rsvp_acompanhantes nem vw_lista_portaria.
-- Criar os buckets PRIVADOS mural-historico, memorias-originais e memorias-mural
-- no painel Storage do Supabase antes de enviar imagens.
-- Enviar, baixar e excluir objetos exclusivamente pela Storage API.

begin;

create table if not exists public.fotos_historicas (
    id uuid primary key default gen_random_uuid(),
    titulo text not null check (length(btrim(titulo)) between 1 and 120),
    legenda text,
    ano smallint check (ano between 1900 and 2100),
    thumb_path text not null unique check (length(btrim(thumb_path)) > 0),
    display_path text not null unique check (length(btrim(display_path)) > 0),
    thumb_bytes bigint check (thumb_bytes >= 0),
    display_bytes bigint check (display_bytes >= 0),
    ordem integer not null default 0,
    ativo boolean not null default true,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create index if not exists idx_fotos_historicas_ativas_ordem
    on public.fotos_historicas (ordem, criado_em)
    where ativo = true;

create table if not exists public.memorias_festa (
    id uuid primary key default gen_random_uuid(),
    nome_convidado text,
    frase text check (frase is null or length(frase) <= 280),
    original_path text unique,
    original_nome text,
    original_mime text,
    original_bytes bigint check (original_bytes >= 0),
    original_sha256 text check (
        original_sha256 is null
        or original_sha256 ~ '^[0-9a-fA-F]{64}$'
    ),
    display_path text not null unique check (length(btrim(display_path)) > 0),
    display_bytes bigint check (display_bytes >= 0),
    status_publicacao text not null default 'pendente'
        check (status_publicacao in ('pendente', 'aprovado', 'rejeitado')),
    status_arquivo text not null default 'no_supabase'
        check (status_arquivo in ('no_supabase', 'exportado', 'verificado', 'removido')),
    destino_backup text check (destino_backup in ('drive', 'celular', 'computador', 'outro')),
    referencia_backup text,
    exportado_em timestamptz,
    verificado_em timestamptz,
    original_removido_em timestamptz,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now(),
    constraint ck_memoria_original_ativo check (
        status_arquivo = 'removido' or original_path is not null
    ),
    constraint ck_memoria_remocao_verificada check (
        status_arquivo <> 'removido'
        or (verificado_em is not null and original_removido_em is not null)
    )
);

create index if not exists idx_memorias_festa_publicacao
    on public.memorias_festa (status_publicacao, criado_em desc);

create index if not exists idx_memorias_festa_arquivo
    on public.memorias_festa (status_arquivo, criado_em desc);