import textwrap

import pytest

from .responses import ensure_no_code_block


@pytest.mark.parametrize(
    "markdown_input, expected_output",
    [
        (
            """
        ```python
        def hello_world():
            print("Hello, world!")
        ```
        """,
            'def hello_world():\n    print("Hello, world!")\n',
        ),
        (
            """
        ```python
        def add(a, b):
            return a + b
        ```
        """,
            "def add(a, b):\n    return a + b\n",
        ),
        (
            """
        ```sql
        SELECT * FROM users;
        ```
        """,
            "SELECT * FROM users;",
        ),
        ("no markdown", "no markdown"),
    ],
)
def test_extract_python_blocks(markdown_input: str, expected_output: str):
    assert (
        ensure_no_code_block(textwrap.dedent(markdown_input)).strip()
        == expected_output.strip()
    )
