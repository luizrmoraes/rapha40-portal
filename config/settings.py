from datetime import datetime
from zoneinfo import ZoneInfo

EVENTO_NOME = "Rapha 40"
DATA_EVENTO = "10/10/2026"
HORA_EVENTO = "16h"
LOCAL_EVENTO = "Churrasqueira 2"
CONDOMINIO = "Condomínio Be Happy Freguesia"
ACESSO1 = "Estr. do Capenha, 1467"
ACESSO2 = "Trav. Cunha Galvão, 205"

TZ_EVENTO = ZoneInfo("America/Sao_Paulo")

# Controle da surpresa:
# "rsvp"   -> mostra somente confirmação de presença.
# "festa"  -> libera mural, Arquivo 40 e memórias.
MODO_FORCADO = "rsvp"

# Opcional: caso queira liberar automaticamente no dia.
LIBERAR_PORTAL_EM = datetime(
    2026,
    10,
    10,
    14,
    0,
    tzinfo=TZ_EVENTO,
)

MAX_ACOMPANHANTES_ADULTOS = 5
MAX_CRIANCAS = 6


def obter_modo_portal() -> str:
    """
    Define o modo efetivo do portal.

    Enquanto MODO_FORCADO for 'rsvp' ou 'festa',
    ele prevalece sobre a regra de data/hora.
    Defina como None para ativação automática.
    """
    if MODO_FORCADO in {"rsvp", "festa"}:
        return MODO_FORCADO

    agora = datetime.now(TZ_EVENTO)

    if agora >= LIBERAR_PORTAL_EM:
        return "festa"

    return "rsvp"