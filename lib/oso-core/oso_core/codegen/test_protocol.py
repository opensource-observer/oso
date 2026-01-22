import ast
import typing as t
from dataclasses import dataclass

import pytest
from oso_core.codegen.protocol import (
    create_protocol_module,
    resolve_import_alias,
    resolve_relative_imports,
)

T = t.TypeVar("T")


def assert_type_and_return(val: t.Any, expected_type: t.Type[T]) -> T:
    assert isinstance(val, expected_type), f"Expected {expected_type}, got {type(val)}"
    return val


def test_create_protocol_module_from_source() -> None:
    source_code = """
import typing as t

class MyService:
    @property
    def status(self) -> str:
        return "ok"

    def process(self, data: t.Dict[str, t.Any]) -> int:
        return 0

    async def fetch(self, url: str) -> str:
        return "data"

    async def _internal_method(self) -> None:
        pass
        
    x: int = 10
"""
    target = "dummy_module:MyService"

    protocol_mod = create_protocol_module(
        target, protocol_name="MyServiceProtocol", module_source_code=source_code
    )

    assert isinstance(protocol_mod, ast.Module)

    imports = [n for n in protocol_mod.body if isinstance(n, ast.Import)]
    assert any(
        alias.name == "typing" and alias.asname == "t"
        for imp in imports
        for alias in imp.names
    )

    proto_cls_list = [n for n in protocol_mod.body if isinstance(n, ast.ClassDef)]
    assert len(proto_cls_list) == 1
    proto_cls = proto_cls_list[0]

    assert proto_cls.name == "MyServiceProtocol"
    assert len(proto_cls.bases) == 1
    base = assert_type_and_return(proto_cls.bases[0], ast.Attribute)
    assert base.attr == "Protocol"

    methods = [
        n
        for n in proto_cls.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    assert len(methods) == 3

    status_prop = next(m for m in methods if m.name == "status")
    assert any(
        isinstance(d, ast.Name) and d.id == "property"
        for d in status_prop.decorator_list
    )

    assert len(status_prop.body) == 1
    stmt = assert_type_and_return(status_prop.body[0], ast.Expr)
    value = assert_type_and_return(stmt.value, ast.Constant)
    assert value.value is Ellipsis

    ann_assigns = [n for n in proto_cls.body if isinstance(n, ast.AnnAssign)]
    assert len(ann_assigns) == 1
    ann_assign = ann_assigns[0]
    target_node = assert_type_and_return(ann_assign.target, ast.Name)
    assert target_node.id == "x"
    assert ann_assign.value is None


def test_create_protocol_module_with_extra_imports() -> None:
    source_code = "class A: pass"
    target = "dummy:A"

    extra: t.List[ast.stmt] = [ast.Import(names=[ast.alias(name="foo")])]
    mod = create_protocol_module(
        target, extra_imports=extra, module_source_code=source_code
    )

    imports = [n for n in mod.body if isinstance(n, ast.Import)]
    assert any(alias.name == "foo" for imp in imports for alias in imp.names)


def test_create_protocol_module_preserves_imports() -> None:
    source_code = """
import typing as t
from decimal import Decimal

class MyService:
    def calculate(self, val: Decimal) -> Decimal:
        return val
"""
    target = "dummy:MyService"
    protocol_mod = create_protocol_module(target, module_source_code=source_code)

    imports = [n for n in protocol_mod.body if isinstance(n, ast.ImportFrom)]
    assert any(
        imp.module == "decimal" and any(a.name == "Decimal" for a in imp.names)
        for imp in imports
    )


def test_create_protocol_module_typing_conflict_import() -> None:
    source_code = """
import something as t

class MyService:
    def foo(self, x: t.Type) -> None:
        pass
"""
    target = "dummy:MyService"
    protocol_mod = create_protocol_module(target, module_source_code=source_code)

    imports = [n for n in protocol_mod.body if isinstance(n, ast.Import)]
    assert any(
        alias.name == "something" and alias.asname == "t"
        for imp in imports
        for alias in imp.names
    )

    typing_imp = next(
        (imp for imp in imports if any(a.name == "typing" for a in imp.names)), None
    )
    assert typing_imp is not None
    typing_alias_in_import = typing_imp.names[0].asname or typing_imp.names[0].name
    assert typing_alias_in_import != "t"

    proto_cls = [n for n in protocol_mod.body if isinstance(n, ast.ClassDef)][0]
    base_attr = assert_type_and_return(proto_cls.bases[0], ast.Attribute)
    assert isinstance(base_attr.value, ast.Name)
    assert base_attr.value.id == typing_alias_in_import


def expect_none(stmt: t.Optional[ast.stmt]) -> bool:
    return stmt is None


def expect_import(
    name: str, asname: t.Optional[str]
) -> t.Callable[[t.Optional[ast.stmt]], bool]:
    def check(stmt: t.Optional[ast.stmt]) -> bool:
        return (
            isinstance(stmt, ast.Import)
            and stmt.names[0].name == name
            and stmt.names[0].asname == asname
        )

    return check


def expect_import_no_asname(name: str) -> t.Callable[[t.Optional[ast.stmt]], bool]:
    def check(stmt: t.Optional[ast.stmt]) -> bool:
        return (
            isinstance(stmt, ast.Import)
            and stmt.names[0].name == name
            and stmt.names[0].asname is None
        )

    return check


def expect_importfrom(
    module: str, name: str, asname: t.Optional[str]
) -> t.Callable[[t.Optional[ast.stmt]], bool]:
    def check(stmt: t.Optional[ast.stmt]) -> bool:
        return (
            isinstance(stmt, ast.ImportFrom)
            and stmt.module == module
            and stmt.names[0].name == name
            and stmt.names[0].asname == asname
        )

    return check


@pytest.mark.parametrize(
    "source, module_path, name, alias, expected_alias, stmt_check",
    [
        ("import foo as f", None, "foo", "bar", "f", expect_none),
        ("x = 1", None, "foo", "f", "f", expect_import("foo", "f")),
        ("f = 1", None, "foo", "f", "foo", expect_import_no_asname("foo")),
        (
            "f = 1\nfoo = 2",
            None,
            "foo",
            "f",
            "f_generated",
            expect_import("foo", "f_generated"),
        ),
        (
            "f = 1\nfoo = 2\nf_generated = 3",
            None,
            "foo",
            "f",
            "f_generated_1",
            expect_import("foo", "f_generated_1"),
        ),
        ("from pkg import foo as f", "pkg", "foo", "bar", "f", expect_none),
        ("x = 1", "pkg", "foo", "f", "f", expect_importfrom("pkg", "foo", "f")),
    ],
)
def test_resolve_import_alias(
    source: str,
    module_path: t.Optional[str],
    name: str,
    alias: str,
    expected_alias: str,
    stmt_check: t.Callable[[t.Optional[ast.stmt]], bool],
) -> None:
    module = ast.parse(source)
    res_alias, res_stmt = resolve_import_alias(
        module, name, module_path=module_path, alias=alias
    )
    assert res_alias == expected_alias
    assert stmt_check(res_stmt)


def expect_error(
    exc_type: t.Type[Exception],
) -> t.Callable[[t.Union[t.Any, Exception]], bool]:
    def check(res_or_exc: t.Union[t.Any, Exception]) -> bool:
        return isinstance(res_or_exc, exc_type)

    return check


def expect_result(
    expected: t.List[t.Tuple[str, int, t.List[t.Tuple[str, t.Optional[str]]]]],
) -> t.Callable[[t.Union[t.List[ast.stmt], Exception]], bool]:
    def check(res: t.Union[t.List[ast.stmt], Exception]) -> bool:
        if isinstance(res, Exception):
            return False
        if len(res) != len(expected):
            return False
        for imp, (exp_module, exp_level, exp_names) in zip(res, expected):
            if not isinstance(imp, ast.ImportFrom):
                return False
            if imp.module != exp_module or imp.level != exp_level:
                return False
            if len(imp.names) != len(exp_names):
                return False
            for n, (en, eas) in zip(imp.names, exp_names):
                if n.name != en or n.asname != eas:
                    return False
        return True

    return check


@pytest.mark.parametrize(
    "imports, module_name, checker",
    [
        (
            [
                ast.ImportFrom(
                    module=None, names=[ast.alias(name="a", asname=None)], level=1
                )
            ],
            "pkg.mod",
            expect_result([("pkg", 0, [("a", None)])]),
        ),
        (
            [
                ast.ImportFrom(
                    module="b", names=[ast.alias(name="c", asname=None)], level=2
                )
            ],
            "pkg.mod",
            expect_result([("b", 0, [("c", None)])]),
        ),
        (
            [
                ast.ImportFrom(
                    module=None, names=[ast.alias(name="a", asname=None)], level=3
                )
            ],
            "pkg.mod",
            expect_error(ValueError),
        ),
    ],
)
def test_resolve_relative_imports_param(
    imports: t.List[ast.stmt],
    module_name: str,
    checker: t.Callable[[t.Union[t.List[ast.stmt], Exception]], bool],
) -> None:
    try:
        res = resolve_relative_imports(imports, module_name)
        assert checker(res)
    except Exception as e:
        if not checker(e):
            raise e


def test_create_protocol_module_filters_unused_imports() -> None:
    source_code = """
from typing import List, Dict, Any
# Dict is unused in the class

class MyService:
    def foo(self, x: List[Any]) -> None:
        pass
"""
    target = "dummy:MyService"
    protocol_mod = create_protocol_module(target, module_source_code=source_code)

    imports = [n for n in protocol_mod.body if isinstance(n, ast.ImportFrom)]
    typing_imp = next(imp for imp in imports if imp.module == "typing")

    imported_names = {n.name for n in typing_imp.names}
    assert "List" in imported_names
    assert "Any" in imported_names
    assert "Dict" not in imported_names


def test_create_protocol_module_star_import_error() -> None:
    source_code = """
from something import *

class MyService:
    pass
"""
    target = "dummy:MyService"
    with pytest.raises(ValueError, match="Star import found"):
        create_protocol_module(target, module_source_code=source_code)


def test_create_protocol_module_star_import_allowed() -> None:
    source_code = """
from something import *

class MyService:
    pass
"""
    target = "dummy:MyService"
    protocol_mod = create_protocol_module(
        target, module_source_code=source_code, include_star_imports=True
    )

    imports = [n for n in protocol_mod.body if isinstance(n, ast.ImportFrom)]
    star_imp = next(imp for imp in imports if imp.module == "something")
    assert star_imp.names[0].name == "*"


def test_create_protocol_module_inspect() -> None:
    # Use a standard library class to test inspection
    target = "email.message:Message"

    # Run with use_inspect=True
    protocol_mod = create_protocol_module(target, use_inspect=True)

    assert isinstance(protocol_mod, ast.Module)

    # Check if we have ClassDef
    cls_def = next((n for n in protocol_mod.body if isinstance(n, ast.ClassDef)), None)
    assert cls_def is not None
    assert cls_def.name == "MessageProtocol"

    # Check if bases include Protocol
    assert len(cls_def.bases) == 1
    base = cls_def.bases[0]
    assert isinstance(base, ast.Attribute)
    assert base.attr == "Protocol"

    # Check if methods are present (e.g. get_payload)
    methods = [
        n.name
        for n in cls_def.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    assert "get_payload" in methods
    assert "add_header" in methods


@dataclass
class MyDependency:
    x: int


class MyServiceWithDep:
    def process(self, dep: MyDependency) -> None:
        pass


def test_create_protocol_module_inspect_imports() -> None:
    target = f"{MyServiceWithDep.__module__}:MyServiceWithDep"

    # Run with use_inspect=True
    mod = create_protocol_module(target, use_inspect=True)

    imports = [n for n in mod.body if isinstance(n, ast.ImportFrom)]

    # Check if MyDependency is imported
    # It should be imported from the same module
    dependency_import = next(
        (i for i in imports if any(n.name == "MyDependency" for n in i.names)), None
    )
    assert dependency_import is not None
    assert dependency_import.module == MyServiceWithDep.__module__
