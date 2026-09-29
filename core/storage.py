from __future__ import annotations

from urllib.parse import urljoin

import streamlit as st
from supabase import Client, create_client

BUCKET_HISTORICO = "mural-historico"
BUCKET_ORIGINAIS = "memorias-originais"
BUCKET_MURAL = "memorias-mural"
_BUCKETS = {BUCKET_HISTORICO, BUCKET_ORIGINAIS, BUCKET_MURAL}
_BUCKETS_EXIBICAO = {BUCKET_HISTORICO, BUCKET_MURAL}


def _base_url() -> str:
    url = str(st.secrets["SUPABASE_URL"]).rstrip("/")
    if not url.startswith("https://"):
        raise ValueError("SUPABASE_URL deve ser a URL HTTPS do projeto.")
    return url


@st.cache_resource
def _cliente() -> Client:
    chave = str(st.secrets["supabase_storage"]["secret_key"])
    if not chave.startswith("sb_secret_"):
        raise ValueError("Configure uma secret key sb_secret_ para o Storage.")
    return create_client(_base_url(), chave)


def _validar_path(path: str) -> str:
    if not isinstance(path, str) or not path or path.startswith("/"):
        raise ValueError("Use um caminho relativo dentro do bucket.")
    if any(parte in {"", ".", ".."} for parte in path.split("/")):
        raise ValueError("Caminho invalido.")
    return path


def _validar_bucket(bucket: str) -> None:
    if bucket not in _BUCKETS:
        raise ValueError("Bucket nao permitido.")


def _url_assinada(bucket: str, path: str, validade_segundos: int) -> str:
    _validar_bucket(bucket)
    _validar_path(path)
    if not 60 <= validade_segundos <= 3600:
        raise ValueError("Validade deve estar entre 60 e 3600 segundos.")
    resposta = _cliente().storage.from_(bucket).create_signed_url(
        path, validade_segundos
    )
    if isinstance(resposta, dict):
        url = resposta.get("signedUrl") or resposta.get("signedURL")
    else:
        url = getattr(resposta, "signed_url", None)
    if not url:
        raise RuntimeError("Storage nao retornou URL assinada.")
    if url.startswith(("https://", "http://")):
        return url
    if url.startswith("/object/"):
        return f"{_base_url()}/storage/v1{url}"
    return urljoin(f"{_base_url()}/", url)


def url_exibicao(bucket: str, path: str, validade_segundos: int = 900) -> str:
    """Use apenas para registros ativos/aprovados obtidos de repositories."""
    if bucket not in _BUCKETS_EXIBICAO:
        raise ValueError("Nao gerar URL publica de originais.")
    return _url_assinada(bucket, path, validade_segundos)


def url_original_admin(path: str, validade_segundos: int = 300) -> str:
    if not st.session_state.get("admin_autenticado", False):
        raise PermissionError("Acesso administrativo necessario.")
    return _url_assinada(BUCKET_ORIGINAIS, path, validade_segundos)


def enviar_arquivo(
    bucket: str, path: str, conteudo: bytes, content_type: str
) -> None:
    """Gere paths unicos; valide tamanho e formato real antes de chamar."""
    _validar_bucket(bucket)
    _validar_path(path)
    if not isinstance(conteudo, bytes) or not conteudo:
        raise ValueError("Arquivo vazio ou invalido.")
    if not isinstance(content_type, str) or not content_type.startswith("image/"):
        raise ValueError("Somente imagens sao aceitas.")
    _cliente().storage.from_(bucket).upload(
        path=path,
        file=conteudo,
        file_options={"content-type": content_type, "upsert": "false"},
    )


def baixar_original_admin(path: str) -> bytes:
    if not st.session_state.get("admin_autenticado", False):
        raise PermissionError("Acesso administrativo necessario.")
    _validar_path(path)
    return _cliente().storage.from_(BUCKET_ORIGINAIS).download(path)


def excluir_original_admin(path: str) -> None:
    """Nao expor em tela ate conferir status verificado e pedir confirmacao."""
    if not st.session_state.get("admin_autenticado", False):
        raise PermissionError("Acesso administrativo necessario.")
    _validar_path(path)
    _cliente().storage.from_(BUCKET_ORIGINAIS).remove([path])

def remover_upload_falho(bucket: str, path: str) -> None:
    """Remove um objeto de um envio que não foi concluído."""
    if bucket not in {BUCKET_HISTORICO, BUCKET_ORIGINAIS, BUCKET_MURAL}:
        raise ValueError("Bucket não permitido para limpeza de upload.")
    _validar_path(path)
    _cliente().storage.from_(bucket).remove([path])

def url_preview_memoria_admin(
    path: str, validade_segundos: int = 300
) -> str:
    """Prévia da versão reduzida, somente em sessão admin."""
    if not st.session_state.get("admin_autenticado", False):
        raise PermissionError("Acesso administrativo necessário.")

    return _url_assinada(
        BUCKET_MURAL,
        path,
        validade_segundos,
    )