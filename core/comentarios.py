"""Repositório de comentários públicos, sem moderação prévia."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg2.extras import RealDictCursor

from core.database import executar_db, executar_leitura

_CONFIG = {
    "arquivo": (
        "public.comentarios_fotos_historicas",
        "foto_id",
        "public.fotos_historicas",
        "ativo = true",
    ),
    "mural": (
        "public.comentarios_memorias_festa",
        "memoria_id",
        "public.memorias_festa",
        "status_publicacao = 'aprovado'",
    ),
}


def _config(tipo: str) -> tuple[str, str, str, str]:
    try:
        return _CONFIG[tipo]
    except KeyError as exc:
        raise ValueError("Tipo de foto inválido.") from exc


def _id(valor: str | UUID) -> str:
    try:
        return str(UUID(str(valor)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("Identificador inválido.") from exc


def listar_comentarios(
    tipo: str, foto_id: str | UUID, *, limite: int = 100
) -> list[dict[str, Any]]:
    tabela, coluna, origem, filtro = _config(tipo)
    foto_id = _id(foto_id)
    if not 1 <= limite <= 200:
        raise ValueError("Limite inválido.")

    def consultar(connection):
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                select c.id, c.nome, c.comentario, c.criado_em
                from {tabela} c
                join {origem} f on f.id = c.{coluna}
                where c.{coluna} = %s and f.{filtro}
                order by c.criado_em desc, c.id desc
                limit %s;
                """,
                (foto_id, limite),
            )
            return [dict(linha) for linha in cursor.fetchall()]

    return executar_leitura(consultar)


def criar_comentario(
    tipo: str, foto_id: str | UUID, nome: str, comentario: str
) -> str:
    tabela, coluna, origem, filtro = _config(tipo)
    foto_id = _id(foto_id)
    nome = nome.strip()
    comentario = comentario.strip()
    if not 2 <= len(nome) <= 80:
        raise ValueError("Informe um nome entre 2 e 80 caracteres.")
    if not 1 <= len(comentario) <= 500:
        raise ValueError("O comentário deve ter entre 1 e 500 caracteres.")

    def inserir(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                insert into {tabela} ({coluna}, nome, comentario)
                select id, %s, %s
                from {origem}
                where id = %s and {filtro}
                returning id;
                """,
                (nome, comentario, foto_id),
            )
            linha = cursor.fetchone()
            if linha is None:
                raise ValueError("A foto não está disponível para comentários.")
            return str(linha[0])

    return executar_db(inserir)


def listar_comentarios_admin(*, limite: int = 200) -> list[dict[str, Any]]:
    if not 1 <= limite <= 500:
        raise ValueError("Limite inválido.")

    def consultar(connection):
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                select * from (
                    select 'arquivo'::text as tipo, c.id,
                           c.foto_id as item_id, f.titulo as item_titulo,
                           c.nome, c.comentario, c.criado_em
                    from public.comentarios_fotos_historicas c
                    join public.fotos_historicas f on f.id = c.foto_id
                    union all
                    select 'mural'::text as tipo, c.id,
                           c.memoria_id as item_id,
                           coalesce(f.frase, 'Memória sem mensagem') as item_titulo,
                           c.nome, c.comentario, c.criado_em
                    from public.comentarios_memorias_festa c
                    join public.memorias_festa f on f.id = c.memoria_id
                ) comentarios
                order by criado_em desc, id desc
                limit %s;
                """,
                (limite,),
            )
            return [dict(linha) for linha in cursor.fetchall()]

    return executar_leitura(consultar)


def excluir_comentario_admin(tipo: str, comentario_id: str | UUID) -> bool:
    tabela, _, _, _ = _config(tipo)
    comentario_id = _id(comentario_id)

    def excluir(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                f"delete from {tabela} where id = %s returning id;",
                (comentario_id,),
            )
            return cursor.fetchone() is not None

    return executar_db(excluir)
