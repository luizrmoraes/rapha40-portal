"""Processamento compartilhado de JPEG, MPO, PNG e WebP."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_PIXELS = 40_000_000
FORMATOS = {
    "JPEG": ("jpg", "image/jpeg"),
    "MPO": ("mpo", "image/mpo"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}


def _abrir(conteudo: bytes, limite_bytes: int) -> tuple[Image.Image, str]:
    if not conteudo or len(conteudo) > limite_bytes:
        raise ValueError(
            f"A imagem deve ter no máximo {limite_bytes // (1024 * 1024)} MB."
        )
    try:
        with Image.open(BytesIO(conteudo)) as original:
            formato = (original.format or "").upper()
            if formato not in FORMATOS:
                raise ValueError("Use uma imagem JPEG, MPO, PNG ou WebP.")
            if original.width * original.height > MAX_PIXELS:
                raise ValueError("A resolução da imagem excede o limite permitido.")
            if formato == "MPO":
                original.seek(0)
            original.load()
            imagem = ImageOps.exif_transpose(original)
            imagem.load()
            return imagem.copy(), formato
    except ValueError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Não foi possível abrir esta imagem.") from exc


def _webp(imagem: Image.Image, limite: int, qualidade: int) -> bytes:
    copia = imagem.copy()
    copia.thumbnail((limite, limite), Image.Resampling.LANCZOS)
    if copia.mode in ("RGBA", "LA") or (
        copia.mode == "P" and "transparency" in copia.info
    ):
        fundo = Image.new("RGB", copia.size, "white")
        rgba = copia.convert("RGBA")
        fundo.paste(rgba, mask=rgba.getchannel("A"))
        copia = fundo
    else:
        copia = copia.convert("RGB")
    saida = BytesIO()
    copia.save(saida, format="WEBP", quality=qualidade, method=6)
    return saida.getvalue()


def preparar_display(
    conteudo: bytes, *, limite_mb: int = 12
) -> tuple[bytes, str, str]:
    """Devolve display WebP, extensão e MIME reais do original."""
    imagem, formato = _abrir(conteudo, limite_mb * 1024 * 1024)
    extensao, mime = FORMATOS[formato]
    return _webp(imagem, 1600, 82), extensao, mime


def preparar_historico(conteudo: bytes) -> tuple[bytes, bytes]:
    """Devolve miniatura e versão de exibição, sem guardar original."""
    imagem, _ = _abrir(conteudo, 15 * 1024 * 1024)
    return _webp(imagem, 480, 76), _webp(imagem, 1600, 82)
