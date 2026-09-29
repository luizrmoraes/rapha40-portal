"""Repositorios PostgreSQL do portal Rapha 40."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar
from uuid import UUID

from psycopg2.extras import RealDictCursor

from core.database import executar_db, executar_leitura

T = TypeVar("T")


def _buscar(sql: str, parametros: tuple[Any, ...] = (), *, um: bool = False):
    def operacao(connection):
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, parametros)
            if um:
                linha = cursor.fetchone()
                return dict(linha) if linha else None
            return [dict(linha) for linha in cursor.fetchall()]

    return executar_leitura(operacao)


def _alterar(sql: str, parametros: tuple[Any, ...]) -> dict[str, Any] | None:
    def operacao(connection):
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, parametros)
            linha = cursor.fetchone()
            return dict(linha) if linha else None

    return executar_db(operacao)


def criar_rsvp(
    nome_principal: str,
    vai_comparecer: bool,
    quantidade_criancas: int = 0,
    acompanhantes: list[str] | None = None,
) -> str:
    nome = nome_principal.strip()
    nomes = [nome_item.strip() for nome_item in (acompanhantes or [])]
    if len(nome) < 3:
        raise ValueError("Informe o nome completo.")
    if not isinstance(vai_comparecer, bool):
        raise ValueError("Presença inválida.")
    if any(len(nome_item) < 3 for nome_item in nomes):
        raise ValueError("Informe o nome completo de cada acompanhante.")
    if not vai_comparecer and (nomes or quantidade_criancas):
        raise ValueError("Recusas não podem incluir acompanhantes ou crianças.")
    if not isinstance(quantidade_criancas, int) or quantidade_criancas < 0:
        raise ValueError("Quantidade de crianças inválida.")

    def operacao(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                insert into public.rsvps
                    (nome_principal, vai_comparecer, quantidade_criancas, status, origem)
                values (%s, %s, %s, %s, 'portal')
                returning id;
                """,
                (
                    nome,
                    vai_comparecer,
                    quantidade_criancas,
                    "confirmado" if vai_comparecer else "recusado",
                ),
            )
            rsvp_id = cursor.fetchone()[0]
            for acompanhante in nomes:
                cursor.execute(
                    """
                    insert into public.rsvp_acompanhantes (rsvp_id, nome_completo)
                    values (%s, %s);
                    """,
                    (rsvp_id, acompanhante),
                )
            return str(rsvp_id)

    return executar_db(operacao)


def carregar_lista_portaria() -> list[dict[str, Any]]:
    return _buscar(
        "select nome, tipo from public.vw_lista_portaria order by nome, tipo;"
    )


def carregar_resumo() -> dict[str, Any]:
    return _buscar(
        """
        select
            (select count(*) from public.rsvps) as respostas,
            (select count(*) from public.vw_lista_portaria) as confirmados,
            (select count(*) from public.rsvps
             where vai_comparecer = false and status = 'recusado') as recusados,
            (select coalesce(sum(quantidade_criancas), 0) from public.rsvps
             where vai_comparecer = true and status = 'confirmado') as criancas;
        """,
        um=True,
    )


def listar_fotos_historicas(
    *, somente_ativas: bool = True, mais_recentes: bool = False
) -> list[dict[str, Any]]:
    direcao = "desc" if mais_recentes else "asc"
    return _buscar(
        f"""
        select id, titulo, legenda, ano, mes, data_estimada,
               thumb_path, display_path, thumb_bytes, display_bytes,
               ordem, ativo, criado_em
        from public.fotos_historicas
        where (%s = false or ativo = true)
        order by (ano is null) asc, ano {direcao},
                 coalesce(mes, 0) {direcao}, ordem asc,
                 criado_em asc, id asc;
        """,
        (somente_ativas,),
    )


def listar_memorias_aprovadas(*, limite: int = 100) -> list[dict[str, Any]]:
    if not 1 <= limite <= 500:
        raise ValueError("Limite deve estar entre 1 e 500.")
    return _buscar(
        """
        select id, nome_convidado, frase, display_path, criado_em
        from public.memorias_festa
        where status_publicacao = 'aprovado'
        order by criado_em desc, id desc
        limit %s;
        """,
        (limite,),
    )


