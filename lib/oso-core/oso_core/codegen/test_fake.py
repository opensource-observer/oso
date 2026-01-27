import ast

from oso_core.codegen.fake import create_fake_module


# Helper to check if a body contains a return with polyfactory call
def has_factory_call(node: ast.FunctionDef, factory_type: str, model_name: str) -> bool:
    if not node.body:
        return False
    ret = node.body[0]
    if not isinstance(ret, ast.Return):
        return False
    call = ret.value
    if not isinstance(call, ast.Call):
        return False
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "build":
        return False
    inner_call = call.func.value
    if not isinstance(inner_call, ast.Call):
        return False
    if (
        not isinstance(inner_call.func, ast.Attribute)
        or inner_call.func.attr != "create_factory"
    ):
        return False
    factory_cls = inner_call.func.value
    if not isinstance(factory_cls, ast.Name) or factory_cls.id != factory_type:
        return False
    if not inner_call.args:
        return False
    model_arg = inner_call.args[0]
    if not isinstance(model_arg, ast.Name) or model_arg.id != model_name:
        return False
    return True


def test_create_fake_module_pydantic():
    target = "oso_core.codegen.test_only_examples.pydantic_example:MyProtocol"
    mod = create_fake_module(target)

    fake_cls = next(n for n in mod.body if isinstance(n, ast.ClassDef))
    assert fake_cls.name == "FakeMyProtocol"

    method = next(
        n
        for n in fake_cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "get_model"
    )
    assert has_factory_call(method, "ModelFactory", "MyModel")

    imports = [n for n in mod.body if isinstance(n, ast.ImportFrom)]
    assert any(
        i.module == "polyfactory.factories.pydantic_factory"
        and any(n.name == "ModelFactory" for n in i.names)
        for i in imports
    )


def test_create_fake_module_dataclass():
    target = "oso_core.codegen.test_only_examples.dataclass_example:MyProtocol"
    mod = create_fake_module(target)

    fake_cls = next(n for n in mod.body if isinstance(n, ast.ClassDef))
    method = next(
        n
        for n in fake_cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "get_data"
    )

    assert has_factory_call(method, "DataclassFactory", "MyData")

    imports = [n for n in mod.body if isinstance(n, ast.ImportFrom)]
    assert any(
        i.module == "polyfactory.factories.dataclass_factory"
        and any(n.name == "DataclassFactory" for n in i.names)
        for i in imports
    )


def test_create_fake_module_typeddict():
    target = "oso_core.codegen.test_only_examples.typed_dict_example:MyProtocol"
    mod = create_fake_module(target)

    fake_cls = next(n for n in mod.body if isinstance(n, ast.ClassDef))
    method = next(
        n
        for n in fake_cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "get_dict"
    )

    assert has_factory_call(method, "TypedDictFactory", "MyDict")

    imports = [n for n in mod.body if isinstance(n, ast.ImportFrom)]
    assert any(
        i.module == "polyfactory.factories.typed_dict_factory"
        and any(n.name == "TypedDictFactory" for n in i.names)
        for i in imports
    )
