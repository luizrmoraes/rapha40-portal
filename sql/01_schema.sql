create extension if not exists pgcrypto;

create table if not exists public.rsvps (
    id uuid primary key default gen_random_uuid(),
    nome_principal text not null,
    vai_comparecer boolean not null,
    quantidade_criancas integer not null default 0
        check (quantidade_criancas >= 0),
    status text not null default 'confirmado'
        check (status in ('confirmado', 'recusado', 'cancelado')),
    origem text not null default 'portal',
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.rsvp_acompanhantes (
    id uuid primary key default gen_random_uuid(),
    rsvp_id uuid not null
        references public.rsvps(id)
        on delete cascade,
    nome_completo text not null,
    criado_em timestamptz not null default now()
);

create index if not exists idx_rsvps_nome_principal
    on public.rsvps (nome_principal);

create index if not exists idx_rsvp_acompanhantes_rsvp_id
    on public.rsvp_acompanhantes (rsvp_id);