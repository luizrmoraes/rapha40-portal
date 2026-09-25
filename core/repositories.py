"""Acesso aos metadados do portal Rapha 40 no PostgreSQL/Supabase.

Arquivos de imagem sao enviados/baixados pela Storage API em outro modulo.
Nao guarde bytes das imagens nas tabelas nem use SQL em storage.objects.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg2.extras import RealDictCursor

from core.database import get_connection


def _ler(sql: str, parametros: tuple[Any, ...] = (), *, um: bool = False):
    connection = get_connection()
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, parametros)
            resultado = cursor.fetchone() if um else cursor.fetchall()
            return dict(resultado) if um and resultado else (
                [dict(linha) for linha in resultado] if not um else None
            )
    except Exception:
        connection.rollback()
        raise
    finally:
        # Conexao em cache: finalizar inclusive transacoes somente-leitura.
        connection.rollback()


def _escrever(sql: str, parametros: tuple[Any, ...]) -> dict[str, Any]:
    connection = get_connection()
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, parametros)
            linha = cursor.fetchone()
        connection.commit()
        return dict(linha) if linha is not None else None
    except Exception:
        connection.rollback()
        raise


def criar_rsvp(
    nome_principal: str,
    vai_comparecer: bool,
    quantidade_criancas: int = 0,
    acompanhantes: list[str] | None = None,
) -> str:
    """Salva titular e acompanhantes numa mesma transacao."""
    nome = nome_principal.strip()
    nomes_acompanhantes = [n.strip() for n in (acompanhantes or [])]
    if len(nome) < 3:
        raise ValueError("Informe o nome completo.")
    if not isinstance(vai_comparecer, bool):
        raise ValueError("Presenca invalida.")
    if any(len(n) < 3 for n in nomes_acompanhantes):
        raise ValueError("Informe o nome completo de cada acompanhante.")
    if not vai_comparecer and (nomes_acompanhantes or quantidade_criancas):
        raise ValueError("Recusas nao podem incluir acompanhantes ou criancas.")
    if not isinstance(quantidade_criancas, int) or quantidade_criancas < 0:
        raise ValueError("Quantidade de criancas invalida.")

    connection = get_connection()
    try:
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
            for acompanhante in nomes_acompanhantes:
                cursor.execute(
                    """
                    insert into public.rsvp_acompanhantes (rsvp_id, nome_completo)
                    values (%s, %s);
                    """,
                    (rsvp_id, acompanhante),
                )
        connection.commit()
        return str(rsvp_id)
    except Exception:
        connection.rollback()
        raise


def carregar_lista_portaria() -> list[dict[str, Any]]:
    return _ler(
        "select nome, tipo from public.vw_lista_portaria order by nome, tipo;"
    )


def carregar_resumo() -> dict[str, Any]:
    return _ler(
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


def listar_fotos_historicas(*, somente_ativas: bool = True) -> list[dict[str, Any]]:
    return _ler(
        """
        select id, titulo, legenda, ano, thumb_path, display_path,
               thumb_bytes, display_bytes, ordem, ativo, criado_em
        from public.fotos_historicas
        where (%s = false or ativo = true)
        order by ordem, criado_em, id;
        """,
        (somente_ativas,),
    )


def listar_memorias_aprovadas(*, limite: int = 100) -> list[dict[str, Any]]:
    if not 1 <= limite <= 500:
        raise ValueError("Limite deve estar entre 1 e 500.")
    return _ler(
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
    """Chamar somente depois da verificacao de admin na camada de interface."""
    if not 1 <= limite <= 500:
        raise ValueError("Limite deve estar entre 1 e 500.")
    return _ler(
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


def carregar_uso_fotos() -> list[dict[str, Any]]:
    """Estimativa baseada nos metadados; nao e a quota oficial do Storage."""
    return _ler(
        """
        select categoria, fotos, bytes_reduzidas, bytes_exibicao, bytes_originais
        from public.vw_uso_fotos order by categoria;
        """
    )


def criar_memoria(
    *,
    nome_convidado: str | None,
    frase: str | None,
    original_path: str,
    original_nome: str,
    original_mime: str,
    original_bytes: int,
    original_sha256: str,
    display_path: str,
    display_bytes: int,
) -> str:
    """Registra metadados APOS confirmar uploads do original e da reduzida.

    Em caso de erro, o modulo de upload deve tentar remover os objetos enviados.
    """
    if not original_path or not display_path or not original_nome:
        raise ValueError("Caminhos e nome do original sao obrigatorios.")
    if original_bytes <= 0 or display_bytes <= 0:
        raise ValueError("Tamanhos dos arquivos devem ser positivos.")
    if len(original_sha256) != 64 or any(
        c not in "0123456789abcdefABCDEF" for c in original_sha256
    ):
        raise ValueError("SHA-256 invalido.")
    if frase is not None and len(frase) > 280:
        raise ValueError("Frase deve ter ate 280 caracteres.")
    linha = _escrever(
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
            original_path,
            original_nome,
            original_mime,
            original_bytes,
            original_sha256.lower(),
            display_path,
            display_bytes,
        ),
    )
    return str(linha["id"])


def definir_publicacao(memoria_id: str | UUID, status: str) -> bool:
    """Admin: aprova ou rejeita; a tela chamadora deve validar a sessao."""
    if status not in {"aprovado", "rejeitado", "pendente"}:
        raise ValueError("Status de publicacao invalido.")
    linha = _escrever(
        """
        update public.memorias_festa
        set status_publicacao = %s, atualizado_em = now()
        where id = %s
        returning id;
        """,
        (status, str(memoria_id)),
    ) if _memoria_existe(memoria_id) else None
    return linha is not None


def _memoria_existe(memoria_id: str | UUID) -> bool:
    return _ler(
        "select id from public.memorias_festa where id = %s;",
        (str(memoria_id),),
        um=True,
    ) is not None


def registrar_exportacao(
    memoria_id: str | UUID, *, destino: str, referencia: str | None = None
) -> bool:
    """Marcar somente quando o download/copia ao destino terminou."""
    if destino not in {"drive", "celular", "computador", "outro"}:
        raise ValueError("Destino de backup invalido.")
    linha = _escrever(
        """
        update public.memorias_festa
        set status_arquivo = 'exportado', destino_backup = %s,
            referencia_backup = %s, exportado_em = now(),
            verificado_em = null, atualizado_em = now()
        where id = %s and status_arquivo in ('no_supabase', 'exportado')
        returning id;
        """,
        (destino, referencia, str(memoria_id)),
    ) if _status_arquivo_permite(memoria_id, {"no_supabase", "exportado"}) else None
    return linha is not None


def registrar_verificacao(memoria_id: str | UUID) -> bool:
    """Admin confirma que a copia externa abre e corresponde ao original."""
    linha = _escrever(
        """
        update public.memorias_festa
        set status_arquivo = 'verificado', verificado_em = now(),
            atualizado_em = now()
        where id = %s and status_arquivo = 'exportado'
        returning id;
        """,
        (str(memoria_id),),
    ) if _status_arquivo_permite(memoria_id, {"exportado"}) else None
    return linha is not None


def _status_arquivo_permite(memoria_id: str | UUID, estados: set[str]) -> bool:
    linha = _ler(
        "select status_arquivo from public.memorias_festa where id = %s;",
        (str(memoria_id),),
        um=True,
    )
    return bool(linha and linha["status_arquivo"] in estados)


def registrar_original_removido(memoria_id: str | UUID) -> bool:
    """Chamar SOMENTE depois da exclusao confirmada via Storage API.

    Se a remocao falhar, nao chame esta funcao: o banco deve refletir
    que o original ainda ocupa espaco no bucket.
    """
    linha = _escrever(
        """
        update public.memorias_festa
        set status_arquivo = 'removido', original_path = null,
            original_removido_em = now(), atualizado_em = now()
        where id = %s and status_arquivo = 'verificado'
              and verificado_em is not null
        returning id;
        """,
        (str(memoria_id),),
    ) if _status_arquivo_permite(memoria_id, {"verificado"}) else None
    return linha is not None
