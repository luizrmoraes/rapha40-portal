import streamlit as st

from config.settings import (
    CONDOMINIO,
    DATA_EVENTO,
    EVENTO_NOME,
    HORA_EVENTO,
    LOCAL_EVENTO,
    MAX_ACOMPANHANTES_ADULTOS,
    MAX_CRIANCAS,
)
from core.repositories import criar_rsvp


def render_rsvp() -> None:
    inicializar_estado_rsvp()

    st.title("Confirme sua presença")

    st.write(
        f"Para organizar a lista de acesso nas portarias do "
        f"{CONDOMINIO}, confirme seus dados abaixo."
    )

    st.caption(
        f"{EVENTO_NOME} · {DATA_EVENTO} · {HORA_EVENTO} · {LOCAL_EVENTO}"
    )

    presenca = st.radio(
        "Você vai conseguir comparecer?",
        options=["Sim, estarei lá", "Não vou conseguir comparecer"],
        horizontal=True,
        key="rsvp_presenca",
    )

    if presenca == "Sim, estarei lá":
        renderizar_confirmacao()
    else:
        renderizar_recusa()


def renderizar_confirmacao() -> None:
    nome_principal = st.text_input(
        "Seu nome completo *",
        placeholder="Ex.: João da Silva",
        max_chars=120,
        key="rsvp_nome_principal",
    )

    acompanhantes = []

    for indice in range(st.session_state.qtd_acompanhantes):
        col_campo, col_remover = st.columns([5, 1])

        with col_campo:
            nome_acompanhante = st.text_input(
                f"Nome completo do acompanhante {indice + 1} *",
                placeholder=f"Ex.: Acompanhante {indice + 1}",
                max_chars=120,
                key=f"rsvp_acompanhante_{indice}",
            )
            acompanhantes.append(nome_acompanhante)

        with col_remover:
            st.write("")
            if st.button(
                "×",
                key=f"btn_remover_acompanhante_{indice}",
                help=f"Remover acompanhante {indice + 1}",
                type="secondary",
            ):
                remover_acompanhante(indice)
                st.rerun()

    if st.session_state.qtd_acompanhantes < MAX_ACOMPANHANTES_ADULTOS:
        if st.button(
            "＋ Adicionar acompanhante",
            key="btn_adicionar_acompanhante",
            type="secondary",
        ):
            st.session_state.qtd_acompanhantes += 1
            st.rerun()

    if st.session_state.qtd_acompanhantes >= MAX_ACOMPANHANTES_ADULTOS:
        st.caption(
            f"Limite de {MAX_ACOMPANHANTES_ADULTOS} acompanhantes atingido."
        )

    quantidade_criancas = st.number_input(
        "Quantidade de crianças",
        min_value=0,
        max_value=MAX_CRIANCAS,
        value=0,
        step=1,
        key="rsvp_quantidade_criancas",
        help="Informe apenas a quantidade de crianças que estarão no seu grupo.",
    )

    confirmar = st.button(
        "Confirmar presença",
        type="primary",
        use_container_width=True,
        key="btn_confirmar_presenca",
    )

    if not confirmar:
        return

    erros = validar_formulario(
        nome_principal=nome_principal,
        acompanhantes=acompanhantes,
    )

    if erros:
        for erro in erros:
            st.error(erro)
        return

    dados_rsvp = {
        "nome_principal": normalizar_nome(nome_principal),
        "vai_comparecer": True,
        "acompanhantes": [
            normalizar_nome(nome)
            for nome in acompanhantes
            if nome.strip()
        ],
        "quantidade_criancas": int(quantidade_criancas),
    }

    salvar_e_ir_para_resultado(dados_rsvp)


def renderizar_recusa() -> None:
    nome_principal = st.text_input(
        "Seu nome completo *",
        placeholder="Ex.: João da Silva",
        max_chars=120,
        key="rsvp_nome_principal_recusa",
    )

    enviar_recusa = st.button(
        "Enviar resposta",
        type="primary",
        use_container_width=True,
        key="btn_enviar_recusa",
    )

    if not enviar_recusa:
        return

    if len(nome_principal.strip()) < 3:
        st.error("Informe seu nome completo.")
        return

    dados_rsvp = {
        "nome_principal": normalizar_nome(nome_principal),
        "vai_comparecer": False,
        "acompanhantes": [],
        "quantidade_criancas": 0,
    }

    salvar_e_ir_para_resultado(dados_rsvp)


def salvar_e_ir_para_resultado(dados_rsvp: dict) -> None:
    try:
        with st.spinner("Registrando sua resposta..."):
            rsvp_id = criar_rsvp(
                nome_principal=dados_rsvp["nome_principal"],
                vai_comparecer=dados_rsvp["vai_comparecer"],
                quantidade_criancas=dados_rsvp["quantidade_criancas"],
                acompanhantes=dados_rsvp["acompanhantes"],
            )

        dados_rsvp["rsvp_id"] = rsvp_id
        st.session_state.rsvp_dados = dados_rsvp
        st.session_state.tela = (
            "confirmado"
            if dados_rsvp["vai_comparecer"]
            else "recusado"
        )

        st.rerun()

    except Exception as erro:
        st.error(
            "Não foi possível registrar sua resposta neste momento. "
            "Por favor, tente novamente em alguns minutos."
        )

        # Mantenha durante o desenvolvimento.
        # Remova antes de divulgar o link aos convidados.
        with st.expander("Detalhes técnicos"):
            st.exception(erro)


def inicializar_estado_rsvp() -> None:
    if "qtd_acompanhantes" not in st.session_state:
        st.session_state.qtd_acompanhantes = 0


def remover_acompanhante(indice_removido: int) -> None:
    quantidade_atual = st.session_state.qtd_acompanhantes

    for indice in range(indice_removido, quantidade_atual - 1):
        chave_atual = f"rsvp_acompanhante_{indice}"
        chave_proxima = f"rsvp_acompanhante_{indice + 1}"

        st.session_state[chave_atual] = st.session_state.get(
            chave_proxima,
            "",
        )

    chave_ultimo = f"rsvp_acompanhante_{quantidade_atual - 1}"

    if chave_ultimo in st.session_state:
        del st.session_state[chave_ultimo]

    st.session_state.qtd_acompanhantes -= 1


def validar_formulario(
    nome_principal: str,
    acompanhantes: list[str],
) -> list[str]:
    erros = []

    if len(nome_principal.strip()) < 3:
        erros.append("Informe seu nome completo.")

    for indice, acompanhante in enumerate(acompanhantes, start=1):
        if len(acompanhante.strip()) < 3:
            erros.append(
                f"Informe o nome completo do acompanhante {indice}."
            )

    return erros


def normalizar_nome(nome: str) -> str:
    return " ".join(nome.strip().split()).title()