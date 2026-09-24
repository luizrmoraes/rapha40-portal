from pathlib import Path
import streamlit as st


def aplicar_tema() -> None:
    css_path = Path("assets/css/style.css")

    with open(css_path, encoding="utf-8") as arquivo:
        st.markdown(
            f"<style>{arquivo.read()}</style>",
            unsafe_allow_html=True,
        )