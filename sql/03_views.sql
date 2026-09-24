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