"""Área administrativa do portal Rapha 40."""

from __future__ import annotations

import csv
import hmac
import io
from typing import Any

import streamlit as st

from core.comentarios import excluir_comentario_admin, listar_comentarios_admin
from core.repositories import (
    carregar_lista_portaria,
    carregar_resumo,
    definir_publicacao,
    listar_memorias_pendentes,
)
from core.storage import url_preview_memoria_admin


def render_admin_login() -> None:
    if st.session_state.get("admin_autenticado", False):
        st.session_state.tela = "admin"
        st.rerun()

    st.title("Acesso administrativo")
    st.caption("Informe a senha para continuar.")
    with st.form("form_admin_login"):
        senha = st.text_input("Senha", type="password", key="admin_senha")
        entrar = st.form_submit_button(
            "Entrar", type="primary", use_container_width=True
        )

    if not entrar:
        return
    senha_configurada = st.secrets["ADMIN_PASSWORD"]
    if not hmac.compare_digest(senha, senha_configurada):
        st.error("Senha incorreta.")
        return
    st.session_state.admin_autenticado = True
    st.session_state.tela = "admin"
    st.rerun()


def render_admin() -> None:
    if not st.session_state.get("admin_autenticado", False):
        st.session_state.tela = "admin_login"
        st.rerun()
        return

    st.title("Área administrativa")
    col_titulo, col_saida = st.columns([4, 1])
    with col_titulo:
        st.caption("Moderação de memórias e acompanhamento da festa")
    with col_saida:
        if st.button("Sair", key="admin_sair", type="secondary"):
            st.session_state.admin_autenticado = False
            st.session_state.pop("excluir_comentario_pendente", None)
            st.session_state.tela = "home"
            st.rerun()

    with st.expander("1. Aprovação de memórias", expanded=True):
        render_aprovacoes()

    with st.expander("2. Cadastro de fotos do Arquivo 40", expanded=False):
        render_upload_arquivo()

    with st.expander("3. Comentários publicados", expanded=False):
        render_comentarios_admin()

    with st.expander("4. Resumo e lista de portaria", expanded=False):
        render_resumo_e_portaria()


def render_aprovacoes() -> None:
    st.subheader("Memórias aguardando aprovação")
    try:
        pendentes = listar_memorias_pendentes(limite=200)
    except Exception:
        st.error("Não foi possível carregar as memórias.")
        return

    st.caption(f"{len(pendentes)} memória(s) aguardando aprovação.")
    if not pendentes:
        st.info("Nenhuma memória aguardando aprovação.")
        return

    for memoria in pendentes:
        memoria_id = str(memoria["id"])
        with st.container(border=True):
            try:
                st.image(
                    url_preview_memoria_admin(memoria["display_path"]),
                    use_container_width=True,
                )
            except Exception:
                st.warning("Não foi possível carregar a prévia desta foto.")
            st.write(memoria.get("frase") or "Sem mensagem.")
            st.caption(f"Enviado por: {memoria.get('nome_convidado') or 'Anônimo'}")
            aprovar, rejeitar = st.columns(2)
            if aprovar.button("Aprovar", key=f"aprovar_{memoria_id}", type="primary"):
                try:
                    definir_publicacao(memoria_id, "aprovado")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Não foi possível aprovar esta memória: {exc}")
            if rejeitar.button("Rejeitar", key=f"rejeitar_{memoria_id}"):
                try:
                    definir_publicacao(memoria_id, "rejeitado")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Não foi possível rejeitar esta memória: {exc}")


def render_upload_arquivo() -> None:
    st.subheader("Adicionar foto histórica")
    st.caption(
        "A foto será preparada para exibição; o original não será preservado no Supabase."
    )
    with st.form("form_upload_arquivo", clear_on_submit=True):
        arquivo = st.file_uploader(
            "Foto", type=["jpg", "jpeg", "png", "webp"], key="arquivo_foto"
        )
        titulo = st.text_input("Título", max_chars=120, key="arquivo_titulo")
        legenda = st.text_area("Legenda", key="arquivo_legenda")
        col_ano, col_mes = st.columns(2)
        with col_ano:
            ano = st.number_input(
                "Ano", min_value=1900, max_value=2100, value=2000,
                step=1, key="arquivo_ano",
            )
        with col_mes:
            mes = st.number_input(
                "Mês (opcional; 0 = não informar)", min_value=0,
                max_value=12, value=0, step=1, key="arquivo_mes",
            )
        data_estimada = st.checkbox("Data aproximada", key="arquivo_data_estimada")
        ordem = st.number_input(
            "Ordem", min_value=0, value=0, step=1, key="arquivo_ordem"
        )
        salvar = st.form_submit_button(
            "Cadastrar foto", type="primary", use_container_width=True
        )

    if not salvar:
        return
    if arquivo is None:
        st.error("Escolha uma foto para cadastrar.")
        return
    if not titulo.strip():
        st.error("Informe o título da foto.")
        return

    try:
        from core.historico import cadastrar_foto_historica
        from io import BytesIO
        from PIL import Image

        with Image.open(BytesIO(arquivo.getvalue())) as imagem_teste:
            st.info(
                f"Diagnóstico: nome={arquivo.name!r}; "
                f"formato detectado={imagem_teste.format!r}; "
                f"modo={imagem_teste.mode!r}; "
                f"dimensões={imagem_teste.size}"
            )

        with st.spinner("Preparando e enviando a foto..."):
            cadastrar_foto_historica(
                conteudo=arquivo.getvalue(),
                titulo=titulo,
                legenda=legenda,
                ano=int(ano),
                mes=int(mes) or None,
                data_estimada=data_estimada,
                ordem=int(ordem),
            )
    except ModuleNotFoundError as exc:
        if exc.name == "core.historico":
            st.error("O arquivo core/historico.py não está na pasta do projeto.")
        else:
            raise
    except ValueError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Não foi possível cadastrar a foto: {exc}")
    else:
        st.success("Foto cadastrada com sucesso no Arquivo 40.")


