from __future__ import annotations

from typing import Iterable


DEFAULT_ENCODINGS: tuple[str, ...] = ("utf-8", "cp1252", "latin-1")


def detect_encoding(cfg_bytes: bytes) -> str | None:
    """Best-effort encoding detection using chardet if available."""
    try:
        import chardet  # type: ignore
    except Exception:
        return None

    result = chardet.detect(cfg_bytes)
    encoding = result.get("encoding")
    confidence = float(result.get("confidence") or 0.0)
    if encoding and confidence >= 0.5:
        return str(encoding)
    return None


def decode_cfg_bytes(
    cfg_bytes: bytes,
    extra_candidates: Iterable[str] | None = None,
) -> tuple[str, str]:
    """Decode COMTRADE CFG bytes with robust fallback chain.

    Returns
    -------
    tuple[text, encoding_used]
    """
    candidates: list[str] = []
    detected = detect_encoding(cfg_bytes)
    if detected:
        candidates.append(detected)

    if extra_candidates:
        for enc in extra_candidates:
            if enc and enc not in candidates:
                candidates.append(enc)

    for enc in DEFAULT_ENCODINGS:
        if enc not in candidates:
            candidates.append(enc)

    for enc in candidates:
        try:
            return cfg_bytes.decode(enc), enc
        except UnicodeDecodeError:
            continue

    return cfg_bytes.decode("latin-1", errors="replace"), "latin-1"


def write_cfg_as_utf8(cfg_bytes: bytes, target_path: str, extra_candidates: Iterable[str] | None = None) -> str:
    """Decode CFG using fallback encoding chain and rewrite in UTF-8.

    Returns encoding used for decode.
    """
    text, used_encoding = decode_cfg_bytes(cfg_bytes, extra_candidates=extra_candidates)
    with open(target_path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return used_encoding
