"""Entrada e roteamento do portal Rapha 40."""

import streamlit as st

from config.settings import obter_modo_portal
from ui.theme import aplicar_tema
from views.admin import render_admin, render_admin_login
from views.home import render_home
from views.rsvp import render_rsvp
from views.rsvp_confirmado import render_rsvp_confirmado
from views.rsvp_recusado import render_rsvp_recusado

st.set_page_config(
    page_title="Rapha 40",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

aplicar_tema()

if "tela" not in st.session_state:
    st.session_state.tela = "home"

modo = obter_modo_portal()
tela = st.session_state.tela

# O admin permanece acessivel nos dois modos.
# render_admin tambem verifica admin_autenticado antes de mostrar dados.
if tela == "admin_login":
    render_admin_login()

elif tela == "admin":
    render_admin()

elif modo == "rsvp":
    # Nao importar nem exibir paginas da festa antes da liberacao.
    if tela == "home":
        render_home()
    elif tela == "rsvp":
        render_rsvp()
    elif tela == "confirmado":
        render_rsvp_confirmado()
    elif tela == "recusado":
        render_rsvp_recusado()
    else:
        st.session_state.tela = "home"
        st.rerun()

elif modo == "festa":
    if tela in {"home", "portal_festa"}:
        from views.portal_festa import render_portal_festa

        render_portal_festa()

    elif tela == "arquivo_40":
        from views.arquivo_40 import render_arquivo_40

        render_arquivo_40()

    elif tela == "memoria_futuro":
        from views.memoria_futuro import render_memoria_futuro

        render_memoria_futuro()

    elif tela == "mural_memorias":
        from views.mural_memorias import render_mural_memorias

        render_mural_memorias()

    else:
        st.session_state.tela = "home"
        st.rerun()

else:
    st.error("Modo do portal inválido.")
