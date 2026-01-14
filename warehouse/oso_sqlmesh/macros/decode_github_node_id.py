from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def decode_github_node_id(
    evaluator: MacroEvaluator,
    node_id_exp: exp.Expression,
):
    """
    Decodes a GitHub GraphQL Node ID to its underlying integer actor ID.

    Supports two formats:
    1. Legacy: Base64 "Type:ID" (e.g., `MDQ6...` -> `4027037`).
    2. Next-gen: URL-safe Base64 msgpack `[type, id]` (e.g., `U_kg...` -> `57900666`).

    Format detection: `_` implies Next-gen.

    Next-gen Msgpack structure:
    - Byte 0: 0x92 (fixarray)
    - Byte 1: Type (0x00=User)
    - Byte 2+: Integer (fixint 0x00-0x7f, uint8 0xcc, uint16 0xcd, uint32 0xce)

    Args:
        evaluator: Macro evaluator
        node_id_exp: Node ID expression

    Returns:
        Expression returning integer ID or NULL.
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


def _build_legacy_decoder_duckdb(node_id_exp: exp.Expression) -> exp.Expression:
    """Decodes legacy Node ID (base64 "Type:ID") in DuckDB."""
    # Decode base64 blob -> varchar
    decoded = exp.Anonymous(
        this="from_base64",
        expressions=[node_id_exp],
    )
    decoded_str = exp.Cast(
        this=decoded,
        to=exp.DataType.build("VARCHAR"),
    )
    # Extract trailing digits (ID)
    extracted = exp.RegexpExtract(
        this=decoded_str,
        expression=exp.Literal.string(r"(\d+)$"),
        group=exp.Literal.number(1),
    )
    return exp.Cast(
        this=extracted,
        to=exp.DataType.build("BIGINT"),
    )


def _build_nextgen_decoder_duckdb(node_id_exp: exp.Expression) -> exp.Expression:
    """Decodes next-gen Node ID (URL-safe base64 msgpack) in DuckDB."""
    # Extract suffix after first underscore (safe for nested underscores)
    underscore_pos = exp.Anonymous(
        this="instr",
        expressions=[node_id_exp, exp.Literal.string("_")],
    )
    suffix_part = exp.Substring(
        this=node_id_exp,
        start=exp.Add(this=underscore_pos, expression=exp.Literal.number(1)),
    )

    # Normalize URL-safe base64: '-' -> '+', '_' -> '/'
    replaced1 = exp.Anonymous(
        this="replace",
        expressions=[suffix_part, exp.Literal.string("-"), exp.Literal.string("+")],
    )
    replaced2 = exp.Anonymous(
        this="replace",
        expressions=[replaced1, exp.Literal.string("_"), exp.Literal.string("/")],
    )

    # Calculate standard Base64 padding
    suffix_len = exp.Length(this=replaced2)
    padding_needed = exp.Mod(
        this=exp.Sub(
            this=exp.Literal.number(4),
            expression=exp.Mod(this=suffix_len, expression=exp.Literal.number(4)),
        ),
        expression=exp.Literal.number(4),
    )

    padding = exp.Anonymous(
        this="repeat",
        expressions=[exp.Literal.string("="), padding_needed],
    )
    padded = exp.Concat(
        expressions=[replaced2, padding],
        safe=False,
        coalesce=False,
    )

    decoded_bytes = exp.Anonymous(
        this="from_base64",
        expressions=[padded],
    )

    # DuckDB lacks get_byte; convert to hex for byte extraction
    hex_str = exp.Anonymous(
        this="hex",
        expressions=[decoded_bytes],
    )

    # Extract byte from hex string (1-indexed)
    def get_byte(hex_exp: exp.Expression, pos: int) -> exp.Expression:
        # Position in hex string: (pos-1)*2 + 1
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
        return exp.Cast(
            this=hex_with_prefix,
            to=exp.DataType.build("INTEGER"),
        )

    # Msgpack parsing
    marker = get_byte(hex_str, 3)

    # DuckDB: Use arithmetic for bitwise ops (b4<<24 | ... | b7)
    byte4 = get_byte(hex_str, 4)
    byte5 = get_byte(hex_str, 5)
    byte6 = get_byte(hex_str, 6)
    byte7 = get_byte(hex_str, 7)

    # uint32 (0xce)
    uint32_value = exp.Add(
        this=exp.Add(
            this=exp.Add(
                this=exp.Mul(
                    this=byte4,
                    expression=exp.Literal.number(1 << 24),
                ),
                expression=exp.Mul(
                    this=byte5,
                    expression=exp.Literal.number(1 << 16),
                ),
            ),
            expression=exp.Mul(
                this=byte6,
                expression=exp.Literal.number(1 << 8),
            ),
        ),
        expression=byte7,
    )

    # uint16 (0xcd)
    uint16_value = exp.Add(
        this=exp.Mul(
            this=byte4,
            expression=exp.Literal.number(1 << 8),
        ),
        expression=byte5,
    )

    # uint8 (0xcc)
    uint8_value = byte4

    # fixint (0x01-0x7f)
    fixint_value = marker

    return exp.Case(
        ifs=[
            exp.If(
                this=exp.EQ(this=marker, expression=exp.Literal.number(206)),  # 0xce
                true=uint32_value,
            ),
            exp.If(
                this=exp.EQ(this=marker, expression=exp.Literal.number(205)),  # 0xcd
                true=uint16_value,
            ),
            exp.If(
                this=exp.EQ(this=marker, expression=exp.Literal.number(204)),  # 0xcc
                true=uint8_value,
            ),
            exp.If(
                this=exp.LTE(
                    this=marker, expression=exp.Literal.number(127)
                ),  # <= 0x7f
                true=fixint_value,
            ),
        ],
        default=exp.Null(),
    )


def _build_duckdb_decoder(node_id_exp: exp.Expression) -> exp.Expression:
    """Builds the complete DuckDB decoder handling both formats."""
    # Check for underscore (next-gen format)
    contains_underscore = exp.GT(
        this=exp.Anonymous(
            this="instr",
            expressions=[node_id_exp, exp.Literal.string("_")],
        ),
        expression=exp.Literal.number(0),
    )

    legacy_result = _build_legacy_decoder_duckdb(node_id_exp)
    nextgen_result = _build_nextgen_decoder_duckdb(node_id_exp)

    case_expr = exp.Case(
        ifs=[
            exp.If(
                this=exp.Is(this=node_id_exp, expression=exp.Null()),
                true=exp.Null(),
            ),
            exp.If(
                this=contains_underscore,
                true=nextgen_result,
            ),
        ],
        default=legacy_result,
    )

    return exp.Try(this=case_expr)


def _build_legacy_decoder_trino(node_id_exp: exp.Expression) -> exp.Expression:
    """Decodes legacy Node ID in Trino."""
    # from_base64(node_id) -> varbinary -> varchar
    decoded = exp.Anonymous(
        this="from_base64",
        expressions=[node_id_exp],
    )
    decoded_str = exp.Anonymous(
        this="from_utf8",
        expressions=[decoded],
    )
    # Extract trailing digits
    extracted = exp.Anonymous(
        this="regexp_extract",
        expressions=[
            decoded_str,
            exp.Literal.string(r"(\d+)$"),
            exp.Literal.number(1),
        ],
    )
    return exp.Cast(
        this=extracted,
        to=exp.DataType.build("BIGINT"),
    )


def _build_nextgen_decoder_trino(node_id_exp: exp.Expression) -> exp.Expression:
    """Decodes next-gen Node ID in Trino."""
    # Split on underscore, take second part
    suffix_part = exp.Anonymous(
        this="element_at",
        expressions=[
            exp.Anonymous(
                this="split",
                expressions=[node_id_exp, exp.Literal.string("_")],
            ),
            exp.Literal.number(2),
        ],
    )

    # Normalize URL-safe base64
    replaced1 = exp.Anonymous(
        this="replace",
        expressions=[suffix_part, exp.Literal.string("-"), exp.Literal.string("+")],
    )
    replaced2 = exp.Anonymous(
        this="replace",
        expressions=[replaced1, exp.Literal.string("_"), exp.Literal.string("/")],
    )

    # Calculate padding
    suffix_len = exp.Anonymous(
        this="length",
        expressions=[replaced2],
    )
    padding_needed = exp.Mod(
        this=exp.Sub(
            this=exp.Literal.number(4),
            expression=exp.Mod(this=suffix_len, expression=exp.Literal.number(4)),
        ),
        expression=exp.Literal.number(4),
    )

    # Apply padding
    target_len = exp.Add(this=suffix_len, expression=padding_needed)
    padded = exp.Anonymous(
        this="rpad",
        expressions=[replaced2, target_len, exp.Literal.string("=")],
    )

    decoded_bytes = exp.Anonymous(
        this="from_base64",
        expressions=[padded],
    )

    # Helper: Extract byte at position (1-indexed)
    def get_byte(blob_exp: exp.Expression, pos: int) -> exp.Expression:
        # Trino lacks direct byte access; convert to hex and parse
        single_byte = exp.Anonymous(
            this="substr",
            expressions=[blob_exp, exp.Literal.number(pos), exp.Literal.number(1)],
        )
        hex_str = exp.Anonymous(
            this="to_hex",
            expressions=[single_byte],
        )
        return exp.Anonymous(
            this="from_base",
            expressions=[hex_str, exp.Literal.number(16)],
        )

    # Msgpack parsing
    marker = get_byte(decoded_bytes, 3)

    # uint32 (0xce)
    byte4 = get_byte(decoded_bytes, 4)
    byte5 = get_byte(decoded_bytes, 5)
    byte6 = get_byte(decoded_bytes, 6)
    byte7 = get_byte(decoded_bytes, 7)

    uint32_value = exp.BitwiseOr(
        this=exp.BitwiseOr(
            this=exp.BitwiseOr(
                this=exp.Anonymous(
                    this="bitwise_left_shift",
                    expressions=[byte4, exp.Literal.number(24)],
                ),
                expression=exp.Anonymous(
                    this="bitwise_left_shift",
                    expressions=[byte5, exp.Literal.number(16)],
                ),
            ),
            expression=exp.Anonymous(
                this="bitwise_left_shift",
                expressions=[byte6, exp.Literal.number(8)],
            ),
        ),
        expression=byte7,
    )

    # uint16 (0xcd)
    uint16_value = exp.BitwiseOr(
        this=exp.Anonymous(
            this="bitwise_left_shift",
            expressions=[byte4, exp.Literal.number(8)],
        ),
        expression=byte5,
    )

    # uint8 (0xcc)
    uint8_value = byte4

    # fixint (0x01-0x7f)
    fixint_value = marker

    return exp.Case(
        ifs=[
            exp.If(
                this=exp.EQ(this=marker, expression=exp.Literal.number(206)),  # 0xce
                true=uint32_value,
            ),
            exp.If(
                this=exp.EQ(this=marker, expression=exp.Literal.number(205)),  # 0xcd
                true=uint16_value,
            ),
            exp.If(
                this=exp.EQ(this=marker, expression=exp.Literal.number(204)),  # 0xcc
                true=uint8_value,
            ),
            exp.If(
                this=exp.LTE(
                    this=marker, expression=exp.Literal.number(127)
                ),  # <= 0x7f
                true=fixint_value,
            ),
        ],
        default=exp.Null(),
    )


def _build_trino_decoder(node_id_exp: exp.Expression) -> exp.Expression:
    """Builds the complete Trino decoder handling both formats."""
    # Check for underscore (next-gen format)
    contains_underscore = exp.GT(
        this=exp.Anonymous(
            this="strpos",
            expressions=[node_id_exp, exp.Literal.string("_")],
        ),
        expression=exp.Literal.number(0),
    )

    legacy_result = _build_legacy_decoder_trino(node_id_exp)
    nextgen_result = _build_nextgen_decoder_trino(node_id_exp)

    case_expr = exp.Case(
        ifs=[
            exp.If(
                this=exp.Is(this=node_id_exp, expression=exp.Null()),
                true=exp.Null(),
            ),
            exp.If(
                this=contains_underscore,
                true=nextgen_result,
            ),
        ],
        default=legacy_result,
    )

    return exp.Try(this=case_expr)
