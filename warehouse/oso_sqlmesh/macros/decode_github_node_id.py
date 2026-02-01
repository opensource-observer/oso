from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator

# Msgpack format markers
MSGPACK_UINT8 = 204  # 0xcc
MSGPACK_UINT16 = 205  # 0xcd
MSGPACK_UINT32 = 206  # 0xce
MSGPACK_UINT64 = 207  # 0xcf
MSGPACK_FIXINT_MAX = 127  # 0x7f - values 0x00-0x7f are fixint

# Bit shift constants
SHIFT_8 = 1 << 8
SHIFT_16 = 1 << 16
SHIFT_24 = 1 << 24
SHIFT_32 = 1 << 32
SHIFT_40 = 1 << 40
SHIFT_48 = 1 << 48
SHIFT_56 = 1 << 56


@macro()
def decode_github_node_id(
    evaluator: MacroEvaluator,
    node_id_exp: exp.Expression,
):
    """
    Decodes a GitHub GraphQL Node ID to its underlying integer ID.

    Supports two formats:
    1. Legacy: Base64 "Type:ID" (e.g., `MDQ6VXNlcjEyMzQ1` -> `12345`).
    2. Next-gen: URL-safe Base64 msgpack `[type, id]` (e.g., `U_kgDOBbc7Ag` -> `57900666`).

    Format detection: `_` in the string implies next-gen format.

    Next-gen Msgpack structure:
    - Byte 0: 0x92 (fixarray of 2 elements)
    - Byte 1: Type indicator (0x00=User, 0x01=Repo, etc.)
    - Byte 2+: Integer encoded as fixint/uint8/uint16/uint32/uint64

    Args:
        evaluator: SQLMesh macro evaluator
        node_id_exp: SQL expression containing the Node ID string

    Returns:
        SQL expression returning the decoded BIGINT ID, or NULL on failure.
    """
    from sqlmesh.core.dialect import parse_one

    if evaluator.runtime_stage == "loading":
        return parse_one("CAST(NULL AS BIGINT)", dialect="trino")

    dialect = evaluator.engine_adapter.dialect

    if dialect == "duckdb":
        return _build_duckdb_decoder(node_id_exp)
    elif dialect == "trino":
        return _build_trino_decoder(node_id_exp)
    else:
        raise ValueError(f"Unsupported dialect: {dialect}")


def _get_byte_from_hex_duckdb(hex_exp: exp.Expression, pos: int) -> exp.Expression:
    """Extract byte at 1-indexed position from hex string (DuckDB)."""
    hex_pos = (pos - 1) * 2 + 1
    two_chars = exp.Substring(
        this=hex_exp,
        start=exp.Literal.number(hex_pos),
        length=exp.Literal.number(2),
    )
    hex_with_prefix = exp.Concat(
        expressions=[exp.Literal.string("0x"), two_chars],
        safe=False,
        coalesce=False,
    )
    # Use TRY_CAST + COALESCE to handle out-of-bounds or invalid hex gracefully
    return exp.Coalesce(
        this=exp.TryCast(this=hex_with_prefix, to=exp.DataType.build("BIGINT")),
        expressions=[exp.Literal.number(0)],
    )


def _get_byte_from_hex_trino(hex_exp: exp.Expression, pos: int) -> exp.Expression:
    """Extract byte at 1-indexed position from hex string (Trino)."""
    hex_pos = (pos - 1) * 2 + 1
    two_chars = exp.Substring(
        this=hex_exp,
        start=exp.Literal.number(hex_pos),
        length=exp.Literal.number(2),
    )
    # Use TRY + COALESCE to handle out-of-bounds or invalid hex gracefully
    return exp.Coalesce(
        this=exp.Try(
            this=exp.Anonymous(
                this="from_base",
                expressions=[two_chars, exp.Literal.number(16)],
            )
        ),
        expressions=[exp.Literal.number(0)],
    )


def _build_uint_value_duckdb(bytes_list: list[exp.Expression]) -> exp.Expression:
    """Build uint value from bytes using arithmetic (DuckDB)."""
    num_bytes = len(bytes_list)
    if num_bytes == 1:
        return bytes_list[0]

    shifts = [SHIFT_8, SHIFT_16, SHIFT_24, SHIFT_32, SHIFT_40, SHIFT_48, SHIFT_56]
    result = bytes_list[-1]
    for i, byte_exp in enumerate(reversed(bytes_list[:-1])):
        shift_amount = shifts[i]
        shifted = exp.Mul(this=byte_exp, expression=exp.Literal.number(shift_amount))
        result = exp.Add(this=shifted, expression=result)
    return result


def _build_uint_value_trino(bytes_list: list[exp.Expression]) -> exp.Expression:
    """Build uint value from bytes using bitwise ops (Trino)."""
    num_bytes = len(bytes_list)
    if num_bytes == 1:
        return bytes_list[0]

    shifts = [8, 16, 24, 32, 40, 48, 56]
    result = bytes_list[-1]
    for i, byte_exp in enumerate(reversed(bytes_list[:-1])):
        shift_amount = shifts[i]
        shifted = exp.Anonymous(
            this="bitwise_left_shift",
            expressions=[byte_exp, exp.Literal.number(shift_amount)],
        )
        result = exp.BitwiseOr(this=shifted, expression=result)
    return result


