"""Componentes visuais reutilizaveis do portal Rapha 40.

Nao consulta banco, nao gera links de Storage e nao altera st.session_state.tela.
A tela chamadora fornece URLs de imagem validas (ex.: URLs assinadas).
"""

from __future__ import annotations

from collections.abc import Callable
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
    """Muda de tela somente apos clique; usar chaves unicas por pagina."""
    if st.button(texto, key=chave, type=tipo, use_container_width=True):
        st.session_state.tela = destino
        st.rerun()


def titulo_secao(titulo: str, descricao: str | None = None) -> None:
    st.subheader(titulo)
    if descricao:
        st.caption(descricao)


def cartao_foto_historica(
    foto: dict[str, Any],
    *,
    imagem_url: str | None,
) -> None:
    """Exibe metadados; imagem_url deve apontar para a versao de exibicao.

    thumb_path/display_path sao caminhos no bucket, nao URLs validas por si.
    """
    titulo = str(foto.get("titulo") or "Foto do arquivo")
    with st.container(border=True):
        if imagem_url:
            st.image(imagem_url, use_container_width=True)
        else:
            st.info("Imagem indisponível no momento.")
        st.markdown(f"**{titulo}**")
        ano = foto.get("ano")
        if ano is not None:
            st.caption(str(ano))
        legenda = foto.get("legenda")
        if legenda:
            st.write(str(legenda))


def cartao_memoria(
    memoria: dict[str, Any],
    *,
    imagem_url: str | None,
) -> None:
    """Exibe versao reduzida de uma memoria ja aprovada."""
    with st.container(border=True):
        if imagem_url:
            st.image(imagem_url, use_container_width=True)
        else:
            st.info("Imagem indisponível no momento.")
        frase = memoria.get("frase")
        if frase:
            st.write(str(frase))
        nome = memoria.get("nome_convidado")
        if nome:
            st.caption(f"Enviado por {nome}")


def metricas_resumo(resumo: dict[str, Any]) -> None:
    """Exibe indicadores RSVP em duas linhas, confortaveis no celular."""
    primeira = st.columns(2)
    primeira[0].metric("Respostas", int(resumo.get("respostas") or 0))
    primeira[1].metric("Confirmados", int(resumo.get("confirmados") or 0))
    segunda = st.columns(2)
    segunda[0].metric("Recusados", int(resumo.get("recusados") or 0))
    segunda[1].metric("Crianças", int(resumo.get("criancas") or 0))


def mensagem_vazia(texto: str) -> None:
    st.info(texto)


def executar_com_erro(
    operacao: Callable[[], Any],
    *,
    mensagem_erro: str = "Não foi possível carregar os dados. Tente novamente.",
) -> Any | None:
    """Opcional para consultas em telas publicas. Nao expõe excecoes ao convidado.

    Se None for um resultado valido para sua operacao, trate a excecao na
    propria tela em vez de usar este helper.
    """
    try:
        return operacao()
    except Exception:
        st.error(mensagem_erro)
        return None
