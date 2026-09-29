"""Mural público com pills, ampliação e comentários imediatos."""

from __future__ import annotations

from typing import Any

import streamlit as st

from core.comentarios import criar_comentario, listar_comentarios
from core.repositories import listar_memorias_aprovadas
from core.storage import BUCKET_MURAL, url_exibicao
from ui.components import botao_navegacao, cabecalho, cartao_memoria

ACOES_MEMORIA = {
    "ampliar": ":material/zoom_in: Ampliar foto",
    "comentarios": ":material/chat: Comentários",
}


@st.dialog("Foto da memória", width="large")
def mostrar_memoria_ampliada(memoria: dict[str, Any]) -> None:
    try:
        imagem_url = url_exibicao(BUCKET_MURAL, memoria["display_path"], 900)
    except Exception:
        st.error("Não foi possível carregar a foto ampliada.")
        return
    st.html('<style>[data-testid="stDialog"] [data-testid="stImage"] img{max-height:80vh!important;max-width:100%!important;width:auto!important;height:auto!important;object-fit:contain!important;margin:0 auto!important}[data-testid="stDialog"] [data-testid="stImage"]{width:100%!important}</style>')
    st.image(imagem_url, width="stretch")
    if memoria.get("frase"):
        st.write(str(memoria["frase"]))
    if memoria.get("nome_convidado"):
        st.caption(f"Enviado por {memoria['nome_convidado']}")


@st.dialog("Comentários", width="large")
def mostrar_comentarios(memoria: dict[str, Any]) -> None:
    try:
        comentarios = listar_comentarios("mural", memoria["id"])
    except Exception:
        st.error("Não foi possível carregar os comentários.")
        comentarios = []
    if comentarios:
        for item in comentarios:
            st.caption(f"{item['nome']} · {item['criado_em']:%d/%m/%Y %H:%M}")
            st.write(item["comentario"])
            st.divider()
    else:
        st.info("Ainda não há comentários para esta memória.")
    with st.form(f"form_comentario_mural_{memoria['id']}", clear_on_submit=True):
        nome = st.text_input("Seu nome", max_chars=80)
        texto = st.text_area("Comentário", max_chars=500)
        enviar = st.form_submit_button("Enviar comentário", type="primary")
    if enviar:
        try:
            criar_comentario("mural", memoria["id"], nome, texto)
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Não foi possível enviar o comentário.")
        else:
            st.success("Comentário publicado.")
            st.rerun()


def _registrar_acao(memoria_id: str) -> None:
    acao = st.session_state.get(f"acao_memoria_{memoria_id}")
    if acao is not None:
        st.session_state["acao_memoria_pendente"] = (memoria_id, acao)
        st.session_state[f"acao_memoria_{memoria_id}"] = None


def _render_acoes(memoria: dict[str, Any]) -> None:
    memoria_id = str(memoria["id"])
    with st.container(horizontal=True, horizontal_alignment="center"):
        st.pills("Ações da memória", options=ACOES_MEMORIA.keys(), format_func=lambda acao: ACOES_MEMORIA[acao], selection_mode="single", label_visibility="collapsed", key=f"acao_memoria_{memoria_id}", on_change=_registrar_acao, args=(memoria_id,))
    pendente = st.session_state.get("acao_memoria_pendente")
    if pendente and pendente[0] == memoria_id:
        del st.session_state["acao_memoria_pendente"]
        mostrar_memoria_ampliada(memoria) if pendente[1] == "ampliar" else mostrar_comentarios(memoria)


def render_mural_memorias() -> None:
    cabecalho("Mural de memórias", "Lembranças compartilhadas na festa.")
    botao_navegacao("← Voltar ao portal", "portal_festa", chave="mural_voltar_portal")
    try:
        memorias = listar_memorias_aprovadas(limite=100)
    except Exception:
        st.error("Não foi possível carregar o mural. Tente novamente.")
        return
    if not memorias:
        st.info("Ainda não há memórias publicadas. Volte em breve!")
        return
    for memoria in memorias:
        try:
            imagem_url = url_exibicao(BUCKET_MURAL, memoria["display_path"], 900)
        except Exception:
            imagem_url = None
        cartao_memoria(memoria, imagem_url=imagem_url)
        _render_acoes(memoria)
