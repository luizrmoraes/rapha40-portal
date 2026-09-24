import streamlit as st

from config.settings import (
    CONDOMINIO,
    DATA_EVENTO,
    EVENTO_NOME,
    HORA_EVENTO,
    LOCAL_EVENTO,
    ACESSO1,
    ACESSO2
)


def render_rsvp_confirmado() -> None:
    dados = st.session_state.get("rsvp_dados")

    # Proteção: se alguém acessar a tela diretamente sem preencher o RSVP,
    # volta para o formulário.
    if not dados:
        st.session_state.tela = "rsvp"
        st.rerun()

    acompanhantes = dados.get("acompanhantes", [])
    quantidade_criancas = int(dados.get("quantidade_criancas", 0))

    total_adultos = 1 + len(acompanhantes)
    total_pessoas = total_adultos + quantidade_criancas

    st.title("Presença confirmada ✓")

    st.success(
        "Sua confirmação foi registrada com sucesso."
    )

    st.write(
        f"Obrigado, **{dados['nome_principal']}**. "
        f"Seu nome já está registrado para a lista de acesso do "
        f"**{CONDOMINIO}**."
    )

    st.divider()

    st.subheader("Dados do evento")

    col_data, col_hora = st.columns(2)

    with col_data:
        st.metric("📅 Data", DATA_EVENTO)

    with col_hora:
        st.metric("🕒 Horário", HORA_EVENTO)

    st.metric("📍 Local", LOCAL_EVENTO)

    st.metric("🗺️ Endereço", ACESSO1)

    st.caption("ou")

    st.metric("🗺️ Endereço", ACESSO2)

    st.caption(CONDOMINIO)

    st.divider()

    st.subheader("Seu grupo confirmado")

    st.write(f"**Convidado principal:** {dados['nome_principal']}")

    if acompanhantes:
        st.write("**Acompanhantes adultos:**")

        for indice, acompanhante in enumerate(acompanhantes, start=1):
            st.write(f"{indice}. {acompanhante}")
    else:
        st.write("**Acompanhantes adultos:** nenhum informado")

    if quantidade_criancas > 0:
        st.write(
            f"**Crianças:** {quantidade_criancas}"
        )
    else:
        st.write("**Crianças:** nenhuma informada")

    st.divider()

    col_adultos, col_criancas, col_total = st.columns(3)

    with col_adultos:
        st.metric("Adultos", total_adultos)

    with col_criancas:
        st.metric("Crianças", quantidade_criancas)

    with col_total:
        st.metric("Total", total_pessoas)

    st.divider()

    st.caption(
        f"{EVENTO_NOME} · {DATA_EVENTO} · {HORA_EVENTO}"
    )

    st.markdown(
        "<div style='text-align: center; padding-top: 8px;'>"
        "<strong>Te espero lá!</strong>"
        "</div>",
        unsafe_allow_html=True,
    )