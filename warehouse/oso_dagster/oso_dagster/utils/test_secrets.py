import uuid

from .secrets import (
    SimpleSecretResolver,
    resolve_secrets_for_func,
    secret_ref_arg,
)


def fake_func(s: str = secret_ref_arg(group_name="fake", key="foo")):
    return s


def test_create_fake():
    test_str = str(uuid.uuid4())
    resolver = SimpleSecretResolver(
        {
            "fake__foo": bytes(test_str, "utf-8"),
        }
    )

    resolved = resolve_secrets_for_func(resolver, fake_func)
    assert fake_func(**resolved) == test_str

    # Also test setting the argument directly
    assert fake_func(s="test") == "test"
