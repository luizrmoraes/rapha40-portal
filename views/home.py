from pathlib import Path

import streamlit as st

from config.settings import (
    DATA_EVENTO,
    EVENTO_NOME,
    HORA_EVENTO,
    LOCAL_EVENTO,
    CONDOMINIO,
    obter_modo_portal,
)


def render_home() -> None:
    modo = obter_modo_portal()

    caminho_hero = Path("assets/images/hero-rapha-40.png")

    if caminho_hero.exists():
        st.image(
            str(caminho_hero),
            use_container_width=True,
        )
    else:
        st.warning("Imagem principal ainda não encontrada.")

    if modo == "rsvp":
        render_home_rsvp()
    else:
        render_home_festa()


def render_home_rsvp() -> None:
    st.markdown(
        """
        <div class="home-message">
                Depois de tantas histórias, conquistas e desafios,
                chegou a hora de celebrar mais um capítulo desta jornada.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "Confirmar presença",
        type="primary",
        use_container_width=True,
        key="btn_ir_rsvp",
    ):
        limpar_dados_rsvp()
        st.session_state.tela = "rsvp"
        st.rerun()

    st.markdown(
        f"""
        <div class="event-summary">
            <div><span>DATA</span>{DATA_EVENTO}</div>
            <div><span>HORÁRIO</span>{HORA_EVENTO}</div>
            <div><span>LOCAL</span>{CONDOMINIO} - {LOCAL_EVENTO}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_festa() -> None:
    st.markdown(
        """
        <div class="home-message">
            <div class="home-kicker">RAPHA 40</div>
            <div class="home-title">VOCÊ FAZ PARTE<br> DESSA HISTÓRIA</div>
            <p>
                Explore momentos, descubra histórias e deixe
                uma lembrança para o futuro.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "🖼 Mural de Memórias",
        use_container_width=True,
        key="btn_ir_mural",
    ):
        st.session_state.tela = "mural"
        st.rerun()

    if st.button(
        "🔥 Arquivo 40",
        use_container_width=True,
        key="btn_ir_arquivo",
    ):
        st.session_state.tela = "arquivo_40"
        st.rerun()

    if st.button(
        "📸 Deixe uma memória para o futuro",
        use_container_width=True,
        key="btn_ir_memoria",
    ):
        st.session_state.tela = "memoria_futuro"
        st.rerun()


def limpar_dados_rsvp() -> None:
    """
    Limpa o estado de um teste anterior antes de abrir o RSVP.
    Não altera dados já gravados no banco.
    """
    chaves = [
        "rsvp_dados",
        "rsvp_nome_principal",
        "rsvp_nome_principal_recusa",
        "rsvp_presenca",
        "rsvp_quantidade_criancas",
        "qtd_acompanhantes",
    ]

    for chave in list(st.session_state.keys()):
        if (
            chave in chaves
            or chave.startswith("rsvp_acompanhante_")
        ):
            del st.session_state[chave]