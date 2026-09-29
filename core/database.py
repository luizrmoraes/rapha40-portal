"""Conexoes PostgreSQL por operacao para uso seguro entre sessoes Streamlit."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import psycopg2
import streamlit as st

T = TypeVar("T")


# Nao use @st.cache_resource em uma conexao psycopg2 compartilhada.
# Cada execucao abre sua propria conexao, faz commit/rollback e fecha.
def _abrir_conexao():
    return psycopg2.connect(
        st.secrets["supabase_db"]["url"],
        connect_timeout=10,
        application_name="rapha40-portal",
    )


def executar_db(operacao: Callable[[Any], T]) -> T:
    """Executa uma operacao com conexao isolada e transacao controlada."""
    connection = _abrir_conexao()
    try:
        resultado = operacao(connection)
        connection.commit()
        return resultado
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def executar_leitura(operacao: Callable[[Any], T]) -> T:
    """Executa leitura isolada e fecha a conexao sem manter transacao aberta."""
    connection = _abrir_conexao()
    try:
        return operacao(connection)
    finally:
        connection.rollback()
        connection.close()