def _build_msgpack_case_expr(
    marker: exp.Expression,
    uint8_val: exp.Expression,
    uint16_val: exp.Expression,
    uint32_val: exp.Expression,
    uint64_val: exp.Expression,
) -> exp.Expression:
    """Build CASE expression for msgpack integer decoding."""
    return exp.Case(
        ifs=[
            exp.If(
                this=exp.EQ(this=marker, expression=exp.Literal.number(MSGPACK_UINT64)),
                true=uint64_val,
            ),
            exp.If(
                this=exp.EQ(this=marker, expression=exp.Literal.number(MSGPACK_UINT32)),
                true=uint32_val,
            ),
            exp.If(
                this=exp.EQ(this=marker, expression=exp.Literal.number(MSGPACK_UINT16)),
                true=uint16_val,
            ),
            exp.If(
                this=exp.EQ(this=marker, expression=exp.Literal.number(MSGPACK_UINT8)),
                true=uint8_val,
            ),
            exp.If(
                this=exp.LTE(
                    this=marker, expression=exp.Literal.number(MSGPACK_FIXINT_MAX)
                ),
                true=marker,  # fixint: marker IS the value
            ),
        ],
        default=exp.Null(),
    )


def _normalize_url_safe_base64(suffix_exp: exp.Expression) -> exp.Expression:
    """Convert URL-safe base64 chars to standard base64."""
    replaced1 = exp.Anonymous(
        this="replace",
        expressions=[suffix_exp, exp.Literal.string("-"), exp.Literal.string("+")],
    )
    return exp.Anonymous(
        this="replace",
        expressions=[replaced1, exp.Literal.string("_"), exp.Literal.string("/")],
    )


def _build_legacy_decoder_duckdb(node_id_exp: exp.Expression) -> exp.Expression:
    """Decode legacy Node ID (base64 'Type:ID') in DuckDB."""
    decoded = exp.Anonymous(this="from_base64", expressions=[node_id_exp])
    decoded_str = exp.Cast(this=decoded, to=exp.DataType.build("VARCHAR"))
    extracted = exp.RegexpExtract(
        this=decoded_str,
        expression=exp.Literal.string(r"(\d+)$"),
        group=exp.Literal.number(1),
    )
    return exp.Cast(this=extracted, to=exp.DataType.build("BIGINT"))


def _build_legacy_decoder_trino(node_id_exp: exp.Expression) -> exp.Expression:
    """Decode legacy Node ID (base64 'Type:ID') in Trino."""
    decoded = exp.Anonymous(this="from_base64", expressions=[node_id_exp])
    decoded_str = exp.Anonymous(this="from_utf8", expressions=[decoded])
    extracted = exp.Anonymous(
        this="regexp_extract",
        expressions=[decoded_str, exp.Literal.string(r"(\d+)$"), exp.Literal.number(1)],
    )
    return exp.Cast(this=extracted, to=exp.DataType.build("BIGINT"))


def _extract_suffix_after_underscore_duckdb(
    node_id_exp: exp.Expression,
) -> exp.Expression:
    """Extract substring after first underscore (DuckDB)."""
    underscore_pos = exp.Anonymous(
        this="instr",
        expressions=[node_id_exp, exp.Literal.string("_")],
    )
    return exp.Substring(
        this=node_id_exp,
        start=exp.Add(this=underscore_pos, expression=exp.Literal.number(1)),
    )


def _extract_suffix_after_underscore_trino(
    node_id_exp: exp.Expression,
) -> exp.Expression:
    """Extract substring after first underscore (Trino)."""
    underscore_pos = exp.Anonymous(
        this="strpos",
        expressions=[node_id_exp, exp.Literal.string("_")],
    )
    return exp.Anonymous(
        this="substr",
        expressions=[
            node_id_exp,
            exp.Add(this=underscore_pos, expression=exp.Literal.number(1)),
        ],
    )


def _pad_base64_duckdb(normalized_exp: exp.Expression) -> exp.Expression:
    """Add base64 padding using repeat (DuckDB)."""
    str_len = exp.Length(this=normalized_exp)
    sub_expr = exp.Sub(
        this=exp.Literal.number(4),
        expression=exp.Mod(this=str_len, expression=exp.Literal.number(4)),
    )
    padding_needed = exp.Mod(
        this=exp.Paren(this=sub_expr),
        expression=exp.Literal.number(4),
    )
    padding = exp.Anonymous(
        this="repeat",
        expressions=[exp.Literal.string("="), padding_needed],
    )
    return exp.Concat(expressions=[normalized_exp, padding], safe=False, coalesce=False)


