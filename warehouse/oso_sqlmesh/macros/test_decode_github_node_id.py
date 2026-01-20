import base64

import pytest
from macros.decode_github_node_id import (
    _pad_base64_duckdb,
    _pad_base64_trino,
    decode_github_node_id,
)
from sqlglot import expressions as exp


class MockAdapter:
    def __init__(self, dialect: str):
        self.dialect = dialect


class MockEvaluator:
    def __init__(self, dialect: str):
        self.runtime_stage = "evaluating"
        self.engine_adapter = MockAdapter(dialect)


class TestPaddingCalculation:
    """Test that base64 padding is calculated correctly for all string lengths."""

    @pytest.mark.parametrize(
        "length,expected_padding",
        [
            (1, 3),
            (2, 2),
            (3, 1),
            (4, 0),
            (5, 3),
            (6, 2),
            (7, 1),
            (8, 0),
            (9, 3),
            (10, 2),
        ],
    )
    def test_padding_formula(self, length: int, expected_padding: int):
        actual = (4 - length % 4) % 4
        assert actual == expected_padding, (
            f"len={length}: expected {expected_padding}, got {actual}"
        )

    def test_trino_padding_sql_has_correct_parentheses(self):
        suffix_exp = exp.Column(this="suffix")
        result = _pad_base64_trino(suffix_exp)
        sql = result.sql(dialect="trino")
        assert "(4 - LENGTH(suffix) % 4) % 4" in sql, f"Missing parentheses in: {sql}"

    def test_duckdb_padding_sql_has_correct_parentheses(self):
        suffix_exp = exp.Column(this="suffix")
        result = _pad_base64_duckdb(suffix_exp)
        sql = result.sql(dialect="duckdb")
        assert "(4 - LENGTH(suffix) % 4) % 4" in sql, f"Missing parentheses in: {sql}"


class TestDecodeGitHubNodeId:
    """Test the full decode_github_node_id macro."""

    @pytest.mark.parametrize(
        "node_id,expected_id",
        [
            # GitHub v2 format: msgpack [0, id] with urlsafe base64
            # MsgPack formats by ID range:
            #   FixInt (0-127): 1 byte, no marker
            #   UInt8 (128-255): 2 bytes, marker 0xcc
            #   UInt16 (256-65535): 3 bytes, marker 0xcd
            #   UInt32 (65536-4.29B): 5 bytes, marker 0xce
            #   UInt64 (>4.29B): 9 bytes, marker 0xcf
            #
            # FixInt (0-127) - suffix length 4 (BUG AFFECTED - needs 0 padding)
            ("U_kgAA", 0),
            ("U_kgAb", 27),
            ("U_kgBO", 78),
            ("U_kgB_", 127),
            # UInt8 (128-255) - suffix length 6 (needs 2 padding)
            ("U_kgDMgA", 128),
            ("U_kgDMyA", 200),
            ("U_kgDM_w", 255),
            # UInt16 (256-65535) - suffix length 7 (needs 1 padding)
            ("U_kgDNAQA", 256),
            ("U_kgDNA-g", 1000),
            ("U_kgDN__8", 65535),
            # UInt32 (65536-4.29B) - suffix length 10 (needs 2 padding)
            ("U_kgDOAAEAAA", 65536),
            ("U_kgDOAAGGoA", 100000),
            ("U_kgDOBbc7Ag", 95894274),
            # UInt64 (>4.29B) - suffix length 15 (needs 1 padding)
            ("U_kgDPAAAAASoF8gA", 5000000000),
            # Legacy v1 format (base64 encoded "type:id" string)
            ("MDQ6VXNlcjEyMzQ1Njc=", 1234567),
        ],
    )
    def test_python_decode_matches_expected(self, node_id: str, expected_id: int):
        """Verify test expectations using Python decode as reference."""
        import msgpack

        if "_" in node_id:
            _, encoded_part = node_id.split("_", 1)
            padding = "=" * (4 - len(encoded_part) % 4)
            decoded_bytes = base64.urlsafe_b64decode(encoded_part + padding)
            data = msgpack.unpackb(decoded_bytes)
            result = data[1] if isinstance(data, list) else data
        else:
            decoded_str = base64.b64decode(node_id).decode("utf-8")
            id_segment = decoded_str.split(":")[-1]
            result = int("".join(filter(str.isdigit, id_segment)))

        assert result == expected_id

    @pytest.mark.parametrize("dialect", ["trino", "duckdb"])
    def test_macro_generates_valid_sql(self, dialect: str):
        evaluator = MockEvaluator(dialect)
        node_id_exp = exp.Literal.string("U_kgAb")
        result = decode_github_node_id(evaluator, node_id_exp)
        sql = result.sql(dialect=dialect)
        assert sql is not None
        assert len(sql) > 0
        assert "TRY(" in sql

    @pytest.mark.parametrize("dialect", ["trino", "duckdb"])
    def test_macro_handles_null_input(self, dialect: str):
        evaluator = MockEvaluator(dialect)
        node_id_exp = exp.Column(this="node_id")
        result = decode_github_node_id(evaluator, node_id_exp)
        sql = result.sql(dialect=dialect)
        assert "IS NULL" in sql

    @pytest.mark.parametrize("dialect", ["trino", "duckdb"])
    def test_macro_detects_nextgen_format(self, dialect: str):
        evaluator = MockEvaluator(dialect)
        node_id_exp = exp.Column(this="node_id")
        result = decode_github_node_id(evaluator, node_id_exp)
        sql = result.sql(dialect=dialect)
        if dialect == "trino":
            assert "STRPOS" in sql
        else:
            assert "instr" in sql.lower()

    def test_short_node_ids_use_fixint_path(self):
        """Short node IDs (len 6) should decode using fixint (marker <= 127)."""
        evaluator = MockEvaluator("trino")
        node_id_exp = exp.Literal.string("U_kgAb")
        result = decode_github_node_id(evaluator, node_id_exp)
        sql = result.sql(dialect="trino")
        assert "<= 127" in sql, "fixint check should be present"


class TestNodeIdFormats:
    """Test various GitHub Node ID formats."""

    @pytest.mark.parametrize(
        "node_id,id_type",
        [
            ("U_kgDOBbc7Ag", "user_v2"),
            ("R_kgDOGh4L_g", "repo_v2"),
            ("O_kgDOABcDEw", "org_v2"),
            ("MDQ6VXNlcjEyMzQ1Njc=", "user_v1"),
            ("MDEwOlJlcG9zaXRvcnkxMjM0NTY3", "repo_v1"),
        ],
    )
    def test_format_detection(self, node_id: str, id_type: str):
        """Macro should handle both v1 and v2 formats."""
        evaluator = MockEvaluator("trino")
        node_id_exp = exp.Literal.string(node_id)
        result = decode_github_node_id(evaluator, node_id_exp)
        sql = result.sql(dialect="trino")
        assert sql is not None
