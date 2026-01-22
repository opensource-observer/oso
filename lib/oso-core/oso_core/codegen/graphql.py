"""
Codegen plugin for ariadne-codengen.

This automatically generates a generic t.Protocol for the GraphQL client class
based on the generated graphql client from ariadne-codengen.
"""

import ast
import typing as t
from dataclasses import dataclass

type StmtListCallable = t.Callable[[], t.List[ast.stmt]]

T = t.TypeVar("T", bound=ast.stmt)


@dataclass(kw_only=True)
class StmtPointer(t.Generic[T]):
    stmt_list: "StmtListWrapper"
    pointer: T

    def insert_before(self, stmt: ast.stmt) -> None:
        self.stmt_list.insert_before(self.pointer, stmt)

    @property
    def location(self) -> int:
        return self.stmt_list.index_of(self.pointer)

    def insert_after(self, stmt: ast.stmt) -> None:
        self.stmt_list.insert_after(self.pointer, stmt)


class StmtListWrapper:
    def __init__(self, stmt_list: StmtListCallable):
        self._stmt_list = stmt_list

    def insert_before(self, pointer: ast.stmt, stmt: ast.stmt) -> None:
        location = self._stmt_list().index(pointer)
        self._stmt_list().insert(location, stmt)

    def insert_after(self, pointer: ast.stmt, stmt: ast.stmt) -> None:
        location = self._stmt_list().index(pointer)
        self._stmt_list().insert(location + 1, stmt)

    def index_of(self, pointer: ast.stmt) -> int:
        return self._stmt_list().index(pointer)

    def find_class_def(self, class_name: str) -> t.Optional[StmtPointer[ast.ClassDef]]:
        for node in self._stmt_list():
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return StmtPointer(stmt_list=self, pointer=node)
        return None

    def find_function_def(
        self, function_name: str
    ) -> t.Optional[StmtPointer[ast.FunctionDef] | StmtPointer[ast.AsyncFunctionDef]]:
        for node in self._stmt_list():
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == function_name
            ):
                if isinstance(node, ast.FunctionDef):
                    return StmtPointer(stmt_list=self, pointer=node)
                else:
                    return StmtPointer(stmt_list=self, pointer=node)
        return None

    def list_class_defs(self) -> t.List[StmtPointer[ast.ClassDef]]:
        return [
            StmtPointer(stmt_list=self, pointer=node)
            for node in self._stmt_list()
            if isinstance(node, ast.ClassDef)
        ]

    def list_function_defs(
        self,
    ) -> t.List[StmtPointer[ast.FunctionDef] | StmtPointer[ast.AsyncFunctionDef]]:
        async_funcs = [
            StmtPointer(stmt_list=self, pointer=node)
            for node in self._stmt_list()
            if isinstance(node, ast.AsyncFunctionDef)
        ]
        sync_funcs = [
            StmtPointer(stmt_list=self, pointer=node)
            for node in self._stmt_list()
            if isinstance(node, ast.FunctionDef)
        ]
        return async_funcs + sync_funcs


def _find_class_def(module: ast.Module, class_name: str) -> t.Optional[StmtPointer]:
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            wrapper = StmtListWrapper(stmt_list=lambda: module.body)
            return StmtPointer(stmt_list=wrapper, pointer=node)
    return None


def generate_client_module(self, module: ast.Module) -> ast.Module:
    """Rewrites the client module to add a Protocol for the client class."""

    module_body = StmtListWrapper(stmt_list=lambda: module.body)

    # Find the client class
    client_class_pointer = module_body.find_class_def("Client")

    if client_class_pointer is None:
        raise ValueError("Could not find Client class in module")

    client_class = client_class_pointer.pointer

    assert isinstance(client_class, ast.ClassDef), "Expected ClassDef node"

    client_class_wrapper = StmtListWrapper(stmt_list=lambda: client_class.body)
    method_defs = client_class_wrapper.list_function_defs()

    # Create the Protocol class
    protocol_methods: t.List[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for method_pointer in method_defs:
        method = method_pointer.pointer
        decorator_list: list[ast.expr] = []
        body: list[ast.stmt] = [ast.Return()]
        match method:
            case ast.FunctionDef():
                protocol_method = ast.FunctionDef(
                    name=method.name,
                    args=method.args,
                    body=body,
                    decorator_list=decorator_list,
                    returns=method.returns,
                    type_params=method.type_params,
                )
            case ast.AsyncFunctionDef():
                protocol_method = ast.AsyncFunctionDef(
                    name=method.name,
                    args=method.args,
                    body=body,
                    decorator_list=decorator_list,
                    returns=method.returns,
                    type_params=method.type_params,
                )
            case _:
                raise ValueError("Expected FunctionDef or AsyncFunctionDef node")
        protocol_methods.append(protocol_method)

    return module
