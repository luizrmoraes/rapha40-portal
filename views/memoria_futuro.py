"""Envio de memória usando o processador compartilhado de imagens."""

from __future__ import annotations

import hashlib
import logging
from uuid import uuid4

import streamlit as st

from core.image_processing import preparar_display
from core.repositories import criar_memoria
from core.storage import (
    BUCKET_MURAL,
    BUCKET_ORIGINAIS,
    enviar_arquivo,
    remover_upload_falho,
)
from ui.components import botao_navegacao, cabecalho

_LOG = logging.getLogger(__name__)


def _tentar_novamente(mensagem: str) -> None:
    st.error(mensagem)
    if st.button("Tentar novamente", key="memoria_tentar_novamente"):
        st.rerun()


def render_memoria_futuro() -> None:
    cabecalho(
        "Envie sua memória",
        "Compartilhe uma foto e uma mensagem para o Rapha.",
    )
    botao_navegacao("← Voltar ao portal", "portal_festa", chave="memoria_voltar")

    if st.session_state.get("memoria_envio_concluido", False):
        st.success("Memória recebida! Ela aparecerá no mural após aprovação.")
        if st.button("Enviar outra memória", key="memoria_enviar_outra"):
            st.session_state.memoria_envio_concluido = False
            st.rerun()
        return

    st.caption("A foto aparecerá no mural somente após aprovação.")
    area_formulario = st.empty()
    with area_formulario.container():
        with st.form("form_memoria", clear_on_submit=True):
            nome = st.text_input("Seu nome (opcional)", max_chars=120)
            frase = st.text_area("Sua mensagem (opcional)", max_chars=280)
            arquivo = st.file_uploader(
                "Escolha uma foto (JPEG, PNG ou WebP, até 12 MB)",
                type=["jpg", "jpeg", "png", "webp"],
                accept_multiple_files=False,
            )
            enviado = st.form_submit_button(
                "Enviar memória", type="primary", use_container_width=True
            )

    if not enviado:
        return
    if nome.strip().casefold() == "admin":
        st.session_state.tela = "admin_login"
        st.rerun()
    if arquivo is None:
        area_formulario.empty()
        _tentar_novamente("Escolha uma foto para enviar.")
        return

    original = arquivo.getvalue()
    nome_original = arquivo.name[:255]
    area_formulario.empty()
    enviados: list[tuple[str, str]] = []

    try:
        with st.spinner("Preparando e enviando sua foto...", show_time=True):
            reduzida, extensao, mime = preparar_display(original, limite_mb=12)
            identificador = uuid4().hex
            original_path = f"{identificador}/original.{extensao}"
            display_path = f"{identificador}/display.webp"

            enviar_arquivo(BUCKET_ORIGINAIS, original_path, original, mime)
            enviados.append((BUCKET_ORIGINAIS, original_path))
            enviar_arquivo(BUCKET_MURAL, display_path, reduzida, "image/webp")
            enviados.append((BUCKET_MURAL, display_path))
            criar_memoria(
                nome_convidado=nome,
                frase=frase,
                original_path=original_path,
                original_nome=nome_original,
                original_mime=mime,
                original_bytes=len(original),
                original_sha256=hashlib.sha256(original).hexdigest(),
                display_path=display_path,
                display_bytes=len(reduzida),
            )
    except ValueError as erro:
        for bucket, path in reversed(enviados):
            try:
                remover_upload_falho(bucket, path)
            except Exception:
                _LOG.exception("Falha ao limpar upload: %s/%s", bucket, path)
        _tentar_novamente(str(erro))
        return
    except Exception:
        for bucket, path in reversed(enviados):
            try:
                remover_upload_falho(bucket, path)
            except Exception:
                _LOG.exception("Falha ao limpar upload: %s/%s", bucket, path)
        _LOG.exception("Falha no envio de memória")
        _tentar_novamente("Não foi possível concluir o envio. Tente novamente.")
        return

    st.session_state.memoria_envio_concluido = True
    st.rerun()
