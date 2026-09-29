from pathlib import Path

import streamlit as st


@st.cache_data
def carregar_css() -> str:
    caminho = Path(__file__).resolve().parent.parent / "assets" / "css" / "style.css"
    return caminho.read_text(encoding="utf-8")


def aplicar_tema() -> None:
    st.markdown(f"<style>{carregar_css()}</style>", unsafe_allow_html=True)