def listar_memorias_admin(*, limite: int = 200) -> list[dict[str, Any]]:
    if not 1 <= limite <= 500:
        raise ValueError("Limite deve estar entre 1 e 500.")
    return _buscar(
        """
        select id, nome_convidado, frase, original_path, original_nome,
               original_mime, original_bytes, original_sha256,
               display_path, display_bytes, status_publicacao, status_arquivo,
               destino_backup, referencia_backup, exportado_em,
               verificado_em, original_removido_em, criado_em
        from public.memorias_festa
        order by criado_em desc, id desc
        limit %s;
        """,
        (limite,),
    )


def listar_memorias_pendentes(*, limite: int = 200) -> list[dict[str, Any]]:
    if not 1 <= limite <= 500:
        raise ValueError("Limite deve estar entre 1 e 500.")
    return _buscar(
        """
        select id, nome_convidado, frase, display_path, criado_em
        from public.memorias_festa
        where status_publicacao = 'pendente'
        order by criado_em asc, id asc
        limit %s;
        """,
        (limite,),
    )


def carregar_uso_fotos() -> list[dict[str, Any]]:
    return _buscar(
        """
        select categoria, fotos, bytes_reduzidas, bytes_exibicao, bytes_originais
        from public.vw_uso_fotos order by categoria;
        """
    )


def criar_memoria(
    *, nome_convidado: str | None, frase: str | None,
    original_path: str, original_nome: str, original_mime: str,
    original_bytes: int, original_sha256: str,
    display_path: str, display_bytes: int,
) -> str:
    if not original_path or not display_path or not original_nome:
        raise ValueError("Caminhos e nome do original são obrigatórios.")
    if original_bytes <= 0 or display_bytes <= 0:
        raise ValueError("Tamanhos dos arquivos devem ser positivos.")
    if len(original_sha256) != 64 or any(
        caractere not in "0123456789abcdefABCDEF" for caractere in original_sha256
    ):
        raise ValueError("SHA-256 inválido.")
    if frase is not None and len(frase) > 280:
        raise ValueError("Frase deve ter até 280 caracteres.")

    linha = _alterar(
        """
        insert into public.memorias_festa
            (nome_convidado, frase, original_path, original_nome,
             original_mime, original_bytes, original_sha256,
             display_path, display_bytes)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        returning id;
        """,
        (
            nome_convidado.strip() or None if nome_convidado is not None else None,
            frase.strip() or None if frase is not None else None,
            original_path, original_nome, original_mime, original_bytes,
            original_sha256.lower(), display_path, display_bytes,
        ),
    )
    if not linha:
        raise RuntimeError("Memória não foi registrada.")
    return str(linha["id"])


def definir_publicacao(memoria_id: str | UUID, status: str) -> bool:
    if status not in {"aprovado", "rejeitado", "pendente"}:
        raise ValueError("Status de publicação inválido.")
    linha = _alterar(
        """
        update public.memorias_festa
        set status_publicacao = %s, atualizado_em = now()
        where id = %s
        returning id;
        """,
        (status, str(memoria_id)),
    )
    return linha is not None


def registrar_exportacao(
    memoria_id: str | UUID, *, destino: str, referencia: str | None = None
) -> bool:
    if destino not in {"drive", "celular", "computador", "outro"}:
        raise ValueError("Destino de backup inválido.")
    linha = _alterar(
        """
        update public.memorias_festa
        set status_arquivo = 'exportado', destino_backup = %s,
            referencia_backup = %s, exportado_em = now(),
            verificado_em = null, atualizado_em = now()
        where id = %s and status_arquivo in ('no_supabase', 'exportado')
        returning id;
        """,
        (destino, referencia, str(memoria_id)),
    )
    return linha is not None


def registrar_verificacao(memoria_id: str | UUID) -> bool:
    linha = _alterar(
        """
        update public.memorias_festa
        set status_arquivo = 'verificado', verificado_em = now(), atualizado_em = now()
        where id = %s and status_arquivo = 'exportado'
        returning id;
        """,
        (str(memoria_id),),
    )
    return linha is not None


def registrar_original_removido(memoria_id: str | UUID) -> bool:
    linha = _alterar(
        """
        update public.memorias_festa
        set status_arquivo = 'removido', original_path = null,
            original_removido_em = now(), atualizado_em = now()
        where id = %s and status_arquivo = 'verificado'
              and verificado_em is not null
        returning id;
        """,
        (str(memoria_id),),
    )
    return linha is not None