"""Componentes visuais reutilizaveis do portal Rapha 40."""

from __future__ import annotations

from collections.abc import Callable
from html import escape
from typing import Any

import streamlit as st


def cabecalho(titulo: str, descricao: str | None = None) -> None:
    st.title(titulo)
    if descricao:
        st.write(descricao)


def botao_navegacao(
    texto: str,
    destino: str,
    *,
    chave: str,
    tipo: str = "secondary",
) -> None:
    if st.button(texto, key=chave, type=tipo, use_container_width=True):
        st.session_state.tela = destino
        st.rerun()


def titulo_secao(titulo: str, descricao: str | None = None) -> None:
    st.subheader(titulo)
    if descricao:
        st.caption(descricao)


def _texto_html(valor: Any) -> str:
    return escape(str(valor), quote=True)


def _polaroid(
    *,
    imagem_url: str | None,
    titulo: str | None = None,
    legenda: str | None = None,
    detalhe: str | None = None,
) -> None:
    """Exibe foto em moldura CSS sem alterar o arquivo original.

    A regra object-fit da folha CSS define se a imagem e cortada ou preservada.
    """
    if imagem_url:
        imagem_html = (
            f'<img class="rapha-polaroid__photo" '
            f'src="{_texto_html(imagem_url)}" '
            f'alt="{_texto_html(titulo or legenda or "Foto do portal")}" '
            'loading="lazy">'
        )
    else:
        imagem_html = (
            '<div class="rapha-polaroid__missing" role="status">'
            'Imagem indisponível no momento.</div>'
        )

    titulo_html = (
        f'<p class="rapha-polaroid__title">{_texto_html(titulo)}</p>'
        if titulo else ""
    )
    legenda_html = (
        f'<p class="rapha-polaroid__caption">{_texto_html(legenda)}</p>'
        if legenda else ""
    )
    detalhe_html = (
        f'<p class="rapha-polaroid__meta">{_texto_html(detalhe)}</p>'
        if detalhe else ""
    )

    st.html(
        '<figure class="rapha-polaroid">'
        f'{imagem_html}'
        '<figcaption class="rapha-polaroid__text">'
        f'{titulo_html}{legenda_html}{detalhe_html}'
        '</figcaption>'
        '</figure>'
    )

_MESES_CURTOS = (
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
)


def formatar_data_foto(foto: dict[str, Any]) -> str | None:
    ano = foto.get("ano")
    if ano is None:
        return None

    mes = foto.get("mes")
    if mes is not None:
        data = f"{_MESES_CURTOS[int(mes) - 1]}/{int(ano) % 100:02d}"
    else:
        data = str(ano)

    return f"~ {data}" if foto.get("data_estimada") else data

def cartao_foto_historica(
    foto: dict[str, Any], *, imagem_url: str | None
) -> None:
    legenda = str(foto["legenda"]) if foto.get("legenda") else None
    data = formatar_data_foto(foto)

    if legenda and data:
        texto_inferior = f"{legenda} | {data}"
    else:
        texto_inferior = legenda or data

    _polaroid(
        imagem_url=imagem_url,
        titulo=str(foto.get("titulo") or "Foto do arquivo"),
        legenda=texto_inferior,
    )

def cartao_memoria(
    memoria: dict[str, Any], *, imagem_url: str | None
) -> None:
    nome = memoria.get("nome_convidado")
    _polaroid(
        imagem_url=imagem_url,
        legenda=str(memoria["frase"]) if memoria.get("frase") else None,
        detalhe=f"Enviado por {nome}" if nome else None,
    )


def metricas_resumo(resumo: dict[str, Any]) -> None:
    primeira = st.columns(2)
    primeira[0].metric("Respostas", int(resumo.get("respostas") or 0))
    primeira[1].metric("Confirmados", int(resumo.get("confirmados") or 0))
    segunda = st.columns(2)
    segunda[0].metric("Recusados", int(resumo.get("recusados") or 0))
    segunda[1].metric("Crianças", int(resumo.get("criancas") or 0))


def mensagem_vazia(texto: str) -> None:
    st.info(texto)


def executar_com_erro(
    operacao: Callable[[], Any], *,
    mensagem_erro: str = "Não foi possível carregar os dados. Tente novamente.",
) -> Any | None:
    try:
        return operacao()
    except Exception:
        st.error(mensagem_erro)
        return None
