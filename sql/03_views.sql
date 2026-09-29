create or replace view public.vw_lista_portaria as
select
    r.id as rsvp_id,
    upper(trim(r.nome_principal)) as nome,
    'CONVIDADO PRINCIPAL' as tipo,
    r.criado_em
from public.rsvps r
where r.vai_comparecer = true
  and r.status = 'confirmado'

union all

select
    a.rsvp_id,
    upper(trim(a.nome_completo)) as nome,
    'ACOMPANHANTE' as tipo,
    r.criado_em
from public.rsvp_acompanhantes a
join public.rsvps r
    on r.id = a.rsvp_id
where r.vai_comparecer = true
  and r.status = 'confirmado';

-- Controle administrativo: estimativa baseada nos metadados gravados pelo app.
-- NAO equivale a quota oficial do Supabase nem inclui arquivos orfaos/outros buckets.
create or replace view public.vw_uso_fotos
with (security_invoker = true) as
select
    'historicas'::text as categoria,
    count(*)::bigint as fotos,
    coalesce(sum(thumb_bytes), 0)::bigint as bytes_reduzidas,
    coalesce(sum(display_bytes), 0)::bigint as bytes_exibicao,
    0::bigint as bytes_originais
from public.fotos_historicas
union all
select
    'memorias_festa'::text as categoria,
    count(*)::bigint as fotos,
    0::bigint as bytes_reduzidas,
    coalesce(sum(display_bytes), 0)::bigint as bytes_exibicao,
    coalesce(sum(case when status_arquivo <> 'removido' then original_bytes else 0 end), 0)::bigint as bytes_originais
from public.memorias_festa;

-- Nao disponibilizar nomes, caminhos ou estimativa via chave publica da API.
alter table public.fotos_historicas enable row level security;
alter table public.memorias_festa enable row level security;
revoke all on public.fotos_historicas from anon, authenticated;
revoke all on public.memorias_festa from anon, authenticated;
revoke all on public.vw_uso_fotos from anon, authenticated;

commit;

-- Consultas administrativas (SQL Editor ou backend protegido do Streamlit):
-- select * from public.vw_uso_fotos;
-- select id, nome_convidado, status_publicacao, status_arquivo,
--        original_bytes, display_bytes, criado_em
-- from public.memorias_festa order by criado_em desc;
-- Nao execute DELETE em storage.objects: use a Storage API e confirme backup
-- antes de marcar status_arquivo='removido' e original_path=NULL.