def _pad_base64_trino(normalized_exp: exp.Expression) -> exp.Expression:
    """Add base64 padding using rpad (Trino)."""
    str_len = exp.Anonymous(this="length", expressions=[normalized_exp])
    sub_expr = exp.Sub(
        this=exp.Literal.number(4),
        expression=exp.Mod(this=str_len, expression=exp.Literal.number(4)),
    )
    padding_needed = exp.Mod(
        this=exp.Paren(this=sub_expr),
        expression=exp.Literal.number(4),
    )
    target_len = exp.Add(this=str_len, expression=padding_needed)
    return exp.Anonymous(
        this="rpad",
        expressions=[normalized_exp, target_len, exp.Literal.string("=")],
    )


def _build_nextgen_decoder_duckdb(node_id_exp: exp.Expression) -> exp.Expression:
    """Decode next-gen Node ID (URL-safe base64 msgpack) in DuckDB."""
    suffix = _extract_suffix_after_underscore_duckdb(node_id_exp)
    normalized = _normalize_url_safe_base64(suffix)
    padded = _pad_base64_duckdb(normalized)
    decoded_bytes = exp.Anonymous(this="from_base64", expressions=[padded])
    hex_str = exp.Anonymous(this="hex", expressions=[decoded_bytes])

    marker = _get_byte_from_hex_duckdb(hex_str, 3)
    bytes_4_to_11 = [_get_byte_from_hex_duckdb(hex_str, i) for i in range(4, 12)]

    uint8_val = bytes_4_to_11[0]
    uint16_val = _build_uint_value_duckdb(bytes_4_to_11[:2])
    uint32_val = _build_uint_value_duckdb(bytes_4_to_11[:4])
    uint64_val = _build_uint_value_duckdb(bytes_4_to_11[:8])

    return _build_msgpack_case_expr(
        marker, uint8_val, uint16_val, uint32_val, uint64_val
    )


def _build_nextgen_decoder_trino(node_id_exp: exp.Expression) -> exp.Expression:
    """Decode next-gen Node ID (URL-safe base64 msgpack) in Trino."""
    suffix = _extract_suffix_after_underscore_trino(node_id_exp)
    normalized = _normalize_url_safe_base64(suffix)
    padded = _pad_base64_trino(normalized)
    decoded_bytes = exp.Anonymous(this="from_base64", expressions=[padded])
    hex_str = exp.Anonymous(this="to_hex", expressions=[decoded_bytes])

    marker = _get_byte_from_hex_trino(hex_str, 3)
    bytes_4_to_11 = [_get_byte_from_hex_trino(hex_str, i) for i in range(4, 12)]

    uint8_val = bytes_4_to_11[0]
    uint16_val = _build_uint_value_trino(bytes_4_to_11[:2])
    uint32_val = _build_uint_value_trino(bytes_4_to_11[:4])
    uint64_val = _build_uint_value_trino(bytes_4_to_11[:8])

    return _build_msgpack_case_expr(
        marker, uint8_val, uint16_val, uint32_val, uint64_val
    )


def _contains_underscore_duckdb(node_id_exp: exp.Expression) -> exp.Expression:
    """Check if string contains underscore (DuckDB)."""
    return exp.GT(
        this=exp.Anonymous(
            this="instr",
            expressions=[node_id_exp, exp.Literal.string("_")],
        ),
        expression=exp.Literal.number(0),
    )


def _contains_underscore_trino(node_id_exp: exp.Expression) -> exp.Expression:
    """Check if string contains underscore (Trino)."""
    return exp.GT(
        this=exp.Anonymous(
            this="strpos",
            expressions=[node_id_exp, exp.Literal.string("_")],
        ),
        expression=exp.Literal.number(0),
    )


def _build_decoder(
    node_id_exp: exp.Expression,
    contains_underscore_fn,
    legacy_decoder_fn,
    nextgen_decoder_fn,
) -> exp.Expression:
    """Build complete decoder with format detection and error handling."""
    case_expr = exp.Case(
        ifs=[
            exp.If(
                this=exp.Is(this=node_id_exp, expression=exp.Null()),
                true=exp.Null(),
            ),
            exp.If(
                this=contains_underscore_fn(node_id_exp),
                true=nextgen_decoder_fn(node_id_exp),
            ),
        ],
        default=legacy_decoder_fn(node_id_exp),
    )
    return exp.Try(this=case_expr)


def _build_duckdb_decoder(node_id_exp: exp.Expression) -> exp.Expression:
    """Build complete DuckDB decoder."""
    return _build_decoder(
        node_id_exp,
        _contains_underscore_duckdb,
        _build_legacy_decoder_duckdb,
        _build_nextgen_decoder_duckdb,
    )


def _build_trino_decoder(node_id_exp: exp.Expression) -> exp.Expression:
    """Build complete Trino decoder."""
    return _build_decoder(
        node_id_exp,
        _contains_underscore_trino,
        _build_legacy_decoder_trino,
        _build_nextgen_decoder_trino,
    )
