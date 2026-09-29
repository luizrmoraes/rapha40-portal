"""Arquivo 40 com pills, diálogo de comentários e ampliação."""

from __future__ import annotations

from typing import Any

import streamlit as st

from core.comentarios import criar_comentario, listar_comentarios
from core.repositories import listar_fotos_historicas
from core.storage import BUCKET_HISTORICO, url_exibicao
from ui.components import botao_navegacao, cabecalho, cartao_foto_historica

ACOES_FOTO = {
    "ampliar": ":material/zoom_in: Ampliar foto",
    "comentarios": ":material/chat: Comentários",
}


@st.dialog("Foto do Arquivo 40", width="large")
def mostrar_foto_ampliada(foto: dict[str, Any]) -> None:
    try:
        imagem_url = url_exibicao(BUCKET_HISTORICO, foto["display_path"], 900)
    except Exception:
        st.error("Não foi possível carregar a foto ampliada.")
        return
    st.html('<style>[data-testid="stDialog"] [data-testid="stImage"] img{max-height:80vh!important;max-width:100%!important;width:auto!important;height:auto!important;object-fit:contain!important;margin:0 auto!important}[data-testid="stDialog"] [data-testid="stImage"]{width:100%!important}</style>')
    st.image(imagem_url, width="stretch")
    st.subheader(str(foto.get("titulo") or "Foto do arquivo"))
    if foto.get("legenda"):
        st.write(str(foto["legenda"]))


@st.dialog("Comentários", width="large")
def mostrar_comentarios(foto: dict[str, Any]) -> None:
    st.subheader(str(foto.get("titulo") or "Foto do arquivo"))
    try:
        comentarios = listar_comentarios("arquivo", foto["id"])
    except Exception:
        st.error("Não foi possível carregar os comentários.")
        comentarios = []
    if comentarios:
        for item in comentarios:
            st.caption(f"{item['nome']} · {item['criado_em']:%d/%m/%Y %H:%M}")
            st.write(item["comentario"])
            st.divider()
    else:
        st.info("Ainda não há comentários para esta foto.")
    with st.form(f"form_comentario_arquivo_{foto['id']}", clear_on_submit=True):
        nome = st.text_input("Seu nome", max_chars=80)
        texto = st.text_area("Comentário", max_chars=500)
        enviar = st.form_submit_button("Enviar comentário", type="primary")
    if enviar:
        try:
            criar_comentario("arquivo", foto["id"], nome, texto)
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Não foi possível enviar o comentário.")
        else:
            st.success("Comentário publicado.")
            st.rerun()


def _registrar_acao(foto_id: str) -> None:
    acao = st.session_state.get(f"acao_foto_{foto_id}")
    if acao is not None:
        st.session_state["acao_foto_pendente"] = (foto_id, acao)
        st.session_state[f"acao_foto_{foto_id}"] = None


def _render_acoes(foto: dict[str, Any]) -> None:
    foto_id = str(foto["id"])
    with st.container(horizontal=True, horizontal_alignment="center"):
        st.pills("Ações da foto", options=ACOES_FOTO.keys(), format_func=lambda acao: ACOES_FOTO[acao], selection_mode="single", label_visibility="collapsed", key=f"acao_foto_{foto_id}", on_change=_registrar_acao, args=(foto_id,))
    pendente = st.session_state.get("acao_foto_pendente")
    if pendente and pendente[0] == foto_id:
        del st.session_state["acao_foto_pendente"]
        mostrar_foto_ampliada(foto) if pendente[1] == "ampliar" else mostrar_comentarios(foto)


def render_arquivo_40() -> None:
    cabecalho("Arquivo 40", "Quarenta anos de histórias em imagens.")
    botao_navegacao("← Voltar ao portal", "portal_festa", chave="arquivo_voltar")
    ordenacao = st.selectbox("Ordem da linha do tempo", ("Mais antigas primeiro", "Mais recentes primeiro"), key="arquivo_ordenacao")
    try:
        fotos = listar_fotos_historicas(mais_recentes=(ordenacao == "Mais recentes primeiro"))
    except Exception:
        st.error("Não foi possível carregar as fotos. Tente novamente.")
        return
    if not fotos:
        st.info("As fotos do arquivo aparecerão aqui em breve.")
        return
    ano_anterior: object = object()
    for foto in fotos:
        ano_atual = foto.get("ano")
        if ano_atual != ano_anterior:
            col_ano, col_topo = st.columns([3, 2], vertical_alignment="center")

            with col_ano:
                st.subheader(str(ano_atual) if ano_atual is not None else "Sem data")

            with col_topo:
                st.markdown(
                    '<div style="text-align:right; font-size:0.82rem">'
                    '<a href="#arquivo-40" style="color:#c99a45">'
                    '↑ Voltar ao topo'
                    '</a></div>',
                    unsafe_allow_html=True,
                )

            ano_anterior = ano_atual
        try:
            imagem_url = url_exibicao(BUCKET_HISTORICO, foto["thumb_path"], 900)
        except Exception:
            imagem_url = None
        cartao_foto_historica(foto, imagem_url=imagem_url)
        _render_acoes(foto)