def render_comentarios_admin() -> None:
    st.subheader("Comentários publicados")
    try:
        comentarios = listar_comentarios_admin(limite=300)
    except Exception:
        st.error("Não foi possível carregar os comentários.")
        return

    if not comentarios:
        st.info("Ainda não há comentários publicados.")
        return

    st.caption(f"{len(comentarios)} comentário(s) exibido(s).")
    pendente = st.session_state.get("excluir_comentario_pendente")
    for item in comentarios:
        tipo = item["tipo"]
        comentario_id = str(item["id"])
        alvo = (tipo, comentario_id)
        origem = "Arquivo 40" if tipo == "arquivo" else "Mural de memórias"
        with st.container(border=True):
            st.caption(
                f"{origem} · {item['nome']} · "
                f"{item['criado_em']:%d/%m/%Y %H:%M}"
            )
            st.write(str(item["item_titulo"]))
            st.write(str(item["comentario"]))

            if pendente == alvo:
                st.warning("Excluir este comentário permanentemente?")
                confirmar, cancelar = st.columns(2)
                if confirmar.button(
                    "Confirmar exclusão", key=f"confirmar_{tipo}_{comentario_id}"
                ):
                    try:
                        excluido = excluir_comentario_admin(tipo, comentario_id)
                    except Exception:
                        st.error("Não foi possível excluir o comentário.")
                    else:
                        st.session_state.pop("excluir_comentario_pendente", None)
                        if excluido:
                            st.rerun()
                        st.warning("Comentário não encontrado.")
                if cancelar.button("Cancelar", key=f"cancelar_{tipo}_{comentario_id}"):
                    st.session_state.pop("excluir_comentario_pendente", None)
                    st.rerun()
            elif st.button(
                "Excluir comentário", key=f"excluir_{tipo}_{comentario_id}"
            ):
                st.session_state.excluir_comentario_pendente = alvo
                st.rerun()


def render_resumo_e_portaria() -> None:
    try:
        resumo = carregar_resumo()
        lista_portaria = carregar_lista_portaria()
    except Exception as exc:
        st.error(f"Não foi possível carregar os dados administrativos: {exc}")
        return

    colunas = st.columns(4)
    colunas[0].metric("Respostas", resumo.get("respostas", 0))
    colunas[1].metric("Confirmados", resumo.get("confirmados", 0))
    colunas[2].metric("Recusados", resumo.get("recusados", 0))
    colunas[3].metric("Crianças", resumo.get("criancas", 0))

    st.subheader("Lista de portaria")
    if not lista_portaria:
        st.info("Ainda não há convidados confirmados.")
        return

    busca = st.text_input(
        "Pesquisar nome", placeholder="Digite parte do nome...", key="admin_busca_nome"
    )
    termo = busca.strip().casefold()
    exibicao = (
        [item for item in lista_portaria if termo in item["nome"].casefold()]
        if termo else lista_portaria
    )
    st.caption(
        f"{len(exibicao)} pessoa(s) encontrada(s) de {len(lista_portaria)} na lista."
    )
    st.dataframe(exibicao, use_container_width=True, hide_index=True)
    st.download_button(
        "Baixar lista completa para a portaria",
        data=gerar_csv(lista_portaria),
        file_name="lista_portaria_rapha40.csv",
        mime="text/csv",
        type="primary",
    )


def gerar_csv(registros: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["Nome", "Tipo"])
    for registro in registros:
        writer.writerow([registro.get("nome", ""), registro.get("tipo", "")])
    return buffer.getvalue().encode("utf-8-sig")
