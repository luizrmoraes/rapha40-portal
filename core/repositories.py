import psycopg2

from core.database import get_connection


def criar_rsvp(
    nome_principal: str,
    vai_comparecer: bool,
    quantidade_criancas: int,
    acompanhantes: list[str],
) -> str:
    """
    Grava o RSVP e seus acompanhantes em uma única transação.

    Retorna o UUID do RSVP criado.
    """
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                insert into public.rsvps (
                    nome_principal,
                    vai_comparecer,
                    quantidade_criancas,
                    status,
                    origem
                )
                values (%s, %s, %s, %s, %s)
                returning id;
                """,
                (
                    nome_principal,
                    vai_comparecer,
                    quantidade_criancas,
                    "confirmado" if vai_comparecer else "recusado",
                    "portal",
                ),
            )

            rsvp_id = str(cursor.fetchone()[0])

            if vai_comparecer and acompanhantes:
                dados_acompanhantes = [
                    (rsvp_id, nome)
                    for nome in acompanhantes
                ]

                cursor.executemany(
                    """
                    insert into public.rsvp_acompanhantes (
                        rsvp_id,
                        nome_completo
                    )
                    values (%s, %s);
                    """,
                    dados_acompanhantes,
                )

        connection.commit()

        return rsvp_id

    except Exception:
        connection.rollback()
        raise