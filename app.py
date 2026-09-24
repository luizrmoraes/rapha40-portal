import streamlit as st

from views.rsvp import render_rsvp
from views.rsvp_confirmado import render_rsvp_confirmado
from views.rsvp_recusado import render_rsvp_recusado


st.set_page_config(
    page_title="Rapha 40",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if "tela" not in st.session_state:
    st.session_state.tela = "rsvp"

if st.session_state.tela == "rsvp":
    render_rsvp()

elif st.session_state.tela == "confirmado":
    render_rsvp_confirmado()

elif st.session_state.tela == "recusado":
    render_rsvp_recusado()

else:
    st.session_state.tela = "rsvp"
    st.rerun()