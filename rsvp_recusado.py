import streamlit as st

from config.settings import (
    DATA_EVENTO,
    EVENTO_NOME,
    HORA_EVENTO,
)


def render_rsvp_recusado() -> None:
    dados = st.session_state.get("rsvp_dados")

    if not dados:
        st.session_state.tela = "rsvp"
        st.rerun()

    nome = dados.get("nome_principal", "")

    st.title("Obrigado por responder")

    if nome:
        st.write(f"Obrigado, **{nome}**.")

    st.write(
        "Que pena que você não poderá estar presente, "
        "mas agradeço muito por informar."
    )

    st.divider()

    st.caption(
        f"{EVENTO_NOME} · {DATA_EVENTO} · {HORA_EVENTO}"
    )