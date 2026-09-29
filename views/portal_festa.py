"""Página inicial do modo festa com hero visual da celebração."""

from pathlib import Path

import streamlit as st

from config.settings import EVENTO_NOME
from ui.components import botao_navegacao, cabecalho


def _divisor() -> None:
    st.markdown('<div class="festa-divider"></div>', unsafe_allow_html=True)


def render_portal_festa() -> None:
    caminho_hero = Path("assets/images/hero-rapha-40.png")
    if caminho_hero.exists():
        st.image(str(caminho_hero), use_container_width=True)
    else:
        st.warning("Imagem principal ainda não encontrada.")

    st.markdown(
        f"""
        <div class="festa-hero-caption">
            <h2>Que bom ter você aqui.</h2>
            <p>
                Este é o cantinho para rever histórias, descobrir memórias
                e registrar um pedacinho desta celebração.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _divisor()
    st.markdown(
        """
        <div class="festa-section-heading">
            <hr>
            <h3><span class="festa-section-icon">📷 Arquivo 40</span></h3>
            <div>
                <p>Uma volta por momentos que ajudaram a construir esta história.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    botao_navegacao(
        "Explorar o Arquivo 40 📷 ",
        "arquivo_40",
        chave="portal_arquivo_40",
        tipo="primary",
    )

    _divisor()
    st.markdown(
        """
        <div class="festa-section-heading">
            <hr>
            <h3><span class="festa-section-icon">✨ Mural de memórias </span></h3>
            <div>
                <p>Fotos e mensagens compartilhadas pelos convidados durante a festa.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    botao_navegacao(
        "Ver o mural de hoje ✨ ",
        "mural_memorias",
        chave="portal_mural_memorias",
        tipo="primary",
    )

    _divisor()
    st.markdown(
        """
        <div class="festa-section-heading">
            <hr>
            <h3><span class="festa-section-icon">💌 Enviar uma memória</span></h3>
            <div>
                <p>Compartilhe uma foto, uma frase ou uma lembrança deste momento.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    botao_navegacao(
        "Deixar uma memória 💌 ",
        "memoria_futuro",
        chave="portal_memoria_futuro",
    )

    st.markdown(
        """
        <hr>
        <div class="festa-footer-note">
            Cada foto e cada frase ajudam a guardar este dia.
        </div>
        """,
        unsafe_allow_html=True,
    )
