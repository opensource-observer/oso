import ast
import textwrap

import pytest
from oso_core.codegen.utils import filter_imports


@pytest.mark.parametrize(
    "source, used_names, module_path, include_star_imports, expected_source",
    [
        # 1. Basic Import
        ("import a, b", {"a"}, None, False, "import a"),
        ("import a, b", {"b"}, None, False, "import b"),
        ("import a, b", {"c"}, None, False, ""),
        # 2. Import From
        ("from m import a, b", {"a"}, None, False, "from m import a"),
        ("from m import a, b", {"b"}, None, False, "from m import b"),
        (
            "from typing import List, Dict, Any",
            {"List"},
            None,
            False,
            "from typing import List",
        ),
        # 3. Aliases
        ("import a as x, b as y", {"x"}, None, False, "import a as x"),
        ("from m import a as x, b as y", {"y"}, None, False, "from m import b as y"),
        # 4. Local Definitions
        (
            textwrap.dedent("""
                class Local:
                    pass
            """),
            {"Local"},
            "my.mod",
            False,
            "from my.mod import Local",
        ),
        (
            textwrap.dedent("""
                def func():
                    pass
            """),
            {"func"},
            "my.mod",
            False,
            "from my.mod import func",
        ),
        (
            textwrap.dedent("""
                x = 1
            """),
            {"x"},
            "my.mod",
            False,
            "from my.mod import x",
        ),
        (
            textwrap.dedent("""
                x: int = 1
            """),
            {"x"},
            "my.mod",
            False,
            "from my.mod import x",
        ),
        # 5. Star Imports (Include)
        ("from m import *", set(), None, True, "from m import *"),
        # 6. Mixed
        (
            textwrap.dedent("""
                import a
                class B:
                 pass
            """),
            {"a", "B"},
            "my.mod",
            False,
            textwrap.dedent("""
                import a
                from my.mod import B
            """),
        ),
    ],
)
def test_filter_imports_parameterized(
    source, used_names, module_path, include_star_imports, expected_source
):
    module = ast.parse(source)
    results = filter_imports(module, used_names, module_path, include_star_imports)

    # Create a module from results to unparse
    result_mod = ast.Module(body=results, type_ignores=[])
    # Normalize expected source by parsing and unparsing (handles whitespace diffs)
    if expected_source:
        expected_normalized = ast.unparse(ast.parse(expected_source)).strip()
    else:
        expected_normalized = ""

    assert ast.unparse(result_mod).strip() == expected_normalized


def test_filter_imports_star_raise():
    source = "from m import *"
    module = ast.parse(source)
    with pytest.raises(ValueError, match="Star import found"):
        filter_imports(module, set(), include_star_imports=False)


def test_filter_shadowing_imports_throws_error():
    source = textwrap.dedent("""
        from my import A

        class A:
            def method(self):
                pass
    """)
    module = ast.parse(source)
    with pytest.raises(ValueError, match="Ambiguous name 'A' defined multiple times."):
        filter_imports(module, {"A"}, module_path="my.mod")


def test_filter_shadowing_definitions_throws_error():
    source = textwrap.dedent("""
        def A(): pass
        def A(): pass
    """)
    module = ast.parse(source)
    with pytest.raises(ValueError, match="Ambiguous name 'A' defined multiple times."):
        filter_imports(module, {"A"}, module_path="my.mod")


def test_valid_overloads_pass():
    source = textwrap.dedent("""
        from typing import overload

        @overload
        def A(x: int): ...
        
        @overload
        def A(x: str): ...
        
        def A(x): pass
    """)
    module = ast.parse(source)
    # Should not raise
    filter_imports(module, {"A"}, module_path="my.mod")


def test_valid_overloads_pass_using_alias():
    source = textwrap.dedent("""
        import typing as t

        @t.overload
        def A(x: int): ...
        
        @t.overload
        def A(x: str): ...
        
        def A(x): pass
    """)
    module = ast.parse(source)
    # Should not raise
    filter_imports(module, {"A"}, module_path="my.mod")
