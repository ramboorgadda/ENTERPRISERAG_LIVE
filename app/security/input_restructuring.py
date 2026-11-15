from __future__ import annotations

from app.config import settings


def _get_encoding(model: str):
    try:
        import tiktoken

        try:
            return tiktoken.encoding_for_model(model)
        except Exception:
            return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def count_tokens(text: str) -> int:
    if not text:
        return 0

    enc = _get_encoding(settings.llm_model_answer)
    if enc is not None:
        return len(enc.encode(text))

    # Fallback heuristic when tokenizer isn't available.
    return max(1, len(text) // 4)


def restructure_input(text: str) -> tuple[str, str]:
    text = (text or "").strip()
    if not text:
        return "", "empty"

    max_tokens = max(1, settings.max_input_tokens)
    token_count = count_tokens(text)
    if token_count <= max_tokens:
        return text, "original"

    enc = _get_encoding(settings.llm_model_answer)
    if enc is None:
        # Character fallback roughly mirrors token clipping.
        max_chars = max_tokens * 4
        return text[:max_chars], "truncated"

    clipped_ids = enc.encode(text)[:max_tokens]
    return enc.decode(clipped_ids), "truncated"