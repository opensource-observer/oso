
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

    Supports both formats:
    - **Legacy**: Base64 "Type:ID" (e.g., `MDQ6VXNlcjQwMjcwMzc=` → `4027037`)
    - **Next-gen**: URL-safe Base64 msgpack `[type, id]` (e.g., `U_kgDOA3N-eg` → `57900666`)

    Format detection:
    - Contains `_` → Next-gen
    - No `_` → Legacy

    Args:
        evaluator: Macro evaluator
        node_id_exp: GitHub Node ID expression (string)

    Returns:
        Expression returning decoded integer actor ID or NULL
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
    """
    Decode legacy format Node ID in DuckDB.
    MDQ6VXNlcjQwMjcwMzc= → base64 decode → "User:4027037" → 4027037
    """
    # from_base64(node_id) returns a blob, convert to varchar then extract
    decoded = exp.Anonymous(
        this="from_base64",
        expressions=[node_id_exp],
    )
    # Cast blob to varchar to get the string
    decoded_str = exp.Cast(
        this=decoded,
        to=exp.DataType.build("VARCHAR"),
    )
    # Extract the integer at the end of the string using regexp_extract
    # The format might be "04:User4027037" or "User:4027037", so we extract trailing digits
    extracted = exp.RegexpExtract(
        this=decoded_str,
        expression=exp.Literal.string(r"(\d+)$"),
        group=exp.Literal.number(1),
    )
    # Cast to BIGINT
    return exp.Cast(
        this=extracted,
        to=exp.DataType.build("BIGINT"),
    )


def _build_nextgen_decoder_duckdb(node_id_exp: exp.Expression) -> exp.Expression:
    """
    Decode next-gen format Node ID in DuckDB.
    U_kgDOA3N-eg → split on '_' → take suffix → URL-safe base64 decode → extract integer
    """
    # Find position of first underscore to extract suffix
    # We use instr + substring instead of string_split to safely handle the suffix
    # even if it contains underscores (though uncommon in URL-safe base64, usually it's '/')
    underscore_pos = exp.Anonymous(
        this="instr",
        expressions=[node_id_exp, exp.Literal.string("_")],
    )
    suffix_part = exp.Substring(
        this=node_id_exp,
        start=exp.Add(this=underscore_pos, expression=exp.Literal.number(1)),
    )

    # Replace URL-safe base64 characters: - → +, _ → /
    replaced1 = exp.Anonymous(
        this="replace",
        expressions=[suffix_part, exp.Literal.string("-"), exp.Literal.string("+")],
    )
    replaced2 = exp.Anonymous(
        this="replace",
        expressions=[replaced1, exp.Literal.string("_"), exp.Literal.string("/")],
    )

    # Calculate padding needed: (4 - len % 4) % 4
    suffix_len = exp.Length(this=replaced2)
    padding_needed = exp.Mod(
        this=exp.Sub(
            this=exp.Literal.number(4),
            expression=exp.Mod(this=suffix_len, expression=exp.Literal.number(4)),
        ),
        expression=exp.Literal.number(4),
    )

    # Add padding using repeat('=', padding_needed)
    padding = exp.Anonymous(
        this="repeat",
        expressions=[exp.Literal.string("="), padding_needed],
    )
    padded = exp.Concat(
        expressions=[replaced2, padding],
        safe=False,
        coalesce=False,
    )

    # Decode base64 to blob
    decoded_bytes = exp.Anonymous(
        this="from_base64",
        expressions=[padded],
    )

    # Convert blob to hex string for byte extraction
    # DuckDB doesn't have get_byte, so we use hex() and extract 2 chars per byte
    hex_str = exp.Anonymous(
        this="hex",
        expressions=[decoded_bytes],
    )

    # Helper to get byte at position (1-indexed)
    # hex string has 2 chars per byte, so byte N is at position (N-1)*2 + 1
    def get_byte(hex_exp: exp.Expression, pos: int) -> exp.Expression:
        """Extract single byte from hex string at position (1-indexed) and return as integer."""
        # Position in hex string: (pos-1)*2 + 1 for 1-indexed substring
        hex_pos = (pos - 1) * 2 + 1
        two_chars = exp.Substring(
            this=hex_exp,
            start=exp.Literal.number(hex_pos),
            length=exp.Literal.number(2),
        )
        # Convert 2-char hex to integer using ('0x' || hex)::INTEGER
        hex_with_prefix = exp.Concat(
            expressions=[exp.Literal.string("0x"), two_chars],
            safe=False,
            coalesce=False,
        )
        return exp.Cast(
            this=hex_with_prefix,
            to=exp.DataType.build("INTEGER"),
        )

    # Get the type marker at byte 3
    marker = get_byte(hex_str, 3)

    # For uint32 (0xce = 206): read bytes 4-7 as big-endian
    # (byte4 << 24) | (byte5 << 16) | (byte6 << 8) | byte7
    byte4 = get_byte(hex_str, 4)
    byte5 = get_byte(hex_str, 5)
    byte6 = get_byte(hex_str, 6)
    byte7 = get_byte(hex_str, 7)

    # For DuckDB, use arithmetic instead of bitwise operators to avoid dialect issues.
    # Since the bytes are in non-overlapping positions, OR is equivalent to ADD.
    # Left shift by N is equivalent to multiplication by 2^N.
    # uint32 = b4<<24 | b5<<16 | b6<<8 | b7
    #        = b4*2^24 + b5*2^16 + b6*2^8 + b7

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

    # For uint16 (0xcd = 205): read bytes 4-5 as big-endian
    # = b4<<8 | b5 = b4*256 + b5
    uint16_value = exp.Add(
        this=exp.Mul(
            this=byte4,
            expression=exp.Literal.number(1 << 8),
        ),
        expression=byte5,
    )

    # For uint8 (0xcc = 204): read byte 4
    uint8_value = byte4

    # For fixint (0x01-0x7f): the marker byte IS the value
    fixint_value = marker

    # Build CASE expression
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
    """
    Build the complete DuckDB decoder that handles both formats.
    """
    # Check if it contains underscore (next-gen format)
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
    """
    Decode legacy format Node ID in Trino.
    MDQ6VXNlcjQwMjcwMzc= → base64 decode → "User:4027037" → 4027037
    """
    # from_base64(node_id) returns varbinary
    decoded = exp.Anonymous(
        this="from_base64",
        expressions=[node_id_exp],
    )
    # Convert varbinary to varchar using from_utf8
    decoded_str = exp.Anonymous(
        this="from_utf8",
        expressions=[decoded],
    )
    # Extract the integer at the end of the string using regexp_extract
    extracted = exp.Anonymous(
        this="regexp_extract",
        expressions=[
            decoded_str,
            exp.Literal.string(r"(\d+)$"),
            exp.Literal.number(1),
        ],
    )
    # Cast to BIGINT
    return exp.Cast(
        this=extracted,
        to=exp.DataType.build("BIGINT"),
    )


