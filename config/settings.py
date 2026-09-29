from datetime import datetime, time
from zoneinfo import ZoneInfo


EVENTO_NOME = "Rapha 40"
DATA_EVENTO = "10/10/2026"  # Ajuste aqui para a data real da festa.
HORA_EVENTO = "16h"
LOCAL_EVENTO = "Churrasqueira 2"
CONDOMINIO = "Condomínio Be Happy Freguesia"
ACESSO1 = "Estr. do Capenha, 1467"
ACESSO2 = "Trav. Cunha Galvão, 205"

TZ_EVENTO = ZoneInfo("America/Sao_Paulo")

# None = ativação automática; "rsvp" ou "festa" = modo forçado.
MODO_FORCADO = None

# Horário em que o portal da festa será liberado no dia do evento.
HORA_LIBERACAO = time(14, 0)

MAX_ACOMPANHANTES_ADULTOS = 5
MAX_CRIANCAS = 6


def obter_modo_portal() -> str:
    if MODO_FORCADO in {"rsvp", "festa"}:
        return MODO_FORCADO

    data_evento = datetime.strptime(DATA_EVENTO, "%d/%m/%Y").date()
    liberar_em = datetime.combine(
        data_evento,
        HORA_LIBERACAO,
        tzinfo=TZ_EVENTO,
    )

    return "festa" if datetime.now(TZ_EVENTO) >= liberar_em else "rsvp"