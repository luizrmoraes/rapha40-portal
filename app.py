import streamlit as st

from config.settings import obter_modo_portal
from ui.theme import aplicar_tema
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

# Antes da festa: só Home e RSVP são permitidos.
if modo == "rsvp":
    if st.session_state.tela == "home":
        render_home()

    elif st.session_state.tela == "rsvp":
        render_rsvp()

    elif st.session_state.tela == "confirmado":
        render_rsvp_confirmado()

    elif st.session_state.tela == "recusado":
        render_rsvp_recusado()

    else:
        st.session_state.tela = "home"
        st.rerun()

# Dia da festa: carregaremos as telas secretas.
elif modo == "festa":
    from views.portal_festa import render_portal_festa

    render_portal_festa()

else:
    st.error("Modo do portal inválido.")