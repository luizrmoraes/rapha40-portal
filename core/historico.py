"""Cadastro de fotos históricas usando o processador compartilhado."""

from __future__ import annotations

from uuid import uuid4

from core.database import executar_db
from core.image_processing import preparar_historico
from core.storage import BUCKET_HISTORICO, enviar_arquivo, remover_upload_falho


def cadastrar_foto_historica(
    *, conteudo: bytes, titulo: str, legenda: str | None, ano: int | None,
    mes: int | None, data_estimada: bool = False, ordem: int = 0,
) -> str:
    titulo = titulo.strip()
    legenda = legenda.strip() or None if legenda is not None else None
    if not 1 <= len(titulo) <= 120:
        raise ValueError("O título deve ter entre 1 e 120 caracteres.")
    if ano is not None and (type(ano) is not int or not 1900 <= ano <= 2100):
        raise ValueError("Ano inválido.")
    if mes is not None and (type(mes) is not int or not 1 <= mes <= 12):
        raise ValueError("Mês inválido.")
    if mes is not None and ano is None:
        raise ValueError("Informe o ano ao selecionar o mês.")
    if type(ordem) is not int or ordem < 0:
        raise ValueError("Ordem inválida.")

    thumb, display = preparar_historico(conteudo)
    identificador = uuid4().hex
    thumb_path = f"historico/{identificador}/thumb.webp"
    display_path = f"historico/{identificador}/display.webp"
    enviados: list[str] = []
    try:
        enviar_arquivo(BUCKET_HISTORICO, thumb_path, thumb, "image/webp")
        enviados.append(thumb_path)
        enviar_arquivo(BUCKET_HISTORICO, display_path, display, "image/webp")
        enviados.append(display_path)

        def inserir(connection):
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into public.fotos_historicas
                        (titulo, legenda, ano, mes, data_estimada,
                         thumb_path, display_path, thumb_bytes, display_bytes,
                         ordem, ativo)
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true)
                    returning id;
                    """,
                    (titulo, legenda, ano, mes, data_estimada,
                     thumb_path, display_path, len(thumb), len(display), ordem),
                )
                return str(cursor.fetchone()[0])

        return executar_db(inserir)
    except Exception:
        for path in reversed(enviados):
            try:
                remover_upload_falho(BUCKET_HISTORICO, path)
            except Exception:
                pass
        raise
