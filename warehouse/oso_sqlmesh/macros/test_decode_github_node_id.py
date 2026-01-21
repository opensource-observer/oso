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
            # --- Next-Gen v2 (MsgPack) Formats ---
            # FixInt (0-127) - 3 bytes total
            ("U_kgAA", 0),  # Min (0)
            ("U_kgBA", 64),  # Median (64)
            ("U_kgBy", 114),  # Real-world User ID
            # UInt8 (128-255) - 4 bytes total
            ("U_kgDMgA", 128),  # Min (128)
            ("U_kgDMvw", 191),  # Median (191)
            ("U_kgDM_w", 255),  # Max (255)
            # UInt16 (256-65535) - 5 bytes total
            ("U_kgDNAQA", 256),  # Min (256)
            ("U_kgDNgH8", 32895),  # Median (32895)
            ("U_kgDN__8", 65535),  # Max (65535)
            # UInt32 (65536-4.29B) - 7 bytes total
            ("U_kgDOAAEAAA", 65536),  # Min (65536)
            ("U_kgDOgAB__w", 2147516415),  # Median (2147516415)
            ("U_kgDO_____w", 4294967295),  # Max (UInt32 Max)
            # UInt64 (>4.29B) - 11 bytes total
            ("U_kgDPAAAAAQAAAAA", 4294967296),  # Min (UInt64 Min)
            ("U_kgDPgAAAAH____8", 9223372039002259455),  # Median (9223372039002259455)
            ("U_kgDP__________8", 18446744073709551615),  # Max (UInt64 Max)
            # User IDs
            ("U_kgDOCH_3TQ", 142604109),
            ("U_kgDOAFB_cg", 5275506),
            ("U_kgDOASN2_w", 19101439),
            ("U_kgDOAe68Mg", 32422962),
            ("U_kgDOA_d-aQ", 66551401),
            # Repo IDs (Critical regression: these caused out-of-bounds in UInt64 path)
            ("R_kgDOIa5_LQ", 565083949),
            ("R_kgDOEb_ZAQ", 297785601),
            ("R_kgDOHZb1_w", 496432639),
            ("R_kgDOIW0T0w", 560796627),
            ("R_kgDOF_r28w", 402323187),
            # Bot IDs
            ("BOT_kgDODH_GIQ", 209700385),
            ("BOT_kgDOCr-_NA", 180338484),
            ("BOT_kgDOCJg4_A", 144193788),
            ("BOT_kgDOCAbJvQ", 134662589),
            # --- Legacy v1 (Base64 "Type:ID") Formats ---
            ("MDQ6VXNlcjEyMzQ1Njc=", 1234567),  # User:1234567
            ("MDEwOlJlcG9zaXRvcnk3NDUyMDEyNA==", 74520124),  # Repository:74520124
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
