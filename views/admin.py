import csv
import hmac
import io

import streamlit as st
from psycopg2.extras import RealDictCursor

from core.database import get_connection


def render_admin_login() -> None:
    if st.session_state.get("admin_autenticado", False):
        st.session_state.tela = "admin"
        st.rerun()

    st.title("Acesso administrativo")

    st.caption("Informe a senha para continuar.")

    with st.form("form_admin_login"):
        senha = st.text_input(
            "Senha",
            type="password",
            key="admin_senha",
        )

        entrar = st.form_submit_button(
            "Entrar",
            type="primary",
            use_container_width=True,
        )

    if not entrar:
        return

    senha_configurada = st.secrets["ADMIN_PASSWORD"]

    senha_valida = hmac.compare_digest(
        senha.encode("utf-8"),
        senha_configurada.encode("utf-8"),
    )

    if not senha_valida:
        st.error("Senha incorreta.")
        return

    st.session_state.admin_autenticado = True
    st.session_state.tela = "admin"
    st.rerun()


def render_admin() -> None:
    if not st.session_state.get("admin_autenticado", False):
        st.session_state.tela = "admin_login"
        st.rerun()

    st.title("Área administrativa")

    col_titulo, col_saida = st.columns([4, 1])

    with col_saida:
        sair = st.button(
            "Sair",
            key="admin_sair",
            type="secondary",
        )

    if sair:
        st.session_state.admin_autenticado = False
        st.session_state.tela = "home"
        st.rerun()

    st.divider()

    try:
        resumo = carregar_resumo()
        lista_portaria = carregar_lista_portaria()
    except Exception:
        st.error("Não foi possível carregar os dados administrativos.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Respostas", resumo["respostas"])

    with col2:
        st.metric("Confirmados", resumo["confirmados"])

    with col3:
        st.metric("Recusados", resumo["recusados"])

    with col4:
        st.metric("Crianças", resumo["criancas"])

    st.divider()

    st.subheader("Lista de portaria")

    if not lista_portaria:
        st.info("Ainda não há convidados confirmados.")
        return

    busca = st.text_input(
        "Pesquisar nome",
        placeholder="Digite parte do nome...",
        key="admin_busca_nome",
    )

    if busca.strip():
        termo = busca.strip().casefold()

        lista_exibicao = [
            item
            for item in lista_portaria
            if termo in item["nome"].casefold()
        ]
    else:
        lista_exibicao = lista_portaria

    st.caption(
        f"{len(lista_exibicao)} pessoa(s) encontrada(s) "
        f"de {len(lista_portaria)} na lista."
    )

    st.dataframe(
        [
            {
                "Nome": item["nome"],
                "Tipo": item["tipo"],
            }
            for item in lista_exibicao
        ],
        use_container_width=True,
        hide_index=True,
    )

    csv_bytes = gerar_csv(lista_portaria)

    st.download_button(
        "Baixar lista completa para a portaria",
        data=csv_bytes,
        file_name="lista_portaria_rapha40.csv",
        mime="text/csv",
        type="primary",
    )


def carregar_lista_portaria() -> list[dict]:
    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute(
                """
                select
                    nome,
                    tipo
                from public.vw_lista_portaria
                order by nome, tipo;
                """
            )

            return [
                dict(registro)
                for registro in cursor.fetchall()
            ]

    finally:
        connection.rollback()


def carregar_resumo() -> dict:
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select
                    count(*) as respostas,
                    count(*) filter (
                        where vai_comparecer = true
                          and status = 'confirmado'
                    ) as confirmados,
                    count(*) filter (
                        where vai_comparecer = false
                          and status = 'recusado'
                    ) as recusados,
                    coalesce(
                        sum(
                            case
                                when vai_comparecer = true
                                 and status = 'confirmado'
                                then quantidade_criancas
                                else 0
                            end
                        ),
                        0
                    ) as criancas
                from public.rsvps;
                """
            )

            registro = cursor.fetchone()

            return {
                "respostas": registro[0],
                "confirmados": registro[1],
                "recusados": registro[2],
                "criancas": registro[3],
            }

    finally:
        connection.rollback()


def gerar_csv(registros: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")

    writer.writerow(["Nome", "Tipo"])

    for registro in registros:
        writer.writerow(
            [
                registro["nome"],
                registro["tipo"],
            ]
        )

    # BOM para o Excel reconhecer UTF-8 corretamente.
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")