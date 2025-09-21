import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any


TOKEN_REGEX = re.compile(r"^0[xX][0-9A-Fa-f_]+$")
SPLIT_REGEX = re.compile(r"[,\s]+")  # comma, whitespace (space/tab/newline) in any combination


@dataclass
class ParseResult:
    data: bytes
    warnings: List[str]
    trunc_info: List[Dict[str, Any]]
    byte_spans: List[Dict[str, Any]]


def tokenize_flexible_hex(input_str: str) -> List[str]:
    if not input_str:
        return []
    parts = SPLIT_REGEX.split(input_str)
    return [p for p in parts if p]


def _normalize_token(token: str) -> str:
    if not TOKEN_REGEX.match(token):
        raise ValueError(f"Invalid token format: '{token}'")
    # strip 0x/0X
    body = token[2:]
    # remove underscores
    body = body.replace("_", "")
    # odd digits -> left pad 0
    if len(body) % 2 == 1:
        body = "0" + body
    return body.lower()


def parse_token_to_bytes(token: str) -> bytes:
    body = _normalize_token(token)
    # length in bytes
    nbytes = len(body) // 2
    # parse integer and emit little-endian of exact length
    try:
        value = int(body, 16)
    except ValueError:
        # Should be unreachable after regex, but keep for safety
        raise ValueError(f"Invalid token format: '{token}'")
    return value.to_bytes(nbytes, byteorder="little")


def assemble_bytes(tokens: List[str], target_len: Optional[int]) -> Tuple[bytes, Dict[str, Any]]:
    warnings: List[str] = []
    trunc_info: List[Dict[str, Any]] = []
    byte_spans: List[Dict[str, Any]] = []

    # Expand tokens and collect spans
    output = bytearray()
    for ti, tok in enumerate(tokens):
        tb = parse_token_to_bytes(tok)
        for bi, b in enumerate(tb):
            output.append(b)
            byte_spans.append({
                "token_index": ti,  # 0-based index into tokens
                "offset": bi,       # byte offset within token after LE expansion
            })

    if target_len is None:
        return (bytes(output), {
            "warnings": warnings,
            "trunc_info": trunc_info,
            "byte_spans": byte_spans,
        })

    n = int(target_len)
    cur_len = len(output)
    if cur_len == n:
        return (bytes(output), {
            "warnings": warnings,
            "trunc_info": trunc_info,
            "byte_spans": byte_spans,
        })

    if cur_len < n:
        # pad tail with zero bytes, mark spans as padded
        pad_from = cur_len
        for _ in range(n - cur_len):
            output.append(0)
            byte_spans.append({
                "padded": True,
            })
        warnings.append(f"padded {n - cur_len} bytes with 0x00 from index {pad_from} to {n-1}")
        meta = {
            "warnings": warnings,
            "trunc_info": trunc_info,
            "byte_spans": byte_spans,
            "padding_info": {"from": pad_from, "to": n - 1},
        }
        return (bytes(output), meta)

    # cur_len > n: truncate from the tail (high side)
    # Collect truncation info for dropped bytes with their original mapping
    for gi in range(n, cur_len):
        span = byte_spans[gi] if gi < len(byte_spans) else {}
        info = {"global_index": gi}
        if isinstance(span, dict):
            if "token_index" in span:
                info["token_index"] = span["token_index"]
            if "offset" in span:
                info["offset"] = span["offset"]
        trunc_info.append(info)
    warnings.append(f"truncated {cur_len - n} bytes from tail (indices {n}..{cur_len-1})")
    # slice head
    new_output = bytes(output[:n])
    new_spans = byte_spans[:n]
    meta = {
        "warnings": warnings,
        "trunc_info": trunc_info,
        "byte_spans": new_spans,
    }
    return (new_output, meta)


def parse_flexible_input(input_str: str, target_len: Optional[int]) -> ParseResult:
    tokens = tokenize_flexible_hex(input_str)
    # Validate each token and collect errors with indices (1-based for UX)
    errors = []
    for idx, tok in enumerate(tokens, start=1):
        if not TOKEN_REGEX.match(tok):
            errors.append((idx, tok))
        else:
            # extra validation: ensure body has at least one hex digit after removing underscores
            body = tok[2:].replace("_", "")
            if len(body) == 0:
                errors.append((idx, tok))
            elif not re.fullmatch(r"[0-9A-Fa-f]+", body):
                errors.append((idx, tok))
    if errors:
        msgs = [f"token #{i}: '{t}'" for i, t in errors]
        raise ValueError("Invalid tokens: " + "; ".join(msgs))

    data, meta = assemble_bytes(tokens, target_len)
    return ParseResult(
        data=data,
        warnings=meta.get("warnings", []),
        trunc_info=meta.get("trunc_info", []),
        byte_spans=meta.get("byte_spans", []),
    )