def _build_nextgen_decoder_trino(node_id_exp: exp.Expression) -> exp.Expression:
    """
    Decode next-gen format Node ID in Trino.
    U_kgDOA3N-eg → split on '_' → take suffix → URL-safe base64 decode → extract integer
    """
    # Split on underscore and take the second element (1-indexed in Trino)
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

    # Replace URL-safe base64 characters: - → +, _ → /
    replaced1 = exp.Anonymous(
        this="replace",
        expressions=[suffix_part, exp.Literal.string("-"), exp.Literal.string("+")],
    )
    replaced2 = exp.Anonymous(
        this="replace",
        expressions=[replaced1, exp.Literal.string("_"), exp.Literal.string("/")],
    )

    # Calculate padding needed: (4 - len % 4) % 4
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

    # Pad using rpad with '='
    # We need: rpad(string, length + padding_needed, '=')
    target_len = exp.Add(this=suffix_len, expression=padding_needed)
    padded = exp.Anonymous(
        this="rpad",
        expressions=[replaced2, target_len, exp.Literal.string("=")],
    )

    # Decode base64 to varbinary
    decoded_bytes = exp.Anonymous(
        this="from_base64",
        expressions=[padded],
    )

    # Helper to get byte at position (1-indexed for Trino varbinary)
    def get_byte(blob_exp: exp.Expression, pos: int) -> exp.Expression:
        """Extract single byte at position and return as integer."""
        # In Trino: to_big_endian_64 won't work for single byte
        # Use: bitwise_and(to_integer(substr(blob, pos, 1)), 255)
        # Actually: for single byte, use from_big_endian_32 after padding
        # Simpler: use array approach
        # Trino has no direct byte access, need to use bit manipulation
        # Approach: cast varbinary to array of tinyint using sequence
        # Actually use: CAST(SUBSTRING(blob FROM pos FOR 1) AS TINYINT) doesn't exist
        # Best approach: convert to hex and parse
        single_byte = exp.Anonymous(
            this="substr",
            expressions=[blob_exp, exp.Literal.number(pos), exp.Literal.number(1)],
        )
        # to_hex returns hex string, then from_base(hex, 16)
        hex_str = exp.Anonymous(
            this="to_hex",
            expressions=[single_byte],
        )
        return exp.Anonymous(
            this="from_base",
            expressions=[hex_str, exp.Literal.number(16)],
        )

    # Get the type marker at byte 3
    marker = get_byte(decoded_bytes, 3)

    # For uint32 (0xce = 206): read bytes 4-7 as big-endian
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

    # For uint16 (0xcd = 205): read bytes 4-5 as big-endian
    uint16_value = exp.BitwiseOr(
        this=exp.Anonymous(
            this="bitwise_left_shift",
            expressions=[byte4, exp.Literal.number(8)],
        ),
        expression=byte5,
    )

    # For uint8 (0xcc = 204): read byte 4
    uint8_value = byte4

    # For fixint (0x01-0x7f): the marker byte IS the value
    fixint_value = marker

    # Build CASE expression
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
    """
    Build the complete Trino decoder that handles both formats.
    """
    # Check if it contains underscore (next-gen format)
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
